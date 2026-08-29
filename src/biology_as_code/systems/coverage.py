"""System coverage table for one meal observation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from biology_as_code.systems.adapters import adapt_system
from biology_as_code.systems.anatomy import BODY_SYSTEMS
from biology_as_code.systems.meal import MealObservation
from biology_as_code.systems.states import EvalState, WalkResult


@dataclass(frozen=True)
class SystemCoverageRow:
    # One of the ELEVEN anatomical organ systems (cardiovascular, digestive,
    # endocrine, immune, integumentary, muscular, nervous, reproductive,
    # respiratory, skeletal, urinary) — which body PART. Not one of the seven
    # functional systems on the law register, which are `functional_system`.
    system_id: str
    organ_system: str
    shipped: bool
    result: WalkResult

    @property
    def state(self) -> EvalState:
        return self.result.state


@dataclass(frozen=True)
class SystemCoverageTable:
    meal_id: str
    rows: tuple[SystemCoverageRow, ...]

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in self.rows:
            key = row.state.value
            out[key] = out.get(key, 0) + 1
        return out

    def shipped_rows(self) -> tuple[SystemCoverageRow, ...]:
        return tuple(r for r in self.rows if r.shipped)

    def grey_majority(self) -> bool:
        """True when UNEVALUABLE+OPEN+REFUSE outnumber HOLDS+REFUTED+Plausible."""
        c = self.counts()
        grey = c.get("UNEVALUABLE", 0) + c.get("OPEN", 0) + c.get("REFUSE", 0)
        green = c.get("HOLDS", 0) + c.get("REFUTED", 0) + c.get("Plausible", 0)
        return grey >= green

    def to_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "system_id": r.system_id,
                "organ_system": r.organ_system,
                "shipped": r.shipped,
                "state": r.state.value,
                "gate": r.result.gate_id,
                "l3_named": r.result.l3_named,
                "reason": r.result.reason,
                "missing": list(r.result.missing_fields),
                "citations": list(r.result.citations),
            }
            for r in self.rows
        ]


def cover_meal(data: Mapping[str, Any] | MealObservation | None) -> SystemCoverageTable:
    meal = data if isinstance(data, MealObservation) else MealObservation.from_mapping(data)
    rows = []
    for spec in BODY_SYSTEMS:
        result = adapt_system(spec.id, meal)
        rows.append(
            SystemCoverageRow(
                system_id=spec.id,
                organ_system=spec.name,
                shipped=spec.shipped,
                result=result,
            )
        )
    return SystemCoverageTable(meal_id=meal.meal_id, rows=tuple(rows))


def render_table(table: SystemCoverageTable) -> str:
    lines = [
        f"System coverage — {table.meal_id}",
        f"counts: {table.counts()}  grey_majority={table.grey_majority()}",
        "",
        f"{'system':<22} {'state':<14} {'gate':<24} reason",
        "-" * 88,
    ]
    for row in table.rows:
        gate = row.result.gate_id or "—"
        flag = "" if row.shipped else " [parked]"
        lines.append(
            f"{row.organ_system + flag:<22} {row.state.value:<14} {gate:<24} {row.result.reason}"
        )
    return "\n".join(lines)
