"""Lightweight package config (no product score secrets)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackageConfig:
    """Runtime flags for open dig."""

    enable_product_score: bool = False  # patent-pending plugin; default off
    claim_tier_default: str = "open"
    verbose: bool = False


DEFAULT_CONFIG = PackageConfig()
