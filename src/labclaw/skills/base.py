"""CloudSkill protocol — interface for external AI capabilities.

Each CloudSkill:
1. Declares metadata (name, version, capabilities)
2. Returns AgentTool instances for the agent runtime
3. Provides health_check for runtime validation
4. Maps to scientific loop steps via SkillCapability enum
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class SkillCapability(StrEnum):
    """Which scientific loop step(s) a skill can enhance."""

    LITERATURE_SEARCH = "literature_search"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    INSTRUMENT_KNOWLEDGE = "instrument_knowledge"
    DATA_ANALYSIS = "data_analysis"
    SCIENTIFIC_WRITING = "scientific_writing"
    GENERAL_REASONING = "general_reasoning"


class SkillMetadata(BaseModel):
    """Identity and capabilities of a cloud skill."""

    name: str
    version: str
    description: str
    capabilities: list[SkillCapability]
    author: str = ""
    requires_api_key: bool = False
    api_key_env: str = ""


@runtime_checkable
class CloudSkill(Protocol):
    """Protocol for cloud brain skills.

    Each skill provides AgentTool instances and a health check.
    Skills are discovered and loaded by the SkillRegistry.
    """

    metadata: SkillMetadata

    def get_tools(self) -> list[Any]:
        """Return AgentTool instances this skill provides."""
        ...

    async def health_check(self) -> bool:
        """Verify the skill's backend is reachable. Returns True if healthy."""
        ...

    def configure(self, **kwargs: Any) -> None:
        """Apply runtime configuration (API keys, model overrides, etc.)."""
        ...
