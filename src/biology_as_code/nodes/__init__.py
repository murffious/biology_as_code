"""
Nutrient nodes — one nutrient modelled as a pipeline, with provenance per claim.

A nutrient node answers "what happens to this substance between the plate and the
tissue", stage by stage, and attaches a provenance record to every quantitative
claim along the way. The shape is fixed by ``schemas/nutrient-node.schema.json``;
``data/zinc.node.yaml`` and ``data/glucose.node.yaml`` are the reference
instances, chosen because between them they exercise every hard part: saturable
absorption, homeostatic flattening, transporter competition, a two-pool store
where the *small* pool sets the timescale, and a case (glucose) where identical
composition gives non-identical availability.

Energy is deliberately not a node. It is a cascade of subtractions and a balance,
not a fraction scored against a reference intake — see
``simulation.energy_accounting``.

The gate lattice
----------------
Every claim carries a ``certification``, ordered::

    rejected < candidate < prior < gate < bound

``prior`` is a quantitative value from a secondary source: usable, but not a
Bound. Promotion to ``bound`` requires reading the primary and confirming it
reports the quantity with a stated population and dose. :func:`at_least` filters
a node's claims by that lattice, so a caller can ask for bound-only numbers and
get an honest empty answer rather than a textbook figure wearing a lab coat.

Dependencies
------------
Parsing needs PyYAML, which is *not* a runtime dependency of this package (the
zero-dependency guarantee in ``packets/validate.py`` applies here too). It is in
the ``dev`` extra; :func:`load_node` raises a directed ImportError without it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

from biology_as_code.packets.validate import (
    ValidationResult,
    load_schema,
    validate_against,
)

DATA_DIR = Path(__file__).resolve().parent / "data"

#: The gate lattice, ascending. Index is the tier.
CERTIFICATION_ORDER: tuple[str, ...] = (
    "rejected",
    "candidate",
    "prior",
    "gate",
    "bound",
)


class NodeUnavailable(RuntimeError):
    """Raised when a node file or the schema cannot be located."""


class NodeNotFound(KeyError):
    """Raised when a nutrient_id has no node file."""


def _require_yaml() -> Any:
    try:
        import yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "parsing nutrient nodes needs PyYAML, which is not a runtime dependency "
            "of biology-as-code. Install it with: pip install 'biology-as-code[dev]' "
            "or pip install pyyaml"
        ) from exc
    return yaml


def _walk_up_for(relative: str) -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative
        if candidate.is_dir():
            return candidate
    return None


def schema_path() -> Path:
    """Locate ``schemas/nutrient-node.schema.json`` in a repository checkout.

    The node YAML ships inside the wheel but the schema does not, matching how
    ``packets`` resolves its schemas. Loading works from an installed wheel;
    validating needs the repo.
    """
    found = _walk_up_for("schemas")
    if found is None:
        raise NodeUnavailable(
            "schemas/ not found; nutrient-node.schema.json lives in the repository "
            "checkout, not in the wheel. Clone the repo to validate."
        )
    return found / "nutrient-node.schema.json"


@lru_cache(maxsize=1)
def node_schema() -> dict[str, Any]:
    """The nutrient-node JSON Schema as a dict."""
    return load_schema(schema_path())


@lru_cache(maxsize=1)
def claim_provenance_schema() -> dict[str, Any]:
    """The claim-level provenance subschema, lifted out of ``$defs``.

    The repo's validator has no ``$ref`` support, so the subschema is applied by
    :func:`validate_node` in an explicit sweep rather than by reference. Keeping
    it in the schema file means the vocabulary still has exactly one definition.
    """
    return node_schema()["$defs"]["claim_provenance"]


@dataclass(frozen=True)
class Claim:
    """One provenance-bearing claim, with the path it was found at."""

    path: str
    claim_id: str
    certification: str
    data: dict[str, Any]

    @property
    def tier(self) -> int:
        """Position in :data:`CERTIFICATION_ORDER`; -1 if the value is unknown."""
        try:
            return CERTIFICATION_ORDER.index(self.certification)
        except ValueError:
            return -1


@dataclass(frozen=True)
class NutrientNode:
    """A parsed nutrient node. Thin, read-only view over the YAML."""

    nutrient_id: str
    node_kind: str
    raw: dict[str, Any]
    source_path: Path | None = None

    @property
    def name(self) -> str:
        return str(self.raw.get("identity", {}).get("name", self.nutrient_id))

    @property
    def sources(self) -> dict[str, Any]:
        return dict(self.raw.get("sources") or {})

    @property
    def scoring_guard(self) -> dict[str, Any]:
        """Why this nutrient cannot be scored naively. Empty dict if undeclared."""
        return dict(self.raw.get("scoring_guard") or {})

    @property
    def promotion_blockers(self) -> tuple[str, ...]:
        blockers = (self.raw.get("provenance") or {}).get("promotion_blockers") or []
        return tuple(str(b) for b in blockers)

    @property
    def unresolved_parents(self) -> tuple[str, ...]:
        """Parents the secondary named that were never chased to a document."""
        parents = (self.raw.get("provenance") or {}).get("unresolved_parents") or []
        return tuple(str(p) for p in parents)

    def claims(self) -> tuple[Claim, ...]:
        """Every nested provenance record, in document order."""
        return tuple(
            Claim(
                path=path,
                claim_id=str(prov.get("claim_id", "")),
                certification=str(prov.get("certification", "")),
                data=prov,
            )
            for path, prov in _iter_claim_provenance(self.raw)
        )

    def at_least(self, certification: str) -> tuple[Claim, ...]:
        """Claims certified at ``certification`` or above.

        ``node.at_least("bound")`` returning empty is the honest answer for a node
        built entirely from secondary sources — which is currently both of them.
        """
        if certification not in CERTIFICATION_ORDER:
            raise ValueError(
                f"unknown certification {certification!r}; "
                f"expected one of {CERTIFICATION_ORDER}"
            )
        floor = CERTIFICATION_ORDER.index(certification)
        return tuple(c for c in self.claims() if c.tier >= floor)

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_path: Path | None = None) -> NutrientNode:
        if "nutrient_id" not in data:
            raise ValueError("nutrient node requires 'nutrient_id'")
        return cls(
            nutrient_id=str(data["nutrient_id"]),
            node_kind=str(data.get("node_kind", "unknown")),
            raw=data,
            source_path=source_path,
        )


def _iter_claim_provenance(
    node: Any, path: str = "", *, at_root: bool = True
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield every nested ``provenance`` object with its document path.

    The node's own top-level ``provenance`` is document provenance (how the node
    was built) rather than a claim, so it is skipped — it has a different shape
    and validating it against the claim vocabulary would report a false error.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if key == "provenance" and isinstance(value, dict):
                if not at_root:
                    yield child, value
                continue
            yield from _iter_claim_provenance(value, child, at_root=False)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _iter_claim_provenance(item, f"{path}[{index}]", at_root=False)


def node_path(nutrient_id: str) -> Path:
    """Path to a node's YAML file."""
    candidate = DATA_DIR / f"{nutrient_id}.node.yaml"
    if not candidate.is_file():
        raise NodeNotFound(nutrient_id)
    return candidate


