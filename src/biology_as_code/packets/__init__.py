"""
Typed food packets — the input side of the claim auditor.

    from biology_as_code.packets import get_packet, list_packets, validate_packet

    p = get_packet("ex.spinach_salad.zero_fat")
    p.cargo_nutrients()          # ('beta_carotene', 'phylloquinone')
    p.partner("dietary_lipid_g") # 0
    validate_packet(p).valid     # True

Packets live in ``examples/foods/`` in the repository and are not bundled into
the wheel; see :mod:`biology_as_code.packets.loader` for why.
"""

from biology_as_code.packets.loader import (
    FoodPacket,
    PacketNotFound,
    PacketsUnavailable,
    clear_packet_cache,
    get_packet,
    iter_packets,
    list_packets,
    load_packet,
    packet_schema,
    packets_dir,
    validate_packet,
)
from biology_as_code.packets.validate import (
    PacketValidationError,
    ValidationResult,
    unsupported_keywords,
    validate_against,
)

__all__ = [
    "FoodPacket",
    "PacketNotFound",
    "PacketValidationError",
    "PacketsUnavailable",
    "ValidationResult",
    "clear_packet_cache",
    "get_packet",
    "iter_packets",
    "list_packets",
    "load_packet",
    "packet_schema",
    "packets_dir",
    "unsupported_keywords",
    "validate_against",
    "validate_packet",
]
