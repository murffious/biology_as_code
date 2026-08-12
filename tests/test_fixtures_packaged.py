"""Fixtures and version ship for installable package."""

from __future__ import annotations


def test_version_is_010():
    from biology_as_code import __version__

    assert __version__ == "0.1.0"


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
