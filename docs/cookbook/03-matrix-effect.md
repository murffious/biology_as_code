# Lab 3 — The matrix effect

**Question for students:** almonds and almond flour have the same ingredient list.
Do they behave the same in the gut?

This lab has no gate in it at all. It is a pure bound story driven by physical
form — the case where a nutrition-facts panel is *least* informative.

## The pair

```python
from biology_as_code.packets import get_packet

for packet_id in ("ex.almond.whole", "ex.almond.flour"):
    packet = get_packet(packet_id)
    print(packet.common_name)
    print("  cargo    :", packet.cargo_nutrients())
    print("  integrity:", packet.matrix_integrity)
    print("  notes    :", packet.matrix.get("notes"))
```

Identical cargo. The difference is recorded in `matrix.integrity`: `intact` for
the whole nut, `destroyed` for the flour.

## Audit both

```python
from biology_as_code import Claim, audit_claim

claim = Claim(
    id="claim.matrix_form",
    surface_claim="Food form changes lipid accessibility",
    verb_class="bound_increase",
    nutrient="lipid",
)

for packet_id in ("ex.almond.whole", "ex.almond.flour"):
    result = audit_claim(claim, get_packet(packet_id))
    directions = [f.direction for f in result.bound_findings]
    print(f"{packet_id:20s} {result.verdict:10s} {directions} {result.law_refs}")
```

Expected:

```text
ex.almond.whole      Plausible  ['NARROWS_BOUND'] ('LAW-024',)
ex.almond.flour      Plausible  ['EXPANDS_BOUND'] ('LAW-024',)
```

## The teaching point

LAW-024 states that food form and fibre viscosity govern gastric emptying and the
*rate* of absorption. The intact cell wall encapsulates intracellular lipid, so
the accessible fraction is lower. Milling removes that barrier.

Nothing about the panel changes. Calories, fat grams, protein — all identical. The
variable that moved is not in the panel at all.

!!! warning "Why this matters for scoring systems"
    Any nutrient-profiling model that reads only a panel cannot distinguish these
    two foods. Whatever score it emits will be the same for both. That is a
    structural limit of panel-based scoring, not a tuning problem.

## Unknown is not intact

Most packets in the repository do not declare matrix integrity:

```python
from biology_as_code.packets import iter_packets
from collections import Counter

print(Counter(p.matrix_integrity for p in iter_packets()))
```

Those `unknown` packets produce no matrix finding at all — the auditor does not
assume an intact default. A missing declaration yields silence, not a guess.

## Exercise

1. `ex.orange.whole` and `ex.orange.juice` are the same physical pair as the
   almonds. Both are stubs. Fill in their `matrix` blocks and re-run this lab.
2. `ex.oats.porridge.plain` and `ex.oat.flour.gruel` are a third such pair. Which
   law would you cite for a viscosity claim, and does the register support it?
3. LAW-024 covers *rate*. Does rate alone justify a claim about total absorbed
   lipid over a day? Where does that argument break?
