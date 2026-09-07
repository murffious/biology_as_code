"""Issue #15 — colonic fermentation without invented SCFA grams."""

from __future__ import annotations

from biology_as_code.dig.colon_fermentation import (
    FiberType,
    SCFAType,
    process_fiber,
)


def test_missing_input_is_unevaluable_not_zero():
    silent = process_fiber(None, None)
    assert silent.state == "UNEVALUABLE"
    assert silent.gate == "unknown"
    assert silent.products == ()
    assert silent.amounts == {}


def test_zero_substrate_closes_the_gate():
    zero = process_fiber(0, FiberType.SOLUBLE)
    assert zero.state == "REFUTED"
    assert zero.gate == "closed"
    assert zero.products == ()


def test_positive_substrate_holds_product_identity_not_grams():
    result = process_fiber(12, FiberType.RESISTANT_STARCH)
    assert result.state == "HOLDS"
    assert result.gate == "open"
    assert set(result.products) == {
        SCFAType.ACETATE,
        SCFAType.PROPIONATE,
        SCFAType.BUTYRATE,
    }
    assert result.amounts == {
        "acetate": None,
        "propionate": None,
        "butyrate": None,
    }
    assert "0.40" not in result.note
    assert "0.35" not in result.note


def test_string_fiber_type_accepted():
    result = process_fiber(5, "soluble_fiber")
    assert result.state == "HOLDS"
    assert result.fiber_type is FiberType.SOLUBLE


def test_unknown_type_is_unevaluable():
    result = process_fiber(5, "inulin_brand_x")
    assert result.state == "UNEVALUABLE"


def test_negative_fiber_is_refused():
    result = process_fiber(-1, FiberType.SOLUBLE)
    assert result.state == "REFUSE"


def test_no_invented_law_id():
    result = process_fiber(8, FiberType.SOLUBLE)
    blob = str(result.to_dict())
    assert "LAW-048" not in blob
    assert result.provenance["pmid"] == "12740060"
