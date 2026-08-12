"""
L2_REDOX_COMPETITION — apply as open-tier FLOW modifiers.

Maps to LAW-042 (competition), LAW-041 (redox), LAW-004 (ascorbate EXPANDS).
Does NOT treat ascorbate absence as a closed gate (reject ×0.1 fail-closed rule).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from biology_as_code.engine.paths import data_file

from .state import MetabolicState

_RULE_PATH = data_file("rule_L2_REDOX_COMPETITION.json")


def load_rule(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else _RULE_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def apply_l2_redox_competition(
    state: MetabolicState,
    *,
    rule: dict[str, Any] | None = None,
    use_prototype_ratio: bool = True,
) -> MetabolicState:
    """
    Mutates iron/zinc bioavailability factors on state.

    Competition: if iron_rel / zinc_rel > 3, zinc factor *= 0.4 (prototype).
    Ascorbate: if present, iron factor *= 2.0 (LAW-004 expand); if absent, factor stays 1.0 base
    (optional mild phytate/tannin already applied elsewhere).
    """
    rule = rule or load_rule()
    state.cite(*rule.get("law_links", {}).get("competition", []))
    state.cite(*rule.get("law_links", {}).get("ascorbate_enhancer", []))
    state.cite(*rule.get("law_links", {}).get("iron_redox_gate", []))

    # refuse bad semantics from naive JSON
    for r in rule.get("honesty", {}).get("refuse", []):
        if r not in state.refuse:
            state.refuse.append(r)

    fe = max(state.iron_rel, 1e-9)
    zn = max(state.zinc_rel, 1e-9)
    ca = max(state.calcium_rel, 1e-9)

    fe_f = state.iron_bioavailability_factor
    zn_f = state.zinc_bioavailability_factor

    comp = (rule.get("rule_definition") or {}).get("competition") or {}
    pen = comp.get("prototype_penalty") or {}
    thr = float(pen.get("if_molar_or_mass_ratio_A_to_B_gt", 3.0))
    mul = float(pen.get("then_absorption_factor_B_multiply", 0.4))

    if use_prototype_ratio:
        # Iron high vs zinc → zinc pays (teaching COMPETE_FOR DMT1)
        if fe / zn > thr:
            zn_f *= mul
            state.note(
                f"L2_REDOX: Fe:Zn ratio {fe/zn:.1f} > {thr} → Zn factor ×{mul} "
                f"(prototype; LAW-042)"
            )
        # Calcium high vs iron → iron pays (common meal pattern)
        if ca / fe > thr:
            fe_f *= mul
            state.note(
                f"L2_REDOX: Ca:Fe ratio {ca/fe:.1f} > {thr} → Fe factor ×{mul} "
                f"(prototype; LAW-042 / LAW-047 family)"
            )

    redox = (rule.get("rule_definition") or {}).get("redox_iron") or {}
    sem = redox.get("law_semantics") or {}
    if state.ascorbate_same_meal:
        exp = sem.get("ascorbate_present_same_meal") or {}
        factor = float(exp.get("prototype_factor", 2.0))
        fe_f *= factor
        state.note(f"L2_REDOX: ascorbate same meal → Fe factor ×{factor} (LAW-004 EXPANDS)")
        state.cite("LAW-004")
    else:
        # Explicitly do NOT apply ×0.1
        state.note(
            "L2_REDOX: ascorbate absent → Fe path still open (gate=none LAW-004); "
            "no ×0.1 fail_state"
        )

    if state.tannin_same_meal:
        fe_f *= 0.55
        state.cite("LAW-006")
        state.note("L2_REDOX: tannin same meal → Fe ×0.55 (LAW-006 prior)")

    if state.phytate_matrix:
        fe_f *= 0.6
        zn_f *= 0.6
        state.cite("LAW-002")
        state.note("L2_REDOX: phytate matrix → Fe/Zn ×0.6 (LAW-002 prior)")

    state.iron_bioavailability_factor = round(max(fe_f, 0.0), 4)
    state.zinc_bioavailability_factor = round(max(zn_f, 0.0), 4)
    state.claim_tier = "open"
    state.meta["l2_redox_rule"] = rule.get("rule_id")
    return state
