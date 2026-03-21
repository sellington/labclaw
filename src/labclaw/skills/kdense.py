"""K-Dense skill — real integration with K-Dense AI scientific skills.

Uses the claude-skills-mcp server (pip install claude-skills-mcp) via
the MCP protocol to access 170+ scientific skills covering bioinformatics,
cheminformatics, clinical research, ML/AI, and lab automation.

The MCP server exposes:
- find_helpful_skills: semantic search over all skills
- read_skill_document: retrieve specific skill content
- list_skills: full inventory

Maps to: ASK step (skill discovery) and GENERAL_REASONING.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)

# Cached MCP session
_mcp_lock = asyncio.Lock()
_mcp_session: Any = None
_mcp_transport: Any = None


async def _ensure_mcp_session() -> Any:
    """Start the K-Dense MCP server and connect via stdio."""
    global _mcp_session, _mcp_transport  # noqa: PLW0603
    if _mcp_session is not None:
        return _mcp_session

    async with _mcp_lock:
        if _mcp_session is not None:
            return _mcp_session

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command="uvx",
                args=["claude-skills-mcp"],
            )
            transport = stdio_client(server_params)
            read_stream, write_stream = await transport.__aenter__()
            session = ClientSession(read_stream, write_stream)
            await session.initialize()

            _mcp_session = session
            _mcp_transport = transport
            logger.info("K-Dense MCP server connected")
            return session
        except Exception as exc:
            logger.warning("K-Dense MCP connection failed: %s", exc)
            return None


async def _find_skills(
    description: str,
    *,
    limit: int = 5,
) -> ToolResult:
    """Find relevant scientific skills by description."""
    try:
        session = await _ensure_mcp_session()
        if session is None:
            return ToolResult(
                success=False,
                error="K-Dense MCP server not available. Install: pip install claude-skills-mcp",
            )

        result = await asyncio.wait_for(
            session.call_tool(
                "find_helpful_skills",
                arguments={"description": description, "limit": limit},
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "skills": result.content if hasattr(result, "content") else str(result),
                "query": description,
            },
        )
    except TimeoutError:
        logger.warning("K-Dense find_skills timed out after 30s")
        return ToolResult(success=False, error="K-Dense find_skills timed out after 30s")
    except Exception as exc:
        logger.warning("K-Dense find_skills failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _read_skill(
    skill_name: str,
) -> ToolResult:
    """Read the full content of a specific skill document."""
    try:
        session = await _ensure_mcp_session()
        if session is None:
            return ToolResult(
                success=False,
                error="K-Dense MCP server not available",
            )

        result = await asyncio.wait_for(
            session.call_tool(
                "read_skill_document",
                arguments={"skill_name": skill_name},
            ),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "skill_name": skill_name,
                "content": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("K-Dense read_skill timed out after 30s")
        return ToolResult(success=False, error="K-Dense read_skill timed out after 30s")
    except Exception as exc:
        logger.warning("K-Dense read_skill failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _list_all_skills() -> ToolResult:
    """List all available K-Dense scientific skills."""
    try:
        session = await _ensure_mcp_session()
        if session is None:
            return ToolResult(
                success=False,
                error="K-Dense MCP server not available",
            )

        result = await asyncio.wait_for(
            session.call_tool("list_skills", arguments={}),
            timeout=30.0,
        )
        return ToolResult(
            success=True,
            data={
                "skills": result.content if hasattr(result, "content") else str(result),
            },
        )
    except TimeoutError:
        logger.warning("K-Dense list_skills timed out after 30s")
        return ToolResult(success=False, error="K-Dense list_skills timed out after 30s")
    except Exception as exc:
        logger.warning("K-Dense list_skills failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class KDenseSkill:
    """Real K-Dense integration — 170+ scientific skills via MCP."""

    metadata: SkillMetadata = SkillMetadata(
        name="kdense",
        version="0.2.0",
        description=(
            "K-Dense AI: 170+ scientific skills, 250+ databases. "
            "Bioinformatics, cheminformatics, clinical research, "
            "lab automation, and more via MCP protocol."
        ),
        capabilities=[
            SkillCapability.LITERATURE_SEARCH,
            SkillCapability.GENERAL_REASONING,
            SkillCapability.INSTRUMENT_KNOWLEDGE,
        ],
        author="labclaw-core",
        requires_api_key=False,
    )

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for K-Dense access."""
        return [
            AgentTool(
                name="kdense_find_skills",
                description=(
                    "Find relevant scientific skills from "
                    "K-Dense's 170+ skills library by description."
                ),
                fn=_find_skills,
                parameters_schema={
                    "description": {
                        "type": "string",
                        "description": "What you need to do",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 5)",
                    },
                },
            ),
            AgentTool(
                name="kdense_read_skill",
                description=(
                    "Read the full content of a K-Dense skill document, including code examples."
                ),
                fn=_read_skill,
                parameters_schema={
                    "skill_name": {
                        "type": "string",
                        "description": "Skill name to read",
                    },
                },
            ),
            AgentTool(
                name="kdense_list_skills",
                description="List all available K-Dense skills.",
                fn=_list_all_skills,
                parameters_schema={},
            ),
        ]

    async def health_check(self) -> bool:
        """Check if K-Dense MCP server can be started."""
        try:
            session = await asyncio.wait_for(
                _ensure_mcp_session(),
                timeout=5.0,
            )
            return session is not None
        except Exception:
            return False

    def configure(self, **kwargs: Any) -> None:
        """Reset MCP session."""
        global _mcp_session, _mcp_transport  # noqa: PLW0603
        if kwargs.get("reset"):
            _mcp_session = None
            _mcp_transport = None


assert isinstance(KDenseSkill(), CloudSkill)
