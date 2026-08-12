"""
Laws written in Abstract Physiological Operation form.

See ``docs/notational-conventions.md`` for the notation. One law is converted so
far — LAW-004, the flagship EXPANDS_BOUND — as the demonstration that the
notation is executable rather than decorative.
"""

from biology_as_code.engine.laws.ao.law_004 import (
    LAW_004_AO,
    AOStep,
    UncertaintyCompletion,
    apply_law_004,
)

__all__ = ["LAW_004_AO", "AOStep", "UncertaintyCompletion", "apply_law_004"]
