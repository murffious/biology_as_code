"""Shared shape for versioned response objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, runtime_checkable

__all__ = ["Sample", "ResponseResult", "ResponseProtocol", "ResponseNotExecutable"]


class ResponseNotExecutable(NotImplementedError):
    """
    Raised by a declared-but-unimplemented response.

    Deliberately not a silent ``None``. A stub that returns nothing gets
    treated as a zero somewhere downstream; a stub that raises tells the caller
    exactly which protocol is missing.
    """


@dataclass(frozen=True)
class Sample:
    """One timed measurement."""

    minutes: float
    value: float

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ValueError(f"sample time must be non-negative, got {self.minutes}")


@dataclass
class ResponseResult:
    """Outcome of applying a response protocol to a sample series."""

    protocol: str
    """The protocol's headline quantity."""
    value: float
    unit: str
    """Ordinal class from the protocol's own bounds, or empty when unclassified."""
    classification: str = ""
    """Everything needed to reproduce the number."""
    detail: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "value": self.value,
            "unit": self.unit,
            "classification": self.classification,
            "detail": self.detail,
            "warnings": list(self.warnings),
        }


@runtime_checkable
class ResponseProtocol(Protocol):
    """A versioned, executable definition of a measurement."""

    #: e.g. ``"GlycemicResponse/1.0"``. Immutable once published.
    protocol_id: str

    def compute(self, samples: Sequence[Sample]) -> ResponseResult:
        """Apply the protocol to a sample series."""
        ...
