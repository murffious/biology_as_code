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

**Count:** 28 registry graphs · 28 mermaid packs · **0 missing · 0 orphan packs** (when export is up to date).

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
| Full amino-acid catabolism map (per AA) | **Partial** — urea + supporting, not every AA pathway graph |
| Photosynthesis / non-human pathways | **Out of scope** |
| Product meal score / Kibo-vars scorer | **Excluded** (patent pending) |

Goal: **every registry pathway graph has a mermaid pack** (met today).  
Stretch: add new **graphs in code first**, then re-run `export_pathway_packs.py` so docs never drift.

## Why `packs/` not next to each `.py` by same name

If both `beta_oxidation.py` and `beta_oxidation/` exist, Python imports the **directory** as a package and **shadows** the module.  
So diagrams live under `pathways/packs/<id>/` — same package tree, no import breakage.

## Regenerate after code changes

```bash
cd biology_as_code
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```
