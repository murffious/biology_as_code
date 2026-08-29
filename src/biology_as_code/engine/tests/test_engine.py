"""Smoke + promotion tests for the unified engine package."""

from __future__ import annotations

import json
import unittest

from biology_as_code.engine.paths import PACKAGE_ROOT


class TestEngineCore(unittest.TestCase):
    def test_import_package(self):
        from biology_as_code.data import engine

        self.assertEqual(len(engine.SEVEN_SYSTEMS), 7)

    def test_registry_has_promoted_laws(self):
        from biology_as_code.engine.laws import load_system_bound_registry

        reg = load_system_bound_registry()
        self.assertGreaterEqual(len(reg), 47)
        for lid in ("LAW-004", "LAW-043", "LAW-044", "LAW-045", "LAW-046", "LAW-047"):
            self.assertIn(lid, reg, msg=f"missing {lid}")

    def test_registry_qa_law_001_through_047(self):
        from biology_as_code.engine.laws import load_system_bound_registry

        reg = load_system_bound_registry()
        qa = reg.qa()
        self.assertTrue(qa["ok"], msg=qa.get("errors"))
        self.assertEqual(qa["n"], 47)
        # sequential ids
        for i in range(1, 48):
            self.assertIn(f"LAW-{i:03d}", reg)

    def test_iron_walk(self):
        from biology_as_code.engine.laws import walk_pathway
        from biology_as_code.engine.pathways import NONHAEM_IRON_PATHWAY

        r = walk_pathway(
            NONHAEM_IRON_PATHWAY,
            "fe.meal_payload",
            context={"ascorbate_same_meal": True},
        )
        self.assertGreater(r.yield_factor, 1.0)

    def test_sim(self):
        from biology_as_code.engine.sim import MetabolicSimulator, MetabolicState

        out = MetabolicSimulator().run(MetabolicState(fat_g=20, fiber_g=10))
        self.assertTrue(out.micelle_gate_open)
        self.assertIn("L-FAT-1", out.laws_cited)

    def test_cascade(self):
        from biology_as_code.engine.pathways import propagate_cascades

        r = propagate_cascades({"nut.retinol": "low"})
        self.assertFalse(r["diagnosis"])
        self.assertTrue(r["cascades_fired"])

    def test_organ_bounds(self):
        from biology_as_code.engine.geography import ORGAN_BOUNDS

        self.assertIn("stomach", ORGAN_BOUNDS)
        lo, hi = ORGAN_BOUNDS["stomach"].pH_range
        self.assertLess(lo, hi)

    def test_topics_ontology(self):
        from biology_as_code.engine.topics import build_sim_context_template, load_topics

        reg = load_topics()
        self.assertGreater(len(reg), 1000)
        s = reg.summary()
        self.assertIn("mapped", s)
        linked = reg.linked_to_law("LAW-004")
        self.assertTrue(linked)
        ctx = build_sim_context_template()
        self.assertIn("ascorbate_same_meal", ctx)


class TestPromotedLaws043_047(unittest.TestCase):
    """Assert STUB promotions became real system-bound law rows with correct shape."""

    PROMOTED = {
        "LAW-043": {
            "system": "Assimilation",
            "gate_present": True,
            "subsystem_has": "Cobalamin",
            "relation_tokens": ("OPENS_GATE", "CLOSES_GATE"),
        },
        "LAW-044": {
            "system": "Assimilation",
            "gate_present": False,
            "subsystem_has": "SGLT",
            "relation_tokens": ("NARROWS_BOUND",),
        },
        "LAW-045": {
            "system": "Transport",
            "gate_present": True,
            "subsystem_has": "Chylomicron",
            "relation_tokens": ("OPENS_GATE",),
        },
        "LAW-046": {
            "system": "Transport",
            "gate_present": False,
            "subsystem_has": "Portal",
            "relation_tokens": ("portal", "lymph"),
        },
        "LAW-047": {
            "system": "Assimilation",
            "gate_present": False,
            "subsystem_has": "Calcium",
            "relation_tokens": ("NARROWS_BOUND",),
        },
    }

    def setUp(self):
        from biology_as_code.engine.laws import load_system_bound_registry

        self.reg = load_system_bound_registry()

    def test_promoted_shape_and_systems(self):
        for lid, expect in self.PROMOTED.items():
            with self.subTest(lid=lid):
                L = self.reg.get(lid)
                self.assertEqual(L.system_name, expect["system"])
                self.assertEqual(L.gate_present, expect["gate_present"], msg=L.gate_text)
                self.assertIn(expect["subsystem_has"].lower(), L.subsystem.lower())
                self.assertTrue(L.law_statement.strip())
                self.assertTrue(L.bound_text.strip())
                self.assertTrue(L.conditions_text.strip())
                rel = (L.relation_expression or "").upper()
                for tok in expect["relation_tokens"]:
                    self.assertIn(tok.upper(), rel)

    def test_b12_is_gate_not_mere_bound(self):
        L = self.reg.get("LAW-043")
        self.assertTrue(L.gate_present)
        self.assertIn("IF", L.gate_text.upper() + L.law_statement.upper())

    def test_sglt1_is_bound_not_gate(self):
        L = self.reg.get("LAW-044")
        self.assertFalse(L.gate_present)
        self.assertTrue(L.gate_text.lower().startswith("none"))

    def test_ca_fe_not_confused_with_lfat1_gate(self):
        """LAW-047 must stay magnitude-only (false-law contrast vs L-FAT-1)."""
        L = self.reg.get("LAW-047")
        self.assertFalse(L.gate_present)
        self.assertEqual(L.relation_type, "NARROWS_BOUND")
        blob = (L.law_statement + " " + L.bound_text + " " + (L.related_to or "")).lower()
        self.assertTrue(
            "gate" in blob or "l-fat" in blob or "not" in blob,
            msg="expect teaching note that Ca×Fe is not a categorical gate",
        )

    def test_no_retired_stub_ids_as_related_primary(self):
        """Related field may mention history but system should be real LAW ids."""
        for lid in self.PROMOTED:
            L = self.reg.get(lid)
            # related_to should point to other laws / L-FAT-1, not be only a STUB
            related = L.related_to or ""
            self.assertNotEqual(related.strip(), "STUB-A-01")
            self.assertTrue(L.subsystem, msg=f"{lid} empty subsystem")


