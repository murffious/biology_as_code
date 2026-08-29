"""
LAW-004 in AO form.

These tests cite AO step numbers, which is the point of numbering them: a
failure says which step of the law is wrong, not that "iron absorption is off".
See ``docs/notational-conventions.md``.
"""

from __future__ import annotations

import pytest

from biology_as_code.engine.laws.ao import LAW_004_AO, UncertaintyCompletion, apply_law_004
from biology_as_code.engine.laws.ao.law_004 import (
    LAW_004_ASCORBATE_FOLD_BOUNDS,
    LAW_004_DOSE_BOUNDS_MG,
    OutOfKingdom,
)

# --- the AO form itself -------------------------------------------------------


def test_the_law_is_an_ordered_numbered_list():
    numbers = [step.number for step in LAW_004_AO]
    assert numbers == ["AO-004.1", "AO-004.2", "AO-004.3", "AO-004.4", "AO-004.5"]
    assert all(step.law_id == "LAW-004" for step in LAW_004_AO)


def test_every_step_declares_reads_writes_and_uncertainty():
    """A step that does not say what it does when an input is missing is incomplete."""
    for step in LAW_004_AO:
        assert step.reads, step.number
        assert step.writes, step.number
        assert step.effect, step.number
        assert step.uncertainty, step.number


def test_no_step_is_withdrawn_yet():
    assert not [s for s in LAW_004_AO if s.is_withdrawn]


# --- AO-004.1 domain boundary -------------------------------------------------


def test_ao_004_1_refuses_haem_iron_rather_than_widening():
    """
    The domain boundary uses `!`, not `?`. Applying an ascorbate fold to haem
    iron is not a wide answer, it is a wrong one.
    """
    with pytest.raises(OutOfKingdom, match="outside the law's domain"):
        apply_law_004(lumen_fe=1.0, species="haem", ascorbate_same_meal=True)


def test_ao_004_1_admits_non_haem():
    result = apply_law_004(lumen_fe=1.0, species="nonhaem", ascorbate_same_meal=False)
    assert "AO-004.1" in result.steps_run


# --- AO-004.2 concurrency before the fold -------------------------------------


def test_ao_004_2_runs_before_ao_004_3():
    """
    Ordering is normative. Ascorbate two hours later is not a smaller effect,
    it is no effect, so concurrency must be settled before the fold applies.
    """
    result = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=500)
    assert result.steps_run.index("AO-004.2") < result.steps_run.index("AO-004.3")


def test_ao_004_2_unknown_timing_is_contested_not_absent():
    """`None` timing is not the same as no ascorbate: the state records the gap."""
    unknown = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=None)
    absent = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=False)

    assert unknown.yield_completion.state == "contested"
    assert absent.yield_completion.state == "normal"
    # Neither applies a fold, but only one of them admits it does not know.
    assert unknown.delivered_fe == absent.delivered_fe


def test_ao_004_3_does_not_run_when_concurrency_is_false():
    result = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=False)
    assert "AO-004.3" not in result.steps_run
    assert any("precondition" in line for line in result.log)


# --- AO-004.3 the ? operator --------------------------------------------------


def test_ao_004_3_widens_rather_than_defaulting_when_the_dose_is_unknown():
    """
    Ascorbate present but unquantified is the `?` case: the fold widens to the
    law's stated range instead of picking a plausible number.
    """
    result = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=None)
    completion = result.yield_completion
    assert completion.state == "contested"
    assert completion.bounds == LAW_004_ASCORBATE_FOLD_BOUNDS
    assert "widened" in completion.note


def test_ao_004_3_dose_maps_between_the_two_cited_anchors():
    """~2x at an orange-juice dose (Rossander), ~10x at the tea-rescue dose (Derman)."""
    juice = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=75)
    rescue = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=1000)
    assert juice.delivered_fe == pytest.approx(2.0, rel=0.05)
    assert rescue.delivered_fe == pytest.approx(10.0, rel=0.05)
    assert juice.delivered_fe < rescue.delivered_fe


def test_ao_004_3_rejects_a_dose_outside_the_normative_host_bounds():
    """Host-defined means host-supplied within a stated range, not unconstrained."""
    with pytest.raises(ValueError, match="normative host-defined bounds"):
        apply_law_004(
            lumen_fe=1.0,
            ascorbate_same_meal=True,
            ascorbate_dose_mg=LAW_004_DOSE_BOUNDS_MG[1] + 1,
        )


# --- AO-004.4 "can overcome" is arithmetic ------------------------------------


