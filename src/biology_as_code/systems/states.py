"""Fail-closed evaluation states.

Mirrors docs/constitution.md. ``CONFIRMED`` exists in the lattice so an
evidence-promotion step can set it later; adapters in this package must
never emit it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvalState(str, Enum):
    HOLDS = "HOLDS"
    UNEVALUABLE = "UNEVALUABLE"
    REFUSE = "REFUSE"
    OPEN = "OPEN"
    REFUTED = "REFUTED"
    # Auditor sibling names kept for join with biology_as_code.audit
    BUSTED = "Busted"
    PLAUSIBLE = "Plausible"
    CONFIRMED = "Confirmed"


MECHANISM_EMITTABLE = frozenset(
    {
        EvalState.HOLDS,
        EvalState.UNEVALUABLE,
        EvalState.REFUSE,
        EvalState.OPEN,
        EvalState.REFUTED,
        EvalState.BUSTED,
        EvalState.PLAUSIBLE,
    }
)


@dataclass(frozen=True)
class WalkResult:
    state: EvalState
    system_id: str
    gate_id: str | None
    reason: str
    l3_named: bool
    declared_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.state is EvalState.CONFIRMED:
            raise ValueError("mechanism walk cannot emit CONFIRMED")
