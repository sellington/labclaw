"""MakerClaw — Unified Makerspace AI Control Plane.

Provides first-class `makerclaw` package imports while preserving `labclaw` compatibility.
"""

from __future__ import annotations

from labclaw import __version__
from labclaw.brain import (
    apply_shop_profile,
    execute,
    health,
    list_tools,
    reason,
    write,
)

__all__ = [
    "__version__",
    "apply_shop_profile",
    "execute",
    "health",
    "list_tools",
    "reason",
    "write",
]
