<!--
Use this template when adding or substantially changing a teaching pathway graph.
Full guide: docs/python/ADD_PATHWAY.md
Fill: docs/python/templates/NEW_PATHWAY_CHECKLIST.md (paste below or attach).
-->

## Summary

<!-- One paragraph: what process, why it belongs, teaching/clinical hook. -->

## Pathway identity

- **Name (`snake_case`):** 
- **Module:** `src/biology_as_code/pathways/`
- **New module / extend existing:** 

## Integration (required)

- [ ] Wired in `pathways/registry.py` → `pathway_loaders()` only
- [ ] `PYTHONPATH=src python3 scripts/export_pathway_packs.py`
- [ ] Pack present: `pathways/packs/<name>/{pathway.mermaid,tests.md,README.md}`
- [ ] `packs/COVERAGE.md` updated
- [ ] Tests added/updated
- [ ] `PYTHONPATH=src python3 scripts/check_pathway_integration.py --pathway <name>` → exit 0
- [ ] `PYTHONPATH=src python3 tests/test_pathway_packs.py` → pass
- [ ] Real references only (or topology-only, stated)
- [ ] No product score / proprietary / invented magnitudes

## Checklist paste

<!-- Paste filled NEW_PATHWAY_CHECKLIST.md here -->

## Test plan

```bash
PYTHONPATH=src python3 scripts/check_pathway_integration.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```
