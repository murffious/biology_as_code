# From competing taxonomies to Biology as Code

**Ideas paper** · 19 August 2026 · not a deposit · not a claim  
Working line (keep this): *a narrative review mapping the competing taxonomies and the mechanistic evidence linking processing to metabolic outcomes.*

The next paper is not another UPF review. It is the compiler: take that mapping and type it so a processing event becomes a Biology as Code object — a transformation with a host path — instead of a slogan.

---

## 1. What the working line actually licenses

Two objects, not one.

1. **Taxonomies** are incompatible measurement instruments. They do not measure “processing.” Each measures a different construct (purpose, matrix, palatability, place of preparation, convenience). Pooling them is measurement error.
2. **Mechanistic evidence linking processing to metabolic outcomes** is the Biology as Code layer. It is not a taxonomy. It is what a transformation does to a host: eating rate, ileal-brake hormones, postprandial flux, hepatic DNL, microbiome, circulating metabolome.

NOVA is the loudest instrument. It is not the biology.

The v2 synthesis already holds this line and is correctly narrower than the field’s rhetoric: two small crossovers (Hall 2019; Dicken 2025) support a causal contribution of processing to *energy intake* independent of nutrient composition; downstream disease claims stay observational and low-certainty; CHIPS is preprint. Keep that fail-closed voice. Do not let the Bac paper “upgrade” Hall into CVD.

---

## 2. What you already have (do not rewrite)

| Artifact | Role |
|---|---|
| Zenodo v2 — *Ultra-Processed Food Literature Synthesis* | Public narrative. Six instruments: NOVA, Siga, HPF, UNC, EPIC-Soft/GloboDiet, CHIPS. Mechanisms graded. |
| `research_/examples/upf.md` | Schema-ready atlas. Broader than v2: adds IFIC, IFPRI, Mexican NIPH, Nova+HFSS, USDA/IFT, AND “heavily processed.” This is the right seed for Bac. |
| Biology as Code toolkit (zenodo.21536449) | Digestion state machines, LAW-SPEC cards, pathway graphs, fail-closed provenance. |
| Evidence Hub / EDP-1 | Study cards that refuse to pool mismatched exposures. |

The gap: v2 *describes* the taxonomies. Bac has *organs and laws*. Nothing yet joins “this food was extruded + emulsified” to “this host path fired.” That join is the next paper.

---

## 3. Taxonomies besides NOVA

They are not rival labels for the same thing. They are projections of different axes. A grocery cart can be 10% or 47% “highly/ultra-processed” on the same Portuguese food list (de Araújo 2022: NOVA 10.2%, IARC-EPIC 47.4%).

### 3.1 The six already in v2

| System | What it actually measures | Top bin | Status |
|---|---|---|---|
| **NOVA** (Monteiro 2009–2019) | Purpose of industrial formulation + cosmetic additives + little intact food | Ultra-processed | Dominant; group 4 is heterogeneous |
| **Siga** (Fardet 2018) | Matrix integrity + Markers of Ultra-Processing (MUPs); extrusion/puffing count even without additives | Red / ultra | Closest to Bac; low uptake |
| **HPF** (Fazzino 2019) | Three nutrient-pair thresholds (fat+Na, fat+sugar, carb+Na) | Hyper-palatable | Not a processing taxonomy at all |
| **UNC / Poti** (2015) | Alteration of natural form + convenience | Highly processed | NOVA variant; rice stays “less processed” |
| **EPIC-Soft / GloboDiet** (Slimani 2009) | 24-h recall facet: place + preparation | Highly processed (post-hoc) | Instrument, not a taxonomy; cheese ~100% “highly” |
| **CHIPS** (2025 preprint) | Processing + health-evidence + “intuition” | Splits yogurt/bread from soda | **Not peer reviewed. Do not treat as established.** |

### 3.2 The ones v2 omitted and should not

These are in `upf.md` and in Medin et al. 2025 (*Food Nutr Res* 69:12217) and the UK SACN 2023 eight-system scan.

