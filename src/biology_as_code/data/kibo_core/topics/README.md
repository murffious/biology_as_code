# Topics → simulation representation

Converts the encyclopedia **topic vocabulary** (`list.topics.md`, frozen reference) into typed nodes the simulator can use.

## Pipeline

```
list.topics.md (reference, do not edit)
        │  build / re-run classifier
        ▼
data/topics_ontology.json   (~1450 terms, auto-classified)
        │
        ▼
topics/registry.py          TopicRegistry
topics/sim_map.py           context templates + role meanings
        │
        ▼
sim MetabolicState.context / WalkState.context
laws LAW-### links where known
```

## Sim roles (representation)

| Role | Simulation meaning | Example |
|------|--------------------|---------|
| `cargo` | Amount / relative pool | Iron, glucose, leucine |
| `modifier` | Context flag or factor | Phytate, tannin, caffeine |
| `signal` | Hormone 0–2 scale | Insulin, CCK, cortisol |
| `mechanism` | Enzyme / transporter in a phase | Amylase, LPL, DMT1 |
| `process` | Named pathway process | Glycolysis, ketogenesis |
| `compartment` | Geography seat | Colon, liver, adipocyte |
| `endpoint` | Outcome node (open tier) | Scurvy, T2D — **not auto-diagnosed** |
| `measurement` | Assessment method | BMI equation, DLW |
| `host_context` | Population / life stage | Pregnancy, elderly |
| `payload_food` | Food identity | Milk, wheat |
| `lexicon` | Vocabulary only (most terms) | Until a law/slot exists |

## Status

| Status | Meaning |
|--------|---------|
| `mapped` | Has LAW-### / STUB link |
| `sim_stub` | Has sim role + system, no law yet |
| `lexicon` | Named term; no sim physics |

## Usage

```python
from kibo_core.topics import load_topics, build_sim_context_template, topics_linked_to_law

reg = load_topics()
print(reg.summary())
# {'n': 1455, 'mapped': 167, 'sim_stub': 183, ...}

for t in topics_linked_to_law("LAW-004"):
    print(t.label, t.field_hint)

ctx = build_sim_context_template()  # core keys for sim/walk
ctx["ascorbate_same_meal"] = True
```

## Rebuild ontology from the list (dev only — not in the pip wheel)

```bash
# from biology_as_code repo root
python tools/topics_build/build_from_list.py
```

Scripts live under `tools/topics_build/` so an installed package cannot clobber
`topics_ontology.json` by accident.

## Honesty

- Auto-classification is **heuristic** — refine high-value terms by hand.  
- Endpoints never auto-diagnose.  
- Magnitudes stay open unless a law locks them.  
- Source file stays frozen under `biology_as_code_nutrition_intelligence-main/`.
