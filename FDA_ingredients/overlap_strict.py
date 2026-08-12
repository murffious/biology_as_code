#!/usr/bin/env python3
"""Strict FDA substance → nutrient_id matching. Run after clean/*.clean.csv exist."""
from __future__ import annotations
import csv, re
from collections import defaultdict
from pathlib import Path

SYNONYMS = {
    "ascorbic acid": "vitamin_c", "l-ascorbic acid": "vitamin_c",
    "thiamin": "vitamin_b1", "thiamine": "vitamin_b1", "riboflavin": "vitamin_b2",
    "niacin": "vitamin_b3", "nicotinic acid": "vitamin_b3", "nicotinamide": "vitamin_b3",
    "pantothenic acid": "vitamin_b5", "pyridoxine": "vitamin_b6", "biotin": "vitamin_b7",
    "folic acid": "folate", "folate": "folate", "cyanocobalamin": "vitamin_b12", "cobalamin": "vitamin_b12",
    "cholecalciferol": "vitamin_d", "ergocalciferol": "vitamin_d",
    "vitamin d": "vitamin_d", "vitamin d2": "vitamin_d", "vitamin d3": "vitamin_d",
    "alpha-tocopherol": "vitamin_e", "phylloquinone": "vitamin_k", "menaquinone": "vitamin_k",
    "retinol": "vitamin_a", "beta-carotene": "vitamin_a", "beta carotene": "vitamin_a",
    "choline chloride": "choline", "choline bitartrate": "choline", "choline": "choline",
    "l-carnitine": "carnitine", "carnitine": "carnitine", "taurine": "taurine",
    "creatine monohydrate": "creatine", "creatine": "creatine", "caffeine": "caffeine",
    "curcumin": "curcumin", "resveratrol": "resveratrol", "quercetin": "quercetin",
    "lutein": "lutein_zeaxanthin", "zeaxanthin": "lutein_zeaxanthin", "lycopene": "lycopene",
    "soy isoflavone": "isoflavones", "isoflavones": "isoflavones", "isoflavone": "isoflavones",
    "genistein": "genistein", "daidzein": "daidzein",
    "plant sterols": "phytosterols_total", "plant sterol": "phytosterols_total",
    "phytosterol": "phytosterols_total", "beta-sitosterol": "beta_sitosterol", "sitosterol": "beta_sitosterol",
    "fructo-oligosaccharide": "inulin_fos", "fructooligosaccharide": "inulin_fos", "inulin": "inulin_fos",
    "galacto-oligosaccharide": "gos", "galactooligosaccharide": "gos",
    "beta-glucan": "beta_glucan", "beta glucan": "beta_glucan", "psyllium": "psyllium_mucilage",
    "polyphenols": "total_polyphenols", "polyphenol": "total_polyphenols",
    "epigallocatechin gallate": "egcg", "epigallocatechin": "egcg",
    "anthocyanin": "anthocyanins", "proanthocyanidin": "proanthocyanidins",
    "chlorogenic acid": "chlorogenic_acid", "piperine": "piperine", "capsaicin": "capsaicinoids",
    "allicin": "allicin_organosulfur_garlic", "sulforaphane": "sulforaphane", "glucoraphanin": "sulforaphane",
    "coenzyme q10": "coq10", "ubiquinone": "coq10", "alpha-lipoic acid": "lipoic_acid", "lipoic acid": "lipoic_acid",
    "conjugated linoleic acid": "cla", "docosahexaenoic acid": "dha", "eicosapentaenoic acid": "epa",
    "alpha-linolenic acid": "ala", "linoleic acid": "linoleic_acid", "arachidonic acid": "arachidonic_acid",
    "lactoferrin": "lactoferrin", "phytic acid": "phytate", "oxalic acid": "oxalate",
    "pectin": "pectin", "zinc oxide": "zinc", "zinc sulfate": "zinc",
    "calcium carbonate": "calcium", "potassium iodide": "iodine", "selenomethionine": "selenium",
    "choline": "choline", "betaine anhydrous": "betaine", "trimethylglycine": "betaine", "betaine": "betaine",
}

