# Contributing

Two kinds of contribution, one constitution. A third path is **teaching pathways**
(graphs + mermaid packs) with a fixed integration template.

## Branches

`main` is what ships. `dev` is the integration branch: open your pull request
against `dev` unless it is a hotfix.

    git switch dev && git pull
    git switch -c feat/thing
    ...
    gh pr create --base dev

**Both are watched by CI.** That matters more than it sounds. Ten pull requests
once sat open here with no checks at all, because they targeted feature branches
while `.github/workflows/ci.yml` only listened on `[main, master]`. Every one was
red and the pull request UI showed nothing. If you ever add another branch that
people merge into, add it to the `on:` lists in `ci.yml` and `docs.yml` in the
same commit, or you have rebuilt that trap.

Two rules that follow from the same incident:

- **Do not target a feature branch.** Stack by rebasing onto `dev`, not by
  pointing one pull request at another branch.
- **Run the suite after any rebase.** A rebase onto a squash-merged parent
  applies cleanly and can still break the build, because the parent's history no
  longer matches its contents. `git rebase` succeeding is not a green check.

Merged branches delete themselves. Before this was switched on they accumulated
until nobody could tell which were live.

**Both branches take changes only through a pull request with green checks.** A
repository ruleset (`ci-required`) enforces it: a direct push to `main` or `dev`
is refused, and a pull request cannot merge until the separation gate, the three
Python test jobs, coverage, and the docs build all report. Repository admins can
bypass on a pull request for a genuine emergency; the bypass is recorded on the
PR, so use it as the audit trail it is. No approving review is required — a
solo maintainer cannot approve their own PR — so the checks *are* the review.

### Hotfixes and the sync back

A hotfix goes to `main` on its own branch (`fix/...`, `gh pr create --base main`).
The moment it merges, `dev` is behind, and the next feature PR will carry a
conflict nobody authored. Sync immediately:

    gh pr create --base dev --head main --title "sync: main → dev"

The sync PR is a fast-forward and its checks are already green on the same
commits; merge it as soon as they re-report. This happened once already
(`f0199c8` sat on `main` alone) and was caught by hand.

### Releasing

`dev` → `main` is a pull request like any other (`gh pr create --base main
--head dev`). After it merges, run `scripts/release_check.sh` on `main`, bump
`version` in `pyproject.toml`, `CITATION.cff` and
`src/biology_as_code/data/VERSION_MANIFEST.json` together (`__version__` is read from
the manifest, not from package metadata; the CI wheel smoke fails if the two disagree), move the
`[Unreleased]` section of `CHANGELOG.md` under the new version, tag `vX.Y.Z`, and
publish a GitHub Release from the tag. The release event is what runs
`publish.yml` (PyPI + a new Zenodo version); a push never does.

## Data — strengthen the register

Evidence, packet fills, claims, and gate/bound rules go through a **fail-closed
gate**: an unsourced magnitude can never be promoted, so the crowd can only
strengthen the register. This is the highest-leverage way to help.

→ See [**docs/contributing-data.md**](docs/contributing-data.md). No code required;
you add one small JSON file and open a PR, or use the
[evidence issue form](../../issues/new?template=evidence.yml).

## Pathways — teaching graphs + mermaid

Adding or extending a metabolic / digestion / sensing **pathway graph** is a
structured workflow: code first, export mermaid, tests, coverage, integration gate.

| Resource | Purpose |
|----------|---------|
| [**docs/python/ADD_PATHWAY.md**](docs/python/ADD_PATHWAY.md) | Full template guide (order of work, anti-patterns) |
| [**docs/python/templates/NEW_PATHWAY_CHECKLIST.md**](docs/python/templates/NEW_PATHWAY_CHECKLIST.md) | Paste into PR body |
| [**docs/python/templates/pathway_module_stub.py**](docs/python/templates/pathway_module_stub.py) | Copy to `src/.../pathways/` |
| `scripts/export_pathway_packs.py` | Regenerate `packs/<id>/pathway.mermaid` |
| `scripts/check_pathway_integration.py` | **Must exit 0** before merge |
| `src/biology_as_code/pathways/packs/COVERAGE.md` | Graphs ↔ modules honesty map |

```bash
pip install -e ".[dev]"
# after editing a graph:
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 scripts/check_pathway_integration.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```

CI runs the same integration check, so a skipped step turns the PR red rather
than slipping through.

**Single wire point:** register loaders only in
`src/biology_as_code/pathways/registry.py` (`pathway_loaders`). Export uses that
list — do not duplicate module lists in the export script.

**Import the graph types, do not redeclare them.** New modules take
`PathwayNodeType` / `MetaboliteNode` / `ReactionEdge` / `MetabolicPathway` from
`pathways/_types.py` and override `summary()` only. The existing 16 modules each
declared their own copies, which is why the exporter silently dropped fields it
did not recognise — see [docs/python/PATHWAY_TYPES_REFACTOR.md](docs/python/PATHWAY_TYPES_REFACTOR.md).
Note the cofactor sign convention documented there: `atp_cost=-1` means ATP
consumed, but `nadh_cost=-1` means NADH *produced*.

Gold example of a complete small addition: `ketolysis.py` + `tests/test_ketolysis.py`.

## Code (general)

```bash
pip install -e ".[dev]"
ruff check src tests --exclude tests/_legacy_test_pathways_source.py
pytest -q
PYTHONPATH=src python3 scripts/check_pathway_integration.py
```

**Use this package's own venv.** There are two in the workspace: the repo-root
`.venv` (cobra/scipy, for the VMH/GEM tooling in `tools/`) has **no pytest**, so
running the suite from it looks like the tests are missing rather than unrun. Work
on `biology_as_code` from `biology_as_code/.venv`:

```bash
./.venv/bin/python -m pytest tests/ -q
```

CI runs the full suite + ruff on 3.11 / 3.12 / 3.13 and builds the wheel. Keep it
green.

### Invariants that must not drift

These are the brand, enforced by tests — a PR that breaks one turns CI red:

- **Zero runtime dependencies.** `dependencies = []` stays empty. Anything heavier
  is a `dev` extra.
- **Empty beats fake.** Missing data is `UNEVALUABLE`/`OPEN`, never a default pass
  or a fabricated number. No citation is ever invented.
- **Gate ≠ Bound.** A `GateRule` may only cite laws whose card has
  `gate.present == True`; a `BoundRule` only laws where it is `False`.
- **No magnitude without primary evidence.** Directions are fine; numbers need a
  sourced, verifiable citation (see the [validation ledger](docs/VALIDATION_LEDGER.md)).
- **Pathway packs match the registry.** Every graph has a mermaid pack; no orphan
  packs (`check_pathway_integration.py`).

### The product boundary

The open package is the teaching/auditing engine. The patent-pending **product meal
score and its variables are not part of this repo** — they live behind the gated
`scoring/` hook. Do not add scoring weights, vendor-variable formulas, or a
meal-score implementation here; contributions that do will be declined.
