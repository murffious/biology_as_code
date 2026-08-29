"""
Five published human results the engine is required to reproduce.

Read ``README.md`` in this package before changing anything here. In short:
tolerances are part of the tests, they are never weakened to make something
pass, and the ``xfail`` markers are strict so that meeting a target cannot
happen silently.
"""

from __future__ import annotations

import pytest

from tests.conformance.harness import (
    MechanismMissing,
    atwater_kcal,
    packet_pair,
    predict_ad_libitum_intake_kcal,
    predict_energy,
    predict_ldl_response,
    predicted_glycemic_iauc,
    within_percentage_points,
    within_relative_tolerance,
)

# --------------------------------------------------------------------------
# 1. Hall 2019 — ultra-processing drives spontaneous intake
# --------------------------------------------------------------------------

HALL_TARGET_KCAL_PER_DAY = 508.0
HALL_TOLERANCE = 0.40  # ±40%


@pytest.mark.conformance
@pytest.mark.xfail(
    strict=True,
    reason=(
        "needs an oral (bite-clock) process, a gastric filling/emptying compartment, "
        "and an intake controller. The engine takes grams as input, so spontaneous "
        "intake cannot yet be an output."
    ),
)
def test_hall_2019_upf_drives_spontaneous_overconsumption():
    """
    Matched-analyte, matched-liking UPF versus unprocessed meal sequences,
    presented ad libitum, diverge in spontaneous energy intake by
    **+508 kcal/day** on the ultra-processed arm.

    This is the load-bearing result for the whole specification. The two arms
    were matched for presented energy, macronutrients, sugar, sodium and fibre,
    and for palatability ratings. Everything the analyte panel can see was held
    equal, and intake still diverged by half a thousand calories a day. A model
    whose only input is the panel cannot produce this number — not
    approximately, not in the right direction. Reproducing it is what it means
    for method identity to be real.

    Tolerance ±40%, i.e. 305–711 kcal/day. Wide on purpose: this is a
    fourteen-participant inpatient crossover and the effect size carries a
    substantial confidence interval. Narrowing it would be claiming precision
    the source does not have.

    Hall KD, Ayuketah A, Brychta R, et al. Ultra-processed diets cause excess
    calorie intake and weight gain: an inpatient randomized controlled trial of
    ad libitum food intake. Cell Metab. 2019;30(1):67-77.e3.
    doi:10.1016/j.cmet.2019.05.008
    """
    upf_intake = predict_ad_libitum_intake_kcal(
        ["ex.white.bread.upf", "ex.potato.chips.upf", "ex.soda.cola"], days=14
    )
    unprocessed_intake = predict_ad_libitum_intake_kcal(
        ["ex.oats.porridge.plain", "ex.chicken.breast", "ex.broccoli.steamed"], days=14
    )
    divergence = (upf_intake - unprocessed_intake) / 14.0

    assert divergence > 0, "UPF arm must consume more, not less"
    assert within_relative_tolerance(divergence, HALL_TARGET_KCAL_PER_DAY, HALL_TOLERANCE), (
        f"predicted {divergence:.0f} kcal/day divergence; "
        f"target {HALL_TARGET_KCAL_PER_DAY} ±{HALL_TOLERANCE:.0%}"
    )


# --------------------------------------------------------------------------
# 2. Novotny 2012 — the Atwater gap in whole almonds
# --------------------------------------------------------------------------

ALMOND_OVERESTIMATE_PERCENT = 32.0
ALMOND_TOLERANCE_POINTS = 10.0

#: Macros for a 100 g reference portion of almonds. Identical for both packets
#: — that is the point of the test.
ALMOND_100G = {"carbs_g": 21.6, "protein_g": 21.2, "fats_g": 49.9, "fiber_g": 12.5}


