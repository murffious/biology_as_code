# Biology as Code — Zenodo deposit summary

*One-page summary for the Zenodo archival record. Paste the Description block into the
Zenodo "Description" field; use the metadata below for the other fields.*

---

## Title

**Biology as Code: an open, provenance-tracked toolkit for meal digestion and metabolic-pathway modeling**

## Description (abstract)

`biology-as-code` is an open-source Python package that models what happens to a meal —
digestion, absorption, and the metabolic pathways it drives — as **inspectable code** rather
than a black box. It is built on a simple discipline: *gate ≠ bound, empty beats fake, and no
fabricated data* — outputs are traceable to their sources and the software fails closed rather
than inventing a confident answer over missing information.

The package provides a meal-simulation pipeline (`simulate_meal`), a declarative model of the
gastrointestinal tract as versioned, inspectable state machines (`run_digestion`, `trace`), a
library of 28 teaching metabolic-pathway graphs (glycolysis, TCA, β-oxidation, ketogenesis and
ketolysis, and AMPK·mTORC1·SREBP nutrient-sensing networks), 47 "LAW-SPEC" law cards that
express the underlying rules as queryable data (System / Organ / Gate / Bound / Conditions /
typed relation), and an evidence/provenance layer that surfaces every citation and validates
PubMed identifiers without making network calls by default. It ships with meal fixtures, a
vitamins registry, and synthetic teaching personas (no personal health information).

It is pure Python (≥ 3.11), dependency-free, and installable from PyPI (`pip install
biology-as-code`). The patent-pending product/meal-scoring engine is deliberately **not**
included (only an optional, disabled hook). This is FLOW teaching / research software and is
**not medical advice or a clinical decision-support system**.

## What's inside

- Metabolic pathway graphs — `get_pathway(...)`, rendered to mermaid via `visualization.pathway_to_mermaid`
- Declarative digestion machines (oral → colon) — `list_machines()`, `trace()`, `run_digestion(...)`
- LAW-SPEC law cards — `law_card("LAW-004")` → System / Organ / Gate / Bound / Conditions / relation
- Meal simulation and fed / fasted / exercise scenarios — `simulate_meal(...)`
- Bundled data — meal fixtures, vitamins, synthetic personas, iron/colon/law data
- Provenance — `all_sources()` / `pubmed_url()`; no fabricated data, no default network access

## Install

```bash
pip install biology-as-code
```

---

## Zenodo metadata (fill the fields)

| Field | Value |
|-------|-------|
| **Upload type** | Software |
| **Title** | Biology as Code: an open, provenance-tracked toolkit for meal digestion and metabolic-pathway modeling |
| **Authors** | Murff, Paul (Morf Engineering) |
| **Version** | 0.1.0 |
| **License** | MIT |
| **Keywords** | nutrition, digestion, metabolism, metabolic pathways, systems biology, bioinformatics, teaching, provenance, reproducibility, Python |
| **Language** | English |
| **Related identifiers** | `https://pypi.org/project/biology-as-code/` (is identical to) · `https://github.com/murffious/biology_as_code` (is supplement to) |

## Suggested citation

> Murff, P. (2026). *Biology as Code: an open, provenance-tracked toolkit for meal digestion and
> metabolic-pathway modeling* (v0.1.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.21536449

**DOI:** [10.5281/zenodo.21536449](https://doi.org/10.5281/zenodo.21536449)
