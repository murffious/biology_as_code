"""
Fractional-absorption seed: it parses without flattening, and it disagrees with
the registry in the places it should.

The conflict test is the point of this file. ``MINERAL_REGISTRY`` has carried
bare ``typical_bioavailability`` floats since it was written; the seed carries the
same quantity with a dose, a cohort and a citation. Where they disagree, that is
information — and it is information that disappears the moment someone
"reconciles" the two by overwriting one with the other. Pinning the disagreements
means a future edit to either side has to be deliberate.
"""

from __future__ import annotations

import pytest

pytest.importorskip("yaml", reason="the absorption seed is YAML; PyYAML is in the dev extra")

from biology_as_code.dig.mineral_interactions import (  # noqa: E402
    MINERAL_REGISTRY,
    absorption_prior,
    unsourced_minerals,
)
from biology_as_code.nodes.bounds import (  # noqa: E402
    absorption_bounds,
    bounds_by_mineral,
    parse_fraction,
    reconcile_with_registry,
    seed_meta,
)


def test_seed_loads_and_every_entry_is_a_prior():
    """Secondary source in, `prior` out. Nothing in this seed may claim Bound."""
    bounds = absorption_bounds()
    assert len(bounds) == 20
    assert {b.gate for b in bounds} == {"prior"}


def test_seed_declares_what_promotion_requires():
    meta = seed_meta()
    assert meta["gate_default"] == "prior"
    assert set(meta["promote_requires"]) == {
        "read_primary",
        "population_stated",
        "dose_stated",
    }
    assert meta["source_secondary"]["author"].startswith("Kohlmeier")


def test_resolved_parents_carry_dois():
    """Five parents were resolved against the publisher record, not guessed."""
    resolved = [b for b in absorption_bounds() if b.has_resolved_parent]
    assert len(resolved) == 5
    for bound in resolved:
        assert bound.parent_doi and bound.parent_doi.startswith("10.")
    unresolved = [b for b in absorption_bounds() if not b.has_resolved_parent]
    assert all(b.parent_doi is None for b in unresolved), (
        "a bound without provenance: resolved must not carry a DOI"
    )


@pytest.mark.parametrize(
    "raw,kind,described",
    [
        (0.70, "point", "0.7"),
        ("<0.02", "upper", "<0.02"),
        (">0.90", "lower", ">0.9"),
        ({"min": 0.30, "max": 0.60}, "range", "0.3-0.6"),
        ({"young_adult": 0.40, "older": 0.20}, "cohort", "older 0.2, young_adult 0.4"),
        (None, "unstated", "unstated"),
        ("about half", "unstated", "unstated"),
    ],
)
def test_fraction_parsing_keeps_the_stated_shape(raw, kind, described):
    spec = parse_fraction(raw)
    assert spec.kind == kind
    assert spec.describe() == described


def test_one_sided_bounds_do_not_invent_the_other_side():
    """`>0.90` means at least 0.90. It does not mean 0.95."""
    spec = parse_fraction(">0.90")
    assert spec.high is None
    assert spec.contains(0.95) and spec.contains(1.0)
    assert not spec.contains(0.70)


def test_unstated_fraction_permits_nothing():
    """An absent fraction must not read as 'any value is fine'."""
    spec = parse_fraction(None)
    assert not spec.contains(0.5)
    assert not spec.contains(0.0)


def test_known_conflicts_with_the_registry():
    """Five minerals where the registry float sits outside the sourced prior.

    Not necessarily errors — mostly scope. Zinc carries the seed's 3 mg dose
    condition, which is exactly why 0.30 and 0.70 can both be right. If this set
    changes, someone moved a number on one side or the other and should say why.
    """
    conflicts = {r.mineral_id for r in reconcile_with_registry() if r.is_conflict}
    assert conflicts == {"zn", "se", "mn", "mo", "f"}


def test_zinc_conflict_carries_its_dose_condition():
    """The condition is what resolves the apparent contradiction."""
    zinc = next(r for r in reconcile_with_registry() if r.mineral_id == "zn")
    assert zinc.is_conflict
    assert zinc.registry_value == 0.30
    assert zinc.seed.point == 0.70
    assert "3 mg" in zinc.note


def test_copper_is_a_curve_not_a_float():
    """The seed is richer than the registry here, not poorer.

    Copper absorption runs above 0.50 at low dose and under 0.15 above ~6.5 mg.
    The registry's single 0.50 cannot express that, so the verdict must not read
    as 'the seed has nothing'.
    """
    copper = next(r for r in reconcile_with_registry() if r.mineral_id == "cu")
    assert copper.verdict == "dose_dependent"
    assert bounds_by_mineral()["cu"].dose_response["shape"] == "strongly_dose_dependent"


def test_calcium_is_flagged_for_reanchoring():
    """The seed disowns its own calcium figure, and the registry already agrees.

    Kohlmeier's >40% reads high for adults; the DRI-era figure is 0.25–0.30, which
    is what MINERAL_REGISTRY already holds. The seed must not be imported over it.
    """
    calcium = next(r for r in reconcile_with_registry() if r.mineral_id == "ca")
    assert calcium.verdict == "reanchor"
    assert "do not admit as bound" in calcium.note
    assert MINERAL_REGISTRY["ca"].typical_bioavailability == 0.30
    assert bounds_by_mineral()["ca"].needs_reanchor


def test_iron_has_no_sourced_prior_at_all():
    """The mineral the interaction rules lean on hardest is the one with no source."""
    assert "fe" in unsourced_minerals()
    assert absorption_prior("fe") is None
    assert MINERAL_REGISTRY["fe"].typical_bioavailability == 0.10


def test_absorption_prior_returns_the_scoped_bound():
    zinc = absorption_prior("zn")
    assert zinc is not None
    assert zinc.dose_ref_mg == 3
    assert zinc.parent_doi == "10.1093/jn/130.5.1378S"
    assert zinc.fraction.point == 0.70


def test_vitamin_entries_are_not_forced_into_the_mineral_registry():
    """`vit.*` entries belong to the vitamin module; they must not map to minerals."""
    vitamins = [b for b in absorption_bounds() if b.nutrient.startswith("vit.")]
    assert vitamins
    assert all(b.mineral_id is None for b in vitamins)
