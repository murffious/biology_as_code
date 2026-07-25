# Claim auditor

The constitution says: fail closed when data is missing, never promote soft verbs
to law, never tunnel from L1 to L5. This page documents the code that enforces
those three rules.

```python
from biology_as_code import Claim, audit_claim
from biology_as_code.packets import get_packet

claim = Claim(
    id="claim.spinach_vitA_no_fat",
    surface_claim="Fat-free spinach salad prevents vitamin A deficiency",
    verb_class="disease_claim",
    nutrient="beta_carotene",
    surface_verb="prevents",
)

audit = audit_claim(claim, get_packet("ex.spinach_salad.zero_fat"))
audit.verdict                        # 'Busted'
audit.l1_to_l5["closed_through"]     # 'L3'
audit.law_refs                       # ('LAW-020', 'LAW-045')
```

## The verdict lattice

| Verdict | Meaning |
| --- | --- |
| `REFUSE` | Not auditable as stated — soft or marketing verbs, no typed mechanism. Returned before any packet is read. |
| `UNEVALUABLE` | Well-formed claim, but the packet does not declare the facts needed to decide. |
| `Busted` | A gate rule fired against a fact the packet actually declared. The path is shut. |
| `Plausible` | Gate open, bound direction determined. The strongest verdict a mechanism walk can reach. |
| `Confirmed` | **Never emitted.** Confirmation is an evidence-tier judgement about magnitude and endpoint. Reserved in the schema for a later evidence-promotion step. |

Refusing is a result, not a failure. A tool that returns `UNEVALUABLE` on 44 of 46
packets is reporting the true state of the data.

## Silence is not a zero

This is the whole design. `examples/foods/spinach_salad_zero_fat.json` declares
`dietary_lipid_g: 0` — a fact, so the gate can close and the verdict is `Busted`.
A stub packet declares nothing about lipid, so the gate state is unknown and the
verdict is `UNEVALUABLE`. `FoodPacket.declares()` separates the two cases and
everything else follows from it.

Treating absence as zero would manufacture a confident `Busted` out of missing
data. That is the failure mode this package exists to avoid.

## Gate ≠ Bound

Two rule types, not one table with a flag:

- **`GateRule`** is categorical. Hydrophobic cargo needs a lipid phase for
  micellar presentation (LAW-020) and chylomicron export (LAW-045). No lipid, no
  path — the claim is false, not small.
- **`BoundRule`** is a signed magnitude. Ascorbate expands the non-haem iron
  ceiling (LAW-004); tea tannins narrow it (LAW-006). The path stays open either
  way. No numbers are asserted, only a direction, because magnitudes belong to
  evidence rather than to law.

The register already draws this line. LAW-047 describes calcium's effect on iron
as "a magnitude effect, not a categorical gate like fat for micelles."

The three teaching pairs in `examples/foods/` exercise it:

| Pair | Result |
| --- | --- |
| `lentils_with_ascorbate` vs `lentils_with_tea` | Gate open both ways; `EXPANDS_BOUND` vs `NARROWS_BOUND`. Same label milligrams. |
| `spinach_salad_with_oil` vs `spinach_salad_zero_fat` | Gate open vs closed. A categorical difference. |
| `almond_whole` vs `almond_flour` | Gate irrelevant; matrix integrity flips the bound direction (LAW-024). |

## The rule table cannot drift from the register

Every rule carries `law_refs` into the LAW-SPEC register, and CI asserts a
structural invariant:

- a `GateRule` may only cite laws whose card has `gate.present == True`
- a `BoundRule` may only cite laws where it is `False`
- every cited law id must exist

So a rule cannot borrow categorical authority from a magnitude law, or cite a law
that was never written. Adding a rule is a source-backed decision that CI checks.

## Adding a lipid phase does not license a disease claim

```python
audit_claim(claim, get_packet("ex.spinach_salad.with_oil")).verdict
# 'UNEVALUABLE' — gate now passes, but closed_through == 'L5'
```

