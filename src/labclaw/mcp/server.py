"""MakerClaw / LabClaw MCP Server — expose Makerspace & Cloud Brain tools via MCP."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from labclaw.brain import execute, health, list_tools, reason, write

mcp = FastMCP(
    "labclaw",
    instructions=(
        "MakerClaw / LabClaw Cloud Brain — unified gateway for makerspace inventory, "
        "SOP docs, 3D printers, CNC routers, CAD/EDA MCP endpoints, and 2400+ scientific tools"
    ),
)


@mcp.tool()
async def labclaw_search_tools(query: str = "", category: str = "") -> str:
    """Find available makerspace, CAD, CNC, or scientific tools by keyword or category."""
    tools = await list_tools(category=category)
    if query:
        q = query.lower()
        tools = [t for t in tools if q in t.name.lower() or q in t.description.lower()]
    return json.dumps([t.model_dump() for t in tools], indent=2)


@mcp.tool()
async def labclaw_execute_tool(tool_name: str, arguments: str = "{}") -> str:
    """Execute any makerspace or scientific tool by name. Pass arguments as JSON string."""
    args = json.loads(arguments) if isinstance(arguments, str) else arguments
    result = await execute(tool_name, **args)
    return json.dumps(result.model_dump(), indent=2)


@mcp.tool()
async def labclaw_inventory(
    action: str = "list",
    query: str = "",
    category: str = "",
    sku: str = "",
    delta: float | None = None,
    bom_json: str = "",
) -> str:
    """Manage makerspace inventory (list, search, low_stock, update_stock, check_bom)."""
    act = action.strip().lower()
    if act == "search":
        res = await execute("inventory_search", query=query)
    elif act == "low_stock":
        res = await execute("inventory_low_stock")
    elif act == "update_stock":
        res = await execute("inventory_update_stock", sku=sku, delta=delta)
    elif act == "check_bom":
        res = await execute("inventory_check_bom", items=bom_json)
    else:
        res = await execute("inventory_list", category=category)
    return json.dumps(res.model_dump(), indent=2)


@mcp.tool()
async def labclaw_devices(
    action: str = "list",
    device_id: str = "cubiko-cnc",
    material: str = "fr4_isolation",
    spindle_rpm: int = 10000,
    gcode: str = "",
    command: str = "",
) -> str:
    """Control & inspect makerspace 3D printers and CNC machines."""
    act = action.strip().lower()
    if act == "status":
        res = await execute("device_status", device_id=device_id)
    elif act == "feeds":
        res = await execute("device_feeds_and_speeds", material=material, spindle_rpm=spindle_rpm)
    elif act == "validate_gcode":
        res = await execute("device_validate_gcode", gcode=gcode, device_id=device_id)
    elif act == "command":
        res = await execute("device_send_command", device_id=device_id, action=command)
    else:
        res = await execute("device_list")
    return json.dumps(res.model_dump(), indent=2)


@mcp.tool()
async def labclaw_cad(
    action: str = "endpoints",
    domain: str = "",
    pcb_width_mm: float = 35.4,
    pcb_height_mm: float = 33.5,
    expected_volume_delta_cm3: float = 0.0,
    actual_mass_before_g: float | None = None,
    actual_mass_after_g: float | None = None,
) -> str:
    """CAD/EDA/CAM MCP endpoints and calculators (endpoints, enclosure, verify_mass, pcb2gcode)."""
    act = action.strip().lower()
    if act == "enclosure":
        res = await execute(
            "cad_enclosure_calculator",
            pcb_width_mm=pcb_width_mm,
            pcb_height_mm=pcb_height_mm,
        )
    elif act == "verify_mass":
        res = await execute(
            "cad_verify_mass_delta",
            expected_volume_delta_cm3=expected_volume_delta_cm3,
            actual_mass_before_g=actual_mass_before_g,
            actual_mass_after_g=actual_mass_after_g,
        )
    elif act == "pcb2gcode":
        res = await execute("cam_pcb2gcode_command", board_width_mm=pcb_width_mm)
    else:
        res = await execute("cad_endpoints", domain=domain)
    return json.dumps(res.model_dump(), indent=2)


@mcp.tool()
async def labclaw_docs(
    action: str = "list",
    query: str = "",
    slug: str = "",
    title: str = "",
    content: str = "",
) -> str:
    """Search, read, or author Makerspace SOPs and machine documentation."""
    act = action.strip().lower()
    if act == "search":
        res = await execute("docs_search", query=query)
    elif act == "get":
        res = await execute("docs_get", slug=slug)
    elif act == "save":
        res = await execute("docs_save", slug=slug, title=title, content=content)
    elif act == "generate_sop":
        res = await execute("docs_generate_sop", title=title or "Makerspace SOP")
    else:
        res = await execute("docs_list")
    return json.dumps(res.model_dump(), indent=2)


@mcp.tool()
async def labclaw_reason(question: str, domain: str = "general") -> str:
    """Ask a makerspace or scientific domain question. Returns expert-level reasoning."""
    result = await reason(question, domain=domain)
    return result.data if result.success else f"Error: {result.error}"


@mcp.tool()
async def labclaw_write(section: str, context: str) -> str:
    """Generate a technical or scientific writing section (abstract, methods, results)."""
    result = await write(section=section, context=context)
    return result.data if result.success else f"Error: {result.error}"


@mcp.tool()
async def labclaw_health() -> str:
    """Check Cloud Brain health and available skills."""
    status = await health()
    return json.dumps(status.model_dump(), indent=2)


def main() -> None:
    """Run MCP server via stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
