"""
The ten kinds, exercised.

Each kind in the VHM catalog gets at least one test that would fail if the type
stopped meaning what it says. The point is not coverage of every method — it is
that the *distinctions* the types were introduced to make are actually enforced
somewhere, rather than living only in a docstring.
"""

from __future__ import annotations

import pytest

from biology_as_code.engine.clocks import CLOCK_ORDER, Clock, is_faster_than
from biology_as_code.engine.compartments import (
    Admission,
    Compartment,
    ExoticCompartment,
    SimpleCompartment,
    compartment_registry,
)
from biology_as_code.engine.fluxes import SINK_EXTERNAL, SOURCE_EXTERNAL, Flux, FluxSet
from biology_as_code.engine.laws.models import CONSERVING_RELATIONS
from biology_as_code.engine.laws.registry import load_system_bound_registry
from biology_as_code.engine.modifiers import BindingRegistry, ModifierBinding
from biology_as_code.engine.pathways import COLON_FERMENTATION
from biology_as_code.engine.processes import Context, PacketState, Process, ProcessResult
from biology_as_code.engine.signals import (
    SIGNALS,
    ExogenousSignal,
    get_signal,
    signals_from_medication_profile,
)
from biology_as_code.packets import get_packet


class _DictHost:
    """Minimal HostStateLike over a flat dotted-path dict."""

    def __init__(self, values: dict | None = None):
        self._values = values or {}

    def get(self, path: str, default=None):
        return self._values.get(path, default)


# --- Kind 1: Packet -----------------------------------------------------------


def test_method_identity_is_what_separates_whole_from_flour():
    """Identity and analyte panel agree; only the method identity differs."""
    whole = get_packet("ex.almond.whole")
    flour = get_packet("ex.almond.flour")

    assert whole.identity["family_hint"] == flour.identity["family_hint"]
    assert whole.cargo_nutrients() == flour.cargo_nutrients()
    assert whole.method_ops() != flour.method_ops()
    assert "mill" in flour.method_ops()
    assert "mill" not in whole.method_ops()
    assert flour.matrix_destroyed_by_processing
    assert not whole.matrix_destroyed_by_processing


def test_absent_method_identity_is_not_the_same_as_no_processing():
    """An undeclared food must not read as raw."""
    undeclared = get_packet("ex.spinach_salad.zero_fat")
    declared = get_packet("ex.almond.whole")
    assert not undeclared.declares_method_identity
    assert undeclared.method_ops() == ()
    assert declared.declares_method_identity


def test_method_identity_order_is_preserved():
    bread = get_packet("ex.white.bread.upf")
    ops = bread.method_ops()
    assert ops.index("mill") < ops.index("bake")


# --- Kind 2: Compartment ------------------------------------------------------


def test_default_compartments_satisfy_the_protocol():
    registry = compartment_registry()
    assert registry, "no default compartments built from ORGAN_BOUNDS"
    for comp in registry.values():
        assert isinstance(comp, Compartment)


def test_compartment_admission_uses_bounds():
    stomach = compartment_registry()["stomach"]
    host, ctx = _DictHost(), Context()
    assert stomach.accept(PacketState("x", ph=2.0), host, ctx)
    assert not stomach.accept(PacketState("x", ph=7.0), host, ctx)


def test_unmeasured_ph_is_admitted_as_unknown_not_rejected():
    """Absence of a measurement is a gap, not a failure."""
    stomach = compartment_registry()["stomach"]
    admission = stomach.accept(PacketState("x", ph=None), _DictHost(), Context())
    assert admission.admitted
    assert "unchecked" in admission.reason


def test_post_surgical_is_an_exotic_compartment_that_can_remove_topology():
    """A bypass removes a segment from the path; no multiplier expresses that."""
    default = compartment_registry()["stomach"]
    sleeve = ExoticCompartment(
        id="stomach.post_sleeve",
        overrides="stomach",
        delegate=SimpleCompartment(
            id="stomach.post_sleeve",
            downstream=("small_intestine", "large_intestine"),
            ph_range=(1.5, 4.5),
        ),
        reason="sleeve gastrectomy: reduced reservoir volume and acid output",
        bypasses=("small_intestine",),
        evidence_state="supported",
    )
    assert isinstance(sleeve, Compartment)
    assert "small_intestine" in default.downstream
    result = sleeve.transform(PacketState("x"), _DictHost(), Context())
    assert sleeve.emit(result) == ("large_intestine",)
    assert any("overrode stomach" in line for line in result.log)


