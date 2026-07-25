# Digestion engine — food handled under conditions

`digest(food, conditions) → DigestionTrace` answers the question the whole project
started from: **once a food is standardized, how does the body handle it, and under
what conditions?**

It is the [claim auditor](claim-auditor.md)'s sibling. The auditor answers *is a
claim true*; `digest` answers *what does the body do*. Both walk the same
gate/bound physiology.

```python
from biology_as_code import digest, Conditions

digest("ex.spinach_salad.zero_fat").summary
# 'beta_carotene: transport gate CLOSED — path shut (LAW-020, LAW-045) | …'
```

## The four seats — `Conditions`

The constitution reads every law from four seats. `Conditions` gathers them into one
input, so the **same standardized food** can be handled differently:

| Seat | Field | Example |
|---|---|---|
| **Host** | `host` | `Conditions(host={"bileCapacity": 0.3})` — cholestasis |
| **Partner** | `partners` | `Conditions(partners={"tea_tannins": True})` — you also drank tea |
| **Stage** | `stage` | life stage / where on L1→L5 attention sits |
| **Clock** | `clock` | `fed` / `fasted` |

```python
base    = digest("ex.lentils.with_ascorbate")
with_tea = digest("ex.lentils.with_ascorbate", Conditions(partners={"tea_tannins": True}))

base.summary      # nonhaem_iron: path open; bound EXPANDS_BOUND (ascorbate) (LAW-004)
with_tea.summary  # …EXPANDS_BOUND (ascorbate), NARROWS_BOUND (tea) (LAW-004, LAW-006)
```

Same packet. A Partner-seat condition changes the handling, with the law citations to
back it. That is the entire thesis, executable.

## Two layers, honestly tiered

A `DigestionTrace` carries both:

- **Machine layer (teaching-FLOW)** — the food runs through the full-digest state
  machine; the trace records the `path` (oral→…→colon), the **`events`** each stage
  emits, and the `fired_edge_cases`.
- **Handling layer (fail-closed, law-backed)** — each cargo nutrient is evaluated
  against the gate/bound table. A gate whose required co-factor is **undeclared** is
  `UNEVALUABLE`, never a default pass. Silence is not a zero.

## Events — the extension point

Every stage `emits` typed events (`micelles`, `fat-soluble-vehicle`,
`stage:stage.oral`). `trace.events` is that stream. The ordered digestion flow is a
state machine; the *non-linear* parts of physiology (hormonal signaling, feedback
loops, cross-system reactions) are naturally **event-driven** — a subscriber layer can
sit on top of this event stream. In the AWS model below, that is Step Functions →
EventBridge → fan-out.

## The Step Functions model → ASL export

The machines were authored Step-Functions-style, so they compile almost 1:1 to
**Amazon States Language**. This is a **concept and an artifact, not a deployment** —
the exporter is pure, offline, and never calls AWS:

```bash
python scripts/export_step_functions.py                 # write dist/asl/*.json
python scripts/export_step_functions.py --food ex.spinach_salad.zero_fat
```

- `machine_to_asl` compiles one machine → an ASL state machine (`task`→`Pass`, or a
  nested `Task` for a stage; `choice`→`Choice`; `succeed`→`Succeed`; predicates →
  `NumericLessThan` / `And` / `Or` / `Not`).
- `food_to_input(food, conditions)` produces the nested execution input the ASL reads
  as `$.meal.fatG`.

The local runtime stays `biology_as_code.machines.trace`; the ASL export just proves
the mapping and hands you deployable JSON if you ever want it. See
[`scripts/export_step_functions.py`](https://github.com/murffious/biology_as_code/blob/main/scripts/export_step_functions.py).
