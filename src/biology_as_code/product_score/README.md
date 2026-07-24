# Optional product meal-score + Kibo-vars scorer (patent pending)

**Not part of open dig.** Digestion still evaluates claims and FLOW scores without this.

## What this plugin is for

| Proprietary (this module) | Open dig (always allowed) |
|---------------------------|---------------------------|
| Product **MEAL score** (commercial composite) | Residual, enzymes, SCFA, minerals |
| **Kibo vars** product weighted scorer | pathway_regulation activities 0–1 |
| Product tier / badge from secret formula | Claim support \| partial \| refuse |
| | Process *measurements* as dig telemetry |
| | Teaching energy_charge / FLOW meters |

Open dig **may score and evaluate** all day.  
It must **not** emit the product meal score or Kibo-vars product stack unless this private plugin is installed and enabled.

## Open vs private files

| Path | Role |
|------|------|
| `interface.py` / `loader.py` | **Open** — contracts + optional load |
| `proprietary/engine.py` | **Private** — gitignored patent-pending math |
| pip `kibo_product_score` | **Private** install alternative |

## Enable proprietary analysis

```bash
export KIBO_PRODUCT_SCORE_MODULE=my_private.score_engine
# or
cp /secure/engine.py product_score/proprietary/engine.py
```

Private module:

```python
def get_analyzer():
    return MyAnalyzer()  # .analyze(request) -> ProductScoreResult | dict
```

## API

```python
from product_score import run_product_score_analysis, product_score_available

# Open path: dig ran; product score skipped
run_product_score_analysis(depth_report=report, enabled=False)
# → available: false, status: disabled_by_caller

# Product path: only if private engine present
run_product_score_analysis(depth_report=report, enabled=True)
```

`kibo_engine` / `unified_facade` default **`enable_product_score=False`**.
