"""Cloud brain skills API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from labclaw.skills.base import SkillMetadata

router = APIRouter()


class SkillHealthResponse(BaseModel):
    """Health check result for a single skill."""

    name: str
    healthy: bool


class SkillExecuteRequest(BaseModel):
    """Request to execute a skill tool."""

    tool_name: str
    arguments: dict[str, Any] = {}


class SkillExecuteResponse(BaseModel):
    """Response from skill tool execution."""

    success: bool
    data: Any = None
    error: str = ""


@router.get("/")
def list_skills() -> list[SkillMetadata]:
    """List all registered cloud skills."""
    from labclaw.skills.registry import skill_registry

    return skill_registry.list_skills()


@router.get("/by-capability/{capability}")
def list_skills_by_capability(capability: str) -> list[SkillMetadata]:
    """List skills filtered by capability."""
    from labclaw.skills.base import SkillCapability
    from labclaw.skills.registry import skill_registry

    try:
        cap = SkillCapability(capability)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown capability: {capability!r}. "
            f"Valid: {[c.value for c in SkillCapability]}",
        ) from None

    skills = skill_registry.get_by_capability(cap)
    return [s.metadata for s in skills]


@router.get("/tools")
def list_skill_tools() -> list[dict[str, Any]]:
    """List all tools provided by registered skills."""
    from labclaw.skills.registry import skill_registry

    tools = skill_registry.get_all_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters_schema,
        }
        for t in tools
    ]


@router.post("/execute")
async def execute_skill_tool(request: SkillExecuteRequest) -> SkillExecuteResponse:
    """Execute a specific skill tool by name."""
    from labclaw.skills.registry import skill_registry

    tools = skill_registry.get_all_tools()
    tool_map = {t.name: t for t in tools}

    if request.tool_name not in tool_map:
        raise HTTPException(
            status_code=404,
            detail=f"Tool {request.tool_name!r} not found. Available: {list(tool_map.keys())}",
        )

    tool = tool_map[request.tool_name]
    result = await tool.execute(**request.arguments)
    return SkillExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
    )
