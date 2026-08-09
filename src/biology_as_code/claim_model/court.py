"""
The Court — adjudicate a claim against the constitution.

The verdict is computed, never predicted. Court takes Rosetta's parse, resolves
the claim's mechanism against the graph, optionally consults the evidence-grade
model, and returns one of the five verdicts in ``claim_audit.schema.json``.

The precedence rules are fixed and ordered, and the first that fires wins:

  1. Untypable language      -> REFUSE       (soft/marketing verbs; no mechanism)
  2. Endpoint with no path   -> REFUSE       (food -> disease, no pipeline named)
  3. Gate closed in graph    -> Busted       (the mechanism is blocked)
  4. Gate unresolvable       -> UNEVALUABLE  (we do not know, and say so)
  5. Typed + strong evidence -> Confirmed
  6. Typed + weak evidence   -> Plausible

Rule 4 is the one that matters. A classifier asked to choose among four verdicts
will always choose one; this returns "I cannot evaluate that" and is the reason
the model sits underneath the Court rather than replacing it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from biology_as_code.claim_model.rosetta import RosettaParse, parse

VERDICTS = ("Confirmed", "Plausible", "Busted", "UNEVALUABLE", "REFUSE")

#: Minimum combined term rarity for a law to count as grounding a claim.
#: Tuned so two register-wide terms cannot ground a law on their own.
_GROUND_FLOOR = 0.15

#: Evidence grade -> the strongest verdict that grade can license.
_GRADE_CEILING = {
    "A": "Confirmed",
    "B": "Plausible",
    "C": "Plausible",
    "D": "UNEVALUABLE",
}


@dataclass
class Adjudication:
    """A verdict and the complete reason for it."""

    surface: str
    verdict: str
    rosetta: RosettaParse
    reason: str
    rule: int
    gate_check: str = "unevaluable"
    resolved_laws: list[str] = field(default_factory=list)
    evidence_grade: str | None = None
    evidence_confidence: float | None = None
    atomized: list[str] = field(default_factory=list)
    weakest_atom: str | None = None

    def to_fixture(self) -> dict[str, Any]:
        """Serialise to the repo's ``claim_audit.schema.json`` shape."""
        return {
            "id": f"claim.{abs(hash(self.surface)) % 10**10}",
            "surface_claim": self.surface,
            "atomized": self.atomized,
            "gate_check": self.gate_check,
            "gate_note": self.reason,
            "verdict": self.verdict,
            "integrity": "unknown",
            "rosetta": {
                "surface_verb": self.rosetta.surface_verb,
                "class": self.rosetta.verb_class,
                "relation_enum": self.rosetta.relation,
            },
        }

    def explain(self) -> str:
        lines = [
            f"claim    : {self.surface}",
            f"verdict  : {self.verdict}   (rule {self.rule})",
            f"reason   : {self.reason}",
            f"rosetta  : verb={self.rosetta.surface_verb!r} "
            f"class={self.rosetta.verb_class!r} relation={self.rosetta.relation!r}",
            f"gate     : {self.gate_check}",
        ]
        if self.resolved_laws:
            lines.append(f"laws     : {', '.join(self.resolved_laws)}")
        if self.evidence_grade:
            conf = f" (confidence {self.evidence_confidence:.2f})" if self.evidence_confidence else ""
            lines.append(f"evidence : predicted grade {self.evidence_grade}{conf}")
        if len(self.atomized) > 1:
            lines.append(f"atoms    : {len(self.atomized)} — weakest sets the verdict")
        return "\n".join(lines)