| System | Origin | Bins | What “worst” means | Why it matters |
|---|---|---|---|---|
| **IFIC** | Eicher-Miller 2012 | 5 | Ready-to-eat convenience | Measures convenience/preservation, not formulation. Fortified cereal and “healthy” packaged food land in the top bin. Industry-adjacent; do not ignore it — it is how many US comms pieces talk. |
| **IFPRI** | Asfaw 2011 (Guatemala) | 3 | Highly processed | Degree of processing in an LMIC *purchase* survey. Street food vs packaged. Not transferable to NHANES. |
| **UP3** | UnProcessed Pantry Project | mixed | Unprocessed pantry vs not | Program taxonomy, not an epi instrument. Nutritional quality is in-scope. |
| **Mexican NIPH** | Moubarac review 2014 | mixed | Industrialized / modern vs traditional | Catches nixtamal vs industrial bread. Local structure, not cosmetic additives. |
| **Nova + HFSS** | Popkin 2024 | hybrid | Ultra *and* high fat/salt/sugar | Admits the two axes are not the same. The policy-useful hybrid. |
| **USDA / IFT “processed”** | legal / tech | binary-ish | Any alteration of a commodity | Almost everything in a store. Useless as a health exposure. The word the public hears. |
| **AND “heavily processed”** | practice guidance | informal | Many added ingredients | Consumer language. Overlaps NOVA 3 and 4. |
| **IAFNS Food Classification WG** | 2023–2026 principles | not a scale | Science-based processing *and* formulation | Industry-science forum trying to write rules so a future FDA definition is not just NOVA. Watch it; do not adopt it as truth. |

**Rule for Bac:** `classification.system` is a required field. If OPEN, the card cannot enter a pooled pane. Two papers pool only if they share system + metric + contrast.

**Rule for language:** “ultra,” “highly,” and “hyper” are not synonyms.

- *Ultra* = NOVA-4 (purpose + cosmetic additives).
- *Highly* = IARC/IFPRI/UNC top bin (place/intensity; includes pasteurized milk, many cheeses).
- *Hyper* = HPF / reward (formulation of fat+carb+salt). Not a processing step count.

### 3.3 The construct that none of them are

None of these systems is a typed list of **unit operations** (milling, extrusion, hydrogenation, homogenization, reconstitution, cosmetic-additive addition, packaging). Siga comes closest. That typed list is what Biology as Code can own.

---

## 4. The Bac move: one object, many projections

Do not pick a winner among taxonomies. Compile them.

```
PROCESSING_EVENT
  purpose          // NOVA’s question
  unit_operations  // what was actually done
  matrix_state     // Siga’s question (intact | fractured | reconstituted)
  additive_set     // emulsifiers, colours, NNS, hydrolysates…
  nutrient_package // HFSS / composition axis
  palatability     // HPF clusters
  place            // EPIC / IFPRI (kitchen vs plant vs street)
  convenience      // IFIC
```

Each existing taxonomy is a *lossy projection* of this object. That is why they disagree, and why a reformulation that deletes the NOVA marker additives but keeps extrusion will “leave group 4” without changing the host path.

This is the same compile law already in `HYPOTHESIS.md`: the food system compiles every health directive down to its instruction set, and the instruction set has only ever contained analytes. Any FDA UPF definition that is a checklist of marker additives will be formulated around in one product cycle. A Bac `PROCESSING_EVENT` that carries `matrix_state` and `unit_operations` is the definition that cannot be compiled around without changing the biology.

---

## 5. Mechanistic evidence linking processing to metabolic outcomes

Keep the v2 gradient. Promote nothing.

### 5.1 What is earned (human, causal, small)

| Claim | Source | Bound |
|---|---|---|
| Ad libitum UPF diet raises energy intake vs nutrient-matched unprocessed | Hall 2019, NIH ward, n=20, 2-wk crossover | +508 ± 106 kcal/d; +0.9 kg vs −0.9 kg |
| Eating rate is higher on the UPF arm | Same trial (and secondary reports) | ~17 kcal/min faster |
| Free-living, both diets meeting national guidance, processing still moves weight | Dicken 2025 UPDATE, n=55, 8-wk | Extra ~1 kg loss on minimally processed; magnitude *contested* in *Nature Medicine* correspondence |
| Direction replicates free-living | Hamano 2024 | +814 kcal/d, +1.1 kg, fewer chews/kcal |

