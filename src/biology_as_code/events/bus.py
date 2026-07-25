"""
A tiny, in-process event bus — the non-linear layer over the digestion state machine.

The ordered digestion flow stays a state machine (:func:`biology_as_code.digest`);
this handles the parts of physiology that are *not* a line: hormonal signaling and
feedback loops react to events and can emit further events (a cascade). Zero
dependency; the failure mode is fail-closed — a subscriber with nothing to say emits
nothing, never a fabricated signal.

In the AWS model the machines already borrow, this bus is **EventBridge**: Step
Functions emits, subscribers fan out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

_MAX_EVENTS = 500  # cascade cap — a feedback loop can never run forever


@dataclass(frozen=True)
class Event:
    """One physiological event. ``type`` is the machine emit or a reaction name."""

    type: str
    stage: str = ""
    source: str = "machine"  # "machine" | a subscriber name
    note: str = ""
    law_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "stage": self.stage,
            "source": self.source,
            "note": self.note,
            "law_refs": list(self.law_refs),
        }


Handler = Callable[["Event", "EventBus"], None]


@dataclass
class EventBus:
    """Subscribe handlers to event types; publish events; record the cascade.

    A handler receives ``(event, bus)`` and may ``bus.publish(...)`` further events.
    ``subscribe("*", handler)`` sees every event.
    """

    _subs: dict[str, list[Handler]] = field(default_factory=dict)
    emitted: list[Event] = field(default_factory=list)
    _queue: list[Event] = field(default_factory=list)
    _draining: bool = False

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subs.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        # Enqueue and drain iteratively, so a cascade (a handler that publishes) never
        # recurses — a deep feedback loop must not blow the Python stack.
        self._queue.append(event)
        if self._draining:
            return
        self._draining = True
        try:
            while self._queue and len(self.emitted) < _MAX_EVENTS:
                current = self._queue.pop(0)
                self.emitted.append(current)
                for handler in list(self._subs.get(current.type, ())) + list(self._subs.get("*", ())):
                    handler(current, self)
        finally:
            self._draining = False

    def run(self, events: list[Event | str]) -> list[Event]:
        """Publish a sequence of events (strings are wrapped) and return the cascade."""
        for item in events:
            self.publish(item if isinstance(item, Event) else Event(type=str(item)))
        return self.emitted

    def reactions(self) -> list[Event]:
        """Only the events that subscribers produced (source != 'machine')."""
        return [e for e in self.emitted if e.source != "machine"]