class Court:
    """Adjudicator. Holds the graph; the model is optional."""

    def __init__(self, graph: Any, model: Any | None = None) -> None:
        self.graph = graph
        self.model = model
        self._index_cache: dict[str, set[str]] | None = None

    # ------------------------------------------------------------ public

    def adjudicate(self, surface: str, *, extra: dict[str, Any] | None = None) -> Adjudication:
        """Rule on one claim. Compound claims are ruled on atom by atom."""
        atoms = parse(surface).atomized
        # A fragment carrying no claim verb is a noun phrase, not an assertion.
        # Ruling on it would let "eat fat-free spinach salad" — which asserts
        # nothing — outrank the adjudication of the claim actually being made.
        assertive = [a for a in atoms if parse(a).verb_class is not None]
        if len(assertive) > 1:
            # Each atom is typed on its own language but gated against the whole
            # claim: "fat-free spinach ... to prevent deficiency" splits the
            # condition away from the assertion, and the condition is the point.
            rulings = [self._rule_one(a, extra, context=surface) for a in assertive]
            # VERDICTS is ordered strongest -> most restrictive, so the highest
            # index is the weakest link, and the weakest link sets the tier.
            worst = max(rulings, key=lambda r: VERDICTS.index(r.verdict))
            worst.surface = surface
            worst.atomized = atoms
            worst.weakest_atom = worst.rosetta.surface
            worst.reason = f"weakest of {len(assertive)} assertions: {worst.reason}"
            return worst
        # One assertion (or none): rule on it, but read conditions from the whole.
        target = assertive[0] if assertive else surface
        ruling = self._rule_one(target, extra, context=surface)
        ruling.surface = surface
        ruling.atomized = atoms
        return ruling

    def adjudicate_many(self, surfaces: list[str]) -> list[Adjudication]:
        return [self.adjudicate(s) for s in surfaces]

    # ------------------------------------------------------------ rules

    def _rule_one(
        self,
        surface: str,
        extra: dict[str, Any] | None,
        *,
        context: str | None = None,
    ) -> Adjudication:
        r = parse(surface)
        scope = context or surface   # gate conditions read from the whole claim
        base = dict(surface=surface, rosetta=r, atomized=[surface])

        # Rule 1 — soft and marketing language types to nothing checkable, and
        # no amount of graph evidence can rescue a claim that asserts nothing.
        if r.verb_class in {"soft", "marketing"}:
            return Adjudication(
                **base, verdict="REFUSE", rule=1, gate_check="unevaluable",
                reason=f"{r.verb_class} verb {r.surface_verb!r}: "
                       "no mechanism, no endpoint, no magnitude",
            )

        # Rule 1b — no recognised verb at all. Not refused, just unreadable.
        if r.verb_class is None:
            return Adjudication(
                **base, verdict="UNEVALUABLE", rule=1, gate_check="unevaluable",
                reason="no recognised claim verb; Rosetta could not type this claim",
            )

        # Ground the claim before ruling on it: a disease claim that names a
        # checkable mechanism is Busted or Confirmed on that mechanism, not
        # refused for its verb. Refusal is for claims with nothing underneath.
        laws = self._resolve_laws(scope)
        gate = self._gate_state(scope, laws, r)

        # Rule 2 — a gate the constitution records as closed for this claim.
        if gate == "fail":
            return Adjudication(
                **base, verdict="Busted", rule=2, gate_check="fail",
                resolved_laws=laws,
                reason="the mechanism this claim depends on is gated closed "
                       "under the stated conditions",
            )

        # Rule 3 — reaches a disease endpoint with no mechanism underneath it.
        if r.reaches_endpoint and not r.typed and not laws:
            return Adjudication(
                **base, verdict="REFUSE", rule=3, gate_check="unevaluable",
                reason="claim reaches a disease endpoint with no mechanism named "
                       "between food and outcome",
            )

        # Rule 3b — a malformed mechanism is refused however well its entities
        # resolve. Naming molecules the register knows is not naming a pathway,
        # and no amount of grounding converts an unstated mechanism into a
        # stated one. This is the rule that stops the Court confirming a claim
        # merely because it mentions familiar nouns.
        if r.relation == "MALFORMED_MECHANISM":
            return Adjudication(
                **base, verdict="REFUSE", rule=3, gate_check=gate,
                resolved_laws=laws,
                reason=f"{r.verb_class} verb {r.surface_verb!r} names no mechanism "
                       "between input and endpoint"
                       + (f"; {len(laws)} law(s) mention its entities but none "
                          "states the path it asserts" if laws else ""),
            )

        # Rule 4 — nothing in the graph resolves this. Say so.
        if not laws:
            return Adjudication(
                **base, verdict="UNEVALUABLE", rule=4, gate_check="unevaluable",
                reason="no law in the register governs this mechanism; "
                       "claim is well-formed but ungrounded",
            )

        grade, conf = self._grade(surface, extra)
        ceiling = _GRADE_CEILING.get(grade or "", "UNEVALUABLE")

        # Rule 5/6 — typed, grounded, and graded.
        if r.hedged and ceiling == "Confirmed":
            ceiling = "Plausible"

        return Adjudication(
            **base, verdict=ceiling, rule=5 if ceiling == "Confirmed" else 6,
            gate_check="pass", resolved_laws=laws,
            evidence_grade=grade, evidence_confidence=conf,
            reason=f"typed as {r.relation}, grounded in {len(laws)} law(s), "
                   f"evidence grade {grade or 'unknown'}"
                   + (" (hedged, capped at Plausible)" if r.hedged else ""),
        )

    # ------------------------------------------------------------ helpers

    def _law_index(self) -> dict[str, set[str]]:
        """
        Inverted index from domain term to law id, built once per Court.

        Terms come from each law's statement, gate, bound, conditions and
        subsystem. Only distinctive terms are indexed — a term appearing in more
        than a third of the register carries no information and would let the
        Court ground a claim on a resemblance, which the register forbids.
        """
        if self._index_cache is not None:
            return self._index_cache

        raw: dict[str, set[str]] = {}
        for law in self.graph.nodes("Law"):
            p = law.props
            blob = " ".join(str(x) for x in (
                law.name, p.get("gate_text", ""), p.get("bound_text", ""),
                p.get("conditions", ""), p.get("subsystem", ""), p.get("organ", ""),
            ))
            for term in _terms(blob):
                raw.setdefault(term, set()).add(law.id)

        # No ceiling filter. Dropping common terms outright loses the ones that
        # matter most — "fat" appears in many laws and is still the gate
        # condition of the carotenoid pipeline. Rarity is scored below instead.
        self._index_cache = raw
        return self._index_cache

    def _resolve_laws(self, surface: str) -> list[str]:
        """
        Which laws govern the mechanism this claim names.

        Two routes, both literal. Named Compound and Nutrient nodes walk to the
        laws that govern them; distinctive law vocabulary matches directly. A law
        needs two distinct term hits to be grounded on vocabulary alone, so a
        single shared word cannot pull in an unrelated law.
        """
        text = (surface or "").lower()
        hits: set[str] = set()

        for label in ("Compound", "Nutrient"):
            for node in self.graph.nodes(label):
                name = (node.name or "").lower()
                if len(name) > 3 and name in text:
                    for law in self.graph.neighbors(node.id, incoming=True):
                        if law.label == "Law":
                            hits.add(law.id)

        index = self._law_index()
        score: dict[str, float] = {}
        matched: dict[str, int] = {}
        for term in _terms(text):
            ids = index.get(term)
            if not ids:
                continue
            weight = 1.0 / len(ids)   # a term in one law is worth more than in twenty
            for law_id in ids:
                score[law_id] = score.get(law_id, 0.0) + weight
                matched[law_id] = matched.get(law_id, 0) + 1

        # Two distinct terms AND enough combined rarity. Two common terms alone
        # (0.067 each against a 47-law register) fall below the floor; one rare
        # term plus one common term clears it.
        hits.update(
            law_id for law_id, s in score.items()
            if matched.get(law_id, 0) >= 2 and s >= _GROUND_FLOOR
        )
        return sorted(hits)

    def _gate_state(self, surface: str, laws: list[str], r: RosettaParse) -> str:
        """
        Resolve the gate for this claim: pass, fail, or unevaluable.

        A gate fails when the claim asserts closure outright, or when it states
        the absence of something a governing law's gate requires — "fat-free"
        against a law whose gate is fat co-presence.
        """
        if r.relation == "CLOSES_GATE":
            return "fail"

        text = (surface or "").lower()
        absent = _absent_terms(text)
        if not absent:
            return "pass" if laws else "unevaluable"

        for law_id in laws:
            law = self.graph.get_node(law_id)
            if law is None or not law.props.get("gate_present"):
                continue
            gate_terms = _terms(str(law.props.get("gate_text") or ""))
            if absent & gate_terms:
                return "fail"
        return "pass" if laws else "unevaluable"

    def _grade(
        self, surface: str, extra: dict[str, Any] | None
    ) -> tuple[str | None, float | None]:
        if self.model is None:
            return None, None
        grade, _ = self.model.predict(surface, extra)
        return grade, self.model.confidence(surface, extra)


