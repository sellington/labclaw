# MakerClaw Architecture (v0.3.0)

MakerClaw is a unified Makerspace AI Control Plane that bridges physical fabrication hardware (3D printers, CNC routers, robot arms), digital CAD/EDA MCP servers (Autodesk Fusion 360, KiCad, headless CAM), SQLite shop inventory, and Markdown standard operating procedures (SOPs) into a single agentic gateway.

---

## Five-Layer Makerspace Stack

```
┌──────────────────────────────────────────────────────────────────┐
│  Layer 5: OPERATOR CONSOLE & FIRST-RUN SETUP WIZARD              │
│  Dark-mode Web Console (/) · Setup Wizard (/setup) · SVG Tools   │
├──────────────────────────────────────────────────────────────────┤
│  Layer 4: SHOP KNOWLEDGE & INVENTORY                             │
│  SQLite Inventory (`inventory.db`) · Markdown SOPs · YAML Overlay│
├──────────────────────────────────────────────────────────────────┤
│  Layer 3: PHYSICAL VERIFICATION & ENGINEERING ENGINE             │
│  CAD Mass/Volume Delta Oracle · CNC Feeds/Speeds · Heightmap Warp│
├──────────────────────────────────────────────────────────────────┤
│  Layer 2: UNIFIED GATEWAY & ACTIVE MCP MULTIPLEXER               │
│  FastAPI REST (`/brain/*`) · FastMCP Server · CAD Tool Router    │
├──────────────────────────────────────────────────────────────────┤
│  Layer 1: HARDWARE DRIVERS, SIMULATORS & G-CODE INTERLOCKS       │
│  Moonraker · gSender/GRBL · Bambu · OctoPrint · Safety Validator │
└──────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Hardware Drivers, Simulators & Safety Interlocks

Every 3D printer, CNC router, and bench instrument is registered with an identity, work envelope, protocol, and safety constraints:

| Protocol | Target Hardware | Capabilities |
|---|---|---|
| `gsender_rest` / `grbl` | Desktop CNC routers (Genmitsu Cubiko, 3018, Shapeoko) | JWT `/api/signin`, `/api/controllers`, `/api/gcode`, `G38.2` Z-probing |
| `moonraker` | Klipper 3D printers (Voron, RatRig, Creality K1) | `/printer/objects/query`, `/printer/print/start`, `/printer/gcode/script` |
| `bambu_mqtt` | Bambu Lab P1S / X1C / A1 | LAN status, filament reservation, thermal safety checks |
| `octoprint` | Prusa / Marlin 3D printers | `/api/version`, `/api/job`, G-code upload |
| `simulators` | Sandboxed CI & Dev VM (`makerclaw simulators`) | Full Moonraker + gSender HTTP simulator + Fusion 360 TCP socket server |

**Pre-Flight G-Code Safety Interlock (`device_validate_gcode`):**
All G-code programs are checked prior to execution for:
- Machine XYZ work envelope compliance
- Maximum cutter flute length (LOC) vs. deepest Z plunge
- Sacrificial MDF spoilboard presence for through-cuts
- Unhandled GRBL toolchange (`T<n>`, `M6`) and `M0` pause hazards
- 3D printer hotend (`<= 300 °C`) and bed (`<= 120 °C`) thermal ceilings

---

## Layer 2: Unified Gateway & Active MCP Multiplexer

- **Python SDK (`import makerclaw`)**: `execute()`, `list_tools()`, `reason()`, `write()`, `health()`, `apply_shop_profile()`
- **FastAPI REST API (`makerclaw brain`)**: `/`, `/setup`, `/brain/profile`, `/brain/health`, `/brain/inventory`, `/brain/devices`, `/brain/cad`, `/brain/docs`, `/brain/execute`
- **Active MCP Multiplexer (`cad_federate_tools`)**: Context-window-aware router that selects the relevant downstream Fusion 360, KiCad, and CAM tools for a task and attaches mandatory verification gates (`cad_verify_mass_delta`, `kicad-cli pcb drc`, `device_validate_gcode`).
