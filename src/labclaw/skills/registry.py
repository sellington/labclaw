"""Skill registry — discovers, loads, and manages cloud skills.

Skills can be registered:
1. Programmatically via register()
2. Via Python entry points (group='labclaw.skills')
3. Via local directory discovery
"""

from __future__ import annotations

import importlib.metadata
import logging
import os
from typing import Any

from labclaw.core.events import event_registry
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Register skill events
# ---------------------------------------------------------------------------

_SKILL_EVENTS = [
    "infra.skills.registered",
    "infra.skills.unregistered",
    "infra.skills.health_check",
    "infra.skills.error",
]

for _evt in _SKILL_EVENTS:
    if not event_registry.is_registered(_evt):
        event_registry.register(_evt)


class SkillRegistry:
    """Central registry for cloud brain skills."""

    def __init__(self) -> None:
        self._skills: dict[str, CloudSkill] = {}

    def register(self, skill: CloudSkill) -> None:
        """Register a skill. Raises ValueError if name already registered."""
        name = skill.metadata.name
        if name in self._skills:
            raise ValueError(f"Skill {name!r} already registered")

        self._skills[name] = skill
        logger.info(
            "Registered skill %s v%s (capabilities=%s)",
            name,
            skill.metadata.version,
            [c.value for c in skill.metadata.capabilities],
        )
        event_registry.emit(
            "infra.skills.registered",
            {"name": name, "version": skill.metadata.version},
        )

    def unregister(self, name: str) -> None:
        """Remove a skill. Raises KeyError if not found."""
        if name not in self._skills:
            raise KeyError(f"Skill {name!r} not found")
        del self._skills[name]
        logger.info("Unregistered skill %s", name)
        event_registry.emit("infra.skills.unregistered", {"name": name})

    def get(self, name: str) -> CloudSkill:
        """Get a skill by name. Raises KeyError if not found."""
        if name not in self._skills:
            raise KeyError(f"Skill {name!r} not found")
        return self._skills[name]

    def get_by_capability(self, capability: SkillCapability) -> list[CloudSkill]:
        """Get all skills with a given capability."""
        return [s for s in self._skills.values() if capability in s.metadata.capabilities]

    def list_skills(self) -> list[SkillMetadata]:
        """Return metadata for all registered skills."""
        return [s.metadata for s in self._skills.values()]

    def get_all_tools(self) -> list[Any]:
        """Collect AgentTool instances from all registered skills."""
        tools: list[Any] = []
        for skill in self._skills.values():
            try:
                tools.extend(skill.get_tools())
            except Exception as exc:
                logger.warning("Failed to get tools from skill %s: %s", skill.metadata.name, exc)
                event_registry.emit(
                    "infra.skills.error",
                    {"name": skill.metadata.name, "error": str(exc)},
                )
        return tools

    async def health_check_all(self) -> dict[str, bool]:
        """Run health checks on all skills. Returns {name: healthy}."""
        results: dict[str, bool] = {}
        for name, skill in self._skills.items():
            try:
                healthy = await skill.health_check()
                results[name] = healthy
            except Exception:
                results[name] = False
                logger.warning("Health check failed for skill %s", name)
            event_registry.emit(
                "infra.skills.health_check",
                {"name": name, "healthy": results[name]},
            )
        return results

    def discover_entry_points(self) -> list[str]:
        """Find skills via Python entry_points (group='labclaw.skills')."""
        if not os.environ.get("LABCLAW_ENABLE_SKILL_PLUGINS", ""):
            return []

        found: list[str] = []
        for ep in importlib.metadata.entry_points(group="labclaw.skills"):
            try:
                skill_cls = ep.load()
                skill = skill_cls()
                self.register(skill)
                found.append(ep.name)
            except Exception as exc:
                logger.warning("Failed to load skill %s: %s", ep.name, exc)
                event_registry.emit(
                    "infra.skills.error",
                    {"name": ep.name, "error": str(exc)},
                )
        return found

    @property
    def count(self) -> int:
        """Number of registered skills."""
        return len(self._skills)


# Global singleton
skill_registry = SkillRegistry()
