#!/usr/bin/env python3
"""Check that ontology.json and relation-crosswalk.v1.json agree with themselves
and with what they copy.

  python3 check_manifest.py            report
  python3 check_manifest.py --strict   exit 1 on any FAIL

The manifest is a hand-written file that quotes other files: the spine stages
migrate_spine_naming.py declares, the relation vocabulary mechanism_schema.py
executes, the fields FDP-1 enforces. The crosswalk beside it quotes six more
vocabularies. A quoted value nobody re-checks drifts — the first version of the
manifest invented a spine stage (`spine:catalogue`), had Value implement two
interfaces whose required properties it did not carry, and named a Citable
property (`evidence_span`) that exists nowhere in the SDK.

Internal checks always run. Cross-repo checks run only when the sibling
checkout is beside this repo (or NC_ROOT / BOOK_ROOT point at one) and its
imports resolve; otherwise they report themselves as skipped, never as passed.
"""
from __future__ import annotations

import json
import os
import sys
import typing
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / "ontology.json"
CROSSWALK = HERE / "relation-crosswalk.v1.json"
CROSSWALK_REL = "ontology-sdk/relation-crosswalk.v1.json"

OK, FAIL, SKIP = "OK", "FAIL", "skip"
HEADER = "ontology"
SCALARS = {"any", "Any", "string", "boolean", "object", "T"}
RELATIONS = {"exact", "narrower", "broader", "related", "none"}


def _sibling(env: str, *patterns: str, probe: str) -> Path | None:
    p = os.getenv(env)
    if p and (Path(p) / probe).exists():
        return Path(p)
    for pat in patterns:
        for cand in sorted(ROOT.parent.glob(pat)):
            if (cand / probe).exists():
                return cand
    return None


def _sibling_nc() -> Path | None:
    return _sibling("NC_ROOT", "nutri-collective", "*nutri-collective*",
                    probe="evidence-platform/src/mechanism_schema.py")


def _sibling_book() -> Path | None:
    return _sibling("BOOK_ROOT", "book", "*book*", probe="claim-language/claim_verbs.json")


def _props(spec: dict) -> set[str]:
    props = spec.get("properties", [])
    return set(props.keys() if isinstance(props, dict) else props)


def _xw() -> dict:
    return json.loads(CROSSWALK.read_text(encoding="utf-8"))


# ----------------------------------------------------------------- manifest

def check_header(m):
    head = m.get(HEADER) or {}
    missing = [k for k in ("name", "version", "as_of", "status", "description") if not head.get(k)]
    return [f"header lacks {missing}"] if missing else []


def check_blocks_are_dicts(m):
    return [f"block {k!r} is not a dict of named entries"
            for k, v in m.items() if k != HEADER and not isinstance(v, dict)]


def check_spine_stages(m):
    stages = set(m.get("spine_stages", {}))
    out = []
    for name, spec in m.get("object_types", {}).items():
        st = spec.get("spine_stage", "MISSING")
        if st == "MISSING":
            out.append(f"object_types.{name} has no spine_stage key (use null when off the spine)")
        elif st is not None and st not in stages:
            out.append(f"object_types.{name}.spine_stage {st!r} is not a declared stage")
        if st is None and not spec.get("note") and not spec.get("spine_span"):
            out.append(f"object_types.{name} is off the spine but does not say why (note)")
        for s in spec.get("spine_span", []):
            if s not in stages:
                out.append(f"object_types.{name}.spine_span {s!r} is not a declared stage")
    return out


def check_interfaces_are_satisfied(m):
    ifaces = m.get("interfaces", {})
    out = []
    for block in ("object_types", "types"):
        for name, spec in m.get(block, {}).items():
            have = _props(spec)
            for iface in spec.get("implements", []):
                if iface not in ifaces:
                    out.append(f"{block}.{name} implements unknown interface {iface!r}")
                    continue
                aliases = ifaces[iface].get("aliases", {})
                for req in ifaces[iface].get("required_properties", []):
                    if req in have or any(a in have for a in aliases.get(req, [])):
                        continue
                    out.append(f"{block}.{name} implements {iface} but lacks {req!r}")
    return out


