"""
Process — the one signature every transformation shares.

Digestion steps, pathway walks and simulation phases all do the same shape of
work, and all three expressed it differently: a phase mutated a shared
``MetabolicState``, a pathway walk returned a ``WalkResult``, a digestion helper
returned a bare dict. Three shapes for one idea means no composition, no
uniform trace, and no way to test that a new step behaves like the existing
ones.

The signature is::

    (PacketState, HostState, Context) -> (PacketState', Signals, Fluxes)

Read as: *what is being acted on*, *whose body is acting*, and *under what
circumstances* — producing a changed packet, the messages the body sent, and
the material that moved. Everything a process is allowed to do appears in that
line. In particular a process may not reach for host state that was not passed
in, and may not move material except by declaring a flux.

Purity
------
A process must not mutate its inputs. :meth:`PacketState.evolve` returns a new
packet; the existing phase functions that mutate ``MetabolicState`` in place are
adapted rather than rewritten (see :func:`process_from_pathway`), so the
protocol can be adopted incrementally without a flag day.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Protocol, runtime_checkable

from biology_as_code.engine.clocks import Clock
from biology_as_code.engine.fluxes import Flux

__all__ = [
    "Context",
    "HostStateLike",
    "PacketState",
    "Process",
    "ProcessResult",
    "process_from_pathway",
]


@dataclass(frozen=True)
class PacketState:
    """
    A packet as it exists partway through the gut, not as it exists on a label.

    ``identity`` is what the food *is* and does not change as it moves.
    ``method_identity`` is the ordered list of process operations already
    applied to it — the field that distinguishes whole almonds from almond
    flour, which have the same identity and the same analyte panel.
    """

    identity: str
    """Ordered process operations already applied, oldest first."""
    method_identity: tuple[str, ...] = ()
    """Substance amounts currently in the packet, keyed by substance id."""
    cargo: Mapping[str, float] = field(default_factory=dict)
    """Where the packet currently is."""
    compartment: str = "oral"
    """intact | partial | destroyed | unknown."""
    matrix_integrity: str = "unknown"
    ph: float | None = None
    """Fraction of cargo physically reachable by enzymes (0-1); None = unknown."""
    bioaccessible_fraction: float | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)

    def evolve(self, **changes: Any) -> PacketState:
        """A new packet with the given fields changed. Never mutates in place."""
        return replace(self, **changes)

    def with_operation(self, op: str) -> PacketState:
        """Record one more process operation in the method identity."""
        return replace(self, method_identity=(*self.method_identity, op))

    def amount(self, substance: str) -> float:
        return float(self.cargo.get(substance, 0.0))


@runtime_checkable
class HostStateLike(Protocol):
    """
    The minimum a process may assume about host state.

    Deliberately tiny. A process that needs more should take it from
    :class:`Context`, where the dependency is visible, rather than growing this
    protocol until it means "any host at all".
    """

    def get(self, path: str, default: Any = None) -> Any:
        """Read a host field by dotted path, e.g. ``fast_state.gastric_ph``."""
        ...


@dataclass(frozen=True)
class Context:
    """
    Circumstances that are neither the packet nor the host.

    ``clock`` is the clock this invocation runs on; ``dt_seconds`` is the
    interval it covers. A process that integrates a flux must use ``dt_seconds``
    rather than assuming a step size.
    """

    clock: Clock = Clock.MEAL
    dt_seconds: float = 0.0
    """Free-form boolean gates and scalars, as the existing walks already use."""
    flags: Mapping[str, Any] = field(default_factory=dict)
    note: str = ""

    def flag(self, key: str, default: Any = None) -> Any:
        return self.flags.get(key, default)


@dataclass
class ProcessResult:
    """The three-part return: changed packet, signals emitted, material moved."""

    packet: PacketState
    signals: tuple[str, ...] = ()
    fluxes: tuple[Flux, ...] = ()
    law_ids: tuple[str, ...] = ()
    log: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "packet": {
                "identity": self.packet.identity,
                "method_identity": list(self.packet.method_identity),
                "compartment": self.packet.compartment,
                "cargo": dict(self.packet.cargo),
                "matrix_integrity": self.packet.matrix_integrity,
                "bioaccessible_fraction": self.packet.bioaccessible_fraction,
            },
            "signals": list(self.signals),
            "fluxes": [f.as_dict() for f in self.fluxes],
            "law_ids": list(self.law_ids),
            "log": list(self.log),
        }


@runtime_checkable
class Process(Protocol):
    """Anything that transforms a packet. One call, one signature."""

    #: Stable id for the trace.
    id: str

    def __call__(
        self, packet: PacketState, host: HostStateLike, ctx: Context
    ) -> ProcessResult: ...


@dataclass
class _PathwayProcess:
    """Adapter: an existing pathway-node graph, exposed as a :class:`Process`."""

    id: str
    nodes: Mapping[str, Any]
    start: str
    substance: str
    source_compartment: str
    sink_compartment: str
    context_builder: Any = None

    def __call__(self, packet: PacketState, host: HostStateLike, ctx: Context) -> ProcessResult:
        from biology_as_code.engine.laws.walk import walk_pathway

        flags = dict(ctx.flags)
        if self.context_builder is not None:
            flags = {**self.context_builder(**dict(ctx.flags)), **flags}

        walk = walk_pathway(self.nodes, self.start, cargo=self.substance, context=flags)

        before = packet.amount(self.substance)
        after = before * walk.yield_factor
        cargo = {**dict(packet.cargo), self.substance: after}

        fluxes: tuple[Flux, ...] = ()
        if ctx.dt_seconds > 0 and after > 0:
            fluxes = (
                Flux(
                    substance=self.substance,
                    source=self.source_compartment,
                    sink=self.sink_compartment,
                    rate=after / (ctx.dt_seconds / 3600.0),
                    substance_unit="rel",
                    time_unit="per_h",
                    clock=ctx.clock,
                    law_ids=tuple(sorted({lid for n in self.nodes.values() for lid in n.law_ids})),
                    prior=walk.prior_product,
                    note=f"{self.id}: yield_factor {walk.yield_factor:.3f}",
                ),
            )

        return ProcessResult(
            packet=packet.evolve(cargo=cargo).with_operation(self.id),
            signals=(),
            fluxes=fluxes,
            law_ids=tuple(sorted({lid for n in self.nodes.values() for lid in n.law_ids})),
            log=list(walk.log),
        )


def process_from_pathway(
    *,
    process_id: str,
    nodes: Mapping[str, Any],
    start: str,
    substance: str,
    source_compartment: str,
    sink_compartment: str,
    context_builder: Any = None,
) -> Process:
    """
    Wrap an existing pathway-node graph as a :class:`Process`.

    This is the adoption path for the protocol. The pathway keeps its current
    shape and its current tests; the adapter supplies the signature, turns the
    walk's ``yield_factor`` into a change in packet cargo, and expresses the
    movement as a :class:`Flux` instead of leaving it implicit.

    ``context_builder`` is an existing ``*_context_from_engine`` helper, when
    the pathway has one. Explicit flags in the :class:`Context` win over
    anything the builder derives, so a caller can always pin a gate.
    """
    return _PathwayProcess(
        id=process_id,
        nodes=nodes,
        start=start,
        substance=substance,
        source_compartment=source_compartment,
        sink_compartment=sink_compartment,
        context_builder=context_builder,
    )
