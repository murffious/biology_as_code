# Roadmap — from v0.1.0 to "big time"

**Status today (2026-07-24):** published on PyPI (`pip install biology-as-code`), v0.1.0 alpha,
zero-dependency, 28 pathway graphs, 8 digestion machines + full-digest process, 47 LAW-SPEC law
cards, an evidence/provenance layer, 67 meal fixtures + 8 personas. Clean IP boundary, `release_check.sh` green.

**The thesis that can make it matter:** nutrition science as *inspectable, provenance-tracked,
fail-closed code* — the opposite of black-box AI nutrition apps. "Empty beats fake." That contrast
is the newsworthy hook; everything below exists to make it credible enough to stand behind.

> **Strategy vs. engineering.** This file is the *engineering* roadmap — how to ship the package.
> For the *product* direction — why the wedge is food **judgment**, how the claim auditor becomes a
> dietary-health-claims adjudication authority, and how the PySpark/AWS/React Native build-out and the
> LLM claims agent stack on top of it — see [docs/standardization-roadmap.md](docs/standardization-roadmap.md).

---

## What "big time" packages actually have

The scientific Python packages that get cited and covered (Biopython, scanpy, COBRApy, RDKit…) share:
credibility (a **paper + DOI**, validated numbers), **great docs**, broad **distribution** (conda-forge),
disciplined **testing/CI**, a real **community process**, and a **clear narrative**. We have the narrative
and the engine; we need the rest.

---

## Phase 1 — Foundation & credibility (v0.1.x → v0.2, weeks)

*Make it trustworthy and easy to adopt.*

- [ ] **Full-suite CI, not a subset.** CI currently runs only 3 test files + pathway packs. Run the
      whole suite, add a **coverage** gate + badge, and matrix over 3.11/3.12/3.13 (+ Windows/macOS/Linux).
- [ ] **Docs site.** Turn `docs/` into a real site (MkDocs-Material or Sphinx): quickstart, the
      `simulate_meal` / `run_digestion` / law-cards / provenance walkthroughs, an auto API reference
      (`py.typed` is already there), and the mermaid diagrams inline.
- [ ] **Badges** in the README: CI, coverage, PyPI version, Python versions, license, DOI.
- [ ] **Zenodo DOI.** Connect the GitHub repo to Zenodo so every release is archived and **citable** —
      the single cheapest credibility win for a science package.
- [ ] **Community files:** `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue/PR templates.
- [ ] **conda-forge feedstock** — many scientific users install via conda, not pip.
- [ ] **Validation invariants, expanded.** Pin more pathways to textbook stoichiometry the way glycolysis
      (+2 ATP/+2 NADH), TCA, and ETC (P/O 2.5/1.5) already are, and fail CI on drift.

## Phase 2 — Depth & validation (v0.2 → v0.5, a few months)

*Make the science defensible and the outputs usable.*

- [ ] **Close the book-TODO backlog** (package side): more pathways, deeper regulatory graphs, the
      **evidence-register merge** (EV-039–041 → gleaned register), and turn the **MICOM / FBA bridge**
      from docs-only into an optional integration.
- [ ] **Benchmark the digestion model** against reference datasets; publish a short **validation report**
      (what's textbook-exact vs teaching-FLOW — keep the honesty tiering explicit).
- [ ] **Real evidence integration (optional, still fail-closed):** ship an opt-in PubMed/E-utilities
      fetcher behind the existing `fetch_pubmed` gate; grow `law_evidence` coverage beyond LAW-026.
- [ ] **Interop:** DataFrame/JSON outputs, Jupyter-friendly `_repr_html_` for pathways/machines/reports,
      and a matplotlib/plotly view alongside mermaid.
- [ ] **A "cookbook"** of worked case studies (fed vs fasted, fiber/matrix what-ifs, iron + ascorbate,
      a persona × meal walkthrough) — the thing people share.

## Phase 3 — Stability & adoption (→ v1.0, the push)

*Make it stable, cited, and known.*

- [ ] **API-stability commitment** + semantic-versioning + a deprecation policy → cut **v1.0**.
- [ ] **A paper.** Submit to **JOSS** (Journal of Open Source Software) — peer-reviewed, fast, citable,
      and the standard on-ramp to legitimacy; or a methods preprint. This is the "makes the news" step.
- [ ] **Reproducible benchmarks** + a public validation dashboard.
- [ ] **Talks & tutorials:** SciPy / PyData / a nutrition-informatics venue; a short screencast of the
      declarative digestion machine tracing a meal.
- [ ] **Real users:** get it used in a course or a lab; collect citations/testimonials.
- [ ] **Narrative push:** blog the "biology as code + provenance + fail-closed" thesis as the antidote
      to AI-hype nutrition tools. This is the differentiator that earns coverage.

---

## Do these three first (highest leverage, this week)

1. **Full-suite CI + coverage badge** — proves it works, on every push.
2. **Docs site** from the existing `docs/` — the #1 adoption blocker for a new package.
3. **Zenodo DOI on v0.1.0** — makes it citable immediately, for free.

## Guardrails to keep while scaling

- Keep the **IP boundary** (product/meal score stays a gated hook) and the **provenance/honesty** rules —
  they're the brand. Never ship fabricated numbers or a green score over missing data.
- Every new pathway/machine carries its **sources** (already wired into the pack exporter).
- Bump `pyproject.toml` + `VERSION_MANIFEST.json` + `CHANGELOG.md` together every release.
