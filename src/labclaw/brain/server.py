"""MakerClaw / LabClaw Cloud Brain REST API & Web Dashboard."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

import labclaw.brain as brain

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MAX_REQUEST_BODY = 1 * 1024 * 1024  # 1 MB
_MAX_RESPONSE_SIZE = 100 * 1024  # 100 KB
_RATE_LIMIT = os.environ.get("LABCLAW_RATE_LIMIT", "60/minute")

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = {}


class ReasonRequest(BaseModel):
    question: str
    domain: str = "general"
    context: str = ""


class WriteRequest(BaseModel):
    section: str
    context: str


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_api_keys: set[str] | None = None


def _load_api_keys() -> set[str] | None:
    """Load API keys from LABCLAW_API_KEYS env var (comma-separated)."""
    global _api_keys
    if _api_keys is not None:
        return _api_keys if _api_keys else None
    raw = os.environ.get("LABCLAW_API_KEYS", "")
    if raw.strip():
        _api_keys = {k.strip() for k in raw.split(",") if k.strip()}
    else:
        _api_keys = set()
    return _api_keys if _api_keys else None


def _reset_api_keys() -> None:
    """Reset cached API keys (for testing)."""
    global _api_keys
    _api_keys = None


async def verify_api_key(request: Request) -> None:
    """Verify X-API-Key header when keys are configured."""
    keys = _load_api_keys()
    if keys is None:
        return  # No keys configured — allow anonymous
    provided = request.headers.get("X-API-Key", "")
    if provided not in keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MakerClaw Cloud Brain",
    description=(
        "Unified Makerspace Gateway — Inventory, Docs, 3D Printers, CNCs & CAD/EDA MCP Endpoints"
    ),
    version="0.2.0",
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )


# ---------------------------------------------------------------------------
# Middleware: request body size limit
# ---------------------------------------------------------------------------


@app.middleware("http")
async def _limit_request_body(request: Request, call_next: Any) -> Response:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_REQUEST_BODY:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Response truncation helper
# ---------------------------------------------------------------------------


def _truncate_response(data: Any) -> dict[str, Any] | list[Any]:
    """Truncate response data if serialized size exceeds limit."""
    serialized = json.dumps(data, default=str)
    if len(serialized.encode()) > _MAX_RESPONSE_SIZE:
        return {
            "truncated": True,
            "message": f"Response truncated (>{_MAX_RESPONSE_SIZE} bytes)",
            "data": serialized[:_MAX_RESPONSE_SIZE].rstrip(),
        }
    return data  # type: ignore[no-any-return]


_DASHBOARD_HTML = (
    "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>"
    "<title>MakerClaw — Makerspace Brain & MCP Gateway</title>"
    "<style>"
    "body{background:#0d1117;color:#e6edf3;font-family:monospace;margin:0;padding:24px;}"
    "h1{color:#58a6ff;margin-top:0;}"
    ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;}"
    ".card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;}"
    ".card h2{font-size:15px;color:#79c0ff;margin:0 0 10px 0;border-bottom:1px solid #21262d;}"
    "pre{background:#010409;padding:10px;border-radius:6px;overflow:auto;max-height:280px;}"
    ".badge{display:inline-block;padding:2px 8px;border-radius:12px;background:#238636;color:#fff;}"
    "</style></head><body>"
    "<h1>MakerClaw Control Plane <span class='badge'>MCP + REST</span></h1>"
    "<p>Unified Makerspace Gateway: Inventory, SOP Docs, 3D Printers, CNCs &amp; CAD MCP.</p>"
    "<div class='grid'>"
    "<div class='card'><h2>System Health</h2><pre id='health'>Loading...</pre></div>"
    "<div class='card'><h2>Devices (Printers / CNC)</h2><pre id='devices'>Loading...</pre></div>"
    "<div class='card'><h2>CAD / EDA / CAM MCP</h2><pre id='cad'>Loading...</pre></div>"
    "<div class='card'><h2>Shop Inventory</h2><pre id='inventory'>Loading...</pre></div>"
    "<div class='card'><h2>Shop SOPs &amp; Docs</h2><pre id='docs'>Loading...</pre></div>"
    "<div class='card'><h2>Brain Tools</h2><pre id='tools'>Loading...</pre></div>"
    "</div><script>"
    "async function load(id,u){const r=await fetch(u);"
    "document.getElementById(id).textContent=JSON.stringify(await r.json(),null,2);}"
    "load('health','/brain/health');load('devices','/brain/devices');"
    "load('cad','/brain/cad');load('inventory','/brain/inventory');"
    "load('docs','/brain/docs');load('tools','/brain/tools');"
    "</script></body></html>"
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def get_dashboard() -> HTMLResponse:
    """Serve the MakerClaw web control plane dashboard."""
    return HTMLResponse(content=_DASHBOARD_HTML)


@app.get("/brain/health")
@limiter.limit(_RATE_LIMIT)
async def get_health(request: Request) -> dict[str, Any]:
    """Check Cloud Brain health."""
    status = await brain.health()
    return status.model_dump()


@app.get("/brain/tools")
@limiter.limit(_RATE_LIMIT)
async def get_tools(request: Request, category: str = "") -> dict[str, Any] | list[Any]:
    """List available tools, optionally filtered by category."""
    tools = await brain.list_tools(category=category)
    result: list[Any] = [t.model_dump() for t in tools]
    return _truncate_response(result)


@app.get("/brain/inventory")
@limiter.limit(_RATE_LIMIT)
async def get_inventory(
    request: Request, category: str = "", query: str = "", low_stock: bool = False
) -> dict[str, Any] | list[Any]:
    """Query makerspace inventory items."""
    if query:
        res = await brain.execute("inventory_search", query=query)
    else:
        res = await brain.execute("inventory_list", category=category, low_stock_only=low_stock)
    return _truncate_response(res.model_dump())


@app.get("/brain/devices")
@limiter.limit(_RATE_LIMIT)
async def get_devices(request: Request, device_type: str = "") -> dict[str, Any] | list[Any]:
    """List registered makerspace 3D printers, CNC machines, and bench devices."""
    res = await brain.execute("device_list", device_type=device_type)
    return _truncate_response(res.model_dump())


@app.get("/brain/cad")
@limiter.limit(_RATE_LIMIT)
async def get_cad_endpoints(request: Request, domain: str = "") -> dict[str, Any] | list[Any]:
    """List registered CAD, EDA, and CAM MCP endpoints."""
    res = await brain.execute("cad_endpoints", domain=domain)
    return _truncate_response(res.model_dump())


@app.get("/brain/docs")
@limiter.limit(_RATE_LIMIT)
async def get_docs(
    request: Request, query: str = "", category: str = ""
) -> dict[str, Any] | list[Any]:
    """List or search makerspace SOPs and documentation."""
    if query:
        res = await brain.execute("docs_search", query=query)
    else:
        res = await brain.execute("docs_list", category=category)
    return _truncate_response(res.model_dump())


@app.post("/brain/execute", dependencies=[Depends(verify_api_key)])
@limiter.limit(_RATE_LIMIT)
async def post_execute(request: Request, body: ExecuteRequest) -> dict[str, Any] | list[Any]:
    """Execute a tool by name."""
    result = await brain.execute(body.tool_name, **body.arguments)
    return _truncate_response(result.model_dump())


@app.post("/brain/reason", dependencies=[Depends(verify_api_key)])
@limiter.limit(_RATE_LIMIT)
async def post_reason(request: Request, body: ReasonRequest) -> dict[str, Any] | list[Any]:
    """Domain reasoning."""
    result = await brain.reason(body.question, domain=body.domain, context=body.context)
    return _truncate_response(result.model_dump())


@app.post("/brain/write", dependencies=[Depends(verify_api_key)])
@limiter.limit(_RATE_LIMIT)
async def post_write(request: Request, body: WriteRequest) -> dict[str, Any] | list[Any]:
    """Generate a writing section."""
    result = await brain.write(section=body.section, context=body.context)
    return _truncate_response(result.model_dump())
