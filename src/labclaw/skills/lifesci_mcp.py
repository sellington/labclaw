"""Life Sciences MCP skill — real integrations with biomedical MCP servers.

Connects to life science MCP servers via stdio to provide:
- PubMed literature search (uvx pubmed-mcp)
- bioRxiv/medRxiv preprint search
- ChEMBL drug data queries
- OpenTargets disease-gene queries
- ClinicalTrials.gov search

Each tool lazily connects to its MCP server on first use.
Maps to: LITERATURE_SEARCH and DATA_ANALYSIS steps.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP server definitions
# ---------------------------------------------------------------------------

_MCP_SERVERS: dict[str, dict[str, Any]] = {
    "pubmed": {
        "command": "uvx",
        "args": ["pubmed-mcp"],
        "tool_name": "search",
    },
    "biorxiv": {
        "command": "uvx",
        "args": ["biorxiv-mcp"],
        "tool_name": "search",
    },
    "chembl": {
        "command": "uvx",
        "args": ["chembl-mcp"],
        "tool_name": "query",
    },
    "opentargets": {
        "command": "uvx",
        "args": ["opentargets-mcp"],
        "tool_name": "query",
    },
    "clinical_trials": {
        "command": "uvx",
        "args": ["clinicaltrials-mcp"],
        "tool_name": "search",
    },
}

# Cached MCP sessions per server
_mcp_lock = asyncio.Lock()
_mcp_sessions: dict[str, Any] = {}
_mcp_transports: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Lazy MCP connection
# ---------------------------------------------------------------------------


async def _ensure_session(server_key: str) -> Any:
    """Start the MCP server for *server_key* and return a ClientSession."""
    if server_key in _mcp_sessions:
        return _mcp_sessions[server_key]

    server_cfg = _MCP_SERVERS.get(server_key)
    if server_cfg is None:
        logger.warning("Unknown MCP server key: %s", server_key)
        return None

    async with _mcp_lock:
        if server_key in _mcp_sessions:
            return _mcp_sessions[server_key]

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=server_cfg["command"],
                args=server_cfg["args"],
            )
            transport = stdio_client(params)
            read_stream, write_stream = await transport.__aenter__()
            session = ClientSession(read_stream, write_stream)
            await session.initialize()

            _mcp_sessions[server_key] = session
            _mcp_transports[server_key] = transport
            logger.info("Life-sci MCP server '%s' connected", server_key)
            return session
        except Exception as exc:
            logger.warning("Life-sci MCP '%s' connection failed: %s", server_key, exc)
            return None


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _search_pubmed(
    query: str,
    *,
    max_results: int = 10,
) -> ToolResult:
    """Search PubMed via the pubmed-mcp server."""
    try:
        session = await _ensure_session("pubmed")
        if session is None:
            return ToolResult(
                success=False,
                error="PubMed MCP server not available. Install: uvx pubmed-mcp",
            )
        result = await asyncio.wait_for(
            session.call_tool(
                _MCP_SERVERS["pubmed"]["tool_name"],
                arguments={"query": query, "max_results": max_results},
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "source": "pubmed",
                "query": query,
                "results": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("PubMed search timed out after 30s")
        return ToolResult(success=False, error="PubMed search timed out after 30s")
    except Exception as exc:
        logger.warning("PubMed search failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _search_biorxiv(
    query: str,
    *,
    max_results: int = 10,
) -> ToolResult:
    """Search bioRxiv/medRxiv via the biorxiv-mcp server."""
    try:
        session = await _ensure_session("biorxiv")
        if session is None:
            return ToolResult(
                success=False,
                error="bioRxiv MCP server not available. Install: uvx biorxiv-mcp",
            )
        result = await asyncio.wait_for(
            session.call_tool(
                _MCP_SERVERS["biorxiv"]["tool_name"],
                arguments={"query": query, "max_results": max_results},
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "source": "biorxiv",
                "query": query,
                "results": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("bioRxiv search timed out after 30s")
        return ToolResult(success=False, error="bioRxiv search timed out after 30s")
    except Exception as exc:
        logger.warning("bioRxiv search failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _query_chembl(
    query: str,
    *,
    query_type: str = "compound",
) -> ToolResult:
    """Query ChEMBL drug data via the chembl-mcp server."""
    try:
        session = await _ensure_session("chembl")
        if session is None:
            return ToolResult(
                success=False,
                error="ChEMBL MCP server not available. Install: uvx chembl-mcp",
            )
        result = await asyncio.wait_for(
            session.call_tool(
                _MCP_SERVERS["chembl"]["tool_name"],
                arguments={"query": query, "query_type": query_type},
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "source": "chembl",
                "query": query,
                "query_type": query_type,
                "results": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("ChEMBL query timed out after 30s")
        return ToolResult(success=False, error="ChEMBL query timed out after 30s")
    except Exception as exc:
        logger.warning("ChEMBL query failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _query_opentargets(
    query: str,
    *,
    query_type: str = "target",
) -> ToolResult:
    """Query OpenTargets via the opentargets-mcp server."""
    try:
        session = await _ensure_session("opentargets")
        if session is None:
            return ToolResult(
                success=False,
                error=("OpenTargets MCP server not available. Install: uvx opentargets-mcp"),
            )
        result = await asyncio.wait_for(
            session.call_tool(
                _MCP_SERVERS["opentargets"]["tool_name"],
                arguments={"query": query, "query_type": query_type},
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "source": "opentargets",
                "query": query,
                "query_type": query_type,
                "results": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("OpenTargets query timed out after 30s")
        return ToolResult(success=False, error="OpenTargets query timed out after 30s")
    except Exception as exc:
        logger.warning("OpenTargets query failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _search_clinical_trials(
    query: str,
    *,
    max_results: int = 10,
    status: str = "recruiting",
) -> ToolResult:
    """Search ClinicalTrials.gov via the clinicaltrials-mcp server."""
    try:
        session = await _ensure_session("clinical_trials")
        if session is None:
            return ToolResult(
                success=False,
                error=(
                    "ClinicalTrials.gov MCP server not available. Install: uvx clinicaltrials-mcp"
                ),
            )
        result = await asyncio.wait_for(
            session.call_tool(
                _MCP_SERVERS["clinical_trials"]["tool_name"],
                arguments={
                    "query": query,
                    "max_results": max_results,
                    "status": status,
                },
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "source": "clinical_trials",
                "query": query,
                "status": status,
                "results": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("ClinicalTrials search timed out after 30s")
        return ToolResult(
            success=False,
            error="ClinicalTrials search timed out after 30s",
        )
    except Exception as exc:
        logger.warning("ClinicalTrials search failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# CloudSkill implementation
# ---------------------------------------------------------------------------


class LifeSciMCPSkill:
    """Life Sciences MCP integration — biomedical data via MCP servers."""

    metadata: SkillMetadata = SkillMetadata(
        name="lifesci_mcp",
        version="0.1.0",
        description=(
            "Life Sciences MCP: PubMed, bioRxiv, ChEMBL, OpenTargets, "
            "and ClinicalTrials.gov via MCP protocol."
        ),
        capabilities=[
            SkillCapability.LITERATURE_SEARCH,
            SkillCapability.DATA_ANALYSIS,
        ],
        author="labclaw-core",
        requires_api_key=False,
    )

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for life science MCP access."""
        return [
            AgentTool(
                name="lifesci_search_pubmed",
                description="Search PubMed for biomedical literature.",
                fn=_search_pubmed,
                parameters_schema={
                    "query": {
                        "type": "string",
                        "description": "Search query for PubMed",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                    },
                },
            ),
            AgentTool(
                name="lifesci_search_biorxiv",
                description="Search bioRxiv/medRxiv for preprints.",
                fn=_search_biorxiv,
                parameters_schema={
                    "query": {
                        "type": "string",
                        "description": "Search query for bioRxiv",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                    },
                },
            ),
            AgentTool(
                name="lifesci_query_chembl",
                description="Query ChEMBL for drug compound data.",
                fn=_query_chembl,
                parameters_schema={
                    "query": {
                        "type": "string",
                        "description": "Compound name or ChEMBL ID",
                    },
                    "query_type": {
                        "type": "string",
                        "description": "Query type: compound, target, assay",
                    },
                },
            ),
            AgentTool(
                name="lifesci_query_opentargets",
                description="Query OpenTargets for disease-gene associations.",
                fn=_query_opentargets,
                parameters_schema={
                    "query": {
                        "type": "string",
                        "description": "Gene name, disease, or target ID",
                    },
                    "query_type": {
                        "type": "string",
                        "description": "Query type: target, disease, drug",
                    },
                },
            ),
            AgentTool(
                name="lifesci_search_clinical_trials",
                description="Search ClinicalTrials.gov for clinical studies.",
                fn=_search_clinical_trials,
                parameters_schema={
                    "query": {
                        "type": "string",
                        "description": "Search query for trials",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Trial status filter (default recruiting)",
                    },
                },
            ),
        ]

    async def health_check(self) -> bool:
        """Check if at least one life science MCP server is reachable."""
        for key in _MCP_SERVERS:
            try:
                session = await asyncio.wait_for(
                    _ensure_session(key),
                    timeout=5.0,
                )
                if session is not None:
                    return True
            except Exception:
                continue
        return False

    def configure(self, **kwargs: Any) -> None:
        """Reset MCP connections."""
        if kwargs.get("reset"):
            _mcp_sessions.clear()
            _mcp_transports.clear()


assert isinstance(LifeSciMCPSkill(), CloudSkill)