def run(clean: Path, nodes_root: Path) -> None:
    nodes = []
    id_to_pack = {}
    for sub, pack in [("deep", "A"), ("deep-bioactives", "B")]:
        d = nodes_root / sub
        if not d.is_dir():
            continue
        for p in d.glob("*.yml"):
            nid = p.stem
            id_to_pack[nid] = pack
            text = p.read_text(encoding="utf-8", errors="replace")
            aliases = {nid.replace("_", " ")}
            m = re.search(r'^\s*name:\s*["\']?(.+?)["\']?\s*$', text, re.M)
            if m:
                aliases.add(m.group(1).strip().strip('"').strip("'").lower())
            nodes.append({"nutrient_id": nid, "pack": pack, "aliases": {a.lower() for a in aliases if len(a) >= 4}})

    syn = {k: v for k, v in SYNONYMS.items() if v in id_to_pack}
    alias_map = {}
    for n in nodes:
        for a in n["aliases"]:
            if len(a) >= 6:  # only long aliases
                alias_map.setdefault(a, set()).add(n["nutrient_id"])

    def match(name, other):
        blob = re.sub(r"\s+", " ", f"{name} {other}".lower()).strip()
        hits = {}
        for phrase in sorted(syn.keys(), key=len, reverse=True):
            if re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", blob):
                hits[syn[phrase]] = max(hits.get(syn[phrase], 0), 100)
                break
        for a, nids in alias_map.items():
            if re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", blob):
                for nid in nids:
                    hits[nid] = max(hits.get(nid, 0), 90 if len(a) >= 10 else 80)
        ranked = sorted(
            [{"nutrient_id": k, "score": v, "pack": id_to_pack[k]} for k, v in hits.items() if v >= 80],
            key=lambda x: (-x["score"], x["nutrient_id"]),
        )
        return ranked[:5]

    match_rows = []
    by_inv, by_pack = defaultdict(int), defaultdict(int)
    for inv, fname in {
        "food_substances": "FoodSubstances.clean.csv",
        "gras_notices": "GRASNotices.clean.csv",
        "fcn": "FCN.clean.csv",
        "indirect_additives": "IndirectAdditives.clean.csv",
    }.items():
        path = clean / fname
        if not path.exists():
            continue
        for r in csv.DictReader(path.open(encoding="utf-8")):
            name = r.get("_substance") or ""
            if len(name) < 3:
                continue
            # skip obvious packaging monomers unless GRAS/food
            hits = match(name, r.get("_other_names") or "")
            if not hits:
                continue
            top = hits[0]
            by_inv[inv] += 1
            by_pack[top["pack"]] += 1
            match_rows.append({
                "inventory": inv,
                "substance": name,
                "cas": r.get("_cas") or "",
                "use": (r.get("_use") or "")[:220],
                "matched_nutrient_id": top["nutrient_id"],
                "pack": top["pack"],
                "score": top["score"],
                "alt_matches": ";".join(f"{h['nutrient_id']}({h['score']})" for h in hits[1:4]),
            })

    fields = list(match_rows[0].keys()) if match_rows else [
        "inventory","substance","cas","use","matched_nutrient_id","pack","score","alt_matches"
    ]
    with (clean / "overlap_matches.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(match_rows)

    hit_ids = sorted({m["matched_nutrient_id"] for m in match_rows})
    a_hits = [i for i in hit_ids if id_to_pack.get(i) == "A"]
    b_hits = [i for i in hit_ids if id_to_pack.get(i) == "B"]
    high = [m for m in match_rows if m["score"] >= 100]
    seen = set()
    high_u = []
    for m in sorted(high, key=lambda x: x["substance"]):
        k = (m["inventory"], m["substance"].lower())
        if k in seen:
            continue
        seen.add(k)
        high_u.append(m)

    md = [
        "# FDA ingredients ↔ nutrient nodes overlap\n\n",
        "Strict whole-phrase / synonym matching (score ≥ 80). Not legal advice.\n\n",
        "## Match summary\n\n",
        f"- Matches: **{len(match_rows):,}**\n",
        f"- Unique nutrient_ids: **{len(hit_ids)}** (Tier A **{len(a_hits)}**, Tier B **{len(b_hits)}**)\n",
        f"- By inventory: `{dict(by_inv)}`\n",
        f"- By pack: `{dict(by_pack)}`\n\n",
        "## Synonym-level examples (score 100)\n\n",
        "| Inventory | Substance | → nutrient_id | Pack |\n",
        "|-----------|-----------|---------------|------|\n",
    ]
    for e in high_u[:35]:
        sub = e["substance"].replace("|", "/")[:55]
        md.append(f"| {e['inventory']} | {sub} | `{e['matched_nutrient_id']}` | {e['pack']} |\n")
    md.append("\n## Tier A ids hit\n\n" + ", ".join(f"`{i}`" for i in a_hits) + "\n")
    md.append("\n## Tier B ids hit\n\n" + ", ".join(f"`{i}`" for i in b_hits) + "\n")
    md.append("\nFull list: `overlap_matches.csv`\n")
    (clean / "overlap_report.md").write_text("".join(md), encoding="utf-8")
    print(f"strict matches={len(match_rows)} nodes={len(hit_ids)} A={len(a_hits)} B={len(b_hits)}")

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    run(here / "clean", here.parent / "nutrient-nodes")
