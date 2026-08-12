"""
Compartment — the formal shape an organ has to satisfy.

The engine already had organs: ``ORGAN_BOUNDS`` gives each one a pH range, a
transit window and a secretion volume, and the seven-system map says what each
one is for. What it did not have was a *contract*. Nothing said what an organ
does to a packet, so nothing could check that a new one behaved like the
existing ones, and nothing could substitute a modified organ for a default one.

A compartment does three things and this protocol names them:

``accept``
    Decide whether a packet may enter, and in what condition. This is where
    bounds act as admission criteria.

``transform``
    Do the compartment's work: change the packet's state, emit signals, and
    declare the fluxes that carry material out.

``emit``
    Say where the packet goes next. Branching is allowed; an empty result means
    the packet terminates here.

Exotic compartments
-------------------
A post-surgical host is not a host with a scaling factor applied. After a
sleeve gastrectomy the stomach's *bounds* change — reservoir volume, emptying
profile, acid output — and after a bypass the *topology* changes, because a
segment of small intestine is no longer in the path at all. Neither is
expressible as a multiplier on the default organ.

So ``post_surgical`` states are modelled as **exotic compartments**: real
compartments that override the defaults, registered against the same protocol.
:class:`ExoticCompartment` carries the override explicitly, along with the
reason it exists, so a report can say *which* compartment was non-default and
why rather than silently producing different numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from biology_as_code.engine.fluxes import Flux

if TYPE_CHECKING:  # pragma: no cover - typing only
    from biology_as_code.engine.processes import Context, HostStateLike, PacketState

__all__ = [
    "Admission",
    "Compartment",
    "CompartmentResult",
    "ExoticCompartment",
    "SimpleCompartment",
    "compartment_registry",
]


@dataclass(frozen=True)
class Admission:
    """Outcome of :meth:`Compartment.accept`."""

    admitted: bool
    reason: str = ""
    """Bounds that were checked, for the report trail."""
    bounds_checked: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.admitted


@dataclass
class CompartmentResult:
    """Outcome of :meth:`Compartment.transform`."""

    packet: PacketState
    """Signal ids emitted, resolvable against the signal catalog."""
    signals: tuple[str, ...] = ()
    """Material leaving this compartment, as rate-typed fluxes."""
    fluxes: tuple[Flux, ...] = ()
    law_ids: tuple[str, ...] = ()
    log: list[str] = field(default_factory=list)


@runtime_checkable
class Compartment(Protocol):
    """
    A place a packet can be, that does something to it.

    Implementations need not inherit from anything — the protocol is
    ``runtime_checkable``, so an organ defined elsewhere satisfies it by having
    the right methods.
    """

    #: Stable id, matching the key in ``ORGAN_BOUNDS`` where one exists.
    id: str

    def accept(self, packet: PacketState, host: HostStateLike, ctx: Context) -> Admission:
        """May this packet enter, given the host and context?"""
        ...

    def transform(
        self, packet: PacketState, host: HostStateLike, ctx: Context
    ) -> CompartmentResult:
        """Do this compartment's work on the packet."""
        ...

    def emit(self, result: CompartmentResult) -> tuple[str, ...]:
        """Ids of the compartments the packet may go to next."""
        ...


@dataclass
class SimpleCompartment:
    """
    A minimal concrete compartment, for compartments whose behaviour is fully
    described by their bounds and their downstream links.

    Real organs subclass or replace this; it exists so that a compartment can be
    declared without writing three methods that only restate the bounds.
    """

    id: str
    label: str = ""
    downstream: tuple[str, ...] = ()
    """pH window the packet must be inside, or None for no pH admission rule."""
    ph_range: tuple[float, float] | None = None
    law_ids: tuple[str, ...] = ()
    note: str = ""

    def accept(self, packet: PacketState, host: HostStateLike, ctx: Context) -> Admission:
        if self.ph_range is None:
            return Admission(True, "no pH admission rule", ())
        ph = getattr(packet, "ph", None)
        if ph is None:
            # Absence of a measurement is not a failure; it is an unknown, and
            # the packet is admitted with the gap recorded.
            return Admission(True, "packet declares no pH; admitted unchecked", ("ph",))
        lo, hi = self.ph_range
        if lo <= ph <= hi:
            return Admission(True, f"pH {ph} within [{lo}, {hi}]", ("ph",))
        return Admission(False, f"pH {ph} outside [{lo}, {hi}]", ("ph",))

    def transform(
        self, packet: PacketState, host: HostStateLike, ctx: Context
    ) -> CompartmentResult:
        return CompartmentResult(packet=packet, law_ids=self.law_ids)

    def emit(self, result: CompartmentResult) -> tuple[str, ...]:
        return self.downstream


@dataclass
class ExoticCompartment:
    """
    A compartment that overrides a default one.

    Wraps the compartment it replaces so the delta is inspectable: a report can
    name the base organ, the override, and the reason. Used for post-surgical
    anatomy, but nothing about it is surgery-specific — a stoma, a resection or
    an experimentally clamped organ all fit.
    """

    id: str
    """Id of the default compartment this replaces."""
    overrides: str
    delegate: Compartment
    """Why the default does not apply. Required — an unexplained override is
    indistinguishable from a bug."""
    reason: str
    """Compartment ids removed from the path entirely (e.g. bypassed segments)."""
    bypasses: tuple[str, ...] = ()
    evidence_state: str = "candidate"

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(f"exotic compartment {self.id!r} must state why it overrides a default")

    def accept(self, packet: PacketState, host: HostStateLike, ctx: Context) -> Admission:
        return self.delegate.accept(packet, host, ctx)

    def transform(
        self, packet: PacketState, host: HostStateLike, ctx: Context
    ) -> CompartmentResult:
        result = self.delegate.transform(packet, host, ctx)
        result.log.append(f"exotic compartment {self.id} overrode {self.overrides}: {self.reason}")
        return result

    def emit(self, result: CompartmentResult) -> tuple[str, ...]:
        return tuple(c for c in self.delegate.emit(result) if c not in self.bypasses)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "overrides": self.overrides,
            "bypasses": list(self.bypasses),
            "reason": self.reason,
            "evidence_state": self.evidence_state,
        }


def compartment_registry() -> dict[str, SimpleCompartment]:
    """
    Default compartments built from the existing organ bounds.

    Derived from ``ORGAN_BOUNDS`` rather than duplicating it, so the bounds stay
    single-sourced. The downstream chain is the canonical GI path.
    """
    from biology_as_code.engine.geography.organ_bounds import ORGAN_BOUNDS

    chain = {
        "oral": ("stomach",),
        "stomach": ("small_intestine",),
        "small_intestine": ("large_intestine",),
        "large_intestine": (),
        "pancreas": ("small_intestine",),
        "liver_gallbladder": ("small_intestine",),
    }
    out: dict[str, SimpleCompartment] = {}
    for key, bounds in ORGAN_BOUNDS.items():
        out[key] = SimpleCompartment(
            id=key,
            label=bounds.name,
            downstream=chain.get(key, ()),
            ph_range=bounds.pH_range,
            note=bounds.notes,
        )
    return out
