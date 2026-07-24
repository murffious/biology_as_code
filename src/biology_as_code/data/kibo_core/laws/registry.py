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
from biology_as_code.data.kibo_core.paths import data_file

_DEFAULT_TC = data_file("textbook_to_code_laws.json")
_DEFAULT_SB = data_file("all_laws_system_bound.json")


@dataclass(frozen=True)
class LawRecord:
    id: str
    kibo_system: str
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

    @property
    def address(self) -> str:
        return f"{self.kibo_system}.{self.subsystem}"


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
        return [L for L in self.all() if L.kibo_system == system]

    def executable(self) -> list[LawRecord]:
        return [L for L in self.all() if L.executable]

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
            if L.kibo_system not in SEVEN:
                errors.append(f"{L.id} bad system {L.kibo_system}")
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
        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warns": warns,
            "n": len(self),
            "executable_n": len(self.executable()),
        }


def _from_tc_law(raw: dict[str, Any]) -> LawRecord:
    gate = raw.get("gate") or {}
    bound = raw.get("bound") or {}
    cond = raw.get("conditions") or {}
    tr = raw.get("typed_relation") or {}
    ch = raw.get("code_hooks") or {}
    return LawRecord(
        id=raw["id"],
        kibo_system=raw["kibo_system"],
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
    )


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
    rel_type = "MIXED"
    for t in (
        "OPENS_GATE",
        "CLOSES_GATE",
        "EXPANDS_BOUND",
        "NARROWS_BOUND",
        "FRAMEWORK",
    ):
        if t in rel.upper():
            rel_type = t
            break
    return LawRecord(
        id=raw["id"],
        kibo_system=raw.get("system") or "",
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
    )


def load_system_bound_registry(path: Path | str | None = None) -> LawRegistry:
    """Preferred registry for Part 1 / 7-system binding."""
    p = Path(path) if path else _DEFAULT_SB
    data = json.loads(p.read_text(encoding="utf-8"))
    laws = [_from_sb_law(x) for x in data.get("laws") or []]
    return LawRegistry(laws, meta={"source": str(p), "schema": data.get("schema_version")})
