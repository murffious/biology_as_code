# New pathway PR checklist

Copy this into the PR description and fill every box.  
Guide: [docs/python/ADD_PATHWAY.md](../ADD_PATHWAY.md)

## Identity

| Field | Value |
|-------|--------|
| Pathway `name` (snake_case) | `________________` |
| Module path | `src/biology_as_code/pathways/________.py` |
| New module or extend existing? | new / extend |
| Clinical or teaching hook (one line) | |
| Links to existing graphs (if any) | e.g. `urea_cycle` |

## Code

- [ ] Graph built (`nodes` + `edges`); endpoints valid
- [ ] `description` written (FLOW teaching, not medical advice claim)
- [ ] `references` listed **or** explicitly “topology-only / textbook standard”
- [ ] `get_*_registry()` factory + `list_all` or `.pathways`
- [ ] Wired in `pathways/registry.py` → `pathway_loaders()` **only**
- [ ] No directory that shadows a `.py` name

## Mechanisms (if used)

- [ ] N/A — no `mechanism_id` on edges
- [ ] New ids registered in `metabolic_mechanisms.py`
- [ ] Every edge `mechanism_id` resolves

## Export & mermaid

- [ ] Ran `PYTHONPATH=src python3 scripts/export_pathway_packs.py`
- [ ] `packs/<name>/pathway.mermaid` present (`flowchart` + edges)
- [ ] `packs/<name>/tests.md` + `README.md` present
- [ ] Did **not** hand-edit auto mermaid

## Docs

- [ ] `packs/COVERAGE.md` row added / textbook gap updated
- [ ] `CHANGELOG.md` entry (if release-facing)
- [ ] README “what's inside” (optional)

## Tests

- [ ] Discoverable: `get_pathway("<name>")` works
- [ ] Dedicated test file **or** invariants covered by existing suite
- [ ] `PYTHONPATH=src python3 tests/test_pathway_packs.py` passes
- [ ] `PYTHONPATH=src python3 scripts/check_pathway_integration.py --pathway <name>` exits 0

## Boundaries

- [ ] No product meal score / vendor-variable / proprietary engine
- [ ] No invented citations or fabricated magnitudes
- [ ] Zero new runtime dependencies

## Reviewer notes

_What should a reviewer look at first? Teaching point? Clinical enzyme? Link to urea?_

```
…
```
