"""Regression tests for prepublish deferred items (M4/L3/L4/L5 quality choices)."""

from __future__ import annotations


def test_m4_build_scripts_not_in_package():
    import importlib.util

    # Must not be importable from the installed package path
    assert (
        importlib.util.find_spec(
            "biology_as_code.data.kibo_core.topics._classify_topics_impl"
        )
        is None
    )
    assert (
        importlib.util.find_spec("biology_as_code.data.kibo_core.topics.build_from_list")
        is None
    )


def test_l3_extra_molecular_registered():
    from biology_as_code.dig.digestive_definition_layer import (
        get_digestive_definition_registry,
    )

    reg = get_digestive_definition_registry()
    for sid in ("nhe3", "dra", "mct1", "occludin", "zo1"):
        assert reg.get(sid) is not None, f"missing registered structure {sid}"


def test_l4_single_mechanism_factory_has_expansions():
    from biology_as_code.dig.digestive_mechanism_layer import (
        get_digestive_mechanism_registry,
    )

    reg = get_digestive_mechanism_registry()
    for pid in (
        "electroneutral_nacl_absorption",
        "vagal_afferent_signaling",
        "crf_stress_barrier_response",
    ):
        assert reg.get(pid) is not None, f"missing process {pid}"
    # factory is idempotent-ish: second call still full
    reg2 = get_digestive_mechanism_registry()
    assert len(reg2.list_ids()) >= len(reg.list_ids())


def test_l5_vitamin_modifiers_react_to_low_adequacy():
    from biology_as_code.simulation.metabolic_state import MetabolicState

    st = MetabolicState()
    st.load_vitamins()
    st.energy_charge = 1.0
    # Severe B-vitamin inadequacy should pull energy_charge below 1.0
    for vid in list(st.vitamin_pool):
        if vid.startswith("b") or vid in ("folate", "b9"):
            st.vitamin_pool[vid].adequacy = 0.2
    st.apply_vitamin_modifiers()
    assert st.energy_charge < 1.0
    assert st.vitamin_pool["b1"].coenzyme_factor == max(0.5, 0.2)
