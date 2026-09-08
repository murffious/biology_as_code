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
**Code.** Every dict literal under `src/biology_as_code/` that carries both a
`pmid` and a `citation` key.

**Prose.** Every PubMed id in `docs/**.md` and the top-level `*.md`, matched
against the citation text around it. Docs were the blind spot that mattered: four
of the twelve wrong ids found on 2026-09-07 were on `docs/metabolic-constants.md`,
where nothing read them. A page that tells a reader which paper backs a constant
is making the same promise the code makes.

Prose has one thing code does not: ids that are *deliberately* wrong. The
correction tables record what an id used to be and what it actually resolves to.
Those live in `tools/pmid_docs.allow`, one per line with a written reason, the
same shape as `tools/separation.allow`. A gate with no exception mechanism gets
switched off the first week. The title from PubMed must appear in the citation string, both
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
    python3 tools/check_pmids.py --code-only        # skip prose
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
DOCS = ROOT / "docs"
CACHE = ROOT / "tools" / "pmid_cache.json"
ALLOW = ROOT / "tools" / "pmid_docs.allow"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

#: `PMID 12345`, `PMID: 12345`, and the bare pubmed URL.
PMID_IN_PROSE = re.compile(
    r"(?:PMID[:\s]\s*|pubmed\.ncbi\.nlm\.nih\.gov/)(\d{4,9})", re.IGNORECASE
)

#: How far around the id to look for the title. Markdown wraps citations across
#: lines, and a title can sit either side of the identifier.
CONTEXT_LINES = 6

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


def harvest_grounded(tree: ast.AST, path: pathlib.Path) -> list[dict]:
    """PubMed ids attached to a constant by `grounded(...)`.

    These carry no title to diff against — the `supports` field says what the
    paper backs, not what it is called — so they are existence-checked only.
    They are harvested here anyway, and this is the point: `check_constants.py`
    requires every grounded constant's id to be present in `pmid_cache.json`, so
    if this harvester did not see them, `--update-cache` would drop them and the
    constants gate would start failing on ids it could no longer resolve. One
    harvester, one cache, no drift between the two gates.
    """
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "grounded"):
            continue
        for kw in node.keywords:
            if kw.arg == "pmid" and isinstance(kw.value, ast.Constant):
                rows.append(
                    {
                        "pmid": str(kw.value.value),
                        "citation": "",
                        "existence_only": True,
                        "where": f"{path.relative_to(ROOT)}:{node.lineno}",
                    }
                )
    return rows


def collect() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text())
        rows.extend(harvest(tree, path))
        rows.extend(harvest_grounded(tree, path))
    return rows


def harvest_json(path: pathlib.Path) -> list[dict]:
    """Every object in a JSON register carrying both a `pmid` and a `title`.

    Checked as strictly as code: the title is right there, so there is no excuse
    for it not matching. This is where an evidence register keeps its citations,
    and it is the *authoritative* copy — prose that refers to a study by its
    internal record id (EV-041) is pointing here.
    """
    rows: list[dict] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            pmid, title = node.get("pmid"), node.get("title")
            if isinstance(pmid, str) and isinstance(title, str) and pmid.isdigit():
                rows.append(
                    {
                        "pmid": pmid,
                        "citation": title,
                        "stored_title": True,
                        "where": str(path.relative_to(ROOT)),
                    }
                )
                return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    try:
        walk(json.loads(path.read_text()))
    except json.JSONDecodeError:
        pass
    return rows


def collect_json() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(SRC.rglob("*.json")):
        rows.extend(harvest_json(path))
    return rows


def load_allow() -> tuple[dict[str, str], dict[str, str]]:
    """`<pmid or path>  <reason>` per line; `#` comments. A reason is mandatory.

    Two kinds of entry, because prose has two kinds of exception:

    * a **pmid@path** — an id quoted deliberately *in one named file*, such as
      the correction tables that record what an identifier used to be. Skipped
      there and nowhere else, so the same wrong id used as a real citation on
      another page is still caught. A bare pmid is accepted and skips everywhere,
      but prefer the scoped form.
    * a **path** — a file of bare reference lists, ids with no author or title
      beside them to diff against. Not skipped: every id in it is still checked
      for *existence*, which is what catches a dead identifier like the one that
      resolved to no PubMed record at all. Only the "does it name this paper"
      half is dropped, because there is no name to compare.
    """
    ids: dict[str, str] = {}
    paths: dict[str, str] = {}
    if not ALLOW.exists():
        return ids, paths
    for raw in ALLOW.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, _, reason = line.partition(" ")
        key = key.strip()
        if not reason.strip():
            raise SystemExit(f"{ALLOW.name}: {key} has no written reason")
        if key.split("@", 1)[0].isdigit():
            ids[key] = reason.strip()
        else:
            paths[key] = reason.strip()
    return ids, paths


