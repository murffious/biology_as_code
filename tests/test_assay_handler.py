"""The deterministic claim scorer as a stateless (Lambda-shaped) handler."""

from __future__ import annotations

import json

from biology_as_code.agents.assay.handler import handler


def test_scores_direct_invoke():
    resp = handler({"claim": "Creatine increases strength."})
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["verdict"]["label"] in {"CONFIRMED", "PLAUSIBLE", "BUSTED"}
    assert len(body["claim_id"]) == 16


def test_scores_api_gateway_proxy():
    event = {"body": json.dumps({"claim": "Spirulina removes heavy metals from your brain."})}
    resp = handler(event)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["verdict"]["label"] == "BUSTED"


def test_scores_bare_string_event():
    resp = handler("Creatine increases strength.")
    assert resp["statusCode"] == 200


def test_missing_claim_is_400():
    assert handler({})["statusCode"] == 400
    assert handler({"claim": ""})["statusCode"] == 400
    assert handler({"body": ""})["statusCode"] == 400


def test_never_raises_on_junk():
    for junk in (None, 123, [], "   ", {"body": "not json"}):
        resp = handler(junk)
        assert resp["statusCode"] in (200, 400, 422)