def test_an_exotic_compartment_must_say_why_it_overrides():
    with pytest.raises(ValueError, match="why it overrides"):
        ExoticCompartment(
            id="x",
            overrides="stomach",
            delegate=SimpleCompartment(id="x"),
            reason="   ",
        )


# --- Kind 3: Process ----------------------------------------------------------


def test_the_scfa_pathway_satisfies_the_process_protocol():
    assert isinstance(COLON_FERMENTATION, Process)


def test_process_returns_packet_signals_and_fluxes():
    packet = PacketState("meal", cargo={"fermentable_substrate": 10.0})
    host = _DictHost(
        {"fast_state.fermentable_fraction": 0.7, "slow_state.microbiome_diversity": 0.8}
    )
    result = COLON_FERMENTATION(packet, host, Context(clock=Clock.MEAL, dt_seconds=6 * 3600))

    assert isinstance(result, ProcessResult)
    assert result.packet.amount("scfa") > 0
    assert set(result.signals) <= set(SIGNALS)
    assert result.fluxes
    assert "colon.fermentation" in result.packet.method_identity


def test_a_process_does_not_mutate_its_input_packet():
    packet = PacketState("meal", cargo={"fermentable_substrate": 10.0})
    before = dict(packet.cargo)
    COLON_FERMENTATION(packet, _DictHost(), Context(dt_seconds=3600))
    assert dict(packet.cargo) == before
    assert packet.method_identity == ()


def test_fermentation_cannot_create_substrate():
    """Enhancers raise conversion efficiency, not mass."""
    packet = PacketState("meal", cargo={"fermentable_substrate": 10.0})
    host = _DictHost(
        {"fast_state.fermentable_fraction": 0.9, "slow_state.microbiome_diversity": 0.95}
    )
    result = COLON_FERMENTATION(packet, host, Context(dt_seconds=3600))
    assert result.packet.amount("scfa") <= 10.0
    assert result.packet.amount("fermentable_substrate") >= 0.0


def test_explicit_context_flags_override_host_derived_ones():
    packet = PacketState("meal", cargo={"fermentable_substrate": 10.0})
    # Dysbiotic host, so both walks land below a yield factor of 1 and the
    # substrate clip does not mask the difference.
    host = _DictHost(
        {"fast_state.fermentable_fraction": 0.9, "slow_state.microbiome_diversity": 0.3}
    )
    pinned = COLON_FERMENTATION(
        packet, host, Context(dt_seconds=3600, flags={"high_fermentable_fraction": False})
    )
    free = COLON_FERMENTATION(packet, host, Context(dt_seconds=3600))
    assert pinned.packet.amount("scfa") < free.packet.amount("scfa")


# --- Kind 4: Law --------------------------------------------------------------


def test_laws_carry_evidence_state_and_review_scheduling():
    reg = load_system_bound_registry()
    for law in reg.all():
        assert law.evidence_state in ("verified", "supported", "contested", "candidate")
    assert reg.qa()["ok"]


def test_unannotated_laws_default_to_candidate_not_verified():
    """Introducing the field must not silently promote the whole registry."""
    reg = load_system_bound_registry()
    assert reg.by_evidence("candidate"), "expected unannotated laws to read as candidate"
    assert not reg.by_evidence("verified"), (
        "no law has been curated as verified yet; a verified law here means the "
        "default flipped the wrong way"
    )


def test_due_for_review_excludes_unscheduled_laws():
    reg = load_system_bound_registry()
    due = reg.due_for_review("2099-01-01")
    assert all(law.review_scheduled for law in due)
    assert len(due) < len(reg.all())


# --- The RelationType fix: CONSERVES ------------------------------------------


def test_a_balance_law_is_typed_conserves():
    """
    LAW-039 asserts the bile-acid pool is conserved across the enterohepatic
    loop. It was filed EXPANDS_BOUND only because no conservation relation
    existed in the vocabulary.
    """
    reg = load_system_bound_registry()
    law = reg.get("LAW-039")
    assert law.relation_type == "CONSERVES"
    assert law.is_conserving
    assert law in reg.conserving()
    assert "conserved" in law.law_statement.lower()


