# Bioactive peptides — provenance home (not “just another bioactive”)

**Problem:** `collagen` was carrying hydrolysate claims as a generic bioactive; `postbiotic` was swallowing bacteriocins. Lycopene is *in* the tomato; most bioactive peptides are **generated** — so provenance is the class, not only chemistry.

---

## Three tiers by origin

| Tier | Provenance | Attachment | Scoreable on food node? | Examples |
|------|------------|------------|-------------------------|----------|
| **1 Intrinsic** | present as eaten | `food_node` | Yes | carnosine, anserine, glutathione, lunasin; lycopene (compound) |
| **2 Process-generated** | fermentation / industrial hydrolysis **before** eating | `process_node` | Yes, but score **process**, not species | VPP/IPP, collagen hydrolysate, soy peptides in natto/miso, bacteriocins |
| **3 Digestion-generated** | formed in gut | `host_food_edge` | **No** — category error | casomorphins, gluten exorphins, most “dietary ACE peptides”; **same shape as urolithin A** |

Tier 3 = interaction of food substrate × host proteases × microbiome (conversion rate varies, like ~40% urolithin converters).

---

## Bioavailability filter (peptides)

Most peptides → free amino acids → **count as protein**.  
Serum survivors tend to be **proline-rich** (Pro-Hyp, VPP/IPP).  

Schema field: `proline_rich_gate: true|false` — **plausibility gate**, not proof of endpoint.

---

## Evidence grades (this catalog)

| Claim | Grade | Note |
|-------|-------|------|
| VPP/IPP → BP | **B** | ~3/1 mmHg meta; high heterogeneity (JP > EU) |
| Collagen peptides → skin/tendon | **C** | Pro-Hyp in serum; small/industry trials |
| Dietary carnosine → performance | **C** | A-grade is beta-alanine → muscle carnosine |
| A1/A2 · BCM-7 | **D** | Contested / marketing-driven |
| Lunasin | **C** | Mostly in vitro |

---

## Schema patch applied

1. **`kind: peptide`** (plus protein / postbiotic / metabolite…)  
2. **`provenance`** enum: `intrinsic | process_generated | digestion_generated`  
3. **`attachment`**: `food_node | process_node | host_food_edge`  
4. **Split `collagen`** → `collagen_peptide` (process) + `collagen_protein` (intrinsic structural)  
5. **Add** carnosine, anserine, VPP/IPP, casomorphin, bacteriocin, …  
6. **Narrow `postbiotic`** to organic-acid style metabolites; bacteriocins get own id  
7. **urolithin** marked digestion_generated / host_food_edge  

**Files**

| Path | Role |
|------|------|
| `BioactiveCompound.schema.json` | Compound shape |
| `bioactive-peptides.catalog.json` | Peptide / split SSOT |
| `food_health_claims_500.json` | `bioactive_taxonomy` updated (`meta.bioactive_schema_rev: peptide_provenance_v1`); trailing FDA scrap stripped; 5 food refs `collagen`→`collagen_peptide` |

---

## Meat / fish wiring (todo)

Carnosine (and anserine on poultry/fish) should appear on **food nodes**, not only taxonomy. Catalog lists target foods; full 500-food rebuild can attach them in a later pass.

---

## Rule of thumb

> If it isn’t in the food until the eater’s gut (or a fermenter) makes it, **don’t put the claim on the species node alone.**