@pytest.mark.conformance
@pytest.mark.xfail(
    strict=True,
    reason=(
        "needs the encapsulation-gated bioaccessibility law. Absorption currently "
        "depends on grams alone, so whole almonds and almond flour — same panel, "
        "different method identity — return identical energy."
    ),
)
def test_novotny_2012_atwater_overestimates_whole_almond_energy():
    """
    Whole almonds deliver substantially less metabolizable energy than their
    analyte panel prices them at: measured ME ~4.6 kcal/g against ~6.0-6.1
    kcal/g by Atwater general factors, an overestimate of about **32%**.

    The mechanism is encapsulation. Almond lipid sits inside intact cotyledon
    cell walls; chewing fractures the tissue but leaves most cells unbroken, so
    a large fraction of the fat is never reachable by lipase and leaves in the
    faeces. Milling to flour destroys the cell walls and closes most of the
    gap — same species, same panel, different program.

    Two assertions, and both matter. The overestimate must be ~32% for the
    whole packet, and it must be materially smaller for flour. A model that
    produced a flat 32% shortfall for anything almond-shaped would hit the
    first and fail the second, which is how a fudge factor is distinguished
    from a mechanism.

    Tolerance ±10 percentage points on the overestimate (so 22-42%), not ±10%
    relative. Novotny JA, Gebauer SK, Baer DJ. Discrepancy between the Atwater
    factor predicted and empirically measured energy values of almonds in human
    diets. Am J Clin Nutr. 2012;96(2):296-301. doi:10.3945/ajcn.112.035782
    """
    whole, flour = packet_pair("ex.almond.whole", "ex.almond.flour")

    # Precondition: the two packets differ only in method identity.
    assert whole.cargo_nutrients() == flour.cargo_nutrients()
    assert "mill" in flour.method_ops() and "mill" not in whole.method_ops()

    whole_energy = predict_energy(whole, **ALMOND_100G)
    flour_energy = predict_energy(flour, **ALMOND_100G)

    assert whole_energy.label_kcal == pytest.approx(flour_energy.label_kcal), (
        "the two packets must price identically by panel — that is the premise"
    )

    assert within_percentage_points(
        whole_energy.overestimate_percent,
        ALMOND_OVERESTIMATE_PERCENT,
        ALMOND_TOLERANCE_POINTS,
    ), (
        f"whole almond overestimate {whole_energy.overestimate_percent:.1f}%; "
        f"target {ALMOND_OVERESTIMATE_PERCENT}% ±{ALMOND_TOLERANCE_POINTS} points"
    )

    assert flour_energy.overestimate_percent < whole_energy.overestimate_percent - 10.0, (
        "milling must close most of the gap; a flat shortfall for anything almond-"
        f"shaped is a fudge factor, not a mechanism (whole "
        f"{whole_energy.overestimate_percent:.1f}% vs flour "
        f"{flour_energy.overestimate_percent:.1f}%)"
    )


# --------------------------------------------------------------------------
# 3. Hjerpsted 2011 — cheese versus butter, direction only
# --------------------------------------------------------------------------

CHEESE_BUTTER_FAT_G = 40.0


@pytest.mark.conformance
@pytest.mark.xfail(
    strict=True,
    reason=(
        "needs a lipoprotein compartment carrying adaptation-clock state between "
        "meals. The engine's horizon is a single eating occasion."
    ),
)
def test_hjerpsted_2011_cheese_and_butter_diverge_in_direction_only():
    """
    Cheese and butter matched for fat content produce **different** LDL
    responses: cheese lower than butter.

    Direction only, and deliberately so. The divergence replicates; the
    mechanism does not. Calcium-driven faecal fat excretion is the most cited
    candidate, and it is one of several — the protein matrix, the fermentation,
    and the physical structure of the cheese are all live explanations, and the
    faecal-fat effect is not large enough in every trial to carry the result on
    its own.

    So this test asserts an ordering and nothing else. It also asserts, as a
    guard, that the model has **not** hard-coded a faecal-fat explanation: if
    the divergence is produced by a fat-loss term alone, the model has encoded
    an answer the literature has not reached, and that is a failure even though
    the direction would be right.

    No magnitude tolerance is stated, because stating one would be inventing a
    number. Hjerpsted J, Leedo E, Tholstrup T. Cheese intake in large amounts
    lowers LDL-cholesterol concentrations compared with butter intake of equal
    fat content. Am J Clin Nutr. 2011;94(6):1479-1484.
    doi:10.3945/ajcn.111.022426
    """
    cheese_ldl = predict_ldl_response("ex.cheddar.cheese", fat_g=CHEESE_BUTTER_FAT_G)
    butter_ldl = predict_ldl_response("ex.butter", fat_g=CHEESE_BUTTER_FAT_G)

    assert cheese_ldl < butter_ldl, (
        f"cheese LDL response ({cheese_ldl}) must be below butter ({butter_ldl}) "
        "at equal fat"
    )


