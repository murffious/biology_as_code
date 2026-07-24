#!/usr/bin/env python3
"""Run one open dig meal — no product meal score."""

from biology_as_code import simulate_meal

if __name__ == "__main__":
    result = simulate_meal(
        name="demo bowl",
        carbs_g=55,
        protein_g=35,
        fats_g=18,
        fiber_g=22,
        enable_product_score=False,
    )
    print("payload:", result.payload_name)
    print("absorbed:", result.absorbed_macros_g)
    print("residual:", result.residual_macros_g)
    print("pathway_regulation:", result.pathway_regulation)
    print("product_score_available:", result.product_score_available)