def check_every_interface_has_an_implementer(m):
    used = set()
    for block in ("object_types", "types"):
        for spec in m.get(block, {}).values():
            used.update(spec.get("implements", []))
    return [f"interface {i!r} has no implementer" for i in m.get("interfaces", {}) if i not in used]


def check_predicates_are_typed_over_declared_kinds(m):
    kinds = set(m.get("entity_kinds", {})) | {"any"}
    out = []
    for name, spec in m.get("predicates", {}).items():
        for side in ("domain", "range"):
            bad = [k for k in spec.get(side, []) if k not in kinds]
            if bad:
                out.append(f"predicates.{name}.{side} names undeclared kinds {bad}")
            if not spec.get(side):
                out.append(f"predicates.{name}.{side} is empty")
    return out


def check_entity_kinds_point_at_object_types(m):
    types = set(m.get("object_types", {}))
    return [f"entity_kinds.{k}.object_type {v.get('object_type')!r} is not an object type"
            for k, v in m.get("entity_kinds", {}).items()
            if v.get("object_type") is not None and v.get("object_type") not in types]


def check_actions_are_honest(m):
    names = set(m.get("object_types", {})) | set(m.get("types", {})) | SCALARS
    out = []
    for name, spec in m.get("actions", {}).items():
        if "implemented" not in spec:
            out.append(f"actions.{name} does not say whether it is implemented")
        for arg, typ in spec.get("inputs", {}).items():
            if typ not in names:
                out.append(f"actions.{name}.inputs.{arg} type {typ!r} is undeclared")
        ret = spec.get("returns", "")
        inner = ret[len("ActionResponse<"):-1] if ret.startswith("ActionResponse<") and ret.endswith(">") else None
        if inner is None or inner not in names:
            out.append(f"actions.{name}.returns {ret!r} is not ActionResponse<declared type>")
    return out


def check_predicates_match_mechanism_schema(m):
    """Cross-repo: the copy must equal the executed matrix, name for name."""
    nc = _sibling_nc()
    if nc is None:
        return SKIP, ["no nutri-collective checkout beside this repo (set NC_ROOT)"]
    src = nc / "evidence-platform" / "src"
    sys.path.insert(0, str(src))
    try:
        import mechanism_schema as ms  # noqa: WPS433
    except Exception as e:  # pydantic or a sibling module missing
        return SKIP, [f"could not import mechanism_schema ({type(e).__name__}: {e})"]
    finally:
        sys.path.pop(0)
    out = []
    theirs = {r.value for r in ms.Relation}
    mine = set(m.get("predicates", {}))
    if theirs != mine:
        out.append(f"predicate names differ: only here {sorted(mine - theirs)}, only in mechanism_schema {sorted(theirs - mine)}")
    kinds = {k.value for k in ms.EntityKind}
    if kinds != set(m.get("entity_kinds", {})):
        out.append(f"entity kinds differ: manifest {sorted(m.get('entity_kinds', {}))} vs {sorted(kinds)}")
    for rel, (dom, rng) in ms.COMPAT.items():
        spec = m.get("predicates", {}).get(rel.value)
        if spec is None:
            continue
        want_d = {"any"} if dom == set(ms.EntityKind) else {k.value for k in dom}
        want_r = {"any"} if rng == set(ms.EntityKind) else {k.value for k in rng}
        if set(spec.get("domain", [])) != want_d:
            out.append(f"predicates.{rel.value}.domain {sorted(spec.get('domain', []))} != {sorted(want_d)}")
        if set(spec.get("range", [])) != want_r:
            out.append(f"predicates.{rel.value}.range {sorted(spec.get('range', []))} != {sorted(want_r)}")
    return out


# ---------------------------------------------------------------- crosswalk