This is the only place the word *cause* is earned, and the endpoint is energy intake / short-term weight, not heart attacks.

### 5.2 What is a coherent host path, not yet end-to-end in humans

This is the Biology as Code map. Each row is a candidate LAW, not a finding.

| Step | Physiology (book / organ) | Processing does | Evidence grade |
|---|---|---|---|
| Oral | Barrett, ch. mastication / cephalic phase | Soft matrix → fewer chews → shorter oro-sensory exposure | Strong in Hall; kinematics measurable |
| Gastric | Barrett, emptying | Low viscosity, small particles → faster emptying | Physiology textbook-grade; few UPF trials measure it |
| Ileal brake | Barrett, distal gut L-cells | Proximal absorption → less GLP-1 / PYY | **Leading hypothesis. Not shown end-to-end on matched UPF vs unprocessed diets.** |
| Hepatic flux | Gass & Kaplan; Griffiths metabolome | Nutrient flood → insulin pulse, ChREBP/SREBP-1c, DNL | Biochemistry textbook-grade; UPF-specific human flux data thin |
| Microbiome | SCFA, mucus, emulsifiers | CMC / P80 (mice); CMC human feeding (Chassaing 2022) | Animal strong; human small and heterogeneous |
| Reward | HPF clusters; GLP-1R in central amygdala (Godschall 2026, mice) | Fat+carb+salt combinations | Mechanism plausible; “addiction” is a surface claim |
| Circulating metabolome | Griffiths; MetaboAnalyst / XCMS stack | Poly-metabolite score of % energy from UPF | New measurement layer (see §6) |

Wang / Chen / Xu 2026 (*Front. Nutr.* 13:1737280) tell the same cascade as “nutrient flood → organelle stress” and are useful as a map, not as a citation for causality. Their own abstract says the framework remains a conceptual proposition. Your v2 is stricter and should stay the public voice.

### 5.3 What is telemetry, not law

Lane 2024 umbrella (~9.9M, NOVA): consistent direction across many outcomes; GRADE mostly low / very low; four of 45 analyses moderate. File as observational association under a NOVA instrument. Do not let a news card sit on the clinical node as if it were Hall.

Toxicology (AGEs, micro/nanoplastics): keep v2’s open-question posture. Nihart 2025 measured no diet.

---

## 6. Metabolomics is the missing instrument, not another taxonomy

The metabolomics note you pasted is the **assay stack** for the host path. It does not classify food. It reads what the host did with the food.

That is the transition: taxonomies name the exposure; metabolomics names the intermediate.

### 6.1 Why this matters now

Abar / Loftfield 2025 (*PLOS Medicine*; NCI DCEG write-up 20 May 2025): blood and urine poly-metabolite scores, trained on IDATA (n=718) and **tested inside Hall’s own 20-person feeding trial**, distinguish 80% UPF energy from 0% UPF energy. That is the first objective exposure measure that is not an FFQ recode.

2025–2026 follow-ons (treat as association unless they inherit a feeding design):

- UPF metabolomic pattern ↔ CRC (Du 2025)
- UPF-related metabolites ↔ CRP ↑, IGF-1 ↓, SHBG ↓ (Kityo 2025)
- Targeted European-cohort signature of lipid-oxidation / membrane lipids (news syntheses mid-2026; cite the primary when you have the PDF)

**Fail-closed:** a plasma signature associated with self-reported NOVA intake is still downstream of the taxonomy problem, unless it was validated on a controlled diet (Hall / Abar). Do not replace “NOVA Q4” with “UPF metabolome score” and call the construct solved.

### 6.2 The tool stack, mapped onto Bac

Use this as the methods appendix of the Bac paper, not as the argument.

