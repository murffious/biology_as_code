# Lab 1 — Gate vs Bound

**Question for students:** two meals contain the same iron. One is absorbed
better. Is that because a *path opened*, or because a *ceiling moved*?

Getting this wrong is the most common modelling error in nutrition software. It
produces systems that report "no absorption" when they mean "less absorption."

## The pair

Two packets, identical non-haem iron cargo, differing only in one partner field.

```python
from biology_as_code.packets import get_packet

for packet_id in ("ex.lentils.with_ascorbate", "ex.lentils.with_tea"):
    packet = get_packet(packet_id)
    print(packet.common_name)
    print("  cargo   :", packet.cargo_nutrients())
    print("  partners:", {p["field"]: p["value"] for p in packet.partners})
```

Both declare `nonhaem_iron`. Neither declares a different amount. The only
difference is the company the iron keeps.

## Audit both

```python
from biology_as_code import Claim, audit_claim

claim = Claim(
    id="claim.iron_bound",
    surface_claim="This meal changes absorbable non-haem iron",
    verb_class="bound_increase",
    nutrient="nonhaem_iron",
)

for packet_id in ("ex.lentils.with_ascorbate", "ex.lentils.with_tea"):
    result = audit_claim(claim, get_packet(packet_id))
    print(f"{packet_id:28s} gate={result.gate_check:5s} verdict={result.verdict}")
    for finding in result.bound_findings:
        print(f"   {finding.direction:15s} {finding.law_refs} — {finding.note}")
```

Expected output:

```text
ex.lentils.with_ascorbate    gate=pass  verdict=Plausible
   EXPANDS_BOUND   ('LAW-004',) — ascorbate reduces and chelates Fe, ...
ex.lentils.with_tea          gate=pass  verdict=Plausible
   NARROWS_BOUND   ('LAW-006',) — tea/coffee tannins bind Fe and reduce ...
```

## The teaching point

`gate=pass` **in both cases.** The transporter path was never shut. Ascorbate
and tannin move the ceiling in opposite directions, and the auditor reports a
signed direction — not a number.

That restraint is deliberate. Direction is what the law supports; magnitude is an
evidence question that depends on dose, matrix, and host iron status. A system
that prints "38% more iron absorbed" here is inventing precision it does not have.

## Contrast: what a real gate looks like

```python
from biology_as_code.audit import gates_for, bounds_for

print("iron gates :", gates_for("nonhaem_iron"))
print("iron bounds:", [(r.triggered_by, r.direction) for r in bounds_for("nonhaem_iron")])
print()
print("carotenoid gates:", [(r.requires, r.law_refs) for r in gates_for("beta_carotene")])
```

Non-haem iron has **no** gate rule — only bound rules. Beta-carotene has a gate
requiring `dietary_lipid_g`. The register itself draws this line: LAW-047
describes calcium's effect on iron as "a magnitude effect, not a categorical gate
like fat for micelles."

## Exercise

1. Add a `calcium_same_meal: true` partner to a copy of the ascorbate packet.
   Which laws now fire, and do they cancel?
2. LAW-004 says ascorbate "can overcome inhibitors such as tea tannin." The
   auditor currently reports both directions independently and does not resolve
   the conflict. Is reporting `['EXPANDS_BOUND', 'NARROWS_BOUND']` the honest
   answer, or should the table encode precedence? Argue both sides.
3. Find a supplement label that treats an iron bound as though it were a gate.
