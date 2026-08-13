# Digestion machines (open teaching layer)

Each GI **stage** is one versioned JSON file describing a Step-Functions-style
state graph: `states` with a `startAt`, transitions (`next` / `choices` /
`default`), physiological `edgeCases`, and teaching time windows. The app/code
reads them through `registry.json` and never hard-codes stage data — that's the
"biology as code" point.

```
machines/
  data/registry.json               # index: id -> {version, revision, status, hash}
  data/_schema/machine.schema.json # the format (JSON Schema draft 2020-12)
  data/stage/<name>.json           # one machine per digestion stage
  data/process/<name>.json         # top-level sequence over stage ids
```

Shipped machines: **stages** `oral → stomach → duodenum → jejunum → colon`, and
the **process** `full-digest` that chains them (with a host/intake gate).

State types: `task` (a step), `choice` (branch, first match wins), `gate`
(precondition), `succeed` (terminal). Conditions are declarative and
inspectable — `{field, op, value}` or `{all/any/not: [...]}` — never executable code.
Time windows are `windowH: [centerHours, durationHours]` (both ≥ 0), not start/end.

## Open tier only

These machines are **FLOW teaching** artifacts. They deliberately carry **no**
scoring `penalties`, product-score gates, or vendor-scoring hooks — the validator
(`validate_all()`) fails if any score-shaped field ever leaks in. Product scoring
lives in the separate patent-pending engine (see `PROPRIETARY_IP.md`).

## Usage

```python
from biology_as_code.machines import list_machines, get_machine, validate_all

list_machines()                          # 5 stages + process.full-digest
get_machine('stage.duodenum')['states']  # inspect the graph
validate_all()                           # {'ok': True, 'n': 6, 'errors': []}
```

## Editing a machine

1. Edit the stage JSON. 2. Bump `revision` (+1) in the file and its `registry.json`
row (and `version` if human-notable). 3. Recompute the `hash`
(`content_hash(get_machine(id))`) into the registry row. `validate_all()` fails on
hash drift, dangling transitions, or a missing `startAt`.