| Stage | Tools | Bac job |
|---|---|---|
| Raw → features | ProteoWizard → **MS-DIAL** or **XCMS/Asari**; MZmine for MS²-rich discovery | Feature table with parameters declared (IPO / Paramounter). Tool choice is a provenance field: feature overlap across tools can be ~8%. |
| Annotation | matchms, SIRIUS/CANOPUS, GNPS FBMN, HMDB / METLIN / MassBank / LipidBlast | Identity is graded. Unknowns stay OPEN. ESI artifacts are first-class, not “discoveries.” |
| Stats / pathways | **MetaboAnalyst 6.0** (web + R); mixOmics / ropls / limma; Python sklearn | Dose-response / BMD and mummichog belong here. PCA is not a mechanism. |
| Orchestration | Galaxy-M, W4M, Nextflow, xcmsrocker | Reproducible run, not a GUI screenshot. |

Starting pipeline for a Hall-style meal contrast:

```
mzML → MS-DIAL (or XCMS) → SIRIUS/GNPS → MetaboAnalyst
                                         ↘ Bac LAW cards (which peak sits on which path)
```

Scripted over GUI for anything that will be cited. Parameter file travels with the card.

### 6.3 The experiment nobody has run (plant this)

Two keto (or two “non-UPF”) diets matched on every analyte the label can carry — ribeye/eggs/spinach vs bars/shakes/keto-bread — inside a ward, with:

- eating rate / chews
- GLP-1, PYY, CCK time series
- CGM + postprandial TG
- blood/urine metabolome (Abar score + untargeted)
- optional: emulsifier / SCFA panel

Bac predicts they diverge. Every operational definition the current system can carry predicts they do not. That trial is the falsifier.

---

## 7. The four books, compiled

They are not decoration. They are the four layers Bac already pretends to have.

| Book | Layer | What to pull |
|---|---|---|
| **Griffiths, *Metabolomics, Metabonomics and Metabolite Profiling*** (RSC, 2007/8; ISBN 978-0-85404-299-9) | Assay science | What a “metabolome” is, why NMR vs MS, why identification ≠ peak. Dated on software (pre-MS-DIAL, pre-SIRIUS, pre-GNPS-FBMN) but the *epistemology* is still right: empty beats fake. Use as the teaching preface to §6; do not cite it for 2026 tools. |
| **Nutritional Factors: Modulating Effects on Metabolic Processes** (QP 171 .N87; authors incompletely identified) | Composition axis | Nutrient-as-modulator of metabolic processes — the HFSS / nutrient-package projection. **Identify the exact edition before citing.** Call number confirms the subject, not the bibliographic record. |
| **Barrett, *Gastrointestinal Physiology*, 2e** (Lange / McGraw-Hill, 2013–14; ISBN 978-0-07-177401-7) | Host path, lumen | Mastication, gastric emptying, CCK, ileal brake, GLP-1/PYY, bile, absorption kinetics. This is the law book for `run_digestion`. The v2 “distal-gut signalling” section is Barrett, untyped. |
| **Gass & Kaplan, *Handbook of Endocrinology*, vol. I, 2e** (CRC, 1996; ISBN 978-0-8493-9429-4) | Host path, hormone | Insulin, glucagon, incretins, thyroid, adrenal, gonadal modulation of fuel. Dated on GLP-1 agonists; still the right *topology* for endocrine laws. Pair with a 2024–26 incretin review for the Godschall / orforglipron layer. |

The compile: Griffiths tells you how to *see* the metabolome; Barrett and Gass tell you which peaks *should* move if a matrix collapses; the nutritional-factors book tells you which peaks would move from composition alone. A study that cannot say which of those three it measured cannot enter the ledger.

---

## 8. What is actually new online (2025–2026) vs what you already knew

Worth ingesting:

- Medin et al. 2025 — six-system systematic review (NOVA, EPIC, IFPRI, UNC, UP3, Siga). Confirms `upf.md`. Siga is the only one that both names unique additives *and* applies quantitative nutrient criteria.
- Abar / Loftfield 2025 — poly-metabolite score validated on Hall’s trial. The measurement paper the Bac stack has been waiting for.
- Dicken 2025 + *Nature Medicine* correspondence — second human crossover, contested magnitude. Already in v2.
- Wang et al. 2026 *Front. Nutr.* — matrix-collapse cascade, useful diagram, overclaims relative to your v2.
- IAFNS 2025–26 classification principles — the industry-science counter-schema. Track as a competing compiler, not as evidence.

