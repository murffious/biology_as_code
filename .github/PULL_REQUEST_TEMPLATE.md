<!--
Target `dev` unless this is a hotfix. See CONTRIBUTING.md → Branches.
Adding or changing a pathway graph? Open the PR with ?template=pathway.md instead.
-->

## What changed

<!-- One paragraph. What, and why it belongs in this repository. -->

## Checks I ran locally

- [ ] `ruff check src tests --exclude tests/_legacy_test_pathways_source.py`
- [ ] `./.venv/bin/python -m pytest tests/ -q`
- [ ] `PYTHONPATH=src python3 scripts/check_pathway_integration.py` (if pathways touched)
- [ ] `python3 tools/check_pmids.py --strict` and committed the refreshed `tools/pmid_cache.json` (if a citation was added)
- [ ] Rebased onto `dev` and re-ran the suite afterwards

## Invariants

- [ ] No runtime dependency added (`dependencies = []` untouched)
- [ ] No number without a source; no citation invented; missing data stays `OPEN`/`UNEVALUABLE`
- [ ] Nothing from the product side (score weights, vendor variables, human rows)
