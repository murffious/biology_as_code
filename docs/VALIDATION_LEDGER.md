# Validation Ledger & Master Bibliography

Every claim in this package that rests on a **domain fact** rather than a
mechanism, with the source that would validate it and how strong that footing is
today. Mechanism (loaders, gates, tests) is out of scope here — it is testable and
tested. This ledger tracks the parts that a green test suite *cannot* verify.

Companion to `docs/VALIDATION.md` and `paper/SUBMISSION.md`. Sources marked
**[verified 2026-07]** were confirmed against the primary record this session.

## Source-strength score

| Score | Label | Meaning |
| --- | --- | --- |
| **5** | Locked | Primary human quantitative evidence, verifiable citation; a magnitude may be asserted. |
| **4** | Strong | Direct human study (or several converging) with a verifiable citation; direction solid, magnitude bounded. |
| **3** | Established mechanism | Textbook/consensus physiology, not in dispute; single or secondary citation, **or** deliberately shape-only (magnitude unlocked by policy). |
| **2** | Structural inference | Follows from food identity/composition; defensible, no primary citation attached yet. |
| **1** | Asserted / flagged | Stated in code or paper but explicitly unverified; source named but unconfirmed, or full-text pending. |
| **0** | Unsourced | No source. Must not bear weight until one is attached. |

The package's own rule holds here: **empty beats fake**. A `2` with an honest note
is worth more than a `5` asserted from memory.

---

## Master bibliography

### Primary literature — verified this session

- **Poon T, Labonté M-È, Mulligan C, Ahmed M, Dickinson KM, L'Abbé MR.** Comparison
  of nutrient profiling models for assessing the nutritional quality of foods: a
  validation study. *Br J Nutr.* 2018. **PMID 30015603 · PMC6137431.**
  Five regional models vs Ofcom reference across **15,342** foods; discordant
  classifications **5.3% FSANZ, 8.3% Nutri-Score, 22.0% EURO, 33.4% PAHO, 37.0%
  HCST**. **[verified 2026-07]** — backs the JOSS Statement-of-Need statistic.
- **Brown MJ, Ferruzzi MG, Nguyen ML, Cooper DA, Eldridge AL, Schwartz SJ, et al.**
  Carotenoid bioavailability is higher from salads ingested with full-fat than with
  fat-reduced salad dressings. *Am J Clin Nutr.* 2004;80(2):396–403.
  With **fat-free** dressing, carotenoid appearance in chylomicrons was
  **negligible**; optimal absorption needed **>6 g** added fat. **[verified 2026-07]**
  — backs the fat-vehicle gate (LAW-020) and the leafy-green `lipid_phase_present=False` calls.
- **Unlu NZ, Bohn T, Clinton SK, Schwartz SJ.** Carotenoid absorption from salad and
  salsa by humans is enhanced by the addition of avocado or avocado oil. *J Nutr.*
  2005;135(3):431–436. **PMID 15735074.** Absorption gain "attributed primarily to
  the lipids present in avocado." **[verified 2026-07]** — backs
  `avocado: lipid_phase_present=True` on **intrinsic** lipid.
- **Kopec RE, et al.** Avocado consumption enhances human postprandial provitamin A
  absorption and conversion. **PMID 24899156.** Supporting, intrinsic avocado lipid.
- **Gaitán D, … Lönnerdal B, et al.** Calcium and nonheme/heme iron absorption. *J
  Nutr.* 2011;141(9):1652–1656. DOI 10.3945/jn.111.138651. Inhibition appears at
  **≥800–1000 mg** single-dose; **absent over a whole 4-day diet**. **[verified 2026-07]**
  — nuance for LAW-047 (calcium `NARROWS_BOUND`, meal-level only).

### LAW-026 colonic-energy pack (PMIDs in `base_unit_colon_fermentation.skeleton.json`)

- **38441170** — fibre ± protein fermentation → butyrate.
- **10702589** — fibre digesta → SCFA (in vitro).
- **33995299** — RS source + microbiome set butyrate; **EV-041, the anti-overlock evidence**.
- **40403748** — methanogenesis / SCFA / human ME. **Full-text PENDING** — the *only*
  in-pack route to promoting the energy magnitude to a lock.
