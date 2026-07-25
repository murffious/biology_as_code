# Validation report

What in this package is checked, what is checked *against*, and what is teaching
scaffolding that should not be cited as a result. Read this before using any number
from the package in an argument.

The short version: **the structural claims are tested, the magnitudes largely are
not, and the package is built to say so.**

## Tiers

The tier vocabulary is declared per component in
`src/biology_as_code/data/VERSION_MANIFEST.json` and enforced by
`tests/test_version_manifest.py`.

| Tier | Meaning | Citable as |
| --- | --- | --- |
| `LAW` | A rule from the LAW-SPEC register, with gate/bound/conditions and source | The stated law, at its stated confidence |
| `UNITS` | A filled unit with locked magnitude | The magnitude, within stated conditions |
| `UNITS_skeleton` | Structure present, **magnitude not locked** | Structure only — never the numbers |
| `EVIDENCE` | Provenance and citation handling | Provenance, not conclusions |
| `FLOW` | Teaching simulation | Direction and shape of a mechanism |
| `POLICY` | A recorded decision about promotion | The decision, not a finding |

`FLOW` is the largest tier. That is deliberate and it is the main limitation of the
package: most of the simulation exists to make a mechanism visible, not to predict
a value.

## What is actually verified

### Structurally verified (136 tests)

| Claim | How it is checked |
| --- | --- |
| Every food packet conforms to its schema | `test_packets.py` validates all 46 against `food_packet.schema.json` |
| Every claim audit conforms to its schema | `test_claim_audit.py` validates outputs against `claim_audit.schema.json` |
| No rule cites a nonexistent law | Every `law_refs` entry resolved against the 47-law register |
| Gate rules rest only on gate laws | `GateRule` law cards must have `gate.present == True`; `BoundRule` must not |
| `Confirmed` is unreachable | Asserted across every packet × claim combination |
| Undeclared ≠ declared-zero | `FoodPacket.declares()` tested against both cases |
| The manifest describes reality | Every component module and data artifact path must resolve |
| One version everywhere | pyproject, manifest, `CITATION.cff` and runtime must agree |
| Documentation executes | Every cookbook code block runs in CI |
| Unlocked magnitudes are declared | Skeleton artifacts must carry `magnitude_locked: false` |

Writing the last four found four live defects: the manifest advertised Python
`>=3.10` while the package required `>=3.11`; the `evidence_pubmed` component named
a module that had been renamed; a `UNITS_skeleton` artifact carrying 24 numeric
coefficients did not declare its magnitude as unlocked; and two documentation links
resolved only under the previous Jekyll setup.

### Verified against the register, not against outcomes

The 47 law cards carry their own conditions and hedges. Several are explicitly
provisional — LAW-001's bound, for instance, records its source example and marks
itself "Provisional; not pure isolated-fibre." The auditor propagates the law
reference so a reader can inspect that hedge; **it does not upgrade a provisional
law by using it.**

### Not verified

| Area | Status |
| --- | --- |
| Absorption coefficients in `simulate_meal` | `FLOW`. Directionally reasonable, not fitted to or validated against measured data |
| SCFA and colonic fermentation magnitudes | `UNITS_skeleton`, `magnitude_locked: false`. Energy band 1.5–2.5 kcal/g is an unlocked prior |
| Energy routing fractions | `FLOW` |
| AMPK / mTORC1 / SREBP activities | `FLOW` proxies. Signed edges are textbook; activity levels are illustrative |
| Pathway graph stoichiometry | Teaching graphs. Not systematically diffed against a reference database such as KEGG or Rhea |
| Bound magnitudes in the auditor | **Not emitted at all.** The auditor returns a signed direction only |

That last row is the design, not a gap. Direction is what the cited laws support;
magnitude depends on dose, matrix and host status, and the package declines rather
than interpolating.

## Coverage of the example data

Six of the 46 packets in `examples/foods/` are filled in. The rest are stubs, so
most audits return `UNEVALUABLE`:

```python
from biology_as_code.audit import audit_packet_coverage
from biology_as_code.packets import iter_packets

audit_packet_coverage(list(iter_packets()), "beta_carotene")
# {'Busted': 1, 'Plausible': 1, 'UNEVALUABLE': 44}
```

44 of 46 undecidable is the honest state of the data, and it is asserted by a test
so it cannot quietly improve on paper. Each `UNEVALUABLE` is a packet awaiting a
sourced fact.

## What would raise the tier

In rough order of value per unit of work:

1. **Fill the packet backlog.** 40 stubs. Each needs declared partner fields and
   matrix integrity — structural facts, not magnitudes — which moves audits out of
   `UNEVALUABLE` without asserting any number.
2. **Diff the pathway graphs against a reference database.** A test comparing
   stoichiometry to KEGG or Rhea would move `pathway_graphs` from teaching to
   verified for the subset it covers.
3. **Lock one magnitude properly.** Take the colonic fermentation energy band
   through the `UNITS_skeleton` → `UNITS` promotion with recorded evidence, as
   `LAW026_PROMOTION_DECISION.md` does for LAW-026. One worked promotion
   demonstrates the process better than ten more skeletons.
4. **Criterion validation.** The strongest verdict available is `Plausible`.
   Promoting anything to `Confirmed` requires outcome evidence, which is a research
   programme rather than a code change.

## What this report is not

This is not a claim that the package's outputs are clinically valid. It is
`FLOW`-tier teaching and research software and is not medical advice. Its
contribution is that the boundary between checked and unchecked is written down and
tested, rather than left for a reader to infer from confident-looking output.
