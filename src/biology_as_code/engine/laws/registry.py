"""Load law reformulation JSON and expose LawRegistry for tests / engines."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SEVEN = frozenset(
    {
        "Assimilation",
        "Transport",
        "Communication",
        "Defense",
        "Biotransformation",
        "Energy",
        "Structure",
    }
)

# Package data (copied from gleaned reformulations)
from biology_as_code.engine.laws.models import CONSERVING_RELATIONS
from biology_as_code.engine.paths import data_file

#: Curated standing in the literature. Mirrors ModifierBinding.evidence_state so
#: a law and a binding can be filtered by the same vocabulary.
EVIDENCE_STATES = ("verified", "supported", "contested", "candidate")

_DEFAULT_TC = data_file("textbook_to_code_laws.json")
_DEFAULT_SB = data_file("all_laws_system_bound.json")


@dataclass(frozen=True)
class LawRecord:
    id: str
    system_name: str
    organ: str
    subsystem: str
    law_statement: str
    status: str
    gate_text: str
    gate_present: bool
    bound_text: str
    conditions_text: str
    relation_type: str
    relation_expression: str
    score_role: str
    executable: bool
    related_to: str
    raw: dict[str, Any]
    #: ``verified`` | ``supported`` | ``contested`` | ``candidate``. A law's
    #: standing in the literature, curated by a human. Distinct from ``status``,
    #: which describes the law's *form* (framework, effect composite, and so on)
    #: rather than how well established it is. Defaults to ``candidate`` so an
    #: unannotated law reads as unreviewed rather than as accepted.
    evidence_state: str = "candidate"
    #: ISO date by which this law should be re-read against the literature, or
    #: empty when none has been set. A law with no review date is not wrong; it
    #: is unscheduled, and the QA pass reports it as such.
    review_by: str = ""

    @property
    def address(self) -> str:
        return f"{self.system_name}.{self.subsystem}"

    @property
    def is_conserving(self) -> bool:
        """Whether this law asserts a conserved quantity (see ``CONSERVES``)."""
        return self.relation_type in CONSERVING_RELATIONS

    @property
    def review_scheduled(self) -> bool:
        return bool(self.review_by.strip())


class LawRegistry:
    def __init__(self, laws: list[LawRecord], meta: dict[str, Any] | None = None):
        self._by_id = {L.id: L for L in laws}
        self.meta = meta or {}
        if len(self._by_id) != len(laws):
            raise ValueError("duplicate law ids")

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, law_id: str) -> bool:
        return law_id in self._by_id

    def get(self, law_id: str) -> LawRecord:
        return self._by_id[law_id]

    def all(self) -> list[LawRecord]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def by_system(self, system: str) -> list[LawRecord]:
        return [L for L in self.all() if L.system_name == system]

    def executable(self) -> list[LawRecord]:
        return [L for L in self.all() if L.executable]

    def conserving(self) -> list[LawRecord]:
        """Laws asserting a conserved quantity (relation type ``CONSERVES``)."""
        return [L for L in self.all() if L.relation_type in CONSERVING_RELATIONS]

    def by_evidence(self, *states: str) -> list[LawRecord]:
        wanted = set(states)
        return [L for L in self.all() if L.evidence_state in wanted]

    def due_for_review(self, on_date: str) -> list[LawRecord]:
        """Laws whose ``review_by`` date is on or before ``on_date`` (ISO).

        Laws with no review date are not returned: they are unscheduled, which
        the QA pass reports separately. Silently folding them in here would
        make "due" and "never scheduled" indistinguishable.
        """
        return [L for L in self.all() if L.review_scheduled and L.review_by <= on_date]

    def iter_ids(self) -> Iterator[str]:
        yield from sorted(self._by_id)

    def qa(self) -> dict[str, Any]:
        """Structural QA — returns errors/warns (empty errors ⇒ pass)."""
        errors: list[str] = []
        warns: list[str] = []
        expect = [f"LAW-{i:03d}" for i in range(1, 48)]
        for e in expect:
            if e not in self._by_id:
                errors.append(f"missing {e}")
        for L in self.all():
            if L.system_name not in SEVEN:
                errors.append(f"{L.id} bad system {L.system_name}")
            if not L.subsystem:
                errors.append(f"{L.id} empty subsystem")
            if not L.law_statement:
                errors.append(f"{L.id} empty law_statement")
            if not L.bound_text:
                errors.append(f"{L.id} empty bound")
            if not L.conditions_text:
                errors.append(f"{L.id} empty conditions")
            if L.relation_type == "OPENS_GATE" and not L.gate_present:
                warns.append(f"{L.id} OPENS_GATE but gate_present false")
            if L.executable and L.status in ("FRAMEWORK", "EFFECT_COMPOSITE"):
                warns.append(f"{L.id} executable with status {L.status}")
            if L.evidence_state not in EVIDENCE_STATES:
                errors.append(f"{L.id} bad evidence_state {L.evidence_state}")
            if not L.review_scheduled:
                warns.append(f"{L.id} has no review_by date")
        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warns": warns,
            "n": len(self),
            "executable_n": len(self.executable()),
            "conserving_n": len(self.conserving()),
            "unscheduled_review_n": sum(1 for L in self.all() if not L.review_scheduled),
        }


def _from_tc_law(raw: dict[str, Any]) -> LawRecord:
    gate = raw.get("gate") or {}
    bound = raw.get("bound") or {}
    cond = raw.get("conditions") or {}
    tr = raw.get("typed_relation") or {}
    ch = raw.get("code_hooks") or {}
    return LawRecord(
        id=raw["id"],
        system_name=raw["system_name"],
        organ=raw.get("organ") or "",
        subsystem=raw.get("subsystem") or "",
        law_statement=raw.get("law_statement") or raw.get("name") or "",
        status=raw.get("status") or "",
        gate_text=gate.get("text") or "",
        gate_present=bool(gate.get("present")),
        bound_text=bound.get("text") or "",
        conditions_text=cond.get("text") or "",
        relation_type=tr.get("primary_type") or "",
        relation_expression=tr.get("expression") or "",
        score_role=ch.get("score_role") or "",
        executable=bool(ch.get("executable")),
        related_to=raw.get("related_to") or "",
        raw=raw,
        evidence_state=_evidence_state(raw),
        review_by=str(raw.get("review_by") or ""),
    )


def _evidence_state(raw: dict[str, Any]) -> str:
    """Read a law's evidence state, defaulting to ``candidate``.

    An unannotated law is unreviewed, not accepted. Defaulting the other way
    would make the whole registry read as verified the moment the field was
    introduced, which is the opposite of what adding it is for.
    """
    value = str(raw.get("evidence_state") or "").strip().lower()
    return value if value in EVIDENCE_STATES else "candidate"


def load_registry(path: Path | str | None = None) -> LawRegistry:
    p = Path(path) if path else _DEFAULT_TC
    data = json.loads(p.read_text(encoding="utf-8"))
    laws = [_from_tc_law(x) for x in data.get("laws") or []]
    return LawRegistry(laws, meta=data.get("metadata") or {})


def load_default_registry() -> LawRegistry:
    return load_registry(_DEFAULT_TC)


def load_system_bound(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    p = Path(path) if path else _DEFAULT_SB
    data = json.loads(p.read_text(encoding="utf-8"))
    return {L["id"]: L for L in data.get("laws") or []}


def _from_sb_law(raw: dict[str, Any]) -> LawRecord:
    """System-bound reformulation row → LawRecord."""
    gate_raw = (raw.get("gate") or "none").strip()
    gate_present = not gate_raw.lower().startswith("none")
    rel = raw.get("relation") or ""
    # An explicit relation_type on the row wins over sniffing the relation
    # expression. Sniffing picks the first type it sees in a compound
    # expression, which is right often enough to be useful and wrong exactly
    # where a law's primary relation is not its first clause.
    explicit = str(raw.get("relation_type") or "").strip().upper()
    rel_type = "MIXED"
    if explicit:
        rel_type = explicit
    else:
        for t in (
            "OPENS_GATE",
            "CLOSES_GATE",
            "EXPANDS_BOUND",
            "NARROWS_BOUND",
            "CONSERVES",
            "IDENTITY",
            "FRAMEWORK",
        ):
            if t in rel.upper():
                rel_type = t
                break
    return LawRecord(
        id=raw["id"],
        system_name=raw.get("system") or "",
        organ=raw.get("organ") or "",
        subsystem=raw.get("subsystem") or "",
        law_statement=raw.get("law") or "",
        status=raw.get("status") or "",
        gate_text=gate_raw,
        gate_present=gate_present,
        bound_text=raw.get("bound") or "",
        conditions_text=raw.get("conditions") or "",
        relation_type=rel_type,
        relation_expression=rel,
        score_role="",
        executable=False,
        related_to=raw.get("related") or "",
        raw=raw,
        evidence_state=_evidence_state(raw),
        review_by=str(raw.get("review_by") or ""),
    )


def load_system_bound_registry(path: Path | str | None = None) -> LawRegistry:
    """Preferred registry for Part 1 / 7-system binding."""
    p = Path(path) if path else _DEFAULT_SB
    data = json.loads(p.read_text(encoding="utf-8"))
    laws = [_from_sb_law(x) for x in data.get("laws") or []]
    return LawRegistry(laws, meta={"source": str(p), "schema": data.get("schema_version")})
