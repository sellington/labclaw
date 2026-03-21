"""Cloud Brain server — unified API for all scientific AI skills."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from labclaw.skills.base import SkillMetadata
from labclaw.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RESPONSE_SIZE = 100_000  # 100KB
MAX_REQUEST_SIZE = 1_048_576  # 1MB

# ---------------------------------------------------------------------------
# API Key Authentication
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_valid_keys() -> set[str]:
    """Load valid API keys from env."""
    raw = os.environ.get("LABCLAW_API_KEYS", "")
    if not raw:
        return set()  # No auth if no keys configured
    return {k.strip() for k in raw.split(",") if k.strip()}


async def _verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """Validate API key from header against configured keys."""
    keys = _get_valid_keys()
    if not keys:
        return "anonymous"  # No auth configured = open access
    if not api_key or api_key not in keys:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------


def _rate_limit_key(request: Request) -> str:
    """Key function for rate limiting: use API key if present, else IP."""
    return request.headers.get("X-API-Key", get_remote_address(request))


limiter = Limiter(key_func=_rate_limit_key)


# ---------------------------------------------------------------------------
# Request Size Middleware
# ---------------------------------------------------------------------------


class _RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with Content-Length exceeding MAX_REQUEST_SIZE."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)


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
    dependencies=[Depends(_verify_api_key)],
)

app.state.limiter = limiter
app.add_middleware(_RequestSizeLimitMiddleware)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


_STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui() -> HTMLResponse:
    """Serve the Cloud Brain web UI."""
    html_path = _STATIC_DIR / "brain.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>Cloud Brain</h1><p>UI not found.</p>")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/brain/skills", response_model=list[SkillMetadata])
@limiter.limit("120/minute")
async def list_skills(request: Request) -> list[SkillMetadata]:
    """List all registered skills."""
    return _registry.list_skills()


@app.get("/brain/tools", response_model=list[ToolInfo])
@limiter.limit("120/minute")
async def list_tools(request: Request) -> list[ToolInfo]:
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
@limiter.limit("120/minute")
async def health_check(request: Request) -> dict[str, bool]:
    """Health check all skills."""
    return await _registry.health_check_all()


@app.post("/brain/execute", response_model=ExecuteResponse)
@limiter.limit("60/minute")
async def execute_tool(request: Request, req: ExecuteRequest) -> ExecuteResponse:
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

    # Truncate oversized responses
    result_json = json.dumps(result.data, default=str)
    if len(result_json) > MAX_RESPONSE_SIZE:
        result.data = {
            "truncated": True,
            "size": len(result_json),
            "preview": result_json[:MAX_RESPONSE_SIZE],
        }

    return ExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
    )


@app.get("/brain/inventory", response_model=InventoryResponse)
@limiter.limit("120/minute")
async def inventory(request: Request) -> InventoryResponse:
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
    for cap_name in sorted(cap_map):
        skill_names = cap_map[cap_name]
        tool_count = sum(tools_per_skill.get(n, 0) for n in skill_names)
        categories.append(
            InventoryCategory(
                capability=cap_name,
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
