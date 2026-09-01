# LAW-026 PMID filter (20 candidates → keep/drop)

**Law:** Fermentable carbohydrate reaching the colon is not calorie-free — SCFA energy recovery (+ bulk/gas).  
**Source pack:** `evidence_candidates_LAW026.json`  
**Filter date:** 2026-07-21  
**Rule:** Keep only papers that support **substrate → colonic fermentation → SCFA (and/or host energy salvage)**. Drop disease outcomes, methods-only, livestock production, and query false positives (“energy” ≠ colon harvest).

**Magnitude still unlocked.** Keepers are EV *stubs* for review — not automatic law lock.

---

## Keep (7) — draft EV stubs

| PMID | Year | Verdict | One-line reason |
|------|------|---------|-----------------|
| [38441170](https://pubmed.ncbi.nlm.nih.gov/38441170/) | 2024 | **KEEP** | Fiber (+ protein) co-fermentation **increases butyrate** — direct substrate→SCFA. |
| [10702589](https://pubmed.ncbi.nlm.nih.gov/10702589/) | 2000 | **KEEP** | Classic **in vitro fermentation** of dietary fiber digesta → SCFA (propionate emphasis). |
| [33995299](https://pubmed.ncbi.nlm.nih.gov/33995299/) | 2021 | **KEEP** | **RS source + microbiome** change butyrate yield — supports LAW-025/026 conditions. |
| [40484608](https://pubmed.ncbi.nlm.nih.gov/40484608/) | 2025 | **KEEP** | In vitro fermentation: starch form vs exogenous butyrate — fermentation metabolite path. |
| [36638279](https://pubmed.ncbi.nlm.nih.gov/36638279/) | 2023 | **KEEP (weak)** | Fiber/RS vs protected butyrate on GI **VFAs** + digestibility (animal; energy-adjacent). |
| [39748438](https://pubmed.ncbi.nlm.nih.gov/39748438/) | 2025 | **KEEP (weak)** | Fiber physico-chemistry → **fermentation + energy metabolism** (animal feed; mechanism useful). |
| [42357471](https://pubmed.ncbi.nlm.nih.gov/42357471/) | 2026 | **KEEP (borderline)** | Plant substrates profiled for **SCFA production** — substrate→metabolite mapping. |

### Draft EV stubs (keepers)

Use provisional IDs **EV-039…EV-045** until merged into `gleaned/registers/evidence.md`.

---

#### EV-039 — Dietary fiber co-fermentation increases butyrate (substrate → SCFA)

**Observation:** Certain dietary fibers combined with protein increase **butyrate** in gut microbiota fermentation models — SCFA yield depends on co-substrates, not fiber grams alone.  
**Source:** PMID 38441170 (2024). *Food & Function.* https://pubmed.ncbi.nlm.nih.gov/38441170/  
**Supports:** LAW-026 (fermentable cargo → SCFA); anti-lumping of “fiber: Y g”.  
**Does not support:** Locked kcal/g magnitude; disease prevention.  
**SSI (provisional):** 🟡 needs abstract/full read for design quality.  
**Engine:** Prefer `fermentable_fraction` + matrix context over total fiber_g in FLOW; do not lock UNITS from this alone.

---

#### EV-040 — In vitro fermentation of fiber-rich digesta produces SCFAs

**Observation:** Ileal digesta containing oat-bran fiber fermented with adapted cecal inocula produces SCFAs (study reports increased **propionate** under those conditions).  
**Source:** PMID 10702589 (2000). *J Nutr.* https://pubmed.ncbi.nlm.nih.gov/10702589/  
**Supports:** LAW-026 core mechanism — escaped fiber is fermented to absorbable SCFAs.  
**Does not support:** Human free-living energy balance magnitude; species is model system.  
**SSI (provisional):** 🟢 mechanism solid; 🟡 for human kcal claim.  
**Engine:** Colon fermentation node is not “zero energy out”; product vector = acetate/propionate/butyrate.

---

#### EV-041 — Resistant starch source and microbiome set butyrate yield

**Observation:** In vitro fermentation shows **butyrate production varies by RS source and microbiome composition**.  
**Source:** PMID 33995299 (2021). *Front Microbiol.* https://pubmed.ncbi.nlm.nih.gov/33995299/  
**Supports:** LAW-025 (RS type/prep) + LAW-026 **conditions** (fermentability is not universal).  
**Does not support:** Fixed FLOW coefficients (0.6, 2 kcal/g, etc.).  
**SSI (provisional):** 🟢 for conditionality; 🔴 for locking a single magnitude.  
**Engine:** `rs_profile` + `MicrobiomeProfile` are first-class; magnitude_locked stays false.

---

#### EV-042 — Starch form modulates fermentation metabolites (vs exogenous butyrate)

**Observation:** Butyrylated starch vs exogenous butyrate vs RS differ in microbiota/metabolite patterns during **in vitro fermentation**.  
**Source:** PMID 40484608 (2025). *Carbohydr Polym.* https://pubmed.ncbi.nlm.nih.gov/40484608/  
**Supports:** Form of fermentable starch changes SCFA/metabolite outcomes (matrix/form law family).  
**Does not support:** Cognitive/aging claims in sister paper; host energy kcal formula.  
**SSI (provisional):** 🟡.  
**Engine:** Payload form fields matter for colon stage; keep FLOW demos provisional.

---

#### EV-043 — Fiber/RS interventions change GI volatile fatty acids (animal)

**Observation:** Soluble corn fiber, resistant corn starch, and protected butyrate alter performance and gastrointestinal **VFAs** / digestibility in an animal model.  
**Source:** PMID 36638279 (2023). *J Anim Sci.* https://pubmed.ncbi.nlm.nih.gov/36638279/  
**Supports:** Fermentable fiber/RS → VFA/SCFA-class products in vivo GI tract (energy-carrier metabolites).  
**Does not support:** Direct human energy recovery bound; production-animal endpoints.  
**SSI (provisional):** 🟡 (species transfer).  
**Engine:** Ancillary support only; prefer human/in vitro human-inocula packs for lock.

---

#### EV-044 — Fiber physico-chemistry links to fermentation and energy utilization (feed)

**Observation:** Dietary fiber physicochemical properties relate to **fermentation characteristics** and effects on nutrient utilization / energy metabolism in feed science.  
**Source:** PMID 39748438 (2025). *J Anim Sci Biotechnol.* https://pubmed.ncbi.nlm.nih.gov/39748438/  
**Supports:** Fermentability is a property of fiber physics/chemistry → energy-relevant outcomes.  
**Does not support:** Human SCFA kcal/g table; obesity epidemiology.  
**SSI (provisional):** 🟡.  
**Engine:** Aligns with `FiberProperties` (viscosity, fermentability); not a magnitude source.

---

#### EV-045 — Plant substrates profiled for SCFA (and other metabolites)

**Observation:** Plant-based substrates can be evaluated by integrated profiling of **SCFAs** (and other compounds) as fermentation/metabolite outputs.  
**Source:** PMID 42357471 (2026). *Molecules.* https://pubmed.ncbi.nlm.nih.gov/42357471/  
**Supports:** Substrate → SCFA as a measurable evaluation axis.  
**Does not support:** Neuroactive/disease claims without separate EV; energy yield lock.  
**SSI (provisional):** 🟡 title-level; read full text before promotion.  
**Engine:** Optional catalog support for colonic medium substrate types.

---

## Drop (13) — one-line reasons

| PMID | Year | Drop reason |
|------|------|-------------|
| 42366393 | 2026 | **Disease axis** (ALL/leukemia) — not energy-recovery law. |
| 42280405 | 2026 | Lever is **polyphenol supplementation**, not fermentable fiber energy. |
| 42065568 | 2026 | **Constipation / motility** symptom model — wrong claim tier. |
| 41946979 | 2026 | **Catfish growth** / production animal — not human colon energy. |
| 42041444 | 2026 | **Assay/method** (electrochemical SCFA profiling) — no law mechanism. |
| 42104939 | 2026 | **Cognition / aging** outcome — disease/brain claim, not LAW-026 energy. |
| 39909254 | 2025 | **Atopic dermatitis** — disease; keep out of energy law pack. |
| 40817467 | 2025 | **Bacterial stress response** in Bacteroides — microbe physiology, not host salvage. |
| 42163967 | 2026 | **Blood pressure** control — clinical outcome, wrong kingdom. |
| 42008882 | 2026 | **Beef muscle** energy metabolism / resveratrol — not colon fermentation. |
| 41439104 | 2025 | **Grocery purchase** patterns (Nunavut) — epidemiology of shopping. |
| 41293580 | 2025 | **Obesity panel** energy intake + fiber — population ecology, not SCFA path. |
| 41006931 | 2025 | **Skeletal muscle** fiber types / injury — false positive on “fiber/energy”. |

---

## Summary counts

| | n |
|--|---|
| Input candidates | 20 |
| **KEEP** | **7** (4 primary + 3 weak/borderline) |
| **DROP** | **13** |
| Magnitude lock? | **No** |
| Ready for LAW-SPEC promote? | **No** — stubs only |

### Primary keepers for next EV merge (priority order)
1. **38441170** (EV-039)  
2. **10702589** (EV-040)  
3. **33995299** (EV-041)  
4. **40484608** (EV-042)  

Weak/ancillary: 36638279, 39748438, 42357471.

### Still missing for a strong LAW-026 pack
Classic human energy-recovery citations often used in textbooks (e.g. SCFA contribution to daily energy, Atwater-style fiber factors) may **not** be in this auto-harvest. Consider a **targeted local search** or online fallback for:
- “short-chain fatty acids energy contribution human”
- “Atwater factor dietary fiber”
- Cummings / Macfarlane-type reviews on SCFA absorption and energy

---

## Next actions
1. Full-text/abstract read of EV-039–041 (priority).  
2. Append EV-039+ to `gleaned/registers/evidence.md` when SSI reviewed.  
3. Link PMIDs on `colon.fermentation` base unit `sources[]`.  
4. Keep FLOW SCFA kcal; keep `magnitude_locked: false` until a dedicated energy-yield paper is attached.
---

*Copyright 2026 Paul Murff and Biology as Code contributors (Morf Engineering Inc.). Licensed under Apache-2.0 — see repository `LICENSE` and `NOTICE`.*
