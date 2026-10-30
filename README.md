# MakerClaw (LabClaw Makerspace Fork)

**Unified Makerspace AI Control Plane — Inventory, Shop SOPs/Docs, 3D Printers, CNC Routers, and CAD/EDA MCP Endpoints.**

Forked from [labclaw/labclaw](https://github.com/labclaw/labclaw) and retooled for hardware makerspaces, digital fabrication shops, and robotics labs. MakerClaw exposes a unified Python SDK, FastAPI REST API + Web Dashboard, CLI (`makerclaw` / `labclaw`), and MCP server for AI agents (Hermes Agent, Claude Desktop, OpenCode, Cursor).

## Core Makerspace Capabilities

| Skill | Tools | What It Does |
|---|---|---|
| **Inventory (`inventory`)** | `inventory_list`, `inventory_search`, `inventory_add`, `inventory_update_stock`, `inventory_check_bom`, `inventory_low_stock`, `inventory_seed_defaults` | SQLite-backed shop inventory for filaments (PLA, LW-PLA, PETG), CNC stock blanks (FR-4 copper clad, MDF spoilboards, 6061 aluminum, Birch plywood, anodized cards), cutting bits, MCUs/sensors, and fasteners. Includes BOM validation against on-hand stock with clickable primary/backup vendor URLs. |
| **Devices & Machines (`devices`)** | `device_list`, `device_register`, `device_status`, `device_validate_gcode`, `device_send_command`, `device_feeds_and_speeds` | Connect & monitor 3D printers (Bambu Lab P1S, Moonraker/Klipper, OctoPrint), CNC routers (Genmitsu Cubiko GRBL 1.1h via gSender Headless Remote API), and robot arms (uArm Swift Pro). Enforces pre-flight G-code safety interlocks (envelope bounds, cutter flute-length limits, sacrificial spoilboard check, GRBL `T<n>`/`M0` hazards, hotend/bed thermal limits) and verified CNC feeds & speeds. |
| **CAD / EDA / CAM MCP (`cad_mcp`)** | `cad_endpoints`, `cad_register_endpoint`, `cad_bridge_call`, `cad_verify_mass_delta`, `cad_enclosure_calculator`, `cam_pcb2gcode_command` | Manages MCP-enabled CAD/EDA endpoints (Autodesk Fusion 360 socket MCP on `:9876`, KiCad 10 MCP + Freerouting, headless `pcb2gcode`), verifies CAD volume/mass deltas ($\Delta V$ / $\Delta m$ oracle), computes flat-bottom 3D-printed enclosure & press-fit clearances, and generates mirrored GRBL PCB milling pipelines. |
| **Shop Docs & SOPs (`docs`)** | `docs_list`, `docs_search`, `docs_get`, `docs_save`, `docs_generate_sop`, `maker_reason`, `design_project` | Searchable Markdown knowledge base of shop SOPs (Cubiko CNC setup & probing, in-house FR-4 PCB milling, FDM enclosure rules, KiCad ERC/DRC gates), SOP generator, and 5-phase mechatronics project planner. |

## Quick Start

```bash
# Install with dev & LLM extras
uv sync --extra dev --extra llm

# Run full Makerspace workflow demo (BOM check + CNC feeds/speeds + G-code safety + CAD enclosure math)
uv run makerclaw demo --maker

# List all registered tools (25+ makerspace & brain tools)
uv run makerclaw tools

# Query shop inventory, devices, or SOP docs from CLI
uv run makerclaw inventory --category filament
uv run makerclaw devices --type cnc
uv run makerclaw docs --search spoilboard

# Start REST API + Web Dashboard on http://127.0.0.1:18802
uv run makerclaw brain --port 18802

# Start MCP Server (stdio)
uv run makerclaw mcp
```

## REST API & Web Dashboard

```bash
curl http://localhost:18802/brain/health
curl http://localhost:18802/brain/inventory?category=cnc_tooling
curl http://localhost:18802/brain/devices?device_type=cnc
curl http://localhost:18802/brain/cad
curl http://localhost:18802/brain/docs?query=cubiko
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "device_feeds_and_speeds", "arguments": {"material": "fr4_isolation", "spindle_rpm": 20000}}'
```

## MCP Configuration (Hermes Agent / Claude Desktop)

```json
{
  "mcpServers": {
    "makerclaw": {
      "command": "makerclaw",
      "args": ["mcp"]
    }
  }
}
```

## Testing & Quality Gates

```bash
make test       # 100% unit test coverage enforced (--cov-fail-under=100)
make lint       # ruff check + ruff format --check
uv run mypy src/labclaw/
```

## License

Apache 2.0
