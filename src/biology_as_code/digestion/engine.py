"""
``digest(food, conditions) -> DigestionTrace`` — how the body handles a
standardized food, under conditions.

This is the sibling of the claim auditor. The auditor answers *is a claim true*;
this answers *what does the body do with this food*. Both walk the same physiology:

- The **machine layer** (teaching-FLOW) runs the food through the full-digest state
  machine and records the stage path, the **events** each stage emits, and the edge
  cases that fired — reusing :func:`run_digestion`.
- The **handling layer** (fail-closed, law-backed) evaluates each cargo nutrient
  against the gate/bound table (:mod:`biology_as_code.audit.gates`), under the four
  seats. A gate whose required co-factor is undeclared is ``UNEVALUABLE``, never a
  default pass.

Composition, not duplication: it wires ``packets`` + ``machines`` + ``audit.gates``
together behind one call and adds the missing input — :class:`Conditions`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from biology_as_code.audit.gates import bounds_for, gates_for
from biology_as_code.digestion.conditions import Conditions
from biology_as_code.machines.digestion import meal_to_context, run_digestion
from biology_as_code.packets.loader import FoodPacket, get_packet

# Categorical matrix state -> the 0-1 fraction the machine context expects.
_MATRIX_FRACTION = {"intact": 1.0, "partial": 0.5, "destroyed": 0.1, "unknown": 0.8}


@dataclass(frozen=True)
class BoundFinding:
    """One bound rule that fired, with the co-present fact that triggered it."""

    triggered_by: str
    direction: str  # EXPANDS_BOUND | NARROWS_BOUND
    note: str
    law_refs: tuple[str, ...]


@dataclass(frozen=True)
class NutrientHandling:
    """What the body does with one cargo nutrient, under the given conditions."""

    nutrient: str
    gate: str  # "open" | "closed" | "unevaluable" | "none"
    gate_note: str
    bounds: tuple[BoundFinding, ...]
    law_refs: tuple[str, ...]

    @property
    def headline(self) -> str:
        refs = f" ({', '.join(self.law_refs)})" if self.law_refs else ""
        if self.gate == "closed":
            return f"{self.nutrient}: transport gate CLOSED — path shut{refs}"
        if self.gate == "unevaluable":
            return f"{self.nutrient}: gate UNEVALUABLE — required co-factor not declared"
        dirs = ", ".join(f"{b.direction} ({b.triggered_by})" for b in self.bounds)
        if self.gate == "open":
            return f"{self.nutrient}: gate open" + (f"; bound {dirs}{refs}" if dirs else "")
        return f"{self.nutrient}: path open" + (f"; bound {dirs}{refs}" if dirs else "; no bound modifier declared")

    def to_dict(self) -> dict[str, Any]:
        return {
            "nutrient": self.nutrient,
            "gate": self.gate,
            "gate_note": self.gate_note,
            "bounds": [
                {"triggered_by": b.triggered_by, "direction": b.direction, "note": b.note, "law_refs": list(b.law_refs)}
                for b in self.bounds
            ],
            "law_refs": list(self.law_refs),
        }


@dataclass
class DigestionTrace:
    """The result of digesting a food under conditions."""

    food: str
    conditions: dict[str, Any]
    path: tuple[str, ...]
    status: str
    events: tuple[str, ...]
    fired_edge_cases: tuple[dict[str, Any], ...]
    handling: tuple[NutrientHandling, ...]

    @property
    def summary(self) -> str:
        return " | ".join(h.headline for h in self.handling) or "no typed cargo to handle"

    def to_dict(self) -> dict[str, Any]:
        return {
            "food": self.food,
            "conditions": self.conditions,
            "path": list(self.path),
            "status": self.status,
            "events": list(self.events),
            "fired_edge_cases": [dict(ec) for ec in self.fired_edge_cases],
            "handling": [h.to_dict() for h in self.handling],
            "summary": self.summary,
        }


def _declares(packet: FoodPacket, extra: dict[str, Any], name: str) -> bool:
    return name in extra or packet.declares(name)


def _value(packet: FoodPacket, extra: dict[str, Any], name: str) -> Any:
    return extra[name] if name in extra else packet.partner(name)


def packet_to_context(packet: FoodPacket, conditions: Conditions | None = None) -> dict[str, Any]:
    """Bridge a standardized packet + conditions into the machine context namespace.

    Fail-closed on the fat field: ``meal.fatG`` is only asserted when the packet (or a
    condition) actually declares dietary lipid, so the duodenum's low-fat edge case
    fires on *declared* low fat, never on silence.
    """
    conditions = conditions or Conditions()
    extra = dict(conditions.partners)
    ctx = meal_to_context(
        matrix_integrity=_MATRIX_FRACTION.get(packet.matrix_integrity, 0.8),
        host=conditions.host_context(),
        intake={"intake.food": 1 if packet.cargo else 0},
    )
    fat = extra.get("dietary_lipid_g", packet.partner("dietary_lipid_g"))
    lipid_phase = extra.get("lipid_phase_present", packet.partner("lipid_phase_present"))
    if isinstance(fat, (int, float)) and not isinstance(fat, bool):
        ctx["meal.fatG"] = float(fat)
    elif lipid_phase is True:
        ctx["meal.fatG"] = 12.0  # a declared lipid phase clears the low-fat teaching edge
    else:
        ctx.pop("meal.fatG", None)  # unknown fat: do not fire the low-fat edge as if zero
    return ctx


def _handle_nutrient(nutrient: str, packet: FoodPacket, extra: dict[str, Any]) -> NutrientHandling:
    law_refs: set[str] = set()
    gate_state = "none"
    gate_note = ""
    for rule in gates_for(nutrient):
        law_refs |= set(rule.law_refs)
        declared = [f for f in rule.fields if _declares(packet, extra, f)]
        if not declared:
            gate_state = "unevaluable"
            gate_note = rule.gate_note
        elif not any(rule.satisfied_by(f, _value(packet, extra, f)) for f in declared):
            gate_state = "closed"
            gate_note = rule.gate_note
            break
        else:
            gate_state = "open"
            gate_note = rule.gate_note

    findings: list[BoundFinding] = []
    for rule in bounds_for(nutrient):
        if rule.source == "matrix":
            if packet.matrix_integrity == rule.triggered_by:
                findings.append(BoundFinding(rule.triggered_by, rule.direction, rule.note, rule.law_refs))
                law_refs |= set(rule.law_refs)
            continue
        if _declares(packet, extra, rule.triggered_by) and rule.satisfied_by(_value(packet, extra, rule.triggered_by)):
            findings.append(BoundFinding(rule.triggered_by, rule.direction, rule.note, rule.law_refs))
            law_refs |= set(rule.law_refs)

    return NutrientHandling(nutrient, gate_state, gate_note, tuple(findings), tuple(sorted(law_refs)))


def digest(food: FoodPacket | str, conditions: Conditions | None = None) -> DigestionTrace:
    """Digest a standardized food under conditions. Accepts a packet or a packet id."""
    packet = get_packet(food) if isinstance(food, str) else food
    conditions = conditions or Conditions()
    context = packet_to_context(packet, conditions)

    run = run_digestion(context)
    proc = run["process"]
    events = [e for step in proc["path"] for e in (step.get("emits") or [])]
    events += [e for stage in run["stages"] for e in (stage.get("emits") or [])]

    extra = dict(conditions.partners)
    handling = tuple(_handle_nutrient(n, packet, extra) for n in packet.cargo_nutrients())

    return DigestionTrace(
        food=packet.common_name,
        conditions=conditions.to_dict(),
        path=tuple(step["state"] for step in proc["path"]),
        status=proc["status"],
        events=tuple(events),
        fired_edge_cases=tuple(run["firedEdgeCases"]),
        handling=handling,
    )
