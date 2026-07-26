#!/usr/bin/env python3
"""FDP-1 reference validator.

Checks a JSON document against the five conformance requirements of
FDP-1 §6 (Food Data Provenance Declaration). It is deliberately small and
dependency-free: the specification is the contract, this file is the proof the
contract is mechanically testable.

Usage:
    python validator/validate_fdp.py examples/iron-two-hosts.json
    python validator/validate_fdp.py < some-declaration.json

Exit status is 0 if every value and score conforms, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field

OPEN = "OPEN"

# §2 — every nutrient value declares these seven fields. `nutrient_ref` names
# WHICH nutrient the value is for (resolvable through a crosswalk such as
# MASTER_CROSSWALK.tsv); `source_ref` names WHERE the number came from.
VALUE_FIELDS = ("nutrient_ref", "value", "unit", "source", "source_ref", "method", "retrieved")
# §3 — every score declares these five fields.
SCORE_FIELDS = ("score_id", "inputs", "provenance_grade", "weights_published", "validation")

VALUE_SOURCES = {"analytical", "label", "calculated", "imputed", "literature", OPEN}

# §2 Provenance grades — source enum -> letter grade.
SOURCE_TO_GRADE = {
    "analytical": "A",
    "calculated": "B",
    "label": "C",
    "imputed": "D",
    "literature": "D",
    OPEN: "—",
}
# Weakest-link ordering (§3.1): higher is better; "—" (OPEN) is the worst and
# therefore dominates any set it appears in.
GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1, "—": 0}
RANK_TO_GRADE = {rank: grade for grade, rank in GRADE_RANK.items()}

# §3.2 validation levels, weakest to strongest. Any level above `none` must
# carry a citation.
VALIDATION_LEVELS = (
    "none",
    "face",
    "convergent",
    "criterion-intermediate",
    "criterion-substantial",
)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    checked_values: int = 0
    checked_scores: int = 0

    def fail(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


def weakest_link(grades: list[str]) -> str:
    """§3.1 — a score's grade is the grade of its lowest-graded input."""
    if not grades:
        return "—"
    worst_rank = min(GRADE_RANK.get(g, 0) for g in grades)
    return RANK_TO_GRADE[worst_rank]


def value_key(decl: dict) -> tuple:
    """The (nutrient_ref, source_ref) pair a score's `inputs` reference (§3)."""
    return (decl.get("nutrient_ref"), decl.get("source_ref"))


def check_value(name: str, decl: dict, rep: Report) -> str | None:
    """Validate one value declaration; return its provenance grade or None."""
    where = f"value[{name}]"
    if not isinstance(decl, dict):
        rep.fail(where, "must be an object with the seven §2 fields")
        return None

    # Requirement 1 — all seven fields present.
    missing = [f for f in VALUE_FIELDS if f not in decl]
    if missing:
        rep.fail(where, f"missing required §2 field(s): {', '.join(missing)}")

    # Requirement 4 — unknowns are the literal OPEN, never null/empty/omitted.
    for f in VALUE_FIELDS:
        if f in decl and decl[f] in (None, ""):
            rep.fail(where, f"field '{f}' is empty; unknowns SHALL be the literal \"OPEN\" (§4)")

    # nutrient_ref names the nutrient and should not itself be OPEN — a value you
    # cannot name is not a value you can declare (§2).
    if decl.get("nutrient_ref") == OPEN:
        rep.fail(where, "nutrient_ref is OPEN; a value must name which nutrient it is for (§2)")

    source = decl.get("source")
    if source is not None and source not in VALUE_SOURCES:
        rep.fail(where, f"source '{source}' is not one of {sorted(VALUE_SOURCES)}")

    rep.checked_values += 1
    return SOURCE_TO_GRADE.get(source, "—")


def check_score(idx: int, score: dict, grades: dict[tuple, str], rep: Report) -> None:
    label = score.get("score_id", f"#{idx}") if isinstance(score, dict) else f"#{idx}"
    where = f"score[{label}]"
    if not isinstance(score, dict):
        rep.fail(where, "must be an object with the five §3 fields")
        return

    # Requirement 2 — all five fields present.
    missing = [f for f in SCORE_FIELDS if f not in score]
    if missing:
        rep.fail(where, f"missing required §3 field(s): {', '.join(missing)}")

    # Requirement 2 (cont.) + Requirement 3 — every input resolves to a declared
    # value by its {nutrient_ref, source_ref} pair, and provenance_grade is
    # COMPUTED by the weakest-link rule over those inputs, not asserted.
    inputs = score.get("inputs")
    if isinstance(inputs, list) and inputs:
        input_grades = []
        for i, ref in enumerate(inputs):
            if not isinstance(ref, dict) or "nutrient_ref" not in ref or "source_ref" not in ref:
                rep.fail(where, f"inputs[{i}] must be a {{ nutrient_ref, source_ref }} pair (§3)")
                continue
            key = (ref["nutrient_ref"], ref["source_ref"])
            if key not in grades:
                rep.fail(where, f"inputs[{i}] {key} does not resolve to any declared value (§2)")
            else:
                input_grades.append(grades[key])
        expected = weakest_link(input_grades)
        declared = score.get("provenance_grade")
        if input_grades and declared != expected:
            rep.fail(
                where,
                f"provenance_grade is '{declared}' but the weakest-link rule (§3.1) "
                f"over its inputs computes '{expected}'",
            )
    elif "inputs" in score:
        rep.fail(where, "inputs must be a non-empty array of {nutrient_ref, source_ref} pairs (§3)")

    # Requirement 5 — validation.level above `none` carries a citation.
    validation = score.get("validation")
    if isinstance(validation, dict):
        level = validation.get("level")
        if level not in VALIDATION_LEVELS:
            rep.fail(where, f"validation.level '{level}' is not one of {list(VALIDATION_LEVELS)}")
        elif level != "none" and not validation.get("citation"):
            rep.fail(where, f"validation.level '{level}' is above 'none' but carries no citation (§3.2)")
    elif "validation" in score:
        rep.fail(where, "validation must be an object { level, citation } (§3.2)")

    rep.checked_scores += 1


def validate(doc: dict) -> Report:
    rep = Report()
    if not isinstance(doc, dict):
        rep.fail("document", "top level must be a JSON object")
        return rep

    values = doc.get("values", {})
    if not isinstance(values, dict):
        rep.fail("values", "must be an object mapping names to value declarations")
        values = {}

    # Index declared values by the (nutrient_ref, source_ref) pair that scores
    # reference in their `inputs`.
    grades: dict[tuple, str] = {}
    for name, decl in values.items():
        grade = check_value(name, decl, rep)
        if grade is not None and isinstance(decl, dict):
            grades[value_key(decl)] = grade

    scores = doc.get("scores", [])
    if not isinstance(scores, list):
        rep.fail("scores", "must be an array of score declarations")
        scores = []
    for i, score in enumerate(scores):
        check_score(i, score, grades, rep)

    return rep


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        with open(argv[1], "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        source_name = argv[1]
    else:
        doc = json.load(sys.stdin)
        source_name = "<stdin>"

    rep = validate(doc)
    print(f"FDP-1 conformance check — {source_name}")
    print(f"  values checked: {rep.checked_values}   scores checked: {rep.checked_scores}")
    if rep.ok:
        print("  RESULT: CONFORMS to FDP-1 §6")
        return 0
    print(f"  RESULT: NON-CONFORMING — {len(rep.errors)} problem(s):")
    for err in rep.errors:
        print(f"    - {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
