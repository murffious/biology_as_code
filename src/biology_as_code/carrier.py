"""
The unified carrier: one ``DigestRun`` object both the app and the engine consume.

Why this module exists
----------------------
The running input to digestion — *who is eating* (host) + *what is on the plate*
(packet) + *how it enters the mouth* (ingestion) — used to be expressed two
different ways: the TypeScript app validated JSON against ``HostState`` /
``PacketLoad`` / ``IngestionEvent`` / ``DigestRun`` schemas, while the Python
engine took a :class:`~biology_as_code.digestion.conditions.Conditions` dataclass.
Same concept, two encodings — so the two sides could disagree about what the input
even was.

This module makes the **JSON DigestRun the single source of truth**. The exact
same file the app validates is loaded here, checked against the *same* schemas
(shipped under ``machines/data/schemas/``), and flattened into the machine context
by :func:`to_machine_context` — a field-for-field port of the app's
``toMachineContext`` (``src/lib/machines/digestRun.ts``). ``Conditions`` does not
go away: it becomes a *typed view* over a DigestRun (:func:`conditions_from_digest_run`),
not a rival encoding.

Design constraints kept
-----------------------
* **Zero dependency.** Validation reuses the repo's own tiny JSON-Schema subset
  validator (:mod:`biology_as_code.packets.validate`) — no ``jsonschema``, no
  ``pydantic``. Each component (host / packet / ingestion) is validated against its
  own schema file. This is a shape/required-fields gate, not a full JSON-Schema
  check: ``$ref`` items and numeric ``min``/``max`` are not enforced (surfaced on
  ``validate_digest_run(...).skipped_keywords``).
* **Fail-closed, with app parity.** :func:`to_machine_context` reproduces the app's
  ``enrichDigestRun`` + ``toMachineContext`` for the host + packet + ingestion input
  (including the chew→mastication derivation and teaching defaults), so the same
  DigestRun yields the same context. ``clinical`` / ``goals`` are **not** folded in
  yet (see :func:`to_machine_context`) — that boundary is explicit, not silent.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from biology_as_code.digestion.conditions import Conditions
from biology_as_code.machines.digestion import run_digestion
from biology_as_code.packets.validate import ValidationResult, validate_against

SCHEMA_DIR = Path(__file__).resolve().parent / "machines" / "data" / "schemas"


class DigestRunInvalid(ValueError):
    """Raised when a DigestRun (or one of its components) fails schema validation."""

    def __init__(self, errors: tuple[str, ...]):
        self.errors = errors
        super().__init__("; ".join(errors) or "invalid DigestRun")


@lru_cache(maxsize=None)
def load_carrier_schema(name: str) -> dict[str, Any]:
    """Load a carrier JSON Schema by file name, e.g. ``HostState.schema.json``."""
    path = SCHEMA_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"carrier schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# DigestRun value object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DigestRun:
    """One carrier object: host + packet (+ optional ingestion / clinical / goals).

    A thin, read-only view over the JSON. Mirrors ``DigestRun.schema.json`` — the
    exact shape the app produces and validates. ``host`` and ``packet`` are
    required; everything else is optional and defaults to empty.
    """

    host: dict[str, Any]
    packet: dict[str, Any]
    ingestion: dict[str, Any] = field(default_factory=dict)
    clinical: dict[str, Any] = field(default_factory=dict)
    goals: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    process_id: str = "process.full-digest"
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def common_name(self) -> str:
        return str(self.packet.get("name") or self.packet.get("id") or self.id or "meal")


def _validate_component(instance: Any, schema_name: str, label: str) -> ValidationResult:
    """Validate one component against its own schema; prefix errors with ``label``."""
    result: ValidationResult = validate_against(instance, load_carrier_schema(schema_name))
    return ValidationResult(
        valid=result.valid,
        errors=tuple(f"{label}: {e}" for e in result.errors),
        skipped_keywords=result.skipped_keywords,
    )


def validate_digest_run(obj: dict[str, Any]) -> ValidationResult:
    """Validate a DigestRun dict by checking each component against its schema.

    Not a full JSON-Schema check. The composite ``DigestRun.schema.json`` is
    ``$ref``-based, and the zero-dep subset validator does not resolve ``$ref`` or
    enforce numeric ``minimum``/``maximum`` — so nested ``$defs`` items (ingredient
    items, sequence steps) and range bounds pass unchecked. Those skipped keywords
    are surfaced on the result's ``skipped_keywords`` so a caller can refuse to trust
    a pass; this is a **shape + required-fields** gate, weaker than the app's Ajv.
    """
    errors: list[str] = []
    skipped: set[str] = set()
    if not isinstance(obj, dict):
        return ValidationResult(valid=False, errors=("DigestRun must be an object",))
    if "host" not in obj:
        errors.append("DigestRun: missing required 'host'")
    if "packet" not in obj:
        errors.append("DigestRun: missing required 'packet'")
    checks = [("host", "HostState.schema.json"), ("packet", "PacketLoad.schema.json")]
    if obj.get("ingestion"):
        checks.append(("ingestion", "IngestionEvent.schema.json"))
    for key, schema_name in checks:
        if key in obj:
            r = _validate_component(obj[key], schema_name, key)
            errors.extend(r.errors)
            skipped.update(r.skipped_keywords)
    return ValidationResult(valid=not errors, errors=tuple(errors), skipped_keywords=tuple(sorted(skipped)))


def load_digest_run(source: dict[str, Any] | str | Path, *, validate: bool = True) -> DigestRun:
    """Build a :class:`DigestRun` from a dict or a path to a DigestRun JSON file.

    With ``validate=True`` (default) the object is checked against the shared
    carrier schemas first, raising :class:`DigestRunInvalid` on failure. This is a
    shape/required-fields gate (see :func:`validate_digest_run` for its blind spots),
    not a full re-implementation of the app's validator.
    """
    if isinstance(source, (str, Path)):
        obj = json.loads(Path(source).read_text(encoding="utf-8"))
    else:
        obj = source
    if validate:
        result = validate_digest_run(obj)
        if not result.valid:
            raise DigestRunInvalid(result.errors)
    return DigestRun(
        host=dict(obj.get("host") or {}),
        packet=dict(obj.get("packet") or {}),
        ingestion=dict(obj.get("ingestion") or {}),
        clinical=dict(obj.get("clinical") or {}),
        goals=dict(obj.get("goals") or {}),
        id=obj.get("id"),
        process_id=obj.get("process_id", "process.full-digest"),
        raw=dict(obj),
    )


# ---------------------------------------------------------------------------
# The bridge: DigestRun -> flat machine context (port of TS toMachineContext)
# ---------------------------------------------------------------------------


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _chew_seconds_to_quality(chew_s: float) -> float:
    """Chew-seconds -> mastication-quality teaching curve. Parity with the app's
    ``chewSecondsToQuality`` (``digestRun.ts``): ``1 - e^(-s/12)``, floored at 0.2."""
    if chew_s <= 0:
        return 0.2
    return _clamp01(1.0 - math.exp(-chew_s / 12.0))


_REFINED_FORMS = {"juiced", "liquid", "ultra_processed", "flour"}


def _score_food_order_from_sequence(sequence: list, items: list) -> float | None:
    """Veg/protein-before-refined heuristic. Parity with the app's
    ``scoreFoodOrderFromSequence`` — refined item first/second drags the score."""
    if not sequence:
        return None
    by_id = {i.get("id"): i for i in items}
    ordered = sorted(sequence, key=lambda s: s.get("rank", 0))
    score = 0.75
    for idx, step in enumerate(ordered):
        it = by_id.get(step.get("item_ref"))
        if not it:
            continue
        nova = _num(it.get("nova_class"))
        refined = it.get("form") in _REFINED_FORMS or (nova is not None and nova >= 3)
        if refined and idx == 0:
            score -= 0.35
        if refined and idx == 1:
            score -= 0.15
        if it.get("form") in ("raw_whole", "cooked") and idx == 0:
            score += 0.1
    return _clamp01(score)


def _chew_samples(ingestion: dict[str, Any]) -> list[float]:
    """Chew-second samples the app averages: per-bite, each sequence bite, total/bites."""
    samples: list[float] = []
    mpb = _num(ingestion.get("chew_time_s_mean_per_bite"))
    if mpb is not None:
        samples.append(mpb)
    seq = ingestion.get("sequence") or []
    for s in seq:
        c = _num(s.get("chew_time_s"))
        if c is not None:
            samples.append(c)
    total = _num(ingestion.get("chew_time_s_total"))
    if total is not None:
        samples.append(total / max(1, len(seq)))
    return samples


def _derive_ingestion(ingestion: dict[str, Any], items: list) -> dict[str, Any]:
    """Port of the app's ``deriveIngestion`` (via ``enrichDigestRun``): derive
    mastication quality from chew samples, food-order from the sequence, and the
    matrix-integrity boost — so the flattened context matches the app's, not the
    raw explicit values. An explicit ``ingestion.derived`` block wins per field.
    """
    if not ingestion:
        return {"mastication_quality": 0.5, "food_order_score": 0.5, "matrix_integrity_boost": 0.0}
    derived = ingestion.get("derived") or {}

    samples = _chew_samples(ingestion)
    mast = _num(ingestion.get("mastication_quality"))
    if samples:  # chew samples override any explicit mastication_quality (app behaviour)
        mast = _chew_seconds_to_quality(sum(samples) / len(samples))
    if mast is None:
        mast = 0.5

    order = _num(ingestion.get("food_order_score"))
    if ingestion.get("sequence"):
        from_seq = _score_food_order_from_sequence(ingestion["sequence"], items)
        if from_seq is not None:
            order = from_seq
    if order is None:
        order = 0.5

    boost = _clamp01(mast) * 0.2 - 0.1  # high chew -> slight matrix boost; low chew -> drag
    return {
        "mastication_quality": derived["mastication_quality"]
        if _num(derived.get("mastication_quality")) is not None else _clamp01(mast),
        "food_order_score": derived["food_order_score"]
        if _num(derived.get("food_order_score")) is not None else _clamp01(order),
        "matrix_integrity_boost": derived["matrix_integrity_boost"]
        if _num(derived.get("matrix_integrity_boost")) is not None else boost,
    }


def _chew_seconds(ingestion: dict[str, Any]) -> float | None:
    """Mean chew seconds for the ``meal.chewTimeS`` teaching field
    (app order: per-bite -> mean over sequence -> total)."""
    per_bite = _num(ingestion.get("chew_time_s_mean_per_bite"))
    if per_bite is not None:
        return per_bite
    seq = ingestion.get("sequence") or []
    chews = [c for c in (_num(s.get("chew_time_s")) for s in seq) if c is not None]
    if chews:
        return sum(chews) / len(chews)
    return _num(ingestion.get("chew_time_s_total"))


def to_machine_context(dr: DigestRun) -> dict[str, Any]:
    """Flatten a DigestRun into the dotted machine context the executor consumes.

    Ports the app's ``enrichDigestRun`` + ``toMachineContext`` for the
    **host + packet + ingestion** input: the chew→mastication derivation, the
    matrix-integrity boost, and the teaching defaults (matrix 0.7, mastication/order
    0.5, macros 0, processing_combined 0.3, residue_burden 0, alcohol 0, postSurgical
    false) are reproduced so the same DigestRun yields the same context on both sides.

    Scope boundary: ``DigestRun.clinical`` and ``DigestRun.goals`` are **not** folded
    into the context here (the app maps them onto ``host.*``, e.g. a clinical IR band
    overriding ``host.insulinResistance``). They are carried on the object but
    reserved — so a DigestRun that relies on clinical/goals to change host flags will
    diverge from the app until those mappings are ported. Genuinely optional
    host/packet fields are omitted when undeclared (fail-closed).
    """
    host = dr.host
    packet = dr.packet
    ingestion = dr.ingestion
    derived = packet.get("derived") or {}
    ing = _derive_ingestion(ingestion, packet.get("items") or [])

    matrix = _clamp01(
        (derived.get("matrix_integrity") if _num(derived.get("matrix_integrity")) is not None else 0.7)
        + (ing.get("matrix_integrity_boost") if _num(ing.get("matrix_integrity_boost")) is not None else 0.0)
    )
    food_quality = derived["food_quality"] if _num(derived.get("food_quality")) is not None else matrix

    intake = dict(packet.get("intake") or {})
    if ingestion.get("hydrated_with_meal") is True:
        intake["hydration"] = 1

    macros = packet.get("macros_g") or {}
    partners = packet.get("partners") or {}
    ctx: dict[str, Any] = {}

    # --- host.* (required flags always; optional ones only when declared) ---
    ctx["host.ready"] = host.get("ready")
    ctx["host.postSurgical"] = bool(host.get("post_surgical", False))
    ctx["host.alcohol"] = host["alcohol_with_meal"] if _num(host.get("alcohol_with_meal")) is not None else 0
    for src, dst in (
        ("acid_capacity", "host.acidCapacity"),
        ("bile_capacity", "host.bileCapacity"),
        ("insulin_resistance", "host.insulinResistance"),
        ("leucine_adequacy", "host.leucineAdequacy"),
        ("sleep_quality", "host.sleepQuality"),
        ("stress_level", "host.stressLevel"),
        ("hydration_status", "host.hydrationStatus"),
    ):
        if _num(host.get(src)) is not None:
            ctx[dst] = host[src]

    # --- intake.* (binary presence channels) ---
    for ch in ("food", "hydration", "supplement"):
        if ch in intake:
            ctx[f"intake.{ch}"] = intake[ch]

    # --- meal.* (macros default 0, derived matrix/quality with app defaults) ---
    ctx["meal.proteinG"] = macros.get("protein", 0)
    ctx["meal.fatG"] = macros.get("fat", 0)
    ctx["meal.glucoseG"] = macros.get("carb", 0)  # available CHO teaching proxy
    ctx["meal.fiberG"] = macros.get("fiber", 0)
    ctx["meal.fructoseG"] = macros.get("fructose", 0)
    ctx["meal.matrixIntegrity"] = matrix
    ctx["meal.foodQuality"] = food_quality
    ctx["meal.masticationQuality"] = ing["mastication_quality"]  # already chew-derived + defaulted
    ctx["meal.foodOrderScore"] = ing["food_order_score"]

    chew_s = _chew_seconds(ingestion)
    if chew_s is not None:
        ctx["meal.chewTimeS"] = chew_s
    if derived.get("nova_max") is not None:
        ctx["meal.novaMax"] = derived["nova_max"]
    # app's derivePacketDerived defaults these when the packet is silent
    ctx["meal.processingCombined"] = (
        derived["processing_combined"] if _num(derived.get("processing_combined")) is not None else 0.3
    )
    ctx["meal.residueBurden"] = (
        derived["residue_burden"] if _num(derived.get("residue_burden")) is not None else 0
    )
    if _num(partners.get("lipid_g")) is not None:
        ctx["meal.partnerLipidG"] = partners["lipid_g"]
    if isinstance(partners.get("ascorbate"), bool):
        ctx["meal.partnerAscorbate"] = partners["ascorbate"]
    if isinstance(partners.get("tannin"), bool):
        ctx["meal.partnerTannin"] = partners["tannin"]

    # Drop any host key that ended up None (undeclared) so predicates fail-close.
    return {k: v for k, v in ctx.items() if v is not None}


def conditions_from_digest_run(dr: DigestRun) -> Conditions:
    """A :class:`Conditions` (four-seats) *view* over a DigestRun.

    Host flags become the ``host`` seat (camelCased to match the machine context);
    same-meal partners become the ``partner`` seat; life stage and fed/fasted clock
    are read from the host/ingestion when present. This keeps the four-seats
    ergonomics without making Conditions a second, drifting encoding of the input.
    """
    host_ctx = {k.split(".", 1)[1]: v for k, v in to_machine_context(dr).items() if k.startswith("host.")}
    partners = dr.packet.get("partners") or {}
    partner_seat: dict[str, Any] = {}
    if _num(partners.get("lipid_g")) is not None:
        partner_seat["dietary_lipid_g"] = partners["lipid_g"]
    if isinstance(partners.get("ascorbate"), bool):
        partner_seat["ascorbate"] = partners["ascorbate"]
    if isinstance(partners.get("tannin"), bool):
        partner_seat["tannin"] = partners["tannin"]
    stage = str(dr.host.get("lifecycle") or "adult")
    clock = "fasted" if dr.ingestion.get("clock") == "fasted" else "fed"
    return Conditions(host=host_ctx, partners=partner_seat, stage=stage, clock=clock)


def run_digest_run(dr: DigestRun | dict[str, Any] | str | Path) -> dict[str, Any]:
    """Run a DigestRun through the full-digest machines and return the stage trace.

    Accepts a :class:`DigestRun`, a dict, or a path — the same JSON the app reads.
    Returns the :func:`~biology_as_code.machines.digestion.run_digestion` result
    ``{process, stages, context, final_states, firedEdgeCases}``.
    """
    if not isinstance(dr, DigestRun):
        dr = load_digest_run(dr)
    return run_digestion(to_machine_context(dr), process=dr.process_id)
