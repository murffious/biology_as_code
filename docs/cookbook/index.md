# Cookbook

Four self-contained labs built on the packets and laws that ship with the
repository. Each one runs against real code — no pseudocode, no placeholder
numbers — and each ends with exercises that have arguable answers rather than
lookup answers.

| Lab | Mechanism | What it teaches |
| --- | --- | --- |
| [1. Gate vs Bound](01-gate-vs-bound.md) | non-haem iron + ascorbate / tannin | A ceiling moving is not a path opening. |
| [2. The fat-vehicle gate](02-fat-vehicle-gate.md) | carotenoids + dietary lipid | A categorical gate, and why fixing it does not license a disease claim. |
| [3. The matrix effect](03-matrix-effect.md) | whole almond vs almond flour | The variable that moved is not on the panel. |
| [4. Auditing a real claim](04-claim-audit.md) | a marketing sentence | Refuse first, then trace. |

## Running them

Every code block executes as written from a repository checkout:

```bash
git clone https://github.com/murffious/biology_as_code
cd biology_as_code
pip install -e ".[dev]"
```

Food packets live in `examples/foods/` and are resolved from the checkout, so
these labs need the repo rather than just the wheel.

Notebook versions for Colab and classroom use are generated from these pages into
`notebooks/`, so there is one source of truth:

```bash
python scripts/build_notebooks.py
```

`tests/test_cookbook.py` executes every code block in CI, so a lab cannot drift
from the API without turning the build red.

## Suggested sequence for a course

Labs 1–3 are the mechanism trio and work in any order, though 1 before 2 makes the
Gate ≠ Bound contrast land harder. Lab 4 assumes all three.

For a single 90-minute session, Lab 1 plus Lab 4 covers the argument end to end:
the distinction that matters, then the tool that enforces it.
