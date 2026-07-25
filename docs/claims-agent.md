# Claims agent (assay)

The claims agent turns a wild nutrition claim into a **normalized, content-addressed
claim object** and stress-tests it with a deterministic gauntlet. It ships in the
package as `biology_as_code.agents.assay`.

> **The standard, in one paragraph.** A post becomes a **Source** plus a
> content-addressed **Claim** with one or more **AtomicClaim**s. An 8-attack
> gauntlet — a pure, versioned function — grades it **`BUSTED` · `PLAUSIBLE` ·
> `CONFIRMED`**. You author exactly one small vocabulary (ACA); everything else
> imports FoodOn, ChEBI, MONDO, ECO, Biolink, and friends. See the
> [claim schema](claim-schema.md) and the [source registry](claim-sources.md).

The verdict is deterministic: **the LLM never decides a grade.** Same evidence set +
atoms + rubric version → same verdict. That reproducibility is the whole point — the
failure mode is "refuses / declines", never "confidently wrong". It is the same
verdict family as the in-package [claim auditor](claim-auditor.md), pointed at wild
social claims rather than food packets.

## The 8-attack gauntlet

Each attack interrogates one weakness. Failing a **core** attack busts the claim;
failing only **soft** attacks leaves it plausible.

| Attack | Core? | Fails when… |
|---|---|---|
| Human evidence | ● core | no human study directly supports the wording |
| Dose / form | ● core | studied form ≠ claimed use (extract vs food, clinical vs kitchen) |
| Mechanism vs outcome | ● core | a mechanism is sold as a demonstrated clinical outcome |
| Superlative | ● core | "only / best / permanently" language is falsified |
| Replication | ● core | no independent replication |
| Atomization | ○ soft | a bundle hides weak absolute/superlative atoms behind a kernel |
| Effect size | ○ soft | the effect is trivial, surrogate-only, or unshown in the population |
| Confounding | ○ soft | material confounding or funding concern |

Verdict rule: any core attack fails → **BUSTED**; else soft failures or rebuttals →
**PLAUSIBLE**; survives all → **CONFIRMED** (an evidence-tier judgement, never emitted
by a mechanism walk alone).

## Use it

**Python:**

```python
from biology_as_code.agents.assay import assay_claim

r = assay_claim("Spirulina removes heavy metals from your brain.")
r.claim.verdict.label        # 'BUSTED'
r.claim.scoped_restatement   # the honest version a coach can speak
```

**CLI:**

```bash
python -m biology_as_code.agents.assay test "Creatine increases strength."
python -m biology_as_code.agents.assay golden      # run the golden fixtures
```

**As a service** — a zero-dependency, offline, Lambda-shaped handler at
`biology_as_code.agents.assay.handler:handler`. It runs only the deterministic
gauntlet: no network, no keys, so it cannot fabricate a verdict (bad input → 400).

**Into the contribution gate (Door B)** — an assay verdict becomes a fail-closed
contribution via `biology_as_code.contrib.from_assay.contribute_assay_result`.
Without a primary source it returns `NEEDS_SOURCE`, so the agent can never
auto-accept its own claim. See [Contributing data](contributing-data.md).

## Determinism and the two-engine contract

Scoring is a pure function of `(evidence, atoms, rubric_version)`. A golden fixture
suite pins this engine's verdicts and the bare-16-hex `claim_id`s, and the package's
test suite enforces them in CI. Agreement with the separate TypeScript twin is the
*goal* of the two-engine design, but it is **not yet an enforced cross-repo check** —
the two golden sets can drift until a shared corpus (or a parity job pinning matching
`rubric_version` + identical fixtures) is wired up.

## The one authored vocabulary — ACA

Everything normalizes to an established ontology except the verdict layer. **ACA
(Assay Claim Assessment)** is ~20 terms — the verdict scale plus the eight attack
types — formalized as CC0 SHACL/OWL in
[`schemas/aca.ttl`](https://github.com/murffious/biology_as_code/blob/main/schemas/aca.ttl)
and
[`schemas/claim-shape.ttl`](https://github.com/murffious/biology_as_code/blob/main/schemas/claim-shape.ttl).
