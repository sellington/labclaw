"""Biomni skill — real integration with Stanford SNAP Biomni agent.

Uses the biomni Python package (pip install biomni) which provides
an autonomous biomedical AI agent with 150+ specialized tools
covering 59 databases across biology, chemistry, and medicine.

Maps to: ANALYZE step (biomedical data interpretation) and GENERAL_REASONING.
"""

from __future__ import annotations

import logging
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_biomni_agent: Any = None


def _get_agent(
    llm: str = "claude-sonnet-4-20250514",
    data_path: str = "./data",
) -> Any:
    """Get or create the Biomni A1 agent singleton."""
    global _biomni_agent  # noqa: PLW0603
    if _biomni_agent is None:
        from biomni.agent import A1

        _biomni_agent = A1(path=data_path, llm=llm)
        logger.info("Biomni A1 agent initialized with LLM=%s", llm)
    return _biomni_agent


async def _biomni_go(
    query: str,
    *,
    llm: str = "claude-sonnet-4-20250514",
    data_path: str = "./data",
) -> ToolResult:
    """Run a biomedical query through Biomni's autonomous agent."""
    try:
        agent = _get_agent(llm=llm, data_path=data_path)
        result = agent.go(query)

        return ToolResult(
            success=True,
            data={
                "result": str(result)[:5000],
                "query": query,
                "llm": llm,
            },
        )
    except Exception as exc:
        logger.warning("Biomni go() failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _biomni_list_tools() -> ToolResult:
    """List all custom tools registered in Biomni."""
    try:
        agent = _get_agent()
        custom_tools = agent.list_custom_tools()
        return ToolResult(
            success=True,
            data={"tools": custom_tools},
        )
    except Exception as exc:
        logger.warning("Biomni list_tools failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _biomni_add_data(
    name: str,
    *,
    path: str = "",
    description: str = "",
) -> ToolResult:
    """Add custom data to Biomni's data lake."""
    try:
        agent = _get_agent()
        agent.add_data(name=name, path=path, description=description)
        return ToolResult(
            success=True,
            data={"added": name, "path": path},
        )
    except Exception as exc:
        logger.warning("Biomni add_data failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class BiomniSkill:
    """Real Biomni integration — autonomous biomedical AI agent."""

    metadata: SkillMetadata = SkillMetadata(
        name="biomni",
        version="0.2.0",
        description=(
            "Stanford SNAP Biomni: autonomous biomedical AI agent "
            "with 150+ tools across 59 databases."
        ),
        capabilities=[
            SkillCapability.DATA_ANALYSIS,
            SkillCapability.GENERAL_REASONING,
            SkillCapability.HYPOTHESIS_GENERATION,
        ],
        author="labclaw-core",
        requires_api_key=True,
        api_key_env="ANTHROPIC_API_KEY",
    )

    def __init__(
        self,
        llm: str = "claude-sonnet-4-20250514",
        data_path: str = "./data",
    ) -> None:
        self._llm = llm
        self._data_path = data_path

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for Biomni access."""
        from functools import partial

        return [
            AgentTool(
                name="biomni_go",
                description=(
                    "Run a biomedical query through Biomni's "
                    "autonomous AI agent. Handles multi-step "
                    "reasoning across 150+ bio tools and 59 DBs."
                ),
                fn=partial(
                    _biomni_go,
                    llm=self._llm,
                    data_path=self._data_path,
                ),
                parameters_schema={
                    "query": {
                        "type": "string",
                        "description": "Biomedical question or task",
                    },
                },
            ),
            AgentTool(
                name="biomni_list_tools",
                description="List custom tools in Biomni agent.",
                fn=_biomni_list_tools,
                parameters_schema={},
            ),
            AgentTool(
                name="biomni_add_data",
                description=("Add custom data to Biomni's data lake for analysis."),
                fn=_biomni_add_data,
                parameters_schema={
                    "name": {
                        "type": "string",
                        "description": "Dataset name",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path to data",
                    },
                    "description": {
                        "type": "string",
                        "description": "Dataset description",
                    },
                },
            ),
        ]

    async def health_check(self) -> bool:
        """Check if Biomni can be imported."""
        try:
            from biomni.agent import A1  # noqa: F401

            return True
        except ImportError:
            return False

    def configure(self, **kwargs: Any) -> None:
        """Update LLM model or data path."""
        global _biomni_agent  # noqa: PLW0603
        if "llm" in kwargs:
            self._llm = kwargs["llm"]
            _biomni_agent = None
        if "data_path" in kwargs:
            self._data_path = kwargs["data_path"]
            _biomni_agent = None


assert isinstance(BiomniSkill(), CloudSkill)
