"""
Dependency-free validator for the open digestion machines.

Checks, per machine and across the registry:
  - envelope fields present; ``startAt`` resolves to a real state
  - every transition (next / choices / default / edgeCases.next / onFail.next)
    points at an existing state — no dangling edges
  - content ``hash`` in the registry matches the file (catches silent edits)
  - the open tier stays open: NO scoring ``penalties`` / product-score hooks

No jsonschema dependency — the JSON Schema in ``data/_schema`` is the published
contract; these hand-rolled checks are what CI runs so the package stays zero-dep.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from biology_as_code.machines.loader import get_machine, load_registry, machine_path

_ENVELOPE = ("kind", "id", "version", "revision", "title", "status", "startAt", "states")
# Anything score-shaped must never appear in an open machine.
_FORBIDDEN_KEYS = ("penalties", "penalty", "deduct", "score", "weight")
_FORBIDDEN_SUBSTR = ("biosolvency", "vendor_vars", "product_score", "score_axes")


def content_hash(machine: dict[str, Any]) -> str:
    """Stable content hash of a machine, ignoring the local ``$schema`` pointer."""
    payload = {k: v for k, v in machine.items() if k != "$schema"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()[:16]


def _transitions(state: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if isinstance(state.get("next"), str):
        out.append(state["next"])
    if isinstance(state.get("default"), str):
        out.append(state["default"])
    for c in state.get("choices", []) or []:
        if isinstance(c.get("next"), str):
            out.append(c["next"])
    for e in state.get("edgeCases", []) or []:
        if isinstance(e.get("next"), str):
            out.append(e["next"])
    on_fail = state.get("onFail")
    if isinstance(on_fail, dict) and isinstance(on_fail.get("next"), str):
        out.append(on_fail["next"])
    return out


def _find_forbidden(obj: Any) -> str | None:
    """Return the first score-shaped key/substring found anywhere, else None."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in _FORBIDDEN_KEYS:
                return k
            hit = _find_forbidden(v)
            if hit:
                return hit
    elif isinstance(obj, list):
        for item in obj:
            hit = _find_forbidden(item)
            if hit:
                return hit
    elif isinstance(obj, str):
        low = obj.lower()
        for s in _FORBIDDEN_SUBSTR:
            if s in low:
                return s
    return None


def validate_machine(machine: dict[str, Any]) -> list[str]:
    """Return a list of error strings for one machine ('' means valid)."""
    errors: list[str] = []
    for field in _ENVELOPE:
        if field not in machine:
            errors.append(f"missing envelope field: {field}")

    states = machine.get("states") or {}
    if not isinstance(states, dict) or not states:
        errors.append("states must be a non-empty object")
        return errors

    start = machine.get("startAt")
    if start not in states:
        errors.append(f"startAt '{start}' is not a defined state")

    keys = set(states)
    for name, state in states.items():
        if not isinstance(state, dict):
            errors.append(f"state '{name}' is not an object")
            continue
        for target in _transitions(state):
            if target not in keys:
                errors.append(f"state '{name}' -> dangling transition '{target}'")

    forbidden = _find_forbidden(machine)
    if forbidden:
        errors.append(f"open machine must not contain score hook: '{forbidden}'")

    return errors


def _process_stage_refs(machine: dict[str, Any]) -> list[str]:
    """Machine ids referenced by a process via ``emits: ["stage:<id>"]``."""
    refs: list[str] = []
    for state in (machine.get("states") or {}).values():
        for emit in (state.get("emits") or []):
            if isinstance(emit, str) and emit.startswith("stage:"):
                refs.append(emit.split(":", 1)[1])
    return refs


def _process_chain_order(machine: dict[str, Any]) -> list[str]:
    """Stage ids in the order the process actually walks its main line."""
    states = machine.get("states") or {}
    order: list[str] = []
    cur = machine.get("startAt")
    seen: set[str] = set()
    while cur and cur in states and cur not in seen:
        seen.add(cur)
        state = states[cur]
        for emit in state.get("emits") or []:
            if isinstance(emit, str) and emit.startswith("stage:"):
                order.append(emit.split(":", 1)[1])
        if state.get("type") == "succeed" or state.get("end"):
            break
        nxt = state.get("next") or state.get("default")
        if nxt is None and state.get("choices"):
            nxt = state["choices"][0].get("next")
        cur = nxt
    return order


def validate_all() -> dict[str, Any]:
    """Validate every registered machine + registry consistency.

    Returns ``{ok, n, errors}`` where ``errors`` is a list of ``"<id>: <msg>"``.
    """
    errors: list[str] = []
    rows = load_registry().get("machines", [])
    known_ids = {row.get("id") for row in rows}
    for row in rows:
        mid = row.get("id", "<no id>")
        path = machine_path(mid)
        if path is None or not path.is_file():
            errors.append(f"{mid}: file missing ({row.get('path')})")
            continue
        machine = get_machine(mid)
        for msg in validate_machine(machine):
            errors.append(f"{mid}: {msg}")
        if machine.get("id") != mid:
            errors.append(f"{mid}: file id '{machine.get('id')}' != registry id")
        want = row.get("hash")
        got = content_hash(machine)
        if want and want != got:
            errors.append(f"{mid}: hash drift (registry {want} != file {got})")
        # A process may only chain stages that actually exist in the registry.
        if machine.get("kind") == "process":
            for ref in _process_stage_refs(machine):
                if ref not in known_ids:
                    errors.append(f"{mid}: references unknown stage '{ref}'")

    # SSOT integrity: the three places that imply a stage order must agree —
    # registry row order, each stage's `order` field, and the process chain.
    stage_rows = [r for r in rows if r.get("kind") == "stage"]
    registry_stage_ids = [r.get("id") for r in stage_rows]
    order_fields = [(get_machine(r.get("id")) or {}).get("order") for r in stage_rows]
    if all(o is not None for o in order_fields) and order_fields != sorted(order_fields):
        errors.append(
            f"registry stage rows are not in ascending `order` field order: {order_fields}"
        )
    for row in rows:
        if row.get("kind") != "process":
            continue
        chain = _process_chain_order(get_machine(row.get("id")) or {})
        if chain and chain != registry_stage_ids:
            errors.append(
                f"{row.get('id')}: chain order {chain} != registry stage order {registry_stage_ids}"
            )

    return {"ok": not errors, "n": len(rows), "errors": errors}
