#!/usr/bin/env bash
# Local pre-PyPI checklist
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== install dev tools =="
python3 -m pip install -q -e ".[dev]" build twine

echo "== tests =="
python3 -m pytest tests/test_public_api.py tests/test_quiet.py tests/test_fixtures_packaged.py -q
PYTHONPATH=src python3 tests/test_pathway_packs.py
PYTHONPATH=src python3 scripts/check_pathway_integration.py

echo "== proprietary guard =="
if git ls-files | grep -E 'product_score/proprietary/engine|kiboScoreModel\.private'; then
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
from biology_as_code import simulate_meal, __version__, list_pathways
from biology_as_code.data.fixtures import list_meal_ids, load_meal
assert __version__ == "0.1.0"
assert len(list_pathways()) >= 10
assert list_meal_ids()
m = load_meal(list_meal_ids()[0])
assert m and "kibo_score" not in str(m)
r = simulate_meal(carbs_g=40, protein_g=20, fats_g=12, fiber_g=10)
assert r.absorbed_macros_g
print("wheel smoke OK", __version__, "pathways", len(list_pathways()), "meals", len(list_meal_ids()))
PY
deactivate
rm -rf .venv-release-check

echo ""
echo "Release check passed. Next:"
echo "  twine upload --repository testpypi dist/*"
echo "  twine upload dist/*"
