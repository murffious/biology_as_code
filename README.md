# Biology as Code

**Standardizing Nutrition Science for Preventive Medicine**

Public **companion** to the book — not the full manuscript.

| | |
|--|--|
| **Book** | Paid product (link below when live) |
| **This repo** | Free schemas, example packets, short constitution notes |
| **Primary reader** | Engineers / systems builders |
| **Ethos** | Fail-closed · gate ≠ bound · empty beats fake |

---

## What this is

A systems constitution for nutrition: food is a **typed packet**, digestion is **execution under law**, and claims must survive a **gate-first audit** (no L1→L5 tunnels).

This repository is the O’Reilly-style **companion**:

- example **food objects** you can extend
- **JSON schemas** for packets and claim audits
- short **docs** for the free public face of the framework

It is **not** a free ebook dump of the full draft.

---

## Quick start

```bash
git clone https://github.com/murffious/biology_as_code.git
cd biology_as_code
# browse examples/foods/*.json and schemas/
```

Docs site (GitHub Pages): enable **Settings → Pages → Deploy from branch `main` / folder `/docs`**  
(or use the Actions workflow once enabled).

---

## Repository map

```text
docs/                 # public site / short free content
schemas/              # packet + claim + relation subset
examples/
  foods/              # example food packets (stubs + filled)
  claims/             # Court-style claim fixtures
  units/              # teaching UNIT fixtures (iron, fat vehicle)
LICENSE-SAMPLES.md    # license for schemas & examples
```

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

| File | Teaching point |
|------|----------------|
| [`examples/foods/spinach_salad_zero_fat.json`](examples/foods/spinach_salad_zero_fat.json) | Fat-vehicle gate **closed** (carotenoids / fat-solubles) |
| [`examples/foods/spinach_salad_with_oil.json`](examples/foods/spinach_salad_with_oil.json) | Same cargo, lipid partner present |
| [`examples/foods/lentils_with_tea.json`](examples/foods/lentils_with_tea.json) | Iron bound **narrowed** by tannin |
| [`examples/foods/lentils_with_ascorbate.json`](examples/foods/lentils_with_ascorbate.json) | Iron bound **expanded** by same-meal ascorbate |
| [`examples/foods/almond_whole.json`](examples/foods/almond_whole.json) | Matrix encapsulation prior |
| [`examples/foods/almond_flour.json`](examples/foods/almond_flour.json) | Same identity, destroyed matrix |

Add more under `examples/foods/` — keep the schema; leave unknowns `"open"` or omit.

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
