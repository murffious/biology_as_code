# Lab 5 — Vitamin D vehicle (Combs gate, not a DRI table)

**Question for students:** two supplements list the same vitamin D on the panel.
One is an oil softgel. One is a dry tablet taken with water and no meal.
Does the label IU arrive?

This lab extends [Lab 2](02-fat-vehicle-gate.md) from leaf carotenoids to
cholecalciferol. Same constitution: **gate ≠ bound**, **label ≠ dose**,
**empty beats fake**. It does not encode a requirement, a % absorbed, or a
clinical protocol. Those stay in Combs / DRI / Krause.

## The pair

```python
from biology_as_code.packets import get_packet

for packet_id in ("ex.vitamin.d.softgel", "ex.vitamin.d.dry_tablet"):
    packet = get_packet(packet_id)
    print(packet.common_name)
    print("  cargo :", packet.cargo_nutrients())
    print("  lipid :", packet.partner("dietary_lipid_g"), "g")
    print("  status:", packet.status if hasattr(packet, "status") else "filled")
```

Same named cargo (`cholecalciferol`). One declares a lipid partner, the other
declares `0`. Label milligrams / IU stay `open` on purpose.

## Audit a disease slogan against both

```python
from biology_as_code import Claim, audit_claim
from biology_as_code.packets import get_packet

claim = Claim(
    id="claim.vitd_prevents_rickets",
    surface_claim="Take this vitamin D tablet to prevent rickets",
    verb_class="disease_claim",
    nutrient="cholecalciferol",
    surface_verb="prevents",
)

for packet_id in ("ex.vitamin.d.dry_tablet", "ex.vitamin.d.softgel"):
    result = audit_claim(claim, get_packet(packet_id))
    print(f"\n--- {packet_id}")
    print("verdict        :", result.verdict)
    print("gate_check     :", result.gate_check)
    print("closed_through :", result.l1_to_l5.get("closed_through"))
    print("laws           :", result.law_refs)
```

Expected teaching shape (not a clinical answer):

- Dry tablet: mechanism gate fails at **L3** if the auditor treats
  cholecalciferol like other fat-soluble cargo (lipid required). That is a
  closed path, not a smaller number.
- Softgel: lipid gate can pass, but a **disease** verb must still die at **L5**
  (`UNEVALUABLE`). One capsule is not a rickets trial.

If `cholecalciferol` is not yet on the fat-soluble gate register, the honest
result is `UNEVALUABLE` — not a invented pass. Do not patch a green score over
a missing nutrient alias. File that as a follow-up law-register PR.

## Weaker verb

```python
mechanism_claim = Claim(
    id="claim.vitd_needs_lipid",
    surface_claim="An oil vehicle makes this vitamin D absorbable via micelles",
    verb_class="bound_increase",
    nutrient="cholecalciferol",
)
result = audit_claim(mechanism_claim, get_packet("ex.vitamin.d.softgel"))
print(result.verdict, result.gate_check)
```

A mechanism claim may be `Plausible` when the vehicle is declared.
A rickets claim is not. The packet did not change into a textbook chapter on
DRI or pediatrics.

## What this lab refuses to compute

- IU → nmol/L 25(OH)D
- Host adiposity, malabsorption, or latitude
- Infant drops vs adult capsules as clinical protocols

Those are Brown / Krause / Combs chapters. Code here only asks: was the lipid
seat occupied?

## Exercise

1. Compare `ex.vitamin.d.dry_tablet` to `ex.spinach_salad.zero_fat`. Same cliff,
   different cargo. Name the cargo and the shared gate field.
2. A dry tablet swallowed *with* a 15 g fat meal — which seat moved, packet or
   meal partner? Should that be a new packet or a composed meal object?
3. If `gates_for("cholecalciferol")` is empty, is the correct next commit a fake
   % absorption table, or a LAW-020 alias row? Argue from the constitution.
