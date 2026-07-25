"""
Guards the discipline behind ``scripts/fill_packets.py``.

The script declares facts that follow from a food's identity — a lipid phase in
olive oil, a destroyed matrix in a flour, tannins in tea. Those are safe. What
would not be safe is letting magnitudes in through the same door, or losing the
ability to tell an inference from identity apart from measured data.

These tests hold that line. If a future fill writes a gram value, collapses
``label_amount``, or drops the provenance marker, they fail.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from biology_as_code.audit import audit_packet_coverage
from biology_as_code.packets import iter_packets, validate_packet

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "fill_packets.py"

# Fields that carry a magnitude. A structural fill must never write one.
MAGNITUDE_FIELDS = {"dietary_lipid_g", "calcium_mg", "phytate_mg", "ascorbate_mg"}


def structural_entries(packet) -> list[dict]:
    return [
        entry
        for entry in (*packet.cargo, *packet.partners)
        if entry.get("derivation") == "structural"
    ]


def test_no_structural_declaration_carries_a_magnitude():
    """The whole point of the boolean gate alternative is to avoid inventing grams."""
    offenders = []
    for packet in iter_packets():
        for entry in structural_entries(packet):
            if entry.get("field") in MAGNITUDE_FIELDS:
                offenders.append((packet.id, entry["field"]))
    assert not offenders, f"structural fill wrote a magnitude: {offenders}"


def test_structural_cargo_keeps_label_amount_open():
    """Presence is structural. Quantity is not, and must stay unlocked."""
    for packet in iter_packets():
        for entry in packet.cargo:
            if entry.get("derivation") == "structural":
                assert entry.get("label_amount") == "open", (
                    f"{packet.id}: structural cargo {entry.get('nutrient')} locked a quantity"
                )


def test_every_structural_declaration_states_a_rationale():
    """An unexplained inference is indistinguishable from a guess."""
    for packet in iter_packets():
        for entry in structural_entries(packet):
            rationale = entry.get("rationale", "")
            assert len(rationale) > 15, f"{packet.id}: thin rationale on {entry}"
        if packet.matrix.get("derivation") == "structural":
            assert len(packet.matrix.get("rationale", "")) > 15, f"{packet.id}: thin matrix rationale"


def test_filled_packets_still_validate_against_the_schema():
    for packet in iter_packets():
        result = validate_packet(packet)
        assert result.valid, (packet.id, result.errors)


def test_the_fill_is_idempotent():
    """Re-running the script must be a no-op, or it is not a declarative fill."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert "0 packets would be updated" in result.stdout, (
        "fill_packets.py is not idempotent; re-running changes packets:\n" + result.stdout
    )


def test_skipped_packets_stay_stubs():
    """Ambiguous foods must remain undecidable rather than get a confident verdict."""
    namespace: dict = {"__file__": str(SCRIPT), "__name__": "fill_packets_under_test"}
    exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), namespace)  # noqa: S102
    skipped = namespace["SKIPPED"]
    assert skipped, "the skip list should not be empty; some foods are genuinely ambiguous"

    by_stem = {}
    for path in (REPO_ROOT / "examples" / "foods").glob("*.json"):
        by_stem[path.stem] = json.loads(path.read_text(encoding="utf-8"))

    for stem, reason in skipped.items():
        assert stem in by_stem, f"skip list names a missing packet: {stem}"
        entries = (*by_stem[stem].get("cargo", []), *(by_stem[stem].get("partners") or []))
        assert not any(e.get("derivation") == "structural" for e in entries), (
            f"{stem} is on the skip list ({reason}) but was filled anyway"
        )


@pytest.mark.parametrize("nutrient", ["beta_carotene", "lipid", "nonhaem_iron"])
def test_coverage_still_reports_honestly(nutrient: str):
    """Filling packets must not silently turn undecidable claims into verdicts."""
    packets = list(iter_packets())
    coverage = audit_packet_coverage(packets, nutrient, "bound_increase")
    assert sum(coverage.values()) == len(packets)
    assert coverage.get("UNEVALUABLE", 0) > 0, (
        f"{nutrient}: no packet is undecidable, which would be surprising given 12 "
        "packets are deliberately unfilled"
    )


def test_decidable_share_is_reported_not_assumed():
    """Among packets that declare the cargo, most should now be decidable.

    This is the metric that actually measures the fill. Raw coverage across all 46
    packets is dominated by foods that do not contain the nutrient at all, where
    UNEVALUABLE is the correct and permanent answer.
    """
    packets = [p for p in iter_packets() if "beta_carotene" in p.cargo_nutrients()]
    assert packets, "no packet declares beta_carotene"
    coverage = audit_packet_coverage(packets, "beta_carotene")
    decidable = coverage.get("Busted", 0) + coverage.get("Plausible", 0)
    assert decidable == len(packets), (
        f"every carotenoid-bearing packet should now resolve; got {coverage}"
    )
