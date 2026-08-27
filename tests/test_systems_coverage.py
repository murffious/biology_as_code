from biology_as_code.systems import (
    cover_meal,
    default_ledger,
    lint_claim,
    parked_systems,
    shipped_systems,
    trial_coverage,
)
from biology_as_code.systems.states import EvalState
from biology_as_code.systems.trials import assert_eleven_rows


def test_eleven_systems_five_shipped():
    assert len(shipped_systems()) == 5
    assert len(parked_systems()) == 6
    table = cover_meal({"meal_id": "empty"})
    assert len(table.rows) == 11
    assert table.grey_majority()


def test_parked_are_unevaluable():
    table = cover_meal({"meal_id": "empty"})
    parked = [r for r in table.rows if not r.shipped]
    assert parked
    assert all(r.state is EvalState.UNEVALUABLE for r in parked)


def test_eating_rate_holds_digestive_and_nervous():
    table = cover_meal(
        {
            "meal_id": "fast",
            "eating_rate_kcal_min": 48,
            "hpf_fat_sodium": True,
        }
    )
    by = {r.system_id: r for r in table.rows}
    assert by["digestive"].state is EvalState.HOLDS
    assert by["nervous"].state is EvalState.HOLDS
    assert by["digestive"].result.gate_id == "eating_rate"


def test_zero_fat_vehicle_refutes_digestive():
    table = cover_meal(
        {
            "meal_id": "spinach_zero_fat",
            "lipid_vehicle_g": 0,
            "fat_soluble_cargo": True,
        }
    )
    dig = next(r for r in table.rows if r.system_id == "digestive")
    assert dig.state is EvalState.REFUTED
    assert dig.result.gate_id == "micelle_fat_vehicle"


def test_silence_is_not_zero():
    table = cover_meal({"meal_id": "stub"})
    dig = next(r for r in table.rows if r.system_id == "digestive")
    assert dig.state is EvalState.UNEVALUABLE


def test_linter_flags_l1_to_l5_jump():
    r = lint_claim("Ultra-processed food causes depression.")
    assert r.malformed
    assert r.state is EvalState.REFUSE
    assert r.l1 and r.l5 and not r.l3


def test_linter_allows_named_mechanism():
    r = lint_claim("UPF raises energy intake via faster eating rate.")
    assert not r.malformed
    assert "eating rate" in r.l3


def test_linter_refuses_superfood():
    r = lint_claim("This superfood detox boosts immunity.")
    assert r.malformed
    assert r.state is EvalState.REFUSE


def test_trials_have_eleven_rows():
    for trial in trial_coverage():
        assert_eleven_rows(trial)


def test_hall_digestive_holds():
    hall = trial_coverage("hall_2019")[0]
    dig = next(n for n in hall.notes if n.system_id == "digestive")
    assert dig.state is EvalState.HOLDS
    nervous = next(n for n in hall.notes if n.system_id == "nervous")
    assert nervous.state is not EvalState.HOLDS


def test_mnp_edge_is_refused():
    ledger = default_ledger()
    mnp = next(e for e in ledger.edges if e.edge_id.endswith("mnp.dementia"))
    assert mnp.state is EvalState.REFUSE


def test_gi_t2d_edge_refuted_as_construct_mismatch():
    ledger = default_ledger()
    gi = next(e for e in ledger.edges if e.l3_gate == "insulin_gi_fii")
    assert gi.state is EvalState.REFUTED


def test_next_studies_are_open_edges():
    studies = default_ledger().next_studies()
    assert studies
    assert any("GLP-1" in s for s in studies)
