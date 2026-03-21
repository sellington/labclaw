"""ToolUniverse skill — real integration with mims-harvard/ToolUniverse SDK.

Uses the tooluniverse Python package (pip install tooluniverse) to provide
2000+ scientific tools covering UniProt, ChEMBL, PubChem, OpenTargets,
FAERS, ClinicalTrials, and more.

Maps to: EXPERIMENT step (instrument/tool selection) and ANALYZE step.
"""

from __future__ import annotations

import logging
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)

# Lazy-loaded singleton to avoid slow startup
_tu_instance: Any = None


def _get_tu() -> Any:
    """Get or create the ToolUniverse singleton."""
    global _tu_instance  # noqa: PLW0603
    if _tu_instance is None:
        from tooluniverse import ToolUniverse

        _tu_instance = ToolUniverse()
        _tu_instance.load_tools()
        logger.info(
            "ToolUniverse initialized with %d tools",
            len(_tu_instance.return_all_loaded_tools()),
        )
    return _tu_instance


def _sync_run(tu: Any, payload: dict[str, Any]) -> Any:
    """Run tu.run() in a thread to avoid event-loop conflicts."""
    return tu.run(payload)


async def _run_tool(
    name: str,
    *,
    arguments: dict[str, Any] | None = None,
) -> ToolResult:
    """Execute a ToolUniverse tool by name with arguments."""
    try:
        import asyncio

        tu = _get_tu()
        payload = {"name": name, "arguments": arguments or {}}
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _sync_run, tu, payload)

        if isinstance(result, dict) and result.get("status") == "error":
            return ToolResult(
                success=False,
                error=result.get("error", "Unknown error"),
            )

        return ToolResult(success=True, data=result)
    except Exception as exc:
        logger.warning("ToolUniverse run(%s) failed: %s", name, exc)
        return ToolResult(success=False, error=str(exc))


async def _find_tools(
    description: str,
    *,
    limit: int = 5,
) -> ToolResult:
    """Find relevant tools by natural language description."""
    try:
        tu = _get_tu()

        # Use Tool_Finder (basic keyword search, no embedding needed)
        result = tu.run(
            {
                "name": "Tool_Finder",
                "arguments": {
                    "description": description,
                    "limit": limit,
                },
            }
        )

        if isinstance(result, dict) and result.get("status") == "error":
            # Fallback: pattern-based search
            matches = tu.find_tools_by_pattern(description)
            return ToolResult(
                success=True,
                data={
                    "tools": [
                        {
                            "name": t.get("name", ""),
                            "description": str(t.get("description", ""))[:200],
                            "category": t.get("category", ""),
                        }
                        for t in (matches[:limit] if matches else [])
                    ],
                    "source": "pattern_search",
                },
            )

        return ToolResult(success=True, data=result)
    except Exception as exc:
        logger.warning("ToolUniverse find_tools failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _get_tool_spec(
    tool_name: str,
) -> ToolResult:
    """Get the OpenAI-format specification for a tool."""
    try:
        tu = _get_tu()
        spec = tu.tool_specification(tool_name, format="openai")
        return ToolResult(success=True, data=spec)
    except Exception as exc:
        logger.warning("ToolUniverse spec(%s) failed: %s", tool_name, exc)
        return ToolResult(success=False, error=str(exc))


async def _list_categories() -> ToolResult:
    """List all available tool categories."""
    try:
        tu = _get_tu()
        types = tu.get_tool_types()
        return ToolResult(
            success=True,
            data={
                "categories": types,
                "total": len(types),
            },
        )
    except Exception as exc:
        logger.warning("ToolUniverse list_categories failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class ToolUniverseSkill:
    """Real ToolUniverse integration — 2000+ scientific tools."""

    metadata: SkillMetadata = SkillMetadata(
        name="tooluniverse",
        version="0.2.0",
        description=(
            "2000+ scientific tools via ToolUniverse SDK: UniProt, "
            "ChEMBL, PubChem, OpenTargets, ClinicalTrials, and more."
        ),
        capabilities=[
            SkillCapability.INSTRUMENT_KNOWLEDGE,
            SkillCapability.DATA_ANALYSIS,
            SkillCapability.LITERATURE_SEARCH,
        ],
        author="labclaw-core",
        requires_api_key=False,
    )

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for ToolUniverse access."""
        return [
            AgentTool(
                name="tu_run",
                description=(
                    "Execute any ToolUniverse tool by name. "
                    "2000+ tools: UniProt, ChEMBL, PubChem, "
                    "OpenTargets, FAERS, ClinicalTrials, etc."
                ),
                fn=_run_tool,
                parameters_schema={
                    "name": {
                        "type": "string",
                        "description": "Tool name (e.g. UniProt_get_entry_by_accession)",
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Tool arguments as key-value pairs",
                    },
                },
            ),
            AgentTool(
                name="tu_find_tools",
                description=(
                    "Find relevant scientific tools by description. "
                    "Searches 2000+ tools by keyword matching."
                ),
                fn=_find_tools,
                parameters_schema={
                    "description": {
                        "type": "string",
                        "description": "What you need the tool to do",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 5)",
                    },
                },
            ),
            AgentTool(
                name="tu_get_spec",
                description=(
                    "Get the parameter specification for a tool. "
                    "Returns OpenAI function-calling format schema."
                ),
                fn=_get_tool_spec,
                parameters_schema={
                    "tool_name": {
                        "type": "string",
                        "description": "Tool name",
                    },
                },
            ),
            AgentTool(
                name="tu_list_categories",
                description="List all ToolUniverse tool categories.",
                fn=_list_categories,
                parameters_schema={},
            ),
        ]

    async def health_check(self) -> bool:
        """Check if ToolUniverse SDK loads successfully."""
        try:
            tu = _get_tu()
            tools = tu.return_all_loaded_tools()
            return len(tools) > 0
        except Exception:
            return False

    def configure(self, **kwargs: Any) -> None:
        """Reset the ToolUniverse singleton."""
        global _tu_instance  # noqa: PLW0603
        if kwargs.get("reset"):
            _tu_instance = None


assert isinstance(ToolUniverseSkill(), CloudSkill)
