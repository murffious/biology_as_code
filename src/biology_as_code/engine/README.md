# `engine`

Laws · 7 systems · geography K1–K7 · pathway walks · compartmental FLOW sim.

**Full doc:** [../docs/ENGINE_CORE.md](../docs/ENGINE_CORE.md)

```bash
cd book/simulator_latest
PYTHONPATH=. python3 -m engine.demo
PYTHONPATH=. python3 -m unittest engine.tests.test_engine -v
```

```python
from engine import load_system_bound_registry, MetabolicSimulator, MetabolicState
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