Not worth promoting:

- CHIPS as if it were a peer-reviewed alternative.
- Brain microplastics → UPF (no diet measured).
- Any pooled “UPF causes X” that mixes NOVA, HPF, and GloboDiet recodes.

---

## 9. Three papers, not one

### Paper A — *Processing as a typed event* (methods / schema)

Deposit next to FDP-1 / EDP-1. Public object: `PROCESSING_EVENT` + required `classification.system`. Include the atlas in §3. No new biology. This is the construct-validity paper the field lacks.

One sentence: *Ultra-processed is not an exposure; it is a family of incompatible instruments, and we refuse to pool them.*

### Paper B — *Mechanistic evidence linking processing to metabolic outcomes* (the line you like)

Keep the v2 mechanisms. Add Barrett / Gass as the typed host. Add Abar 2025 as the metabolomic instrument. Add the un-run keto-matched trial as a planted prediction. Do not add a new taxonomy.

One sentence: *The mechanistic case is a cascade from matrix to eating rate to distal-gut signalling to hepatic flux; only the first two steps are causally bound in humans.*

### Paper C — *Biology as Code: compiling the cascade* (software + laws)

Turn Paper B’s table into LAW-SPEC cards (`L-MATRIX-1` eating rate, `L-ILEAL-1` GLP-1/PYY, `L-DNL-1` ChREBP/SREBP). Wire Hall and Abar as the evidence objects. Pathways you already ship (glycolysis, TCA, AMPK·mTORC1·SREBP) are the liver end of the cascade. Fail closed: a card without a bound stays a hypothesis.

One sentence: *A processing event is compilable if and only if it names a unit operation, a matrix state, and a host path with a cited bound.*

Paper B is the public narrative. Paper A is the contract. Paper C is the instrument. v2 is the literature review that A–C sit on.

---

## 10. Practical next actions

1. Lift the `upf.md` atlas (IFIC, IFPRI, UP3, Mexican NIPH, Nova+HFSS) into v2 or into Paper A. v2 currently under-lists.
2. Identify book 2 (QP 171 .N87) before any citation.
3. Pull Abar 2025 (*PLOS Med* e1004560) as a primary, not via the NCI news page.
4. Do not fold metabolomics-tool reviews into the UPF paper. They belong as the methods appendix of Paper C.
5. Keep CHIPS in a “live proposals” footnote.
6. When the Hub Causes / Association panes grow a processing slice, the definition switcher from `upf.md` §4 is the UI, not a new NOVA score.

---

## 11. One-paragraph abstract you can steal

> Competing food-processing taxonomies — NOVA, Siga, HPF, UNC, EPIC-Soft/GloboDiet, IFIC, IFPRI, UP3, and the proposed CHIPS framework — operationalize different constructs. They cannot be pooled. The mechanistic evidence linking processing to metabolic outcomes is a separate object: matrix disintegration raises eating rate and energy intake in the only tight human feeding trials; distal-gut enteroendocrine signalling, emulsifier–microbiome effects, hepatic de novo lipogenesis, and circulating metabolomic signatures are coherent host paths with uneven human evidence. Biology as Code does not choose a taxonomy. It types the underlying processing event (unit operations, matrix state, additive set, nutrient package) and compiles it onto those host paths, failing closed wherever a bound has not been measured.

That is the transition.
)


**Metabolomics data analysis tools** form a modular ecosystem covering raw data preprocessing (peak detection/alignment), annotation/identification, statistical analysis, pathway/network interpretation, and visualization. The field is dominated by open-source options with strong community support, supplemented by commercial vendor software. Recent trends (2021–2026) emphasize AI/ML integration for peak picking and annotation, better MS² handling, exposomics/dose-response capabilities, scalability for large cohorts, and interoperability (e.g., standardized formats and pipelines).

A curated review of tools from 2021–2025 (available on GitHub/Zenodo) categorizes hundreds of resources across annotation, databases, preprocessing, networking, and more.

