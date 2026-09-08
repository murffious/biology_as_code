#!/usr/bin/env bash
# Local pre-PyPI checklist
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== install dev tools =="
python3 -m pip install -q -e ".[dev]" build twine

echo "== tests =="
# Full suite, same as CI. This once ran three files, which is how a green
# release check and a red CI run could describe the same tree.
python3 -m pytest tests/ -q
PYTHONPATH=src python3 tests/test_pathway_packs.py
PYTHONPATH=src python3 scripts/check_pathway_integration.py

echo "== proprietary guard =="
if git ls-files | grep -E 'proprietary/|scoreModel\.private|_product_score_engine'; then
  echo "FAIL: proprietary files tracked"
  exit 1
fi
echo "OK no proprietary engines tracked"

echo "== build =="
rm -rf dist build *.egg-info src/*.egg-info
python3 -m build
twine check dist/*

echo "== wheel smoke =="
python3 -m venv .venv-release-check
# shellcheck disable=SC1091
source .venv-release-check/bin/activate
pip install -q dist/*.whl
python - <<'PY'
import tomllib
from biology_as_code import simulate_meal, __version__, list_pathways
from biology_as_code.data.fixtures import list_meal_ids, load_meal
# Agreement with pyproject, not a pinned string: the pin ("0.1.0") stayed
# behind when 0.2.0 and 0.2.1 shipped, so this script has failed on every
# release since without anyone noticing, because CI has its own smoke test.
with open("pyproject.toml", "rb") as f:
    declared = tomllib.load(f)["project"]["version"]
assert __version__ == declared, (__version__, declared)
assert len(list_pathways()) >= 10
assert list_meal_ids()
m = load_meal(list_meal_ids()[0])
assert m and "flow_score" not in str(m)
r = simulate_meal(carbs_g=40, protein_g=20, fats_g=12, fiber_g=10)
assert r.absorbed_macros_g
print("wheel smoke OK", __version__, "pathways", len(list_pathways()), "meals", len(list_meal_ids()))
PY
deactivate
rm -rf .venv-release-check

echo ""
echo "Release check passed. Next: tag and publish a GitHub Release from main;"
echo "publish.yml uploads to PyPI and versions the Zenodo record on the release event."
echo "Manual uploads bypass the separation gate — see docs/python/PUBLISHING.md."
