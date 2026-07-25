"""
The constitution's four evaluation seats, as one typed input.

`docs/constitution.md` says a law is read from four seats: **Host** (this machine's
config), **Partner** (same-meal co-present fields), **Stage** (where on the L1→L5
path the edge attaches), and **Clock** (concurrency / phase). Until now those were
scattered — host state in `scenarios`, partners in the packet, life stage in
`LifecycleStage`. :class:`Conditions` gathers them so the *same* standardized food
can be handled differently under different conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Conditions:
    """The four seats. Every field is optional; the defaults are a fed adult host.

    ``partners`` override and extend the packet's own partners, so
    ``digest(lentils, Conditions(partners={"tea_tannins": True}))`` narrows the iron
    bound even when the packet never mentioned tea — the whole point of "under what
    conditions".
    """

    host: dict[str, Any] = field(default_factory=dict)
    partners: dict[str, Any] = field(default_factory=dict)
    stage: str = "adult"
    clock: str = "fed"

    def host_context(self) -> dict[str, Any]:
        """``host.*`` keys for the machine context (namespaced if not already)."""
        return {
            (key if key.startswith("host.") else f"host.{key}"): value
            for key, value in self.host.items()
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": dict(self.host),
            "partners": dict(self.partners),
            "stage": self.stage,
            "clock": self.clock,
        }


def fed(**host: Any) -> Conditions:
    """A fed adult host, with optional ``host.*`` overrides (e.g. ``bileCapacity=0.3``)."""
    return Conditions(host=host, clock="fed")


def fasted(**host: Any) -> Conditions:
    """An overnight-fasted adult host."""
    return Conditions(host=host, clock="fasted")