### Core Preprocessing Tools (Feature Detection, Alignment, Quantification)
These convert raw LC-MS/GC-MS data (mzML preferred after conversion via ProteoWizard/msconvert) into feature tables.

- **XCMS** (R/Bioconductor package + XCMS Online web version): Long-standing standard (since ~2005). Handles peak detection (CentWave algorithm), retention time correction, alignment, and filling. Recent updates improve scalability for thousands of samples and integrate into a broader ecosystem. Highly scriptable and reproducible; pairs well with CAMERA for annotation.
- **MS-DIAL** (Windows GUI, latest ~v5.5 as of early 2026): Excellent for untargeted metabolomics/lipidomics across GC/LC-MS and MS/MS (including data-independent acquisition/DIA deconvolution). Strong MS² support, lipid rule-based annotation, and vendor format compatibility. Frequently ranks high in feature recovery and quantification accuracy comparisons.
- **MZmine** (Java-based, open-source; now professionally supported in parts): Flexible GUI + modular workflows. Strong community features, MS² handling, and export to tools like GNPS/SIRIUS. Often detects the most features (sometimes noisier); good for complex datasets.
- **Others**: OpenMS (C++/Python bindings, feature finders); Asari (Python, used in MetaboAnalyst and pipelines for accurate peak detection); MSOne (newer AI-powered end-to-end suite with CNN-based denoising/segmentation).

**Comparisons**: Feature overlap across tools is often low (~8% in some studies). MS-DIAL frequently matches manual integration best for quantification and true positives; XCMS and MZmine perform solidly; vendor tools (e.g., Compound Discoverer) can struggle with certain peak shapes. Parameter optimization (e.g., via Paramounter or IPO) is critical.

**Recommended starting pipelines**:
- GUI-focused: MS-DIAL or MZmine → annotation → stats.
- Scripted/reproducible: ProteoWizard → XCMS/Asari → R/Python stats.
- Python-centric: Asari-based PCPFM (Python Centric Pipeline for Metabolomics) or pyOpenMS workflows.

### Annotation and Identification
- **Spectral matching & libraries**: Matchms, MS-FINDER, library searches against HMDB, METLIN, MassBank, NIST, GNPS libraries, LipidBlast.
- **In silico / structure elucidation**: SIRIUS + CSI:FingerID/CANOPUS (formula prediction, structure ranking, class prediction); CFM-ID; newer generative models.
- **Molecular networking**: **GNPS** (Global Natural Products Social Molecular Networking) — core for Feature-Based Molecular Networking (FBMN). Groups related spectra into molecular families, propagates annotations, and supports community curation/living data. Integrates with MZmine/MS-DIAL/XCMS outputs; enables repository-scale searches (e.g., MASST).
- Emerging challenges: Many “unknowns” may be ESI artifacts/microdroplet reactions; reaction-aware annotation is improving rates significantly.

### Statistical Analysis, Pathway, and Functional Interpretation
- **MetaboAnalyst 6.0** (web platform + R package; actively updated into 2026): The most comprehensive all-in-one tool. Supports targeted/untargeted data (concentration tables, peak lists, raw LC-MS/MS spectra via Asari). Key modules include:
  - Spectra processing + MS² annotation.
  - Univariate/multivariate stats (PCA, PLS-DA, OPLS-DA, volcano, heatmaps, random forests, etc.), including complex metadata/multi-factor designs.
  - Biomarker analysis (ROC curves).
  - Pathway analysis (enrichment + topology) for ~130 species; joint pathway (metabolites + genes); MSEA/enrichment libraries (including gut microbiome and lipidomics sets).
  - Functional analysis (mummichog/GSEA-style for untargeted peaks).
  - Newer: Dose-response/BMD modeling, causal analysis via Mendelian randomization/mGWAS, meta-analysis.
  - Excellent visualizations and reports. Free public server (with limits); Pro/cloud options available.
