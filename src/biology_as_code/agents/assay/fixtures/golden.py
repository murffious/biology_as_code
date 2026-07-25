"""
Golden claim fixtures — TASKS.md P0.4.

Each carries evidence set + expected verdict for the pure score() function.
"""

from __future__ import annotations

from typing import Any

GOLDEN: dict[str, dict[str, Any]] = {
    "spirulina-brain-metals": {
        "id": "spirulina-brain-metals",
        "raw_text": (
            "Spirulina PULLS HEAVY METALS OUT OF YOUR BRAIN AND ORGANS. "
            "IT IS THE ONLY FOOD THAT CROSSES THE BLOOD BRAIN BARRIER TO DO IT."
        ),
        "source": {
            "platform": "X",
            "author": "@wellness_maxi",
            "reach": "921K views",
            "posted_at": "2026-06-11T03:28:00Z",
        },
        "expected_verdict": "BUSTED",
        "expected_survived_max": 2,  # confounding often survives; maybe effect_size soft
        "evidence": {
            "human_studies": 1,
            "human_directly_supports": False,
            "animal_or_in_vitro_only": True,
            "dose_form_match": False,
            "mechanism_only": True,
            "effect_size_meaningful": False,
            "confounding_concern": False,
            "has_superlative_atom": True,
            "superlative_false": True,
            "replication_count": 0,
            "rebuttals": 0,
            "confidence_prior": 0.35,
            "notes": {
                "atomization": (
                    "Splits into 4 assertions. The real-ish atom (protects organs) "
                    "rides behind brain / BBB / only-food."
                ),
                "human_evidence": (
                    "~58 preclinical studies vanish. One human trial remains — "
                    "spirulina extract + zinc for arsenic-poisoned patients. Not brain detox."
                ),
                "dose_form": (
                    "Human signal used an extract with zinc; culture doses 20–30 g/day. "
                    "Post implies eating spirulina."
                ),
                "mechanism_vs_outcome": (
                    "Antioxidant is a mechanism. Pulls metals out of your brain is an "
                    "outcome nobody demonstrated."
                ),
                "effect_size": "No meaningful drop in body burden in healthy people.",
                "confounding": "Not the weak point — overreach, not biased association.",
                "superlative": "Chlorella has stronger human detox data; several compounds cross BBB.",
                "replication": "Brain-detox claim has zero replication.",
            },
        },
        "scoped_restatement": (
            "Spirulina is antioxidant-rich. In animals it protects organs from heavy-metal "
            "damage, and one small trial of a spirulina extract + zinc improved arsenic "
            "clearance in poisoned patients. That's the real, narrow kernel — not brain "
            "detox for healthy people, not BBB-crossing as a food, and not the only food studied."
        ),
        "atom_bases": {
            "a1": (
                "Mostly animal studies; mechanism is antioxidant protection, not chelation. "
                "One human signal: extract + zinc for arsenic."
            ),
            "a2": "No study shows spirulina clears metals from human brain tissue.",
            "a3": "Whole spirulina does not cross the BBB; component claims are preliminary animal data.",
            "a4": "Superlative fails — chlorella has stronger human detox data.",
        },
    },
    "creatine-strength": {
        "id": "creatine-strength",
        "raw_text": "Creatine monohydrate increases strength and high-intensity exercise performance.",
        "source": {"platform": "curated", "author": "assay-golden"},
        "expected_verdict": "CONFIRMED",
        "expected_survived_min": 7,
        "evidence": {
            "human_studies": 50,
            "human_directly_supports": True,
            "animal_or_in_vitro_only": False,
            "dose_form_match": True,
            "mechanism_only": False,
            "effect_size_meaningful": True,
            "confounding_concern": False,
            "has_superlative_atom": False,
            "superlative_false": False,
            "replication_count": 20,
            "rebuttals": 0,
            "confidence_prior": 0.9,
            "notes": {
                "human_evidence": "Dozens of RCTs and meta-analyses support strength/power gains.",
                "dose_form": "3–5 g/day monohydrate matches the claim.",
                "mechanism_vs_outcome": "Phosphocreatine buffering is mechanism; strength is measured outcome.",
                "effect_size": "Small-to-moderate but reliable for high-intensity efforts.",
                "replication": "One of the most replicated sport-nutrition findings.",
            },
        },
        "scoped_restatement": (
            "Creatine monohydrate is one of the best-supported ergogenic aids for strength and "
            "high-intensity performance at typical studied doses (≈3–5 g/day), with extensive "
            "human RCT replication. Not a fat-loss drug; responders vary."
        ),
    },
    "flavonoids-cvd": {
        "id": "flavonoids-cvd",
        "raw_text": (
            "Higher dietary flavonoid intake is associated with modestly lower cardiovascular risk."
        ),
        "source": {"platform": "curated", "author": "assay-golden"},
        "expected_verdict": "PLAUSIBLE",
        "expected_survived_min": 4,
        "expected_survived_max": 7,
        "evidence": {
            "human_studies": 12,
            "human_directly_supports": True,
            "animal_or_in_vitro_only": False,
            "dose_form_match": True,
            "mechanism_only": False,
            "effect_size_meaningful": False,  # soft fail → plausible
            "confounding_concern": True,  # soft fail healthy-user
            "has_superlative_atom": False,
            "superlative_false": False,
            "replication_count": 8,
            "rebuttals": 1,
            "confidence_prior": 0.65,
            "notes": {
                "human_evidence": "Prospective cohorts consistently associate higher intake with lower CVD risk.",
                "effect_size": "Modest association; hard-endpoint supplement RCTs often null.",
                "confounding": "Healthy-user confounding remains a live concern in dietary cohorts.",
                "replication": "Association replicates across cohorts; causality still open.",
            },
        },
        "scoped_restatement": (
            "Higher dietary flavonoid intake associates with modestly lower cardiovascular risk "
            "across cohorts. Consistent, but the one hard-endpoint supplement RCT picture is weaker "
            "— association, not proven isolated cause. Prefer food patterns over megadose pills."
        ),
    },
    "organ-healing-drinks": {
        "id": "organ-healing-drinks",
        "raw_text": (
            "ORGAN HEALING DRINKS: Carrot juice heals eyes, beetroot juice heals brain, "
            "ginger tea heals lungs, lemon water heals liver, coconut water heals kidneys, "
            "pomegranate juice heals heart."
        ),
        "source": {"platform": "pinterest-style", "author": "viral-chart"},
        "expected_verdict": "BUSTED",
        "expected_survived_max": 3,
        "evidence": {
            "human_studies": 0,
            "human_directly_supports": False,
            "animal_or_in_vitro_only": True,
            "dose_form_match": False,
            "mechanism_only": True,
            "effect_size_meaningful": False,
            "confounding_concern": False,
            "has_superlative_atom": True,
            "superlative_false": True,
            "replication_count": 0,
            "rebuttals": 0,
            "confidence_prior": 0.2,
            "notes": {
                "atomization": (
                    "Chart bundles ≥6 organ×drink claims under one 'ORGAN HEALING' frame. "
                    "Must split and re-map organs → body systems."
                ),
                "human_evidence": (
                    "No evidence suite that these drinks heal eyes/brain/lungs/liver/kidneys/heart."
                ),
                "mechanism_vs_outcome": (
                    "Nutrient/hydration stories sold as organ healing outcomes."
                ),
                "superlative": "Healing-drinks frame is marketing superlative.",
                "dose_form": "No clinical dose/duration; kitchen beverages ≠ organ therapy.",
                "replication": "Viral chart pattern has no clinical replication as therapy.",
            },
        },
        "scoped_restatement": (
            "This infographic is a multi-claim marketing frame, not a therapy protocol. "
            "Split by organ, map to systems (visual, nervous, respiratory, hepatic, renal, "
            "cardiovascular), and keep only modest nutrient/hydration kernels — never 'heals organ X'."
        ),
    },
    "acv-belly-fat": {
        "id": "acv-belly-fat",
        "raw_text": "Apple cider vinegar melts belly fat fast.",
        "source": {"platform": "tiktok", "author": "viral"},
        "expected_verdict": "BUSTED",
        "expected_survived_max": 4,
        "evidence": {
            "human_studies": 2,
            "human_directly_supports": False,
            "animal_or_in_vitro_only": False,
            "dose_form_match": True,
            "mechanism_only": True,
            "effect_size_meaningful": False,
            "confounding_concern": False,
            "has_superlative_atom": False,
            "superlative_false": False,
            "replication_count": 0,
            "rebuttals": 0,
            "confidence_prior": 0.25,
            "notes": {
                "human_evidence": "Small trials show tiny weight changes, not targeted belly-fat melting.",
                "mechanism_vs_outcome": "Acetic acid metabolic stories ≠ spot-reduction outcome.",
                "effect_size": "Clinically trivial where positive; not 'melts belly fat fast.'",
                "replication": "No robust replication of dramatic fat-loss claims.",
            },
        },
        "scoped_restatement": (
            "Apple cider vinegar is not a belly-fat solvent. Small trials suggest at most minor "
            "weight effects; spot reduction is not supported. Diluted ACV may have other minor "
            "metabolic effects — nothing like viral before/after claims."
        ),
    },
}


def list_golden_ids() -> list[str]:
    return list(GOLDEN.keys())


def get_golden(fid: str) -> dict[str, Any]:
    return GOLDEN[fid]
