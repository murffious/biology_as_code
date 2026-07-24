"""
Optional product meal-score analysis (patent-pending IP).

Open dig/sim does **not** require this package. When proprietary code is
absent, ``run_product_score_analysis`` returns an unavailable stub.

See ``README.md`` in this package and ``PROPRIETARY_IP.md`` at the repo root.
"""

from .interface import ProductScoreAnalyzer, ProductScoreRequest, ProductScoreResult
from .loader import (
    get_product_score_analyzer,
    product_score_available,
    run_product_score_analysis,
    unavailable_result,
)

__all__ = [
    "ProductScoreAnalyzer",
    "ProductScoreRequest",
    "ProductScoreResult",
    "get_product_score_analyzer",
    "product_score_available",
    "run_product_score_analysis",
    "unavailable_result",
]
