"""Library should stay quiet at default log level."""

from __future__ import annotations

import logging


def test_simulate_meal_no_stdout(capsys):
    from biology_as_code import simulate_meal

    # Ensure package logger is not spamming INFO to root
    logging.getLogger("biology_as_code").setLevel(logging.WARNING)
    r = simulate_meal(carbs_g=30, protein_g=15, fats_g=10, fiber_g=8, enable_product_score=False)
    captured = capsys.readouterr()
    assert "Initializing KIBO" not in captured.out
    assert "=== Simulating" not in captured.out
    assert r.absorbed_macros_g