def harvest_prose(path: pathlib.Path) -> list[dict]:
    """Every PubMed id in a markdown file, with the text around it."""
    lines = path.read_text().splitlines()
    rows = []
    for i, line in enumerate(lines):
        for match in PMID_IN_PROSE.finditer(line):
            lo = max(0, i - CONTEXT_LINES)
            hi = min(len(lines), i + CONTEXT_LINES + 1)
            rows.append(
                {
                    "pmid": match.group(1),
                    "citation": " ".join(lines[lo:hi]),
                    "where": f"{path.relative_to(ROOT)}:{i + 1}",
                }
            )
    return rows


def collect_prose() -> list[dict]:
    paths = sorted(DOCS.rglob("*.md")) + sorted(ROOT.glob("*.md"))
    rows: list[dict] = []
    for path in paths:
        rows.extend(harvest_prose(path))
    # One markdown link yields two hits — the visible `PMID n` and the URL behind
    # it. Same id, same line, one citation.
    seen, unique = set(), []
    for row in rows:
        key = (row["pmid"], row["where"])
        if key not in seen:
            seen.add(key)
            row["prose"] = True
            unique.append(row)
    return unique


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
                authors = record.get("authors") or []
                first = authors[0]["name"] if authors else record.get("sortfirstauthor", "")
                out[pmid] = {
                    "title": record["title"].rstrip("."),
                    "author": first.split(" ")[0] if first else "",
                    "source": record.get("source", ""),
                    "pubdate": record.get("pubdate", "")[:4],
                }
        time.sleep(0.4)
    return out


#: Below this many characters a "prefix" is not evidence of anything.
MIN_PREFIX = 40


def _prefix_match(stored: str, resolved: str) -> bool:
    """Is the stored title the opening of the resolved one?"""
    return len(stored) >= MIN_PREFIX and resolved.startswith(stored)


def _author_present(record: dict, context: str) -> bool:
    """Is the first author's surname in the text around the id?"""
    surname = normalise(record.get("author", ""))
    return bool(surname) and surname in context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 on any mismatch")
    parser.add_argument("--offline", action="store_true", help="cache only, no network")
    parser.add_argument("--update-cache", action="store_true", help="re-resolve everything")
    parser.add_argument("--code-only", action="store_true", help="skip prose in docs/")
    args = parser.parse_args()

    rows = collect() + collect_json()
    allowed: dict[str, str] = {}
    unnamed_files: dict[str, str] = {}
    if not args.code_only:
        allowed, unnamed_files = load_allow()
        for row in collect_prose():
            path = row["where"].rsplit(":", 1)[0]
            if row["pmid"] in allowed or f"{row['pmid']}@{path}" in allowed:
                continue
            row["existence_only"] = path in unnamed_files
            rows.append(row)
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

    bad, ok, existence = [], 0, 0
    for row in rows:
        record = cache.get(row["pmid"], {})
        title = record.get("title")
        if title is None:
            bad.append((row, "no PubMed record"))
            continue
        if row.get("existence_only"):
            # A bare reference list. The id resolves, which is all this file can
            # assert; there is no author or title beside it to diff against.
            existence += 1
            continue
        context = normalise(row["citation"])
        if normalise(title) in context:
            ok += 1
        elif row.get("stored_title") and _prefix_match(context, normalise(title)):
            # A register stores the title as its own field, and several are
            # truncated mid-word by whatever wrote them. Containment therefore
            # runs the other way here: the stored string must be the opening of
            # the real one. Length-guarded so a stub cannot match by accident.
            ok += 1
        elif row.get("prose") and _author_present(record, context):
            # Prose abbreviates titles ("A linear steady-state treatment of
            # enzymatic chains." for a title that runs on), so title containment
            # false-positives constantly and a noisy gate gets switched off. The
            # surname is the discriminating field: every wrong id found on
            # 2026-09-07 named a paper by an unrelated author, and would fail
            # here. Code rows keep the strict title test — they carry a full
            # citation string and have no excuse.
            ok += 1
        else:
            bad.append((row, f'resolves to "{title}" ({record.get("source", "?")})'))

    scope = "code" if args.code_only else "code + prose"
    extra = f", {existence} existence-only" if existence else ""
    skipped = f", {len(allowed)} quoted-deliberately" if allowed else ""
    print(
        f"{len(rows)} shipped citation(s) [{scope}]; "
        f"{ok} confirmed, {len(bad)} mismatched{extra}{skipped}"
    )
    for row, why in bad:
        print(f"  MISMATCH {row['pmid']}  {row['where']}\n    {why}")
    if bad and args.strict:
        return 1
    if bad:
        print("(advisory — pass --strict to fail on these)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
