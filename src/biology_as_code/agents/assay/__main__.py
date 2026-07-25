"""CLI: python -m assay test "claim text" | python -m assay golden"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .atomize import atomize
from .fixtures.golden import GOLDEN
from .pipeline import assay_claim, assay_to_public_dict
from .score import EvidenceSet, score


def cmd_test(args: argparse.Namespace) -> int:
    from .multi_claim import assay_organ_healing_chart, is_organ_healing_chart

    if is_organ_healing_chart(args.text) or args.text.strip().upper() in (
        "ORGAN HEALING DRINKS",
        "ORGAN CHART",
        "@IMAGE",
    ):
        text = args.text
        if text.strip().upper() in ("ORGAN HEALING DRINKS", "ORGAN CHART", "@IMAGE"):
            from .multi_claim import organ_healing_chart_text

            text = organ_healing_chart_text()
        bundle = assay_organ_healing_chart(text, platform=args.platform)
        if args.json:
            print(json.dumps(bundle.to_dict(), indent=2))
            return 0
        print("═" * 60)
        print("ASSAY — multi-claim chart (organ → system)")
        print("═" * 60)
        print(bundle.title)
        print()
        for row in bundle.rows:
            v = row["verdict"]
            print(
                f"  [{v['label']:9}] {row['drink']:18} → {row['organ']:8}  "
                f"system={row['system_label']}"
            )
            print(f"             {row['scoped_restatement'][:100]}")
        print()
        print("Systems summary")
        for s in bundle.systems_summary:
            print(f"  {s['system_label']}: {s['net']}")
        print()
        print("Scoped restatement")
        print(bundle.scoped_restatement[:800])
        return 0

    result = assay_claim(
        args.text,
        platform=args.platform,
        author=args.author,
    )
    if args.json:
        print(json.dumps(assay_to_public_dict(result), indent=2))
        return 0 if not result.validation_errors else 1

    c = result.claim
    v = c.verdict
    print("═" * 60)
    print("ASSAY — claim stress test")
    print("═" * 60)
    print(f"claim_id   {c.claim_id}")
    print(f"subject    {c.subject.canonical}  ({c.subject.ontology_id or 'no id'})")
    print(f"fixture    {result.matched_fixture or '—'}")
    print(f"verdict    {v.label}  ({v.survived}/{v.total} survived)")
    print(f"rule       {v.rule}")
    print(f"confidence {result.confidence}")
    print()
    print("Atoms")
    for a in c.atomic_claims:
        site = f" · {a.site}" if a.site else ""
        print(f"  [{a.grade or '?'}] {a.predicate} → {a.outcome.canonical}{site}")
        if a.evidence_basis:
            print(f"         {a.evidence_basis[:120]}")
    print()
    print("Gauntlet")
    for at in c.attacks:
        mark = "SURVIVES" if at.pass_ else "FAILS"
        print(f"  {mark:8}  {at.name}")
        print(f"           {at.finding[:110]}")
    print()
    if c.red_flags:
        print("Red flags")
        for f in c.red_flags:
            print(f"  • {f}")
        print()
    print("Scoped restatement (coach-safe)")
    print(f"  {c.scoped_restatement}")
    print()
    if result.validation_errors:
        print("VALIDATION ERRORS:", result.validation_errors)
        return 1
    print("schema     OK")
    return 0


def cmd_golden(_: argparse.Namespace) -> int:
    failed = 0
    for fid, g in GOLDEN.items():
        ar = atomize(g["raw_text"])
        # prefer fixture id from atomize when present
        from .pipeline import _ground

        evidence, _, _ = _ground(ar.matched_fixture or fid, ar)
        # force golden evidence
        evidence = EvidenceSet.from_dict(g["evidence"])
        verdict, attacks, _conf = score(evidence, ar.atoms)
        exp = g["expected_verdict"]
        ok = verdict.label == exp
        if "expected_survived_min" in g and verdict.survived < g["expected_survived_min"]:
            ok = False
        if "expected_survived_max" in g and verdict.survived > g["expected_survived_max"]:
            ok = False
        status = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        print(
            f"[{status}] {fid}: got {verdict.label} {verdict.survived}/{verdict.total} "
            f"(expected {exp})"
        )
        if not ok:
            print(f"       failed: {verdict.failed_attacks}")
    return 1 if failed else 0


def cmd_export(args: argparse.Namespace) -> int:
    result = assay_claim(args.text)
    path = Path(args.out)
    path.write_text(json.dumps(result.jsonld, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="assay",
        description="Assay — normalize & stress-test nutrition claims (CanonicalClaim standard)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("test", help="Atomize + gauntlet a claim")
    t.add_argument("text", help="Raw claim text")
    t.add_argument("--platform", default="cli")
    t.add_argument("--author", default=None)
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_test)

    g = sub.add_parser("golden", help="Run golden fixture suite")
    g.set_defaults(func=cmd_golden)

    e = sub.add_parser("export", help="Export JSON-LD ClaimReview envelope")
    e.add_argument("text")
    e.add_argument("--out", default="claim.jsonld")
    e.set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
