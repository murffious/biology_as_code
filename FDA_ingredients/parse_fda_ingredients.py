#!/usr/bin/env python3
"""
parse_fda_ingredients.py — clean FDA inventory CSVs + overlap vs nutrient nodes.

Usage:
  python3 parse_fda_ingredients.py
  python3 parse_fda_ingredients.py --dir /path/to/FDA_ingredients
  python3 parse_fda_ingredients.py --nodes-root ../nutrient-nodes

Writes under <dir>/clean/:
  FoodSubstances.clean.csv
  GRASNotices.clean.csv
  FCN.clean.csv
  IndirectAdditives.clean.csv
  overlap_report.md
  overlap_matches.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


PREAMBLE_STARTS = (
    "Downloaded from",
    "According to Section",
    "It is important to note",
    "Consult the regulation",
)

HEADER_MARKERS = (
    "Substance",
    "FCN No",
    "GRAS Notice",
    "CAS Reg",
    "CAS Registry",
    "Food Contact Substance",
)


def strip_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "; ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def normalize_excel_formulas(text: str) -> str:
    # GRAS export sometimes uses =T("value")
    return re.sub(r'=T\("([^"]*)"\)', r'"\1"', text)


def find_header_line(lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if s.startswith(PREAMBLE_STARTS) or (s.startswith('"') and "inventory" in s.lower()):
            continue
        if any(m in s for m in HEADER_MARKERS) and "," in s:
            return i
    return None


def load_clean_rows(path: Path) -> tuple[list[dict], list[str]]:
    raw = path.read_text(encoding="latin-1", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    hi = find_header_line(lines)
    if hi is None:
        raise ValueError(f"No header found in {path.name}")
    body = normalize_excel_formulas("\n".join(lines[hi:]))
    reader = csv.DictReader(body.splitlines())
    fieldnames = list(reader.fieldnames or [])
    rows = []
    for r in reader:
        # skip empty
        if not any((v or "").strip() for v in r.values()):
            continue
        clean = {k: strip_html(v or "") if isinstance(v, str) else v for k, v in r.items()}
        rows.append(clean)
    return rows, fieldnames


def substance_fields(row: dict) -> tuple[str, str, str]:
    """Return (name, other_names, use)."""
    name = ""
    other = ""
    use = ""
    for k, v in row.items():
        if not k:
            continue
        kl = k.lower()
        if not name and ("substance" in kl or kl == "food contact substance"):
            name = v or ""
        if "other name" in kl:
            other = v or ""
        if "intended use" in kl or "technical effect" in kl or "used for" in kl:
            use = v or ""
    return name, other, use


def cas_field(row: dict) -> str:
    for k, v in row.items():
        if k and "cas" in k.lower():
            return (v or "").strip()
    return ""


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


# --- overlap helpers --------------------------------------------------------

def slug_tokens(s: str) -> set[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9+]+", " ", s)
    stop = {
        "and", "or", "the", "of", "from", "for", "in", "to", "a", "an", "as",
        "use", "used", "agent", "ingredient", "food", "acid", "oil", "extract",
        "sodium", "potassium", "calcium", "with", "by", "on", "at", "level",
        "general", "purpose", "component", "components",
    }
    toks = {t for t in s.split() if len(t) > 2 and t not in stop}
    return toks


def build_node_index(nodes_root: Path) -> list[dict]:
    """Load nutrient_id + display name aliases from deep/ and deep-bioactives/."""
    entries = []
    for sub in ("deep", "deep-bioactives"):
        d = nodes_root / sub
        if not d.is_dir():
            continue
        pack = "A" if sub == "deep" else "B"
        for p in sorted(d.glob("*.yml")):
            nid = p.stem
            text = p.read_text(encoding="utf-8", errors="replace")
            names = {nid.replace("_", " ")}
            m = re.search(r'^\s*name:\s*["\']?(.+?)["\']?\s*$', text, re.M)
            if m:
                names.add(m.group(1).strip().strip('"').strip("'"))
            # symbol line
            m2 = re.search(r"^\s*symbol:\s*(\S+)", text, re.M)
            if m2:
                names.add(m2.group(1))
            # forms
            for fm in re.findall(r"^\s*-\s*form:\s*(\S+)", text, re.M):
                names.add(fm.replace("_", " "))
            aliases = sorted({re.sub(r"\s+", " ", n.lower()) for n in names if n})
            token_sets = [slug_tokens(a) for a in aliases]
            entries.append({
                "nutrient_id": nid,
                "pack": pack,
                "aliases": aliases,
                "token_sets": token_sets,
            })
    return entries


def match_substance(name: str, other: str, nodes: list[dict]) -> list[dict]:
    """Return ranked matches: exact alias, then high token overlap."""
    blob = f"{name} {other}".lower()
    blob_norm = re.sub(r"\s+", " ", blob).strip()
    hits = []
    for n in nodes:
        best = None
        # exact / substring alias
        for a in n["aliases"]:
            if not a or len(a) < 3:
                continue
            if a == blob_norm or a in blob_norm or blob_norm in a:
                score = 100 if a == blob_norm else 80
                best = max(best or 0, score)
        # token Jaccard-ish
        st = slug_tokens(blob_norm)
        if st:
            for ts in n["token_sets"]:
                if not ts:
                    continue
                inter = len(st & ts)
                if inter == 0:
                    continue
                # require significant overlap
                j = inter / len(st | ts)
                if inter >= 2 or (inter == 1 and list(ts)[0] in st and len(list(ts)[0]) > 5):
                    best = max(best or 0, int(40 + 50 * j))
        if best and best >= 55:
            hits.append({
                "nutrient_id": n["nutrient_id"],
                "pack": n["pack"],
                "score": best,
            })
    hits.sort(key=lambda x: (-x["score"], x["nutrient_id"]))
    # dedupe by nutrient_id
    seen = set()
    out = []
    for h in hits:
        if h["nutrient_id"] in seen:
            continue
        seen.add(h["nutrient_id"])
        out.append(h)
    return out[:5]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="FDA_ingredients directory",
    )
    ap.add_argument(
        "--nodes-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "nutrient-nodes",
        help="Path to nutrient-nodes (deep + deep-bioactives)",
    )
    args = ap.parse_args()
    src: Path = args.dir
    out_dir = src / "clean"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "FoodSubstances.csv": "food_substances",
        "GRASNotices.csv": "gras_notices",
        "FCN.csv": "fcn",
        "IndirectAdditives.csv": "indirect_additives",
    }

    all_parsed: dict[str, list[dict]] = {}
    print(f"Parsing FDA inventories in {src}\n")

    for fname, key in files.items():
        path = src / fname
        if not path.exists():
            print(f"  SKIP missing {fname}")
            continue
        rows, fields = load_clean_rows(path)
        # add helper columns
        for r in rows:
            name, other, use = substance_fields(r)
            r["_substance"] = name
            r["_other_names"] = other
            r["_use"] = use
            r["_cas"] = cas_field(r)
            r["_inventory"] = key
        fields2 = ["_inventory", "_substance", "_other_names", "_use", "_cas"] + [
            f for f in fields if f
        ]
        dest = out_dir / fname.replace(".csv", ".clean.csv")
        write_csv(dest, rows, fields2)
        all_parsed[key] = rows
        print(f"  {fname:25} → {dest.name:30}  {len(rows):5,} rows")

    # Overlap vs nutrient nodes
    nodes = build_node_index(args.nodes_root)
    print(f"\nNode index: {len(nodes)} nutrients from {args.nodes_root}")

    match_rows = []
    by_pack = defaultdict(int)
    by_inventory = defaultdict(int)
    examples = []

    # Prefer GRAS + FoodSubstances for nutrition overlap; still scan all
    for inv, rows in all_parsed.items():
        for r in rows:
            name = r.get("_substance") or ""
            if not name or len(name) < 3:
                continue
            hits = match_substance(name, r.get("_other_names") or "", nodes)
            if not hits:
                continue
            top = hits[0]
            by_pack[top["pack"]] += 1
            by_inventory[inv] += 1
            rec = {
                "inventory": inv,
                "substance": name,
                "cas": r.get("_cas") or "",
                "use": (r.get("_use") or "")[:200],
                "matched_nutrient_id": top["nutrient_id"],
                "pack": top["pack"],
                "score": top["score"],
                "alt_matches": ";".join(
                    f"{h['nutrient_id']}({h['score']})" for h in hits[1:4]
                ),
            }
            match_rows.append(rec)
            if len(examples) < 40 and top["score"] >= 80:
                examples.append(rec)

    match_path = out_dir / "overlap_matches.csv"
    write_csv(
        match_path,
        match_rows,
        [
            "inventory",
            "substance",
            "cas",
            "use",
            "matched_nutrient_id",
            "pack",
            "score",
            "alt_matches",
        ],
    )

    # Unique nutrient_ids hit
    hit_ids = sorted({m["matched_nutrient_id"] for m in match_rows})
    a_hits = [i for i in hit_ids if any(n["nutrient_id"] == i and n["pack"] == "A" for n in nodes)]
    b_hits = [i for i in hit_ids if any(n["nutrient_id"] == i and n["pack"] == "B" for n in nodes)]

    md = []
    md.append("# FDA ingredients ↔ nutrient nodes overlap\n\n")
    md.append(f"Parsed from `{src.name}/` on clean export.\n\n")
    md.append("## Clean tables\n\n")
    for fname in files:
        p = out_dir / fname.replace(".csv", ".clean.csv")
        if p.exists():
            n = sum(1 for _ in p.open(encoding="utf-8")) - 1
            md.append(f"- `{p.name}` — **{n:,}** rows\n")
    md.append("\n## Match summary\n\n")
    md.append(f"- Total substance→node matches (score≥55): **{len(match_rows):,}**\n")
    md.append(f"- Unique nutrient_ids hit: **{len(hit_ids)}**\n")
    md.append(f"- Tier A hits: **{len(a_hits)}**\n")
    md.append(f"- Tier B hits: **{len(b_hits)}**\n")
    md.append(f"- Matches by inventory: `{dict(by_inventory)}`\n")
    md.append(f"- Matches by pack (top hit): `{dict(by_pack)}`\n\n")
    md.append("## High-confidence examples (score ≥ 80)\n\n")
    md.append("| Inventory | Substance | → nutrient_id | Pack | Score |\n")
    md.append("|-----------|-----------|---------------|------|------:|\n")
    for e in examples[:25]:
        sub = e["substance"].replace("|", "/")[:50]
        md.append(
            f"| {e['inventory']} | {sub} | `{e['matched_nutrient_id']}` | {e['pack']} | {e['score']} |\n"
        )
    md.append("\n## Tier A ids with ≥1 FDA match\n\n")
    md.append(", ".join(f"`{i}`" for i in a_hits) or "_none_\n")
    md.append("\n\n## Tier B ids with ≥1 FDA match\n\n")
    md.append(", ".join(f"`{i}`" for i in b_hits) or "_none_\n")
    md.append("\n\n## Notes\n\n")
    md.append(
        "- Matching is **name/token based**, not CAS-curated. Review before legal use.\n"
        "- FDA inventories are **partial** and **not** composition data.\n"
        "- FCN / Indirect are mostly packaging chemistry — fewer nutrient overlaps expected.\n"
        "- Full match list: `overlap_matches.csv`\n"
    )
    report = out_dir / "overlap_report.md"
    report.write_text("".join(md), encoding="utf-8")
    print(f"\nWrote {match_path.name} ({len(match_rows)} matches)")
    print(f"Wrote {report.name}")
    print(f"Unique nodes hit: {len(hit_ids)} (A={len(a_hits)}, B={len(b_hits)})")
    # Prefer strict synonym/phrase matcher for the published report
    try:
        from overlap_strict import run as strict_run
        print("\nRe-running strict synonym/phrase overlap…")
        strict_run(out_dir, args.nodes_root)
    except Exception as e:
        print(f"strict overlap skipped: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
