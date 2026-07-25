# LAW-026 promotion decision — best long-term path

**Date:** 2026-07-21  
**Inputs:** EV-039–041 abstract review (local PubMed) · targeted energy-yield search · FAO/Livesey secondary sources  
**Status:** **Recommended policy** (not yet written into LAW-SPEC registry)

---

## 1. Abstract review — priority keepers

### EV-039 · PMID 38441170 (2024) — *Food & Function*
**Title:** Protein combined with certain dietary fibers increases butyrate production in gut microbiota fermentation.

**Abstract gist:** Modern diets send more protein to the colon; study varies protein:fiber ratios and fiber types. **Butyrate production was maintained or increased** with fiber+protein and even pure-protein substrates in their system. Protein fermentation shapes community + metabolites; fiber–protein mixtures can still yield beneficial SCFAs.

| SSI dimension | Rating | Note |
|---------------|--------|------|
| Mechanism (substrate → SCFA) | 🟢 | Direct fermentation readouts |
| Human free-living energy | 🔴 | In vitro / model fermentation |
| Magnitude kcal/g | 🔴 | No energy conversion factor |
| LAW-026 shape | 🟢 | Supports non-zero SCFA from fermentable cargo; matrix matters |

**Tightened use:** Supports **conditions** (co-substrate, not fiber-g alone) and **SCFA production**, not energy factor lock.

---

### EV-040 · PMID 10702589 (2000) — *J Nutr*
**Title:** In vitro fermentation of swine ileal digesta containing oat bran dietary fiber by rat cecal inocula…

**Abstract gist:** Physiological digesta (swine ileal, oat bran vs wheat bran) + rat cecal inocula. **OB digesta fermented faster**, higher **propionate** molar share; WB did **not** increase butyrate; bacterial mass higher/longer on OB. Authors note agreement with in vivo human/rat patterns for these fibers.

| SSI dimension | Rating | Note |
|---------------|--------|------|
| Mechanism | 🟢 | SCFA from escaped fiber digesta |
| Cross-species / inocula | 🟡 | Swine digesta + rat inocula; claims human agreement carefully |
| Magnitude kcal/g | 🔴 | SCFA amounts, not host ME |
| LAW-026 shape | 🟢 | Escape fiber → SCFA is real |

**Tightened use:** Core **mechanism** EV for colon fermentation node. Prefer for “SCFA produced,” not “~2 kcal/g.”

---

### EV-041 · PMID 33995299 (2021) — *Front Microbiol*
**Title:** In vitro fermentation reveals changes in butyrate production dependent on RS source and microbiome composition.

**Abstract gist:** RS benefit often tied to **butyrate**; few taxa degrade RS; butyrate needs **cross-feeding network**. Human trials raise fecal butyrate **on average** with **interindividual** scatter. In vitro: 10 donors × 10 starches → **heterogeneous** butyrate; a microbiome is best suited only to a **subset** of RS; **membership** of degrader/producer guilds matters more than total counts.

| SSI dimension | Rating | Note |
|---------------|--------|------|
| Mechanism + conditions | 🟢 | Strong for LAW-025/026 **conditions** |
| Fixed population magnitude | 🔴 | Explicit interindividual + substrate heterogeneity |
| Magnitude kcal/g | 🔴 | |
| LAW-026 shape | 🟢 | Fermentability is conditional |

**Tightened use:** **Blocks premature magnitude lock.** Supports `rs_profile` + microbiome diversity as first-class inputs.

---

## 2. Energy-yield harvest (classic / host ME) — add to pack

Auto-queries under-harvested “Atwater / ME of fiber.” Local + secondary sources:

| Source | What it gives | Role |
|--------|----------------|------|
| **FAO** food energy chapter | ME factor for dietary fibre often **8 kJ/g (2.0 kcal/g)**; fermentable fibre higher (~11 kJ/g ME cited in FAO discussion); non-fermentable ~0 | **Prior range for FLOW**, not single law constant |
| **NCBI / IOM-style synthesis** (energy values for fibers) | Anaerobic yield estimates **~1.5–2.5 kcal/g** fermented fiber (cites Livesey 1990; Smith et al. 1998); cannot be 4 kcal/g | **Magnitude band** for provisional prior |
| PMID **40403748** (2025) | Methanogenesis + SCFA + **human-host metabolizable energy** (feeding study + continuous CH₄) | **EV-046 candidate** — rare human ME link |
| PMID **27786539** (2018) | SCFAs as end products of fiber/RS fermentation; energy homeostasis review | **EV-047 candidate** — framing review |
| PMID **35688319** (2022) | SCFA from fiber fermentation; energy/glucose homeostasis (review) | **EV-048 candidate** — host energy framing |
| PMID **31925422** (2020) | Atwater lecture — adaptation / energy methods lineage | Background only (not fiber ME factor) |
| FAO / Livesey secondary | ME fibre ~**8 kJ/g (2 kcal/g)**; fermented fiber often **1.5–2.5 kcal/g** band | Prior band for FLOW/UNITS |

### Energy abstracts (tightened)