class TestAssimilationSystem(unittest.TestCase):
    def setUp(self):
        from biology_as_code.engine.laws import load_system_bound_registry

        self.reg = load_system_bound_registry()
        self.assim = self.reg.by_system("Assimilation")

    def test_assimilation_count_and_ids(self):
        # 21 Assimilation laws after 043/044/047 promotion
        self.assertGreaterEqual(len(self.assim), 21)
        ids = {L.id for L in self.assim}
        for lid in (
            "LAW-001",
            "LAW-002",
            "LAW-003",
            "LAW-004",
            "LAW-043",
            "LAW-044",
            "LAW-047",
        ):
            self.assertIn(lid, ids)

    def test_every_assimilation_row_has_lawspec_fields(self):
        for L in self.assim:
            with self.subTest(id=L.id):
                self.assertTrue(L.organ, msg=f"{L.id} missing organ")
                self.assertTrue(L.subsystem, msg=f"{L.id} missing subsystem")
                self.assertTrue(L.law_statement, msg=f"{L.id} missing law")
                self.assertTrue(L.bound_text, msg=f"{L.id} missing bound")
                self.assertTrue(L.conditions_text, msg=f"{L.id} missing conditions")

    def test_flagship_ascorbate_not_gate(self):
        L = self.reg.get("LAW-004")
        self.assertFalse(L.gate_present)
        self.assertIn("EXPANDS_BOUND", L.relation_type)


class TestPrintCards(unittest.TestCase):
    """Print cards for promoted + key Assimilation laws exist past stub depth."""

    PRINT_DIR = (
        PACKAGE_ROOT.parent.parent
        / "gleaned"
        / "registers"
        / "reformulations"
        / "print"
    )

    @classmethod
    def setUpClass(cls):
        if not cls.PRINT_DIR.is_dir():
            raise unittest.SkipTest(f"dev-only gleaned/ tree absent: {cls.PRINT_DIR}")

    def test_promoted_print_cards_exist_and_deepened(self):
        self.assertTrue(self.PRINT_DIR.is_dir(), msg=f"missing {self.PRINT_DIR}")
        for lid in ("LAW-043", "LAW-044", "LAW-045", "LAW-046", "LAW-047"):
            path = self.PRINT_DIR / f"{lid}.md"
            with self.subTest(lid=lid):
                self.assertTrue(path.is_file(), msg=f"missing print card {path}")
                text = path.read_text(encoding="utf-8")
                self.assertIn(lid, text)
                self.assertIn("## Gate", text)
                self.assertIn("## Bound", text)
                self.assertIn("## Typed relation", text)
                # deepen sections (pathway and/or deepen)
                self.assertTrue(
                    "## Pathway" in text or "## Deepen" in text or "depth=`wave" in text,
                    msg=f"{lid} print card still looks like a raw stub",
                )
                self.assertNotIn("depth=`stub`", text)

    def test_assimilation_print_cards_not_stub_depth(self):
        assim_ids = [
            f"LAW-{i:03d}"
            for i in (
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                16,
                19,
                20,
                23,
                24,
                25,
                41,
                42,
                43,
                44,
                47,
            )
        ]
        for lid in assim_ids:
            path = self.PRINT_DIR / f"{lid}.md"
            with self.subTest(lid=lid):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(
                    "depth=`stub`",
                    text,
                    msg=f"{lid} still marked depth=stub after Assimilation deepen",
                )


