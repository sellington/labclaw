"""ToolUniverse skill — scientific instrument knowledge and protocol search.

Wraps the ToolUniverse API to provide instrument lookup, protocol retrieval,
and equipment recommendation capabilities to the agent runtime.

Maps to: EXPERIMENT step (instrument selection and parameter guidance).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)


async def _search_instruments(
    query: str,
    *,
    category: str = "",
    limit: int = 10,
    api_key: str = "",
    base_url: str = "",
) -> ToolResult:
    """Search ToolUniverse for instruments matching a query."""
    try:
        import httpx

        url = f"{base_url}/api/v1/tools/search" if base_url else ""
        if not url or not api_key:
            return ToolResult(
                success=True,
                data={
                    "results": [],
                    "note": "ToolUniverse not configured (set TOOLUNIVERSE_API_KEY)",
                },
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                params={"q": query, "category": category, "limit": limit},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return ToolResult(
            success=True,
            data={
                "results": data.get("tools", [])[:limit],
                "total": data.get("total", 0),
                "query": query,
            },
        )
    except Exception as exc:
        logger.warning("ToolUniverse search failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _get_protocol(
    instrument_id: str,
    *,
    protocol_type: str = "standard",
    api_key: str = "",
    base_url: str = "",
) -> ToolResult:
    """Retrieve a protocol for a specific instrument from ToolUniverse."""
    try:
        import httpx

        url = f"{base_url}/api/v1/tools/{instrument_id}/protocols" if base_url else ""
        if not url or not api_key:
            return ToolResult(
                success=True,
                data={
                    "protocol": None,
                    "note": "ToolUniverse not configured",
                },
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                params={"type": protocol_type},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return ToolResult(
            success=True,
            data={
                "instrument_id": instrument_id,
                "protocol": data.get("protocol"),
                "parameters": data.get("parameters", {}),
            },
        )
    except Exception as exc:
        logger.warning("ToolUniverse protocol retrieval failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class ToolUniverseSkill:
    """ToolUniverse integration — instrument knowledge for the cloud brain."""

    metadata: SkillMetadata = SkillMetadata(
        name="tooluniverse",
        version="0.1.0",
        description="Scientific instrument search, protocol retrieval, and equipment guidance.",
        capabilities=[SkillCapability.INSTRUMENT_KNOWLEDGE],
        author="labclaw-core",
        requires_api_key=True,
        api_key_env="TOOLUNIVERSE_API_KEY",
    )

    def __init__(self) -> None:
        self._api_key = os.environ.get("TOOLUNIVERSE_API_KEY", "")
        self._base_url = os.environ.get("TOOLUNIVERSE_BASE_URL", "")

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for instrument search and protocol retrieval."""
        from functools import partial

        return [
            AgentTool(
                name="search_instruments",
                description=(
                    "Search ToolUniverse for scientific instruments by name, "
                    "category, or application. Returns matching instruments "
                    "with specifications and availability."
                ),
                fn=partial(
                    _search_instruments,
                    api_key=self._api_key,
                    base_url=self._base_url,
                ),
                parameters_schema={
                    "query": {"type": "string", "description": "Search query"},
                    "category": {
                        "type": "string",
                        "description": "Filter by category (e.g., microscopy, sequencing)",
                    },
                    "limit": {"type": "integer", "description": "Max results (default 10)"},
                },
            ),
            AgentTool(
                name="get_instrument_protocol",
                description=(
                    "Retrieve a standard operating protocol for a specific "
                    "instrument, including setup steps, parameters, and safety."
                ),
                fn=partial(
                    _get_protocol,
                    api_key=self._api_key,
                    base_url=self._base_url,
                ),
                parameters_schema={
                    "instrument_id": {"type": "string", "description": "Instrument ID"},
                    "protocol_type": {
                        "type": "string",
                        "description": "Protocol type (standard, calibration, maintenance)",
                    },
                },
            ),
        ]

    async def health_check(self) -> bool:
        """Check if ToolUniverse API is reachable."""
        if not self._api_key or not self._base_url:
            return False
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._base_url}/api/v1/health",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    def configure(self, **kwargs: Any) -> None:
        """Update API key or base URL at runtime."""
        if "api_key" in kwargs:
            self._api_key = kwargs["api_key"]
        if "base_url" in kwargs:
            self._base_url = kwargs["base_url"]


assert isinstance(ToolUniverseSkill(), CloudSkill)
