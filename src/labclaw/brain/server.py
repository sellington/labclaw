"""MakerClaw Cloud Brain REST API, Interactive Operator Console & Setup Wizard."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
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
    arguments: dict[str, Any] = Field(default_factory=dict)


class ReasonRequest(BaseModel):
    question: str
    domain: str = "general"
    context: str = ""


class WriteRequest(BaseModel):
    section: str
    context: str


class ShopProfileRequest(BaseModel):
    shop_name: str = "MakerClaw Workshop"
    inventory: list[dict[str, Any]] = Field(default_factory=list)
    devices: list[dict[str, Any]] = Field(default_factory=list)
    cad_endpoints: list[dict[str, Any]] = Field(default_factory=list)
    docs: list[dict[str, Any]] = Field(default_factory=list)


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
    version="0.3.0",
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
    "<title>MakerClaw — Makerspace Operator Console & MCP Gateway</title>"
    "<style>"
    "body{background:#0d1117;color:#e6edf3;font-family:monospace;margin:0;padding:20px;}"
    "h1{color:#58a6ff;margin:0 0 8px 0;} a{color:#58a6ff;}"
    ".top{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:16px;"
    "background:#161b22;padding:12px;border:1px solid #30363d;border-radius:8px;}"
    ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px;}"
    ".card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;}"
    ".card h2{font-size:15px;color:#79c0ff;margin:0 0 10px 0;border-bottom:1px solid #21262d;"
    "padding-bottom:6px;}"
    "pre{background:#010409;padding:10px;border-radius:6px;overflow:auto;max-height:240px;"
    "font-size:12px;}"
    "textarea,input,select{background:#010409;color:#e6edf3;border:1px solid #30363d;"
    "padding:6px;border-radius:4px;font-family:monospace;}"
    "button{background:#238636;color:#fff;border:0;padding:6px 12px;border-radius:6px;"
    "cursor:pointer;margin-right:6px;margin-top:6px;font-family:monospace;}"
    "button.sec{background:#1f6feb;} button.warn{background:#da3633;}"
    ".badge{display:inline-block;padding:2px 8px;border-radius:12px;background:#238636;"
    "color:#fff;font-size:13px;}"
    ".svgbox{background:#010409;border:1px solid #30363d;border-radius:6px;padding:10px;"
    "margin-top:8px;text-align:center;}"
    "</style></head><body>"
    "<h1>MakerClaw Control Plane <span class='badge'>v0.3.0</span></h1>"
    "<div class='top'>"
    "<span>API Key:</span>"
    "<input id='ak' type='password' placeholder='Paste X-API-Key token' style='width:260px'"
    " onchange='localStorage.setItem(\"mc_key\",this.value)'/>"
    "<a href='/showcase'><strong>[NEW: 3-Design UX Showcase]</strong></a>"
    "<a href='/setup'>[First-Run Setup Wizard]</a>"
    "<a href='/docs'>[OpenAPI / Swagger UI]</a>"
    "<span id='hbadge'></span>"
    "</div>"
    "<div class='grid'>"
    "<div class='card'><h2>1. CNC / 3D Printer G-Code Safety &amp; 2D SVG Visualizer</h2>"
    "<textarea id='gc' rows='5' style='width:96%'>G21\nG90\nM3 S20000\n"
    "G0 X10 Y10 Z2.0\nG1 Z-0.06 F45\nG1 X60 Y10 F200\nG1 X60 Y45 F200\n"
    "G1 X10 Y45 F200\nG1 X10 Y10 F200\nM5</textarea><br/>"
    "<button onclick='runGcode()'>Validate &amp; Render 2D SVG</button>"
    "<button class='warn' onclick='loadBadGcode()'>Load Unsafe G-Code Test</button>"
    "<button class='sec' onclick='runHeightmap()'>G38.2 Heightmap Warp</button>"
    "<div id='svgout' class='svgbox'>Click Validate &amp; Render 2D SVG</div>"
    "<pre id='gcout'>Ready.</pre></div>"
    "<div class='card'><h2>2. Inventory, ArUco Labels &amp; 3D Printable Bin STL</h2>"
    "<input id='sku' value='MCU-XIAO-ESP32C6' style='width:180px'/>"
    "<button onclick='renderLabel()'>Render ArUco Label SVG</button>"
    "<button class='sec' onclick='recBin()'>Size Gridfinity Bin</button>"
    "<button onclick='dlStl(\"tile\")'>Download ArUco Tile .STL</button>"
    "<button class='sec' onclick='dlStl(\"bin\")'>Download Bin .STL</button>"
    "<button class='sec' onclick='checkBom()'>Run BOM Check</button>"
    "<div id='lblout' class='svgbox'>Loading ArUco Label SVG...</div>"
    "<pre id='inv'>Loading...</pre></div>"
    "<div class='card'><h2>3. Bench Vision, uArm Servoing &amp; MCP Router</h2>"
    "<input id='mcpq' value='kicad pcb autoroute motor' style='width:220px'/>"
    "<button onclick='routeMcp()'>Route MCP Tools</button>"
    "<button onclick='scanBench()'>Scan Bench (ArUco Map)</button>"
    "<button class='sec' onclick='uarmPick()'>uArm Pick &amp; Place</button>"
    "<button class='sec' onclick='probeDev(\"sim-moonraker\")'>Probe Sim Printer</button>"
    "<div id='visout' class='svgbox'>Click Scan Bench (ArUco Map)</div>"
    "<pre id='mcpout'>Enter a task or scan bench.</pre>"
    "<pre id='devs'>Loading...</pre></div>"
    "<div class='card'><h2>4. CAD / EDA MCP Endpoints &amp; Shop SOPs</h2>"
    "<button onclick='pingCad()'>Ping Sim Fusion360 TCP</button>"
    "<button class='sec' onclick='askAdvisor()'>Ask Shop SOP Advisor</button>"
    "<pre id='cad'>Loading...</pre><pre id='docs'>Loading...</pre></div>"
    "</div><script>"
    "const qp=new URLSearchParams(location.search).get('token');"
    "if(qp)localStorage.setItem('mc_key',qp);"
    "const kEl=document.getElementById('ak');"
    "kEl.value=localStorage.getItem('mc_key')||'';"
    "async function ex(t,a){const h={'Content-Type':'application/json'};"
    "if(kEl.value)h['X-API-Key']=kEl.value;"
    "const r=await fetch('/brain/execute',{method:'POST',headers:h,"
    "body:JSON.stringify({tool_name:t,arguments:a})});return await r.json();}"
    "async function dlStl(kind){const s=document.getElementById('sku').value;"
    "const r=await ex('cad_generate_aruco_bin_stl',{sku:s,grid_x:1,grid_y:2,height_u:3});"
    "if(!r.data)return;const txt=kind==='tile'?r.data.tile_stl:r.data.bin_stl;"
    "const b=new Blob([txt],{type:'model/stl'});const a=document.createElement('a');"
    "a.href=URL.createObjectURL(b);a.download=`${s}_${kind}.stl`;a.click();"
    "document.getElementById('inv').textContent=JSON.stringify("
    "{sku:r.data.sku,aruco_id:r.data.aruco_id,bin_code:r.data.bin_code,"
    "tile_facets:r.data.tile_facet_count,bin_facets:r.data.bin_facet_count},null,2);}"
    "async function runGcode(){const g=document.getElementById('gc').value;"
    "const v=await ex('device_validate_gcode',{device_id:'cubiko-cnc',gcode:g});"
    "const s=await ex('device_render_gcode_svg',{device_id:'cubiko-cnc',gcode:g});"
    "document.getElementById('gcout').textContent=JSON.stringify(v,null,2);"
    "if(s.data&&s.data.svg)document.getElementById('svgout').innerHTML=s.data.svg;}"
    "function loadBadGcode(){document.getElementById('gc').value="
    "'T1 M6\\nM0\\nM3 S25000\\nG0 X220 Y150 Z50\\nG1 Z-9.5 F200';runGcode();}"
    "async function runHeightmap(){const g=document.getElementById('gc').value;"
    "const r=await ex('device_probe_heightmap',{width_x_mm:40,height_y_mm:30,"
    "grid_x:3,grid_y:3,z_offsets:[-0.03,-0.05],gcode:g});"
    "document.getElementById('gcout').textContent=JSON.stringify(r,null,2);}"
    "async function renderLabel(){const s=document.getElementById('sku').value;"
    "const r=await ex('inventory_bin_label_svg',{sku:s});"
    "if(r.data&&r.data.svg)document.getElementById('lblout').innerHTML=r.data.svg;"
    "else document.getElementById('lblout').textContent=JSON.stringify(r);}"
    "async function recBin(){const s=document.getElementById('sku').value;"
    "const r=await ex('inventory_recommend_bin',{sku:s,max_qty:25});"
    "document.getElementById('inv').textContent=JSON.stringify(r,null,2);}"
    "async function scanBench(){const r=await ex('vision_scan_bench',{});"
    "document.getElementById('mcpout').textContent=JSON.stringify(r,null,2);"
    "if(r.data&&r.data.svg)document.getElementById('visout').innerHTML=r.data.svg;}"
    "async function uarmPick(){const r=await ex('vision_uarm_pick_and_place',"
    "{pick_u:420,pick_v:460,place_u:820,place_v:340});"
    "document.getElementById('mcpout').textContent=JSON.stringify(r,null,2);}"
    "async function checkBom(){const r=await ex('inventory_check_bom',{items:["
    "{sku:'MCU-XIAO-ESP32C6',quantity:1},{sku:'MAG-NEO-6X2',quantity:4},"
    "{item:'TMC2209 Driver',quantity:2,estimated_cost_usd:4.5}]});"
    "document.getElementById('inv').textContent=JSON.stringify(r,null,2);}"
    "async function routeMcp(){const q=document.getElementById('mcpq').value;"
    "const r=await ex('cad_federate_tools',{task_query:q,max_tools:3});"
    "document.getElementById('mcpout').textContent=JSON.stringify(r,null,2);}"
    "async function probeDev(d){const r=await ex('device_status',"
    "{device_id:d,probe_network:true});"
    "document.getElementById('mcpout').textContent=JSON.stringify(r,null,2);}"
    "async function pingCad(){const r=await ex('cad_bridge_call',"
    "{endpoint_id:'sim-fusion360',command:'ping'});"
    "document.getElementById('cad').textContent=JSON.stringify(r,null,2);}"
    "async function askAdvisor(){const r=await ex('maker_reason',"
    "{question:'How do I probe the Cubiko spoilboard and mill FR-4?'});"
    "document.getElementById('docs').textContent=JSON.stringify(r,null,2);}"
    "async function load(id,u){const r=await fetch(u);const j=await r.json();"
    "document.getElementById(id).textContent=JSON.stringify(j,null,2);}"
    "fetch('/brain/health').then(r=>r.json()).then(h=>{"
    "document.getElementById('hbadge').textContent="
    "`Status: ${h.status.toUpperCase()} | ${h.tool_count} Tools`;});"
    "load('devs','/brain/devices');load('cad','/brain/cad');"
    "load('inv','/brain/inventory');load('docs','/brain/docs');"
    "if(kEl.value){runGcode();renderLabel();scanBench();}"
    "</script></body></html>"
)

_SETUP_HTML = (
    "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>"
    "<title>MakerClaw — First-Run Setup Wizard</title>"
    "<style>"
    "body{background:#0d1117;color:#e6edf3;font-family:monospace;margin:0;padding:24px;}"
    ".box{max-width:720px;background:#161b22;border:1px solid #30363d;padding:16px;}"
    "input,textarea{background:#010409;color:#e6edf3;border:1px solid #30363d;width:96%;}"
    "button{background:#238636;color:#fff;border:0;padding:8px 16px;border-radius:6px;}"
    "</style></head><body>"
    "<div class='box'><h1>MakerClaw Setup Wizard</h1>"
    "<p>Configure your makerspace machines, CAD MCP endpoints, and starter inventory.</p>"
    "<label>Shop Name</label><input id='shop_name' value='My Makerspace'/>"
    "<label>API Key (if configured)</label><input id='api_key' placeholder='Optional X-API-Key'/>"
    "<label>Profile JSON (devices, cad_endpoints, inventory)</label>"
    "<textarea id='payload' rows='10'>"
    '{"shop_name": "My Makerspace", "devices": [], "cad_endpoints": []}</textarea>'
    "<button onclick='saveProfile()'>Save &amp; Apply Profile</button>"
    "<pre id='out'></pre><p><a href='/' style='color:#58a6ff;'>Back to Control Plane</a></p></div>"
    "<script>"
    "async function saveProfile(){"
    "const k=document.getElementById('api_key').value;"
    "const h={'Content-Type':'application/json'}; if(k) h['X-API-Key']=k;"
    "const b=document.getElementById('payload').value;"
    "const r=await fetch('/brain/profile',{method:'POST',headers:h,body:b});"
    "document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2);}"
    "</script></body></html>"
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def get_dashboard() -> HTMLResponse:
    """Serve the MakerClaw web control plane dashboard."""
    from labclaw.brain.showcase import SHOWCASE_HTML

    return HTMLResponse(content=SHOWCASE_HTML)


@app.get("/showcase", response_class=HTMLResponse)
async def get_showcase() -> HTMLResponse:
    """Serve the interactive 3-design UI/UX architecture showcase."""
    from labclaw.brain.showcase import SHOWCASE_HTML

    return HTMLResponse(content=SHOWCASE_HTML)


@app.get("/setup", response_class=HTMLResponse)
async def get_setup_wizard() -> HTMLResponse:
    """Serve the MakerClaw first-run setup wizard."""
    return HTMLResponse(content=_SETUP_HTML)


@app.post("/brain/profile", dependencies=[Depends(verify_api_key)])
@limiter.limit(_RATE_LIMIT)
async def post_profile(request: Request, body: ShopProfileRequest) -> dict[str, Any]:
    """Apply a Shop Profile (devices, CAD endpoints, inventory, docs) into the live registry."""
    reg = brain._get_registry()
    counts = brain.apply_shop_profile(reg, body.model_dump())
    return {"success": True, "shop_name": body.shop_name, "applied": counts}


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
