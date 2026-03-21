"""Cloud Brain server — unified API for all scientific AI skills."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from labclaw.skills.base import SkillMetadata
from labclaw.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ExecuteRequest(BaseModel):
    """Payload for POST /brain/execute."""

    tool_name: str
    arguments: dict[str, Any] = {}


class ExecuteResponse(BaseModel):
    """Response from POST /brain/execute."""

    success: bool
    data: Any = None
    error: str = ""


class ToolInfo(BaseModel):
    """Summarised tool descriptor returned by /brain/tools."""

    name: str
    description: str
    parameters: dict[str, Any] = {}


class InventoryCategory(BaseModel):
    """Per-category summary in the inventory."""

    capability: str
    skill_count: int
    tool_count: int
    skills: list[str]


class InventoryResponse(BaseModel):
    """Full inventory with categories and tool counts."""

    total_skills: int
    total_tools: int
    categories: list[InventoryCategory]


# ---------------------------------------------------------------------------
# App-level registry (populated on startup)
# ---------------------------------------------------------------------------

_registry = SkillRegistry()


def _register_builtin_skills() -> None:
    """Import and register all built-in skills."""
    from labclaw.skills.biomni import BiomniSkill
    from labclaw.skills.kdense import KDenseSkill
    from labclaw.skills.lifesci import LifeSciSkill
    from labclaw.skills.tooluniverse import ToolUniverseSkill
    from labclaw.skills.write import WriteSkill

    for cls in (ToolUniverseSkill, BiomniSkill, KDenseSkill, WriteSkill, LifeSciSkill):
        try:
            _registry.register(cls())
        except ValueError:
            pass  # already registered


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _register_builtin_skills()
    logger.info("Cloud Brain started with %d skills", _registry.count)
    yield


app = FastAPI(
    title="Cloud Brain",
    description="Unified API for all scientific AI skills",
    lifespan=_lifespan,
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/brain/skills", response_model=list[SkillMetadata])
async def list_skills() -> list[SkillMetadata]:
    """List all registered skills."""
    return _registry.list_skills()


@app.get("/brain/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """List all tools across all skills."""
    tools = _registry.get_all_tools()
    return [
        ToolInfo(
            name=t.name,
            description=t.description,
            parameters=t.parameters_schema,
        )
        for t in tools
    ]


@app.get("/brain/health")
async def health_check() -> dict[str, bool]:
    """Health check all skills."""
    return await _registry.health_check_all()


@app.post("/brain/execute", response_model=ExecuteResponse)
async def execute_tool(req: ExecuteRequest) -> ExecuteResponse:
    """Execute any tool by name."""
    tools = _registry.get_all_tools()
    tool_map = {t.name: t for t in tools}

    if req.tool_name not in tool_map:
        return ExecuteResponse(
            success=False,
            error=f"Tool {req.tool_name!r} not found",
        )

    tool = tool_map[req.tool_name]
    result = await tool.execute(**req.arguments)
    return ExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
    )


@app.get("/brain/inventory", response_model=InventoryResponse)
async def inventory() -> InventoryResponse:
    """Full inventory with categories and tool counts."""
    skills = _registry.list_skills()
    all_tools = _registry.get_all_tools()

    # Build per-capability map
    cap_map: dict[str, list[str]] = {}
    for s in skills:
        for cap in s.capabilities:
            cap_map.setdefault(cap.value, []).append(s.name)

    # Count tools per skill
    tools_per_skill: dict[str, int] = {}
    for s_meta in skills:
        skill = _registry.get(s_meta.name)
        try:
            tools_per_skill[s_meta.name] = len(skill.get_tools())
        except Exception:
            tools_per_skill[s_meta.name] = 0

    categories: list[InventoryCategory] = []
    for cap in sorted(cap_map):
        skill_names = cap_map[cap]
        tool_count = sum(tools_per_skill.get(n, 0) for n in skill_names)
        categories.append(
            InventoryCategory(
                capability=cap,
                skill_count=len(skill_names),
                tool_count=tool_count,
                skills=sorted(skill_names),
            )
        )

    return InventoryResponse(
        total_skills=len(skills),
        total_tools=len(all_tools),
        categories=categories,
    )
