"""
Walk a declarative digestion machine with a context and record the path taken.

``trace(machine, context)`` evaluates the machine's inspectable predicates
against a flat context dict (dotted keys, e.g. ``{"meal.proteinG": 40}``) and
returns which states fired, which branch each ``choice`` took, which edge cases
tripped, and everything the run emitted. Pure and dependency-free — predicates
are data, never executable code, so this is a safe interpreter, not ``eval``.
"""

from __future__ import annotations

from typing import Any

from biology_as_code.machines.loader import get_machine

_MAX_STEPS = 200


def _cmp(a: Any, op: str, b: Any) -> bool:
    try:
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        if op == "in":
            return a in b
        if op == "between":
            lo, hi = b
            return lo <= a <= hi
    except (TypeError, ValueError):
        return False
    return False


def match(predicate: dict[str, Any] | None, context: dict[str, Any]) -> bool:
    """Evaluate one declarative predicate against the context (missing field -> False)."""
    if not predicate:
        return True
    if "all" in predicate:
        return all(match(p, context) for p in predicate["all"])
    if "any" in predicate:
        return any(match(p, context) for p in predicate["any"])
    if "not" in predicate:
        return not match(predicate["not"], context)

    field = predicate.get("field")
    if field is None:
        return False
    op = predicate.get("op")
    present = field in context and context.get(field) is not None
    if op == "exists":
        return present
    if not present:
        return False
    return _cmp(context.get(field), op, predicate.get("value"))


def _fired_edge_cases(state: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for ec in state.get("edgeCases", []) or []:
        if match(ec.get("when"), context):
            out.append(ec)
    return out


def _next_state(state: dict[str, Any], context: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (next_state_key, note) for a state given the context."""
    stype = state.get("type")
    if stype == "succeed" or state.get("end"):
        return None, None
    if stype == "choice":
        for rule in state.get("choices", []) or []:
            if match(rule.get("when"), context):
                return rule.get("next"), rule.get("note")
        return state.get("default"), "default"
    if stype == "gate":
        if match(state.get("require"), context):
            return state.get("next"), "gate open"
        on_fail = state.get("onFail") or {}
        return on_fail.get("next"), "gate failed"
    # task
    return state.get("next"), None


def trace(machine: str | dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run ``context`` through ``machine`` (id or dict); return the path taken.

    Returns ``{machine, status, path, visited, emits, firedEdgeCases, final}``.
    ``status`` is 'ok' (reached a terminal state), 'incomplete' (dead-ended on a
    non-terminal state — e.g. a choice with no matching rule and no default),
    'truncated' (step cap / cycle), or 'error' (missing/unknown machine or state).
    """
    context = dict(context or {})
    m = get_machine(machine) if isinstance(machine, str) else machine
    if not m:
        return {"machine": machine, "status": "error", "path": [], "visited": [],
                "emits": [], "firedEdgeCases": [], "final": None,
                "error": f"machine not found: {machine!r}"}

    states = m.get("states") or {}
    cur = m.get("startAt")
    path: list[dict[str, Any]] = []
    visited: list[str] = []
    emits: list[str] = []
    fired: list[dict[str, Any]] = []
    status = "ok"

    seen: set[str] = set()
    for _ in range(_MAX_STEPS):
        state = states.get(cur)
        if state is None:
            status = "error"
            path.append({"state": cur, "error": "dangling transition"})
            break
        if cur in seen:
            status = "truncated"  # cycle guard
            break
        seen.add(cur)
        visited.append(cur)

        ecs = _fired_edge_cases(state, context)
        state_emits = list(state.get("emits") or [])
        emits.extend(state_emits)
        for ec in ecs:
            fired.append({"state": cur, "id": ec.get("id"),
                          "effect": ec.get("effect"), "note": ec.get("note")})

        is_terminal = state.get("type") == "succeed" or bool(state.get("end"))
        nxt, note = _next_state(state, context)
        # A fired edge case may re-route — but never out of a terminal state.
        if not is_terminal:
            for ec in ecs:
                if ec.get("next"):
                    nxt, note = ec["next"], f"edgeCase:{ec.get('id')}"
                    break

        path.append({
            "state": cur,
            "type": state.get("type"),
            "label": state.get("label"),
            "next": None if is_terminal else nxt,
            "note": None if is_terminal else note,
            "edgeCases": [ec.get("id") for ec in ecs],
            "emits": state_emits,
        })
        if is_terminal:
            break
        if nxt is None:
            # non-terminal dead end: no matching branch / no `next` — the graph
            # did not actually reach a terminal state.
            status = "incomplete"
            break
        cur = nxt
    else:
        status = "truncated"

    return {
        "machine": m.get("id"),
        "status": status,
        "path": path,
        "visited": visited,
        "emits": emits,
        "firedEdgeCases": fired,
        "final": visited[-1] if visited else None,
    }
