"""Explicit small-intestine → colon handoff.

The pasted simulation_engine.py was right about one thing: unabsorbed fiber
must not vanish. It was wrong to then invent SCFA grams and raise when an
ontology id is missing.

This module only packages what the upper tract declared as unabsorbed.
Missing type → UNEVALUABLE row, not a crash.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from biology_as_code.dig.colon_fermentation import (
    FermentResult,
    FiberType,
    process_fiber,
)

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]


@dataclass(frozen=True, slots=True)
class UnabsorbedFiber:
    amount: float | None
    fiber_type: FiberType | str | None
    source_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChymeHandoff:
    unabsorbed_fiber: tuple[UnabsorbedFiber, ...]

    def ferment(self) -> tuple[FermentResult, ...]:
        return tuple(
            process_fiber(item.amount, item.fiber_type) for item in self.unabsorbed_fiber
        )

    def pool_state(self) -> ConstitutionState:
        """Worst-state wins. Empty handoff is UNEVALUABLE, not a zero pool."""
        rows = self.ferment()
        if not rows:
            return "UNEVALUABLE"
        order = ("REFUSE", "UNEVALUABLE", "REFUTED", "OPEN", "HOLDS")
        states = {row.state for row in rows}
        for state in order:
            if state in states:
                return state  # type: ignore[return-value]
        return "UNEVALUABLE"


def handoff_from_declared(
    items: list[tuple[float | None, FiberType | str | None, str | None]] | None,
) -> ChymeHandoff:
    if items is None:
        return ChymeHandoff(unabsorbed_fiber=())
    return ChymeHandoff(
        unabsorbed_fiber=tuple(
            UnabsorbedFiber(amount=amount, fiber_type=kind, source_id=source_id)
            for amount, kind, source_id in items
        )
    )
