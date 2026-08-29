# Pre-Publish Senior Review — `biology-as-code` 0.1.0

**Scope:** Full audit of the staged (uncommitted) tree before first publish to GitHub + PyPI.
**Reviewed:** packaging, IP/proprietary boundary, public API, all `src/biology_as_code/` subsystems, tests, CI/publish workflows, docs, licenses, and the built wheel/sdist in `dist/`.
**Method:** static review of every subsystem + empirical verification (clean-venv installs on Python 3.10 / 3.11 / 3.13, full test suite, `twine check`, ruff, example scripts, targeted bug repros).

---

## Status: fixes applied & verified (2026-07-23)

**The blocker, all three HIGH items, every MEDIUM, and the low/defensive items below are now fixed and re-verified.** After the changes: `import biology_as_code` + `simulate_meal` work on Python **3.11 / 3.12 / 3.13** (3.10 was **dropped** — it's EOL Oct 2026 — so `requires-python` is now `>=3.11` and pip refuses to install on 3.10); the dig stomach-pH bug and the organ-capacity drift are gone (verified by re-running the exact repros); the wheel no longer ships the dead duplicate or the broken test; ruff is clean; `twine check` passes; 15/15 public tests pass and the engine `gleaned/` tests now **skip** instead of failing. Consciously deferred (with rationale) at the end: M4, L3, L4, L5. See the checklist for the per-item state.

---

## Verdict (original)

**One hard blocker, then go.** The package is well-organized, installs cleanly on Python 3.11+, has a genuinely clean proprietary-IP boundary, quiet/fast imports, an OIDC intent-gated publish flow, and a passing public test suite. **Do not publish as-is only because it cannot be imported on Python 3.10, which its own metadata promises to support.** Fix that plus a couple of correctness/packaging issues and it's ready.

| Area | Status |
|------|--------|
| Proprietary IP boundary (your specific concern) | ✅ **Clean — verified** |
| Installs & runs (Python 3.11 / 3.12 / 3.13) | ✅ Works |
| Installs & runs (Python 3.10, as advertised) | ❌ **BLOCKER — ImportError** |
| Public API correctness | ⚠️ 2 confirmed real bugs (dig pH, organ drift) |
| Packaging / metadata / `twine check` | ⚠️ mostly good; ships a broken embedded test |
| CI + publish workflows | ✅ Strong (OIDC, intent-gated) |
| Docs / licenses | ✅ Accurate and consistent |

---

## IP / Proprietary boundary — PASS (this is the thing you asked me to double-check)

The patent-pending **product MEAL score** / **vendor-variable product scorer** is correctly kept out, gitignored, and optional. Every check passed:

- **Nothing private on disk or staged.** The only files under `scoring/plugin/` are the stubs `__init__.py`, `README.md`, `.gitignore`. No `engine.py` / private scorer exists in the tree.
- **The ignore actually resolves.** `git check-ignore` confirms a dropped `scoring/plugin/engine.py` (and `engine.secret.py`) **is** ignored — the `*` rule in `proprietary/.gitignore` catches it, with explicit un-ignores only for the three stubs.
- **The built wheel carries no algorithm.** `dist/…​.whl` ships only `product_score/{interface,loader,__init__}.py` + `proprietary/{__init__,README}` — a Protocol and an "unavailable" stub. No weights, tier cutoffs, or composite formula anywhere in the wheel.
- **No score fields in data.** 0 occurrences of `flow_score`, `meal_score`, `product_score`, `vendor_vars` (etc.) across all **206** committed JSON files. `data/fixtures/user_personas.py` recursively `_scrub`s ten proprietary keys through every public accessor.
- **Off by default, and fail-closed at runtime.** `MealEngine.enable_external_score = False` by default; and even forcing `run_external_score_analysis(enabled=True)` returns `available: False` with no plugin installed — I confirmed this in a clean install. The test suite pins this (`test_external_scorer_hook_unavailable`, and `"flow_score" not in blob`).
- **Belt-and-suspenders.** `scripts/release_check.sh` fails the build if any `scoring/plugin/engine*` is ever tracked.

**One defensive gap (not a leak):** `user_personas.load_inventory()` returns raw JSON **without** `_scrub`, and `list_personas()` merges it in. No inventory file ships today, so nothing leaks — but if a `user-persona-data-inventory.json` with proprietary keys is ever dropped beside the seed, it would bypass the scrubber. Route `load_inventory` through `_scrub` too.

---

## BLOCKER — must fix before publish

### B1. Package can't be imported on Python 3.10 (`StrEnum`)
`from enum import StrEnum` is used in four modules, and `StrEnum` only exists in **Python 3.11+**:
- `simulation/meal_engine.py:27` ← on the top-level import path, so **`import biology_as_code` itself fails**
- `bridge/bridge_engine.py:22`, `models/nutrition_ontology.py:13`, `simulation/organ_pathway_network.py:9`

But `pyproject.toml` declares `requires-python = ">=3.10"`, ships a `Programming Language :: Python :: 3.10` classifier, and the CI matrix lists `"3.10"`. **Reproduced** in a clean 3.10 venv:

```
ImportError: cannot import name 'StrEnum' from 'enum'   # Python 3.10.14
import biology_as_code   # Python 3.11 / 3.13 → OK
```

Anyone on 3.10 who `pip install biology-as-code` gets an unimportable package, and your own CI would go red on the 3.10 leg the moment you push.

**Fix (pick one):**
- **Drop 3.10:** set `requires-python = ">=3.11"`, remove the 3.10 classifier, drop `"3.10"` from the CI matrix. Simplest. **Recommended.**
- **Keep 3.10:** replace every `class X(StrEnum)` with `class X(str, Enum)` (behaves the same for these uses) and change the imports to `from enum import Enum`.

---

## HIGH — fix before publish

### H1. Wrong stomach-phase digestion whenever `enzyme_context` is non-empty (confirmed)
`digestive_enzymes.py:370` does `context.setdefault("ph", SITE_PH.get(site, 7.0))`, **mutating the caller's dict**. `digestion_capacity_routing.py:249-251` reuses the *same* `ctx` across sites in order Duodenum → Jejunum → Stomach. The first call stamps `ph=6.5` into `ctx`; `setdefault` then refuses to set the Stomach's correct `ph=2.0`, so pepsin is scored at pH 6.5. Reproduced on the documented primary path:

```python
build_absorption_plan(macros_g={"carbs":60,"protein":30,"fats":20},
                      enzyme_context={"bile_salts":0.9,"colipase":True,"trypsin_active":True})
# stomach protein capacity = 0.035   (should be 0.7 — the empty-context result)
```

An empty context accidentally masks it, so naive smoke tests pass. **Fix:** don't mutate the shared context — compute pH locally (`ph = context.get("ph") or SITE_PH.get(site, 7.0)`) or pass a per-site copy from the router.

### H2. `simulate_meal` gives different results on identical input (global-state drift, confirmed)
`organ_pathway_network.py:240` copies the *dict* `DEFAULT_ORGAN_LAWS` but shares the module-global `OrganLaw` **instances**; `set_organ_capacity`/`apply_inflammation` then mutate `law.capacity` **in place**. Since every `simulate_meal` builds a fresh engine, each call corrupts process-global state. Reproduced:

```
gut capacity across 3 identical simulate_meal() calls: [0.947, 0.896, 0.849]   # drifts down every call
```

In a server or batch job this drifts indefinitely. **Fix:** deep-copy (or rebuild) the `OrganLaw` objects per `OrganPathwayNetwork` instance. (`life_stage_dri.py:286`'s shared `LIFE_STAGE_REGISTRY` is the same pattern, currently read-only — harden it the same way.)

### H3. A broken test ships inside the wheel, keyed to your laptop's path
`engine/tests/test_engine.py` is present in the built wheel (`unzip -l` shows it; it's importable from `site-packages` after install). It asserts on `PRINT_DIR = …/src/biology_as_code/gleaned/registers/reformulations/print` (`:207`, `:362`) — a `gleaned/` tree that isn't in the package at all — so it **fails everywhere**. CI never catches it because CI only runs three named test files. **Fix:** exclude tests from packaging and stop shipping dev-only paths:
```toml
[tool.setuptools.packages.find]
where = ["src"]
exclude = ["*.tests", "*.tests.*", "*.engine.tests*"]
```
(Also relocate or delete the stale build scripts noted in M4.)

---

## MEDIUM

- **M1. No input validation on the public API.** `simulate_meal(carbs_g=-10, …)` returns `residual_macros_g={'carbs':-10,…}` — negative "grams" flow through the whole report (glycemic load, etc.). Clamp negatives/NaN to 0 (or raise `ValueError`) in `runner.simulate_meal` / `FoodPayload`.
- **M2. Dead duplicate module ships: `pathways/metabolic_pathway2.py`.** Byte-identical to `metabolic_pathways.py` except it's the *older* copy missing the `mechanism_id` edge links; imported by nothing, but a user importing it silently gets the inferior model. **Delete it.**
- **M3. `bridge/bridge_engine.py:26-31` inserts the package's own dirs onto `sys.path`.** This makes generic internal names (`core`, `utils`, `models`, `data`, `dig`, …) importable as *top-level* modules that can shadow other packages in the same env. It's also unnecessary — the following imports are fully-qualified. Delete lines 26-31 and the `E402` per-file ignore with them.
- **M4. Stale build scripts ship and can clobber package data.** `engine/topics/build_from_list.py` / `_classify_topics_impl.py` are dev tools whose `main()` reads an absent sibling file and would `write_text` over the installed 624 KB `topics_ontology.json`. Exclude/relocate them (they also carry the `F401,F841` ruff waivers).
- **M5. `get_pathway(None)` raises `AttributeError`** (`pathways/registry.py:59`, `name.strip()`), where every other bad input returns `None`. Add `if not name: return None`.
- **M6. `DigestiveFlowSimulator` dereferences optional `metabolic_state` attributes unguarded** (`digestion_flow_simulator.py:189-253`: `.vitamin_pool`, `.energy_charge`, `.hormonal_profile`). A state object missing one aborts transit mid-run with `AttributeError`. `hasattr`-guard like the vitamin path already does.
- **M7. Silent `except Exception: pass`** at `meal_engine.py:800` (`_apply_regulation_to_pathway_net`) discards all errors, so a future API change silently turns regulation into a no-op. Log it (the siblings at `:327`/`:718` at least record into the report).

---

## LOW / polish

- **L1.** `build-system` pins `setuptools>=68`, but the PEP 639 `license = "MIT"` expression + `license-files` (Metadata 2.4) needs `setuptools>=77`. Builds work today only because build isolation pulls the latest; bump the floor to `>=77` for honesty/reproducibility.
- **L2.** `simulation/{respiratory_quotient,nitrogen_balance,energy_intake_need}.py` are unreferenced dead modules (only a legacy test imports them). `respiratory_quotient.calculate` also has an unguarded `co2/o2` division and float `==` equality. Remove or wire up.
- **L3.** `digestive_definition_layer.py:713-1138` — ~420 lines of bare `Structure(...)` expressions + an unused `EXTRA_MOLECULAR` list that construct-and-discard duplicates on every import. Prune.
- **L4.** `digestive_mechanism_layer.py` redefines `get_digestive_mechanism_registry` three times via `_prev_get` closures — works but order-fragile. Collapse into one builder.
- **L5.** `metabolic_state.apply_vitamin_modifiers` never recomputes `coenzyme_factor`, so meal vitamin adequacy multiplies `energy_charge` by 1.0 — an effective no-op.
- **L6.** `scoring/loader.run_external_score_analysis` defaults `enabled=True` (fail-open). Not a leak (callers pass the flag; no plugin ships), but flipping the default to `False` matches the fail-closed ethos.
- **L7.** `bridge_engine.py:399-403` self-cancelling iron-bump math (`bump *= factor/max(factor,1.0)`), and `:449-452` a dead `… and False: pass` branch — almost certainly not intended.
- **L8.** `models/nutrition_ontology.py` runs `load_master()` at import over shared mutable class dicts and hands back live lists (no copy); it's off the top-level import path, so low impact.
- **L9.** `pathways/registry.py` rebuilds every pathway graph on each `get_pathway`/`list_pathways` call — add `functools.lru_cache`.
- **L10.** `protein_quality.ProteinSource.limiting_amino_acid` treats a missing AA as score 0 (reports it as "limiting"); latent since bundled proteins are complete.
- **L11.** Doc nits: `product_score/__init__.py` docstring references a non-existent `book/IP_BOUNDARY.md`; `user_personas.py:5` cites the wrong fixtures path; README says configure Pages as "Deploy from branch `/docs`" while `pages.yml` uses the GitHub-Actions Pages source — pick one so the site doesn't double-deploy.

---

## What's genuinely good (keep it)

- **Clean, quiet, fast public surface** — `import biology_as_code` ≈ 80 ms with no stderr noise; the 624 KB `topics_ontology.json` is lazy-loaded, not eager. 19 curated `__all__` symbols; `get_pathway("missing")` returns `None`.
- **Publish safety** — OIDC Trusted Publisher, intent-gated (`confirm=PUBLISH` / `v*` release tag), least-privilege perms, TestPyPI dry-run path, wheel size guard (2.5 MiB), import smoke test. `PUBLISHING.md` is thorough and accurate.
- **Install-safe data loading** — engine anchors every read to `Path(__file__).parent`; no CWD/absolute-path reliance in runtime code; no mutable default args; no bare `except:` in the reviewed runtime paths.
- **Honest licensing** — MIT for code, attribution license for samples, all-rights-reserved for the book, patent-pending scoring explicitly excluded; consistent across `LICENSE`, `LICENSE-SAMPLES.md`, `pyproject.toml`, and `PROPRIETARY_IP.md`. `twine check` passes both artifacts; all 206 JSON parse; both schemas are valid draft 2020-12.

---

## Pre-publish checklist

- [x] **B1** — Dropped Python 3.10 (EOL Oct 2026): `requires-python = ">=3.11"`, 3.10 classifier removed, ruff `target-version = py311`, CI matrix `["3.11","3.12","3.13"]`, stdlib `enum.StrEnum` used directly. Verified import+run on 3.11/3.12/3.13. **Blocker cleared.**
- [x] **H1** — `site_digestive_capacity` copies the context dict; stomach protein capacity back to `0.7`.
- [x] **H2** — `OrganPathwayNetwork` deep-copies `OrganLaw`/`PathwayNode` per instance; identical calls now stable.
- [x] **H3** — `packages.find` excludes `*.tests*`; wheel no longer ships the test; `gleaned/` tests skip when the tree is absent.
- [x] **M1** — `simulate_meal` clamps negative/NaN macros to `0.0`.
- [x] **M2** — Deleted `pathways/metabolic_pathway2.py`.
- [x] **M3** — Removed the `sys.path.insert` hack + `import sys` + the `E402` waiver.
- [x] **M5** — `get_pathway(None)`/`("")` return `None`; registry graphs now built once (`lru_cache`).
- [x] **M6** — Flow simulator `getattr`/`hasattr`-guards optional `metabolic_state` attributes.
- [x] **M7** — The swallowed `except` in `meal_engine._apply_regulation_to_pathway_net` now `log.debug`s.
- [x] **L1** — `build-system` floor bumped to `setuptools>=77`.
- [x] **L2** — `RespiratoryQuotient.calculate` guards divide-by-zero.
- [x] **L6** — `run_external_score_analysis` default is now `enabled=False` (fail-closed).
- [x] **L7** — Removed the self-cancelling iron-bump line and the dead `… and False: pass` branch.
- [x] **L10** — `limiting_amino_acid` returns `("unknown", 0.0)` when there's no AA data.
- [x] **L11** — Fixed the `book/IP_BOUNDARY.md` + wrong-SSOT-path docstrings and the README Pages instruction.
- [x] **Defensive gap** — `load_inventory()` now routes through `_scrub` before merge.
- [ ] **Next:** `bash scripts/release_check.sh`, then TestPyPI dry-run before production PyPI.

### Consciously deferred — **resolved (quality pass)**

- **M4** — **Done.** Topics build scripts moved to repo `tools/topics_build/` (not in the wheel). Tests load classifier via path if present. `build_from_list` refuses site-packages without force env.
- **L3** — **Done.** Verified `Structure` is a pure dataclass (no register side effect). Dead bare `Structure(...)` block removed; `EXTRA_MOLECULAR` is now registered via `_register_extra_molecular()` (nhe3, dra, mct1, …).
- **L4** — **Done.** Single `get_digestive_mechanism_registry()` calls all three expansion registrars once.
- **L5** — **Done.** `sync_coenzyme_from_adequacy()` keeps coenzyme_factor in lockstep with adequacy; meal vitamin updates call it; low B-vitamin adequacy now reduces `energy_charge` (soft FLOW teaching).
- **L8/L9** — L9 done earlier; L8 still low-impact off import path.
