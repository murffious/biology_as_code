# `tests/conformance/` — the frozen truth

These are not unit tests. They are the specification's **acceptance criteria**:
five published human results the engine is required to reproduce before it can
claim to model what it says it models. Each one encodes a number a ward or a
metabolic-kitchen study actually measured, with the tolerance it is allowed to
miss by and the citation it came from.

## The rules

1. **Every test states a tolerance, and the tolerance is part of the test.**
   A conformance test with an unstated or elastic tolerance is a test that
   passes whatever the engine does.

2. **Never weaken a tolerance to make a test pass.** Tolerances change only
   with a cited justification in the commit that changes them — a different
   paper, a re-analysis, a measurement error identified in the original. "The
   model was close" is not a justification.

3. **They start as `xfail(strict=True)`.** The mechanism each one needs does
   not exist yet. Strict is deliberate: when the mechanism lands the test
   *passes*, strict xfail turns that pass into a failure, and someone has to
   come here and remove the marker. A conformance target cannot be met
   silently.

4. **The engine is called for real.** Where today's engine can compute
   something, these tests compute it and assert on the answer. Where the
   engine has no mechanism at all, the harness raises `MechanismMissing`
   naming precisely what is absent, so the xfail reason is a specification
   gap rather than a stack trace.

## The five, and what has to land for each

| # | Study | Asserts | Flips when |
|---|---|---|---|
| 1 | Hall 2019 | UPF vs unprocessed ad libitum intake, +508 kcal/day ±40% | oral + gastric + an intake controller exist |
| 2 | Novotny 2012 | Atwater overestimates whole-almond ME by ~32% ±10 pts | encapsulation-gated bioaccessibility law lands |
| 3 | Hjerpsted 2011 | cheese vs butter LDL divergence, **direction only** | a lipoprotein response exists — and the mechanism must stay unresolved |
| 4 | Forde et al. | texture-driven eating rate, −369 kcal ±40% | a bite-clock oral process and an intake controller exist |
| 5 | whole vs ground grain | glycemic response ordering, **ordinal only** | matrix acts on carbohydrate release rate |

Tests 2 and 5 are closest: both are computed end-to-end against the real
engine today and fail on the assertion, not on a missing API. They will flip
as soon as the bioaccessibility gate makes absorption depend on
`method_identity` instead of on grams alone.

Test 3 is deliberately weaker than the others. The cheese-versus-butter
divergence is replicated; the *mechanism* is not settled — calcium-driven
faecal fat loss is one candidate among several, and the matrix itself may be
doing the work. Asserting direction only is the honest encoding, and the test
explicitly guards against the model hard-coding a faecal-fat explanation.
