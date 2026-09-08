# User stories

The [roadmap](https://github.com/murffious/biology_as_code/blob/main/ROADMAP.md)
says what to build. These stories say who it is for and how we will know it is done.
Each one names a person, the thing they are trying to do, the moment they hit the
gap, and the acceptance criteria that close it. They are written to be picked up
cold by someone who has never opened this repository.

Every story is filtered through the [constitution](constitution.md) before it
enters. That filter is not decoration: the fastest way to make a nutrition tool
popular is to invent the number the user wanted, and the entire point of this
package is that it will not. So each story carries an explicit *out of scope*
line naming the shortcut it refuses.

Five to start. The roadmap has room for more.

| # | Story | For | Roadmap line | Size |
|---|-------|-----|--------------|------|
| 1 | [Propose a law without writing code](#1-propose-a-law-without-writing-code) | A researcher with a paper in hand | Adoption plan · Do next 1 | S |
| 2 | [One door for a meal](#2-one-door-for-a-meal) | An app developer integrating the engine | Adoption plan · Do next 2 | M |
| 3 | [Click a state, see its evidence](#3-click-a-state-see-its-evidence) | A lecturer tracing a meal live | Adoption plan · Do after 4 | M |
| 4 | [A build that knows its biochemistry](#4-a-build-that-knows-its-biochemistry) | A maintainer merging a pathway | Phase 1 · Validation invariants | M |
| 5 | [The case study people forward](#5-the-case-study-people-forward) | A dietetics educator preparing a class | Phase 2 · Cookbook | S |

---

## 1. Propose a law without writing code

**As a** nutrition researcher who has just read a mechanism paper,
**I want** to propose a new law card by filling in a form,
**so that** the finding reaches the register in the paper's own terms and I never
have to open a Python file to contribute it.

### The moment

A postdoc finishes a paper on how calcium in the same meal reduces non-haem iron
uptake. She knows the substrate, the product, the direction, and the PubMed id. She
opens this repository, finds the pathway template, and closes the tab: it asks her
to write a module, export a mermaid pack, and run three scripts. The finding stays
in her notes. Six months later someone else encodes it from a secondary source, with
the wrong id.

### Acceptance criteria

- A GitHub issue form, `law.yml`, sits beside the existing evidence form. It asks
  for exactly six things: starting substrate, product, whether the relation is a
  **gate** or a **bound**, the PubMed id, the honesty tier, and one sentence on
  what the paper measured.
- Gate versus bound is a required choice with the definitions inline, in the
  words of the [Gate vs Bound cookbook page](cookbook/01-gate-vs-bound.md). A
  submitter who cannot choose is told that is fine and to pick *unsure*; an unsure
  proposal is still a proposal.
- The PubMed id field is validated as digits only. The form says, once, that the
  id will be resolved against PubMed before anything is written, and that a
  mismatch between the id and the paper described sends the proposal back.
- Submission applies the label `law-proposal`. A maintainer turns an accepted
  proposal into a card; the contributor's name goes on the card's provenance.
- The `contributing-data.md` page gains a two-paragraph section: *I have a
  mechanism, not a number*, pointing at the form.

### Out of scope

No field for kcat, Km, rate limit, or percentage effect. A magnitude entered on a
form with no way to verify it becomes fake kinetics the moment it is encoded. The
form collects a relation and a source. Numbers arrive through the evidence form,
where they walk the fail-closed gate.

---

## 2. One door for a meal

**As an** application developer wiring this engine into a product,
**I want** `DigestRun` documented as *the* meal API, with its food packet and its
four seats named and typed,
**so that** I integrate against one contract and am never tempted to invent a
second request schema that carries defaults the engine would refuse.

### The moment

A developer is asked to run a user's lunch through the engine. He finds
`simulate_meal`, `run_digestion`, and `DigestRun`, and cannot tell which is the
front door. He writes a `SimulationRequest` dataclass of his own, gives the host a
default state called *Stressed* with a glutathione level he found in a review, and
ships it. Every downstream number now rests on a pool nobody declared.

### Acceptance criteria

- A docs page, *Running a meal*, opens with one sentence: `DigestRun` is the meal
  API. It shows a food packet entering and names the four seats: **host**,
  **partner**, **stage**, **clock**.
- Each seat has a table row: its type, what it means, and what happens when it is
  absent. Absent means the affected outputs are `OPEN`. There is no default
  persona, no default state, and the page says why in one paragraph.
- The page's code blocks execute under `tests/test_cookbook.py`, the same way the
  cookbook pages do, so the documentation cannot drift from the signature.
- A short *Do not do this* section shows the `SimulationRequest` anti-pattern and
  the undeclared-pool anti-pattern, each in five lines, each with the reason.
- `simulate_meal` and `run_digestion` keep working. Their docstrings gain one line
  each pointing at the page.

### Out of scope

No second schema. No default twin. No mutable millimole ledgers as required
state. Ontology identifiers on the packet are story 3 in the adoption plan and are
not folded into this one.

---

## 3. Click a state, see its evidence

**As a** lecturer walking a class through a digestion trace on a projector,
**I want** to click any named state in the trace and land on its law card and its
PubMed record,
**so that** students see the model as a chain of sourced claims, not as a black
box that emitted a curve.

### The moment

The trace shows a postprandial spike. A student asks where the number came from.
The lecturer has to say *the model*, which is the answer every other nutrition app
gives, and the one this package exists to replace.

### Acceptance criteria

- A provenance UX spec, `docs/provenance-ux.md`, defines the click path:
  named state → law card → citation. It is a spec for a downstream UI, not a UI
  in this package.
- Every named state the engine can emit resolves to a law card id, or is marked
  `OPEN`. A test enumerates the emitted state names and fails on any name with
  neither.
- Every law card that carries a citation carries a PubMed id that
  `tools/check_pmids.py` has confirmed. Cards with a direction but no citation
  render as **direction only**, in those words.
- The spike is presented as a *state* with a name and a source. The spec forbids
  rendering a computed magnitude beside it unless that magnitude has its own card.

### Out of scope

No computed superoxide grams, no ROS curve, no display of a number the register
does not hold. The spec's job is to make absence visible, not to fill it.

---

## 4. A build that knows its biochemistry

**As a** maintainer reviewing a pathway pull request,
**I want** textbook stoichiometry pinned as tests, so that a change that breaks
glycolysis's net yield or the electron transport chain's P/O ratio turns the
pull request red,
**and I want** the build to refuse, in writing, to fail because a clinical curve
was not matched within a tolerance.

### The moment

A contributor refactors the cofactor sign convention. The tests pass. Three
pathways now report NADH consumed where it is produced. Nobody notices until the
mermaid packs are regenerated for the book.

### Acceptance criteria

- Glycolysis (+2 ATP, +2 NADH), the TCA cycle, and the electron transport chain
  (P/O 2.5 and 1.5) are already pinned. This story adds pins for the urea cycle,
  β-oxidation of palmitate, and ketogenesis, each test naming the textbook page
  it took the numbers from.
- A `trial_coverage` ledger lists every registered pathway and whether it is
  pinned, with the source, or unpinned. The ledger is generated; hand edits fail
  the build.
- A mutation test flips one cofactor sign in a fixture and asserts the suite goes
  red. A pin that cannot fail is not a pin.
- The CI step is named *Biological identity* and its comment states the rule: we
  pin what a textbook states as an identity; we do not compare against a 75 g
  oral glucose tolerance curve and fail on a 5 % miss, because that number is a
  measurement of one body, not a law.

### Out of scope

No tolerance-band comparison against clinical time series. No ATP or ROS curves
as pass criteria. Coverage grows by adding identities, never by loosening one.

---

## 5. The case study people forward

**As a** dietetics educator preparing a class on meal context,
**I want** one worked case study that runs the same meal through a fasted host and
a fed host, for a named persona,
**so that** I can hand students a page where every difference on screen has a
source, and every value that stayed unknown says so.

### The moment

The cookbook has four recipes. Each teaches a mechanism. None teaches the thing
students ask about first: *why does the same plate behave differently at 7 a.m.
than at 7 p.m.?* The educator builds the comparison by hand in a notebook, which
nobody else can run.

### Acceptance criteria

- A fifth cookbook page, *Fed versus fasted*, takes one fixture meal and one
  persona from the packaged fixtures and runs `DigestRun` twice, changing only
  the host state.
- The page shows exactly one gate and one bound that behave differently between
  the two runs, and says which law card each comes from.
- At least one value on the page is `OPEN` in one of the runs. The page explains,
  in plain words, why it stayed open and what evidence would close it.
- Every citation on the page is a PubMed id confirmed by `tools/check_pmids.py`.
  The page's code executes under `tests/test_cookbook.py`; its notebook twin is
  generated by `scripts/build_notebooks.py` and the sync check passes.
- The page ends with the three-sentence version a student could repeat to a
  patient, followed by the sentence that it is teaching software and not advice.

### Out of scope

No persona invented for the page; the eight packaged personas are enough. No
number in the comparison that the register does not hold. A difference we cannot
source is shown as a difference in *state*, not in *magnitude*.

---

## How a story moves

A story is done when its acceptance criteria are tests, docs pages, or files in
this repository, and the pull request that adds them names the story by number.
Stories are edited in pull requests against `dev`, like everything else; see
[CONTRIBUTING](https://github.com/murffious/biology_as_code/blob/main/CONTRIBUTING.md).
