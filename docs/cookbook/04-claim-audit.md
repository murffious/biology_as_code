# Lab 4 — Auditing a real claim

The previous labs used claims written to fit the packets. This one runs the
auditor the way a journalist or reviewer would: take a marketing sentence, atomise
it, and see where it fails.

## Step 1 — the sentence

> "Iron supports energy and boosts vitality."

Atomise it before touching any data:

```python
from biology_as_code import Claim, audit_claim
from biology_as_code.packets import get_packet

claim = Claim(
    id="claim.iron_supports_energy",
    surface_claim="Iron supports energy and boosts vitality",
    verb_class="soft",
    nutrient="nonhaem_iron",
    surface_verb="supports / boosts",
    atomized=("supports energy", "boosts vitality"),
)

result = audit_claim(claim, get_packet("ex.lentils.with_ascorbate"))
print("verdict :", result.verdict)
print("why     :", result.gate_note)
print("ladder  :", result.l1_to_l5 or "(never walked)")
```

`REFUSE` — and the ladder was never walked. The packet was well-populated and
irrelevant. "Supports" and "boosts" name no mechanism and no endpoint, so there is
nothing to trace. **Refusing before reading the data is the correct order of
operations.**

## Step 2 — make it auditable

A claim becomes auditable when it names a typed relation:

```python
typed = Claim(
    id="claim.iron_ascorbate_typed",
    surface_claim="Ascorbate in this meal raises absorbable non-haem iron",
    verb_class="bound_increase",
    nutrient="nonhaem_iron",
    surface_verb="raises",
)
result = audit_claim(typed, get_packet("ex.lentils.with_ascorbate"))
print(result.verdict, "|", [f.direction for f in result.bound_findings], "|", result.law_refs)
```

Same food. Same nutrient. The claim was rewritten to say something checkable, and
now it checks out.

## Step 3 — the serialised audit

Every result serialises to `schemas/claim_audit.schema.json`, so audits are
diffable artifacts rather than prose:

```python
import json
print(json.dumps(result.to_dict(), indent=2))
```

```python
from biology_as_code.packets import validate_against
from biology_as_code.packets.loader import schemas_dir

schema = json.loads((schemas_dir() / "claim_audit.schema.json").read_text())
print("schema valid:", validate_against(result.to_dict(), schema).valid)
```

## Step 4 — honest coverage

Run one claim across every packet and count the verdicts:

```python
from biology_as_code.audit import audit_packet_coverage
from biology_as_code.packets import iter_packets

packets = list(iter_packets())
print("packets      :", len(packets))
print("carotenoid   :", audit_packet_coverage(packets, "beta_carotene"))
print("non-haem iron:", audit_packet_coverage(packets, "nonhaem_iron", "bound_increase"))
```

Most packets return `UNEVALUABLE`. Six of the 46 are filled in; the rest are
stubs. The auditor reports that rather than filling the gap, which turns the
number into a backlog: every `UNEVALUABLE` is a packet waiting for a sourced fact.

!!! tip "Grading exercise"
    Give students three claims from real packaging. Ask each to predict the
    verdict *and* the level it closes through, before running the auditor. The
    interesting disagreements are almost always about whether a mechanism is a
    gate or a bound.

## Exercise

1. Find a claim that should return `Busted` but returns `UNEVALUABLE` because the
   packet is a stub. What single field would decide it?
2. `Confirmed` is in the schema but the auditor never emits it. Write the argument
   for what evidence would have to exist before a verdict could be promoted.
3. The constitution lists four states (HOLDS, UNEVALUABLE, REFUSE, OPEN) and the
   schema lists five verdicts. Map them. Which state has no schema home?
