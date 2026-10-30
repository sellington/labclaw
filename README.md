# MakerClaw (v0.3.0)

**Standalone Makerspace AI Control Plane — Inventory, Shop SOPs/Docs, 3D Printers, CNC Routers, and CAD/EDA MCP Endpoints.**

MakerClaw provides a vendor-neutral Python SDK (`import makerclaw`), FastAPI REST API + Operator Web Console, First-Run Setup Wizard (`/setup`), Sandboxed Hardware Simulators (`makerclaw simulators`), CLI (`makerclaw` / `labclaw`), and MCP server for AI agents (Hermes Agent, Claude Desktop, OpenCode, Cursor).

## Core Makerspace Capabilities (35 Tools across 5 Skills)

| Skill | Tools | What It Does |
|---|---|---|
| **Inventory (`inventory`)** | `inventory_list`, `inventory_search`, `inventory_add`, `inventory_update_stock`, `inventory_check_bom`, `inventory_low_stock`, `inventory_seed_defaults`, `inventory_import_order`, `inventory_bin_label_svg` | SQLite-backed shop inventory for filaments, CNC stock blanks, cutting bits, MCUs/sensors, and fasteners. Includes BOM validation, DigiKey/Mouser/LCSC/Bambu CSV order import, and printable SVG barcode bin labels. |
| **Devices & Machines (`devices`)** | `device_list`, `device_register`, `device_status`, `device_validate_gcode`, `device_send_command`, `device_feeds_and_speeds`, `device_upload_job`, `device_probe_heightmap`, `device_render_gcode_svg` | Connect & monitor 3D printers (Bambu Lab, Moonraker/Klipper, OctoPrint) and CNC routers (GRBL / gSender). Enforces pre-flight G-code safety interlocks, verified CNC feeds & speeds, `G38.2` heightmap Z-warping, job dispatch, and 2D SVG toolpath rendering. |
| **CAD / EDA / CAM MCP (`cad_mcp`)** | `cad_endpoints`, `cad_register_endpoint`, `cad_bridge_call`, `cad_verify_mass_delta`, `cad_enclosure_calculator`, `cam_pcb2gcode_command`, `cad_federate_tools` | Manages MCP-enabled CAD/EDA endpoints (Autodesk Fusion 360 socket MCP, KiCad MCP + Freerouting, `pcb2gcode`), verifies CAD volume/mass deltas ($\Delta V$ / $\Delta m$ oracle), computes 3D-printed enclosure clearances, and multiplexes downstream CAD/EDA tools without context bloat. |
| **Shop Docs & SOPs (`docs`)** | `docs_list`, `docs_search`, `docs_get`, `docs_save`, `docs_generate_sop`, `maker_reason`, `reason`, `design_project` | Searchable Markdown knowledge base of shop SOPs (CNC setup & probing, in-house FR-4 PCB milling, FDM enclosure rules, KiCad ERC/DRC gates), SOP generator, and 5-phase mechatronics project planner. |
| **Technical Writing (`write`)** | `write_section` | Structured engineering documentation and report generator. |

## Quick Start

```bash
# Install with dev & LLM extras
uv sync --extra dev --extra llm

# Run full Makerspace workflow demo (BOM check + CNC feeds/speeds + G-code safety + CAD enclosure math)
uv run makerclaw demo --maker

# List all 35 registered tools
uv run makerclaw tools

# Start REST API + Web Dashboard + Setup Wizard on http://127.0.0.1:18802
uv run makerclaw brain --host 0.0.0.0 --port 18802

# Start Sandboxed Hardware Simulators (Moonraker + gSender HTTP + Fusion 360 TCP)
uv run makerclaw simulators --host 127.0.0.1 --port 18803

# Start MCP Server (stdio)
uv run makerclaw mcp
```

## Custom Shop Profile Overlay (`LABCLAW_PROFILE`)

Keep the repository generic and load your shop's specific machine IPs, CAD endpoints, starter inventory, and SOPs via YAML (`examples/profiles/generic-makerspace.yaml`) or the Web Setup Wizard at `http://localhost:18802/setup`:

```bash
export LABCLAW_PROFILE=/etc/makerclaw/shop-profile.yaml
export LABCLAW_INVENTORY_DB=/var/lib/makerclaw/inventory.db
uv run makerclaw brain --host 0.0.0.0 --port 18802
```

## Testing & Quality Gates

```bash
PYTHONPATH=src uv run pytest --cov=labclaw --cov=makerclaw --cov-fail-under=100
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/labclaw/ src/makerclaw/
```

## License

Apache 2.0
