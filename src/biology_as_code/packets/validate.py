"""
Zero-dependency validator for the JSON Schema subset used by this repo.

Deliberately *not* a general JSON Schema implementation. It supports exactly the
keywords that ``schemas/food_packet.schema.json`` and
``schemas/claim_audit.schema.json`` actually use::

    type, required, properties, enum, const, pattern, items,
    oneOf, additionalProperties, default

Anything else in a schema is ignored rather than silently treated as satisfied —
:func:`unsupported_keywords` reports what was skipped so a caller can refuse to
trust a pass. Adding ``jsonschema`` would break the package's zero-dependency
guarantee, so the honest move is a small validator with a declared blind spot.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SUPPORTED = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "type",
        "required",
        "properties",
        "enum",
        "const",
        "pattern",
        "items",
        "oneOf",
        "additionalProperties",
        "default",
    }
)

_TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a validation run. Falsy when invalid, so ``if not result:`` works."""

    valid: bool
    errors: tuple[str, ...] = ()
    skipped_keywords: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def raise_for_errors(self) -> None:
        if not self.valid:
            raise PacketValidationError("; ".join(self.errors))


class PacketValidationError(ValueError):
    """Raised when a packet fails schema validation and the caller wants an exception."""


@dataclass
class _Ctx:
    errors: list[str] = field(default_factory=list)
    skipped: set[str] = field(default_factory=set)


# Keywords whose *keys* are user-chosen names rather than schema vocabulary.
# Descending into them as if the names were keywords would report every property
# in the document as unsupported.
_NAME_MAPS = frozenset({"properties", "$defs", "definitions", "patternProperties"})


def unsupported_keywords(schema: dict[str, Any]) -> list[str]:
    """Keywords present in ``schema`` that this validator does not check."""
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in _NAME_MAPS:
                    # Skip the names; still inspect each subschema.
                    if isinstance(value, dict):
                        for sub in value.values():
                            walk(sub)
                    continue
                if key not in _SUPPORTED:
                    found.add(key)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    return sorted(found)


def _matches_type(value: Any, expected: str) -> bool:
    """Type test with JSON semantics.

    Python's ``bool`` is an ``int`` subclass, but JSON treats booleans and numbers
    as distinct, so ``True`` must not satisfy ``number`` or ``integer``.
    """
    py = _TYPES.get(expected)
    if py is None:
        return True
    if expected in {"number", "integer"} and isinstance(value, bool):
        return False
    return isinstance(value, py)


def _check_type(value: Any, expected: str, path: str, ctx: _Ctx) -> bool:
    if expected not in _TYPES:
        ctx.skipped.add(f"type:{expected}")
        return True
    if not _matches_type(value, expected):
        got = "boolean" if isinstance(value, bool) else type(value).__name__
        ctx.errors.append(f"{path}: expected {expected}, got {got}")
        return False
    return True


def _validate(value: Any, schema: dict[str, Any], path: str, ctx: _Ctx) -> None:
    for key in schema:
        if key not in _SUPPORTED:
            ctx.skipped.add(key)

    if "const" in schema and value != schema["const"]:
        ctx.errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        ctx.errors.append(f"{path}: {value!r} not in enum {schema['enum']!r}")

    if "type" in schema:
        declared = schema["type"]
        options = declared if isinstance(declared, list) else [declared]
        if not any(_matches_type(value, option) for option in options):
            _check_type(value, options[0], path, ctx)
            return

    if "pattern" in schema and isinstance(value, str):
        if re.search(schema["pattern"], value) is None:
            ctx.errors.append(f"{path}: {value!r} does not match /{schema['pattern']}/")

    if "oneOf" in schema:
        matches = 0
        for option in schema["oneOf"]:
            probe = _Ctx()
            _validate(value, option, path, probe)
            ctx.skipped |= probe.skipped
            if not probe.errors:
                matches += 1
        if matches != 1:
            ctx.errors.append(f"{path}: matched {matches} oneOf branches, expected exactly 1")

    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                ctx.errors.append(f"{path}: missing required property {name!r}")
        props = schema.get("properties", {})
        for name, sub in props.items():
            if name in value:
                _validate(value[name], sub, f"{path}.{name}" if path else name, ctx)
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in props:
                    ctx.errors.append(f"{path}: unexpected property {name!r}")

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate(item, schema["items"], f"{path}[{index}]", ctx)


def validate_against(instance: Any, schema: dict[str, Any]) -> ValidationResult:
    """Validate ``instance`` against a schema dict. Never raises on invalid input."""
    ctx = _Ctx()
    _validate(instance, schema, "", ctx)
    return ValidationResult(
        valid=not ctx.errors,
        errors=tuple(ctx.errors),
        skipped_keywords=tuple(sorted(ctx.skipped)),
    )


def load_schema(path: str | Path) -> dict[str, Any]:
    """Read a JSON Schema file from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