def test_conserves_is_checkable_by_closing_the_flux_balance():
    """
    The point of the relation type: a CONSERVES law makes a claim you can test.
    ~98% of the bile-acid pool is reabsorbed at the ileum and the remainder is
    lost in faeces; if the two account for everything that left, the pool is
    conserved and the residual is zero.
    """
    reg = load_system_bound_registry()
    assert reg.get("LAW-039").relation_type in CONSERVING_RELATIONS

    pool_rate = 100.0  # arbitrary units per hour leaving the liver
    reabsorbed, faecal_loss = 98.0, 2.0
    fluxes = FluxSet(
        [
            Flux("bile_acid", "liver_gallbladder", "small_intestine", pool_rate,
                 law_ids=("LAW-039",)),
            Flux("bile_acid", "small_intestine", "liver_gallbladder", reabsorbed,
                 law_ids=("LAW-039",)),
            Flux("bile_acid", "small_intestine", SINK_EXTERNAL, faecal_loss,
                 law_ids=("LAW-039",)),
            # The other half of LAW-039: what is lost in faeces is made good by
            # hepatic synthesis from cholesterol. Without this flux the loop
            # does not close, which is the law's second clause stated as a
            # balance rather than as prose.
            Flux("bile_acid", SOURCE_EXTERNAL, "liver_gallbladder", faecal_loss,
                 law_ids=("LAW-021", "LAW-039"),
                 note="de novo synthesis from cholesterol"),
        ]
    )
    report = fluxes.balance_report("bile_acid")
    assert report["closed"], report
    assert report["unbalanced"] == []
    assert report["external_out_per_s"] == pytest.approx(report["external_in_per_s"])


def test_an_unclosed_balance_is_reported_as_unclosed():
    """A CONSERVES claim that leaks must fail, or the type buys nothing."""
    leaky = FluxSet(
        [
            Flux("bile_acid", "liver_gallbladder", "small_intestine", 100.0),
            Flux("bile_acid", "small_intestine", "liver_gallbladder", 50.0),
        ]
    )
    report = leaky.balance_report("bile_acid")
    assert not report["closed"]
    assert set(report["unbalanced"]) == {"liver_gallbladder", "small_intestine"}
    assert report["residual_per_s"] > 0


def test_closure_is_not_satisfied_by_construction():
    """
    Summing net rates over every compartment is identically zero for any flux
    set, so a closure check built on that sum passes for a model that pumps a
    substance into a dead end. This pins the stronger check.
    """
    dead_end = FluxSet([Flux("x", "a", "b", 7.0)])
    report = dead_end.balance_report("x")
    assert sum(report["compartments"].values()) == pytest.approx(0.0)
    assert not report["closed"]


# --- Kind 6: Modifier ---------------------------------------------------------


def test_modifier_binding_requires_a_binding_site():
    with pytest.raises(ValueError, match="binding_site is required"):
        ModifierBinding(
            id="x",
            modifier="ascorbate",
            binding_site="  ",
            effect_direction="increase",
            relation="EXPANDS_BOUND",
            evidence_state="supported",
        )


def test_direction_and_magnitude_must_agree():
    with pytest.raises(ValueError, match="direction 'increase'"):
        ModifierBinding(
            id="x",
            modifier="ascorbate",
            binding_site="processes.iron.reduction_factor",
            effect_direction="increase",
            effect_magnitude=0.5,
            relation="EXPANDS_BOUND",
            evidence_state="supported",
        )


def test_direction_only_bindings_are_legitimate():
    binding = ModifierBinding(
        id="x",
        modifier="variant",
        binding_site="processes.iron.reduction_factor",
        effect_direction="decrease",
        effect_magnitude=None,
        relation="NARROWS_BOUND",
        evidence_state="contested",
    )
    assert binding.is_direction_only
    assert binding.effective_magnitude() is None


def test_untrusted_magnitudes_do_not_reach_a_computation_by_default():
    binding = ModifierBinding(
        id="x",
        modifier="variant",
        binding_site="processes.iron.reduction_factor",
        effect_direction="decrease",
        effect_magnitude=0.7,
        relation="NARROWS_BOUND",
        evidence_state="candidate",
    )
    assert binding.effective_magnitude() is None
    assert binding.effective_magnitude(allow_untrusted=True) == 0.7


def test_binding_registry_rejects_duplicate_ids():
    reg = BindingRegistry()
    b = ModifierBinding(
        id="dup",
        modifier="m",
        binding_site="processes.a.b",
        effect_direction="unknown",
        relation="MIXED",
        evidence_state="candidate",
    )
    reg.add(b)
    with pytest.raises(ValueError, match="duplicate binding id"):
        reg.add(b)


# --- Kind 7: Signal -----------------------------------------------------------


