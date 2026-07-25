"""
Default physiological subscribers — the non-linear systems, wired as reactors.

Each subscriber fires only on its trigger event and emits a typed reaction (which may
itself trigger further reactions — a cascade). Nothing fires without its trigger:
fail-closed, no fabricated signals. These are teaching-tier signal edges; where a law
grounds the edge it carries the ref.
"""

from __future__ import annotations

from typing import Any, Iterable

from biology_as_code.events.bus import Event, EventBus


def _insulin(event: Event, bus: EventBus) -> None:
    bus.publish(Event("insulin", stage=event.stage, source="insulin_response",
                      note="portal glucose appearance -> pancreatic insulin release"))


def _ampk_from_scfa(event: Event, bus: EventBus) -> None:
    bus.publish(Event("ampk-activation", stage=event.stage, source="energy_sensing",
                      note="colonic SCFA -> AMPK energy sensing", law_refs=("LAW-026",)))


def _ampk_suppressed_by_insulin(event: Event, bus: EventBus) -> None:
    bus.publish(Event("ampk-suppressed", stage=event.stage, source="energy_sensing",
                      note="insulin (fed state) antagonizes AMPK"))


def _mtor(event: Event, bus: EventBus) -> None:
    bus.publish(Event("mtor-activation", stage=event.stage, source="anabolic_signaling",
                      note="amino-acid / MPS signal -> mTORC1 (protein synthesis)"))


def _chylomicron(event: Event, bus: EventBus) -> None:
    bus.publish(Event("chylomicron-export", stage=event.stage, source="lipid_transport",
                      note="fat-soluble vehicle formed -> chylomicron / lymph export",
                      law_refs=("LAW-045",)))


# trigger event type -> reactor
_DEFAULT_SUBSCRIPTIONS = {
    "portal-glucose": _insulin,
    "scfa": _ampk_from_scfa,
    "insulin": _ampk_suppressed_by_insulin,  # cascade: glucose -> insulin -> AMPK down
    "mps-signal": _mtor,
    "fat-soluble-vehicle": _chylomicron,
}


def default_bus() -> EventBus:
    """A bus wired with the default signaling / feedback subscribers."""
    bus = EventBus()
    for event_type, handler in _DEFAULT_SUBSCRIPTIONS.items():
        bus.subscribe(event_type, handler)
    return bus


def react(events: Iterable[Any], bus: EventBus | None = None) -> EventBus:
    """Replay event strings (e.g. ``DigestionTrace.events``) through the bus."""
    bus = bus or default_bus()
    bus.run(list(events))
    return bus


def simulate(food: Any, conditions: Any = None, bus: EventBus | None = None) -> tuple[Any, list[Event]]:
    """digest() then react(): returns ``(trace, reactions)``.

    The trace is the ordered machine walk; the reactions are the non-linear cascade
    the signaling / feedback subscribers produced from its events.
    """
    from biology_as_code.digestion import digest

    trace = digest(food, conditions)
    return trace, react(trace.events, bus).reactions()
