# FDA ingredients inventories

Local downloads from FDA FDCC inventories (2026-08-02).

## Raw files

| File | Inventory |
|------|-----------|
| `FoodSubstances.csv` | Substances Added to Food (ex-EAFUS) |
| `GRASNotices.csv` | GRAS Notices |
| `FCN.csv` | Food Contact Substance Notifications |
| `IndirectAdditives.csv` | Indirect additives (21 CFR contact list) |

## Clean + overlap

```bash
python3 parse_fda_ingredients.py --nodes-root ../nutrient-nodes
```

Outputs in `clean/`:

| File | Purpose |
|------|---------|
| `*.clean.csv` | Preamble stripped; `_substance`, `_cas`, `_use` helpers |
| `overlap_matches.csv` | Name matches → Tier A/B `nutrient_id` |
| `overlap_report.md` | Human summary |

**Note:** Overlap is **name-based** (synonyms + whole phrases), not curated CAS legal mapping. Review before product/regulatory use.

## Relation to nutrient nodes

- **Tier A/B** = biology / composition / bioactives model  
- **FDA_ingredients** = US inventory of food & food-contact substances  

Use GRAS + FoodSubstances for novel bioactive / additive framing; FCN/Indirect for packaging chemistry.
