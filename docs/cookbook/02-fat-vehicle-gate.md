# Lab 2 — The fat-vehicle gate

**Question for students:** a spinach salad's nutrition panel lists vitamin A.
The dressing is fat-free. Does the vitamin A reach the student?

## The pair

```python
from biology_as_code.packets import get_packet

for packet_id in ("ex.spinach_salad.with_oil", "ex.spinach_salad.zero_fat"):
    packet = get_packet(packet_id)
    print(packet.common_name)
    print("  cargo :", packet.cargo_nutrients())
    print("  lipid :", packet.partner("dietary_lipid_g"), "g")
```

Same leaf matrix, same carotenoid cargo. One declares 6 g of dietary lipid, the
other declares 0.

## Audit the label's implied claim

```python
from biology_as_code import Claim, audit_claim

claim = Claim(
    id="claim.spinach_vitA_no_fat",
    surface_claim="Eat fat-free spinach salad for vitamin A to prevent deficiency disease",
    verb_class="disease_claim",
    nutrient="beta_carotene",
    surface_verb="prevents",
)

for packet_id in ("ex.spinach_salad.zero_fat", "ex.spinach_salad.with_oil"):
    result = audit_claim(claim, get_packet(packet_id))
    print(f"\n--- {packet_id}")
    print("verdict        :", result.verdict)
    print("gate_check     :", result.gate_check)
    print("closed_through :", result.l1_to_l5.get("closed_through"))
    print("laws           :", result.law_refs)
    for level in ("L1", "L2", "L3", "L4", "L5"):
        if level in result.l1_to_l5:
            print(f"  {level}: {result.l1_to_l5[level]}")
```

## Two teaching points, not one

**First:** the zero-fat salad returns `Busted`, closed through **L3**. The panel
number is real — the carotenoid is in the leaf — but the micellar path needs a
lipid phase (LAW-020), and the absorbed cargo leaves the enterocyte by chylomicron
(LAW-045). No lipid, no path. This is a categorical failure, not a small number.

**Second, and less obvious:** adding the oil does *not* make the claim true.

```python
result = audit_claim(claim, get_packet("ex.spinach_salad.with_oil"))
print(result.verdict, "at", result.l1_to_l5["closed_through"])
print(result.gate_note)
```

The gate now passes, but the verdict is `UNEVALUABLE` closed through **L5**. A
single meal path cannot carry a disease-prevention endpoint. Fixing the mechanism
earns you the mechanism, nothing further.

!!! note "This is the anti-tunnel rule"
    The constitution forbids L1→L5 tunnelling — jumping from a food to a disease
    slogan without the intervening mechanism. Here it is enforced in code: even a
    mechanically sound meal returns `UNEVALUABLE` for a disease claim.

## Reframe the claim and watch it change

Same packet, same food, weaker verb:

```python
mechanism_claim = Claim(
    id="claim.spinach_carotenoid_mechanism",
    surface_claim="Adding oil to this salad raises carotenoid bioavailability",
    verb_class="bound_increase",
    nutrient="beta_carotene",
)
result = audit_claim(mechanism_claim, get_packet("ex.spinach_salad.with_oil"))
print(result.verdict, "|", result.gate_check, "|", [f.direction for f in result.bound_findings])
```

The mechanism claim is `Plausible`. The disease claim is not. The food did not
change — the claim did. That is the whole lesson.

## Exercise

1. What would the verdict be if a packet declared no lipid field at all? Try
   `get_packet("ex.kale.raw")`. Explain why the answer differs from 0 g.
2. LAW-045's gate text mentions abetalipoproteinemia. Should host genotype be a
   packet field, a persona field, or neither?
3. Find a marketed "fat-free" product whose panel advertises a fat-soluble vitamin.
