"""Eleven standard medical body systems.

Five adapters ship. Six are PARKED so the table can print eleven rows
without inventing walks.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemSpec:
    id: str
    name: str
    uberion_hint: str
    shipped: bool
    default_gates: tuple[str, ...]
    why: str


BODY_SYSTEMS: tuple[SystemSpec, ...] = (
    SystemSpec(
        id="integumentary",
        name="Integumentary",
        uberion_hint="UBERON:0002416",
        shipped=False,
        default_gates=(),
        why="Parked. Skin-barrier and carotenoid-pigment walks exist in the literature; not coded here.",
    ),
    SystemSpec(
        id="skeletal",
        name="Skeletal",
        uberion_hint="UBERON:0001434",
        shipped=False,
        default_gates=(),
        why="Parked. Ca/P/vitamin D walks need host stores; packet-only meals cannot close them.",
    ),
    SystemSpec(
        id="muscular",
        name="Muscular",
        uberion_hint="UBERON:0000062",
        shipped=False,
        default_gates=(),
        why="Parked. Protein-quality + load interaction is host+clock, not meal-only.",
    ),
    SystemSpec(
        id="nervous",
        name="Nervous",
        uberion_hint="UBERON:0001016",
        shipped=True,
        default_gates=("eating_rate_reward", "glycemic_swing_sleep", "diet_to_brain_mnp"),
        why="Shipped. Reward/eating-rate may HOLD when declared; diet→brain MNPs REFUSE.",
    ),
    SystemSpec(
        id="endocrine",
        name="Endocrine",
        uberion_hint="UBERON:0000949",
        shipped=True,
        default_gates=("insulin_gi_fii", "incretin_distal_contact", "clock_cortisol"),
        why="Shipped. GI is not FII; distal-gut incretin walk is OPEN on most packets.",
    ),
    SystemSpec(
        id="cardiovascular",
        name="Cardiovascular",
        uberion_hint="UBERON:0004535",
        shipped=True,
        default_gates=("sodium_load", "energy_surplus_bp", "apob_sat_fat"),
        why="Shipped. Na and energy-surplus gates only when those fields are declared.",
    ),
    SystemSpec(
        id="immune",
        name="Lymphatic / immune",
        uberion_hint="UBERON:0002193",
        shipped=True,
        default_gates=("fiber_scfa_barrier", "emulsifier_mucus", "lps_tlr4"),
        why="Shipped. Human end-to-end walks mostly OPEN; emulsifier gate needs a declared additive.",
    ),
    SystemSpec(
        id="respiratory",
        name="Respiratory",
        uberion_hint="UBERON:0001004",
        shipped=False,
        default_gates=(),
        why="Parked. Aspiration and metabolic-CO2 walks are out of scope for a meal packet.",
    ),
    SystemSpec(
        id="digestive",
        name="Digestive",
        uberion_hint="UBERON:0001007",
        shipped=True,
        default_gates=("matrix_disintegration", "eating_rate", "micelle_fat_vehicle", "transit_fiber"),
        why="Shipped first. This is the existing digestion-machine seat.",
    ),
    SystemSpec(
        id="urinary",
        name="Urinary",
        uberion_hint="UBERON:0001008",
        shipped=False,
        default_gates=(),
        why="Parked. Renal solute load needs host GFR and not just meal Na/protein.",
    ),
    SystemSpec(
        id="reproductive",
        name="Reproductive",
        uberion_hint="UBERON:0000990",
        shipped=False,
        default_gates=(),
        why="Parked. Energy-availability and steroid walks are host-state, not meal-only.",
    ),
)

_BY_ID = {s.id: s for s in BODY_SYSTEMS}


def get_system(system_id: str) -> SystemSpec:
    try:
        return _BY_ID[system_id]
    except KeyError as exc:
        raise KeyError(f"unknown system_id: {system_id}") from exc


def shipped_systems() -> tuple[SystemSpec, ...]:
    return tuple(s for s in BODY_SYSTEMS if s.shipped)


def parked_systems() -> tuple[SystemSpec, ...]:
    return tuple(s for s in BODY_SYSTEMS if not s.shipped)
