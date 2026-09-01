"""Fixtures and version ship for installable package."""

from __future__ import annotations


def test_version_matches_pyproject():
    # Compare against pyproject rather than a literal: a census test named for a
    # version fails on every release and its failure carries no information —
    # the invariant is that the two declarations agree.
    import tomllib

    from biology_as_code import __version__

    with open("pyproject.toml", "rb") as f:
        declared = tomllib.load(f)["project"]["version"]
    assert __version__ == declared


def test_meals_and_vitamins():
    from biology_as_code.data.fixtures import list_meal_ids, load_meal, vitamins_path

    ids = list_meal_ids()
    assert len(ids) >= 10
    m = load_meal(ids[0])
    assert m is not None
    blob = str(m)
    assert "flow_score" not in blob
    assert vitamins_path().is_file()


def test_external_scorer_hook_unavailable():
    from biology_as_code import external_scorer_available, run_external_score_analysis

    assert external_scorer_available() is False
    out = run_external_score_analysis(enabled=True)
    assert out["available"] is False
