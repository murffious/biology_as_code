"""The join grammar has to be checkable, or it is a slogan with a schema.

`relation-crosswalk.v1.json` gained an `ontology-join` vocabulary: the predicates
that may run between this project's namespaces, and a `forbidden` block naming the
axioms that may not. A forbidden list nobody tests is worth less than no list —
it reads like a control and functions as a comment.

Two things are asserted here. First, that the prohibition holds in the tree today.
Second, that the allow-list is *self-verifying*: every `ro` id sits next to the
label it resolved to, so `tools/check_curies.py` re-checks all eleven on every run
and the register cannot quietly drift away from the ontologies it quotes.

The forbidden scan is deliberately blunt. It looks for an equivalence operator
with two ontology prefixes near it, which is the shape of the mistake, and it will
flag prose that *demonstrates* the mistake as well as code that commits it. That
is the right trade at this size: the repository asserts no equivalences at all, so
any hit is worth a human look.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
CROSSWALK = REPO / "ontology-sdk" / "relation-crosswalk.v1.json"
CACHE = REPO / "tools" / ".curie_cache"
VOCAB = "ontology-join"

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".curie_cache",
             ".xref_cache", "site"}
SCAN = {".py", ".json", ".md", ".jsonl"}

# An equivalence operator sitting between two ontology-prefixed ids. Assembled so
# this file does not match its own pattern.
EQUIV = re.compile(
    r"(FOODON|CHEBI|GO|UBERON|CL)" + r":\d{4,}[^\n]{0,40}?"
    + r"(owl:equivalentClass|owl:sameAs|skos:exactMatch)"
    + r"[^\n]{0,40}?(FOODON|CHEBI|GO|UBERON|CL)" + r":\d{4,}")


@pytest.fixture(scope="module")
def crosswalk() -> dict:
    return json.loads(CROSSWALK.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def join_rows(crosswalk) -> list[dict]:
    return [r for r in crosswalk["rows"] if r["vocabulary"] == VOCAB]


def test_the_vocabulary_is_declared_and_populated(crosswalk, join_rows):
    assert VOCAB in crosswalk["vocabularies"]
    assert len(join_rows) == len(crosswalk["vocabularies"][VOCAB]["members"])
    assert len(join_rows) >= 11


def test_every_join_predicate_declares_its_endpoints(join_rows):
    """A join predicate without a domain and a range is not a join predicate — it
    is a verb with an opinion. The endpoints are the whole content of the row."""
    for r in join_rows:
        assert r.get("domain"), f"{r['verb']} has no domain"
        assert r.get("range"), f"{r['verb']} has no range"
        assert r.get("ro"), f"{r['verb']} has no relation id"
        assert r.get("label"), f"{r['verb']} has no resolved label"


def test_every_relation_id_is_cached_and_resolves(join_rows):
    """Self-verification, and the reason `ro` is an id key in check_curies.py's
    PAIR_PATTERNS. If this fails the register is quoting an id nobody looked up."""
    missing, dead = [], []
    for r in join_rows:
        cp = CACHE / (r["ro"].replace(":", "_") + ".json")
        if not cp.exists():
            missing.append(r["ro"])
            continue
        if json.loads(cp.read_text()) is None:
            dead.append(r["ro"])
    assert not dead, f"relation ids that do not resolve: {dead}"
    if missing:
        pytest.skip(f"not in the local curie cache: {missing} — run tools/check_curies.py")


def test_the_declared_label_is_the_resolved_label(join_rows):
    """Written so the label diff in check_curies.py is meaningful rather than
    decorative: the register must carry what OLS4 actually returned."""
    for r in join_rows:
        cp = CACHE / (r["ro"].replace(":", "_") + ".json")
        if not cp.exists():
            continue
        got = json.loads(cp.read_text())
        assert got and got.get("label") == r["label"], (
            f"{r['verb']}: register says {r['label']!r}, {r['ro']} resolves to "
            f"{(got or {}).get('label')!r}")


def test_only_one_join_predicate_is_a_base_edge(join_rows):
    """The shape of the finding. The base is eleven ways to make a claim about
    biology; a namespace join is not a claim, so `none` is the expected answer and
    the single exception should stay conspicuous."""
    direct = [r for r in join_rows if r["relation"] != "none"]
    assert [r["verb"] for r in direct] == ["has_component"]
    assert direct[0]["base"] == "CONTAINS"


def test_the_forbidden_block_names_its_enforcer(crosswalk):
    forbidden = crosswalk["forbidden"]
    assert forbidden["axioms"], "a forbidden list with no axioms"
    enforcer = REPO / forbidden["enforced_by"]
    assert enforcer.is_file(), f"{forbidden['enforced_by']} does not exist"
    assert enforcer.resolve() == pathlib.Path(__file__).resolve()


def test_no_forbidden_equivalence_is_asserted_anywhere():
    """The prohibition, actually checked. The repository asserts no cross-namespace
    equivalences today; this keeps it that way."""
    hits = []
    for p in REPO.rglob("*"):
        if not p.is_file() or p.suffix not in SCAN:
            continue
        if SKIP_DIRS & set(p.parts) or p.resolve() == pathlib.Path(__file__).resolve():
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for m in EQUIV.finditer(text):
            hits.append(f"{p.relative_to(REPO)}: {m.group(0)[:70]}")
    assert not hits, "cross-namespace equivalence asserted:\n  " + "\n  ".join(hits)
