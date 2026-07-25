"""
Event / subscriber layer — the non-linear physiology over the digestion machine.

    from biology_as_code.events import simulate

    trace, reactions = simulate("ex.lentils.with_ascorbate")
    [r.type for r in reactions]   # e.g. ['insulin', 'ampk-suppressed', 'ampk-activation']

The ordered flow stays a state machine (:func:`biology_as_code.digest`); this fans
its events out to signaling / feedback subscribers that react in a cascade,
fail-closed. In the AWS model: Step Functions -> EventBridge -> subscribers.
"""

from __future__ import annotations

from biology_as_code.events.bus import Event, EventBus
from biology_as_code.events.subscribers import default_bus, react, simulate

__all__ = ["Event", "EventBus", "default_bus", "react", "simulate"]
