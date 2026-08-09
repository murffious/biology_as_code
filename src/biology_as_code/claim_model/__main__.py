"""
Adjudicate claims from the command line.

    python -m biology_as_code.claim_model "Vitamin C increases iron absorption"
    python -m biology_as_code.claim_model --json "Iron supports energy"
    echo "claim one" | python -m biology_as_code.claim_model -
    python -m biology_as_code.claim_model --metrics
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="biology_as_code.claim_model",
        description="Adjudicate a nutrition claim against the constitution.",
    )
    ap.add_argument("claims", nargs="*", help="claims to rule on; '-' reads stdin")
    ap.add_argument("--json", action="store_true", help="emit claim-audit fixtures")
    ap.add_argument("--metrics", action="store_true", help="report model metrics and exit")
    ap.add_argument("--no-model", action="store_true",
                    help="rule without the evidence-grade model (constitution only)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    from biology_as_code.claim_model import Court, EvidenceGradeModel
    from biology_as_code.graph import build

    graph = build()
    model = None if args.no_model else EvidenceGradeModel.train_from_graph(
        graph, seed=args.seed
    )

    if args.metrics:
        report = {
            "graph": graph.counts(),
            "integrity": graph.integrity_report(),
            "model": model.metrics if model else None,
        }
        report["integrity"].pop("unsourced_bound_ids", None)
        print(json.dumps(report, indent=2))
        return 0

    claims = list(args.claims)
    if not claims or claims == ["-"]:
        claims = [ln.strip() for ln in sys.stdin if ln.strip()]
    if not claims:
        ap.error("no claims given")

    court = Court(graph, model)
    rulings = court.adjudicate_many(claims)

    if args.json:
        print(json.dumps([r.to_fixture() for r in rulings], indent=2))
    else:
        for i, ruling in enumerate(rulings):
            if i:
                print()
            print(ruling.explain())

    # Non-zero when anything was refused, so this can gate a build.
    return 1 if any(r.verdict == "REFUSE" for r in rulings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