**40403748:** Explores methanogens’ H₂ oxidation enhancing sugar fermentation to SCFAs the host can absorb; uses RCT-style feeding (western vs high-fiber), continuous methane, and **human metabolizable energy (ME)** associations. **Best local hit for host energy salvage.** Still not a single kcal/g table in the abstract — full text before any lock.

**27786539:** SCFAs (acetate, propionate, butyrate) = end products of microbial fermentation of **dietary fibers and RS**; review of SCFA roles in **energy homeostasis** / metabolic syndrome context. Good for shape + host energy framing; disease-prevention language must stay out of LAW-SPEC.

**35688319:** Fiber fermentation → SCFAs → beneficial effects on energy and glucose homeostasis; review of central/peripheral mechanisms. Supports “SCFAs participate in host energy regulation,” not a numerical ME factor.

**Targeted keepers for energy pack:** `40403748`, `27786539`, `35688319` + FAO/Livesey as **secondary priors**.

---

## 3. Best long-term outcome (decision)

### Do **not** lock FLOW’s current formula as law
Engine-style `fiber × 0.6 × 2.0 kcal` (or similar) stays **FLOW open-tier**. EV-041 shows why a single sim constant is dishonest as constitution.

### **Do** lock the **shape** of LAW-026 as solid
**Shape (claimable as law statement):**
1. Fermentable CHO that reaches the colon is **not energy-free**.  
2. Microbiota convert it to **SCFAs** (acetate, propionate, butyrate) that the **host can absorb**.  
3. Yield and SCFA mix depend on **substrate type/form** and **community** (conditions).  
4. Non-fermented residue contributes **bulk** (and gas pathways exist).

### **Magnitude policy (best long-term)**

| Layer | Policy |
|-------|--------|
| **LAW-SPEC bound** | **Shape-only** OR **soft range prior**: metabolizable energy from fermentable fiber/RS typically on order of **~1.5–2.5 kcal/g fermented substrate** (FAO ~2 kcal/g fibre ME as conventional factor) — **`magnitude_locked: false`** until a dedicated primary human balance study is EV-packed with explicit kJ/g. |
| **UNITS priors** | `human_evidence` medium-high for shape; `magnitude_locked: false`; optional `magnitude_range_kcal_per_g: [1.5, 2.5]` as **prior**, not gate. |
| **FLOW** | May use **~2 kcal/g × fermentable_g** for demos; must stay labeled `claim_tiers.scfa = flow`. |
| **App claims** | May say “fiber is not zero calories; fermentation recovers some energy as SCFA.” Must **not** claim precise kcal savings or disease prevention from SCFA. |

### One-line constitution
> **LAW-026 is a solid mechanism/shape law; energy magnitude is a provisional band for FLOW/UNITS priors, never a hard single coefficient until primary human ME evidence is promoted.**

That is the best long-term outcome: honest science, usable product demos, no fake precision.

---

## 4. SSI summary table (after this pass)

| ID | PMID | Shape | Conditions | kcal magnitude | Promote to register? |
|----|------|-------|------------|----------------|----------------------|
| EV-039 | 38441170 | 🟢 | 🟢 matrix | 🔴 | Yes as mechanism EV |
| EV-040 | 10702589 | 🟢 | 🟡 model | 🔴 | Yes as mechanism EV |
| EV-041 | 33995299 | 🟢 | 🟢 RS/microbiome | 🔴 | Yes as **anti-overlock** EV |
| Energy band | FAO / Livesey secondary | 🟢 | — | 🟡 range only | Cite as **prior**, not EV lock |
| 40403748 etc. | TBD full read | ? | ? | ? | Next abstract pass |

---

## 5. Implementation checklist (next engineering)

- [x] Filter 20 PMIDs; draft EV-039–045  
- [x] Abstract-tighten EV-039–041  
- [x] Decision: **shape solid / magnitude provisional band**  
- [ ] Append EV-039–041 to `gleaned/registers/evidence.md` (cross-repo; register not in this package)  
- [x] Attach PMID + FAO/Livesey notes on `base_unit_colon_fermentation.skeleton.json` `sources[]`  
- [x] Set units prior field `energy_kcal_per_g_fermentable: {low: 1.5, mid: 2.0, high: 2.5, locked: false}`  
- [x] Keep engine `claim_tiers`; optional print “ME prior band, not law-locked”  
- [ ] Full-text 40403748 / 27786539 for possible EV-046+ — **the one route to a magnitude lock**  
- [x] Enforce the policy in CI (`tests/test_law026_policy.py`) so an unlocked band is not
      mistaken for an unfinished one  

*Checklist reconciled 2026-07-25: items 2–4 were already satisfied in the skeleton
artifact but left unticked here. The remaining two are a cross-repo merge and a
full-text read; neither is a code change.*

---

## 6. What “fully there” means under this decision

You are **fully there for honesty** when:
1. LAW-026 **shape** is register-complete and tested as statement.  
2. Magnitude is either **absent** or a **documented unlocked band**.  
3. FLOW never overwrites the register.  
4. EV-039–041 (and energy reviews) are linked.

You are **not** fully there when a single demo coefficient is treated as LAW-SPEC truth — and under this decision, you **choose not to go there**. That is a feature.
