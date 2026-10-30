# L2 Makerspace Gateway & MCP Multiplexer Spec

**Layer:** Cloud Brain Gateway, Setup Wizard & MCP Federation (L2)

## Purpose

The L2 Gateway exposes all MakerClaw capabilities over three transports:
1. **FastAPI REST & Operator Console (`src/labclaw/brain/server.py`)** on port `18802`
2. **FastMCP Server (`src/labclaw/mcp/server.py`)** over `stdio`
3. **Python SDK (`import makerclaw`)**

## Endpoints

| Route | Method | Description |
|---|---|---|
| `/` | `GET` | Dark-mode Makerspace Operator Console |
| `/setup` | `GET` | Interactive First-Run Setup Wizard |
| `/brain/profile` | `POST` | Apply a YAML/JSON Shop Profile into live skills |
| `/brain/health` | `GET` | Skill health and registered tool count |
| `/brain/inventory` | `GET` | Query SQLite inventory, low stock, or search |
| `/brain/devices` | `GET` | List registered 3D printers and CNC machines |
| `/brain/cad` | `GET` | List CAD, EDA, and CAM MCP endpoints |
| `/brain/docs` | `GET` | List or search shop SOPs |
| `/brain/execute` | `POST` | Execute any tool by name with API key auth |
