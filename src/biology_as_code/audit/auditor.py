"""
Fail-closed claim auditor.

Takes a nutrition claim plus a typed food packet and walks the L1→L5 delivery
ladder, returning a :class:`ClaimAudit` that serialises to
``schemas/claim_audit.schema.json``.

The verdict lattice
-------------------

``REFUSE``
    The claim is not auditable *as stated* — soft or marketing verbs with no
    typed mechanism and no endpoint. Returned before any packet is read, because
    there is nothing to evaluate against. Refusing is a result, not a failure.

``UNEVALUABLE``
    The claim is well formed but the packet does not declare the facts needed to
    decide. This is the load-bearing case: a packet that is silent about dietary
    lipid is *not* a packet that declares zero. 41 of the repository's 47 packets
    are stubs and must land here.

``Busted``
    A gate rule fired against a fact the packet actually declared. The path is
    shut, so the claim is false rather than small.

``Plausible``
    The gate is open and at least one bound direction was determined. The
    strongest verdict a mechanism walk can reach.

``Confirmed``
    **Never emitted by this module.** Confirmation is an evidence-tier judgement
    about magnitude and endpoint, not something a mechanism walk can establish.
    The value stays in the schema so an evidence-promotion step can set it later;
    ``test_claim_audit.py`` asserts the auditor cannot produce it.

The distinction between "not declared" and "declared false" is the whole design.
:meth:`FoodPacket.declares` separates them, and everything else follows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from biology_as_code.audit.gates import (
    ENDPOINT_VERB_CLASSES,
    UNAUDITABLE_VERB_CLASSES,
    bounds_for,
    gates_for,
)
from biology_as_code.packets.loader import FoodPacket

GateCheck = str  # "pass" | "fail" | "unevaluable"
Verdict = str  # "Busted" | "Plausible" | "Confirmed" | "UNEVALUABLE" | "REFUSE"


@dataclass(frozen=True)
class Claim:
    """A nutrition claim, atomised into an auditable shape.

    ``nutrient`` is the cargo the claim is about and must match a packet cargo
    key. ``verb_class`` comes from ``schemas/relation_enums.subset.json``.
    """

    id: str
    surface_claim: str
    verb_class: str
    nutrient: str | None = None
    surface_verb: str = ""
    atomized: tuple[str, ...] = ()

    @property
    def is_endpoint_claim(self) -> bool:
        return self.verb_class in ENDPOINT_VERB_CLASSES

    @property
    def is_auditable(self) -> bool:
        """False for soft/marketing/hedge verbs, or when no nutrient is named."""
        if self.verb_class in UNAUDITABLE_VERB_CLASSES:
            return False
        return bool(self.nutrient)


@dataclass(frozen=True)
class BoundFinding:
    """One bound rule that fired, with the fact that triggered it."""

    direction: str
    note: str
    triggered_by: str
    law_refs: tuple[str, ...]


@dataclass
class ClaimAudit:
    """Result of an audit. Serialises to ``schemas/claim_audit.schema.json``."""

    id: str
    surface_claim: str
    verdict: Verdict
    gate_check: GateCheck
    gate_note: str = ""
    kingdom: str = "unknown"
    atomized: tuple[str, ...] = ()
    l1_to_l5: dict[str, str] = field(default_factory=dict)
    integrity: str = "unknown"
    rosetta: dict[str, str] = field(default_factory=dict)
    bound_findings: tuple[BoundFinding, ...] = ()
    law_refs: tuple[str, ...] = ()
    packet_id: str | None = None
    unevaluable_because: tuple[str, ...] = ()

    @property
    def is_refusal(self) -> bool:
        return self.verdict == "REFUSE"

    @property
    def is_unevaluable(self) -> bool:
        return self.verdict == "UNEVALUABLE"

    @property
    def constitution_state(self) -> str:
        """The audit expressed in ``docs/constitution.md``'s five-state vocabulary.

        The constitution and ``claim_audit.schema.json`` speak different languages.
        The constitution's states answer *can this be evaluated* — HOLDS,
        UNEVALUABLE, REFUSE, OPEN, REFUTED. The schema's verdicts answer *what is
        the result* — Busted, Plausible, Confirmed, plus UNEVALUABLE and REFUSE,
        which appear in both. They are related but not the same axis.

        The mapping is deliberately lossy in one direction and that loss is
        informative:

        ==================  ==================================================
        ``verdict``         ``constitution_state``
        ==================  ==================================================
        ``REFUSE``          ``REFUSE``
        ``Plausible``       ``HOLDS``   (gate open, bound evaluable)
        ``Confirmed``       ``HOLDS``   (never emitted by a mechanism walk)
        ``UNEVALUABLE``     ``OPEN``    when ``gate_check == "pass"`` — the path
                                        ran but magnitude or endpoint is unlocked
        ``UNEVALUABLE``     ``UNEVALUABLE`` when the gate state itself is unknown
        ``Busted``          ``REFUTED`` — the fifth constitution state
        ==================  ==================================================

        ``REFUTED`` is the constitution's fifth state: *mechanism walk completed
        and contradicted the claim*. The other four describe degrees of
        evaluability and none of them means "evaluated, and false." A closed
        micelle gate is a determinate negative result, not a missing field and not
        a category error, so it reports ``REFUTED`` rather than being forced into
        ``REFUSE`` — which would conflate "we declined to evaluate" with "we
        evaluated and the answer is no", the exact collapse the fail-closed design
        exists to prevent. ``REFUTED`` stays distinct from ``UNEVALUABLE`` (a
        required field is missing) for the same reason.
        """
        if self.verdict == "REFUSE":
            return "REFUSE"
        if self.verdict in {"Plausible", "Confirmed"}:
            return "HOLDS"
        if self.verdict == "Busted":
            return "REFUTED"
        # UNEVALUABLE splits on whether the gate itself resolved.
        return "OPEN" if self.gate_check == "pass" else "UNEVALUABLE"

    def to_dict(self) -> dict[str, Any]:
        """Schema-conformant dict. Empty optional blocks are omitted, not faked."""
        out: dict[str, Any] = {
            "id": self.id,
            "surface_claim": self.surface_claim,
            "verdict": self.verdict,
            "gate_check": self.gate_check,
            "kingdom": self.kingdom,
            "integrity": self.integrity,
        }
        if self.atomized:
            out["atomized"] = list(self.atomized)
        if self.gate_note:
            out["gate_note"] = self.gate_note
        if self.l1_to_l5:
            out["l1_to_l5"] = dict(self.l1_to_l5)
        if self.rosetta:
            out["rosetta"] = dict(self.rosetta)
        return out


def _relation_enum(
    claim: Claim,
    gate_check: GateCheck,
    findings: tuple[BoundFinding, ...],
) -> str:
    """Type the claim's relation using the subset enum vocabulary."""
    if claim.is_endpoint_claim or not claim.is_auditable:
        # A single meal path cannot carry a disease endpoint, and soft verbs
        # never had a mechanism to begin with.
        return "MALFORMED_MECHANISM"
    if gate_check == "fail":
        return "CLOSES_GATE"
    if gate_check == "unevaluable":
        return "NEEDS_RESOLUTION"
    if findings:
        return findings[0].direction
    return "NEEDS_RESOLUTION"


