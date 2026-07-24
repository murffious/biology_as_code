# Proprietary IP — keep out of git

**Product MEAL score** and **Kibo-vars product scorer** are patent-pending.  
They must **never** be committed to this public companion repository.

## Allowed in git (open)

| Kind | Examples |
|------|----------|
| Dig / FLOW sim | residual, enzymes, SCFA, minerals, pathway_regulation |
| Claim evaluation | support / partial / refuse fixtures |
| Law register data | LAW ids, system-bound JSON |
| Schemas & food examples | `schemas/`, `examples/foods/` |
| Open score **hooks** only | `product_score/interface.py`, `loader.py` (returns unavailable) |
| Teaching FLOW meters | energy_charge, soft dig meters (labeled not product meal score) |

## Forbidden in git (proprietary)

| Kind | Examples |
|------|----------|
| Product meal score algorithm | weights, composite formula, tier cutoffs for product |
| Kibo-vars **product** scorer | private weighted K-var production engine |
| Drop-in engines | `product_score/proprietary/engine.py` |
| Private packages | `kibo_product_score/`, private wheels |
| Score system product PDFs | `Kibo_Score_System_Book.pdf` formula dumps |

## How private code loads (local only)

```bash
# never commit these files
export KIBO_PRODUCT_SCORE_MODULE=my_private.module
# or local (gitignored):
# src/biology_as_code/product_score/proprietary/engine.py
```

Open API always works without them:

```python
from biology_as_code.product_score import run_product_score_analysis
run_product_score_analysis(enabled=False)  # dig still runs
```

## Verify before push

```bash
# should print nothing dangerous
git status
git check-ignore -v src/biology_as_code/product_score/proprietary/engine.py
# create a dummy engine and confirm ignored:
touch src/biology_as_code/product_score/proprietary/engine.py
git status --short | grep engine && echo FAIL || echo OK ignored
rm -f src/biology_as_code/product_score/proprietary/engine.py
```

If `git status` shows any `engine.py` under proprietary/, **do not commit**.
