"""Malformed-claim linter.

A claim that names a food (L1) and a disease/outcome (L5) without a
mechanism (L3) is malformed under the constitution.

This is the public-good version of the companion review's epistemology
section. It does not score truth. It scores walk shape.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from biology_as_code.systems.states import EvalState

L5_PATTERNS = (
    r"\bdiabetes\b",
    r"\bt2d\b",
    r"\bobesity\b",
    r"\bweight gain\b",
    r"\bcardiovascular\b",
    r"\bheart disease\b",
    r"\bcvd\b",
    r"\bcancer\b",
    r"\bdepression\b",
    r"\banxiety\b",
    r"\bdementia\b",
    r"\balzheimer",
    r"\baddiction\b",
    r"\binflammation\b",
    r"\bmortality\b",
    r"\bprevents?\b",
    r"\bcauses?\b",
    r"\bleads to\b",
    r"\blinked to\b",
    r"\bassociated with\b",
)

L1_PATTERNS = (
    r"\bultra-?processed\b",
    r"\bupf\b",
    r"\bnova\b",
    r"\bhyperpalatable\b",
    r"\bprocessed food",
    r"\bemulsifier",
    r"\bseed oil",
    r"\bsugar\b",
    r"\bfructose\b",
    r"\bwhole grain",
    r"\byogurt\b",
    r"\bbread\b",
    r"\bcereal\b",
)

L3_PATTERNS = (
    r"\beating rate\b",
    r"\benergy density\b",
    r"\bfood matrix\b",
    r"\bmatrix disintegrat",
    r"\bglp-?1\b",
    r"\bp yy\b",
    r"\bpyy\b",
    r"\bincretin\b",
    r"\binsulin\b",
    r"\bgastric emptying\b",
    r"\bmicelle\b",
    r"\bmucus\b",
    r"\bmicrobiome\b",
    r"\bscfa\b",
    r"\btlr4\b",
    r"\breward\b",
    r"\bdopamine\b",
    r"\bhyperpalat",
    r"\bsodium load\b",
    r"\bapob\b",
)

SOFT_VERBS = (
    r"\bdetox\b",
    r"\bsuperfood\b",
    r"\bcleanses?\b",
    r"\bboosts immunity\b",
    r"\boptimized?\b",
    r"\bhacks?\b",
)


def _hits(patterns: tuple[str, ...], text: str) -> tuple[str, ...]:
    found = []
    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            found.append(m.group(0).lower())
    return tuple(dict.fromkeys(found))


@dataclass(frozen=True)
class LintResult:
    text: str
    state: EvalState
    malformed: bool
    l1: tuple[str, ...]
    l3: tuple[str, ...]
    l5: tuple[str, ...]
    reason: str
    required_l3_prompt: str | None = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "state": self.state.value,
            "malformed": self.malformed,
            "L1": list(self.l1),
            "L3": list(self.l3),
            "L5": list(self.l5),
            "reason": self.reason,
            "required_l3_prompt": self.required_l3_prompt,
        }


def lint_claim(text: str) -> LintResult:
    raw = (text or "").strip()
    if not raw:
        return LintResult(
            text=raw,
            state=EvalState.REFUSE,
            malformed=True,
            l1=(),
            l3=(),
            l5=(),
            reason="Empty claim.",
        )
    l1 = _hits(L1_PATTERNS, raw)
    l3 = _hits(L3_PATTERNS, raw)
    l5 = _hits(L5_PATTERNS, raw)
    soft = _hits(SOFT_VERBS, raw)

    if soft and not l3:
        return LintResult(
            raw,
            EvalState.REFUSE,
            True,
            l1,
            l3,
            l5,
            "Soft/marketing verb with no typed L3 mechanism.",
            required_l3_prompt="Name the gate (eating rate, micelle, mucus, incretin, sodium load, …).",
        )

    if l1 and l5 and not l3:
        return LintResult(
            raw,
            EvalState.REFUSE,
            True,
            l1,
            l3,
            l5,
            "Malformed: L1 food/exposure jumped to L5 outcome with no L3 mechanism.",
            required_l3_prompt=(
                "Split this into walks. Example: UPF → T2D is at least "
                "energy-surplus, matrix/eating-rate, and additive/microbiome — GRADE each separately."
            ),
        )

    if l1 and l3 and not l5:
        return LintResult(
            raw,
            EvalState.OPEN,
            False,
            l1,
            l3,
            l5,
            "Mechanism named, outcome not named. Walk can start; magnitude not claimed.",
        )

    if l3 and l5:
        return LintResult(
            raw,
            EvalState.OPEN,
            False,
            l1,
            l3,
            l5,
            "L3 present. Shape is well-formed. This linter does not grade evidence.",
        )

    if not l1 and not l5 and not l3:
        return LintResult(
            raw,
            EvalState.UNEVALUABLE,
            False,
            l1,
            l3,
            l5,
            "No L1/L3/L5 tokens recognised. Silent, not false.",
        )

    return LintResult(
        raw,
        EvalState.UNEVALUABLE,
        False,
        l1,
        l3,
        l5,
        "Partial shape; not enough to close or refuse.",
    )


def lint_many(texts: list[str]) -> list[LintResult]:
    return [lint_claim(t) for t in texts]
