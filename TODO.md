# TODO — next-session plan

Snapshot of what's shipped and what's next, so work can resume cold.

## Shipped (on `main`)

- **Mockups** — `mockups/` (digestion pipeline, lifespan meal trace, gallery).
- **Crowdsourcing (Door A)** — `contrib/` fail-closed gate (`ACCEPTED / NEEDS_SOURCE / REFUSE`), schema, examples, CI gate, `CONTRIBUTING.md`, evidence issue form.
- **Claims agent** — `agents/assay/` (8-attack gauntlet → BUSTED/PLAUSIBLE/CONFIRMED), Lambda handler, `contrib.from_assay` bridge, docs.
- **Digestion engine** — `digest(food, conditions) → DigestionTrace` (`digestion/engine.py`), `Conditions` (the four seats), + offline **ASL exporter** (`digestion/asl.py`, `scripts/export_step_functions.py`).

---

## PRIMARY NEXT — event / subscriber layer

**Why:** the ordered digestion flow is a state machine; the *non-linear* body
(insulin/AMPK signaling, hormonal loops, feedback) is naturally **event-driven**.
`digest()` already emits the event stream (`DigestionTrace.events`), so this sits
cleanly on top. AWS model: Step Functions → **EventBridge** → fan-out.

**Design**
- A small in-process **event bus** + **subscriber registry** (zero-dep, fail-closed:
  a subscriber lacking data emits nothing — no fabricated signals).
- `digest()` (or a new `simulate(food, conditions)`) **publishes** stage events
  (`absorbed`, `micelles`, `SCFA`, `stage:*`); subscribers **react**, and may emit
  further events (a cascade), captured in the trace.
- Wire the existing systems as subscribers, don't rewrite them:
  `simulation/signaling_pathways.py`, `simulation/hormonal_energy.py`,
  `simulation/organ_pathway_network.py`.

**Proposed files**
- `src/biology_as_code/events/bus.py` — `EventBus` (publish/subscribe), `Event` type.
- `src/biology_as_code/events/subscribers.py` — glucose→insulin→AMPK/mTOR, SCFA→signal.
- `src/biology_as_code/events/__init__.py` — public surface.
- `tests/test_events.py` — a published `absorbed` event triggers the insulin
  subscriber; monotonic/fail-closed (no data → no emission); cascade terminates.
- `docs/events.md` + nav.

**Acceptance**
- `digest(...)` output can be replayed through the bus; subscribers produce typed
  reaction events with law/provenance refs where they exist.
- ruff + full pytest + strict docs build green; wheel stays < 2.5 MB.

---

## Backlog (smaller / external)

- **Door B (crowdsourcing front end)** — API endpoint + submission form over the
  existing assay handler + `contrib.from_assay` bridge. Pieces exist; needs the
  endpoint + form + a bot token to open PRs.
- **Claims Lab mockup** — a 3rd `mockups/` HTML surface for the assay agent
  (intake → gauntlet → verdict → evidence). Deferred by user (has UI backup).
- **GitHub Pages** — Docs *deploy* fails until Pages is enabled
  (Settings → Pages → Source: GitHub Actions). Deferred by user. Build already passes.
- **nutri backend repoint** — `backend/assay_service.py` (separate repo) must switch
  its path-hack import to `from biology_as_code.agents.assay …` after a release.
- **Housekeeping** — delete the stale `feat/auditor-and-docs` branch.