def list_nodes() -> list[str]:
    """Every nutrient_id with a node file, sorted."""
    return sorted(p.name[: -len(".node.yaml")] for p in DATA_DIR.glob("*.node.yaml"))


def load_node(nutrient_id: str) -> NutrientNode:
    """Parse one node by nutrient_id. Does not validate — call :func:`validate_node`."""
    path = node_path(nutrient_id)
    data = _require_yaml().safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a YAML mapping at the top level")
    return NutrientNode.from_dict(data, source_path=path)


def iter_nodes() -> Iterator[NutrientNode]:
    """Every shipped node, sorted by nutrient_id."""
    for nutrient_id in list_nodes():
        yield load_node(nutrient_id)


def validate_node(node: NutrientNode | dict[str, Any]) -> ValidationResult:
    """Validate a node against the schema, its claim vocabulary, and its bibliography.

    Three passes, because one JSON Schema cannot express all of it under this
    repo's validator subset:

    1. the document spine, against the schema proper;
    2. every nested ``provenance`` object, against ``$defs.claim_provenance``;
    3. cross-references — each ``claim_id`` unique, every ``source_ref``
       resolving to a key in ``sources``, and every ``parent_ref`` either
       resolving or admitting that it does not.

    Pass 3 carries the real rule. A ``source_ref`` names the document actually
    read, so it must always resolve. A ``parent_ref`` names what *that* document
    cited, which is frequently a reference the extractor could not chase down —
    the zinc node has fourteen such parents. An unresolved ``parent_ref`` is
    therefore legal, but only when the claim states ``existence_verdict:
    NOT_FOUND``. Claiming ``REAL`` while pointing at a bibliography entry that
    does not exist is the failure mode worth catching: it reads as a verified
    citation and is not one.
    """
    data = node.raw if isinstance(node, NutrientNode) else node
    result = validate_against(data, node_schema())
    errors = list(result.errors)
    skipped = set(result.skipped_keywords)

    prov_schema = claim_provenance_schema()
    known_sources = set((data.get("sources") or {}).keys())
    seen_claim_ids: dict[str, str] = {}

    for path, prov in _iter_claim_provenance(data):
        sub = validate_against(prov, prov_schema)
        errors.extend(f"{path}.{e}" if e.startswith(".") else f"{path}: {e}" for e in sub.errors)
        skipped |= set(sub.skipped_keywords)

        claim_id = prov.get("claim_id")
        if isinstance(claim_id, str):
            if claim_id in seen_claim_ids:
                errors.append(
                    f"{path}: duplicate claim_id {claim_id!r} "
                    f"(already used at {seen_claim_ids[claim_id]})"
                )
            else:
                seen_claim_ids[claim_id] = path

        source_ref = prov.get("source_ref")
        if isinstance(source_ref, str) and source_ref not in known_sources:
            errors.append(f"{path}: source_ref {source_ref!r} is not a key in sources")

        parent_ref = prov.get("parent_ref")
        if isinstance(parent_ref, str) and parent_ref not in known_sources:
            if prov.get("existence_verdict") != "NOT_FOUND":
                errors.append(
                    f"{path}: parent_ref {parent_ref!r} is not a key in sources, and the "
                    f"claim does not declare existence_verdict: NOT_FOUND "
                    f"(got {prov.get('existence_verdict', 'nothing')!r}). An unresolved "
                    f"parent must say so."
                )

    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
        skipped_keywords=tuple(sorted(skipped)),
    )


__all__ = [
    "CERTIFICATION_ORDER",
    "Claim",
    "NodeNotFound",
    "NodeUnavailable",
    "NutrientNode",
    "claim_provenance_schema",
    "iter_nodes",
    "list_nodes",
    "load_node",
    "node_schema",
    "schema_path",
    "validate_node",
]