- Candidate queue in `evidence_candidates_LAW026.json`: 27786539, 35688319, 36638279,
  39748438, 39909254, 40484608, 40817467, 41006931, and further stubs — triage status
  unverified.

### Formal references (`paper/paper.bib`)

- **dooley2018** FoodOn — DOI 10.1038/s41538-018-0032-6
- **griffiths2024** OBO Foundry food ontology — DOI 10.3233/sw-233458
- **wilkinson2016** FAIR principles — DOI 10.1038/sdata.2016.18
- **barbieri2015** Code Biology — DOI 10.1007/978-3-319-14535-8

### Named in-repo but not yet PMID-linked

Legacy citations embedded in law `bound` text, worth promoting to real refs:
**Derman 1977** (tea/ascorbate iron, LAW-004/006), **Rossander** (orange juice iron),
**FAO** food energy factors (~8 kJ/g fibre ME), **Livesey** fermentable-fibre energy
synthesis (~1.5–2.5 kcal/g), **SLAMENGHI** carotenoid-modifier framework (LAW-020).

---

## Validation TODO ledger

Ordered by risk. "Now" = current strength; "Target" = what closes the gap.

### 1 — JOSS discordance statistic — `paper/paper.md:44`
- **Claim:** 5–37% discordant classifications across five models on 15,342 foods.
- **Status:** deliberately uncited pending verification (`paper/SUBMISSION.md`).
- **Now: 1.** Source is verified (Poon 2018, PMID 30015603) → **Target: 4.**
- **Action:** add `poon2018` to `paper.bib`, cite `[@poon2018]` in `paper.md`, tick off
  item 1 in `SUBMISSION.md`. Numbers in the paper match the source exactly.

### 2 — Leafy-green fat gate — `scripts/fill_packets.py` LIPID_PHASE
- **Claim:** `spinach_raw / kale_raw / broccoli_steamed → lipid_phase_present=False`.
- **The worry (retired):** that trace ~0.4 g/100 g leaf lipid makes `False` a
  *confident false negative*. Brown 2004 shows fat-free → **negligible** carotenoid
  in chylomicrons; the leaf's trace lipid is an order of magnitude below the >6 g
  threshold. **`False` is biologically correct.**
- **Now: 2 (structural) → Target: 4** once Brown 2004 is cited in the rationale.
- **Action:** attach Brown 2004 to the rationale strings. **Fix the wording**:
  broccoli's `"no fat added and none intrinsic"` overstates — brassica *does* carry
  trace lipid. Prefer `"negligible intrinsic lipid, below the micellar-formation
  threshold; eaten alone"`.

### 3 — Intrinsic-lipid gate opens — `scripts/fill_packets.py` LIPID_PHASE
- **Claim:** `avocado / salmon_fillet / walnut_whole → lipid_phase_present=True`.
- **avocado:** validated — Unlu 2005 shows avocado's intrinsic lipid enhances
  carotenoid absorption. **Now 2 → Target 4** (cite Unlu 2005).
- **salmon:** oily fish, intrinsic lipid ~8–12 g/100 g, far above threshold —
  structural, defensible. **Now 2.**
- **walnut:** intrinsic lipid ~65 g/100 g, but **matrix-encapsulated** (cell-bound;
  see MATRIX `walnut_whole=intact`). Whole vs ground nut releases lipid differently.
  Defensible but note the matrix caveat. **Now 2.**
- **Open question for LAW-020/045:** does intrinsic lipid satisfy the *same* gate as
  added lipid? Evidence (avocado) says **yes** at the micellar step. Fine as modeled.

### 4 — `matrix.integrity="partial"` is inert — `src/biology_as_code/audit/gates.py`
- **Finding:** `"partial"` is a valid schema enum value, but the matrix BOUND rules
  only fire on `destroyed` and `intact`. `oats_porridge_plain` and
  `whole_wheat_bread` (both `partial`) therefore get **no** bound adjustment.
- **Not a source gap — a design gap.** Score N/A.
- **Action (decide):** either add a `partial` bound rule (a source-backed direction),
  **or** document that `partial` is intentionally inert because its net direction is
  ambiguous. Leaving it silent invites a wrong assumption.

