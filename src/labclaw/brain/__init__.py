"""MakerClaw / LabClaw Cloud Brain — unified gateway for makerspace & lab tools."""

from __future__ import annotations

import logging
import os
from typing import Any

from labclaw.brain.skills.registry import SkillRegistry
from labclaw.brain.types import BrainResult, HealthStatus, ToolInfo

logger = logging.getLogger(__name__)

_registry: SkillRegistry | None = None


def _get_registry() -> SkillRegistry:
    """Get or create the global registry with default skills."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _register_defaults(_registry)
    return _registry


def _register_defaults(registry: SkillRegistry) -> None:
    """Register built-in makerspace and scientific skills. Gracefully skip unavailable ones."""
    llm_provider = _create_llm_provider()

    # Makerspace Inventory skill (SQLite)
    try:
        from labclaw.brain.skills.inventory import InventorySkill

        db_path = os.environ.get("LABCLAW_INVENTORY_DB", ":memory:")
        registry.register(InventorySkill(db_path=db_path))
    except Exception:
        logger.warning("Failed to register InventorySkill", exc_info=True)

    # Makerspace Devices skill (3D printers, CNC routers, safety checker, feeds & speeds)
    try:
        from labclaw.brain.skills.devices import DevicesSkill

        registry.register(DevicesSkill())
    except Exception:
        logger.warning("Failed to register DevicesSkill", exc_info=True)

    # CAD / EDA / CAM MCP Endpoint skill (Fusion 360, KiCad, pcb2gcode)
    try:
        from labclaw.brain.skills.cad_mcp import CadMcpSkill

        registry.register(CadMcpSkill())
    except Exception:
        logger.warning("Failed to register CadMcpSkill", exc_info=True)

    # Makerspace Docs & SOPs skill
    try:
        from labclaw.brain.skills.docs import DocsSkill

        docs_dir = os.environ.get("LABCLAW_DOCS_DIR")
        registry.register(DocsSkill(docs_dir=docs_dir, llm_provider=llm_provider))
    except Exception:
        logger.warning("Failed to register DocsSkill", exc_info=True)

    # ToolUniverse (optional dep)
    try:
        from labclaw.brain.skills.tooluniverse import ToolUniverseSkill

        registry.register(ToolUniverseSkill())
    except ImportError:
        logger.info("ToolUniverse not installed, skipping")
    except Exception:
        logger.warning("Failed to register ToolUniverse", exc_info=True)

    # LifeSci (needs LLM provider)
    try:
        from labclaw.brain.skills.lifesci import LifeSciSkill

        registry.register(LifeSciSkill(llm_provider=llm_provider))
    except Exception:
        logger.warning("Failed to register LifeSci", exc_info=True)

    # Write (needs LLM provider)
    try:
        from labclaw.brain.skills.write import WriteSkill

        registry.register(WriteSkill(llm_provider=llm_provider))
    except Exception:
        logger.warning("Failed to register Write", exc_info=True)


def _create_llm_provider() -> Any | None:
    """Create LLM provider from environment variables.

    Priority: Fireworks AI (FIREWORKS_API_KEY) > OpenAI (OPENAI_API_KEY)
    """
    fireworks_key = os.environ.get("FIREWORKS_API_KEY")
    if fireworks_key:
        try:
            from labclaw.llm.providers.openai_provider import FireworksProvider

            logger.info("Using Fireworks AI provider (Kimi 2.5)")
            return FireworksProvider()
        except Exception as exc:
            logger.warning("Failed to create Fireworks provider: %s", exc)

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            from labclaw.llm.providers.openai_provider import OpenAIProvider

            logger.info("Using OpenAI provider")
            return OpenAIProvider()
        except Exception as exc:
            logger.warning("Failed to create OpenAI provider: %s", exc)

    logger.info("No LLM provider configured (set FIREWORKS_API_KEY or OPENAI_API_KEY)")
    return None


async def execute(tool_name: str, **kwargs: Any) -> BrainResult:
    """Execute a registered makerspace or lab tool by name."""
    return await _get_registry().execute(tool_name, **kwargs)


async def list_tools(category: str = "") -> list[ToolInfo]:
    """List all available tools, optionally filtered by category."""
    return await _get_registry().list_all_tools(category=category)


async def reason(question: str, *, domain: str = "general", context: str = "") -> BrainResult:
    """Domain reasoning via LLM."""
    return await _get_registry().execute(
        "reason", question=question, domain=domain, context=context
    )


async def write(*, section: str, context: str) -> BrainResult:
    """Generate a writing section via LLM."""
    return await _get_registry().execute("write_section", section=section, context=context)


async def health() -> HealthStatus:
    """Check Cloud Brain health status."""
    import labclaw

    reg = _get_registry()
    skill_health = await reg.health()
    all_tools = await reg.list_all_tools()
    status = "ok" if all(skill_health.values()) else "degraded"
    if not skill_health:
        status = "degraded"
    return HealthStatus(
        status=status,
        skills=skill_health,
        tool_count=len(all_tools),
        version=getattr(labclaw, "__version__", "0.0.1"),
    )
