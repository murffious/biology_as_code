#!/usr/bin/env python3
"""Classify list.topics.md → topics_ontology.json (self-contained)."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

BOOK = Path(__file__).resolve().parents[2]
SRC = BOOK / "biology_as_code_nutrition_intelligence-main" / "list.topics.md"
OUT = (Path(__file__).resolve().parents[2] / "src" / "biology_as_code" / "engine" / "data" / "topics_ontology.json")

# Module-level rules — importable by tests without running main()
LAW_LINK_RULES: list[tuple[str, list[str]]] = [
    (r"ascorbic|vitamin c", ["LAW-004", "LAW-012"]),
    (r"\biron\b|ferritin|transferrin|hepcidin|haemochromat", ["LAW-004", "LAW-011", "LAW-041", "LAW-042"]),
    (r"\bzinc\b", ["LAW-003", "LAW-042"]),
    (r"phytate|phytic", ["LAW-002", "LAW-003"]),
    (r"tannin|tea\b|polyphenol", ["LAW-006"]),
    (r"fiber|fibre|pectin|resistant starch", ["LAW-001", "LAW-024", "LAW-025", "LAW-026"]),
    (r"micelle|bile salt|colipase|pancreatic lipase|fat.?soluble", ["L-FAT-1", "LAW-016", "LAW-020"]),
    (r"chylomicron|lipoprotein|ldl|hdl|vldl|fatty acid", ["LAW-022", "LAW-045", "LAW-046"]),
    (r"scfa|butyrate|propionate|acetate|fermentation|colon", ["LAW-025", "LAW-026"]),
    (r"insulin|glucagon|appetite|leptin|ghrelin|satiety", ["LAW-018", "LAW-032"]),
    (r"cortisol|glucocorticoid", ["LAW-034"]),
    (r"cholesterol|hmg-coa", ["LAW-021"]),
    (r"bile acid|enterohepatic", ["LAW-039", "LAW-017"]),
    (r"protein requirement|amino acid score|n-end", ["LAW-015", "LAW-038"]),
    (r"bmi|body mass", ["LAW-040"]),
    (r"waist|whr|android", ["LAW-029"]),
    (r"thiamin|vitamin b1", ["LAW-036"]),
    (r"vitamin e|tocopherol|pufa", ["LAW-035"]),
    (r"tryptophan|serotonin|niacin", ["LAW-027", "LAW-037"]),
    (r"intrinsic factor|cobalamin|b12", ["LAW-043"]),
    (r"sglt|glut5|glucose transporter", ["LAW-044"]),
    (r"pepsin|gastric acid|stomach ph|hcl", ["STUB-A-03"]),
    (r"oxalate", ["LAW-007"]),
    (r"lpl|hormone-sensitive lipase|lipolysis", ["LAW-030", "LAW-031"]),
    (r"caroten|beta-carotene|provitamin a|retinol", ["LAW-020", "L-FAT-1"]),
    (r"mthfr|folate|folic|methylation", ["STUB-B-02", "LAW-027"]),
    (r"energy density", ["LAW-019"]),
    (r"copper", ["LAW-041"]),
    (r"calcium", ["LAW-042", "LAW-047"]),
    (r"portal.?vein|lymph.?partition|lacteal", ["LAW-046", "LAW-045"]),
    (r"scurvy", ["STUB-S-01"]),
    (r"rickets|osteomalacia|vitamin d", ["STUB-S-02"]),
]

# Promoted stubs that must never appear as active law_links
PROMOTED_STUBS_RETIRED = frozenset(
    {"STUB-A-01", "STUB-A-02", "STUB-A-06", "STUB-T-01", "STUB-T-02"}
)


def laws_for_topic_label(label: str) -> list[str]:
    """Return ordered law ids linked to a topic label (classifier pure function)."""
    low = label.lower()
    laws: list[str] = []
    for pat, lids in LAW_LINK_RULES:
        if re.search(pat, low, re.IGNORECASE):
            for lid in lids:
                if lid not in laws:
                    laws.append(lid)
    return laws


def main() -> int:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    master = None
    for b in blocks:
        if '"categories"' in b and "energy_and_metabolism" in b:
            try:
                master = json.loads(b)
                break
            except json.JSONDecodeError:
                pass
    cat_terms: dict[str, list[str]] = {}
    if master and "categories" in master:
        for cat, body in master["categories"].items():
            if isinstance(body, dict):
                if "terms" in body:
                    cat_terms[cat] = list(body["terms"])
                else:
                    for sub, terms in body.items():
                        if sub != "description" and isinstance(terms, list):
                            cat_terms[f"{cat}.{sub}"] = list(terms)
            elif isinstance(body, list):
                cat_terms[cat] = body
    first_section = re.search(r"\n### |\n```", text)
    flat_chunk = text[: first_section.start()] if first_section else text
    flat_terms = []
    for line in flat_chunk.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "{", "`")):
            continue
        if len(line) > 120:
            continue
        if line.startswith(("-", "*")):
            line = line.lstrip("-* ").strip()
        flat_terms.append(line)
    extra = []
    for m in re.finditer(r"^[A-Z](?: —[^\n]*)?\n(.+)$", text, re.MULTILINE):
        chunk = m.group(1)
        if ";" in chunk and len(chunk) > 40:
            for part in chunk.split(";"):
                part = part.strip().rstrip(".")
                if 2 < len(part) < 100:
                    extra.append(part)

    def norm_label(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().strip('"').strip("'"))

    def slug(s: str) -> str:
        s = s.lower().replace("α", "alpha").replace("β", "beta").replace("γ", "gamma")
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_")[:80]

    all_labels = set()
    for t in flat_terms + extra:
        all_labels.add(norm_label(t))
    for terms in cat_terms.values():
        for t in terms:
            all_labels.add(norm_label(t))
    label_cats = defaultdict(set)
    for cat, terms in cat_terms.items():
        for t in terms:
            label_cats[norm_label(t)].add(cat)

    KIND_PATTERNS = [
        ("nutrient_vitamin", r"\bvitamin\b|thiamin|riboflavin|niacin|cobalamin|ascorbic|retinol|tocopherol|folate|folic|biotin|pyridox|pantothen|cholecalciferol|phylloquinone|menaquinone|caroten|beta-carotene|provitamin"),
        ("nutrient_mineral", r"\b(iron|zinc|calcium|magnesium|selenium|iodine|copper|sodium|potassium|phosphorus|manganese|molybdenum|chromium|fluoride|chloride|boron)\b"),
        ("nutrient_aa", r"\b(amino acid|leucine|lysine|methionine|tryptophan|phenylalanine|valine|isoleucine|threonine|histidine|arginine|glutamine|alanine|glycine|tyrosine|serine|cysteine|proline)\b"),
        ("nutrient_fa", r"\b(fatty acid|linoleic|linolenic|oleic|epa|dha|saturated|polyunsaturated|triglyceride|triacylglycerol|cholesterol|phospholipid)\b"),
        ("nutrient_carb", r"\b(glucose|fructose|galactose|sucrose|lactose|starch|glycogen|maltose|carbohydrate|oligosaccharide)\b"),
        ("fiber", r"\b(fiber|fibre|pectin|cellulose|resistant starch|beta.glucan|nsp|non-starch)\b"),
        ("antinutrient", r"\b(phytate|phytic|tannin|oxalate|lectin|goitrogen|avidin|trypsin inhibitor)\b"),
        ("enzyme", r"\b(ase\b|amylase|lipase|pepsin|trypsin|transketolase|dehydrogenase|kinase|synthase|hydroxylase|transferase|phosphatase)\b"),
        ("hormone_signal", r"\b(insulin|glucagon|cortisol|leptin|ghrelin|cck|gastrin|secretin|thyroid|adrenaline|epinephrine|serotonin|glp-1|peptide yy|somatostatin|motilin|acth|aldosterone|androgen|estrogen)\b"),
        ("transporter", r"\b(transporter|dmt1|sglt|glut|ferroportin|npc1l1|channel|receptor|carrier)\b"),
        ("organ_tissue", r"\b(liver|stomach|colon|intestine|pancreas|adipose|muscle|brain|kidney|bone|enterocyte|hepatocyte|thyroid|adrenal|gallbladder)\b"),
        ("process", r"\b(glycolysis|gluconeogenesis|oxidation|ketogenesis|lipolysis|lipogenesis|fermentation|digestion|absorption|methylation|phosphorylation|anabolism|catabolism|thermogenesis|emptying|motility)\b"),
        ("disease_outcome", r"\b(disease|deficiency|anemia|anaemia|diabetes|scurvy|rickets|beriberi|pellagra|goiter|goitre|obesity|cancer|atherosclerosis|kwashiorkor|marasmus|osteoporosis|osteomalacia|hypertension|syndrome|failure|cirrhosis)\b"),
        ("biomarker_method", r"\b(bmi|skinfold|calorimetry|assay|rda|dri|drv|recall|survey|measurement|index|score|panel|equation|harris.benedict|schofield)\b"),
        ("food", r"\b(milk|meat|fish|grain|wheat|rice|soy|egg|vegetable|fruit|oil|butter|coffee|tea|alcohol|beer|wine|bread|legume)\b"),
        ("population", r"\b(infant|child|pregnan|lactat|elderly|athlete|adolesc|adult|women|men\b)\b"),
        ("drug_toxin", r"\b(toxin|mycotoxin|aflatoxin|alcohol|caffeine|orlistat|antibiotic|cocaine|arsenic|cadmium|lead|mercury)\b"),
    ]
    SIM_ROLE = {
        "nutrient_vitamin": "cargo", "nutrient_mineral": "cargo", "nutrient_aa": "cargo",
        "nutrient_fa": "cargo", "nutrient_carb": "cargo", "fiber": "modifier", "antinutrient": "modifier",
        "enzyme": "mechanism", "hormone_signal": "signal", "transporter": "mechanism",
        "organ_tissue": "compartment", "process": "process", "disease_outcome": "endpoint",
        "biomarker_method": "measurement", "food": "payload_food", "population": "host_context",
        "drug_toxin": "modifier", "other": "lexicon",
    }
    SYSTEM_HINTS = {
        "nutrient_mineral": ["Assimilation", "Structure"], "nutrient_vitamin": ["Assimilation", "Energy", "Structure"],
        "nutrient_aa": ["Assimilation", "Structure"], "nutrient_fa": ["Assimilation", "Transport", "Energy"],
        "nutrient_carb": ["Assimilation", "Energy"], "fiber": ["Assimilation", "Energy"],
        "antinutrient": ["Assimilation"], "enzyme": ["Assimilation", "Biotransformation"],
        "hormone_signal": ["Communication", "Energy"], "transporter": ["Assimilation", "Transport"],
        "organ_tissue": ["Assimilation"], "process": ["Energy", "Biotransformation"],
        "disease_outcome": ["Structure", "Defense"], "biomarker_method": [], "food": ["Assimilation"],
        "population": ["Structure"], "drug_toxin": ["Biotransformation", "Defense"], "other": [],
    }
    CHAIN = {
        "payload_food": "L1", "cargo": "L2", "modifier": "L2", "mechanism": "L3", "process": "L3",
        "signal": "L4", "compartment": "L4", "endpoint": "L5", "measurement": None,
        "host_context": "L4", "lexicon": None,
    }
    def classify(label: str) -> dict:
        low = label.lower()
        kind = "other"
        for k, pat in KIND_PATTERNS:
            if re.search(pat, low, re.IGNORECASE):
                kind = k
                break
        role = SIM_ROLE[kind]
        systems = list(SYSTEM_HINTS.get(kind, []))
        if re.search(r"immune|inflammat|antioxid|allergy|infection", low):
            if "Defense" not in systems:
                systems.append("Defense")
        if re.search(r"liver|bile|detox|cytochrome", low):
            if "Biotransformation" not in systems:
                systems.append("Biotransformation")
        if re.search(r"brain|neuro|serotonin|cognition", low):
            if "Communication" not in systems:
                systems.append("Communication")
        laws = laws_for_topic_label(label)
        chain = CHAIN.get(role)
        if role == "cargo":
            rep = {"type": "state_cargo", "unit": "relative_or_mg", "field_hint": f"cargo.{slug(label)}"}
        elif role == "modifier":
            rep = {"type": "context_flag_or_factor", "field_hint": f"mod.{slug(label)}"}
        elif role == "signal":
            rep = {"type": "signal_0_2", "field_hint": f"signal.{slug(label)}"}
        elif role == "mechanism":
            rep = {"type": "phase_mechanism", "field_hint": f"mech.{slug(label)}"}
        elif role == "process":
            rep = {"type": "pathway_process", "field_hint": f"proc.{slug(label)}"}
        elif role == "compartment":
            rep = {"type": "geography_compartment", "field_hint": f"comp.{slug(label)}"}
        elif role == "endpoint":
            rep = {"type": "outcome_node", "field_hint": f"out.{slug(label)}", "claim_tier": "open"}
        elif role == "measurement":
            rep = {"type": "lexicon_measurement", "field_hint": f"meas.{slug(label)}"}
        elif role == "host_context":
            rep = {"type": "host_config", "field_hint": f"host.{slug(label)}"}
        elif role == "payload_food":
            rep = {"type": "food_payload", "field_hint": f"food.{slug(label)}"}
        else:
            rep = {"type": "lexicon_only", "field_hint": f"lex.{slug(label)}"}
        sim_ready = role in ("cargo", "modifier", "signal", "mechanism", "process", "compartment") and bool(systems)
        return {
            "id": f"topic.{slug(label)}",
            "label": label,
            "kind": kind,
            "sim_role": role,
            "systems": systems,
            "chain_layer": chain,
            "categories": sorted(label_cats.get(label, [])),
            "law_links": laws,
            "sim_repr": rep,
            "sim_ready": sim_ready,
            "status": "mapped" if laws else ("sim_stub" if sim_ready else "lexicon"),
        }

    topics = []
    seen = set()
    for lab in sorted(all_labels, key=lambda s: s.lower()):
        if len(lab) < 2 or lab.lower() in ("free", "low", "high", "reduced", "a band"):
            continue
        node = classify(lab)
        if node["id"] in seen:
            continue
        seen.add(node["id"])
        topics.append(node)
    by_role = defaultdict(int)
    by_status = defaultdict(int)
    by_sys = defaultdict(int)
    for t in topics:
        by_role[t["sim_role"]] += 1
        by_status[t["status"]] += 1
        for s in t["systems"]:
            by_sys[s] += 1
    doc = {
        "schema_version": "1.0.0",
        "title": "Encyclopedia topics → simulation ontology",
        "source": "biology_as_code_nutrition_intelligence-main/list.topics.md (frozen reference)",
        "count": len(topics),
        "counts_by_sim_role": dict(sorted(by_role.items(), key=lambda x: -x[1])),
        "counts_by_status": dict(by_status),
        "counts_by_system": dict(by_sys),
        "honesty": {
            "note": "Auto-classified vocabulary for sim representation. Not every term is a law.",
            "not": ["diagnose from topic list", "invent magnitudes", "C-number scores"],
        },
        "topics": topics,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} topics={len(topics)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
