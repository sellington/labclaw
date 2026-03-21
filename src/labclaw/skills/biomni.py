"""Biomni skill — biomedical multimodal AI analysis.

Wraps the Biomni API for biomedical image analysis, molecular interpretation,
and multi-omics data reasoning.

Maps to: ANALYZE step (biomedical data interpretation).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)


async def _analyze_biomedical(
    query: str,
    *,
    data_type: str = "general",
    context: str = "",
    api_key: str = "",
    base_url: str = "",
) -> ToolResult:
    """Analyze biomedical data or images using Biomni."""
    try:
        import httpx

        url = f"{base_url}/api/v1/analyze" if base_url else ""
        if not url or not api_key:
            return ToolResult(
                success=True,
                data={
                    "analysis": "",
                    "note": "Biomni not configured (set BIOMNI_API_KEY)",
                },
            )

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                json={
                    "query": query,
                    "data_type": data_type,
                    "context": context,
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return ToolResult(
            success=True,
            data={
                "analysis": data.get("analysis", ""),
                "confidence": data.get("confidence", 0.0),
                "references": data.get("references", []),
                "data_type": data_type,
            },
        )
    except Exception as exc:
        logger.warning("Biomni analysis failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _interpret_results(
    results: list[dict[str, Any]],
    *,
    domain: str = "neuroscience",
    api_key: str = "",
    base_url: str = "",
) -> ToolResult:
    """Interpret experimental results through a biomedical lens."""
    try:
        import httpx

        url = f"{base_url}/api/v1/interpret" if base_url else ""
        if not url or not api_key:
            return ToolResult(
                success=True,
                data={
                    "interpretation": "",
                    "note": "Biomni not configured",
                },
            )

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                json={"results": results, "domain": domain},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return ToolResult(
            success=True,
            data={
                "interpretation": data.get("interpretation", ""),
                "biological_significance": data.get("significance", ""),
                "suggested_followup": data.get("followup", []),
            },
        )
    except Exception as exc:
        logger.warning("Biomni interpretation failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class BiomniSkill:
    """Biomni integration — biomedical AI analysis for the cloud brain."""

    metadata: SkillMetadata = SkillMetadata(
        name="biomni",
        version="0.1.0",
        description="Biomedical multimodal analysis and result interpretation.",
        capabilities=[SkillCapability.DATA_ANALYSIS, SkillCapability.GENERAL_REASONING],
        author="labclaw-core",
        requires_api_key=True,
        api_key_env="BIOMNI_API_KEY",
    )

    def __init__(self) -> None:
        self._api_key = os.environ.get("BIOMNI_API_KEY", "")
        self._base_url = os.environ.get("BIOMNI_BASE_URL", "")

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for biomedical analysis."""
        from functools import partial

        return [
            AgentTool(
                name="analyze_biomedical",
                description=(
                    "Analyze biomedical data using Biomni AI. Supports imaging, "
                    "molecular, genomic, and multi-omics data interpretation."
                ),
                fn=partial(
                    _analyze_biomedical,
                    api_key=self._api_key,
                    base_url=self._base_url,
                ),
                parameters_schema={
                    "query": {"type": "string", "description": "Analysis query"},
                    "data_type": {
                        "type": "string",
                        "description": "Data type (imaging, molecular, genomic, general)",
                    },
                    "context": {"type": "string", "description": "Additional context"},
                },
            ),
            AgentTool(
                name="interpret_results",
                description=(
                    "Interpret experimental results through a biomedical lens. "
                    "Provides biological significance and suggested follow-ups."
                ),
                fn=partial(
                    _interpret_results,
                    api_key=self._api_key,
                    base_url=self._base_url,
                ),
                parameters_schema={
                    "results": {"type": "array", "description": "Experimental result dicts"},
                    "domain": {
                        "type": "string",
                        "description": "Domain (neuroscience, genomics, etc.)",
                    },
                },
            ),
        ]

    async def health_check(self) -> bool:
        """Check if Biomni API is reachable."""
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
        """Update API key or base URL."""
        if "api_key" in kwargs:
            self._api_key = kwargs["api_key"]
        if "base_url" in kwargs:
            self._base_url = kwargs["base_url"]


assert isinstance(BiomniSkill(), CloudSkill)
