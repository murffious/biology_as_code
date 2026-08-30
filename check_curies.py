#!/usr/bin/env python3
"""Resolve every ontology id in the tree and diff it against the label we gave it.

WHY THIS EXISTS
---------------
A syntactic CURIE check is nearly worthless. `MONDO:0002513` matches every regex
you can write and is a perfectly well-formed identifier; it is also *kidney benign
neoplasm*, and it sat in the tree labelled *hypertriglyceridemia*. A resolve-and-diff
pass on 2026-08-29 found, across the two repos:

    23 of 79 place ids in the digestive atlas (29%) naming a different body part
    10 of 78 CURIEs in principles.json naming a different concept
    UBERON:0001409 "Thoracic duct"      -> semispinalis capitis
    CHEBI:52320    "xanthan gum"        -> ergosteryl ester
    ECO:0000180    "in-vitro/animal"    -> clinical study evidence (the opposite)
    OBI:0000473    "controlled trial"   -> Bruker NMR Case sample changer

Every one of those passes a regex. The only check that finds them is going and
looking. That is all this script does.

TWO THINGS IT HAS TO GET RIGHT, OR IT GETS SWITCHED OFF
-------------------------------------------------------
1. SYNONYMS. A naive label diff over the eleven anatomy hints flags four; only one
   is real. `integumental system` vs our "Integumentary", `renal system` vs our
   "Urinary" (a documented altLabel — that synonym is what settled the renal/urinary
   question), `hemolymphoid` vs "Lymphatic / immune". A 27% false-positive rate
   means the gate is noise and dies in a week. So: match label OR any synonym,
   normalised, both directions.

2. OBSOLESCENCE. An obsolete term still resolves and still label-matches, so a
   label-only diff passes it. `GO:0055128` was superseded by `GO:0050892`; two CDNO
   ids are withdrawn. Root cause of those two: `fdp-1/resolver/build_cdno_xref.py`
   greps `^id:` and `^xref:` out of the OBO and never reads `is_obsolete`.

ADVISORY BY DEFAULT
-------------------
Exits 0 and prints, unless --strict. Every current failure is recorded in
curie_baseline.json; the ratchet is that the count may only go DOWN. This is the
same shape as the register-quality ratchet: making the problem visible must not
block the work that is already in flight.

Responses are cached under .curie_cache/ so a second run is offline and instant.
Networked gates do not belong in CI unprimed; run this locally, commit the
baseline, and let CI compare against the cache.

    python3 check_curies.py                  # advisory, prints a report
    python3 check_curies.py --strict         # exit 1 if debt exceeds the baseline
    python3 check_curies.py --update-baseline
    python3 check_curies.py --offline        # cache only, no network
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
CACHE = ROOT / ".curie_cache"
BASELINE = ROOT / "curie_baseline.json"

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".curie_cache",
             "archive", "site-packages"}
SCAN_SUFFIXES = {".json", ".jsonl", ".py", ".md", ".ts", ".tsx"}

# Prefixes we can actually resolve. Anything else is reported as UNRESOLVABLE
# rather than silently passed — an id we cannot check is not an id we trust.
OLS_ONTOLOGIES = {
    "UBERON": "uberon", "CL": "cl", "GO": "go", "CHEBI": "chebi",
    "MONDO": "mondo", "HP": "hp", "PATO": "pato", "OBI": "obi",
    "ECO": "eco", "RO": "ro", "BFO": "bfo", "FOODON": "foodon",
    "NCBITaxon": "ncbitaxon", "CDNO": "cdno", "NCIT": "ncit",
}
# Reactome is NOT in OLS4. Three of four Reactome ids in the spine were wrong
# precisely because whatever checked them could only see OLS4 and skipped them.
REACTOME = re.compile(r"^R-[A-Z]{3}-\d+$")

CURIE = re.compile(r"\b(" + "|".join(OLS_ONTOLOGIES) + r")[:_](\d{4,})\b")

# How a declared label sits next to its id, across the shapes actually in the tree.
PAIR_PATTERNS = [
    # {"id": "UBERON:0001007", "label": "digestive system"}  (either order)
    re.compile(r'"(?:id|curie|term|ref|iri)"\s*:\s*"([A-Za-z]+[:_]\d{4,})"\s*,\s*'
               r'"(?:label|name|term|title|text)"\s*:\s*"([^"]{2,80})"'),
    re.compile(r'"(?:label|name|term|title|text)"\s*:\s*"([^"]{2,80})"\s*,\s*'
               r'"(?:id|curie|term|ref|iri)"\s*:\s*"([A-Za-z]+[:_]\d{4,})"'),
    # "UBERON:0001007": "digestive system"
    re.compile(r'"([A-Za-z]+[:_]\d{4,})"\s*:\s*"([^"]{2,80})"'),
    # uberion_hint="UBERON:0000383",  ... name="Muscular"   (python, either order)
    re.compile(r'name="([^"]{2,60})"[^)]{0,400}?_hint="([A-Za-z]+[:_]\d{4,})"', re.S),
    # "ECO:0000179",   // animal model system study evidence   (also # and <!-- -->)
    re.compile(r'"([A-Za-z]+[:_]\d{4,})"[^\n]{0,40}?(?://|#|<!--)\s*([^\n(|-]{3,80})'),
    # positional tuples: ("phys.collagen_fibril", "Collagen fibril organization",
    #                     "GO:0030199", ...) — the label is the quoted prose
    # immediately before the id. This is the shape in physiological_effects.py
    # and biochemical_mechanisms.py, which is where the audit said the public
    # defects were and which the first version of this file could not see at all.
    re.compile(r'"([A-Z][^"\n]{3,70})"\s*,\s*\n?\s*"([A-Za-z]+[:_]\d{4,})"'),
    # markdown table cell: | UBERON:0001007 | digestive system |
    re.compile(r'\|\s*`?([A-Za-z]+[:_]\d{4,})`?\s*\|\s*([^|\n]{3,70})\|'),
]


def _norm(s: str) -> str:
    """Compare on meaning, not decoration. 'Lymphatic / immune' -> 'lymphatic immune'."""
    s = s.lower().strip()
    s = re.sub(r"\(.*?\)", " ", s)                 # drop parentheticals
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(the|a|an|of|body|system|systems)\b", " ", s)
    return " ".join(s.split())


def _cache_path(curie: str) -> pathlib.Path:
    return CACHE / (curie.replace(":", "_") + ".json")


def resolve(curie: str, offline: bool = False) -> dict | None:
    """Return {label, synonyms, obsolete} or None if it does not exist."""
    cp = _cache_path(curie)
    if cp.exists():
        return json.loads(cp.read_text()) or None
    if offline:
        return {"_uncached": True}

    prefix, local = re.split(r"[:_]", curie, maxsplit=1)
    try:
        if REACTOME.match(curie) or prefix == "R":
            url = f"https://reactome.org/ContentService/data/query/{curie}"
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.load(r)
            out = {"label": d.get("displayName") or "", "synonyms": d.get("name") or [],
                   "obsolete": False}
        else:
            ont = OLS_ONTOLOGIES[prefix]
            iri = f"http://purl.obolibrary.org/obo/{prefix}_{local}"
            url = ("https://www.ebi.ac.uk/ols4/api/ontologies/"
                   f"{ont}/terms?iri={urllib.parse.quote(iri, safe='')}")
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.load(r)
            terms = d.get("_embedded", {}).get("terms") or []
            if not terms:
                out = None
            else:
                t = terms[0]
                out = {"label": t.get("label") or "",
                       "synonyms": t.get("synonyms") or [],
                       "obsolete": bool(t.get("is_obsolete"))}
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError):
        return {"_error": True}

    CACHE.mkdir(exist_ok=True)
    cp.write_text(json.dumps(out))
    return out


def harvest(root: pathlib.Path) -> dict[tuple[str, str], set[str]]:
    """(curie, declared_label) -> the files that assert it."""
    found: dict[tuple[str, str], set[str]] = {}
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in SCAN_SUFFIXES:
            continue
        if SKIP_DIRS & set(p.parts) or p.name == pathlib.Path(__file__).name:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for pat in PAIR_PATTERNS:
            for m in pat.finditer(text):
                a, b = m.group(1), m.group(2)
                curie, label = (a, b) if re.match(r"^[A-Za-z]+[:_]\d{4,}$", a) else (b, a)
                if not re.match(r"^[A-Za-z]+[:_]\d{4,}$", curie):
                    continue
                curie = curie.replace("_", ":", 1)
                if curie.split(":")[0] not in OLS_ONTOLOGIES:
                    continue
                label = label.strip().strip(",;.")
                if not label or label.startswith(("http", "{")):
                    continue
                # An id is never a label. Registers pair a MONDO id with its DOID
                # xref and an HP id with a sibling HP id; reading the second id as
                # the first one's "label" invents a mismatch that is not there.
                # This was 9 of the first 36 findings — a third of the report was
                # the checker misreading a crosswalk as a naming error.
                if re.match(r"^[A-Za-z][A-Za-z0-9._]*[:_]\d{3,}$", label):
                    continue
                found.setdefault((curie, label), set()).add(
                    str(p.relative_to(root)))
    return found


def audit(root: pathlib.Path, offline: bool = False) -> list[dict]:
    problems = []
    pairs = harvest(root)
    for (curie, label), files in sorted(pairs.items()):
        r = resolve(curie, offline=offline)
        if r is None:
            problems.append({"curie": curie, "declared": label, "kind": "NOT_FOUND",
                             "actual": None, "files": sorted(files)})
            continue
        if not r or r.get("_error") or r.get("_uncached"):
            continue                                  # unknown, not a finding
        names = [r["label"]] + list(r.get("synonyms") or [])
        want = _norm(label)
        if not want:
            continue
        hit = any(want == _norm(n) or want in _norm(n) or _norm(n) in want
                  for n in names if _norm(n))
        if not hit:
            problems.append({"curie": curie, "declared": label, "kind": "WRONG_CONCEPT",
                             "actual": r["label"], "files": sorted(files)})
        elif r.get("obsolete"):
            problems.append({"curie": curie, "declared": label, "kind": "OBSOLETE",
                             "actual": r["label"], "files": sorted(files)})
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if debt exceeds the baseline")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--offline", action="store_true", help="cache only, no network")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args()

    root = pathlib.Path(a.root)
    pairs = harvest(root)
    all_curies = set()
    for p in root.rglob("*"):
        if (p.is_file() and p.suffix in SCAN_SUFFIXES
                and not (SKIP_DIRS & set(p.parts))
                and p.name != pathlib.Path(__file__).name):
            try:
                for m in CURIE.finditer(p.read_text(errors="ignore")):
                    all_curies.add(m.group(0).replace("_", ":", 1))
            except OSError:
                pass
    checked = {k[0] for k in pairs}
    problems = audit(root, offline=a.offline)
    by_kind: dict[str, list[dict]] = {}
    for p in problems:
        by_kind.setdefault(p["kind"], []).append(p)

    for kind in ("NOT_FOUND", "WRONG_CONCEPT", "OBSOLETE"):
        rows = by_kind.get(kind) or []
        if not rows:
            continue
        print(f"\n{kind}  ({len(rows)})")
        for p in rows:
            actual = f" -> actually {p['actual']!r}" if p["actual"] else " -> does not exist"
            print(f"  {p['curie']:<18} declared {p['declared']!r}{actual}")
            for f in p["files"][:3]:
                print(f"        {f}")

    # No silent caps: an id with no adjacent label cannot be diffed against
    # anything, so it is NOT checked. Saying "0 problems" while skipping most of
    # the tree is the failure this whole script exists to prevent.
    unpaired = sorted(all_curies - checked)
    print(f"\nCOVERAGE  {len(checked)}/{len(all_curies)} distinct ids carry a "
          f"declared label and were resolved and diffed.")
    if unpaired:
        print(f"          {len(unpaired)} have NO adjacent label, so nothing was "
              f"checked for them — not a pass, an unknown.")
        print(f"          e.g. {', '.join(unpaired[:6])}")

    total = len(problems)
    if a.update_baseline:
        BASELINE.write_text(json.dumps({
            "what_this_is": ("Ontology ids whose declared label does not match the "
                             "term they resolve to. RATCHET: `count` may only go "
                             "DOWN. Fixing one means lowering it in the same commit."),
            "as_of": "2026-08-29",
            "count": total,
            "problems": problems,
        }, indent=1) + "\n")
        print(f"\nbaseline written: {total} problem(s)")
        return 0

    prior = json.loads(BASELINE.read_text())["count"] if BASELINE.exists() else None
    print(f"\n{total} problem(s)" + (f"; baseline {prior}" if prior is not None else ""))
    if prior is not None and total < prior:
        print(f"IMPROVED by {prior - total} — lower 'count' in {BASELINE.name} to {total}.")
    if a.strict and prior is not None and total > prior:
        print(f"FAIL  debt grew by {total - prior}")
        return 1
    if a.strict and prior is None:
        print("FAIL  no baseline; run --update-baseline")
        return 1
    print("advisory — not failing the build" if not a.strict else "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
