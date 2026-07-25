"""
The registry → Amazon States Language compiler (offline; no AWS).
"""

from __future__ import annotations

from biology_as_code.digestion.asl import (
    food_to_input,
    machine_to_asl,
    predicate_to_asl,
    registry_to_asl,
)
from biology_as_code.machines import get_machine, list_machines


def test_predicate_numeric():
    assert predicate_to_asl({"field": "meal.fatG", "op": "<", "value": 10}) == {
        "Variable": "$.meal.fatG",
        "NumericLessThan": 10,
    }


def test_predicate_exists_and_all():
    assert predicate_to_asl({"field": "meal.fatG", "op": "exists"}) == {
        "Variable": "$.meal.fatG",
        "IsPresent": True,
    }
    conj = predicate_to_asl(
        {"all": [{"field": "a", "op": "==", "value": 0}, {"field": "b", "op": "==", "value": 0}]}
    )
    assert "And" in conj and len(conj["And"]) == 2


def test_full_digest_compiles_to_asl():
    asl = machine_to_asl(get_machine("process.full-digest"))
    # A-Z now starts at S-0 intake-setup (a stage-running task -> nested execution)
    assert asl["StartAt"] == "intakeSetup"
    assert asl["States"]["intakeSetup"]["Type"] == "Task"
    assert "startExecution" in asl["States"]["intakeSetup"]["Resource"]
    assert asl["States"]["intakeGate"]["Type"] == "Choice"
    assert "Default" in asl["States"]["intakeGate"]
    # a stage-running task becomes a nested Step Functions execution
    assert asl["States"]["oral"]["Type"] == "Task"
    assert "startExecution" in asl["States"]["oral"]["Resource"]
    # a succeed becomes Succeed
    assert asl["States"]["complete"]["Type"] == "Succeed"


def test_plain_task_becomes_pass():
    asl = machine_to_asl(get_machine("stage.duodenum"))
    assert asl["States"]["neutralize"]["Type"] == "Pass"


def test_registry_covers_every_machine():
    reg = registry_to_asl()
    assert set(reg) == set(list_machines())
    for asl in reg.values():
        assert "StartAt" in asl and "States" in asl and asl["States"]


def test_food_to_input_nests_and_is_fail_closed():
    spinach = food_to_input("ex.spinach_salad.zero_fat")
    assert spinach["meal"]["fatG"] == 0  # declared zero fat is present
    assert "intake" in spinach and "host" in spinach
    # a food with no declared lipid must not carry a zero meal.fatG
    lentils = food_to_input("ex.lentils.with_ascorbate")
    assert "fatG" not in lentils.get("meal", {})