def test_the_eight_named_signals_are_in_the_catalog():
    for name in ("ghrelin", "cck", "glp1", "gip", "pyy", "insulin", "glucagon", "leptin"):
        assert name in SIGNALS


def test_signals_resolve_by_alias():
    assert get_signal("GLP-1").id == "glp1"
    assert get_signal("PYY3-36").id == "pyy"
    assert get_signal("Cholecystokinin").id == "cck"


def test_an_unknown_signal_raises_rather_than_returning_none():
    with pytest.raises(KeyError, match="unknown signal"):
        get_signal("semaglutide")


def test_leptin_is_the_one_signal_off_the_meal_clock():
    assert SIGNALS["leptin"].clock is Clock.ADAPTATION
    meal_clocked = [s.id for s in SIGNALS.values() if s.clock is Clock.MEAL]
    assert len(meal_clocked) == len(SIGNALS) - 1


def test_a_medication_is_an_exogenous_signal_not_a_hormone():
    profile = {
        "medications": [
            {"id": "glp1_ra", "name": "GLP-1 receptor agonist", "acts_on": "GLP-1",
             "mode": "agonist", "route": "subcutaneous"}
        ]
    }
    signals = signals_from_medication_profile(profile)
    assert len(signals) == 1
    exo = signals[0]
    assert isinstance(exo, ExogenousSignal)
    assert exo.id not in SIGNALS, "a medication must not enter the endogenous catalog"
    assert exo.acts_on == "glp1"
    assert exo.resolved_target() is SIGNALS["glp1"]
    assert exo.clock is Clock.EVENT


def test_an_unresolvable_medication_target_is_carried_not_dropped():
    signals = signals_from_medication_profile(
        {"medications": [{"id": "mystery", "acts_on": "unobtainium"}]}
    )
    assert len(signals) == 1
    assert signals[0].acts_on is None
    assert "unresolved target" in signals[0].note


# --- Kind 8: State (clock typing) ---------------------------------------------


def test_the_six_clocks_exist():
    assert {c.value for c in Clock} == {
        "fixed",
        "adaptation",
        "diurnal",
        "meal",
        "bite",
        "event",
    }


def test_clocks_are_ordered_by_speed():
    assert is_faster_than(Clock.BITE, Clock.MEAL)
    assert is_faster_than(Clock.MEAL, Clock.DIURNAL)
    assert is_faster_than(Clock.DIURNAL, Clock.ADAPTATION)
    assert not is_faster_than(Clock.FIXED, Clock.BITE)
    assert Clock.EVENT not in CLOCK_ORDER


def test_event_cannot_be_ordered_against_a_periodic_clock():
    with pytest.raises(ValueError, match="aperiodic"):
        is_faster_than(Clock.EVENT, Clock.MEAL)


def test_metabolic_state_carries_a_clock():
    from biology_as_code.engine.sim.state import MetabolicState

    assert MetabolicState().clock is Clock.MEAL


# --- Kind 9: Flux -------------------------------------------------------------


def test_a_rate_is_not_an_amount():
    flux = Flux("glucose", "small_intestine", "portal", 12.0, substance_unit="g", time_unit="per_h")
    assert flux.rate == 12.0
    assert flux.amount_over(3600) == pytest.approx(12.0)
    assert flux.amount_over(1800) == pytest.approx(6.0)
    assert flux.unit == "g/h"


def test_negative_rates_are_rejected_in_favour_of_swapping_endpoints():
    with pytest.raises(ValueError, match="swap source and sink"):
        Flux("glucose", "a", "b", -1.0)
    forward = Flux("glucose", "a", "b", 5.0)
    assert forward.reversed().source == "b"


def test_a_flux_cannot_loop_on_one_compartment():
    with pytest.raises(ValueError, match="same compartment"):
        Flux("glucose", "liver", "liver", 1.0)


def test_net_rate_is_gain_minus_loss():
    fluxes = FluxSet(
        [
            Flux("scfa", "large_intestine", "portal", 10.0),
            Flux("scfa", "portal", "liver", 4.0),
        ]
    )
    assert fluxes.net_rate("portal", "scfa") == pytest.approx(6.0 / 3600.0)


# --- Kind 10: Response --------------------------------------------------------


