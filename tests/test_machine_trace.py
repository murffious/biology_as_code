"""Trace executor + machines-driven digestion (SSOT bridge)."""

from __future__ import annotations

# --- predicate evaluation -------------------------------------------------

def test_match_operators_and_missing_fields():
    from biology_as_code.machines import match

    ctx = {"meal.proteinG": 30, "host.postSurgical": True}
    assert match({"field": "meal.proteinG", "op": ">=", "value": 25}, ctx)
    assert not match({"field": "meal.proteinG", "op": "<", "value": 25}, ctx)
    assert match({"field": "host.postSurgical", "op": "==", "value": True}, ctx)
    # missing field never crashes and is not "satisfied"
    assert not match({"field": "meal.fatG", "op": ">=", "value": 10}, ctx)
    assert not match({"field": "meal.fatG", "op": "exists"}, ctx)
    assert match({"field": "meal.proteinG", "op": "exists"}, ctx)
    # all / any / not
    assert match({"all": [
        {"field": "meal.proteinG", "op": ">=", "value": 25},
        {"field": "host.postSurgical", "op": "==", "value": True},
    ]}, ctx)
    assert match({"any": [
        {"field": "meal.fatG", "op": ">=", "value": 99},
        {"field": "meal.proteinG", "op": ">=", "value": 25},
    ]}, ctx)
    assert match({"not": {"field": "meal.fatG", "op": ">=", "value": 10}}, ctx)


# --- trace ----------------------------------------------------------------

def test_trace_high_fat_takes_slow_empty():
    from biology_as_code import trace

    r = trace("stage.stomach", {"meal.fatG": 20, "meal.proteinG": 10,
                                 "meal.glucoseG": 30, "meal.fiberG": 5,
                                 "meal.matrixIntegrity": 0.8})
    assert r["status"] == "ok"
    assert "slowEmpty" in r["visited"]
    assert "fastEmpty" not in r["visited"]
    assert r["final"] == "handoff"


def test_trace_refined_carb_fires_edge_case():
    from biology_as_code import trace

    r = trace("stage.stomach", {"meal.fatG": 2, "meal.proteinG": 5,
                                 "meal.glucoseG": 45, "meal.fiberG": 2,
                                 "meal.matrixIntegrity": 0.1})
    assert "fastEmpty" in r["visited"]
    fired = {ec["id"] for ec in r["firedEdgeCases"]}
    assert "refined-carb-preload" in fired


def test_trace_default_branch_and_terminal():
    from biology_as_code import trace

    # balanced whole-food meal -> mixedEmpty (the choice default)
    r = trace("stage.stomach", {"meal.fatG": 8, "meal.proteinG": 15,
                                 "meal.glucoseG": 20, "meal.fiberG": 10,
                                 "meal.matrixIntegrity": 0.9})
    assert "mixedEmpty" in r["visited"]
    assert r["path"][-1]["type"] == "succeed"


def test_trace_unknown_machine_is_error_not_crash():
    from biology_as_code import trace

    r = trace("stage.nope", {})
    assert r["status"] == "error"
    assert r["final"] is None


def test_trace_does_not_mutate_context():
    from biology_as_code import trace

    ctx = {"meal.fatG": 20, "meal.glucoseG": 30}
    before = dict(ctx)
    trace("stage.stomach", ctx)
    assert ctx == before


# --- digestion bridge (dig reads machines as SSOT) ------------------------

def test_stage_order_is_ssot_from_registry():
    from biology_as_code.dig import digestion_stage_ids

    ids = digestion_stage_ids()
    assert ids == [
        "stage.oral", "stage.stomach", "stage.duodenum", "stage.jejunum",
        "stage.portal", "stage.systemic", "stage.cell", "stage.colon",
    ]


def test_run_digestion_walks_all_stages():
    from biology_as_code import run_digestion

    r = run_digestion(carbs_g=45, protein_g=10, fats_g=5, fiber_g=3, matrix_integrity=0.1)
    # the process chained every stage
    assert list(r["final_states"]) == [
        "stage.oral", "stage.stomach", "stage.duodenum", "stage.jejunum",
        "stage.portal", "stage.systemic", "stage.cell", "stage.colon",
    ]
    assert r["process"]["status"] == "ok"
    # a low-fiber refined meal trips teaching edge cases somewhere in the walk
    assert r["firedEdgeCases"]


def test_run_digestion_empty_intake_stops_early():
    from biology_as_code import run_digestion

    r = run_digestion(context={"intake.food": 0, "intake.hydration": 0,
                               "intake.supplement": 0, "host.ready": 1})
    assert r["process"]["final"] == "stopEmpty"
    assert r["stages"] == []  # no stage emitted -> nothing traced


def test_run_digestion_negative_macros_clamped():
    from biology_as_code.machines import meal_to_context

    ctx = meal_to_context(carbs_g=-10, protein_g=-5, fats_g=-3, fiber_g=-2)
    assert ctx["meal.glucoseG"] == 0.0
    assert ctx["meal.proteinG"] == 0.0


# --- regressions from the adversarial review ------------------------------

def test_trace_non_terminal_dead_end_is_incomplete():
    """A choice with no matching rule and no default must report 'incomplete', not 'ok'."""
    from biology_as_code import trace

    m = {"id": "m", "startAt": "A", "states": {
        "A": {"type": "choice", "label": "A",
              "choices": [{"when": {"field": "k", "op": "==", "value": 9}, "next": "B"}]},
        "B": {"type": "succeed", "label": "B"},
    }}
    r = trace(m, {"k": 1})
    assert r["status"] == "incomplete"
    assert r["final"] == "A"


def test_trace_terminal_edgecase_no_phantom_next():
    """An edgeCase.next on a terminal state must not fabricate a transition."""
    from biology_as_code import trace

    m = {"id": "m", "startAt": "A", "states": {
        "A": {"type": "task", "label": "A", "next": "B"},
        "B": {"type": "succeed", "label": "B",
              "edgeCases": [{"id": "rr", "when": {"field": "f", "op": "==", "value": 1},
                             "effect": "x", "next": "C"}]},
        "C": {"type": "succeed", "label": "C"},
    }}
    r = trace(m, {"f": 1})
    assert r["status"] == "ok"
    assert r["visited"] == ["A", "B"]
    assert r["path"][-1]["next"] is None  # no phantom "C"


def test_meal_to_context_bad_and_nan_fraction_falls_back():
    from biology_as_code.machines import meal_to_context

    assert meal_to_context(matrix_integrity="bad")["meal.matrixIntegrity"] == 0.8
    assert meal_to_context(food_quality="bad")["meal.foodQuality"] == 0.7
    assert meal_to_context(matrix_integrity=float("nan"))["meal.matrixIntegrity"] == 0.8
    assert meal_to_context(matrix_integrity=5)["meal.matrixIntegrity"] == 1.0  # clamped to 0-1


def test_ssot_order_agrees_across_registry_and_execution():
    """The confirmed-fix guarantee: registry order == executed process order."""
    from biology_as_code import run_digestion
    from biology_as_code.dig import digestion_stage_ids
    from biology_as_code.machines import validate_all

    assert validate_all()["ok"]  # includes the new order cross-check
    executed = list(run_digestion(carbs_g=40, protein_g=20, fats_g=10, fiber_g=8)["final_states"])
    assert executed == digestion_stage_ids()
