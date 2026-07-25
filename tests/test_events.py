"""
The event / subscriber layer — non-linear signaling over the digestion machine.
"""

from __future__ import annotations

from biology_as_code.events import Event, EventBus, default_bus, simulate


def test_bus_publishes_and_records():
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe("a", lambda e, b: seen.append(e.type))
    bus.publish(Event("a"))
    assert seen == ["a"]
    assert len(bus.emitted) == 1


def test_cascade_glucose_to_insulin_to_ampk():
    bus = default_bus()
    bus.run(["portal-glucose"])
    types = [e.type for e in bus.emitted]
    assert "insulin" in types  # portal glucose -> insulin
    assert "ampk-suppressed" in types  # ...and the 2nd-order cascade


def test_scfa_activates_ampk_with_law_ref():
    bus = default_bus()
    bus.run(["scfa"])
    ampk = next(e for e in bus.emitted if e.type == "ampk-activation")
    assert "LAW-026" in ampk.law_refs


def test_fail_closed_no_trigger_no_reaction():
    bus = default_bus()
    bus.run(["some-unrelated-event"])
    assert bus.reactions() == []  # nothing fabricated without a trigger


def test_cascade_terminates_on_self_loop():
    bus = EventBus()
    bus.subscribe("loop", lambda e, b: b.publish(Event("loop", source="x")))
    bus.run(["loop"])
    assert len(bus.emitted) <= 500  # the cascade cap holds; no hang


def test_simulate_returns_trace_and_reactions():
    trace, reactions = simulate("ex.spinach_salad.with_oil")
    assert trace.path
    assert any(r.type == "insulin" for r in reactions)
    assert all(r.source != "machine" for r in reactions)


def test_event_serialises():
    assert Event("portal-glucose", law_refs=("LAW-026",)).to_dict()["law_refs"] == ["LAW-026"]
