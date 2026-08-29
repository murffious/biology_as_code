# Bridge

Product API → `engine` (LAW-tagged GI, FLOW sim, iron walk).

**Full doc:** [../docs/BRIDGE.md](../docs/BRIDGE.md)

```bash
cd book/simulator_latest
PYTHONPATH=. python3 -m unittest bridge.tests.test_bridge -v
```

| File | Role |
|------|------|
| `bridge_engine.py` | Main bridge |
| `tests/test_bridge.py` | Tests |
| `module_test.py` | Legacy exercises |

Prefer `meal_engine` for full depth meal sim; use bridge when you need law ids + core FLOW.
