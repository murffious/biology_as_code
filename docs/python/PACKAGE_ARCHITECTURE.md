# Package architecture judgment

**Package name:** `biology_as_code` (not `metabolic`)  
**Brand:** Biology as Code / KIBO dig FLOW  
**Audience:** engineers running food → dig → pathways → claims

## Is the ODE-style ABC rework worth it?

**No — not as a forced rewrite of the existing stack.**

| Proposed ABC surface | Our real code | Verdict |
|----------------------|---------------|---------|
| `Molecule` + concentrations (mM) | Teaching graph nodes + meal macros | Different job |
| `Reaction` + rate laws / Km Vmax | `ReactionEdge` + optional `mechanism_id` | Graph, not ODE |
| `Pathway.get_stoichiometry_matrix()` | Registry graphs with textbook nets | Not required for dig |
| `Simulator.run(duration, dt)` | `KIBOEngine.simulate_payload(meal)` | Discrete meal compile, not time-step ODE |

Doing that rework would mean **renaming everything, dual-maintaining two models, and still not improving** meal residual / SCFA / claim honesty. Hassle ≫ value.

## What *is* worth doing (structural only)

1. **`src/` layout** with folders by role: `pathways/`, `dig/`, `simulation/`, `data/`, `bridge/`  
2. **Keep existing module names** (`metabolic_pathways.py`, `kibo_engine.py`, …)  
3. **Thin public API** in `__init__.py` — `simulate_meal`, pathway registry, scenarios  
4. **Optional protocols** in `core/base.py` that *describe* what we already have (not force scipy ODEs)  
5. **Product meal score / Kibo-vars scorer** stay out-of-tree (`product_score` stub only)

## Folder map (adapted from “metabolic” sketch)

```text
src/biology_as_code/
  core/           # protocols + light helpers (not a second engine)
  pathways/       # existing pathway modules (names kept)
  dig/            # GI transit, enzymes, residual, vitamins/minerals
  simulation/     # kibo_engine, physiological_state, scenarios
  data/           # fixtures, vitamins, kibo_core laws
  models/         # ontology / causal helpers
  bridge/         # LAW-tagged GI + iron walk
  product_score/  # open hook only (patent-pending engine gitignored)
  visualization/  # mermaid helpers (optional)
  utils/
  agents/         # reserved, empty
```

## When to revisit full ABCs

Only if you later add a **true kinetic subpackage** (`biology_as_code.kinetic`) with ODE solvers. Keep it **separate** from dig FLOW so names stay honest.