def test_glycemic_response_is_versioned_and_executable():
    from biology_as_code.responses import GLYCEMIC_RESPONSE_V1, Sample

    samples = [Sample(0, 5.0), Sample(30, 8.0), Sample(60, 7.0), Sample(90, 5.5), Sample(120, 5.0)]
    result = GLYCEMIC_RESPONSE_V1.compute(samples)
    assert result.protocol == "GlycemicResponse/1.0"
    assert result.value > 0
    assert result.detail["baseline"] == 5.0
    assert result.detail["peak_minutes"] == 30


def test_iauc_discards_area_below_baseline():
    """iAUC and net AUC differ in anyone with a reactive dip; this fixes which."""
    from biology_as_code.responses import GLYCEMIC_RESPONSE_V1, Sample, incremental_auc

    dipping = [Sample(0, 5.0), Sample(30, 8.0), Sample(60, 5.0), Sample(90, 3.0), Sample(120, 5.0)]
    flat_after = [
        Sample(0, 5.0), Sample(30, 8.0), Sample(60, 5.0), Sample(90, 5.0), Sample(120, 5.0)
    ]
    # The dip contributes nothing, so both series have the same iAUC.
    assert incremental_auc(dipping, 5.0) == pytest.approx(incremental_auc(flat_after, 5.0))
    assert GLYCEMIC_RESPONSE_V1.compute(dipping).value > 0


def test_iauc_counts_only_the_above_baseline_part_of_a_crossing_segment():
    from biology_as_code.responses import Sample, incremental_auc

    # Straight line from +2 down to -2 over 60 min: above-baseline triangle is
    # half the interval, height 2 → 0.5 * 2 * 30 = 30.
    crossing = [Sample(0, 7.0), Sample(60, 3.0)]
    assert incremental_auc(crossing, 5.0) == pytest.approx(30.0)


def test_glycemic_response_refuses_to_guess_a_baseline():
    from biology_as_code.responses import GLYCEMIC_RESPONSE_V1, Sample

    with pytest.raises(ValueError, match="requires a sample at t=0"):
        GLYCEMIC_RESPONSE_V1.compute([Sample(15, 8.0), Sample(60, 6.0)])


def test_samples_outside_the_window_are_excluded_loudly():
    from biology_as_code.responses import GLYCEMIC_RESPONSE_V1, Sample

    result = GLYCEMIC_RESPONSE_V1.compute(
        [Sample(0, 5.0), Sample(30, 8.0), Sample(60, 6.0), Sample(120, 5.0), Sample(180, 5.0)]
    )
    assert result.detail["n_samples_excluded"] == 1
    assert any("beyond the 120-minute window" in w for w in result.warnings)


def test_classification_is_ordinal_and_protocol_matched():
    from biology_as_code.responses import GLYCEMIC_RESPONSE_V1, GlycemicResponse, Sample

    reference = GLYCEMIC_RESPONSE_V1.compute(
        [Sample(0, 5.0), Sample(30, 9.0), Sample(60, 7.0), Sample(120, 5.0)]
    )
    lower = GLYCEMIC_RESPONSE_V1.compute(
        [Sample(0, 5.0), Sample(30, 6.0), Sample(60, 5.5), Sample(120, 5.0)]
    )
    assert GLYCEMIC_RESPONSE_V1.classify_against(lower, reference).classification == "lower"

    other_protocol = GlycemicResponse(protocol_id="GlycemicResponse/9.9")
    foreign = other_protocol.compute([Sample(0, 5.0), Sample(30, 9.0), Sample(120, 5.0)])
    with pytest.raises(ValueError, match="different protocols"):
        GLYCEMIC_RESPONSE_V1.classify_against(foreign, reference)


@pytest.mark.parametrize("response_cls", ["SatietyResponse", "LipemicResponse"])
def test_declared_but_unexecutable_responses_raise_rather_than_return_zero(response_cls):
    import biology_as_code.responses as responses
    from biology_as_code.responses import ResponseNotExecutable, Sample

    protocol = getattr(responses, response_cls)()
    with pytest.raises(ResponseNotExecutable):
        protocol.compute([Sample(0, 1.0)])


# --- Kind 5: Gate / Bound (already present; pinned here for completeness) ------


def test_gates_and_bounds_are_still_the_existing_ones():
    """The catalog adds kinds; it does not replace the two that already worked."""
    from biology_as_code.audit import gates  # noqa: F401
    from biology_as_code.engine.geography.organ_bounds import ORGAN_BOUNDS

    assert ORGAN_BOUNDS["stomach"].pH_range == (1.5, 3.5)
    assert isinstance(
        compartment_registry()["stomach"].accept(PacketState("x", ph=2.0), _DictHost(), Context()),
        Admission,
    )
