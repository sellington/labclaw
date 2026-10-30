"""MakerClaw / LabClaw CLI — main entry point."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="makerclaw",
        description=(
            "MakerClaw Cloud Brain — Makerspace Inventory, Docs, "
            "3D Printers, CNCs & CAD MCP Gateway"
        ),
    )
    sub = parser.add_subparsers(dest="command")

    demo_p = sub.add_parser("demo", help="Run a live Makerspace or Cloud Brain demo")
    demo_p.add_argument("--maker", action="store_true", help="Run full makerspace workflow demo")

    brain_p = sub.add_parser("brain", help="Start MakerClaw REST API & Web Dashboard")
    brain_p.add_argument("--host", default="127.0.0.1")
    brain_p.add_argument("--port", type=int, default=18802)

    sub.add_parser("mcp", help="Start MCP server for Claude Desktop / Hermes Agent")

    tools_p = sub.add_parser("tools", help="List available tools")
    tools_p.add_argument("--category", default="")

    inv_p = sub.add_parser("inventory", help="Query makerspace inventory")
    inv_p.add_argument("--category", default="")
    inv_p.add_argument("--search", default="")

    dev_p = sub.add_parser("devices", help="List makerspace 3D printers, CNCs, and CAD endpoints")
    dev_p.add_argument("--type", dest="device_type", default="")

    docs_p = sub.add_parser("docs", help="List or search shop SOPs and documentation")
    docs_p.add_argument("--search", default="")

    args = parser.parse_args()

    if args.command == "demo":
        if getattr(args, "maker", False):
            asyncio.run(_maker_demo())
        else:
            asyncio.run(_demo())
    elif args.command == "brain":
        _start_brain(args.port, args.host)
    elif args.command == "mcp":
        _start_mcp()
    elif args.command == "tools":
        asyncio.run(_list_tools(args.category))
    elif args.command == "inventory":
        asyncio.run(_run_inventory(args.category, args.search))
    elif args.command == "devices":
        asyncio.run(_run_devices(args.device_type))
    elif args.command == "docs":
        asyncio.run(_run_docs(args.search))
    else:
        parser.print_help()
        sys.exit(1)


async def _demo() -> None:
    """Run a demo query."""
    from labclaw.brain import execute

    print("Cloud Brain Demo — searching PubMed for CRISPR...")
    result = await execute("search_pubmed", query="CRISPR")
    print(json.dumps(result.model_dump(), indent=2, default=str))


async def _maker_demo() -> None:
    """Run an end-to-end Makerspace showcase across inventory, CNC, CAD, and SOPs."""
    from labclaw.brain import execute

    print("=== MakerClaw Makerspace Control Plane Demo ===")
    bom = await execute(
        "inventory_check_bom",
        items=[
            {"sku": "MCU-XIAO-ESP32C6", "quantity": 1},
            {"sku": "DISP-OLED-1.3-SH1106", "quantity": 1},
            {"sku": "MAG-NEO-6X2", "quantity": 4},
            {"item": "TMC2209 Stepper Driver", "quantity": 2, "estimated_cost_usd": 4.50},
        ],
    )
    feeds = await execute("device_feeds_and_speeds", material="fr4_isolation", spindle_rpm=20000)
    gcode_check = await execute(
        "device_validate_gcode",
        device_id="cubiko-cnc",
        gcode="G21\nG90\nM3 S20000\nG0 X10 Y10 Z2.0\nG1 Z-0.06 F45\nG1 X50 Y40 F200\nM5",
    )
    enclosure = await execute("cad_enclosure_calculator", pcb_width_mm=35.4, pcb_height_mm=33.5)
    summary = {
        "bom_validation": bom.data,
        "cnc_feeds_and_speeds": feeds.data,
        "gcode_safety_validation": gcode_check.data,
        "oled_enclosure_cad_spec": enclosure.data,
    }
    print(json.dumps(summary, indent=2, default=str))


async def _run_inventory(category: str, search: str) -> None:
    """Run inventory CLI query."""
    from labclaw.brain import execute

    if search:
        res = await execute("inventory_search", query=search)
    else:
        res = await execute("inventory_list", category=category)
    print(json.dumps(res.model_dump(), indent=2, default=str))


async def _run_devices(device_type: str) -> None:
    """Run devices & CAD endpoints CLI query."""
    from labclaw.brain import execute

    devs = await execute("device_list", device_type=device_type)
    cads = await execute("cad_endpoints")
    print(
        json.dumps(
            {"devices": devs.data, "cad_mcp_endpoints": cads.data},
            indent=2,
            default=str,
        )
    )


async def _run_docs(search: str) -> None:
    """Run shop SOP documentation CLI query."""
    from labclaw.brain import execute

    if search:
        res = await execute("docs_search", query=search)
    else:
        res = await execute("docs_list")
    print(json.dumps(res.model_dump(), indent=2, default=str))


def _start_brain(port: int, host: str = "127.0.0.1") -> None:
    """Start the Cloud Brain REST API server."""
    import uvicorn

    from labclaw.brain.server import app

    print(f"Starting MakerClaw Cloud Brain on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)


def _start_mcp() -> None:
    """Start the MCP server (stdio transport)."""
    from labclaw.mcp.server import mcp

    mcp.run(transport="stdio")


async def _list_tools(category: str) -> None:
    """List available tools in terminal."""
    from labclaw.brain import list_tools

    tools = await list_tools(category=category)
    if not tools:
        print("No tools available.")
        return
    print(f"{'TOOL':<35} {'SKILL':<15} {'CATEGORY':<15} DESCRIPTION")
    print("-" * 100)
    for t in tools:
        desc = t.description[:35] if len(t.description) > 35 else t.description
        print(f"{t.name:<35} {t.skill:<15} {t.category:<15} {desc}")
    print(f"\nTotal: {len(tools)} tools")


if __name__ == "__main__":
    main()
