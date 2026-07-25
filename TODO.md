# TODO — North Star & plan

## ⭐ North Star (the goal, refined)

**One flow: `user context + a food → through the system → SHOW how a health claim
holds up in the science.`**

Take *who the eater is* (context/conditions) and *what they eat* (a standardized
food), pass it through the modeled body (digest → signaling), and surface the
**claim's verdict with its evidence** — fail-closed, every edge declaring its
strength. Every task below serves making this real **and honest**. The contribution
is the *discipline* (transparent, evidence-tiered, refuses to fake magnitude), not a
biophysical digital twin.

---

## Status — shipped on `main`

- Claim auditor · food packets · **crowdsourcing gate** (Door A) · **claims agent**
  (assay) + handler + contrib bridge · **mockups** (digestion pipeline, lifespan).
- **`digest(food, conditions) → trace`** engine + `Conditions` (the four seats) +
  offline **Step Functions ASL export**.
- **Event/subscriber layer** — built, green, in **PR #5** (blocked from merge only by
  broken links in `python/ADD_PATHWAY.md`, part of the in-progress pathways work).

---

## Phase 1 — UNIFY (the North Star, highest value)

Compose the pieces we already have into one inspectable flow.

- [ ] **`explain(user, food, claim)`** — a single entry point that runs: packet +
  `Conditions` → `digest()` handling → event cascade → **claim verdict** (auditor /
  assay) → **evidence tiers**. Returns one object that tells the whole story.
- [ ] **Claims Lab mockup** — the 3rd `mockups/` surface: enter a food + who's eating
  it + a claim → watch it pass through the body and SHOW the verdict + the evidence
  behind each edge. (User has UI backup for reference.)
- [ ] A **cookbook page / notebook** walking one claim end-to-end.

## Phase 2 — STRENGTHEN the science (earn "mimics the body")

- [ ] **Promote edges consensus → evidence-locked** by attaching primary citations —
  exactly what the crowdsourcing gate (`contrib`) is for. *(I can wire the workflow;
  the citations are the work.)*
- [ ] **Benchmark stage outputs** vs reference datasets (absorption fractions,
  glycemic / insulin response) — roadmap Phase 2. *(Needs the datasets; research.)*
- [ ] **Quantitative kinetics** — magnitudes + time-course, which the system today
  deliberately refuses to fake. *(Needs data; do NOT fabricate.)*

## Phase 3 — SURFACE / ship

- [ ] **Door B** — API endpoint + submission form over the existing assay handler +
  `contrib.from_assay` bridge (needs a deploy target + a bot token for auto-PRs).
- [ ] **GitHub Pages** — enable Settings → Pages → Source: GitHub Actions so the docs
  site deploys (build already passes). *(Your repo setting.)*
- [ ] **nutri backend repoint** — `backend/assay_service.py` → `from
  biology_as_code.agents.assay …` after a release. *(External repo, your side.)*

## Housekeeping

- [ ] Merge **PR #5** (events) once `python/ADD_PATHWAY.md` links are fixed.
- [ ] Delete the stale `feat/auditor-and-docs` branch.

---

### Who does what (honest)
- **I can build:** Phase 1 (all), edge-promotion workflow, Door B software, Claims Lab
  mockup, housekeeping.
- **Needs you:** Pages setting, nutri backend repoint.
- **Needs real data (never faked):** benchmarking, quantitative kinetics.

### Start next
Phase 1 → `explain(user, food, claim)` + Claims Lab. That single flow *is* the North
Star, and everything already exists to compose it.
