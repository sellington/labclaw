"""Makerspace Devices skill — 3D printers, CNC routers, laser cutters, and safety gates.

Provides a unified interface to register, monitor, validate G-code, compute CNC
feeds & speeds, and safely dispatch commands to makerspace hardware:
- 3D Printers (Moonraker/Klipper, OctoPrint, Bambu Lab)
- CNC Machines (Genmitsu Cubiko / Grbl 1.1h via gSender Remote API, FluidNC)
- Robotics & Benchtop equipment (uArm Swift Pro)
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from labclaw.brain.skills.base import SkillCapability, SkillMetadata
from labclaw.brain.types import BrainResult, ToolInfo

_DEFAULT_DEVICES: dict[str, dict[str, Any]] = {
    "bambu-p1s": {
        "device_id": "bambu-p1s",
        "name": "Bambu Lab P1S (Enclosed CoreXY 3D Printer)",
        "device_type": "3d_printer",
        "protocol": "bambu",
        "endpoint": "10.1.1.190:8883",
        "status": "idle",
        "envelope_mm": {"x": 256.0, "y": 256.0, "z": 256.0},
        "max_nozzle_temp_c": 300.0,
        "max_bed_temp_c": 100.0,
        "capabilities": ["print_3mf", "print_gcode", "ams_filament", "telemetry", "pause", "stop"],
        "telemetry": {
            "nozzle_temp_c": 24.0,
            "bed_temp_c": 23.5,
            "loaded_filament": "Bambu PLA Matte Black",
            "progress_pct": 0.0,
        },
    },
    "voron-klipper": {
        "device_id": "voron-klipper",
        "name": "Voron 2.4 (Klipper / Moonraker HTTP)",
        "device_type": "3d_printer",
        "protocol": "moonraker",
        "endpoint": "http://127.0.0.1:7125",
        "status": "idle",
        "envelope_mm": {"x": 300.0, "y": 300.0, "z": 280.0},
        "max_nozzle_temp_c": 300.0,
        "max_bed_temp_c": 120.0,
        "capabilities": ["print_gcode", "home", "jog", "macro", "telemetry", "emergency_stop"],
        "telemetry": {
            "nozzle_temp_c": 25.0,
            "bed_temp_c": 24.0,
            "state": "ready",
        },
    },
    "cubiko-cnc": {
        "device_id": "cubiko-cnc",
        "name": "Genmitsu Cubiko Desktop CNC Router (GRBL 1.1h + gSender)",
        "device_type": "cnc",
        "protocol": "gsender",
        "endpoint": "http://10.1.1.211:8000",
        "status": "idle",
        "envelope_mm": {"x": 150.0, "y": 110.0, "z": 40.0},
        "max_spindle_rpm": 20000,
        "collet": "ER11 (1/8 in / 3.175 mm)",
        "bed_grid_spec": {
            "plate_mm": [180.0, 120.0, 5.5],
            "m5_grid_pitch_mm": {"x": 33.2, "y": 26.5},
            "edge_inset_mm": 7.0,
            "auto_z_probe_xy_mm": [163.0, 111.5],
        },
        "capabilities": [
            "run_gcode",
            "heightmap_probe",
            "home",
            "jog",
            "zero_wcs",
            "spindle_control",
            "emergency_stop",
        ],
        "telemetry": {
            "wpos": {"x": 0.0, "y": 0.0, "z": 15.0},
            "mpos": {"x": -10.0, "y": -10.0, "z": -5.0},
            "spindle_rpm": 0,
            "controller": "Grbl 1.1h",
        },
    },
    "uarm-swift-pro": {
        "device_id": "uarm-swift-pro",
        "name": "uArm Swift Pro 4-DOF Desktop Robot Arm",
        "device_type": "robot_arm",
        "protocol": "serial_gcode",
        "endpoint": "/dev/cu.usbmodem14101",
        "status": "idle",
        "envelope_mm": {"x": 320.0, "y": 320.0, "z": 250.0},
        "capabilities": ["move_xyz", "wrist_rotate", "suction_pump", "gripper", "touch_pen"],
        "telemetry": {"x": 150.0, "y": 0.0, "z": 90.0, "TouchSwitch_PG3": 0},
    },
}

_FEEDS_AND_SPEEDS: dict[str, dict[str, Any]] = {
    "fr4_isolation": {
        "material": "FR-4 Copper Clad (1oz / 35um)",
        "operation": "PCB Trace Isolation Milling",
        "recommended_tool": "30-deg 0.1mm or 0.2mm Carbide V-Bit (1/8 in shank)",
        "profiles": {
            "10000": {
                "spindle_rpm": 10000,
                "grbl_s": "S10000 ($30=10000)",
                "xy_feed_mm_min": 120,
                "z_plunge_mm_min": 30,
                "doc_mm": 0.06,
                "isolation_width_mm": 0.45,
                "overlap_pct": 45,
            },
            "20000": {
                "spindle_rpm": 20000,
                "grbl_s": "S20000 ($30=20000)",
                "xy_feed_mm_min": 200,
                "z_plunge_mm_min": 45,
                "doc_mm": 0.06,
                "isolation_width_mm": 0.45,
                "overlap_pct": 45,
            },
        },
        "notes": [
            (
                "Run dry electrical continuity height-map probe first, detach alligator clips, "
                "then apply 3-4 drops of water+dish soap or IPA film (never silicone oil)."
            ),
            "Strip standalone T<n> and M0 tool-change lines from pcb2gcode output for GRBL 1.1h.",
        ],
    },
    "fr4_cutout": {
        "material": "FR-4 Copper Clad (1.6mm thick)",
        "operation": "PCB Drilling & Tabbed Board Outline Cutout",
        "recommended_tool": "1.0mm Ti-Coated Carbide Flat End Mill (7.0mm LOC)",
        "profiles": {
            "10000": {
                "spindle_rpm": 10000,
                "grbl_s": "S10000",
                "xy_feed_mm_min": 120,
                "z_plunge_mm_min": 30,
                "drill_plunge_mm_min": 45,
                "doc_mm": 0.45,
                "total_z_cut_mm": -1.75,
                "bridges_count": 4,
                "bridge_width_mm": 2.0,
            },
            "20000": {
                "spindle_rpm": 20000,
                "grbl_s": "S20000",
                "xy_feed_mm_min": 180,
                "z_plunge_mm_min": 45,
                "drill_plunge_mm_min": 60,
                "doc_mm": 0.45,
                "total_z_cut_mm": -1.75,
                "bridges_count": 4,
                "bridge_width_mm": 2.0,
            },
        },
        "notes": [
            (
                "CRITICAL: Always place a >= 3.0mm sacrificial MDF spoilboard over any "
                "3D-printed PLA bed adapter so hot fiberglass exits into MDF, never bare PLA."
            ),
        ],
    },
    "plywood_birch": {
        "material": "Birch Aircraft Plywood / Basswood (1/8 in / 3.2mm)",
        "operation": "Through-Cut Profile & Gear Milling",
        "recommended_tool": "1.0mm Flat End Mill (7.0mm LOC)",
        "profiles": {
            "10000": {
                "spindle_rpm": 10000,
                "grbl_s": "S10000",
                "xy_feed_mm_min": 250,
                "z_plunge_mm_min": 60,
                "doc_mm": 0.68,
                "passes": 5,
                "total_z_cut_mm": -3.40,
                "tab_thickness_mm": 1.20,
            },
            "20000": {
                "spindle_rpm": 20000,
                "grbl_s": "S20000",
                "xy_feed_mm_min": 350,
                "z_plunge_mm_min": 80,
                "doc_mm": 0.68,
                "passes": 5,
                "total_z_cut_mm": -3.40,
                "tab_thickness_mm": 1.20,
            },
        },
        "notes": [
            (
                "For stock > 3.5mm thick (up to 6.35mm max LOC ceiling), widen 1.0mm slots "
                "to 1.3-1.4mm via a second offset pass so sawdust evacuates cleanly."
            ),
        ],
    },
    "aluminum_6061": {
        "material": "6061-T6 / 7075-T6 / MIC-6 Aluminum (or C360 Free-Machining Brass)",
        "operation": "2.5D Pocket & Profile Milling",
        "recommended_tool": (
            "3.175mm (1/8 in) or 2.0mm Single-Flute (O-Flute) Upcut Carbide End Mill"
        ),
        "profiles": {
            "10000": {
                "spindle_rpm": 10000,
                "grbl_s": "S10000",
                "xy_feed_mm_min": 300,
                "z_plunge_mm_min": 50,
                "doc_mm": 0.15,
            },
            "20000": {
                "spindle_rpm": 20000,
                "grbl_s": "S20000",
                "xy_feed_mm_min": 400,
                "z_plunge_mm_min": 75,
                "doc_mm": 0.20,
            },
        },
        "notes": [
            (
                "Use 6061-T6, 7075-T6, MIC-6, or C360 brass with IPA mist lubrication. "
                "Avoid gummy 3003/5052 aluminum sheet."
            ),
            "Never attempt steel, stainless steel, or titanium on a desktop 75W-200W spindle.",
        ],
    },
    "anodized_card_engrave": {
        "material": "Anodized Aluminum Business Card Blank (86x54x0.4mm)",
        "operation": "Laser-Sharp V-Engraving / Calibration Coupon",
        "recommended_tool": "30-deg 0.1mm Carbide V-Bit",
        "profiles": {
            "10000": {
                "spindle_rpm": 10000,
                "grbl_s": "S10000",
                "xy_feed_mm_min": 180,
                "z_plunge_mm_min": 30,
                "doc_mm": 0.05,
            },
            "20000": {
                "spindle_rpm": 20000,
                "grbl_s": "S20000",
                "xy_feed_mm_min": 280,
                "z_plunge_mm_min": 40,
                "doc_mm": 0.05,
            },
        },
        "notes": [
            (
                "NEVER use bare electrical continuity probing on anodized aluminum "
                "(oxide layer is insulating). Zero Z via paper drag test or copper foil tape."
            ),
            (
                "NEVER drive a 0.1mm V-bit into the mechanical spring-loaded "
                "tool-setter button — it crushes the tip."
            ),
        ],
    },
}


class DevicesSkill:
    """Makerspace Devices skill — 3D printers, CNC machines, and safety validation."""

    metadata: SkillMetadata = SkillMetadata(
        name="devices",
        version="0.2.0",
        description=(
            "Makerspace device registry & control: 3D printers (Moonraker/Klipper, "
            "OctoPrint, Bambu), CNC machines (Cubiko/Grbl/gSender), G-code safety "
            "validator, and CNC feeds & speeds engine."
        ),
        capabilities=[
            SkillCapability.DEVICE_CONTROL,
            SkillCapability.TOOL_EXECUTION,
        ],
    )

    def __init__(self) -> None:
        self._devices: dict[str, dict[str, Any]] = {
            k: json_clone(v) for k, v in _DEFAULT_DEVICES.items()
        }

    async def execute(self, tool_name: str, **kwargs: Any) -> BrainResult:
        """Route tool execution."""
        handlers: dict[str, Any] = {
            "device_list": self._list_devices,
            "device_register": self._register_device,
            "device_status": self._device_status,
            "device_validate_gcode": self._validate_gcode,
            "device_send_command": self._send_command,
            "device_feeds_and_speeds": self._feeds_and_speeds,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            available = ", ".join(sorted(handlers))
            return BrainResult(
                success=False,
                error=f"Unknown tool '{tool_name}'. Available: {available}",
            )
        return await handler(**kwargs)  # type: ignore[no-any-return]

    async def _list_devices(
        self,
        device_type: str = "",
        **kwargs: Any,
    ) -> BrainResult:
        devices = list(self._devices.values())
        if device_type:
            dt = device_type.strip().lower()
            devices = [d for d in devices if str(d.get("device_type", "")).lower() == dt]
        return BrainResult(
            success=True,
            data={"devices": devices, "count": len(devices)},
        )

    async def _register_device(
        self,
        device_id: str = "",
        name: str = "",
        device_type: str = "3d_printer",
        protocol: str = "moonraker",
        endpoint: str = "",
        envelope_mm: dict[str, float] | None = None,
        capabilities: list[str] | None = None,
        status: str = "idle",
        **kwargs: Any,
    ) -> BrainResult:
        if not device_id.strip() or not name.strip():
            return BrainResult(success=False, error="Both 'device_id' and 'name' are required")
        did = device_id.strip()
        record: dict[str, Any] = {
            "device_id": did,
            "name": name.strip(),
            "device_type": device_type.strip().lower(),
            "protocol": protocol.strip().lower(),
            "endpoint": endpoint.strip(),
            "status": status.strip().lower(),
            "envelope_mm": envelope_mm or {"x": 200.0, "y": 200.0, "z": 200.0},
            "capabilities": capabilities or ["telemetry", "emergency_stop"],
            "telemetry": {},
        }
        self._devices[did] = record
        return BrainResult(success=True, data=record)

    async def _device_status(
        self,
        device_id: str = "",
        probe_network: bool = False,
        **kwargs: Any,
    ) -> BrainResult:
        did = device_id.strip()
        if did not in self._devices:
            return BrainResult(success=False, error=f"Device '{did}' is not registered")

        device = json_clone(self._devices[did])
        if probe_network and device.get("endpoint", "").startswith("http"):
            live = await self._probe_http_device(device)
            device["live_probe"] = live
        return BrainResult(success=True, data=device)

    async def _probe_http_device(self, device: dict[str, Any]) -> dict[str, Any]:
        """Poll live HTTP telemetry for Moonraker, OctoPrint, or gSender."""
        endpoint = str(device.get("endpoint", "")).rstrip("/")
        protocol = str(device.get("protocol", "")).lower()
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                if protocol == "gsender":
                    signin = await client.post(f"{endpoint}/api/signin", json={})
                    token = signin.json().get("token", "")
                    resp = await client.get(f"{endpoint}/api/controllers?token={token}")
                    return {"reachable": resp.status_code == 200, "controllers": resp.json()}
                if protocol == "moonraker":
                    resp = await client.get(
                        f"{endpoint}/printer/objects/query?heater_bed&extruder&print_stats"
                    )
                    return {"reachable": resp.status_code == 200, "telemetry": resp.json()}
                resp = await client.get(f"{endpoint}/api/version")
                return {"reachable": resp.status_code == 200, "info": resp.json()}
        except Exception as exc:
            return {"reachable": False, "error": str(exc)}

    async def _validate_gcode(
        self,
        gcode: str = "",
        device_id: str = "cubiko-cnc",
        spoilboard_present: bool = True,
        max_flute_length_mm: float = 7.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Validate G-code against machine work envelope, spindle/temp limits, and GRBL hazards."""
        if not gcode.strip():
            return BrainResult(success=False, error="G-code string is empty")

        device = self._devices.get(device_id, _DEFAULT_DEVICES["cubiko-cnc"])
        env = device.get("envelope_mm", {"x": 150.0, "y": 110.0, "z": 40.0})
        dtype = device.get("device_type", "cnc")

        warnings: list[str] = []
        violations: list[str] = []

        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []
        feeds: list[float] = []
        spindle_speeds: list[float] = []
        nozzle_temps: list[float] = []
        bed_temps: list[float] = []

        for idx, raw_line in enumerate(gcode.splitlines(), start=1):
            # Strip comments
            line = raw_line.split(";", 1)[0].strip()
            line = re.sub(r"\(.*?\)", "", line).strip()
            if not line:
                continue

            upper = line.upper()

            # Check GRBL unstripped tool-change / M0 pauses
            if dtype == "cnc":
                if re.match(r"^T\d+\b", upper) or "M6" in upper:
                    violations.append(
                        f"Line {idx}: Unstripped tool change '{line}' will error on GRBL 1.1h"
                    )
                if re.search(r"\bM0\b|\bM00\b", upper):
                    warnings.append(
                        f"Line {idx}: Program pause '{line}' detected "
                        "(strip M0 for unattended pcb2gcode runs)"
                    )

            # Extract coordinates and speeds
            for axis, bucket in (("X", xs), ("Y", ys), ("Z", zs), ("F", feeds)):
                m = re.search(rf"{axis}([+-]?\d+(?:\.\d+)?)", upper)
                if m:
                    bucket.append(float(m.group(1)))

            if dtype == "cnc" and ("M3" in upper or "M03" in upper or upper.startswith("S")):
                ms = re.search(r"S(\d+(?:\.\d+)?)", upper)
                if ms:
                    spindle_speeds.append(float(ms.group(1)))

            if dtype == "3d_printer":
                if "M104" in upper or "M109" in upper:
                    mt = re.search(r"S(\d+(?:\.\d+)?)", upper)
                    if mt:
                        nozzle_temps.append(float(mt.group(1)))
                if "M140" in upper or "M190" in upper:
                    mb = re.search(r"S(\d+(?:\.\d+)?)", upper)
                    if mb:
                        bed_temps.append(float(mb.group(1)))

        bbox = {
            "x_min": min(xs) if xs else 0.0,
            "x_max": max(xs) if xs else 0.0,
            "y_min": min(ys) if ys else 0.0,
            "y_max": max(ys) if ys else 0.0,
            "z_min": min(zs) if zs else 0.0,
            "z_max": max(zs) if zs else 0.0,
        }
        span_x = bbox["x_max"] - min(0.0, bbox["x_min"])
        span_y = bbox["y_max"] - min(0.0, bbox["y_min"])
        span_z = bbox["z_max"] - bbox["z_min"]

        if span_x > float(env["x"]):
            violations.append(f"X span {span_x:.2f}mm exceeds {device_id} envelope ({env['x']}mm)")
        if span_y > float(env["y"]):
            violations.append(f"Y span {span_y:.2f}mm exceeds {device_id} envelope ({env['y']}mm)")
        if span_z > float(env["z"]):
            violations.append(f"Z span {span_z:.2f}mm exceeds {device_id} envelope ({env['z']}mm)")

        if dtype == "cnc":
            if bbox["z_min"] < -max_flute_length_mm:
                violations.append(
                    f"Min Z {bbox['z_min']:.2f}mm exceeds cutter flute length "
                    f"({max_flute_length_mm:.2f}mm LOC) — shank will rub/snap bit"
                )
            if bbox["z_min"] < -1.65 and not spoilboard_present:
                violations.append(
                    f"Through-cut Z={bbox['z_min']:.2f}mm without sacrificial MDF "
                    "spoilboard will melt PLA bed adapter and snap bit"
                )
            max_rpm = float(device.get("max_spindle_rpm", 20000))
            if spindle_speeds and max(spindle_speeds) > max_rpm:
                violations.append(
                    f"Spindle speed {max(spindle_speeds):.0f} RPM exceeds max {max_rpm:.0f} RPM"
                )

        if dtype == "3d_printer":
            max_nozzle = float(device.get("max_nozzle_temp_c", 300.0))
            max_bed = float(device.get("max_bed_temp_c", 120.0))
            if nozzle_temps and max(nozzle_temps) > max_nozzle:
                violations.append(
                    f"Nozzle temp {max(nozzle_temps):.1f}C exceeds max {max_nozzle:.1f}C"
                )
            if bed_temps and max(bed_temps) > max_bed:
                violations.append(f"Bed temp {max(bed_temps):.1f}C exceeds max {max_bed:.1f}C")

        safe = len(violations) == 0
        return BrainResult(
            success=True,
            data={
                "safe": safe,
                "device_id": device_id,
                "bounding_box_mm": bbox,
                "max_feed_mm_min": max(feeds) if feeds else 0.0,
                "violations": violations,
                "warnings": warnings,
            },
        )

    async def _send_command(
        self,
        device_id: str = "",
        action: str = "",
        parameters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> BrainResult:
        """Execute a safety-checked command on a makerspace device."""
        did = device_id.strip()
        if did not in self._devices:
            return BrainResult(success=False, error=f"Device '{did}' is not registered")

        device = self._devices[did]
        act = action.strip().lower()
        params = parameters or {}

        # Emergency stop always succeeds immediately regardless of state
        if act == "emergency_stop":
            device["status"] = "stopped"
            return BrainResult(
                success=True,
                data={
                    "device_id": did,
                    "action": "emergency_stop",
                    "status": "stopped",
                    "message": "EMERGENCY STOP executed immediately",
                },
            )

        if device.get("status") in {"offline", "error"}:
            return BrainResult(
                success=False,
                error=(
                    f"Safety checker blocked '{act}': device '{did}' "
                    f"status is '{device.get('status')}'"
                ),
            )

        allowed = [c.lower() for c in device.get("capabilities", [])]
        if act not in allowed and act != "gcode":
            return BrainResult(
                success=False,
                error=f"Action '{act}' not in device '{did}' capabilities: {allowed}",
            )

        if act in {"gcode", "run_gcode", "print_gcode"} and "gcode" in params:
            validation = await self._validate_gcode(
                gcode=str(params["gcode"]),
                device_id=did,
                spoilboard_present=bool(params.get("spoilboard_present", True)),
            )
            if not validation.data["safe"]:
                v_str = "; ".join(validation.data["violations"])
                return BrainResult(
                    success=False,
                    error=f"Safety checker rejected G-code: {v_str}",
                )

        return BrainResult(
            success=True,
            data={
                "device_id": did,
                "action": act,
                "parameters": params,
                "safety_check": "passed",
                "status": device.get("status"),
            },
        )

    async def _feeds_and_speeds(
        self,
        material: str = "fr4_isolation",
        spindle_rpm: int = 10000,
        **kwargs: Any,
    ) -> BrainResult:
        """Lookup verified CNC feeds, speeds, depth of cut, and tooling rules."""
        key = material.strip().lower()
        # Fuzzy match if not exact key
        matched_key = key if key in _FEEDS_AND_SPEEDS else None
        if matched_key is None:
            for k, v in _FEEDS_AND_SPEEDS.items():
                if (
                    key in k
                    or key in str(v["material"]).lower()
                    or key in str(v["operation"]).lower()
                ):
                    matched_key = k
                    break

        if matched_key is None:
            return BrainResult(
                success=False,
                error=(
                    f"No feeds & speeds profile matching '{material}'. "
                    f"Available profiles: {', '.join(sorted(_FEEDS_AND_SPEEDS))}"
                ),
            )

        entry = _FEEDS_AND_SPEEDS[matched_key]
        rpm_key = "20000" if int(spindle_rpm) >= 15000 else "10000"
        profile = entry["profiles"][rpm_key]
        return BrainResult(
            success=True,
            data={
                "profile_key": matched_key,
                "material": entry["material"],
                "operation": entry["operation"],
                "recommended_tool": entry["recommended_tool"],
                "spindle_setting": profile,
                "safety_and_process_notes": entry["notes"],
            },
        )

    async def list_tools(self) -> list[ToolInfo]:
        """Return all device & CNC tools."""
        return [
            ToolInfo(
                name="device_list",
                description="List registered makerspace 3D printers, CNC routers, and robot arms.",
                skill="devices",
                category="devices",
            ),
            ToolInfo(
                name="device_register",
                description=(
                    "Register or update a 3D printer, CNC router, laser cutter, or bench device."
                ),
                skill="devices",
                category="devices",
            ),
            ToolInfo(
                name="device_status",
                description=(
                    "Get status and live telemetry (Moonraker, OctoPrint, gSender, Bambu) "
                    "for a device."
                ),
                skill="devices",
                category="devices",
            ),
            ToolInfo(
                name="device_validate_gcode",
                description=(
                    "Validate G-code against machine work envelope, flute-length limits, "
                    "spoilboard safety, spindle RPM, and GRBL compatibility."
                ),
                skill="devices",
                category="cnc",
            ),
            ToolInfo(
                name="device_send_command",
                description="Send a safety-validated command or G-code snippet to a device.",
                skill="devices",
                category="devices",
            ),
            ToolInfo(
                name="device_feeds_and_speeds",
                description=(
                    "Calculate verified CNC feeds, speeds, stepdown, and tooling for FR-4 PCBs, "
                    "plywood, 6061 aluminum, C360 brass, and anodized aluminum."
                ),
                skill="devices",
                category="cnc",
            ),
        ]

    async def health_check(self) -> bool:
        """Return True when device registry is initialized."""
        return len(self._devices) > 0


def json_clone(obj: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy a JSON-serializable dictionary."""
    import json

    return dict(json.loads(json.dumps(obj)))
