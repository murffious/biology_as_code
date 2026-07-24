"""
Physiological scenarios — thin wrappers over existing factories.

Names match nutrition teaching (fed / fasted / exercise), not product scores.
"""

from __future__ import annotations

from typing import Any

from biology_as_code.simulation.physiological_state import (
    create_exercise_state,
    create_fed_state,
    create_overnight_fast_state,
    create_prolonged_fast_state,
)


def fed() -> Any:
    return create_fed_state()


def overnight_fast() -> Any:
    return create_overnight_fast_state()


def prolonged_fast() -> Any:
    return create_prolonged_fast_state()


def exercise() -> Any:
    return create_exercise_state()


def pathway_activities(state: Any) -> dict:
    """Regulation snapshot for a physiological state (open FLOW)."""
    from biology_as_code.pathways.pathway_regulation import pathway_activity_snapshot as snap

    return snap(state)