- Scripted alternatives: R (mixOmics, ropls, limma, etc.) or Python (scikit-learn, pandas-based pipelines); recent GitBook resources standardize R/Python best practices for lipidomics/metabolomics visualization and stats.
- Pathway tools: MetPA, Mummichog, PaintOmics; multi-omics platforms like Profiler.

### Specialized / Emerging Tools
- **Vendor/commercial**: Bruker MetaboScape (ion mobility + CCS), Thermo Compound Discoverer, Agilent, Shimadzu Peakintelligence (AI peak integration).
- **AI-powered**: MSOne, various spectrum embedding/similarity models (e.g., MS2DeepScore), de novo generators.
- **Exposomics / large-scale**: Tools supporting chemical mixtures, dose-response, and repository mining.
- **Databases & supporting resources**: HMDB, MetaboLights, Metabolomics Workbench, GNPS-MassIVE, METLIN, MassBank, foodMASST/microbeMASST/plantMASST for context-specific searches.
- **Workflow orchestration**: Galaxy-M, Workflow4Metabolomics, Nextflow-based pipelines, Docker images (e.g., xcmsrocker).

### Practical Recommendations
1. **Start simple**: Convert raw data → MS-DIAL or XCMS for features → MetaboAnalyst for stats/pathways.
2. **For MS²-rich discovery**: MS-DIAL/MZmine → GNPS FBMN → SIRIUS.
3. **Reproducibility**: Prefer scripted (R/Python) over pure GUI for publication; document parameters thoroughly.
4. **Quality focus**: Evaluate peak shapes, linearity, missing values, and true-positive rates. Use QC samples and batch correction.
5. **Scale & integration**: For multi-omics or large cohorts, look at modular Python/R ecosystems and cloud options.
6. **Limitations**: Annotation rates remain low for unknowns; tool choice affects results (validate key findings); computational resources matter for large datasets.

Resources for deeper exploration include the Enveda curated tools list (GitHub), MetaboAnalyst tutorials, MS-DIAL documentation, GNPS docs, and recent review papers on preprocessing comparisons. Public datasets (e.g., from MetaboLights or UK Biobank metabolomics releases) are excellent for testing workflows.

If you have a specific data type (LC-MS, GC-MS, NMR, targeted vs. untargeted, lipidomics, exposomics), instrument vendor, or goal (e.g., biomarker discovery, pathway mapping for nutrition schemas, or integrating with your System Load Index work), I can narrow recommendations or outline a concrete pipeline.


Here are the bibliographic details for the four books shown in the photo:

**1. Metabolomics, Metabonomics and Metabolite Profiling**  
Edited by William J. Griffiths  
RSC Biomolecular Sciences series  
Royal Society of Chemistry, 2007 (hardback; some library records list 2008)  
ISBN-13: 978-0-85404-299-9  
ISBN-10: 0-85404-299-7  
Call number visible: QP 171 .M3824 2008  

**2. Nutritional Factors: Modulating Effects on Metabolic Processes**  
Authors: Boers & Bassett (full first names not clearly legible on the spine)  
Call number visible: QP 171 .N87  

*(This appears to be a less widely catalogued title; library call numbers confirm the subject area as nutritional/metabolic physiology.)*

**3. Gastrointestinal Physiology, 2nd Edition**  
Author: Kim E. Barrett  
Lange Physiology Series / McGraw-Hill Education  
2013–2014  
ISBN-13: 978-0-07-177401-7  
ISBN-10: 0-07-177401-7  

**4. Handbook of Endocrinology, Volume I, Second Edition**  
Edited by George H. Gass & Harold M. Kaplan  
CRC Press, 1996  
ISBN-13: 978-0-8493-9429-4  
ISBN-10: 0-8493-9429-5  
Call number visible: QP 187 .C73 1996 Vol. 1  

These align well with work on metabolic processes, nutrient effects, gastrointestinal handling of food, and endocrine regulation of metabolism. Let me know if you need DOIs, chapter-level citations, or help locating PDFs/library access for any of them.




Ultra-Processed Food Literature Synthesis A narrative review mapping the competing taxonomies (NOVA, HPF, EPIC-Soft, CHIPS) and the mechanistic evidence linking processing to metabolic outcomes.