Fixing the mechanism opens the gate. It does not carry the claim to a disease
endpoint, because a single meal path cannot establish one. This is the anti-tunnel
rule in executable form.

## Honest coverage

```python
from biology_as_code.audit import audit_packet_coverage
from biology_as_code.packets import iter_packets

audit_packet_coverage(list(iter_packets()), "beta_carotene")
# {'Busted': 1, 'Plausible': 1, 'UNEVALUABLE': 44}
```

Most packets return `UNEVALUABLE` for any given nutrient, and that is mostly
correct rather than incomplete — a carotenoid claim against a chicken breast is
permanently undecidable, not pending. The useful metric is the decidable share
among packets that actually declare the cargo:

| Nutrient | Decidable |
| --- | --- |
| `beta_carotene` | 5 / 5 |
| `lipid` | 6 / 7 |
| `nonhaem_iron` | 2 / 4 |

12 packets are deliberately left as stubs because the relevant property is
ambiguous — whole versus skim milk, the matrix state of cooked starch, supplement
dose forms. `scripts/fill_packets.py` lists each with its reason. A wrong
structural declaration is worse than a stub, because it produces a confident
verdict.


## Opening a gate without inventing a number

`dietary_lipid_g` needs a value. A packet author who has no sourced number should
not have to invent one to record that olive oil contains a lipid phase, so gate
rules accept alternatives:

```python
from biology_as_code.audit import gates_for
gates_for("beta_carotene")[0].requires
# (('dietary_lipid_g', 'positive'), ('lipid_phase_present', 'true'))
```

Any one declared alternative satisfying the rule opens the gate. None declared is
still `UNEVALUABLE`. `lipid_phase_present` is a boolean about meal composition, so
it carries the gate while leaving the magnitude unlocked — the same discipline the
LAW-026 energy band follows.

Structural declarations are marked. Every one carries `derivation: "structural"`
and a `rationale`, so an inference from a food's identity stays distinguishable from
measured data, and `tests/test_packet_fills.py` asserts no structural fill ever
writes a magnitude or closes `label_amount`.


## Two vocabularies, and a gap between them

`docs/constitution.md` defines four states. `schemas/claim_audit.schema.json`
defines five verdicts. They overlap on two names and are not the same axis: the
constitution's states answer *can this be evaluated*, the schema's verdicts answer
*what is the result*.

`ClaimAudit.constitution_state` maps between them:

| `verdict` | `constitution_state` | |
| --- | --- | --- |
| `REFUSE` | `REFUSE` | declined before reading the packet |
| `Plausible` | `HOLDS` | gate open, bound evaluable |
| `Confirmed` | `HOLDS` | never emitted by a mechanism walk |
| `UNEVALUABLE` (gate passed) | `OPEN` | path ran, magnitude or endpoint unlocked |
| `UNEVALUABLE` (gate unknown) | `UNEVALUABLE` | a required field is missing |
| `Busted` | `REFUTED` | **not one of the four states** |

Two things fall out of writing this down.

**`UNEVALUABLE` was doing two jobs.** The constitution already separates "magnitude
or primary not locked" (`OPEN`) from "required field missing" (`UNEVALUABLE`). The
schema has no `OPEN`, so both collapsed into one verdict. `constitution_state`
splits them again on whether the gate resolved — the spinach-with-oil case is
`OPEN`, a stub packet is `UNEVALUABLE`.

**`Busted` has nowhere to live.** None of the four states means "evaluated, and
false." Forcing it into `REFUSE` would conflate declining to evaluate with
returning a negative result, which is the exact collapse this package exists to
prevent, so the property reports `REFUTED` instead.

Resolving that means either adding a fifth state to the constitution or accepting
that the two vocabularies answer different questions. Both are authorial calls, so
the code surfaces the gap rather than picking for you.
