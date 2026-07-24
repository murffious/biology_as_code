# Biology as Code

**Standardizing Nutrition Science for Preventive Medicine**

Public **companion** + installable Python package (`biology-as-code` on PyPI when published).

| | |
|--|--|
| **Book** | Paid product (not in this package) |
| **This repo / PyPI** | Schemas, food examples, **open dig + teaching pathways** |
| **Not included** | Product **meal score** / Kibo-vars product scorer (patent pending) |
| **Ethos** | Fail-closed · gate ≠ bound · empty beats fake |

**Not medical advice.** FLOW teaching / research software only — not a clinical decision-support system.

---

## Install (PyPI)

```bash
pip install biology-as-code
```

From source:

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

Docs site (GitHub Pages): deployed by the `pages.yml` workflow — set **Settings → Pages → Source: GitHub Actions**.

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

**Biology as Code**  
*Standardizing Nutrition Science for Preventive Medicine*

- Full prose: **not in this repo** (commercial manuscript)  
- Purchase / preorder: *[add store URL]*  
- Issues welcome for **schemas and examples only**

---

## License

- **Schemas & examples:** see [LICENSE-SAMPLES.md](LICENSE-SAMPLES.md) (permissive for reuse with attribution).  
- **Book text, figures, and brand:** © author — all rights reserved unless a separate license is published.

---

## Status

Companion scaffold. Food objects and schemas will grow. Full book remains a paid product.
