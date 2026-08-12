# Pathway mermaid coverage vs Python code

**Last checked:** co-located under `src/biology_as_code/pathways/packs/`  
**Rule:** every **registry pathway graph** should have a `pathway.mermaid` pack.  
Not every **`.py` file** is a graph (some are mechanisms, regulation, loaders).

## Status: graphs ↔ packs

| Registry pathway name | Mermaid pack | Python module (source) |
|----------------------|--------------|-------------------------|
| glycolysis | `packs/glycolysis/` (+ `glycolysis_extra/` hand diagrams) | `metabolic_pathways.py` |
| tca_cycle | `packs/tca_cycle/` | `tca_cycle.py` |
| etc_oxphos | `packs/etc_oxphos/` | `etc_oxphos.py` |
| beta_oxidation | `packs/beta_oxidation/` | `beta_oxidation.py` |
| gluconeogenesis | `packs/gluconeogenesis/` | `gluconeogenesis.py` |
| urea_cycle | `packs/urea_cycle/` | `urea_cycle.py` |
| pentose_phosphate | `packs/pentose_phosphate/` | `pentose_phosphate.py` |
| glycogen_metabolism | `packs/glycogen_metabolism/` | `glycogen_metabolism.py` |
| fatty_acid_synthesis | `packs/fatty_acid_synthesis/` | `fatty_acid_synthesis.py` |
| ketogenesis | `packs/ketogenesis/` | `ketogenesis.py` |
| ketolysis | `packs/ketolysis/` | `ketolysis.py` |
| cholesterol_biosynthesis | `packs/cholesterol_biosynthesis/` | `cholesterol_pathway.py` |
| lipoprotein_transport | `packs/lipoprotein_transport/` | `cholesterol_pathway.py` |
| carb_digestion_absorption | `packs/carb_digestion_absorption/` | `digestion_absorption_pathways.py` |
| protein_digestion_absorption | `packs/protein_digestion_absorption/` | `digestion_absorption_pathways.py` |
| lipid_digestion_absorption | `packs/lipid_digestion_absorption/` | `digestion_absorption_pathways.py` |
| brush_border_final_digestion | `packs/brush_border_final_digestion/` | `digestion_absorption_pathways.py` |
| enterohepatic_bile | `packs/enterohepatic_bile/` | `digestion_absorption_pathways.py` |
| bile_acid_synthesis | `packs/bile_acid_synthesis/` | `digestion_absorption_pathways.py` |
| cori_glucose_alanine | `packs/cori_glucose_alanine/` | `supporting_pathways.py` |
| redox_shuttles | `packs/redox_shuttles/` | `supporting_pathways.py` |
| fructose_galactose | `packs/fructose_galactose/` | `supporting_pathways.py` |
| secondary_bile_acids | `packs/secondary_bile_acids/` | `supporting_pathways.py` |
| prebiotic_probiotic | `packs/prebiotic_probiotic/` | `supporting_pathways.py` |
| fuel_selection_hierarchy | `packs/fuel_selection_hierarchy/` | `supporting_pathways.py` |
| ampk_network | `packs/ampk_network/` | `nutrient_sensing.py` |
| mtorc1_network | `packs/mtorc1_network/` | `nutrient_sensing.py` |
| srebp_network | `packs/srebp_network/` | `nutrient_sensing.py` |
| gut_incretin_network | `packs/gut_incretin_network/` | `nutrient_sensing.py` |
| aa_nitrogen_disposal | `packs/aa_nitrogen_disposal/` | `amino_acid_catabolism.py` |
| bcaa_catabolism | `packs/bcaa_catabolism/` | `amino_acid_catabolism.py` |
| phenylalanine_tyrosine_catabolism | `packs/phenylalanine_tyrosine_catabolism/` | `amino_acid_catabolism.py` |
| methionine_one_carbon | `packs/methionine_one_carbon/` | `amino_acid_catabolism.py` |
| glucogenic_ketogenic_aa | `packs/glucogenic_ketogenic_aa/` | `amino_acid_catabolism.py` |
| iron_absorption | `packs/iron_absorption/` | `meal_critical_pathways.py` |
| cobalamin_absorption | `packs/cobalamin_absorption/` | `meal_critical_pathways.py` |
| glucose_epithelial_transport | `packs/glucose_epithelial_transport/` | `meal_critical_pathways.py` |
| scfa_colonic_production | `packs/scfa_colonic_production/` | `meal_critical_pathways.py` |
| tryptophan_niacin | `packs/tryptophan_niacin/` | `micronutrient_cofactor_pathways.py` |
| carnitine_synthesis | `packs/carnitine_synthesis/` | `micronutrient_cofactor_pathways.py` |

