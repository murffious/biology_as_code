"""
Compile the digestion machine registry to Amazon States Language (ASL).

This is the **concept made concrete**: the machines were authored Step-Functions-style
(``startAt`` / ``states``, ``task`` / ``choice`` / ``succeed``), so they compile
almost 1:1 to ASL. Nothing here calls AWS or deploys — it is a pure, offline,
zero-dependency compiler that emits deployable JSON and proves the mapping. The local
runtime stays :func:`biology_as_code.machines.trace`.

Correspondence:

===========================  ====================================
machine                      Amazon States Language
===========================  ====================================
``startAt`` / ``states``     ``StartAt`` / ``States``
``type: task``               ``Pass`` (or nested ``Task`` if it runs a stage)
``type: choice``             ``Choice`` (+ ``Default``)
``type: gate``               ``Choice`` with one branch (+ ``Default``)
``type: succeed``            ``Succeed``
predicate ``field/op/value`` ``{"Variable": "$.field", "NumericLessThan": v}``
``all`` / ``any`` / ``not``  ``And`` / ``Or`` / ``Not``
===========================  ====================================
"""

from __future__ import annotations

from typing import Any

_NUMERIC = {
    "<": "NumericLessThan",
    "<=": "NumericLessThanEquals",
    ">": "NumericGreaterThan",
    ">=": "NumericGreaterThanEquals",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _equals_test(var: str, value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"Variable": var, "BooleanEquals": value}
    if _is_number(value):
        return {"Variable": var, "NumericEquals": value}
    return {"Variable": var, "StringEquals": value}


def _leaf(pred: dict[str, Any]) -> dict[str, Any]:
    var = "$." + str(pred["field"])
    op = pred.get("op")
    value = pred.get("value")
    if op == "exists":
        return {"Variable": var, "IsPresent": True}
    if op == "==":
        return _equals_test(var, value)
    if op == "!=":
        return {"Not": _equals_test(var, value)}
    if op == "between":
        lo, hi = value
        return {"And": [
            {"Variable": var, "NumericGreaterThanEquals": lo},
            {"Variable": var, "NumericLessThanEquals": hi},
        ]}
    if op == "in":
        return {"Or": [_equals_test(var, v) for v in value]}
    key = _NUMERIC.get(str(op))
    if key is None:
        return {"Variable": var, "IsPresent": True}  # unknown op: degrade safely
    return {"Variable": var, key: value}


def predicate_to_asl(pred: dict[str, Any]) -> dict[str, Any]:
    """Compile a machine predicate into an ASL Choice data-test expression."""
    if "all" in pred:
        return {"And": [predicate_to_asl(p) for p in pred["all"]]}
    if "any" in pred:
        return {"Or": [predicate_to_asl(p) for p in pred["any"]]}
    if "not" in pred:
        return {"Not": predicate_to_asl(pred["not"])}
    return _leaf(pred)


def _state_to_asl(name: str, st: dict[str, Any]) -> dict[str, Any]:
    stype = st.get("type")
    comment = st.get("label", name)
    emits = st.get("emits") or []

    if stype == "succeed" or st.get("end"):
        return {"Type": "Succeed", "Comment": comment}

    if stype == "choice":
        choices = []
        for rule in st.get("choices", []) or []:
            branch = predicate_to_asl(rule["when"])
            branch["Next"] = rule["next"]
            if rule.get("note"):
                branch["Comment"] = rule["note"]
            choices.append(branch)
        out: dict[str, Any] = {"Type": "Choice", "Comment": comment, "Choices": choices}
        if st.get("default"):
            out["Default"] = st["default"]
        return out

    if stype == "gate":
        branch = predicate_to_asl(st["require"])
        branch["Next"] = st.get("next")
        out = {"Type": "Choice", "Comment": comment, "Choices": [branch]}
        on_fail = st.get("onFail") or {}
        if on_fail.get("next"):
            out["Default"] = on_fail["next"]
        return out

    # task: a stage-running task becomes a nested Step Functions execution; a plain
    # task becomes a Pass that records what it emitted.
    stage = next((e.split(":", 1)[1] for e in emits if isinstance(e, str) and e.startswith("stage:")), None)
    if stage:
        out = {
            "Type": "Task",
            "Comment": comment,
            "Resource": "arn:aws:states:::states:startExecution.sync:2",
            "Parameters": {"StateMachineArn.$": f"$.stateMachineArns.{stage.replace('.', '_')}", "Input.$": "$"},
        }
    else:
        out = {"Type": "Pass", "Comment": comment}
        if emits:
            out["Result"] = {"emits": list(emits)}
            out["ResultPath"] = f"$.trace.{name}"
    if st.get("next"):
        out["Next"] = st["next"]
    else:
        out["End"] = True
    edge_cases = st.get("edgeCases") or []
    if edge_cases:
        # ASL has no edge-case concept; annotate (a reroute would add a Choice — noted honestly).
        out["Comment"] = f"{comment} · edgeCases: " + ", ".join(e.get("id", "?") for e in edge_cases)
    return out


def machine_to_asl(machine: dict[str, Any]) -> dict[str, Any]:
    """Compile one machine dict into an ASL state machine dict."""
    return {
        "Comment": machine.get("title", machine.get("id", "machine")),
        "StartAt": machine["startAt"],
        "States": {name: _state_to_asl(name, st) for name, st in machine.get("states", {}).items()},
    }


def registry_to_asl() -> dict[str, dict[str, Any]]:
    """Compile every machine in the registry. Keyed by machine id.

    ``process.full-digest`` is the entry point; its stage tasks reference the other
    machines as nested executions (their ARNs are placeholders to be filled at deploy).
    """
    from biology_as_code.machines import get_machine, list_machines

    out: dict[str, dict[str, Any]] = {}
    for machine_id in list_machines():
        machine = get_machine(machine_id)
        if machine is not None:
            out[machine_id] = machine_to_asl(machine)
    return out


def food_to_input(food: Any, conditions: Any = None) -> dict[str, Any]:
    """Turn a standardized food (packet or id) + conditions into a nested execution input.

    The machine context is flat dotted keys (``meal.fatG``); ASL reads JSONPath
    (``$.meal.fatG``) over nested JSON, so this nests the same data.
    """
    from biology_as_code.digestion.engine import packet_to_context
    from biology_as_code.packets.loader import get_packet

    packet = get_packet(food) if isinstance(food, str) else food
    nested: dict[str, Any] = {}
    for dotted, value in packet_to_context(packet, conditions).items():
        node = nested
        parts = dotted.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return nested
