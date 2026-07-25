"""
The unified carrier: one DigestRun object drives both the app and the engine.

These tests pin the contract that makes the two sides unable to disagree about the
input: the same JSON validates against the same schemas, flattens through the same
field mapping, and runs the full A-Z digestion process (S-0 intake-setup -> colon).
"""

from __future__ import annotations

import pytest

from biology_as_code.carrier import (
    SCHEMA_DIR,
    DigestRun,
    DigestRunInvalid,
    conditions_from_digest_run,
    load_digest_run,
    run_digest_run,
    to_machine_context,
    validate_digest_run,
)
from biology_as_code.machines.loader import list_machines
from biology_as_code.machines.validate import validate_all

EXAMPLE = SCHEMA_DIR / "fixtures" / "digest-run.example.json"


def _minimal(**overrides):
    run = {
        "host": {"ready": 1},
        "packet": {"intake": {"food": 1, "hydration": 0, "supplement": 0}},
    }
    run.update(overrides)
    return run


# --- registration / A-Z process -------------------------------------------------


def test_intake_setup_is_registered_and_first():
    stages = list_machines("stage")
    assert stages[0] == "stage.intake-setup"
    assert "stage.intake-setup" in stages


def test_validate_all_green_with_intake_setup():
    report = validate_all()
    assert report["ok"], report["errors"]
    assert report["n"] == 10  # 9 stages + full-digest process


def test_full_digest_walks_all_nine_stages_from_a_digest_run():
    dr = load_digest_run(EXAMPLE)
    run = run_digest_run(dr)
    walked = [s["machine"] for s in run["stages"]]
    assert walked == [
        "stage.intake-setup", "stage.oral", "stage.stomach", "stage.duodenum",
        "stage.jejunum", "stage.portal", "stage.systemic", "stage.cell", "stage.colon",
    ]
    assert run["process"]["status"] == "ok"


# --- load / validate ------------------------------------------------------------


def test_example_digest_run_loads_and_validates():
    dr = load_digest_run(EXAMPLE)
    assert isinstance(dr, DigestRun)
    assert dr.common_name == "Spinach salad with olive oil"
    assert validate_digest_run(dr.raw).valid


@pytest.mark.parametrize("bad", [{"packet": {"intake": {"food": 1, "hydration": 0, "supplement": 0}}},
                                 {"host": {"ready": 1}}])
def test_missing_required_component_is_rejected(bad):
    assert not validate_digest_run(bad).valid
    with pytest.raises(DigestRunInvalid):
        load_digest_run(bad)


def test_can_skip_validation():
    # A caller may opt out; the object still builds.
    dr = load_digest_run({"host": {}, "packet": {}}, validate=False)
    assert isinstance(dr, DigestRun)


# --- to_machine_context: field mapping fidelity ---------------------------------


def test_context_flattens_host_meal_intake():
    ctx = to_machine_context(load_digest_run(EXAMPLE))
    assert ctx["host.ready"] == 1
    assert ctx["host.acidCapacity"] == 1.0
    assert ctx["intake.food"] == 1
    assert ctx["intake.hydration"] == 1
    assert ctx["meal.proteinG"] == 6
    assert ctx["meal.fatG"] == 14
    assert ctx["meal.glucoseG"] == 12  # macros.carb -> glucoseG teaching proxy
    # matrix + mastication are chew-DERIVED (the app's enrichDigestRun behaviour),
    # not the raw explicit 0.8/0.85 the packet declared — see the parity test below.
    assert ctx["meal.matrixIntegrity"] == pytest.approx(0.8125, abs=1e-3)
    assert ctx["meal.masticationQuality"] == pytest.approx(0.3127, abs=1e-3)


def test_context_matches_app_chew_derivation():
    """Parity guard: chew samples override explicit mastication, and the matrix boost
    follows. Numbers are the app's (chewSecondsToQuality(4.5)=1-e^-0.375=0.3127;
    boost=clamp01(0.3127)*0.2-0.1=-0.0375; matrix=0.85-0.0375=0.8125), NOT the raw
    explicit mastication_quality=0.8 / matrix_integrity=0.85 the fixture declares.
    """
    ctx = to_machine_context(load_digest_run(EXAMPLE))
    assert ctx["meal.masticationQuality"] == pytest.approx(0.31271, abs=1e-4)
    assert ctx["meal.matrixIntegrity"] == pytest.approx(0.81254, abs=1e-4)
    assert ctx["meal.foodOrderScore"] == pytest.approx(0.9)   # no sequence -> explicit kept
    assert ctx["meal.processingCombined"] == pytest.approx(0.15)  # declared
    assert ctx["meal.residueBurden"] == 0                     # app default when silent


def test_context_uses_app_teaching_defaults_when_undeclared():
    # macros default 0, matrix 0.7, mastication/order 0.5 — matches the app so the
    # two sides cannot disagree about a silent field.
    ctx = to_machine_context(load_digest_run(_minimal()))
    assert ctx["meal.proteinG"] == 0
    assert ctx["meal.matrixIntegrity"] == pytest.approx(0.7)
    assert ctx["meal.masticationQuality"] == pytest.approx(0.5)
    assert ctx["meal.foodOrderScore"] == pytest.approx(0.5)


def test_context_omits_undeclared_optional_host_fields():
    ctx = to_machine_context(load_digest_run(_minimal()))
    assert "host.acidCapacity" not in ctx  # fail-closed: not declared -> not asserted
    assert ctx["host.ready"] == 1


def test_hydrated_with_meal_forces_intake_hydration():
    run = _minimal()
    run["ingestion"] = {"hydrated_with_meal": True}
    ctx = to_machine_context(load_digest_run(run))
    assert ctx["intake.hydration"] == 1


# --- fail-closed behaviour through the process ----------------------------------


def test_empty_intake_stops_before_the_mouth():
    run = _minimal()
    run["packet"]["intake"] = {"food": 0, "hydration": 0, "supplement": 0}
    result = run_digest_run(run)
    assert result["process"]["final"] == "stopEmpty"


# --- Conditions view ------------------------------------------------------------


def test_conditions_view_over_digest_run():
    cond = conditions_from_digest_run(load_digest_run(EXAMPLE))
    assert cond.clock == "fed"
    assert cond.stage == "adult"
    assert cond.partners["dietary_lipid_g"] == 14
    assert cond.partners["ascorbate"] is True
    # host seat is camelCased to match the machine context namespace
    assert cond.host["ready"] == 1
