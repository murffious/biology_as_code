# Glycolysis — gold pathway pack

This folder is the **template** for structured pathway documentation.

| File | Role |
|------|------|
| `glycolysis.mermaid` | Full teaching flowchart (investment / split / payoff) |
| `glycolysis-compact.mermaid` | Compact LR form |
| `glycolysis-w-id.mermaid` | Edges labeled with `mechanism_id` |
| `glucose.mermaid` | Broader glucose context |
| `tests.md` | Accuracy audit + structural / biochemical checklist |

## Same pattern for all pathways

Auto packs (mermaid + tests.md) for every registry graph:

→ [`../pathways/`](../pathways/) · index [`../pathways/INDEX.md`](../pathways/INDEX.md)

```bash
cd biology_as_code
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```

Python model: `biology_as_code.pathways.metabolic_pathways`  
Mechanisms: `biology_as_code.pathways.metabolic_mechanisms`
