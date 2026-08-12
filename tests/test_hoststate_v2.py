"""
HostState v2: five strata, four facets, and bindings that resolve.

The tests that matter here are the ones that would catch v2 drifting away from
v1 (a property silently dropped in the restratification), a facet quietly going
missing, or a binding pointing at an engine parameter that no longer exists.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from biology_as_code.engine.parameters import parameter_space, resolve_binding

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "src" / "biology_as_code" / "machines" / "data" / "schemas"
V1_PATH = SCHEMA_DIR / "HostState.schema.json"
V2_PATH = SCHEMA_DIR / "HostState.v2.schema.json"
GENOME_SEED = REPO_ROOT / "design" / "genome_modifier_seed.json"

STRATA = ("constants", "slow_state", "fast_state", "context_stream", "response_history")
FACETS = ("x-binding_site", "x-clock", "x-tier", "x-evidence_state")
CLOCKS = {"fixed", "adaptation", "diurnal", "meal", "bite", "event"}
TIERS = {"T0", "T1", "T2", "T3", "T4"}
EVIDENCE = {"verified", "supported", "contested", "candidate"}

#: v1 properties that are structural rather than host data, so they do not map
#: into a stratum.
_NON_DATA_V1 = {"schema", "honesty"}


def v1() -> dict:
    return json.loads(V1_PATH.read_text(encoding="utf-8"))


def v2() -> dict:
    return json.loads(V2_PATH.read_text(encoding="utf-8"))


def _v2_fields() -> dict[str, tuple[str, dict]]:
    """Every stratum field as ``name -> (stratum, schema)``."""
    out: dict[str, tuple[str, dict]] = {}
    for stratum in STRATA:
        for name, schema in v2()["properties"][stratum]["properties"].items():
            assert name not in out, f"{name} appears in two strata"
            out[name] = (stratum, schema)
    return out


# --- the strata ---------------------------------------------------------------


def test_v2_has_exactly_the_five_strata():
    props = v2()["properties"]
    assert [k for k in props if k in STRATA] == list(STRATA)


def test_v1_still_exists_and_is_untouched():
    """v2 is additive. Existing consumers read v1 and must keep working."""
    assert V1_PATH.is_file()
    assert v1()["properties"]["schema"]["const"] == "bac.HostState/v1"


def test_every_v1_property_lands_in_a_stratum():
    """The restratification must not lose a field."""
    v2_fields = _v2_fields()
    missing = [
        name
        for name in v1()["properties"]
        if name not in _NON_DATA_V1 and name not in v2_fields
    ]
    assert not missing, f"v1 properties dropped from v2: {missing}"


def test_v1_fields_are_stratified_by_rate_of_change():
    """Spot-check that the mapping is by clock, not alphabetical."""
    fields = _v2_fields()
    assert fields["age_years"][0] == "constants"
    assert fields["body_fat_percent"][0] == "slow_state"
    assert fields["acid_capacity"][0] == "slow_state"
    assert fields["hydration_status"][0] == "fast_state"
    assert fields["ready"][0] == "fast_state"


# --- the four facets ----------------------------------------------------------


def test_every_field_carries_all_four_facets():
    problems = []
    for name, (stratum, schema) in _v2_fields().items():
        for facet in FACETS:
            if facet not in schema:
                problems.append(f"{stratum}.{name} missing {facet}")
    assert not problems, problems


def test_facet_values_come_from_the_declared_vocabularies():
    for name, (stratum, schema) in _v2_fields().items():
        where = f"{stratum}.{name}"
        assert schema["x-clock"] in CLOCKS, where
        assert schema["x-tier"] in TIERS, where
        assert schema["x-evidence_state"] in EVIDENCE, where


def test_an_unbound_field_declares_null_rather_than_omitting_the_facet():
    """
    Omitting the facet and declaring it null are different claims. Omission is
    indistinguishable from forgetting; an explicit null says a human decided.
    """
    fields = _v2_fields()
    unbound = [n for n, (_, s) in fields.items() if s["x-binding_site"] is None]
    assert unbound, "expected some fields to be carried without an engine binding"
    for name in unbound:
        assert "x-binding_site" in fields[name][1]


def test_eating_rate_is_the_bite_clock_field():
    """Texture acts at the bite clock; modelling it per-meal loses the mechanism."""
    stratum, schema = _v2_fields()["eating_rate_g_per_min"]
    assert schema["x-clock"] == "bite"
    assert stratum == "fast_state"


# --- bindings resolve ---------------------------------------------------------


def test_every_declared_binding_resolves_to_an_engine_parameter():
    space = parameter_space()
    dangling = []
    for name, (stratum, schema) in _v2_fields().items():
        site = schema["x-binding_site"]
        if site is not None and site not in space:
            dangling.append(f"{stratum}.{name} -> {site}")
    assert not dangling, f"dangling bindings: {dangling}"


def test_the_resolver_tool_passes():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "resolve_bindings", REPO_ROOT / "tools" / "resolve_bindings.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.check()
    assert report["ok"], report["defects"]
    assert report["n_dangling"] == 0
    assert report["n_bound"] > 0


def test_the_resolver_would_actually_catch_a_dangling_binding():
    """A check that cannot fail is not a check."""
    with pytest.raises(KeyError, match="does not resolve"):
        resolve_binding("processes.nonhaem_iron.fe.no_such_node.context.nonsense")


def test_the_parameter_space_is_derived_from_the_engine_not_a_hand_list():
    """
    Deleting a modifier must delete its binding site. If the space were a
    hand-maintained list this would keep passing after the modifier was gone.
    """
    space = parameter_space()
    from biology_as_code.engine.pathways.nonhaem_iron import NONHAEM_IRON_PATHWAY

    node = NONHAEM_IRON_PATHWAY["fe.lumen_speciation"]
    keys = {m.requires_context for m in (*node.inhibitors, *node.enhancers)}
    for key in keys:
        assert f"processes.nonhaem_iron.fe.lumen_speciation.context.{key}" in space
    assert "processes.nonhaem_iron.fe.lumen_speciation.context.unicorn" not in space


# --- genome as bindings only --------------------------------------------------


def test_genome_enters_only_as_modifier_bindings():
    genome = _v2_fields()["genome"]
    stratum, schema = genome
    assert stratum == "constants"
    assert schema["items"]["$ref"] == "#/$defs/modifierBinding"
    # There must be no bare genotype field anywhere in the schema.
    all_names = set(_v2_fields())
    assert not {"genotype", "genotypes", "variants", "snps"} & all_names


def test_genome_seed_rows_are_valid_modifier_bindings():
    from biology_as_code.engine.modifiers import BindingRegistry, ModifierBinding

    seed = json.loads(GENOME_SEED.read_text(encoding="utf-8"))
    registry = BindingRegistry()
    for row in seed["bindings"]:
        registry.add(
            ModifierBinding(
                id=row["id"],
                modifier=row["modifier"],
                binding_site=row["binding_site"],
                effect_direction=row["effect_direction"],
                effect_magnitude=row.get("effect_magnitude"),
                relation=row["relation"],
                evidence_state=row["evidence_state"],
                law_ids=tuple(row.get("law_ids") or ()),
                requires_context=row.get("requires_context"),
                note=row.get("note", ""),
            )
        )
    assert len(registry) == len(seed["bindings"])
    for site in registry.sites():
        resolve_binding(site)


def test_seed_bindings_are_direction_only():
    """No genome row asserts a magnitude the literature does not support."""
    seed = json.loads(GENOME_SEED.read_text(encoding="utf-8"))
    for row in seed["bindings"]:
        assert row.get("effect_magnitude") is None, row["id"]


def test_unmodellable_variants_are_recorded_not_bound_to_a_wrong_parameter():
    """
    Three of the six seed candidates have no engine parameter to act on. They
    are listed as gaps with the missing parameter named, rather than bound to
    the nearest plausible path — which would resolve and be wrong.
    """
    seed = json.loads(GENOME_SEED.read_text(encoding="utf-8"))
    gaps = seed["unmodellable"]["variants"]
    assert gaps
    bound_modifiers = {row["modifier"] for row in seed["bindings"]}
    for gap in gaps:
        assert gap["needs_parameter"], gap["modifier"]
        assert gap["modifier"] not in bound_modifiers
        assert "binding_site" not in gap


# --- post_surgical as an exotic compartment ------------------------------------


def test_post_surgical_binds_to_a_compartment_not_a_scalar():
    stratum, schema = _v2_fields()["post_surgical"]
    assert schema["x-binding_site"] == "compartments.stomach"
    assert schema["x-clock"] == "event"
    assert "ExoticCompartment" in schema["description"]
