# `scoring/` — external scorer plugin interface

**This package contains no scoring algorithm and never will.** It is the
documented boundary at which *any* conforming external scorer — commercial,
academic, or your own — can be called by the engine, and the fail-closed stub
returned when none is present.

The open tree evaluates freely: residual macros, enzyme capacity, SCFA and
colonic medium FLOW, minerals, `pathway_regulation` activities, claim
`support | partial | refuse`, and the teaching meters. None of that goes
through this package. Only a scorer's own composite does.

## The contract

An external scorer is any importable module exposing one of:

```python
def get_analyzer():        # preferred
    return MyScorer()

analyzer = MyScorer()      # or a module-level instance
class ScorerEngine: ...    # or a zero-arg constructible class
```

whose object implements `analyze`:

```python
from biology_as_code.scoring import ScoreRequest, ScoreResult

class MyScorer:
    def analyze(self, request: ScoreRequest) -> ScoreResult:
        ...
```

`ScorerPlugin` is a `runtime_checkable` `Protocol`, so `isinstance` works
without your class importing anything from this repository.

### Inputs (`ScoreRequest`)

| Field | Meaning |
|---|---|
| `payload` | the food/meal payload as given to the engine |
| `depth_report` | the engine's full meal report |
| `bridge_report` | the LAW-tagged bridge report, when one was produced |
| `host_context` | host state passed by the caller |
| `persona` | persona dict, when the caller supplied one |
| `extras` | free-form caller passthrough |

All are optional; a scorer must tolerate `None`.

### Output (`ScoreResult`)

| Field | Meaning |
|---|---|
| `available` | False means no scoring happened |
| `status` | machine-readable outcome |
| `product_score` | the scorer's single headline number, opaque to us |
| `vendor_scores` | any further named values the scorer returns |
| `axes` / `composite` | optional breakdowns, shape defined by the scorer |
| `honesty` | provenance marker; `"external"` by default |
| `error` | populated on failure |

Serialised results always carry `schema: "bac.ExternalScoreAnalysis/v1"`.

Returning a plain `dict` instead of a `ScoreResult` is allowed; the loader
fills in `available`, `status`, `schema` and `provenance_note` defaults.

## Enabling a scorer

One entry point, one environment variable:

```bash
export BAC_SCORER_MODULE=my_org.my_scorer
```

There is no second, blessed package name to fall back on — no vendor is
privileged by the open tree, and resolution is always explainable from that
one variable. If it is unset or the import fails, every call returns the
unavailable stub.

## Fail-closed behaviour

```python
from biology_as_code.scoring import (
    run_external_score_analysis,
    external_scorer_available,
)

# default: not even attempted
run_external_score_analysis(depth_report=report)
# → {"available": False, "status": "disabled_by_caller", ...}

# opted in, but nothing configured
run_external_score_analysis(depth_report=report, enabled=True)
# → {"available": False, "status": "external_scorer_not_installed", ...}
```

`MealEngine` and `UnifiedFacade` both default to
`enable_external_score=False`. A scorer runs only when a caller opts in *and*
one is configured.
