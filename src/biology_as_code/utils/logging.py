"""Package logging — quiet by default (WARNING)."""

from __future__ import annotations

import logging
import os

_LOGGER_NAME = "biology_as_code"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under biology_as_code."""
    base = logging.getLogger(_LOGGER_NAME)
    if not base.handlers:
        # Avoid "No handlers" noise; respect root configuration if user set it.
        handler = logging.NullHandler()
        base.addHandler(handler)
        # Default quiet; set BIOLOGY_AS_CODE_LOG=DEBUG|INFO to enable console-ish use
        level_name = os.environ.get("BIOLOGY_AS_CODE_LOG", "WARNING").upper()
        base.setLevel(getattr(logging, level_name, logging.WARNING))
    if name:
        return base.getChild(name.replace("biology_as_code.", ""))
    return base


def configure_logging(level: str = "WARNING") -> None:
    """Optional explicit configure for demos/CLIs."""
    base = logging.getLogger(_LOGGER_NAME)
    base.handlers.clear()
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    base.addHandler(h)
    base.setLevel(getattr(logging, level.upper(), logging.WARNING))
    base.propagate = False
