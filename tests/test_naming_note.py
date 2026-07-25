"""
The naming disambiguation must stay consistent across every surface that carries it.

`docs/naming.md` is the canonical text. Five other places carry a shortened
version: the README, the package docstring, the Zenodo deposit description, and the
JOSS paper. Prose duplicated across a Markdown file, a Python docstring, a JSON
field and a LaTeX-bound paper is exactly the kind of thing that drifts — one gets
updated, three do not, and the project ends up making three slightly different
claims about its own name.

These tests do not require identical wording, which would be unmaintainable across
four formats. They assert the invariants: every surface names the prior art, every
surface states the descriptive/prescriptive distinction, and the package-facing
copy does not overclaim by importing the book's disciplinary thesis.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import biology_as_code

REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL = REPO_ROOT / "docs" / "naming.md"


def _read(*parts: str) -> str:
    return (REPO_ROOT / Path(*parts)).read_text(encoding="utf-8")


def surfaces() -> dict[str, str]:
    """Every place the note appears, as plain text."""
    return {
        "docs/naming.md": CANONICAL.read_text(encoding="utf-8"),
        "README.md": _read("README.md"),
        "package docstring": biology_as_code.__doc__ or "",
        "zenodo": json.loads(_read(".zenodo.json"))["description"],
        "paper/paper.md": _read("paper", "paper.md"),
    }


@pytest.mark.parametrize("name", list(surfaces()))
def test_every_surface_names_the_prior_art(name: str):
    """A disambiguation that does not name what it disambiguates from is useless."""
    text = surfaces()[name]
    assert "Barbieri" in text, f"{name} does not name the prior art"


@pytest.mark.parametrize("name", list(surfaces()))
def test_every_surface_marks_the_claim_as_methodological(name: str):
    """The load-bearing move is 'this is a method, not a theory of biology'."""
    text = surfaces()[name].lower()
    assert "methodolog" in text or "prescriptive" in text, (
        f"{name} does not state the methodological/prescriptive claim"
    )


@pytest.mark.parametrize("name", ["docs/naming.md", "README.md", "paper/paper.md"])
def test_longer_surfaces_state_the_descriptive_contrast(name: str):
    """Anywhere there is room, say what the other program is: descriptive."""
    text = surfaces()[name].lower()
    assert "descriptive" in text, f"{name} omits the descriptive/prescriptive contrast"


def test_package_docstring_stays_one_sentence_and_defers():
    """A docstring is not the place for an argument. Point at the long version."""
    doc = biology_as_code.__doc__ or ""
    note_lines = [line for line in doc.splitlines() if "Barbieri" in line or "semiotic" in line]
    assert note_lines, "docstring note missing"
    assert "docs/naming.md" in doc, "docstring should defer to the canonical text"
    assert len(" ".join(note_lines)) < 220, "docstring note has grown into an argument"


def test_package_facing_copy_does_not_import_the_book_thesis():
    """The package is a 0.1.0 alpha; asserting what a whole field *should* do overclaims.

    docs/naming.md explains why the package-facing copy makes a narrower claim than
    the book. This guards that decision against a well-meaning copy-paste.
    """
    for name in ("README.md", "package docstring", "zenodo"):
        text = surfaces()[name].lower()
        assert "nutrition science should" not in text, (
            f"{name} imports the book's disciplinary thesis; keep the narrower claim"
        )


def test_paper_scopes_the_note_to_the_software():
    """JOSS reviews software, so the paper's note must be about the software."""
    paper = surfaces()["paper/paper.md"]
    assert "@barbieri2015" in paper, "paper note must carry the citation"
    assert "This software makes no such claim" in paper


def test_canonical_page_documents_every_other_surface():
    """docs/naming.md is the source of truth, so it must list where the copies live."""
    canonical = surfaces()["docs/naming.md"]
    for marker in ("README", "docstring", "Zenodo", "JOSS"):
        assert marker in canonical, f"canonical page does not mention the {marker} copy"


def test_canonical_page_is_in_the_site_nav():
    assert "naming.md" in _read("mkdocs.yml"), "naming page missing from mkdocs nav"
