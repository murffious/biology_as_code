"""Declared[T] — a value that knows the difference between the three ways of not
being a number.

    OPEN  — not known. It exists and could be supplied.
    NONE  — not applicable. Known absent.
    value — measured, with a method behind it.

Every generated SDK types this as Optional[T] and collapses OPEN into NONE.
FDP-1 §4 forbids exactly that: unknowns SHALL be the literal "OPEN", never
null/empty/omitted. Grading follows §3.1 — weakest link, computed, never asserted.

Stdlib only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

OPEN = "OPEN"
NONE = "NONE"

# §3.1 — higher is better. OPEN renders as "—" and ranks below every grade.
GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1, "—": 0}
UNGRADED = "—"


class Refused(Exception):
    """Raised when a caller asks a declared value for something it cannot answer."""


@dataclass(frozen=True)
class Declared(Generic[T]):
    state: object          # a T, or OPEN, or NONE
    grade: str = UNGRADED
    method_ref: str | None = None
    source_ref: str | None = None

    # --- constructors -----------------------------------------------------
    @classmethod
    def open(cls) -> "Declared[T]":
        return cls(OPEN, UNGRADED)

    @classmethod
    def none(cls) -> "Declared[T]":
        return cls(NONE, UNGRADED)

    @classmethod
    def of(cls, value: T, grade: str = UNGRADED, *, method_ref=None, source_ref=None):
        if value is None:
            raise ValueError("null is not a state; use Declared.open() or Declared.none()")
        if grade not in GRADE_RANK:
            raise ValueError(f"unknown grade {grade!r}")
        return cls(value, grade, method_ref, source_ref)

    # --- interrogation ----------------------------------------------------
    @property
    def is_open(self) -> bool:
        return self.state == OPEN

    @property
    def is_none(self) -> bool:
        return self.state == NONE

    @property
    def known(self) -> bool:
        return not (self.is_open or self.is_none)

    def value(self) -> T:
        """The number, or a refusal. Never a silent None."""
        if self.is_open:
            raise Refused("value is OPEN — not known; it exists and could be supplied")
        if self.is_none:
            raise Refused("value is NONE — not applicable; known absent")
        return self.state  # type: ignore[return-value]

    def or_refuse(self, default: T) -> T:
        """Explicit opt-out. The caller has to say the word."""
        return self.state if self.known else default  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.is_open:
            return "Declared(OPEN)"
        if self.is_none:
            return "Declared(NONE)"
        return f"Declared({self.state!r}, grade={self.grade!r})"


def weakest_link(values: list["Declared"]) -> str:
    """FDP-1 §3.1. The grade of a score is the grade of its worst input —
    computed, never asserted. One OPEN input caps the whole score at '—'.

    Averaging is banned on purpose: it would let a system bury weak inputs
    under strong ones.
    """
    if not values:
        return UNGRADED
    return min(
        (UNGRADED if v.is_open else v.grade for v in values),
        key=lambda g: GRADE_RANK.get(g, 0),
    )