### 5 — LAW-045 semantic fit — `src/biology_as_code/audit/gates.py` law_refs
- **Finding:** the fat-vehicle gate cites LAW-020 **and** LAW-045. LAW-045's
  categorical closure is **host-competence** (apoB-48/MTP; abetalipoproteinemia), not
  meal lipid. On a meal-composition gate, **LAW-020 is load-bearing; LAW-045 is a
  downstream export step** that dietary lipid feeds as TAG substrate.
- **Mechanism: 3 (textbook).** CI invariant holds (both cards `gate.present=True`).
- **Action:** keep the citation but add a code note distinguishing the two choke
  points; no new source needed. Not a blocker.

### 6 — `REFUTED` fifth constitution state — code vs docs
- **Finding:** `ClaimAudit.constitution_state` already **returns `REFUTED`**, and
  `tests/test_claim_audit.py` already enforces it (`CONSTITUTION_STATES` includes it;
  `test_refuted_is_not_collapsed_into_refuse`). Only the **docs** still say "four
  states": `docs/constitution.md`, `docs/claim-auditor.md` ("not one of the four
  states"), `docs/cookbook/04-claim-audit.md`.
- **Recommendation (mine): adopt `REFUTED` as the fifth state.** "Evaluated and
  false" is epistemically distinct from REFUSE (declined). Folding it into REFUSE is
  the exact collapse this package exists to prevent, and leaving the code emitting a
  value absent from its own docs is latent drift.
- **Action (docs only):** add `REFUTED` — *"mechanism walk completed and contradicted
  the claim"* — to `constitution.md`; update the two docs that say "four."

### 7 — LAW-026 energy magnitude — stays a soft band
- **Policy (`LAW026_PROMOTION_DECISION.md`, guarded by `test_law026_policy.py`):**
  band 1.5–2.5 kcal/g, `locked: false`, EV-041 forbids a point estimate.
- **Shape: 3. Magnitude: 1 (pending).** Do **not** lock.
- **Only route to a lock:** full-text read of **PMID 40403748** (needs journal access,
  not code). If read, update the decision doc *first*, then the tests.

### 8 — Calcium–iron bound — `src/biology_as_code/audit/gates.py` LAW-047
- **Claim:** `calcium_same_meal → NARROWS_BOUND` for non-haem iron.
- **Nuance (Gaitán 2011):** single-meal inhibition is real at ≥800 mg but **attenuates
  to nil over a whole diet.** The meal-level bound is correct; the whole-diet caveat
  belongs in the note. **Now: 3.**
- **Action:** cite Gaitán 2011 in the LAW-047 note; keep the rule.

### 9 — Iron modifier laws — LAW-004 / LAW-006
- **Status:** real named sources (Derman 1977, Rossander) live in the `bound` text but
  are not PMID-linked. **Now: 3.**
- **Action:** promote to formal PMIDs in the law cards.

---

## Scoreboard

| # | Item | Now | Target | Blocker |
| --- | --- | :-: | :-: | --- |
| 1 | JOSS discordance stat | 1 | 4 | cite Poon 2018 |
| 2 | Leafy-green fat gate = False | 2 | 4 | cite Brown 2004; fix wording |
| 3 | Avocado intrinsic-lipid = True | 2 | 4 | cite Unlu 2005 |
| 3 | Salmon / walnut intrinsic = True | 2 | 3 | structural; matrix caveat |
| 4 | `partial` matrix inert | — | — | design decision |
| 5 | LAW-045 gate co-citation | 3 | 3 | note only |
| 6 | `REFUTED` fifth state | code done | — | docs reconcile |
| 7 | LAW-026 magnitude | 1 | 5 | full-text PMID 40403748 |
| 8 | Calcium–iron bound | 3 | 4 | cite Gaitán 2011 |
| 9 | Iron laws LAW-004/006 | 3 | 4 | attach PMIDs |

**Fastest wins (sources already in hand):** items 1, 2, 3, 8 — four citations close
them. **The one genuinely blocked item is 7**, and it is blocked correctly: it needs
a journal read, and the policy tests exist precisely to stop anyone "finishing" it
without one.
