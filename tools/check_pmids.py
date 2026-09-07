#!/usr/bin/env python3
"""Resolve every PubMed id we ship and diff it against the citation we attached.

WHY THIS EXISTS
---------------
Same reason as `tools/check_curies.py`, one identifier space over. A PMID is
eight digits; every eight-digit string is a well-formed PMID, and most of them
are somebody else's paper. A resolve-and-diff pass on 2026-09-07 found, across
`src/biology_as_code/dig/` and `docs/metabolic-constants.md`:

    12 of 17 PMIDs (71%) naming a different paper
    12740047 "Macfarlane, SCFA production" -> in situ transduction on solid surfaces
    19052988 "Murphy, how mitochondria produce ROS" -> a non-Hodgkin lymphoma case report
    23380711 "Deponte, glutathione catalysis" -> anaerobic co-digestion of grease sludge
    14668792 "Rich, Keilin's respiratory chain" -> no PubMed record at all

Every one passed a regex. Three of them were "corrections" — a previous pass had
replaced a wrong id with another wrong id, twice in a row for the same paper,
because the fix was reasoned about instead of resolved. That is the whole lesson:
the only check that finds these is going and looking.

It matters more here than for a bibliography. These ids are not footnotes; they
are emitted inside `to_dict()` provenance, so a consumer reads them as the
machine-checkable warrant for a HOLDS. An unresolved identifier is decoration.

WHAT IT CHECKS
--------------
Every dict literal under `src/biology_as_code/` that carries both a `pmid` and a
`citation` key. The title from PubMed must appear in the citation string, both
normalised (case, punctuation, whitespace, unicode dashes). Titles are matched by
containment, not equality, so a full Vancouver reference passes and a truncated
one still has to carry the whole title.

CACHED, SO CI IS OFFLINE AND DETERMINISTIC
------------------------------------------
Responses live in `tools/pmid_cache.json`, committed. CI runs `--offline
--strict`, which never touches the network and *fails on a cache miss* — adding a
citation without resolving it is the failure this gate exists to catch, so an
unrun check must not be a pass.

    python3 tools/check_pmids.py                    # advisory, network, prints a report
    python3 tools/check_pmids.py --strict           # exit 1 on any mismatch
    python3 tools/check_pmids.py --offline --strict # cache only; what CI runs
    python3 tools/check_pmids.py --update-cache     # re-resolve and rewrite the cache
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "biology_as_code"
CACHE = ROOT / "tools" / "pmid_cache.json"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

_PUNCT = re.compile(r"[^a-z0-9 ]+")
_SPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Case, punctuation, unicode dashes and whitespace all collapse."""
    text = unicodedata.normalize("NFKD", text).lower()
    text = text.replace("–", "-").replace("—", "-").replace("’", "'")
    return _SPACE.sub(" ", _PUNCT.sub(" ", text)).strip()


def harvest(tree: ast.AST, path: pathlib.Path) -> list[dict]:
    """Every dict literal carrying both a `pmid` and a `citation` key."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        pairs = {}
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                folded = _fold(value)
                if folded is not None:
                    pairs[key.value] = folded
        if "pmid" in pairs and "citation" in pairs:
            found.append(
                {
                    "pmid": pairs["pmid"],
                    "citation": pairs["citation"],
                    "where": f"{path.relative_to(ROOT)}:{node.lineno}",
                }
            )
    return found


def _fold(node: ast.AST) -> str | None:
    """Constant strings and implicit concatenations; anything else is skipped."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fold(node.left), _fold(node.right)
        return None if left is None or right is None else left + right
    return None


def collect() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(SRC.rglob("*.py")):
        rows.extend(harvest(ast.parse(path.read_text()), path))
    return rows


def load_cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def fetch(pmids: list[str]) -> dict:
    """esummary in one batch. A pmid PubMed refuses is recorded, not dropped."""
    out: dict[str, dict] = {}
    for i in range(0, len(pmids), 50):
        batch = pmids[i : i + 50]
        url = f"{ESUMMARY}?" + urllib.parse.urlencode(
            {"db": "pubmed", "retmode": "json", "id": ",".join(batch)}
        )
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.load(response)["result"]
        for pmid in batch:
            record = payload.get(pmid, {})
            if record.get("error") or not record.get("title"):
                out[pmid] = {"title": None, "error": record.get("error", "no record")}
            else:
                out[pmid] = {
                    "title": record["title"].rstrip("."),
                    "source": record.get("source", ""),
                    "pubdate": record.get("pubdate", "")[:4],
                }
        time.sleep(0.4)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 on any mismatch")
    parser.add_argument("--offline", action="store_true", help="cache only, no network")
    parser.add_argument("--update-cache", action="store_true", help="re-resolve everything")
    args = parser.parse_args()

    rows = collect()
    cache = {} if args.update_cache else load_cache()
    wanted = sorted({row["pmid"] for row in rows})
    missing = [pmid for pmid in wanted if pmid not in cache]

    if missing and args.offline:
        print(f"CACHE MISS — {len(missing)} pmid(s) never resolved: {', '.join(missing)}")
        print("An unrun check is not a pass. Run: python3 tools/check_pmids.py --strict")
        return 1
    if missing:
        cache.update(fetch(missing))
        CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")

    bad, ok = [], 0
    for row in rows:
        record = cache.get(row["pmid"], {})
        title = record.get("title")
        if title is None:
            bad.append((row, "no PubMed record"))
        elif normalise(title) in normalise(row["citation"]):
            ok += 1
        else:
            bad.append((row, f'resolves to "{title}" ({record.get("source", "?")})'))

    print(f"{len(rows)} shipped citation(s); {ok} confirmed, {len(bad)} mismatched")
    for row, why in bad:
        print(f"  MISMATCH {row['pmid']}  {row['where']}\n    {why}")
    if bad and args.strict:
        return 1
    if bad:
        print("(advisory — pass --strict to fail on these)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