@pytest.mark.conformance_guard
def test_the_model_does_not_hard_code_a_faecal_fat_explanation():
    """
    Companion guard to the test above, and it runs **now** rather than as an
    xfail: the requirement it encodes is that the engine must not acquire a
    calcium-to-faecal-fat shortcut while nobody is looking.

    The cheese/butter mechanism is unresolved. An engine that resolves it by
    fiat — a calcium term that dumps fat into the faeces — would pass the
    direction test for the wrong reason and would be wrong in every case where
    the real mechanism is the matrix. Checking for the absence of such a term
    is cheap and catches it the day it is added.
    """
    from biology_as_code.engine.laws.registry import load_system_bound_registry

    registry = load_system_bound_registry()
    suspects = [
        law
        for law in registry.all()
        if "calcium" in law.law_statement.lower()
        and any(w in law.law_statement.lower() for w in ("fecal", "faecal", "excret"))
        and law.evidence_state in ("verified", "supported")
    ]
    assert not suspects, (
        "a calcium-driven faecal-fat law is asserted at verified/supported strength: "
        f"{[law.id for law in suspects]}. The cheese/butter mechanism is unresolved; "
        "encoding one candidate as established is exactly what test 3 forbids. If the "
        "evidence has moved, cite it in the commit."
    )


# --------------------------------------------------------------------------
# 4. Forde — texture, eating rate, and intake
# --------------------------------------------------------------------------

FORDE_TARGET_KCAL = -369.0
FORDE_TOLERANCE = 0.40  # ±40%


@pytest.mark.conformance
@pytest.mark.xfail(
    strict=True,
    reason=(
        "needs a bite-clock oral process and an intake controller. "
        "eating_rate_g_per_min exists in HostState v2 and reaches no process."
    ),
)
def test_forde_texture_slows_eating_rate_and_cuts_intake():
    """
    Harder-textured versions of a meal, matched for energy density and
    composition, slow eating rate and reduce ad libitum intake by about
    **369 kcal**.

    This is the bite clock earning its place in the type catalog. Texture does
    not act over a meal, it acts per mouthful: it changes chew count, bolus
    formation time and therefore grams per minute, and intake follows the rate.
    A model that samples oral processing at the meal clock averages the
    mechanism away and gets nothing.

    Tolerance ±40%, i.e. a reduction of 221-517 kcal. As with Hall, the width
    reflects the source rather than modelling slack.

    Forde CG, Mars M, de Graaf K. Ultra-processing or oral processing? A role
    for energy density and eating rate in moderating energy intake from
    processed foods. Curr Dev Nutr. 2020;4(3):nzaa019.
    doi:10.1093/cdn/nzaa019. See also Forde CG, van Kuijk N, Thaler T, de Graaf
    C, Martin N. Texture and savoury taste influences on food intake in a
    realistic hot lunch time meal. Appetite. 2013;60(1):180-186.
    """
    soft_intake = predict_ad_libitum_intake_kcal(["ex.oat.flour.gruel"], days=1)
    hard_intake = predict_ad_libitum_intake_kcal(["ex.oats.porridge.plain"], days=1)
    difference = hard_intake - soft_intake

    assert difference < 0, "the harder-textured meal must reduce intake, not raise it"
    assert within_relative_tolerance(difference, FORDE_TARGET_KCAL, FORDE_TOLERANCE), (
        f"predicted {difference:.0f} kcal difference; "
        f"target {FORDE_TARGET_KCAL} ±{FORDE_TOLERANCE:.0%}"
    )


# --------------------------------------------------------------------------
# 5. Whole versus ground grain — glycemic ordering
# --------------------------------------------------------------------------

GRAIN_CARBS_G = 50.0
GRAIN_FIBER_G = 8.0