def check_manifest_points_at_the_crosswalk(m):
    out = []
    if (m.get(HEADER) or {}).get("crosswalk") != CROSSWALK_REL:
        out.append(f"ontology.crosswalk must be {CROSSWALK_REL!r}")
    if not CROSSWALK.is_file():
        return out + [f"{CROSSWALK_REL} is missing"]
    xw = _xw()
    if set(xw.get("base", {}).get("relations", [])) != set(m.get("predicates", {})):
        out.append("crosswalk base.relations != manifest predicates")
    return out


def check_crosswalk_rows_are_well_formed(m):
    xw = _xw()
    preds = set(m.get("predicates", {}))
    vocabs = set(xw.get("vocabularies", {}))
    out, seen = [], set()
    for r in xw.get("rows", []):
        key = (r.get("vocabulary"), r.get("verb"))
        tag = f"{key[0]}.{key[1]}"
        if key in seen:
            out.append(f"{tag}: duplicate row")
        seen.add(key)
        if key[0] not in vocabs:
            out.append(f"{tag}: vocabulary is not declared")
        rel = r.get("relation")
        if rel not in RELATIONS:
            out.append(f"{tag}: relation {rel!r} is not one of {sorted(RELATIONS)}")
        elif rel == "none":
            if r.get("base") is not None:
                out.append(f"{tag}: a none row carries a base")
            if not r.get("expansion") and not r.get("reason"):
                out.append(f"{tag}: a none row needs an expansion or a reason")
        else:
            if r.get("base") not in preds:
                out.append(f"{tag}: base {r.get('base')!r} is not a manifest predicate")
            if r.get("expansion") or r.get("reason"):
                out.append(f"{tag}: a direct row must not carry an expansion or reason")
    return out


def check_crosswalk_covers_every_member(m):
    xw = _xw()
    out = []
    for v, spec in xw.get("vocabularies", {}).items():
        members = set(spec.get("members", []))
        rows = {r["verb"] for r in xw.get("rows", []) if r.get("vocabulary") == v}
        if members != rows:
            out.append(f"{v}: members without a row {sorted(members - rows)}, rows without a member {sorted(rows - members)}")
    return out


def check_shared_verb_names_map_identically(m):
    """The same name in two vocabularies is a promise; two mappings would be a blocker-5 collision."""
    by: dict[str, list] = {}
    for r in _xw().get("rows", []):
        by.setdefault(r["verb"], []).append(r)
    out = []
    for verb, rs in by.items():
        sigs = {(r["relation"], r.get("base"), bool(r.get("inverse"))) for r in rs}
        if len(sigs) > 1:
            out.append(f"{verb} maps differently across vocabularies: {sorted(map(str, sigs))}")
    return out


def _tally(rows):
    c: dict[str, int] = {}
    for r in rows:
        k = r["relation"] if r["relation"] != "none" else ("none_with_expansion" if r.get("expansion") else "none")
        c[k] = c.get(k, 0) + 1
    c["rows"] = len(rows)
    return dict(sorted(c.items()))


def check_crosswalk_counts_are_derived(m):
    xw = _xw()
    rows = xw.get("rows", [])
    want = {"total": _tally(rows),
            "by_vocabulary": {v: _tally([r for r in rows if r["vocabulary"] == v]) for v in xw.get("vocabularies", {})}}
    return [] if xw.get("counts") == want else [f"counts block is stale; recomputed: {json.dumps(want)}"]


def _walk_relations(o, acc):
    if isinstance(o, dict):
        if isinstance(o.get("relation"), str):
            acc.add(o["relation"])
        for v in o.values():
            _walk_relations(v, acc)
    elif isinstance(o, list):
        for v in o:
            _walk_relations(v, acc)


