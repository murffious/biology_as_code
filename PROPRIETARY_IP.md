# Proprietary IP — keep out of git

> **Status note — under review, August 2026.** The project owner operates no
> commercial implementation of this specification. Product identifiers have been
> removed from `src/` and `tests/` and a CI gate now keeps them out (see
> `design/BASELINE.md`). **Disposition of the patent claims described below is a
> pending legal decision.** This document is retained unchanged pending that
> decision — it is not evidence of an active commercial program, and nothing
> here should be read as having been withdrawn. Paths named below that pointed
> into the package were updated where the code moved; the substantive terms are
> untouched.

**Product MEAL score** and **Kibo-vars product scorer** are patent-pending.  
They must **never** be committed to this public companion repository.

## Allowed in git (open)

| Kind | Examples |
|------|----------|
| Dig / FLOW sim | residual, enzymes, SCFA, minerals, pathway_regulation |
| Claim evaluation | support / partial / refuse fixtures |
| Law register data | LAW ids, system-bound JSON |
| Schemas & food examples | `schemas/`, `examples/foods/` |
| Open score **hooks** only | `scoring/interface.py`, `loader.py` (returns unavailable) |
| Teaching FLOW meters | energy_charge, soft dig meters (labeled not product meal score) |

## Forbidden in git (proprietary)

| Kind | Examples |
|------|----------|
| Product meal score algorithm | weights, composite formula, tier cutoffs for product |
| Kibo-vars **product** scorer | private weighted K-var production engine |
| Drop-in engines | any module named by `BAC_SCORER_MODULE` |
| Private packages | `kibo_product_score/`, private wheels |
| Score system product PDFs | `Kibo_Score_System_Book.pdf` formula dumps |

## How private code loads (local only)

```bash
# never commit these files
export BAC_SCORER_MODULE=my_private.module
```

The in-package `product_score/proprietary/` slot no longer exists: an external
scorer is now resolved only from `BAC_SCORER_MODULE`, so private code has no
directory inside this repository to be dropped into by accident.

Open API always works without them:

```python
from biology_as_code.scoring import run_external_score_analysis
run_external_score_analysis(enabled=False)  # dig still runs
```

## Verify before push

```bash
# should print nothing dangerous
git status
# the separation gate must return nothing:
grep -riE "kibo|mealcoach|morf" src/ tests/ && echo FAIL || echo OK clean
```

CI runs that same gate on every push (`.github/workflows/ci.yml`, job
`separation`), and `scripts/release_check.sh` fails the build if a private
scorer is ever tracked.
