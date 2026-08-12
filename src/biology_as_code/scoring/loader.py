"""
Load an optional external scorer.

Resolution order:
  1. Env ``BAC_SCORER_MODULE`` — import path of a module exposing
     ``get_analyzer()`` (or ``analyzer`` / ``ScorerEngine``).
  2. Nothing else.

There is deliberately no second, "blessed" package name to fall back on. A
single documented entry point means no vendor is privileged by the open tree,
and the resolution result is always explainable from one environment variable.

If no scorer loads, an unavailable stub is returned and digestion/simulation
continue unaffected.
"""

from __future__ import annotations

import importlib
import os
from typing import Any

from .interface import SCHEMA_ID, ScoreRequest, ScoreResult, ScorerPlugin

#: Single documented entry point for an out-of-tree scorer.
SCORER_ENV_VAR = "BAC_SCORER_MODULE"

_CACHED: ScorerPlugin | None = None
_LOAD_TRIED = False
_LOAD_ERROR: str | None = None


def unavailable_result(
    status: str = "external_scorer_not_installed",
    error: str | None = None,
) -> ScoreResult:
    return ScoreResult(
        available=False,
        status=status,
        product_score=None,
        axes=None,
        composite=None,
        honesty="n/a",
        detail={
            "how_to_enable": [
                f"Set {SCORER_ENV_VAR}=your.module (module exposes get_analyzer())",
            ],
            "open_path_ok": (
                "Digestion, residual macros, SCFA FLOW, minerals, pathway_regulation, "
                "claim evaluation, and other FLOW process evals run without a scorer. "
                "Only the external composite is gated here."
            ),
            "not_this_module": [
                "claim support|partial|refuse",
                "enzyme capacity / residual macros",
                "SCFA / colonic medium FLOW",
                "pathway_regulation activities",
                "teaching energy_charge / flow_teaching_meter",
            ],
        },
        error=error,
    )


def _try_module(path: str) -> ScorerPlugin | None:
    mod = importlib.import_module(path)
    if hasattr(mod, "get_analyzer"):
        return mod.get_analyzer()  # type: ignore[no-any-return]
    if hasattr(mod, "analyzer"):
        return mod.analyzer  # type: ignore[no-any-return]
    if hasattr(mod, "ScorerEngine"):
        return mod.ScorerEngine()  # type: ignore[no-any-return]
    return None


def get_external_scorer(*, force_reload: bool = False) -> ScorerPlugin | None:
    """Return the configured scorer, or None when none is configured."""
    global _CACHED, _LOAD_TRIED, _LOAD_ERROR
    if _LOAD_TRIED and not force_reload:
        return _CACHED
    _LOAD_TRIED = True
    _LOAD_ERROR = None
    _CACHED = None

    path = os.environ.get(SCORER_ENV_VAR, "").strip()
    if not path:
        return None

    try:
        _CACHED = _try_module(path)
    except Exception as exc:  # import errors are expected when unconfigured
        _LOAD_ERROR = f"{path}: {exc}"
        _CACHED = None
    if _CACHED is None and _LOAD_ERROR is None:
        _LOAD_ERROR = f"{path}: module exposes no get_analyzer/analyzer/ScorerEngine"
    return _CACHED


def external_scorer_available() -> bool:
    return get_external_scorer() is not None


def run_external_score_analysis(
    *,
    payload: Any = None,
    depth_report: dict[str, Any] | None = None,
    bridge_report: dict[str, Any] | None = None,
    host_context: dict[str, Any] | None = None,
    persona: dict[str, Any] | None = None,
    extras: dict[str, Any] | None = None,
    enabled: bool = False,
) -> dict[str, Any]:
    """
    Optional external scoring step.

    Fail-closed: ``enabled`` defaults to ``False`` so a caller must opt in
    explicitly. Even ``enabled=True`` returns an unavailable stub unless a
    scorer is configured.
    """
    if not enabled:
        return unavailable_result(status="disabled_by_caller").as_dict()

    analyzer = get_external_scorer()
    if analyzer is None:
        return unavailable_result(error=_LOAD_ERROR).as_dict()

    req = ScoreRequest(
        payload=payload,
        depth_report=depth_report,
        bridge_report=bridge_report,
        host_context=host_context,
        persona=persona,
        extras=dict(extras or {}),
    )
    try:
        result = analyzer.analyze(req)
        if isinstance(result, ScoreResult):
            return result.as_dict()
        if isinstance(result, dict):
            # Allow scorers to return plain dicts.
            out = dict(result)
            out.setdefault("available", True)
            out.setdefault("status", "ok")
            out.setdefault("schema", SCHEMA_ID)
            out.setdefault(
                "provenance_note",
                "Score produced by an external plugin outside this repository.",
            )
            return out
        return unavailable_result(
            status="invalid_scorer_return",
            error=f"unexpected type {type(result)}",
        ).as_dict()
    except Exception as exc:
        return unavailable_result(status="scorer_error", error=str(exc)).as_dict()
