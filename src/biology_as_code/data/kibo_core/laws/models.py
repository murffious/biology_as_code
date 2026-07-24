"""
Pathway-first data structures for law-governed nutrition mechanics.

A PathwayNode is a seat in a delivery/metabolism graph:
  - next_pathways: where cargo can go next
  - inhibitors / enhancers: typed modifiers with law_ids + priors
  - priors: belief weights for incomplete science (0–1)

This is the code twin of the textbook→code missing-link layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

RelationType = Literal[
    "OPENS_GATE",
    "CLOSES_GATE",
    "EXPANDS_BOUND",
    "NARROWS_BOUND",
    "STATE_FUNCTION",
    "FRAMEWORK",
    "MIXED",
]

SevenSystem = Literal[
    "Assimilation",
    "Transport",
    "Communication",
    "Defense",
    "Biotransformation",
    "Energy",
    "Structure",
]


@dataclass(frozen=True)
class Modifier:
    """Enhancer or inhibitor on a pathway node (meal matrix or host)."""

    id: str
    nutrient: str
    relation: RelationType
    law_id: str
    """Fold-change when active: >1 expands yield, <1 narrows. None = qualitative."""
    magnitude: float | None = None
    conditions: tuple[str, ...] = ()
    """Prior that this edge is real / magnitude is in the right ballpark (0–1)."""
    prior: float = 0.7
    """Context key that must be truthy in WalkState.context for this modifier to fire."""
    requires_context: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not (0.0 <= self.prior <= 1.0):
            raise ValueError(f"prior must be in [0,1], got {self.prior}")
        if self.magnitude is not None and self.magnitude <= 0:
            raise ValueError(f"magnitude must be positive fold, got {self.magnitude}")


@dataclass
class PathwayNode:
    """One step in a law-governed pathway graph."""

    id: str
    label: str
    system: SevenSystem
    organ: str
    subsystem: str = ""
    mechanism: str = ""
    cargo: tuple[str, ...] = ()
    """Ordered next node ids (branching allowed)."""
    next_pathways: tuple[str, ...] = ()
    inhibitors: tuple[Modifier, ...] = ()
    enhancers: tuple[Modifier, ...] = ()
    """Node-level priors: e.g. {"human_evidence": 0.9, "magnitude_locked": 0.5}."""
    priors: dict[str, float] = field(default_factory=dict)
    law_ids: tuple[str, ...] = ()
    """If True, yield cannot pass this node unless gate_open in context (or default open)."""
    is_gate: bool = False
    gate_context_key: str | None = None
    """Default open when key missing (existence gates often default closed)."""
    gate_default_open: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        for k, v in self.priors.items():
            if not (0.0 <= float(v) <= 1.0):
                raise ValueError(f"prior {k} out of range: {v}")


@dataclass
class WalkState:
    """Mutable cargo state while walking a pathway."""

    cargo: str
    """Yield multiplier (starts at 1.0)."""
    yield_factor: float = 1.0
    """Free-form meal/host context: {"ascorbate_same_meal": True, "tannin": True, ...}."""
    context: dict[str, Any] = field(default_factory=dict)
    path: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""


@dataclass
class WalkResult:
    start: str
    end: str | None
    yield_factor: float
    path: list[str]
    log: list[str]
    blocked: bool
    block_reason: str
    """Product of priors on edges that fired (diagnostic, not a probability of truth)."""
    prior_product: float
    modifiers_fired: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "yield_factor": self.yield_factor,
            "path": self.path,
            "log": self.log,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "prior_product": self.prior_product,
            "modifiers_fired": self.modifiers_fired,
        }
