"""MakerClaw Cloud Brain — unified gateway for makerspace inventory, docs, devices & CAD MCP."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

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
    """Register built-in makerspace skills. Gracefully skip unavailable ones."""
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

    # Top-Down Computer Vision & uArm Visual Servoing skill
    try:
        from labclaw.brain.skills.vision import VisionSkill

        registry.register(VisionSkill())
    except Exception:
        logger.warning("Failed to register VisionSkill", exc_info=True)

    # Write (technical & documentation writing)
    try:
        from labclaw.brain.skills.write import WriteSkill

        registry.register(WriteSkill(llm_provider=llm_provider))
    except Exception:
        logger.warning("Failed to register Write", exc_info=True)

    # Apply optional instance-specific shop profile overlay (LABCLAW_PROFILE)
    profile_path = os.environ.get("LABCLAW_PROFILE", "").strip()
    if profile_path:
        apply_shop_profile(registry, Path(profile_path))


def apply_shop_profile(
    registry: SkillRegistry,
    profile_source: Path | dict[str, Any],
) -> dict[str, int]:
    """Load an external YAML/JSON shop profile or dict into registered skills."""
    counts = {"inventory": 0, "devices": 0, "cad_endpoints": 0, "docs": 0}
    if isinstance(profile_source, Path):
        if not profile_source.exists():
            logger.warning("Shop profile file not found: %s", profile_source)
            return counts
        data = yaml.safe_load(profile_source.read_text(encoding="utf-8")) or {}
    else:
        data = profile_source

    inv_skill: Any = registry._skills.get("inventory")
    if inv_skill is not None and isinstance(data.get("inventory"), list):
        counts["inventory"] = inv_skill._insert_catalog(data["inventory"])

    dev_skill: Any = registry._skills.get("devices")
    if dev_skill is not None and isinstance(data.get("devices"), list):
        for dev in data["devices"]:
            did = str(dev.get("device_id", "")).strip()
            if did:
                dev_skill._devices[did] = dict(dev)
                counts["devices"] += 1

    cad_skill: Any = registry._skills.get("cad_mcp")
    if cad_skill is not None and isinstance(data.get("cad_endpoints"), list):
        for ep in data["cad_endpoints"]:
            eid = str(ep.get("endpoint_id", "")).strip()
            if eid:
                cad_skill._endpoints[eid] = dict(ep)
                counts["cad_endpoints"] += 1

    docs_skill: Any = registry._skills.get("docs")
    if docs_skill is not None and isinstance(data.get("docs"), list):
        for doc in data["docs"]:
            slug = str(doc.get("slug", "")).strip()
            if slug:
                docs_skill._docs[slug] = dict(doc)
                counts["docs"] += 1

    return counts


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
    """Execute a registered makerspace tool by name."""
    return await _get_registry().execute(tool_name, **kwargs)


async def list_tools(category: str = "") -> list[ToolInfo]:
    """List all available tools, optionally filtered by category."""
    return await _get_registry().list_all_tools(category=category)


async def reason(question: str, *, domain: str = "general", context: str = "") -> BrainResult:
    """Makerspace & engineering domain reasoning."""
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
        version=getattr(labclaw, "__version__", "0.3.0"),
    )
