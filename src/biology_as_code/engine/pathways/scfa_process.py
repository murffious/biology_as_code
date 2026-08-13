"""
The colon SCFA pathway, adapted to the Process signature.

This is the worked demonstration that :mod:`biology_as_code.engine.processes`
fits existing code rather than requiring a rewrite. Nothing in
``colon_scfa.py`` changed: the same node graph, the same modifiers, the same
``colon_scfa_context_from_engine`` helper. What is added is the signature —

    (PacketState, HostState, Context) -> (PacketState', Signals, Fluxes)

— and the three things it makes explicit that the bare walk left implicit.

**The packet.** The walk returned a ``yield_factor``, a bare multiplier with no
statement about what it multiplied. Here it changes the fermentable-substrate
amount in a :class:`~biology_as_code.engine.processes.PacketState`, and the
process appends itself to the packet's method identity, so a packet carries the
record of what has been done to it.

**The signals.** L cells co-secrete GLP-1 and PYY in response to colonic
fermentation. That was true before and appeared nowhere in the code. Now the
process emits catalog signal ids, checkable against
:mod:`biology_as_code.engine.signals`.

**The fluxes.** SCFA moving from the colon lumen into the host was previously a
number appearing in a report. It is now a rate-typed
:class:`~biology_as_code.engine.fluxes.Flux` from ``large_intestine`` to
``portal``, with the unfermented remainder going to ``external.excreted`` so
the substrate balance closes.

Magnitudes are unchanged from the underlying pathway and remain provisional
(``magnitude_locked`` is low on every node). This module adds structure, not
confidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from biology_as_code.engine.clocks import Clock
from biology_as_code.engine.fluxes import SINK_EXTERNAL, Flux
from biology_as_code.engine.laws.walk import walk_pathway
from biology_as_code.engine.pathways.colon_scfa import (
    COLON_SCFA_PATHWAY,
    colon_scfa_context_from_engine,
)
from biology_as_code.engine.processes import (
    Context,
    HostStateLike,
    PacketState,
    ProcessResult,
)

__all__ = ["ColonFermentationProcess", "COLON_FERMENTATION"]

#: Signals co-secreted by L cells on colonic fermentation. Catalog ids, so a
#: typo fails at import of the catalog rather than silently naming nothing.
_L_CELL_SIGNALS = ("glp1", "pyy")


@dataclass
class ColonFermentationProcess:
    """Colonic fermentation of ileal residue into SCFA, as a Process."""

    id: str = "colon.fermentation"
    substance: str = "fermentable_substrate"
    product: str = "scfa"
    source_compartment: str = "large_intestine"
    sink_compartment: str = "portal"

    def __call__(self, packet: PacketState, host: HostStateLike, ctx: Context) -> ProcessResult:
        flags = self._context_flags(host, ctx)
        walk = walk_pathway(
            COLON_SCFA_PATHWAY,
            "colon.residue_arrival",
            cargo=self.substance,
            context=flags,
        )

        substrate = packet.amount(self.substance)
        recovered = substrate * walk.yield_factor
        # Yield factor can exceed 1 when enhancers fire; substrate that becomes
        # SCFA cannot exceed substrate that arrived, so the excess is a claim
        # about efficiency of conversion, not about mass. Cap at the substrate
        # and record the clip rather than letting a balance model see mass
        # appear from nowhere.
        clipped = min(recovered, substrate)
        unfermented = substrate - clipped

        cargo = {
            **dict(packet.cargo),
            self.substance: unfermented,
            self.product: packet.amount(self.product) + clipped,
        }

        fluxes: list[Flux] = []
        hours = ctx.dt_seconds / 3600.0 if ctx.dt_seconds > 0 else 0.0
        if hours > 0:
            if clipped > 0:
                fluxes.append(
                    Flux(
                        substance=self.product,
                        source=self.source_compartment,
                        sink=self.sink_compartment,
                        rate=clipped / hours,
                        substance_unit="mmol",
                        time_unit="per_h",
                        clock=Clock.MEAL,
                        law_ids=("LAW-025", "LAW-026"),
                        prior=walk.prior_product,
                        note="SCFA uptake to portal circulation; magnitude not locked",
                    )
                )
            if unfermented > 0:
                fluxes.append(
                    Flux(
                        substance=self.substance,
                        source=self.source_compartment,
                        sink=SINK_EXTERNAL,
                        rate=unfermented / hours,
                        substance_unit="g",
                        time_unit="per_h",
                        clock=Clock.MEAL,
                        law_ids=("LAW-025",),
                        prior=walk.prior_product,
                        note="substrate leaving unfermented; closes the substrate balance",
                    )
                )

        log = list(walk.log)
        if recovered > substrate:
            log.append(
                f"{self.id}: yield_factor {walk.yield_factor:.3f} implied "
                f"{recovered:.4f} from {substrate:.4f} substrate; clipped to substrate "
                "(conversion efficiency cannot create mass)"
            )

        signals = _L_CELL_SIGNALS if clipped > 0 else ()

        return ProcessResult(
            packet=packet.evolve(cargo=cargo, compartment=self.source_compartment).with_operation(
                self.id
            ),
            signals=signals,
            fluxes=tuple(fluxes),
            law_ids=("LAW-017", "LAW-023", "LAW-025", "LAW-026"),
            log=log,
        )

    def _context_flags(self, host: HostStateLike, ctx: Context) -> dict[str, Any]:
        """
        Build walk-context flags from host state, then let explicit flags win.

        Reads the two host fields the pathway actually depends on through the
        ``HostStateLike`` path interface, so the dependency is visible and the
        binding resolver can check it. Explicit context flags override, so a
        caller can always pin a gate for a test.
        """
        fermentable = host.get("fast_state.fermentable_fraction", 0.55)
        diversity = host.get("slow_state.microbiome_diversity", 0.8)
        derived = colon_scfa_context_from_engine(
            fermentable_fraction=float(fermentable),
            microbiome_diversity=float(diversity),
        )
        return {**derived, **dict(ctx.flags)}


#: The published instance.
COLON_FERMENTATION = ColonFermentationProcess()
