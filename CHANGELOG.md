# Changelog

All notable changes to the **biology-as-code** Python package are documented here.

## [Unreleased]

### Added

- **Fail-closed claim auditor** (`biology_as_code.audit`): `audit_claim(claim, packet)`
  walks the L1→L5 delivery ladder and returns a `ClaimAudit` conforming to
  `schemas/claim_audit.schema.json`. Verdict lattice is `REFUSE` / `UNEVALUABLE` /
  `Busted` / `Plausible`. `Confirmed` is deliberately unreachable from a mechanism
  walk — confirmation is an evidence-tier judgement — and a test asserts it can
  never be emitted. `Claim`, `ClaimAudit`, and `audit_claim` are on the top-level API.
- **Declared gate/bound rule table** (`biology_as_code.audit.gates`): `GateRule` for
  categorical requirements, `BoundRule` for signed magnitude modifiers, kept as
  separate types so Gate ≠ Bound is enforced by the type system rather than a flag.
  Every rule carries `law_refs` into the LAW-SPEC register, and CI asserts the
  structural invariant that a `GateRule` may only cite laws with `gate.present == True`
  and a `BoundRule` only laws where it is `False`. No rule may cite a nonexistent law.
- **Typed food packet loader** (`biology_as_code.packets`): `get_packet`, `list_packets`,
  `iter_packets`, `validate_packet`, and a `FoodPacket` view over `examples/foods/`.
  `FoodPacket.declares()` separates "field not declared" from "declared false" —
  the distinction the auditor rests on, since silence is not a zero.
- **Zero-dependency JSON Schema validator** (`biology_as_code.packets.validate`)
  covering the keyword subset the repo's schemas actually use, preserving the
  package's no-dependency guarantee. `unsupported_keywords()` reports its own blind
  spot, and a test fails if a schema ever uses a keyword it cannot check.
- Tests: `tests/test_claim_audit.py` and `tests/test_packets.py` (38 new tests, 107
  total). Includes derivation of both hand-written fixtures in `examples/claims/`,
  and coverage of all three teaching pairs (iron/ascorbate vs tannin, fat-vehicle
  gate, almond matrix).
- Docs: `docs/claim-auditor.md`.

### Changed

- CI now runs the **whole** `tests/` suite. It previously ran four hand-picked
  files; the remaining nine were green but unguarded, so regressions in them could
  land unnoticed.
- CI gained a coverage job with a 90% floor on `audit` and `packets` (currently 92%),
  so an unexercised branch in the fail-closed core cannot silently become a pass.

### Fixed

- Schema validator treated Python `bool` as satisfying `type: number`, because
  `bool` subclasses `int`. JSON separates the two; `True` is no longer a valid number.
- Keyword-coverage walker descended into `properties` and reported every property
  *name* as an unsupported keyword.

## [0.1.0] — 2026-07-24

### Added

- First public PyPI-oriented release of the open dig + teaching pathway package.
- Open declarative **digestion machines** (`biology_as_code.machines`): versioned,
  inspectable JSON state graphs for the GI arc (oral -> stomach -> duodenum ->
  jejunum -> colon) plus a `full-digest` process, with `list_machines`/`get_machine`
  on the top-level API and a zero-dependency loader + validator (`validate_all`).
  Open FLOW tier only - the validator fails if any product-score/penalty hook leaks in.
- `simulate_meal()` high-level API wrapping the meal compile pipeline.
- Pathway graph discovery (`list_pathways`, `get_pathway`) over existing modules.
- Physiological scenarios: fed / overnight fast / prolonged fast / exercise.
- Meal fixtures (no product meal score / kibo_score fields), vitamins registry, personas.
- Law / iron / colon data via `data.kibo_core`.
- **Ketolysis** teaching pathway (`get_pathway("ketolysis")`) — ketone-body oxidation
  (BDH1 -> SCOT/OXCT1 -> ACAT1 -> 2 acetyl-CoA), including the liver's lack of SCOT.
  Closes TODO 6b; complements the existing ketogenesis graph.
- Multi-node **nutrient-sensing** regulatory graphs (`ampk_network`, `mtorc1_network`,
  `srebp_network`) with signed activates/inhibits edges and explicit AMPK/mTORC1/SREBP
  cross-talk. Now **executable from state**: `evaluate_network` propagates a signed graph,
  and `nutrient_sensing_snapshot(state)` chains AMPK→mTORC1→SREBP — surfaced under
  `report["nutrient_sensing"]` (the flat `pathway_regulation` floats are unchanged).
  Sources are rendered into the mermaid packs.
- `β-hydroxybutyrate` signaling pathway (HCAR2/GPR109A, class-I HDAC inhibition, NLRP3,
  GPR41) in the signaling registry — ketones as signals, not just fuel.
- Public LAW-SPEC **law cards** (`get_law`, `list_laws`, `law_card`) over the 47-law
  kibo_core register (System / Organ / Gate / Bound / Conditions / relation).
- Open **evidence/provenance** surface (`all_sources`, `pubmed_url`, `law_evidence`):
  aggregates declared sources, loads bundled LAW-026 PubMed candidates, and offers a
  **fail-closed** (offline, no fabricated citations) PubMed lookup.
- Pack exporter renders a pathway's `references` as `%% Source:` lines + a `## Sources`
  section, so citations survive regeneration.
- Optional product-score **hook only** (engine not shipped; patent pending).
- Quiet default logging (`BIOLOGY_AS_CODE_LOG=DEBUG` for dig traces).
- CI workflow + **Trusted Publisher** OIDC publish workflow.
- MIT `LICENSE` for the installable package.

### Changed

- Removed bulk snapshot fixtures from the wheel (`off_products_snapshot`, `packets-for-sim`,
  `payloads-for-sim`, `FOOD_SUBSET_CLASSIFICATION`, `beverage_library`) to keep the package lean.
- Ruff lint gate focused on real issues (`F` / imports) for legacy teaching modules.
- **M4:** topics ontology build scripts moved to `tools/topics_build/` (not in wheel).
- **L3:** register `EXTRA_MOLECULAR` dig structures; drop dead bare `Structure(...)` block.
- **L4:** single `get_digestive_mechanism_registry()` factory (no triple rebind).
- **L5:** vitamin adequacy keeps `coenzyme_factor` in sync so meal modifiers affect energy/path signals.

### Notes

- FLOW teaching software — not clinical decision support.
- Product meal score and Kibo-vars product scorer are **not** included.
- Book manuscript is **in progress / not yet released**, and is separately licensed (not part of this package).