**Count:** 40 registry graphs · 40 mermaid packs · **0 missing · 0 orphan packs** (when export is up to date).

The last two carry `requires_nutrient` on their edges — the micronutrient a step
cannot run without. They are the only graphs here that answer "which steps stop
if this person is short on B6" rather than "where does the carbon go".

Auto mermaid is generated **from live code graphs**, so topology matches the Python model for that export. Hand gold diagrams in `glycolysis_extra/` may be richer (styling, phases) than auto `pathway.mermaid`.

## Python modules that are *not* pathway graphs (no separate mermaid pack)

| Module | Why no pack folder |
|--------|--------------------|
| `registry.py` | Discovery / loader, not a process graph |
| `__init__.py` | Package exports |
| `metabolic_mechanisms.py` | Shared mechanism catalog (enzymes), not one pathway |
| `pathway_regulation.py` | Fed/fast **activity 0–1** rules, not a node/edge graph |

These are real and used by the engine; they are not “missing mermaids for textbook pathways.” If you want diagrams for regulation, that would be a **new** doc type (state machine / activity table), not a pathway pack.

## Textbook breadth (honest gap)

Classic textbook *chapters* often include more named processes than we model as graphs, for example:

| Common textbook process | In this package today |
|-------------------------|------------------------|
| Glycolysis, TCA, ETC, β-ox, GNG, PPP, glycogen, urea, FAS, ketogenesis | **Yes** (graph + mermaid) |
| Ketolysis | **Yes** |
| Digestion CHO/PRO/FAT, brush border, bile, enterohepatic | **Yes** |
| Cori / alanine, shuttles, fructose–galactose | **Yes** (supporting) |
| AMPK / mTOR / SREBP networks | **Yes** (nutrient_sensing) |
| Gut incretin / CCK–GLP-1–PYY mini-graph | **Yes** (`gut_incretin_network`) |
| AA nitrogen disposal hub (→ urea) | **Yes** (`aa_nitrogen_disposal`) |
| BCAA catabolism (Leu/Ile/Val, BCKDH/MSUD) | **Yes** (`bcaa_catabolism`) |
| Phe / Tyr catabolism (PKU) | **Yes** (`phenylalanine_tyrosine_catabolism`) |
| Met / SAM / one-carbon + Cys | **Yes** (`methionine_one_carbon`) |
| Glucogenic vs ketogenic AA map | **Yes** (classification graph, not a cascade) |
| Non-haem iron absorption (DMT1 / ferroportin / hepcidin) | **Yes** (`iron_absorption`) |
| B12 + intrinsic factor | **Yes** (`cobalamin_absorption`) |
| SGLT1 / GLUT2 epithelial glucose | **Yes** (`glucose_epithelial_transport`) |
| Colonic SCFA (acetate / propionate / butyrate) | **Yes** (`scfa_colonic_production`) |
| Remaining single-AA cascades (His, Trp full, Lys, Pro, Arg, Thr, …) | **Partial** — covered via classification map + nitrogen hub; expand only when clinically needed |
| Photosynthesis / non-human pathways | **Out of scope** |
| External product scoring | **Excluded** (patent pending) |

Goal: **every registry pathway graph has a mermaid pack** (met today).  
Stretch: add new **graphs in code first**, then re-run `export_pathway_packs.py` so docs never drift.

## Why `packs/` not next to each `.py` by same name

If both `beta_oxidation.py` and `beta_oxidation/` exist, Python imports the **directory** as a package and **shadows** the module.  
So diagrams live under `pathways/packs/<id>/` — same package tree, no import breakage.

## Regenerate after code changes

```bash
cd biology_as_code
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 scripts/check_pathway_integration.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```

**Changelog:** package-level history of graph counts, mermaid pack churn, and
source/reference line changes is under repo root
[`CHANGELOG.md`](../../../../CHANGELOG.md) → *Pathway graphs, mermaid packs &
sources* (Unreleased). Update that section when INDEX totals or mechanism wire-ups
change numbers reviewers will notice.

**Contributor template:** [`docs/python/ADD_PATHWAY.md`](../../../../docs/python/ADD_PATHWAY.md)  
(checklist, module stub, PR template under `.github/PULL_REQUEST_TEMPLATE/pathway.md`).
