# Biology as Code

**Standardizing Nutrition Science for Preventive Medicine**

[![CI](https://github.com/murffious/biology_as_code/actions/workflows/ci.yml/badge.svg)](https://github.com/murffious/biology_as_code/actions/workflows/ci.yml)
[![Docs](https://github.com/murffious/biology_as_code/actions/workflows/docs.yml/badge.svg)](https://github.com/murffious/biology_as_code/actions/workflows/docs.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21536449.svg)](https://doi.org/10.5281/zenodo.21536449)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://pypi.org/project/biology-as-code/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/murffious/biology_as_code/blob/main/LICENSE)

**[Documentation](https://murffious.github.io/biology_as_code/)** · [Cookbook](https://murffious.github.io/biology_as_code/cookbook/) · [Validation report](https://murffious.github.io/biology_as_code/VALIDATION/)

> **On the name.** *Code Biology* (Barbieri and others) is an existing field that
> studies organic codes in living systems. This project is unrelated: it is a
> methodological stance that nutrition and pathway models should be written like
> software — versioned, tested, provenance-tracked, fail-closed. Descriptive
> literature, prescriptive tool. See [docs/naming.md](docs/naming.md).

`biology-as-code` is an open Python package that models what happens to a meal —
digestion, absorption, and the metabolic pathways it drives — as inspectable
"biology as code." It is the **free companion** to the *Biology as Code* book,
which is **still being written and has not been released yet**. The package works
on its own today; you do not need the book to use it.

| | |
|--|--|
| **Book** | 📖 *In progress — not yet released.* This repo is its open companion. |
| **This repo / PyPI** | Schemas, food examples, **open dig + teaching pathways** |
| **Not included** | Product **meal score** / Kibo-vars product scorer (patent pending) |
| **Ethos** | Fail-closed · gate ≠ bound · empty beats fake |

**Not medical advice.** FLOW teaching / research software only — not a clinical decision-support system.

---

## What's inside

Install it and `import biology_as_code` — a small, **zero-dependency** toolkit (pure Python 3.11+):

- **Metabolic pathway graphs** (glycolysis, TCA, β-oxidation, ketogenesis/ketolysis,
  AMPK·mTORC1·SREBP nutrient sensing) — `get_pathway(...)`, rendered via
  `visualization.pathway_to_mermaid`.
- **Declarative digestion machines** — the GI tract (oral → colon) as versioned,
  inspectable state graphs: `list_machines()`, `trace()`, `run_digestion(...)`.
- **LAW-SPEC law cards** — the constitution as queryable data:
  `law_card("LAW-004")` → System / Organ / Gate / Bound / Conditions / relation.
- **Meal simulation** — `simulate_meal(carbs_g=…, protein_g=…, fats_g=…, fiber_g=…)`
  and fed / fasted / exercise scenarios.
- **Bundled data** — meal fixtures, a vitamins registry, personas, and iron/colon/law data.
- **Provenance** — `all_sources()` / `pubmed_url()` surface every citation; no fabricated
  data and no network calls by default.

Not included: the patent-pending product/meal score (open hook only) and the book itself.

---

## Install

**From PyPI** — *once the first release is published* (not on PyPI yet):

```bash
pip install biology-as-code
```

**From source** — works today:

```bash
git clone https://github.com/murffious/biology_as_code.git
cd biology_as_code
pip install -e ".[dev]"
```

### Minimal usage

```python
from biology_as_code import simulate_meal, list_pathways, get_pathway, fed, pathway_activities

r = simulate_meal(carbs_g=55, protein_g=35, fats_g=18, fiber_g=20)
print(r.absorbed_macros_g)       # dig residual path (open FLOW)
print(list_pathways()[:5])       # teaching pathway graphs
print(pathway_activities(fed())) # regulation snapshot
# Product meal score is NOT computed here (enable_product_score defaults False)
```

```bash
python examples/python/run_meal.py
python examples/python/fed_vs_fasted.py
bash scripts/release_check.sh   # pre-upload tests + wheel smoke (does not publish)
```

Logging is **quiet by default**. For dig traces: `export BIOLOGY_AS_CODE_LOG=DEBUG`.

**Publishing:** not automatic. Push to `main` = CI only. Upload to PyPI only when you  
**Actions → Publish** with `confirm=PUBLISH`, or publish a **GitHub Release** on a `v*` tag.  
Setup checklist: [`docs/python/PUBLISHING.md`](docs/python/PUBLISHING.md).

Architecture notes: [`docs/python/PACKAGE_ARCHITECTURE.md`](docs/python/PACKAGE_ARCHITECTURE.md)  
License: [MIT](./LICENSE) for code · [LICENSE-SAMPLES.md](./LICENSE-SAMPLES.md) for example JSON · book remains all rights reserved.

Docs live under `docs/` in the repo (no Pages required for PyPI). Optional GitHub Pages is **manual only** (Actions → Deploy GitHub Pages) after Settings → Pages → Source: GitHub Actions.

---

## Repository map

```text
docs/                 # public site / short free content
schemas/              # packet + claim + relation subset
examples/
  foods/              # small teaching food packets (gates / claims)
  meals/README.md     # pointer only — full meals live in package fixtures
  claims/             # claim audit fixtures
  units/              # teaching UNIT fixtures
src/biology_as_code/
  data/fixtures/meals/  # SSOT full meal JSON (ships in wheel; no kibo_score)
  data/fixtures/        # vitamins, personas
  pathways/ dig/ simulation/ ...
pathways/             # mermaid + tests.md packs
glycolysis/           # gold hand-authored mermaid
```

**Meals:** one copy only → `src/biology_as_code/data/fixtures/meals/`  
**Foods:** separate teaching packets → `examples/foods/` (not the same as meals)

---

## Core ideas (60 seconds)

1. **Label ≠ dose** — printed milligrams are not delivered dose.  
2. **Gate ≠ bound** — whether something can happen vs how much.  
3. **Four seats** — host · partner · stage · clock (one law envelope).  
4. **L1→L5** — matrix → nutrient → mechanism → physiology → outcome; no tunnels.  
5. **Empty beats fake** — missing data is `UNEVALUABLE`, not a green score.

See [docs/constitution.md](docs/constitution.md).

---

## Example food objects

**Filled (teaching):**

| File | Teaching point |
|------|----------------|
| [`spinach_salad_zero_fat.json`](examples/foods/spinach_salad_zero_fat.json) | Fat-vehicle gate **closed** |
| [`spinach_salad_with_oil.json`](examples/foods/spinach_salad_with_oil.json) | Same cargo + lipid partner |
| [`lentils_with_tea.json`](examples/foods/lentils_with_tea.json) | Iron bound narrowed (tannin) |
| [`lentils_with_ascorbate.json`](examples/foods/lentils_with_ascorbate.json) | Iron bound expanded (ascorbate) |
| [`almond_whole.json`](examples/foods/almond_whole.json) / [`almond_flour.json`](examples/foods/almond_flour.json) | Matrix intact vs destroyed |

**Stubs (`status: stub`)** — placeholders for real cargo/partners later: oats, breads, rice, orange/juice, salmon, olive oil, tea/lemon/coffee, dairy, meats, tofu, produce, UPF snacks/soda, supplements, IV clinical, etc. See full list under [`examples/foods/`](examples/foods/).

Copy [`_template.json`](examples/foods/_template.json) for new ones. Keep schema; leave `"open"` until you have real fields.

---

## Book

**Biology as Code** — *Standardizing Nutrition Science for Preventive Medicine*

- **Status: in progress.** The manuscript is still being written and is **not yet published** — there is nothing to buy or preorder yet.
- The full prose is **not in this repo** and will be released separately as a commercial book when it's done.
- This repository is the **open companion** (schemas, examples, and the Python package) and is fully usable on its own today.
- Issues welcome for **schemas and examples only** — not the book text.

---

## License

- **Schemas & examples:** see [LICENSE-SAMPLES.md](LICENSE-SAMPLES.md) (permissive for reuse with attribution).  
- **Book text, figures, and brand:** © author — all rights reserved unless a separate license is published.

---

## Citation

If you use `biology-as-code` in your work, please cite it via its archived release:

> Murff, P. (2026). *Biology as Code: an open, provenance-tracked toolkit for meal digestion and metabolic-pathway modeling* (v0.1.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.21536449

A [`CITATION.cff`](CITATION.cff) is included, so GitHub's **"Cite this repository"** button works too.

---

## Status

Early companion scaffold (alpha). The Python package works today and installs from source; food objects and schemas will keep growing. The **book itself is still in progress and has not been released** — this repo does not depend on it.

---

<p align="center">
  <img src="docs/assets/biology-as-code-cover.jpg" alt="Biology as Code — Standardizing Nutrition Science for Preventive Medicine — Paul Murff" width="420" />
</p>

<p align="center"><em>Biology as Code: Standardizing Nutrition Science for Preventive Medicine</em> — Paul Murff</p>

<p align="center"><sub><em>Note: cover art is a draft (not final), and the glucose chemistry shown on it is not yet corrected.</em></sub></p>
