"""Food packet loader + zero-dependency schema validator."""

from __future__ import annotations

import pytest

from biology_as_code.packets import (
    FoodPacket,
    PacketNotFound,
    PacketsUnavailable,
    get_packet,
    iter_packets,
    list_packets,
    packet_schema,
    packets_dir,
    unsupported_keywords,
    validate_against,
    validate_packet,
)

# The six packets filled in by hand before scripts/fill_packets.py existed. These
# carry no `derivation` marker, which is how a hand-authored packet is told apart
# from a structural inference.
HAND_FILLED_IDS = {
    "ex.almond.flour",
    "ex.almond.whole",
    "ex.lentils.with_ascorbate",
    "ex.lentils.with_tea",
    "ex.spinach_salad.with_oil",
    "ex.spinach_salad.zero_fat",
}


def test_packets_dir_resolves_in_repo():
    assert packets_dir().is_dir()


def test_every_packet_validates_against_schema():
    """All shipped packets must satisfy schemas/food_packet.schema.json."""
    failures = []
    for packet in iter_packets():
        result = validate_packet(packet)
        if not result:
            failures.append((packet.id, result.errors))
    assert not failures, f"packets failed schema validation: {failures}"


def test_validator_covers_every_keyword_the_schema_uses():
    """Guard the validator's declared blind spot.

    If someone adds a JSON Schema keyword the validator cannot check, this fails
    rather than letting an unchecked schema silently report a pass.
    """
    unsupported = unsupported_keywords(packet_schema())
    assert unsupported == [], f"schema uses unsupported keywords: {unsupported}"


def test_ids_are_unique():
    ids = list_packets()
    assert len(ids) == len(set(ids))


def test_hand_filled_packets_carry_no_structural_derivation_marker():
    """The original six are authored, not inferred, and must stay distinguishable."""
    for packet in iter_packets():
        if packet.id not in HAND_FILLED_IDS:
            continue
        markers = [
            entry
            for entry in (*packet.cargo, *packet.partners)
            if entry.get("derivation") == "structural"
        ]
        assert not markers, f"{packet.id} gained a structural inference: {markers}"
        assert packet.matrix.get("derivation") != "structural"


def test_every_filled_packet_is_either_authored_or_marked_structural():
    for packet in iter_packets():
        if not packet.is_filled or packet.id in HAND_FILLED_IDS:
            continue
        marked = any(
            entry.get("derivation") == "structural"
            for entry in (*packet.cargo, *packet.partners)
        ) or packet.matrix.get("derivation") == "structural"
        assert marked, f"{packet.id} is filled but records no provenance for how"


def test_template_is_skipped():
    assert not any(p.id.startswith("ex.template") for p in iter_packets())
    assert "_template.json" in {p.name for p in packets_dir().glob("*.json")}


def test_declares_distinguishes_absent_from_false():
    """The whole auditor rests on this: silence is not a zero."""
    zero_fat = get_packet("ex.spinach_salad.zero_fat")
    assert zero_fat.declares("dietary_lipid_g") is True
    assert zero_fat.partner("dietary_lipid_g") == 0

    stub = get_packet("ex.banana")
    assert stub.declares("dietary_lipid_g") is False
    assert stub.partner("dietary_lipid_g") is None


def test_matrix_integrity_defaults_to_unknown():
    assert get_packet("ex.almond.whole").matrix_integrity == "intact"
    assert get_packet("ex.almond.flour").matrix_integrity == "destroyed"
    assert get_packet("ex.lentils.with_ascorbate").matrix_integrity == "unknown"


def test_cargo_nutrients():
    assert get_packet("ex.spinach_salad.with_oil").cargo_nutrients() == (
        "beta_carotene",
        "phylloquinone",
    )


def test_get_packet_unknown_id_raises():
    with pytest.raises(PacketNotFound):
        get_packet("ex.does.not.exist")


def test_missing_directory_raises_rather_than_returning_empty():
    """Fail closed: an unreachable directory must not look like 'no packets'."""
    with pytest.raises(PacketsUnavailable):
        list_packets(directory="/nonexistent/path/for/test")


def test_from_dict_requires_id_and_identity():
    with pytest.raises(ValueError):
        FoodPacket.from_dict({"id": "ex.x"})


def test_status_defaults_to_stub():
    packet = FoodPacket.from_dict({"id": "ex.x", "identity": {"common_name": "x"}})
    assert packet.status == "stub"
    assert packet.is_filled is False


# --- validator unit tests ----------------------------------------------------


def test_validator_rejects_bad_type_and_enum():
    schema = {
        "type": "object",
        "required": ["a"],
        "properties": {"a": {"type": "string", "enum": ["x", "y"]}},
    }
    assert validate_against({"a": "x"}, schema).valid
    assert not validate_against({"a": "z"}, schema).valid
    assert not validate_against({"a": 1}, schema).valid
    assert not validate_against({}, schema).valid


def test_validator_treats_bool_as_not_a_number():
    schema = {"type": "number"}
    assert not validate_against(True, schema).valid


def test_validator_pattern_and_oneof():
    schema = {"type": "string", "pattern": r"^ex\.[a-z]+$"}
    assert validate_against("ex.banana", schema).valid
    assert not validate_against("EX.Banana", schema).valid

    one_of = {"oneOf": [{"type": "string", "const": "open"}, {"type": "object"}]}
    assert validate_against("open", one_of).valid
    assert validate_against({}, one_of).valid
    assert not validate_against(7, one_of).valid


def test_validation_result_is_falsy_when_invalid():
    assert not validate_against(1, {"type": "string"})
    assert validate_against("a", {"type": "string"})
