"""
Load optional proprietary product-score analyzer.

Resolution order:
  1. Env ``KIBO_PRODUCT_SCORE_MODULE`` (import path of a module with get_analyzer())
  2. Local ``product_score.proprietary.engine`` (gitignored private file)
  3. Installed package ``kibo_product_score`` (private wheel / path install)

If none load: return unavailable stub (dig/sim still works).
"""

from __future__ import annotations

import importlib
import os
from typing import Any

from .interface import ProductScoreAnalyzer, ProductScoreRequest, ProductScoreResult

_CACHED: ProductScoreAnalyzer | None = None
_LOAD_TRIED = False
_LOAD_ERROR: str | None = None


def unavailable_result(
    status: str = "proprietary_not_installed",
    error: str | None = None,
) -> ProductScoreResult:
    return ProductScoreResult(
        available=False,
        status=status,
        product_score=None,
        axes=None,
        composite=None,
        honesty="n/a",
        detail={
            "how_to_enable": [
                "Set KIBO_PRODUCT_SCORE_MODULE=your.private.module",
                "Or add biology_as_code/product_score/proprietary/engine.py (gitignored)",
                "Or pip-install private package kibo_product_score",
            ],
            "open_path_ok": (
                "Digestion, residual macros, SCFA FLOW, minerals, pathway_regulation, "
                "claim evaluation, and other FLOW process evals run without this module. "
                "Only product MEAL score + Kibo-vars product scorer are gated here."
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


def _try_module(path: str) -> ProductScoreAnalyzer | None:
    mod = importlib.import_module(path)
    if hasattr(mod, "get_analyzer"):
        return mod.get_analyzer()  # type: ignore[no-any-return]
    if hasattr(mod, "analyzer"):
        return mod.analyzer  # type: ignore[no-any-return]
    if hasattr(mod, "ProductScoreEngine"):
        return mod.ProductScoreEngine()  # type: ignore[no-any-return]
    return None


def get_product_score_analyzer(*, force_reload: bool = False) -> ProductScoreAnalyzer | None:
    """Return analyzer instance or None if proprietary code not present."""
    global _CACHED, _LOAD_TRIED, _LOAD_ERROR
    if _LOAD_TRIED and not force_reload:
        return _CACHED
    _LOAD_TRIED = True
    _LOAD_ERROR = None
    _CACHED = None

    candidates = []
    env = os.environ.get("KIBO_PRODUCT_SCORE_MODULE", "").strip()
    if env:
        candidates.append(env)
    candidates.extend(
        [
            "biology_as_code.product_score.proprietary.engine",
            "kibo_product_score",
            "kibo_product_score.engine",
        ]
    )

    for path in candidates:
        try:
            analyzer = _try_module(path)
            if analyzer is not None:
                _CACHED = analyzer
                return _CACHED
        except Exception as exc:  # import errors expected when private
            _LOAD_ERROR = f"{path}: {exc}"
            continue
    return None


def product_score_available() -> bool:
    return get_product_score_analyzer() is not None


def run_product_score_analysis(
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
    Optional product score step.

    Fail-closed: ``enabled`` defaults to ``False`` so a caller must opt in
    explicitly. Even ``enabled=True`` returns an unavailable stub unless the
    proprietary plugin is installed.
    """
    if not enabled:
        return unavailable_result(status="disabled_by_caller").as_dict()

    analyzer = get_product_score_analyzer()
    if analyzer is None:
        return unavailable_result(error=_LOAD_ERROR).as_dict()

    req = ProductScoreRequest(
        payload=payload,
        depth_report=depth_report,
        bridge_report=bridge_report,
        host_context=host_context,
        persona=persona,
        extras=dict(extras or {}),
    )
    try:
        result = analyzer.analyze(req)
        if isinstance(result, ProductScoreResult):
            return result.as_dict()
        if isinstance(result, dict):
            # Allow proprietary engines to return dicts
            out = dict(result)
            out.setdefault("available", True)
            out.setdefault("status", "ok")
            out.setdefault("schema", "kibo.ProductScoreAnalysis/v1")
            out.setdefault(
                "patent_note",
                "Product meal score from proprietary analyzer (patent pending).",
            )
            return out
        return unavailable_result(
            status="invalid_analyzer_return",
            error=f"unexpected type {type(result)}",
        ).as_dict()
    except Exception as exc:
        return unavailable_result(status="analyzer_error", error=str(exc)).as_dict()
