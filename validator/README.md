# FDP-1 reference validator

A small, dependency-free checker for the [FDP-1 Food Data Provenance
Declaration](../FDP-1-food-data-provenance.md). It mechanically tests a JSON
document against the five conformance requirements of FDP-1 §6.

The specification is the contract; this validator is the proof the contract is
real. It is intentionally short (pure Python ≥ 3.11, standard library only).

## Run it

```bash
python validator/validate_fdp.py examples/iron-two-hosts.json
# or pipe a declaration on stdin:
python validator/validate_fdp.py < my-declaration.json
```

Exit status is `0` when every value and score conforms, `1` otherwise, so it
drops straight into CI or a pre-commit hook.

## What it checks (FDP-1 §6)

1. **Six fields on every value** (§2) — `value`, `unit`, `source`,
   `source_ref`, `method`, `retrieved`.
2. **Five fields on every score** (§3) — `score_id`, `inputs`,
   `provenance_grade`, `weights_published`, `validation`.
3. **The weakest-link rule (§3.1) is recomputed, not trusted.** The validator
   derives each input's grade from its `source`, takes the worst, and rejects a
   `provenance_grade` that claims better than its inputs support.
4. **Unknowns are the literal `OPEN` (§4)** — a `null` or empty field is
   non-conforming; silence and "not known" are different statements.
5. **Validation honesty (§3.2)** — a `validation.level` above `none` must carry
   a `citation`.

Conformance says nothing about whether a score is *correct*. It says only that a
reader can determine what a score was computed from and what evidence supports
it — the entire scope of FDP-1.

## Document shape

```json
{
  "values": { "<name>": { "value": ..., "unit": ..., "source": ...,
                          "source_ref": ..., "method": ..., "retrieved": ... } },
  "scores": [ { "score_id": ..., "inputs": ["<name>", ...],
                "provenance_grade": ..., "weights_published": ...,
                "validation": { "level": ..., "citation": ... } } ]
}
```

See [`examples/iron-two-hosts.json`](../examples/iron-two-hosts.json) for a
worked declaration: one food, full provenance on every input, evaluated for two
host states.
