"""Sandboxed Hardware & CAD Simulators (Moonraker, gSender/Grbl, Fusion 360 TCP).

Provides deterministic, in-process or standalone network simulators for:
1. Moonraker / Klipper 3D printer HTTP API
2. gSender / Grbl 1.1h CNC controller HTTP API
3. Autodesk Fusion 360 socket add-in (newline-delimited JSON over TCP)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel


class GcodeScriptRequest(BaseModel):
    script: str = ""


class PrintJobRequest(BaseModel):
    filename: str = "part.gcode"
    filament_used_g: float = 12.5


def create_simulator_app() -> FastAPI:
    """Create a combined FastAPI simulator app hosting Moonraker and gSender endpoints."""
    sim_app = FastAPI(title="MakerClaw Hardware Simulator Suite", version="0.3.0")

    state: dict[str, Any] = {
        "moonraker": {
            "extruder": {"temperature": 210.0, "target": 210.0},
            "heater_bed": {"temperature": 60.0, "target": 60.0},
            "print_stats": {
                "state": "standby",
                "filename": "",
                "filament_used": 0.0,
            },
            "history": [],
        },
        "gsender": {
            "token": "sim-gsender-jwt-token",
            "wpos": {"x": 0.0, "y": 0.0, "z": 15.0},
            "mpos": {"x": -10.0, "y": -10.0, "z": -5.0},
            "prb": {"x": 0.0, "y": 0.0, "z": -0.04, "result": 1},
            "history": [],
        },
    }

    # --- Moonraker / Klipper HTTP Simulator ---
    @sim_app.get("/printer/objects/query")
    async def moonraker_query() -> dict[str, Any]:
        return {"result": {"status": state["moonraker"]}}

    @sim_app.post("/printer/gcode/script")
    async def moonraker_gcode(body: GcodeScriptRequest) -> dict[str, Any]:
        state["moonraker"]["history"].append(body.script)
        return {"result": "ok", "script": body.script}

    @sim_app.post("/printer/print/start")
    async def moonraker_start(body: PrintJobRequest) -> dict[str, Any]:
        ps = state["moonraker"]["print_stats"]
        ps["state"] = "printing"
        ps["filename"] = body.filename
        ps["filament_used"] += float(body.filament_used_g)
        return {"result": "ok", "print_stats": ps}

    @sim_app.post("/printer/print/pause")
    async def moonraker_pause() -> dict[str, Any]:
        state["moonraker"]["print_stats"]["state"] = "paused"
        return {"result": "ok", "state": "paused"}

    @sim_app.post("/printer/print/cancel")
    async def moonraker_cancel() -> dict[str, Any]:
        state["moonraker"]["print_stats"]["state"] = "cancelled"
        return {"result": "ok", "state": "cancelled"}

    # --- gSender / Grbl 1.1h HTTP Simulator ---
    @sim_app.post("/api/signin")
    async def gsender_signin() -> dict[str, Any]:
        return {"enabled": True, "token": state["gsender"]["token"]}

    @sim_app.get("/api/controllers")
    async def gsender_controllers(token: str = "") -> list[dict[str, Any]]:
        return [
            {
                "port": "/dev/ttyACM0",
                "baudrate": 115200,
                "controllerType": "Grbl",
                "authenticated": token == state["gsender"]["token"],
                "state": {
                    "status": {
                        "activeState": "Idle",
                        "wpos": state["gsender"]["wpos"],
                        "mpos": state["gsender"]["mpos"],
                    }
                },
                "settings": {
                    "parameters": {
                        "PRB": state["gsender"]["prb"],
                    }
                },
            }
        ]

    @sim_app.post("/api/gcode")
    async def gsender_gcode(body: GcodeScriptRequest) -> dict[str, Any]:
        state["gsender"]["history"].append(body.script)
        return {"ok": True, "lines": len(body.script.splitlines())}

    # --- OctoPrint Fallback Endpoint ---
    @sim_app.get("/api/version")
    async def octoprint_version() -> dict[str, Any]:
        return {"api": "0.1", "server": "1.10.0-sim", "text": "OctoPrint Simulator"}

    return sim_app


def handle_fusion_command(payload: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
    """Process a single Fusion 360 socket JSON command against simulated scene state."""
    cmd = str(payload.get("command", "ping")).strip()
    params = payload.get("params") or {}
    if cmd == "ping":
        return {"pong": True, "mode": "simulator"}
    if cmd == "get_scene_info":
        return {"bodies": scene["bodies"], "body_count": len(scene["bodies"])}
    if cmd == "create_box":
        w = float(params.get("width", 2.0))
        d = float(params.get("depth", 2.0))
        h = float(params.get("height", 1.0))
        vol = round(w * d * h, 4)
        body = {
            "name": f"Body{len(scene['bodies']) + 1}",
            "volume_cm3": vol,
            "mass_g": round(vol * 7.85, 4),
        }
        scene["bodies"].append(body)
        return {"ok": True, "body": body}
    return {"ok": True, "command": cmd, "params": params}


async def start_fusion_tcp_simulator(
    host: str = "127.0.0.1", port: int = 19876
) -> asyncio.AbstractServer:
    """Start an async TCP socket server simulating the Fusion 360 MCP add-in."""
    scene: dict[str, Any] = {"bodies": [{"name": "Body1", "volume_cm3": 10.0, "mass_g": 78.5}]}

    async def _client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            line = await reader.readline()
            if line:
                req = json.loads(line.decode("utf-8").strip() or "{}")
                resp = handle_fusion_command(req, scene)
                writer.write((json.dumps(resp) + "\n").encode("utf-8"))
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    return await asyncio.start_server(_client_connected, host, port)
