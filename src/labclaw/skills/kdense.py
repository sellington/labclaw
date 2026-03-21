"""K-Dense skill — scientific literature retrieval and knowledge synthesis.

Provides knowledge-dense retrieval from scientific papers, enabling the
agent to ground hypotheses and analyses in published literature.

Maps to: ASK step (literature context) and HYPOTHESIZE step (prior work).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)


async def _search_literature(
    query: str,
    *,
    max_results: int = 10,
    year_from: int = 0,
    year_to: int = 0,
    api_key: str = "",
    base_url: str = "",
) -> ToolResult:
    """Search scientific literature for papers related to a query."""
    try:
        import httpx

        url = f"{base_url}/api/v1/search" if base_url else ""
        if not url or not api_key:
            return ToolResult(
                success=True,
                data={
                    "papers": [],
                    "note": "K-Dense not configured (set KDENSE_API_KEY)",
                },
            )

        params: dict[str, Any] = {"q": query, "limit": max_results}
        if year_from:
            params["year_from"] = year_from
        if year_to:
            params["year_to"] = year_to

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return ToolResult(
            success=True,
            data={
                "papers": data.get("results", [])[:max_results],
                "total": data.get("total", 0),
                "query": query,
            },
        )
    except Exception as exc:
        logger.warning("K-Dense literature search failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _synthesize_knowledge(
    topic: str,
    *,
    context_papers: list[str] | None = None,
    api_key: str = "",
    base_url: str = "",
) -> ToolResult:
    """Synthesize knowledge from multiple papers on a topic."""
    try:
        import httpx

        url = f"{base_url}/api/v1/synthesize" if base_url else ""
        if not url or not api_key:
            return ToolResult(
                success=True,
                data={
                    "synthesis": "",
                    "note": "K-Dense not configured",
                },
            )

        payload: dict[str, Any] = {"topic": topic}
        if context_papers:
            payload["paper_ids"] = context_papers

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return ToolResult(
            success=True,
            data={
                "synthesis": data.get("synthesis", ""),
                "key_findings": data.get("key_findings", []),
                "cited_papers": data.get("cited_papers", []),
            },
        )
    except Exception as exc:
        logger.warning("K-Dense synthesis failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class KDenseSkill:
    """K-Dense integration — scientific literature retrieval for the cloud brain."""

    metadata: SkillMetadata = SkillMetadata(
        name="kdense",
        version="0.1.0",
        description="Scientific literature search and knowledge synthesis from papers.",
        capabilities=[
            SkillCapability.LITERATURE_SEARCH,
            SkillCapability.HYPOTHESIS_GENERATION,
        ],
        author="labclaw-core",
        requires_api_key=True,
        api_key_env="KDENSE_API_KEY",
    )

    def __init__(self) -> None:
        self._api_key = os.environ.get("KDENSE_API_KEY", "")
        self._base_url = os.environ.get("KDENSE_BASE_URL", "")

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for literature search and synthesis."""
        from functools import partial

        return [
            AgentTool(
                name="search_literature",
                description=(
                    "Search scientific literature for papers related to a query. "
                    "Returns titles, abstracts, authors, and relevance scores."
                ),
                fn=partial(
                    _search_literature,
                    api_key=self._api_key,
                    base_url=self._base_url,
                ),
                parameters_schema={
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max papers (default 10)"},
                    "year_from": {"type": "integer", "description": "Filter by year (start)"},
                    "year_to": {"type": "integer", "description": "Filter by year (end)"},
                },
            ),
            AgentTool(
                name="synthesize_knowledge",
                description=(
                    "Synthesize knowledge from scientific papers on a topic. "
                    "Returns a coherent summary with key findings and citations."
                ),
                fn=partial(
                    _synthesize_knowledge,
                    api_key=self._api_key,
                    base_url=self._base_url,
                ),
                parameters_schema={
                    "topic": {"type": "string", "description": "Topic to synthesize"},
                    "context_papers": {
                        "type": "array",
                        "description": "Paper IDs to include in synthesis",
                    },
                },
            ),
        ]

    async def health_check(self) -> bool:
        """Check if K-Dense API is reachable."""
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


assert isinstance(KDenseSkill(), CloudSkill)
