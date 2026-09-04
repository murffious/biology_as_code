"""ontology-sdk/ontology.json must agree with itself and with what it quotes.

The checker lives beside the manifest so it can be run by hand; this file only
makes sure the suite runs it. A skipped cross-repo check is reported, not
counted as a pass — the sibling checkout is not available in CI.
"""
import importlib.util
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[1] / "ontology-sdk" / "check_manifest.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_manifest", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_manifest_holds():
    cm = _load()
    results = cm.run()
    failed = [(n, msgs) for n, s, msgs in results if s == cm.FAIL]
    assert not failed, "\n".join(f"{n}: {m}" for n, msgs in failed for m in msgs)


def test_manifest_has_the_blocks_get_standard_advertises():
    """nutri-collective's get_standard names these sections in its docstring."""
    import json
    m = json.loads((CHECKER.parent / "ontology.json").read_text())
    assert {"predicates", "object_types", "interfaces", "entity_kinds",
            "actions", "types", "spine_stages"} <= set(m)
