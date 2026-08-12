"""
Flux — a rate-typed flow between two compartments.

Fluxes were implicit before this module: balance models moved quantities by
mutating two fields in the same function and the movement itself was never an
object. That works until you want to ask what left the stomach, or to check
that what left one compartment arrived in another. Neither question has an
answer if the flow is only a side effect.

A :class:`Flux` is the flow made explicit: a substance, a source, a sink, and a
*rate* with its unit and its clock. Amounts are obtained by integrating a rate
over an interval, never by reading a rate as though it were an amount —
:meth:`Flux.amount_over` is the only way to get one, and it is where the unit
bookkeeping lives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from biology_as_code.engine.clocks import Clock

__all__ = ["Flux", "FluxSet", "SINK_EXTERNAL", "SOURCE_EXTERNAL"]

#: Reserved endpoints for flow that crosses the model boundary. Faecal loss is
#: a real destination, and naming it keeps mass balance closable.
SINK_EXTERNAL = "external.excreted"
SOURCE_EXTERNAL = "external.ingested"

_PER_SECOND: dict[str, float] = {
    "per_s": 1.0,
    "per_min": 1.0 / 60.0,
    "per_h": 1.0 / 3600.0,
    "per_day": 1.0 / 86400.0,
}


@dataclass(frozen=True)
class Flux:
    """
    A rate-typed flow of one substance from one compartment to another.

    ``rate`` is expressed in ``substance_unit`` per ``time_unit``; for example
    ``substance_unit="g"``, ``time_unit="per_h"`` is grams per hour. Negative
    rates are rejected: a backwards flow is a different flux with the endpoints
    swapped, and allowing the sign to carry direction makes every downstream
    sum ambiguous.
    """

    substance: str
    source: str
    sink: str
    rate: float
    substance_unit: str = "g"
    time_unit: str = "per_h"
    clock: Clock = Clock.MEAL
    law_ids: tuple[str, ...] = ()
    """Prior that this flux is real and roughly the right size (0-1)."""
    prior: float = 0.7
    note: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.rate < 0:
            raise ValueError(
                f"flux rate must be non-negative, got {self.rate}; "
                "swap source and sink to express the reverse flow"
            )
        if self.time_unit not in _PER_SECOND:
            raise ValueError(f"unknown time_unit {self.time_unit!r}; expected {sorted(_PER_SECOND)}")
        if not (0.0 <= self.prior <= 1.0):
            raise ValueError(f"prior must be in [0,1], got {self.prior}")
        if self.source == self.sink:
            raise ValueError(f"flux source and sink are the same compartment: {self.source!r}")

    @property
    def unit(self) -> str:
        """Human-readable rate unit, e.g. ``g/h``."""
        return f"{self.substance_unit}/{self.time_unit.removeprefix('per_')}"

    def rate_per_second(self) -> float:
        """Rate normalised to ``substance_unit`` per second."""
        return self.rate * _PER_SECOND[self.time_unit]

    def amount_over(self, seconds: float) -> float:
        """
        Amount transferred over an interval, in ``substance_unit``.

        This is the only supported way to turn a flux into a quantity. Reading
        ``rate`` as an amount is the mistake this class exists to prevent.
        """
        if seconds < 0:
            raise ValueError(f"interval must be non-negative, got {seconds}")
        return self.rate_per_second() * seconds

    def reversed(self) -> Flux:
        """The same flow with endpoints swapped."""
        return Flux(
            substance=self.substance,
            source=self.sink,
            sink=self.source,
            rate=self.rate,
            substance_unit=self.substance_unit,
            time_unit=self.time_unit,
            clock=self.clock,
            law_ids=self.law_ids,
            prior=self.prior,
            note=self.note,
            meta=dict(self.meta),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "substance": self.substance,
            "source": self.source,
            "sink": self.sink,
            "rate": self.rate,
            "unit": self.unit,
            "clock": self.clock.value,
            "law_ids": list(self.law_ids),
            "prior": self.prior,
            "note": self.note,
        }


class FluxSet:
    """
    A collection of fluxes with the balance questions attached.

    Kept deliberately small: this answers "what moved, and does it add up",
    and nothing else. Integration over time belongs to the caller that owns
    the timestep.
    """

    def __init__(self, fluxes: Iterable[Flux] = ()):
        self._fluxes: list[Flux] = list(fluxes)

    def __len__(self) -> int:
        return len(self._fluxes)

    def __iter__(self):
        return iter(self._fluxes)

    def add(self, flux: Flux) -> None:
        self._fluxes.append(flux)

    def of(self, substance: str) -> list[Flux]:
        return [f for f in self._fluxes if f.substance == substance]

    def leaving(self, compartment: str) -> list[Flux]:
        return [f for f in self._fluxes if f.source == compartment]

    def entering(self, compartment: str) -> list[Flux]:
        return [f for f in self._fluxes if f.sink == compartment]

    def net_rate(self, compartment: str, substance: str) -> float:
        """
        Net accumulation rate of a substance in a compartment, per second.

        Positive means the compartment is filling.
        """
        gained = sum(
            f.rate_per_second() for f in self.entering(compartment) if f.substance == substance
        )
        lost = sum(
            f.rate_per_second() for f in self.leaving(compartment) if f.substance == substance
        )
        return gained - lost

    def balance_report(self, substance: str, *, tolerance: float = 1e-9) -> dict[str, Any]:
        """
        Per-compartment net rates for one substance, and whether the set balances.

        "Closed" means **every internal compartment is at steady state**: what
        arrives leaves, so nothing silently accumulates in a compartment the
        model is not tracking as a store. The two reserved external endpoints
        are excluded from the check — they exist precisely to absorb flow that
        crosses the model boundary, and requiring them to balance would make
        ingestion and excretion impossible to express.

        Note what this is *not*. Summing net rates over all compartments is
        always exactly zero, because each flux contributes ``+r`` to its sink
        and ``-r`` to its source. A check built on that sum passes for every
        possible set of fluxes, including one that pumps a substance into a
        compartment and never takes it out. The residual reported here is the
        largest internal imbalance instead, which is zero only when the set
        genuinely balances.
        """
        relevant = self.of(substance)
        compartments = sorted({f.source for f in relevant} | {f.sink for f in relevant})
        nets = {c: self.net_rate(c, substance) for c in compartments}
        internal = {c: v for c, v in nets.items() if c not in (SOURCE_EXTERNAL, SINK_EXTERNAL)}
        worst = max((abs(v) for v in internal.values()), default=0.0)
        return {
            "substance": substance,
            "compartments": nets,
            "internal_compartments": sorted(internal),
            "residual_per_s": worst,
            "unbalanced": sorted(c for c, v in internal.items() if abs(v) > tolerance),
            "closed": worst <= tolerance,
            "external_in_per_s": max(0.0, -nets.get(SOURCE_EXTERNAL, 0.0)),
            "external_out_per_s": max(0.0, nets.get(SINK_EXTERNAL, 0.0)),
            "n_fluxes": len(relevant),
        }

    def as_list(self) -> list[dict[str, Any]]:
        return [f.as_dict() for f in self._fluxes]
