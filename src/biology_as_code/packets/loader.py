"""
Load typed food packets from ``examples/foods/``.

Design note — why these are not packaged data
---------------------------------------------
The packets are *repository examples*, not library data. Copying them into
``src/`` to make them importable from a wheel would create two copies of the
same truth and start them drifting, so the loader resolves them from the repo
checkout instead. When the repo is not on disk (e.g. running from an installed
wheel), :func:`packets_dir` raises :class:`PacketsUnavailable` rather than
returning a silent empty list — an empty result would read as "no packets exist"
instead of "packets not reachable from here".

Resolution order:

1. explicit ``directory=`` argument
2. ``BIOLOGY_AS_CODE_PACKETS`` environment variable
3. ``examples/foods`` found by walking up from this module
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

from biology_as_code.packets.validate import (
    ValidationResult,
    load_schema,
    validate_against,
)

_ENV_VAR = "BIOLOGY_AS_CODE_PACKETS"


class PacketsUnavailable(RuntimeError):
    """Raised when the packet directory cannot be located."""


class PacketNotFound(KeyError):
    """Raised when a packet id does not exist in the resolved directory."""


@dataclass(frozen=True)
class FoodPacket:
    """A typed food packet. Thin, read-only view over the JSON — no derived numbers."""

    id: str
    status: str
    identity: dict[str, Any]
    cargo: tuple[dict[str, Any], ...]
    partners: tuple[dict[str, Any], ...]
    injection_zone: str
    matrix: dict[str, Any]
    teaching: dict[str, Any]
    raw: dict[str, Any]
    source_path: Path | None = None

    @property
    def common_name(self) -> str:
        return str(self.identity.get("common_name", self.id))

    @property
    def is_filled(self) -> bool:
        """True only for packets whose author marked them as filled in."""
        return self.status == "filled"

    @property
    def matrix_integrity(self) -> str:
        """``intact`` | ``partial`` | ``destroyed`` | ``unknown`` (default unknown)."""
        return str(self.matrix.get("integrity", "unknown"))

    def cargo_nutrients(self) -> tuple[str, ...]:
        return tuple(str(c["nutrient"]) for c in self.cargo if "nutrient" in c)

    def partner(self, field_name: str) -> Any:
        """Value of a partner field, or ``None`` when the packet does not declare it.

        ``None`` means *not declared*, which is not the same as ``False``. Callers
        that need to distinguish absence from a declared false must check
        :meth:`declares` first.
        """
        for entry in self.partners:
            if entry.get("field") == field_name:
                return entry.get("value")
        return None

    def declares(self, field_name: str) -> bool:
        """Whether the packet declares this partner field at all."""
        return any(entry.get("field") == field_name for entry in self.partners)

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_path: Path | None = None) -> FoodPacket:
        if "id" not in data or "identity" not in data:
            raise ValueError("food packet requires 'id' and 'identity'")
        return cls(
            id=str(data["id"]),
            status=str(data.get("status", "stub")),
            identity=dict(data.get("identity") or {}),
            cargo=tuple(data.get("cargo") or ()),
            partners=tuple(data.get("partners") or ()),
            injection_zone=str(data.get("injection_zone", "unknown")),
            matrix=dict(data.get("matrix") or {}),
            teaching=dict(data.get("teaching") or {}),
            raw=data,
            source_path=source_path,
        )


def _walk_up_for(relative: str) -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative
        if candidate.is_dir():
            return candidate
    return None


def packets_dir(directory: str | Path | None = None) -> Path:
    """Resolve the food-packet directory, or raise :class:`PacketsUnavailable`."""
    if directory is not None:
        path = Path(directory)
        if not path.is_dir():
            raise PacketsUnavailable(f"not a directory: {path}")
        return path

    env = os.environ.get(_ENV_VAR)
    if env:
        path = Path(env)
        if not path.is_dir():
            raise PacketsUnavailable(f"{_ENV_VAR} does not point at a directory: {path}")
        return path

    found = _walk_up_for("examples/foods")
    if found is None:
        raise PacketsUnavailable(
            "food packets not found. They live in the repository at examples/foods/ and "
            "are not shipped inside the wheel. Clone the repo, pass directory=..., or set "
            f"{_ENV_VAR}."
        )
    return found


def schemas_dir() -> Path:
    found = _walk_up_for("schemas")
    if found is None:
        raise PacketsUnavailable("schemas/ not found; expected a repository checkout")
    return found


@lru_cache(maxsize=1)
def packet_schema() -> dict[str, Any]:
    """The FoodPacket JSON Schema as a dict."""
    return load_schema(schemas_dir() / "food_packet.schema.json")


def load_packet(path: str | Path) -> FoodPacket:
    """Load a single packet from a JSON file path."""
    file_path = Path(path)
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return FoodPacket.from_dict(data, source_path=file_path)


def iter_packets(directory: str | Path | None = None) -> Iterator[FoodPacket]:
    """Yield every packet in the directory, sorted by filename. Skips ``_template``."""
    for file_path in sorted(packets_dir(directory).glob("*.json")):
        if file_path.stem.startswith("_"):
            continue
        yield load_packet(file_path)


def list_packets(directory: str | Path | None = None) -> list[str]:
    """All packet ids available."""
    return [packet.id for packet in iter_packets(directory)]


def get_packet(packet_id: str, directory: str | Path | None = None) -> FoodPacket:
    """Fetch one packet by its ``ex.*`` id."""
    for packet in iter_packets(directory):
        if packet.id == packet_id:
            return packet
    raise PacketNotFound(packet_id)


def validate_packet(packet: FoodPacket | dict[str, Any]) -> ValidationResult:
    """Validate a packet against ``schemas/food_packet.schema.json``."""
    data = packet.raw if isinstance(packet, FoodPacket) else packet
    return validate_against(data, packet_schema())