def check_crosswalk_members_match_live_sources(m):
    """Each vocabulary's member list must equal what its source file holds today."""
    xw = _xw()
    vocabs = xw.get("vocabularies", {})
    live: dict[str, set | None] = {}
    # law-model and graph live in this repo
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from biology_as_code.engine.laws.models import RelationType  # noqa: WPS433
        live["law-model"] = set(typing.get_args(RelationType))
    except Exception as e:
        live["law-model"] = None
        law_err = f"{type(e).__name__}: {e}"
    finally:
        sys.path.pop(0)
    live["graph"] = set(json.loads((ROOT / "schemas" / "relation_enums.subset.json").read_text())["RelationType"])
    book, nc = _sibling_book(), _sibling_nc()
    drift = None
    if book:
        live["claim-language"] = set(json.loads((book / "claim-language" / "claim_verbs.json").read_text())["relation_enums"])
        ne = json.loads((book / "nutrient-taxonomy" / "v2" / "nutrient-edge.v2.json").read_text())
        live["nutrient-edge"] = set(ne["properties"]["predicate"]["enum"])
        per_file = {}
        for f in sorted((book / "taxonomies" / "joins").glob("*.json")):
            acc: set = set()
            _walk_relations(json.loads(f.read_text()), acc)
            per_file[f.stem] = acc
        live["taxonomy-joins"] = set().union(*per_file.values()) if per_file else set()
        names = sorted(per_file)
        if len(names) == 2:
            a, b = names
            drift = {f"only_in_{a}": sorted(per_file[a] - per_file[b]), f"only_in_{b}": sorted(per_file[b] - per_file[a])}
    else:
        live["claim-language"] = live["nutrient-edge"] = live["taxonomy-joins"] = None
    if nc:
        edges = json.loads((nc / "evidence-platform" / "site" / "id-crosswalk.v1.json").read_text())["edges"]
        live["id-crosswalk"] = {e.get("kind") for e in edges}
    else:
        live["id-crosswalk"] = None

    out, skipped = [], []
    for v, spec in vocabs.items():
        got = live.get(v)
        if got is None:
            skipped.append(v)
            continue
        want = set(spec.get("members", []))
        if got != want:
            out.append(f"{v}: source holds {sorted(got - want)} not in members; members hold {sorted(want - got)} not in source")
    if drift is not None and vocabs.get("taxonomy-joins", {}).get("drift") != drift:
        out.append(f"taxonomy-joins.drift is stale; live: {json.dumps(drift)}")
    if len(skipped) == len(vocabs):
        return SKIP, ["no source reachable"]
    notes = [f"not checked live (source not beside this repo): {', '.join(skipped)}"] if skipped else []
    if live.get("law-model") is None:
        notes.append(f"law-model import failed: {law_err}")
    return (FAIL, out + notes) if out else (OK, notes)


CHECKS = [check_header, check_blocks_are_dicts, check_spine_stages,
          check_interfaces_are_satisfied, check_every_interface_has_an_implementer,
          check_predicates_are_typed_over_declared_kinds,
          check_entity_kinds_point_at_object_types, check_actions_are_honest,
          check_predicates_match_mechanism_schema,
          check_manifest_points_at_the_crosswalk, check_crosswalk_rows_are_well_formed,
          check_crosswalk_covers_every_member, check_shared_verb_names_map_identically,
          check_crosswalk_counts_are_derived, check_crosswalk_members_match_live_sources]


def run(manifest_path: Path = MANIFEST) -> list[tuple[str, str, list[str]]]:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = []
    for fn in CHECKS:
        r = fn(m)
        if isinstance(r, tuple):
            status, msgs = r
            results.append((fn.__name__, status, list(msgs)))
        else:
            results.append((fn.__name__, FAIL if r else OK, r))
    return results


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    results = run()
    for name, status, msgs in results:
        print(f"{status:5} {name}")
        for msg in msgs:
            print(f"      {msg}")
    fails = sum(1 for _, s, _ in results if s == FAIL)
    skips = sum(1 for _, s, _ in results if s == SKIP)
    print(f"\n{len(results)} checks · {fails} FAIL · {skips} skipped")
    return 1 if (strict and fails) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
