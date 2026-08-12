#!/usr/bin/env python3
"""
Resolve every ``x-binding_site`` / ``binding_site`` against the engine.

A binding annotation is a promise that a host field actually reaches the
engine. This tool checks the promise. It walks the host-state schemas and the
genome seed registry, collects every declared binding site, and resolves each
one against the parameter space introspected from the live engine
(:mod:`biology_as_code.engine.parameters`). A path that does not resolve is a
dangling binding and exits non-zero.

Two things are deliberately *not* errors:

- ``x-binding_site: null``. Host state legitimately records fields no engine
  process reads. Null must be written explicitly, though — an omitted facet is
  reported as a defect, because that is indistinguishable from forgetting.
- A field whose binding resolves but whose evidence state is ``candidate``.
  That is a curation question, not a wiring question, and it is summarised
  rather than failed.

Usage::

    python tools/resolve_bindings.py            # check, exit 1 on dangling
    python tools/resolve_bindings.py --list     # print the parameter space
    python tools/resolve_bindings.py --json     # machine-readable report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biology_as_code.engine.parameters import parameter_space  # noqa: E402

SCHEMA_DIR = SRC / "biology_as_code" / "machines" / "data" / "schemas"

#: Documents scanned for binding annotations.
TARGETS = (
    SCHEMA_DIR / "HostState.v2.schema.json",
    REPO_ROOT / "design" / "genome_modifier_seed.json",
)

FACET_KEYS = ("x-binding_site", "x-clock", "x-tier", "x-evidence_state")
CLOCKS = {"fixed", "adaptation", "diurnal", "meal", "bite", "event"}
TIERS = {"T0", "T1", "T2", "T3", "T4"}
EVIDENCE = {"verified", "supported", "contested", "candidate"}


def _walk(node: Any, path: str = "") -> Iterator[tuple[str, dict]]:
    """Yield every dict in the document with its JSON pointer-ish path."""
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _walk(value, f"{path}/{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


def collect(doc: Any, source: str) -> tuple[list[dict], list[str]]:
    """
    Collect binding declarations and facet defects from one document.

    A declaration is any object carrying ``x-binding_site`` (schema field) or
    ``binding_site`` (a ModifierBinding row).
    """
    declarations: list[dict] = []
    defects: list[str] = []

    for where, obj in _walk(doc):
        # The schema's own facet-vocabulary block documents the facet names and
        # is not a declaration. Scanning it would read the documentation as a
        # binding and choke on its value being a description rather than a path.
        if where == "x-facets" or where.startswith("x-facets/"):
            continue
        if "x-binding_site" in obj:
            declarations.append(
                {
                    "source": source,
                    "where": where,
                    "site": obj["x-binding_site"],
                    "clock": obj.get("x-clock"),
                    "tier": obj.get("x-tier"),
                    "evidence_state": obj.get("x-evidence_state"),
                }
            )
            for key in FACET_KEYS:
                if key not in obj:
                    defects.append(f"{source}:{where}: missing mandatory facet {key}")
            clock, tier, ev = obj.get("x-clock"), obj.get("x-tier"), obj.get("x-evidence_state")
            if clock is not None and clock not in CLOCKS:
                defects.append(f"{source}:{where}: unknown x-clock {clock!r}")
            if tier is not None and tier not in TIERS:
                defects.append(f"{source}:{where}: unknown x-tier {tier!r}")
            if ev is not None and ev not in EVIDENCE:
                defects.append(f"{source}:{where}: unknown x-evidence_state {ev!r}")
        elif "binding_site" in obj and isinstance(obj.get("binding_site"), str):
            declarations.append(
                {
                    "source": source,
                    "where": where,
                    "site": obj["binding_site"],
                    "clock": obj.get("clock"),
                    "tier": obj.get("tier"),
                    "evidence_state": obj.get("evidence_state"),
                }
            )
            if obj.get("evidence_state") not in EVIDENCE:
                defects.append(
                    f"{source}:{where}: binding row has unknown evidence_state "
                    f"{obj.get('evidence_state')!r}"
                )

    return declarations, defects


def check(targets=TARGETS) -> dict[str, Any]:
    space = parameter_space()
    declarations: list[dict] = []
    defects: list[str] = []
    missing_targets: list[str] = []

    for path in targets:
        if not path.is_file():
            missing_targets.append(str(path.relative_to(REPO_ROOT)))
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        d, f = collect(doc, str(path.relative_to(REPO_ROOT)))
        declarations.extend(d)
        defects.extend(f)

    dangling = [
        d for d in declarations if isinstance(d["site"], str) and d["site"] not in space
    ]
    for d in dangling:
        near = space.nearest(d["site"])
        hint = f" Did you mean: {', '.join(near)}?" if near else ""
        defects.append(
            f"{d['source']}:{d['where']}: dangling binding {d['site']!r}"
            f" does not resolve to an engine parameter.{hint}"
        )
    for name in missing_targets:
        defects.append(f"target document not found: {name}")

    bound = [d for d in declarations if isinstance(d["site"], str)]
    unbound = [d for d in declarations if d["site"] is None]

    by_evidence: dict[str, int] = {}
    for d in declarations:
        key = str(d.get("evidence_state"))
        by_evidence[key] = by_evidence.get(key, 0) + 1

    return {
        "ok": not defects,
        "n_parameters": len(space),
        "n_declarations": len(declarations),
        "n_bound": len(bound),
        "n_unbound_declared_null": len(unbound),
        "n_dangling": len(dangling),
        "by_evidence_state": dict(sorted(by_evidence.items())),
        "sites_used": sorted({d["site"] for d in bound}),
        "defects": defects,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="print the engine parameter space")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    if args.list:
        space = parameter_space()
        for path in space.paths():
            print(f"{path}\t{space.origin(path)}")
        return 0

    report = check()

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    print(f"engine parameters:        {report['n_parameters']}")
    print(f"binding declarations:     {report['n_declarations']}")
    print(f"  bound to a parameter:   {report['n_bound']}")
    print(f"  declared unbound (null):{report['n_unbound_declared_null']}")
    print(f"  dangling:               {report['n_dangling']}")
    print(f"evidence states:          {report['by_evidence_state']}")

    if report["defects"]:
        print("\nFAIL")
        for defect in report["defects"]:
            print(f"  - {defect}")
        return 1

    print("\nOK: zero dangling bindings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
