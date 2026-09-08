"""
The cross-reference sidecar must not become a second, quieter crosswalk.

``MASTER_CROSSWALK.xrefs.tsv`` fills cells that VMH left OPEN, from MNXref and
ModelSEED. That is useful and it is also the exact shape of the failure this
repository exists to argue against: a table that grows values whose origin has
gone missing, or that silently overwrites a measured value with a guessed one.

So the invariants below are about restraint, not coverage. A sidecar row must
name its source and its licence; it may only ever touch a cell that reads OPEN;
it may never carry an identifier MNXref has already deprecated; and it must speak
the same CURIE dialect as the canonical table, because a join key in two dialects
is not a join key.

The artefact tests run everywhere. The regeneration tests need ``.xref_cache/``,
which is machine-local by design (the upstream chem_xref.tsv is ~680 MB and is
not vendored), so they skip when it is absent rather than failing in CI.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "enrich_crosswalk_xrefs.py"
CANONICAL = REPO_ROOT / "MASTER_CROSSWALK.tsv"
SIDECAR = REPO_ROOT / "MASTER_CROSSWALK.xrefs.tsv"
CONFLICTS = REPO_ROOT / "MASTER_CROSSWALK.xrefs.conflicts.tsv"
CACHE = REPO_ROOT / ".xref_cache"

OPEN = "OPEN"

# Canonical forms, per tools/normalize_crosswalk.py. Restated here on purpose:
# if the normalizer's dialect changes, this test should fail rather than follow.
VALUE_FORM = {
    "chebi": re.compile(r"chebi:\d+"),
    "kegg": re.compile(r"kegg:C\d{5}"),
    "hmdb": re.compile(r"hmdb:HMDB\d{7}"),
    "seed": re.compile(r"cpd\d{5}"),
    "inchiKey": re.compile(r"[A-Z]{14}-[A-Z]{10}-[A-Z]"),
}


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


@pytest.fixture(scope="module")
def canonical() -> dict[str, dict[str, str]]:
    return {r["vmh"]: r for r in _tsv(CANONICAL)}


@pytest.fixture(scope="module")
def sidecar() -> list[dict[str, str]]:
    return _tsv(SIDECAR)


@pytest.fixture(scope="module")
def conflicts() -> list[dict[str, str]]:
    return _tsv(CONFLICTS)


def test_sidecar_schema_is_exact(sidecar):
    """Every row names the cell, the value, the reconciliation anchor, and the terms."""
    assert sidecar, "sidecar is empty — regenerate it"
    assert list(sidecar[0]) == ["vmh", "column", "value", "mnx", "source",
                                "source_version", "licence", "licence_class"]


def test_every_sidecar_row_targets_a_real_row(sidecar, canonical):
    orphans = {r["vmh"] for r in sidecar} - set(canonical)
    assert not orphans, f"sidecar references {len(orphans)} vmh ids not in the crosswalk"


def test_sidecar_only_ever_fills_open_cells(sidecar, canonical):
    """The load-bearing one. A populated cell is VMH's measurement; the sidecar is
    an outside opinion. If this fails, the table has been quietly overwritten."""
    overwrites = [(r["vmh"], r["column"], canonical[r["vmh"]][r["column"]], r["value"])
                  for r in sidecar if canonical[r["vmh"]][r["column"]] != OPEN]
    assert not overwrites, f"{len(overwrites)} populated cell(s) overwritten: {overwrites[:5]}"


def test_no_cell_is_filled_twice(sidecar):
    seen = [(r["vmh"], r["column"]) for r in sidecar]
    assert len(seen) == len(set(seen)), "a cell appears more than once in the sidecar"


def test_every_row_carries_its_provenance(sidecar):
    for r in sidecar:
        assert r["source"] and r["source_version"], f"{r['vmh']}/{r['column']} has no source"
        assert r["licence"], f"{r['vmh']}/{r['column']} has no licence"
        assert r["mnx"].startswith(("MNXM", "BIOMASS", "WATER")), f"bad anchor {r['mnx']}"


def test_restricted_cells_are_withheld_by_default(sidecar):
    """KEGG forbids non-academic use without a licence; HMDB forbids commercial
    redistribution. This repository is Apache-2.0, which grants both. Those cells
    stay out of the shipped artefact until that is resolved."""
    leaked = [r for r in sidecar if r["licence_class"] == "restricted"]
    assert not leaked, f"{len(leaked)} restricted cell(s) shipped: {leaked[:3]}"
    assert not [r for r in sidecar if r["column"] in ("kegg", "hmdb")]


def test_values_speak_the_canonical_dialect(sidecar):
    """A join key in two dialects is not a join key."""
    for r in sidecar:
        pattern = VALUE_FORM[r["column"]]
        for value in r["value"].split(";"):
            assert pattern.fullmatch(value), f"{r['vmh']}/{r['column']}: {value!r}"


def test_no_deprecated_identifiers(sidecar):
    """MNXref prefixes superseded accessions ``M_`` and labels them
    'secondary/obsolete/fantasy identifier'. Filling a cell with one of those is
    worse than leaving it OPEN."""
    assert not [r for r in sidecar if "M_" in r["value"]]


def test_inchikey_is_the_column_this_actually_unblocks(sidecar, canonical):
    """THIRD-PARTY-DATA.json records that VMH shipped no InChIKey at all: 'any plan
    treating InChIKey as an available join key is building on nothing'. It still
    ships none — this asserts the sidecar is where the change lives, not the table."""
    assert all(r["inchiKey"] == OPEN for r in canonical.values())
    filled = [r for r in sidecar if r["column"] == "inchiKey"]
    assert len(filled) > 1000, f"only {len(filled)} InChIKeys — cache may be stale"


def test_conflicts_are_real_disagreements(conflicts, canonical):
    """A conflict is a populated cell an independent source contradicts. It is
    reported and never applied; if one of these ever became a fill, the sidecar
    would be laundering a disagreement into a fact."""
    for r in conflicts:
        current = canonical[r["vmh"]][r["column"]]
        assert current != OPEN, f"{r['vmh']}/{r['column']} is OPEN, not a conflict"
        assert current == r["canonical_value"]
        assert current not in r["external_value"].split(";")


def test_conflicts_are_not_also_fills(conflicts, sidecar):
    overlap = {(r["vmh"], r["column"]) for r in conflicts} & {(r["vmh"], r["column"]) for r in sidecar}
    assert not overlap, f"cells both filled and in conflict: {sorted(overlap)[:5]}"


# --- regeneration: needs the machine-local cache ----------------------------

needs_cache = pytest.mark.skipif(
    not (CACHE / "mnx_xref.tsv").is_file(),
    reason="no .xref_cache/ — run `python3 tools/enrich_crosswalk_xrefs.py --fetch`",
)


@needs_cache
def test_shipped_sidecar_matches_a_fresh_regeneration():
    r = subprocess.run([sys.executable, str(TOOL), "--check"], cwd=REPO_ROOT,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr


@needs_cache
def test_the_tool_never_writes_the_canonical_table():
    """`make crosswalk-check` compares MASTER_CROSSWALK.tsv byte for byte against
    normalize(extract). Enrichment that touched it would break that gate and erase
    the line between what VMH said and what we added."""
    before = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(TOOL)], cwd=REPO_ROOT,
                   capture_output=True, text=True, timeout=300)
    assert hashlib.sha256(CANONICAL.read_bytes()).hexdigest() == before


@needs_cache
def test_restricted_cells_exist_and_are_classified():
    """The withholding must be a decision, not an empty result: assert the cells
    are really there behind the flag, and that every one is labelled."""
    sys.path.insert(0, str(REPO_ROOT))
    from tools.enrich_crosswalk_xrefs import build

    fills, _, _ = build(include_restricted=True)
    restricted = [f for f in fills if f[7] == "restricted"]
    assert restricted, "nothing was withheld — the licence gate is not doing anything"
    assert {f[1] for f in restricted} == {"kegg", "hmdb"}
    open_fills, _, _ = build(include_restricted=False)
    assert len(open_fills) == len(fills) - len(restricted)