@pytest.mark.conformance
@pytest.mark.xfail(
    strict=True,
    reason=(
        "needs matrix to act on carbohydrate release rate. Absorption depends on "
        "grams alone, so intact and milled grain return the same number."
    ),
)
def test_whole_grain_glycemic_response_is_below_ground_grain():
    """
    Intact-kernel and milled versions of the same grain, matched for available
    carbohydrate, produce **ordered** glycemic responses: whole below ground.

    Ordinal only. The size of the gap depends on the grain, the particle size
    distribution, the cooking and the person, and no single number is
    defensible across them — but the ordering is robust, and an engine that
    cannot reproduce an ordering cannot be said to model the matrix at all.

    Botanical structure is doing the work: an intact cell wall is a physical
    barrier between amylase and starch, so milling raises the rate of glucose
    release without changing how much starch is present. This is the same
    mechanism as test 2 acting on a different macronutrient, which is why the
    two are expected to flip together.

    Jenkins DJ, Wesson V, Wolever TM, et al. Wholemeal versus wholegrain
    breads: proportion of whole or cracked grain and the glycaemic response.
    BMJ. 1988;297(6654):958-960. doi:10.1136/bmj.297.6654.958
    """
    whole, ground = packet_pair("ex.whole.wheat.bread", "ex.white.bread.upf")

    assert whole.matrix_integrity != ground.matrix_integrity, (
        "the packets must differ in matrix integrity — that is the premise"
    )

    whole_response = predicted_glycemic_iauc(
        whole, carbs_g=GRAIN_CARBS_G, fiber_g=GRAIN_FIBER_G
    )
    ground_response = predicted_glycemic_iauc(
        ground, carbs_g=GRAIN_CARBS_G, fiber_g=GRAIN_FIBER_G
    )

    assert whole_response < ground_response, (
        f"whole-grain response ({whole_response:.3f}) must be below ground "
        f"({ground_response:.3f}); equal values mean matrix is not reaching "
        "carbohydrate release at all"
    )


# --------------------------------------------------------------------------
# Suite-level invariants
# --------------------------------------------------------------------------


def test_every_conformance_test_states_a_tolerance_and_a_citation():
    """
    A conformance test without a stated tolerance passes whatever the engine
    does, and one without a citation is an opinion. Both are checked here so
    that adding a sloppy sixth test fails immediately.
    """
    import inspect
    import re

    import tests.conformance.test_ward_conformance as module

    citation = re.compile(r"doi:|BMJ\.|Am J Clin Nutr\.|Cell Metab\.|Appetite\.|Curr Dev Nutr\.")
    tolerance = re.compile(r"[Tt]olerance|ordinal only|[Dd]irection only|ordered")

    checked = 0
    for name, fn in vars(module).items():
        if not name.startswith("test_") or not callable(fn):
            continue
        marks = {m.name for m in getattr(fn, "pytestmark", [])}
        if "conformance" not in marks:
            continue
        doc = inspect.getdoc(fn) or ""
        assert citation.search(doc), f"{name} states no citation"
        assert tolerance.search(doc), f"{name} states no tolerance or ordinal claim"
        checked += 1

    assert checked == 5, f"expected 5 conformance tests, found {checked}"


def test_the_harness_names_the_gap_rather_than_just_failing():
    """An xfail reason must be a specification requirement, not a stack trace."""
    with pytest.raises(MechanismMissing) as exc:
        predict_ad_libitum_intake_kcal(["ex.butter"], days=1)
    assert "intake controller" in exc.value.needs

    with pytest.raises(MechanismMissing) as exc:
        predict_ldl_response("ex.butter", fat_g=10.0)
    assert "lipoprotein" in exc.value.needs


def test_atwater_general_factors_are_annex_b_only():
    """
    The factors are specified for legacy compatibility and marked not-for-new-
    work. Tests 2 and 5 exist to show what they miss, so the suite must not
    quietly start treating them as the answer.
    """
    import inspect

    from tests.conformance import harness

    assert harness.ATWATER_GENERAL == {"carbs": 4.0, "protein": 4.0, "fats": 9.0, "fiber": 2.0}
    assert "Annex-B" in inspect.getsource(harness), (
        "the Atwater factors must stay marked Annex-B / not-for-new-work"
    )
    assert atwater_kcal(carbs_g=10, protein_g=10, fats_g=10) == pytest.approx(170.0)