def _load_topics_classifier():
    """Dev tools live under repo tools/topics_build (not in the wheel)."""
    import importlib.util
    from pathlib import Path

    # .../biology_as_code/src/biology_as_code/engine/tests/this_file
    repo = Path(__file__).resolve().parents[5]
    impl = repo / "tools" / "topics_build" / "_classify_topics_impl.py"
    if not impl.is_file():
        return None
    spec = importlib.util.spec_from_file_location("topics_classify_impl", impl)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestTopicLawLinks(unittest.TestCase):
    def test_pure_classifier_promoted_links(self):
        mod = _load_topics_classifier()
        if mod is None:
            self.skipTest("topics build tools not in tree (dev-only)")
        laws_for_topic_label = mod.laws_for_topic_label
        PROMOTED_STUBS_RETIRED = mod.PROMOTED_STUBS_RETIRED

        cases = {
            "Intrinsic factor": ["LAW-043"],
            "Cobalamin": ["LAW-043"],
            "Vitamin B12": ["LAW-043"],
            "SGLT1": ["LAW-044"],
            "GLUT5": ["LAW-044"],
            "Chylomicron": ["LAW-045"],  # also may get LAW-022/046 via fatty patterns
            "Calcium": ["LAW-042", "LAW-047"],
            "Lacteal": ["LAW-046"],
        }
        for label, must in cases.items():
            with self.subTest(label=label):
                got = laws_for_topic_label(label)
                for lid in must:
                    self.assertIn(lid, got, msg=f"{label} → {got}")
                for stub in PROMOTED_STUBS_RETIRED:
                    self.assertNotIn(stub, got, msg=f"{label} still links retired {stub}")

    def test_ontology_has_no_retired_stub_links(self):
        from biology_as_code.engine.topics import load_topics

        mod = _load_topics_classifier()
        if mod is None:
            self.skipTest("topics build tools not in tree (dev-only)")
        PROMOTED_STUBS_RETIRED = mod.PROMOTED_STUBS_RETIRED

        reg = load_topics()
        # sample critical topics if present
        for label in ("Calcium", "Chylomicron", "SGLT1", "Intrinsic factor", "Cobalamin"):
            node = reg.find(label)
            if node is None:
                continue
            links = set(node.law_links or [])
            overlap = links & PROMOTED_STUBS_RETIRED
            self.assertFalse(
                overlap, msg=f"{label} ontology still has retired stubs {overlap}"
            )

    def test_ontology_links_promoted_laws(self):
        from biology_as_code.engine.topics import load_topics

        reg = load_topics()
        for lid in ("LAW-043", "LAW-044", "LAW-045", "LAW-047"):
            linked = reg.linked_to_law(lid)
            self.assertTrue(
                linked, msg=f"no topics linked to {lid} — rebuild topics ontology?"
            )


class TestL2RedoxCalciumCompetition(unittest.TestCase):
    def test_high_calcium_narrows_iron_factor(self):
        from biology_as_code.engine.sim import MetabolicState
        from biology_as_code.engine.sim.rules_redox import apply_l2_redox_competition

        state = MetabolicState(
            iron_rel=1.0,
            zinc_rel=1.0,
            calcium_rel=10.0,  # high Ca:Fe
            ascorbate_same_meal=False,
        )
        base = state.iron_bioavailability_factor
        out = apply_l2_redox_competition(state)
        self.assertLess(out.iron_bioavailability_factor, base)
        blob = " ".join(out.messages)
        self.assertTrue(
            "LAW-042" in blob or "LAW-047" in blob or "Ca:Fe" in blob,
            msg=f"expected Ca×Fe competition note, got: {blob!r}",
        )

    def test_ascorbate_absence_does_not_hard_close_iron(self):
        from biology_as_code.engine.sim import MetabolicState
        from biology_as_code.engine.sim.rules_redox import apply_l2_redox_competition

        state = MetabolicState(
            iron_rel=1.0,
            zinc_rel=1.0,
            calcium_rel=1.0,
            ascorbate_same_meal=False,
        )
        out = apply_l2_redox_competition(state)
        # without ascorbate, factor stays ~1.0 base (not ×0.1 gate)
        self.assertGreaterEqual(out.iron_bioavailability_factor, 0.5)


class TestSystemsChainMap(unittest.TestCase):
    MAP = (
        PACKAGE_ROOT.parent.parent
        / "gleaned"
        / "registers"
        / "reformulations"
        / "maps"
        / "systems_chain5_laws.json"
    )

    @classmethod
    def setUpClass(cls):
        if not cls.MAP.is_file():
            raise unittest.SkipTest(f"dev-only gleaned/ map absent: {cls.MAP}")

    def test_map_lists_promoted_laws_and_found_stubs(self):
        self.assertTrue(self.MAP.is_file())
        data = json.loads(self.MAP.read_text(encoding="utf-8"))
        law_ids = {x["id"] for x in data["laws"]}
        for lid in ("LAW-043", "LAW-044", "LAW-045", "LAW-046", "LAW-047"):
            self.assertIn(lid, law_ids)
        stubs = {s["id"]: s for s in data["stubs"]}
        for stub, law in (
            ("STUB-A-01", "LAW-043"),
            ("STUB-A-02", "LAW-044"),
            ("STUB-T-01", "LAW-045"),
            ("STUB-T-02", "LAW-046"),
            ("STUB-A-06", "LAW-047"),
        ):
            self.assertEqual(stubs[stub].get("status"), "FOUND")
            self.assertEqual(stubs[stub].get("promoted_to"), law)


if __name__ == "__main__":
    unittest.main()