def audit_claim(claim: Claim, packet: FoodPacket | None = None) -> ClaimAudit:
    """Audit ``claim`` against ``packet``. Never raises on incomplete data."""

    # --- Step 1: is the claim auditable at all? ------------------------------
    if not claim.is_auditable:
        reason = (
            "soft / marketing verbs; no typed mechanism or endpoint"
            if claim.verb_class in UNAUDITABLE_VERB_CLASSES
            else "no nutrient named; nothing to trace through the ladder"
        )
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="REFUSE",
            gate_check="unevaluable",
            gate_note=reason,
            kingdom="mixed",
            atomized=claim.atomized,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": "MALFORMED_MECHANISM",
            },
            unevaluable_because=(reason,),
        )

    nutrient = str(claim.nutrient)

    if packet is None:
        reason = "no food packet supplied; claim cannot be traced against a meal"
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="UNEVALUABLE",
            gate_check="unevaluable",
            gate_note=reason,
            atomized=claim.atomized,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": "NEEDS_RESOLUTION",
            },
            unevaluable_because=(reason,),
        )

    ladder: dict[str, str] = {"L1": f"{packet.common_name} ({packet.identity.get('form', '?')})"}
    gates = gates_for(nutrient)
    kingdom = gates[0].kingdom if gates else "lumen"

    # --- Step 2 (L2): is the cargo declared in this packet? ------------------
    if nutrient not in packet.cargo_nutrients():
        reason = f"packet {packet.id} does not declare {nutrient} in cargo"
        ladder["L2"] = f"{nutrient} NOT declared in packet cargo"
        ladder["closed_through"] = "L2"
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="UNEVALUABLE",
            gate_check="unevaluable",
            gate_note=reason,
            kingdom=kingdom,
            atomized=claim.atomized,
            l1_to_l5=ladder,
            packet_id=packet.id,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": "NEEDS_RESOLUTION",
            },
            unevaluable_because=(reason,),
        )

    ladder["L2"] = f"{nutrient} present in matrix"

    # --- Step 3 (L3): the gate ----------------------------------------------
    gate_check: GateCheck = "pass"
    gate_note = ""
    law_refs: list[str] = []
    missing: list[str] = []

    for rule in gates:
        law_refs.extend(rule.law_refs)
        declared = [field for field in rule.fields if packet.declares(field)]
        if not declared:
            # Silence is not a zero. Fail closed.
            gate_check = "unevaluable"
            gate_note = rule.gate_note
            alternatives = " or ".join(repr(field) for field in rule.fields)
            missing.append(f"packet {packet.id} declares none of {alternatives}")
            continue
        # Any one declared alternative satisfying the rule opens the gate.
        if not any(rule.satisfied_by(field, packet.partner(field)) for field in declared):
            gate_check = "fail"
            gate_note = rule.gate_note
            break

    if not gates:
        gate_note = (
            f"no categorical gate declared for {nutrient}; "
            "this is a BOUND story, path remains possible"
        )

    if gate_check == "fail":
        ladder["L3"] = "micelle / transport path GATE CLOSED"
        ladder["L4"] = "not reached"
        ladder["L5"] = "not executable from this meal path"
        ladder["closed_through"] = "L3"
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="Busted",
            gate_check="fail",
            gate_note=gate_note,
            kingdom=kingdom,
            atomized=claim.atomized,
            l1_to_l5=ladder,
            law_refs=tuple(dict.fromkeys(law_refs)),
            packet_id=packet.id,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": _relation_enum(claim, "fail", ()),
            },
        )

    if gate_check == "unevaluable":
        ladder["L3"] = "gate state UNKNOWN — required co-factor not declared"
        ladder["closed_through"] = "L3"
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="UNEVALUABLE",
            gate_check="unevaluable",
            gate_note=gate_note,
            kingdom=kingdom,
            atomized=claim.atomized,
            l1_to_l5=ladder,
            law_refs=tuple(dict.fromkeys(law_refs)),
            packet_id=packet.id,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": "NEEDS_RESOLUTION",
            },
            unevaluable_because=tuple(missing),
        )

    ladder["L3"] = "transport path available"

    # --- Step 4 (L4): bounds ------------------------------------------------
    findings: list[BoundFinding] = []
    for rule in bounds_for(nutrient):
        value: Any
        if rule.source == "matrix":
            # Matrix rules key off the integrity string, not a partner field.
            value = packet.matrix_integrity == rule.triggered_by
            if packet.matrix_integrity == "unknown":
                continue
        else:
            if not packet.declares(rule.triggered_by):
                continue
            value = packet.partner(rule.triggered_by)
        if rule.satisfied_by(value):
            findings.append(
                BoundFinding(
                    direction=rule.direction,
                    note=rule.note,
                    triggered_by=rule.triggered_by,
                    law_refs=rule.law_refs,
                )
            )
            law_refs.extend(rule.law_refs)

    if not findings:
        reason = f"gate open but no bound modifier declared for {nutrient}; magnitude unknown"
        ladder["L4"] = "systemic delivery possible; magnitude undetermined"
        ladder["closed_through"] = "none"
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="UNEVALUABLE",
            gate_check="pass",
            gate_note=reason,
            kingdom=kingdom,
            atomized=claim.atomized,
            l1_to_l5=ladder,
            law_refs=tuple(dict.fromkeys(law_refs)),
            packet_id=packet.id,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": "NEEDS_RESOLUTION",
            },
            unevaluable_because=(reason,),
        )

    directions = ", ".join(sorted({f.direction for f in findings}))
    ladder["L4"] = f"systemic delivery possible; bound direction {directions}"

    # --- Step 5 (L5): the endpoint ------------------------------------------
    if claim.is_endpoint_claim:
        reason = (
            "disease endpoint is not executable from a single meal path; "
            "requires population evidence, not a mechanism walk"
        )
        ladder["L5"] = "endpoint not executable from this meal path"
        ladder["closed_through"] = "L5"
        return ClaimAudit(
            id=claim.id,
            surface_claim=claim.surface_claim,
            verdict="UNEVALUABLE",
            gate_check="pass",
            gate_note=reason,
            kingdom=kingdom,
            atomized=claim.atomized,
            l1_to_l5=ladder,
            bound_findings=tuple(findings),
            law_refs=tuple(dict.fromkeys(law_refs)),
            packet_id=packet.id,
            rosetta={
                "surface_verb": claim.surface_verb or claim.verb_class,
                "class": claim.verb_class,
                "relation_enum": "MALFORMED_MECHANISM",
            },
            unevaluable_because=(reason,),
        )

    ladder["L5"] = f"mechanism claim supported in direction: {directions}"
    ladder["closed_through"] = "none"

    return ClaimAudit(
        id=claim.id,
        surface_claim=claim.surface_claim,
        verdict="Plausible",
        gate_check="pass",
        gate_note=gate_note,
        kingdom=kingdom,
        atomized=claim.atomized,
        l1_to_l5=ladder,
        bound_findings=tuple(findings),
        law_refs=tuple(dict.fromkeys(law_refs)),
        packet_id=packet.id,
        rosetta={
            "surface_verb": claim.surface_verb or claim.verb_class,
            "class": claim.verb_class,
            "relation_enum": _relation_enum(claim, "pass", tuple(findings)),
        },
    )


def audit_packet_coverage(packets: list[FoodPacket], nutrient: str, verb_class: str = "gate") -> dict[str, int]:
    """Verdict histogram for one nutrient across many packets.

    Useful for reporting honest coverage: how many packets can actually decide a
    claim versus how many fall through to ``UNEVALUABLE``.
    """
    counts: dict[str, int] = {}
    for packet in packets:
        result = audit_claim(
            Claim(
                id=f"coverage.{nutrient}",
                surface_claim=f"{nutrient} claim",
                verb_class=verb_class,
                nutrient=nutrient,
            ),
            packet,
        )
        counts[result.verdict] = counts.get(result.verdict, 0) + 1
    return dict(sorted(counts.items()))
