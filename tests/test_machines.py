"""Open declarative digestion machines: load, validate, and IP-boundary tests."""

from __future__ import annotations

import json


def test_list_and_get():
    from biology_as_code import get_machine, list_machines

    ids = list_machines()
    for expected in ("stage.oral", "stage.stomach", "stage.duodenum", "stage.jejunum", "stage.colon"):
        assert expected in ids
    m = get_machine("stage.stomach")
    assert m is not None
    assert m["startAt"] in m["states"]
    assert get_machine("stage.does-not-exist") is None
    assert get_machine("") is None


def test_kind_filter():
    from biology_as_code.machines import list_machines

    assert len(list_machines(kind="stage")) == 8
    assert list_machines(kind="process") == ["process.full-digest"]
    assert list_machines(kind="lens") == []


def test_validate_all_ok():
    from biology_as_code.machines import validate_all

    result = validate_all()
    assert result["ok"], result["errors"]
    assert result["n"] == 9


def test_no_dangling_transitions():
    from biology_as_code.machines import get_machine, list_machines, validate_machine

    for mid in list_machines():
        assert validate_machine(get_machine(mid)) == [], mid


def test_process_chains_real_stages():
    """process.full-digest may only reference stages that exist in the registry."""
    from biology_as_code.machines import get_machine, list_machines

    ids = set(list_machines())
    proc = get_machine("process.full-digest")
    refs = [
        e.split(":", 1)[1]
        for st in proc["states"].values()
        for e in (st.get("emits") or [])
        if isinstance(e, str) and e.startswith("stage:")
    ]
    assert refs, "process should chain stages"
    for r in refs:
        assert r in ids, f"process references unknown stage {r}"


def test_open_tier_has_no_score_hooks():
    """The whole point: open machines must never carry product-score/penalty hooks."""
    from biology_as_code.machines import get_machine, list_machines

    for mid in list_machines():
        blob = json.dumps(get_machine(mid)).lower()
        for banned in ("penalties", "deduct", "biosolvency", "kibo_vars", "product_score"):
            assert banned not in blob, f"{mid} leaked '{banned}'"


def test_validator_catches_injected_penalty():
    """A score hook injected into a machine must fail validation."""
    from biology_as_code.machines import get_machine, validate_machine

    m = get_machine("stage.stomach")
    m["states"]["fastEmpty"]["penalties"] = [{"id": "x", "deduct": "c4.band"}]
    errors = validate_machine(m)
    assert any("score hook" in e for e in errors)


def test_get_machine_returns_fresh_copy():
    """Mutating a returned machine must not corrupt the next caller's copy."""
    from biology_as_code.machines import get_machine

    a = get_machine("stage.stomach")
    a["states"].clear()
    b = get_machine("stage.stomach")
    assert b["states"], "get_machine handed back shared mutable state"


def test_hash_matches_registry():
    from biology_as_code.machines import content_hash, get_machine, load_registry

    by_id = {r["id"]: r for r in load_registry()["machines"]}
    for mid, row in by_id.items():
        assert content_hash(get_machine(mid)) == row["hash"], f"{mid} hash drift"
