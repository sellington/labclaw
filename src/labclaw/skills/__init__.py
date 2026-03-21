"""Cloud Brain skills — pluggable AI capabilities for the scientific loop.

Each skill wraps an external AI service (ToolUniverse, K-Dense, Biomni, etc.)
and exposes it as one or more AgentTools that the agent runtime can invoke.

Spec: docs/specs/cloud-brain-skills.md
"""

from __future__ import annotations

from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata
from labclaw.skills.registry import SkillRegistry, skill_registry

__all__ = [
    "CloudSkill",
    "SkillCapability",
    "SkillMetadata",
    "SkillRegistry",
    "skill_registry",
]
