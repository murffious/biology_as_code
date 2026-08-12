# HRI/1.0 — Host Response Index
*(formerly BPS; renamed — in food-chemistry contexts "BPS" reads as bisphenol S. "The body's processing score" survives as the public gloss, not the identifier.)*
Editor's Draft 0.1.0 (pre-Stage-2 proposal) · Apache-2.0 · companion to the Response
objects volume and the VHM engine · drop into `design/` alongside the work order

## Definition

The Host Response Index is the **aggregation layer over typed Response objects** — it scores a food by the body's measured or modeled response, conditional on host class, never as a universal ranking:

```
HRI(packet, host_class, context) -> { score_band, bounds, coverage_tier, matrix, floor_cell }
```

Absorption is decomposed as **fraction × rate × site** — never "efficiency," which smuggles a valence (efficient absorption is the goal for iron in a deplete host and the problem for a sugar bolus). It answers the question the RDA never asked. The RDA (1941) tests whether each
*nutrient* clears its line. BPS tests whether each *system* stays within its bounds,
under the actual food as delivered, across all clocks. It is the host-side counterpart
to the packet's transformation record: **the food carries a record of what was done to
it; the body renders a score of what it did with it.**

HRI is a **function, not a property**. There is no universal HRI of a food — only
HRI conditional on a host class (and, personalized, on an individual's response
history). Public display defaults to the reference-host-class distribution, never a
bare number without its host class stated.

## The matrix: 7 systems × 3 clocks

Systems reuse the engine's existing `SevenSystem` enum verbatim
(`src/biology_as_code/…/laws/models.py`):

| | Acute (0–6 h) | Adaptive (days–weeks) | Parameter (months–years) |
|---|---|---|---|
| Assimilation | absorption kinetics, bioaccessibility | transporter regulation | absorptive capacity drift |
| Transport | postprandial transport loads | carrier adaptation | e.g., lipoprotein remodeling |
| Communication | satiety/incretin signaling per meal | signal-gain drift ("food noise") | appetite-controller recalibration |
| Defense | acute inflammatory markers | microbiome/immune shift | chronic inflammatory tone |
| Biotransformation | hepatic first-pass handling | enzyme induction | e.g., DNL/steatosis trajectory |
| Energy | glycemic/lipemic response | glycogen & substrate flexibility | insulin-resistance class drift |
| Structure | — (rarely acute) | tissue turnover inputs | lean mass / bone trajectory |

The **parameter clock is where "breaking our metabolism" gets a unit**:
ΔHostState per exposure-year — measured longitudinally where data exist,
predicted from acute+adaptive mechanisms where they don't, validated against cohorts.

Each cell holds zero or more `CellResult`s:
`{ class: beneficial|neutral|adverse|unknown, method: measured|modeled|prior,
response_refs[], evidence_state, bounds }`.
Cells consume **response classes**, never raw units: each Response object family
(GlycemicResponse/1.x, SatietyResponse/1.x, …) defines its own classification bounds
in its own versioned spec. HRI pins response-spec versions; it never reinterprets
raw data.

## Aggregation: the Liebig floor rule

1. A published **criticality registry** marks which cells are critical, per host class
   (e.g., Energy×acute is critical for insulin-resistant host classes;
   Communication×acute is critical universally). The registry is versioned data,
   not code.
2. **Score = the minimum over covered critical cells.** The barrel, not the average.
   A food that aces six systems while jamming satiety signaling scores as a jam.
3. Non-critical cells may lift the score only within the band above the floor, by a
   published tempering constant α (v1 proposal: α = 0.25, `evidence_state: contested`,
   open Stage-0 question — pure floor is the conservative default).
4. **The matrix always ships with the number.** No consumer surface may display the
   score without one-tap access to the full 7×3 profile and the floor cell. The score
   is a summary; the matrix is the finding.
5. **No averaging across systems, ever.** Averaging is the low-GI-candy hole:
   a single-metric or mean-based score is a Goodhart target regardless of whether the
   metric is an analyte or an outcome.

## Coverage tiers — fail-closed

| Tier | Basis | Cap |
|---|---|---|
| 0 Provisional | Input-axis prediction only (transformation record + reward profile through population priors) | Wide bounds; may not display top band; badge "provisional" |
| 1 Modeled | VHM predictions for all critical cells, **model version green on the ward-literature conformance suite** | Mid bounds; top band allowed only with Tier ≥2 on Energy & Communication acute |
| 2 Measured-acute | Standardized measured responses (per Response specs) in reference hosts for critical acute cells | Narrow bounds on acute row |
| 3 Measured-longitudinal | Adaptive/parameter clocks measured (cohort / NPH-class data) | Full |

Rules: any unmeasured **critical** cell widens the bounds and caps the tier.
**A food can never earn "beneficial" from one passed test.** Missing data stays
missing; it never quietly becomes neutral (repo-native fail-closed discipline).

## Anti-capture invariants

1. **Floor aggregation** (above) — no buy-backs across systems.
2. **Fail-closed coverage** (above) — no halo from a single axis.
3. **Open, versioned, forkable** — weights, floor rules, criticality registry, and
   conformance tests are public; changes ride the staged proposal process; every
   element carries `review_by`. The spec is Apache-2.0; the conformance mark, if any,
   is defended separately (spec open, mark earned — the UL model).

## Position in the architecture

Response objects are HRI's sub-scores. The VHM is its calculator where measurement is
missing — and a VHM version may produce Tier-1 index records **only** while green on the
five ward-literature conformance tests (Hall, almond, cheese/butter, Forde,
whole-vs-ground): calibration is a license, not a suggestion. NPH's 2027 release is
the reference-host distribution. The packet's L0–L3 transformation record is the
prior; BPS is the posterior; **processing is the warrant, BPS is the verdict.**

## Teaching case 1 — the RDA-adequate glass (see example instance)

Fortified sugar-sweetened juice drink, 100% DV vitamin C, host class
`adult_ir_intermediate`:

- **Assimilation×acute (vit C): host-conditional pass.** Absorption runs through
  saturable transporters; fractional absorption falls with dose; in a replete host
  the marginal benefit ≈ nil, in a deplete host it's real. The one genuine benefit —
  visible in the matrix, not erased.
- **Energy×acute: adverse — the floor.** Liquid sugar bolus, no matrix, high glycemic
  response in this host class.
- **Communication×acute: adverse.** Liquid calories, near-zero satiation per calorie.
- **Adaptive/parameter: modeled adverse drift** under repeated exposure
  (Tier 1, bounds wide).

**RDA verdict: adequate. HRI verdict: floored at Energy×acute, low band, matrix
attached.** The score does not say "vitamin C bad." It says the *delivery* failed
systems the checklist never watched — while crediting the repletion cell it served.
Counterpart: the whole orange — same vitamin C cell, fiber matrix → Energy×acute
neutral, Communication×acute beneficial → high floor. The pair is the almond logic,
relocated to the beverage aisle, and it is the entire 1941 error in two instances.

## Open Stage-0 questions (do not resolve silently)

α tempering value and whether it exists at all · the criticality registry's initial
rows per host class · band thresholds per Response spec · display grammar for the
distribution (host-class fan vs. single reference class) · whether Structure×acute
is ever scored.
