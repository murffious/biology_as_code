"""
Public LAW-SPEC "law cards" — inspect the constitution as data.

Each law is a card in the LAW-SPEC shape: **System · Organ · Gate · Bound ·
Conditions · typed relation**. The underlying register (47 system-bound laws)
ships under ``engine``; this module is the small, stable public surface
over it — the same "biology as code" move the digestion machines made, applied
to the laws themselves.

    from biology_as_code import list_laws, get_law, law_card

    list_laws()[:3]              # ['LAW-001', 'LAW-002', 'LAW-003']
    law_card("LAW-004")          # {'id', 'system', 'gate': {...}, 'bound', ...}
    law_card(4)["gate"]          # ints and 'law-004' also resolve

Honesty note: `gate.present` distinguishes a categorical gate from a
magnitude-only bound. Missing magnitude stays open — no fabricated numbers.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from biology_as_code.engine.laws.registry import (
    LawRecord,
    load_system_bound_registry,
)


@lru_cache(maxsize=1)
def _registry():
    return load_system_bound_registry()


def _norm(law_id: str | int) -> str:
    """Normalize 4 / '4' / 'law-004' / 'LAW-004' -> 'LAW-004'."""
    key = str(law_id).strip().upper()
    if key.isdigit():
        return f"LAW-{int(key):03d}"
    if key.startswith("LAW-") and key[4:].isdigit():
        return f"LAW-{int(key[4:]):03d}"
    return key


def list_laws() -> list[str]:
    """All law ids in order (e.g. LAW-001 … LAW-047)."""
    return list(_registry().iter_ids())


def list_systems() -> list[str]:
    """The seven functional systems present in the register."""
    return sorted({law.system_name for law in _registry().all()})


def get_law(law_id: str | int) -> LawRecord | None:
    """Fetch one LawRecord by id (accepts 4 / '4' / 'law-004'); None if unknown."""
    reg = _registry()
    key = _norm(law_id)
    return reg.get(key) if key in reg else None


def laws_by_system(system: str) -> list[LawRecord]:
    """All laws seated in a given functional system (case-insensitive)."""
    target = system.strip().lower()
    return [law for law in _registry().all() if law.system_name.lower() == target]


def law_card(law_id: str | int) -> dict[str, Any] | None:
    """A law as a LAW-SPEC card dict, or None if unknown."""
    law = get_law(law_id)
    if law is None:
        return None
    return {
        "id": law.id,
        "system": law.system_name,
        "organ": law.organ,
        "subsystem": law.subsystem,
        "statement": law.law_statement,
        "gate": {"present": law.gate_present, "text": law.gate_text},
        "bound": law.bound_text,
        "conditions": law.conditions_text,
        "relation": {"type": law.relation_type, "expression": law.relation_expression},
        "executable": law.executable,
        "related_to": law.related_to,
        "status": law.status,
    }


__all__ = [
    "get_law",
    "law_card",
    "laws_by_system",
    "list_laws",
    "list_systems",
]
