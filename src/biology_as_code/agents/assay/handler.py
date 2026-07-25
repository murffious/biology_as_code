"""
Stateless handler for the deterministic claim scorer (AWS Lambda-shaped).

Zero-dependency and offline: it wraps :func:`assay_claim`, so it is Lambda-native
with no layer wrangling and makes no network calls. The LLM / PubMed harvesting
layer is deliberately *not* here — this handler runs only the deterministic
gauntlet, so it cannot fabricate a verdict. That is the exact property a hosted
claims service needs: the failure mode is "declines / 400", never "confidently
wrong".

Accepted event shapes (direct invoke or API-Gateway proxy)::

    "raw claim text"
    {"claim": "raw claim text", "platform": "api"}
    {"body": "{\\"claim\\": \\"raw claim text\\"}"}   # API Gateway proxy

Returns an API-Gateway-style ``{statusCode, headers, body}`` whose body is the
public assay dict (verdict, atoms, scoped restatement, provenance).
"""

from __future__ import annotations

import json
from typing import Any

from biology_as_code.agents.assay.pipeline import assay_claim, assay_to_public_dict


def _extract_claim(event: Any) -> tuple[str | None, str]:
    """Pull (claim_text, platform) from a direct-invoke or proxy event."""
    if isinstance(event, str):
        text = event.strip()
        return (text or None), "cli"
    if not isinstance(event, dict):
        return None, "api"
    body = event.get("body")
    if isinstance(body, str):
        try:
            event = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return None, "api"
    elif isinstance(body, dict):
        event = body
    if not isinstance(event, dict):
        return None, "api"
    claim = event.get("claim") or event.get("text")
    platform = str(event.get("platform") or "api")
    return (str(claim).strip() or None) if claim else None, platform


def _response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }


def handler(event: Any = None, context: Any = None) -> dict[str, Any]:
    """Lambda entry point. Fail-closed: bad input yields 400, never a crash."""
    claim_text, platform = _extract_claim(event)
    if not claim_text:
        return _response(400, {"error": "missing 'claim' text", "verdict": None})
    result = assay_claim(claim_text, platform=platform)
    public = assay_to_public_dict(result)
    status = 200 if not result.validation_errors else 422
    return _response(status, public)