def test_ao_004_4_applies_both_modifiers_multiplicatively():
    """
    Under Derman's conditions ascorbate nets above the tea-free baseline. It
    does so by arithmetic, not by winning a precedence fight — and the tannin
    fold is still applied.
    """
    baseline = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=False)
    tea_only = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=False, tannin_same_meal=True)
    tea_plus_c = apply_law_004(
        lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=1000, tannin_same_meal=True
    )

    assert tea_only.delivered_fe < baseline.delivered_fe, "tannin must narrow"
    assert tea_plus_c.delivered_fe > baseline.delivered_fe, (
        "ascorbate must overcome tannin at the rescue dose"
    )
    # And it overcame it by multiplying, not by suppressing the inhibitor.
    no_tea_plus_c = apply_law_004(
        lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=1000
    )
    assert tea_plus_c.delivered_fe < no_tea_plus_c.delivered_fe, (
        "tannin was skipped rather than applied — 'can overcome' was read as precedence"
    )


def test_ao_004_4_at_a_low_dose_ascorbate_does_not_overcome_tannin():
    """
    The reason precedence is the wrong encoding: at a juice-sized dose against
    tea, the product lands close to baseline rather than above it.
    """
    baseline = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=False)
    juice_with_tea = apply_law_004(
        lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=75, tannin_same_meal=True
    )
    assert juice_with_tea.delivered_fe == pytest.approx(baseline.delivered_fe * 2.0 * 0.55)
    assert juice_with_tea.delivered_fe < 2.0


# --- AO-004.5 emission --------------------------------------------------------


def test_ao_004_5_emits_a_flux_carrying_the_law_ids():
    result = apply_law_004(
        lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=500, tannin_same_meal=True
    )
    assert result.flux is not None
    assert "LAW-004" in result.flux.law_ids
    assert "LAW-006" in result.flux.law_ids, "the tannin law must be cited when it fired"
    assert result.flux.source == "small_intestine"
    assert result.flux.sink == "portal"


def test_ao_004_5_carries_a_contested_state_across_the_boundary():
    """Uncertainty is not dropped at emission."""
    result = apply_law_004(lumen_fe=1.0, ascorbate_same_meal=True, ascorbate_dose_mg=None)
    assert result.yield_completion.state == "contested"
    assert "contested" in result.flux.note


# --- the uncertainty record ---------------------------------------------------


def test_a_value_without_bounds_is_malformed():
    with pytest.raises(ValueError, match="must carry bounds"):
        UncertaintyCompletion(state="normal", value=2.0)


def test_the_question_operator_may_only_widen():
    narrow = UncertaintyCompletion(state="normal", value=2.0, bounds=(1.5, 10.0))
    assert narrow.widen((1.0, 12.0)).bounds == (1.0, 12.0)
    with pytest.raises(ValueError, match="may only widen"):
        narrow.widen((2.0, 3.0))


def test_widening_marks_the_result_contested():
    known = UncertaintyCompletion(state="normal", value=1.0, bounds=(1.0, 1.0))
    assert known.widen((0.5, 2.0)).state == "contested"


# --- the law stays connected to the registry ----------------------------------


def test_the_ao_form_matches_the_registry_record():
    """The AO form is a rewrite of LAW-004, not a fork of it."""
    from biology_as_code.engine.laws.registry import load_system_bound_registry

    law = load_system_bound_registry().get("LAW-004")
    assert law.functional_system == "Assimilation"
    assert "EXPANDS_BOUND" in law.relation_type
    assert "ascorbic acid" in law.law_statement.lower()
    # The bound text is where the fold interval comes from.
    assert "10" in law.bound_text and "2" in law.bound_text


# --- intrinsics ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("%GLP1%", "signals.glp1"),
        ("%CCK%", "signals.cck"),
        ("%GHRELIN%", "signals.ghrelin"),
        ("%Stomach%", "compartments.stomach"),
        ("%Duodenum%", None),  # named in the doc; no ORGAN_BOUNDS entry yet
        ("%GlycemicResponse%", "responses.GlycemicResponse/1.0"),
    ],
)
def test_intrinsics_resolve_against_the_real_catalogs(token, expected):
    """
    `%NAME%` is checkable, which is the whole difference from prose. Note
    `%Duodenum%`: the notation document names it, ORGAN_BOUNDS models the small
    intestine as one compartment, and so it does not resolve. That is the
    resolver doing its job — the gap is real and now visible.
    """
    from biology_as_code.engine.parameters import resolve_intrinsic

    if expected is None:
        with pytest.raises(KeyError):
            resolve_intrinsic(token)
    else:
        assert resolve_intrinsic(token) == expected


def test_an_unresolvable_intrinsic_is_a_defect_not_a_passthrough():
    from biology_as_code.engine.parameters import resolve_intrinsic

    with pytest.raises(KeyError, match="does not resolve"):
        resolve_intrinsic("%Unicorn%")
    with pytest.raises(ValueError, match="not an intrinsic"):
        resolve_intrinsic("GLP1")
