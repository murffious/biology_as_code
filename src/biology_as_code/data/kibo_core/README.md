# `kibo_core`

Laws · 7 systems · geography K1–K7 · pathway walks · compartmental FLOW sim.

**Full doc:** [../docs/KIBO_CORE.md](../docs/KIBO_CORE.md)

```bash
cd book/kibo_simulator_latest
PYTHONPATH=. python3 -m kibo_core.demo
PYTHONPATH=. python3 -m unittest kibo_core.tests.test_kibo_core -v
```

```python
from kibo_core import load_system_bound_registry, MetabolicSimulator, MetabolicState
reg = load_system_bound_registry()
sim = MetabolicSimulator().run(MetabolicState(fat_g=40, ascorbate_same_meal=True))
```

| Path | Role |
|------|------|
| `systems.py` | Functional systems |
| `geography/` | Kingdoms + organ bounds |
| `laws/` | Registry, walk, atomic, QA |
| `pathways/` | Iron, quality, cascade |
| `sim/` | FLOW engine |
| `topics/` | Topic → sim map |
| `data/` | JSON laws & paths |