# ---------------------------------------------------------------- helpers

#: Function words plus the register's own connective vocabulary. These appear
#: everywhere and would ground a claim on nothing.
_STOP = frozenset("""
about above after against and are because been before being below between both
but cannot could during each from further have having here into itself more
most only other over same some such than that their them then there these they
this those through under until very were what when where which while with
without your via per not non none can may must should would while also plus
the a an of in on to for by is it as at or if be
level levels state states value values amount amounts rate rates total
present absent required requires increase decrease higher lower
""".split())

#: Three characters, because the register's most load-bearing terms are short:
#: fat, zinc, iron, bile. Hyphens separate rather than join, so "fat-free"
#: yields "fat" and can match a gate whose condition is fat co-presence.
_TOKEN = re.compile(r"[a-z][a-z0-9]{2,}")

#: Absence markers: "fat-free", "without fat", "no fat", "zero fat", "low-fat".
_ABSENCE = re.compile(
    r"(?:\b(?:without|no|zero|free\s+of|lacking|absent|devoid\s+of)\s+([a-z]{3,}))"
    r"|(?:\b([a-z]{3,})[\s-]*free\b)"
    r"|(?:\blow[\s-]*([a-z]{3,})\b)",
    re.I,
)


def _terms(text: str) -> set[str]:
    """Distinctive content terms, lowercased and stemmed to a common suffix."""
    out = set()
    for tok in _TOKEN.findall((text or "").lower()):
        if tok in _STOP:
            continue
        out.add(_stem(tok))
    return out


def _stem(tok: str) -> str:
    """
    Suffix strip, then truncate to a six-character prefix.

    Prefix truncation rather than real morphology, because the pairs that matter
    here are derivational and no suffix rule joins them: micelle/micellar,
    absorb/absorption, ferment/fermentation. Six characters joins those without
    collapsing distinct terms, and the two-hit requirement in _resolve_laws
    absorbs the residual false matches.
    """
    for suf in ("ation", "ility", "ally", "ular", "ines", "ing", "ted", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 4:
            tok = tok[: -len(suf)]
            break
    return tok[:6]


def _absent_terms(text: str) -> set[str]:
    """Terms the claim explicitly says are missing."""
    found: set[str] = set()
    for match in _ABSENCE.finditer(text or ""):
        for grp in match.groups():
            if grp:
                found.add(_stem(grp.lower()))
    return found


__all__ = ["Court", "Adjudication", "VERDICTS"]
