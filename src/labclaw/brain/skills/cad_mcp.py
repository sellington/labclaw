"""CAD, EDA, and CAM MCP Endpoint skill — Fusion 360, KiCad, and CAM calculators.

Manages MCP-enabled CAD/EDA endpoints (Autodesk Fusion 360 socket/MCP,
KiCad MCP server, headless manifold3d/pcb2gcode pipelines) and provides
parametric verification and enclosure/workholding calculators.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from labclaw.brain.skills.base import SkillCapability, SkillMetadata
from labclaw.brain.types import BrainResult, ToolInfo

_MATERIAL_DENSITIES_G_CM3: dict[str, float] = {
    "steel": 7.85,
    "pla": 1.24,
    "lw_pla": 0.55,
    "petg": 1.27,
    "abs": 1.04,
    "asa": 1.07,
    "aluminum_6061": 2.70,
    "brass_c360": 8.50,
    "copper": 8.96,
    "fr4": 1.85,
    "birch_plywood": 0.68,
}

_DEFAULT_CAD_ENDPOINTS: dict[str, dict[str, Any]] = {
    "fusion360-bench": {
        "endpoint_id": "fusion360-bench",
        "name": "Autodesk Fusion 360 MCP (Bench CAD Host)",
        "domain": "cad_cam",
        "transport": "tcp_socket",
        "host": "127.0.0.1",
        "port": 9876,
        "mcp_command": "uvx fusion360-mcp-server --mode socket --host 127.0.0.1",
        "tool_prefix": "mcp__fusion360__",
        "tool_count": 84,
        "units": "cm (internal geometry), mm (user parameters)",
        "capabilities": [
            "parametric_sketch",
            "extrude_revolve_loft_sweep",
            "boolean_operation",
            "sheet_metal",
            "cam_toolpaths",
            "export_stl_f3d",
            "execute_code",
        ],
    },
    "fusion360-workstation": {
        "endpoint_id": "fusion360-workstation",
        "name": "Autodesk Fusion 360 MCP (Remote Workstation)",
        "domain": "cad_cam",
        "transport": "tcp_socket",
        "host": "cad-workstation.local",
        "port": 9876,
        "mcp_command": "uvx fusion360-mcp-server --mode socket --host cad-workstation.local",
        "tool_prefix": "mcp__fusion360__",
        "tool_count": 84,
        "units": "cm (internal geometry), mm (user parameters)",
        "capabilities": [
            "parametric_sketch",
            "extrude_revolve_loft_sweep",
            "boolean_operation",
            "cam_toolpaths",
            "export_stl_f3d",
            "execute_code",
        ],
    },
    "kicad-eda": {
        "endpoint_id": "kicad-eda",
        "name": "KiCad MCP Server + Freerouting + kicad-cli",
        "domain": "eda_pcb",
        "transport": "stdio",
        "host": "127.0.0.1",
        "port": 0,
        "mcp_command": "kicad-mcp-server",
        "tool_prefix": "mcp__kicad__",
        "tool_count": 248,
        "units": "mm",
        "capabilities": [
            "schematic_capture",
            "erc_validation",
            "pcb_placement",
            "freerouting_autoroute",
            "copper_pours",
            "drc_validation",
            "gerber_bom_cpl_export",
        ],
    },
    "pcb2gcode-cam": {
        "endpoint_id": "pcb2gcode-cam",
        "name": "pcb2gcode Headless Gerber-to-GRBL CNC Toolpath Generator",
        "domain": "cam_pcb",
        "transport": "cli",
        "host": "127.0.0.1",
        "port": 0,
        "mcp_command": "pcb2gcode",
        "tool_prefix": "cam_",
        "tool_count": 4,
        "units": "mm",
        "capabilities": [
            "isolation_routing",
            "excellon_drilling",
            "helical_milldrill",
            "tabbed_board_cutout",
        ],
    },
}


class CadMcpSkill:
    """CAD/EDA/CAM MCP endpoint bridge and parametric geometry calculator."""

    metadata: SkillMetadata = SkillMetadata(
        name="cad_mcp",
        version="0.2.0",
        description=(
            "MCP-enabled CAD/EDA/CAM endpoint management (Fusion 360, KiCad, pcb2gcode), "
            "parametric volume/mass verification, and enclosure/workholding calculators."
        ),
        capabilities=[
            SkillCapability.CAD_CAM,
            SkillCapability.TOOL_EXECUTION,
        ],
    )

    def __init__(self) -> None:
        self._endpoints: dict[str, dict[str, Any]] = {
            k: dict(v) for k, v in _DEFAULT_CAD_ENDPOINTS.items()
        }

    async def execute(self, tool_name: str, **kwargs: Any) -> BrainResult:
        """Route tool execution."""
        handlers: dict[str, Any] = {
            "cad_endpoints": self._list_endpoints,
            "cad_register_endpoint": self._register_endpoint,
            "cad_bridge_call": self._bridge_call,
            "cad_verify_mass_delta": self._verify_mass_delta,
            "cad_enclosure_calculator": self._enclosure_calculator,
            "cam_pcb2gcode_command": self._pcb2gcode_command,
            "cad_federate_tools": self._federate_tools,
            "cad_generate_aruco_bin_stl": self._generate_aruco_bin_stl,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            available = ", ".join(sorted(handlers))
            return BrainResult(
                success=False,
                error=f"Unknown tool '{tool_name}'. Available: {available}",
            )
        return await handler(**kwargs)  # type: ignore[no-any-return]

    async def _list_endpoints(
        self,
        domain: str = "",
        probe: bool = False,
        **kwargs: Any,
    ) -> BrainResult:
        endpoints = [dict(ep) for ep in self._endpoints.values()]
        if domain:
            d = domain.strip().lower()
            endpoints = [ep for ep in endpoints if str(ep.get("domain", "")).lower() == d]

        if probe:
            for ep in endpoints:
                if ep.get("transport") == "tcp_socket" and ep.get("port", 0) > 0:
                    ep["reachable"] = await self._probe_tcp(str(ep["host"]), int(ep["port"]))
                else:
                    ep["reachable"] = True

        return BrainResult(
            success=True,
            data={"endpoints": endpoints, "count": len(endpoints)},
        )

    async def _register_endpoint(
        self,
        endpoint_id: str = "",
        name: str = "",
        domain: str = "cad_cam",
        transport: str = "tcp_socket",
        host: str = "127.0.0.1",
        port: int = 9876,
        mcp_command: str = "",
        tool_prefix: str = "",
        capabilities: list[str] | None = None,
        **kwargs: Any,
    ) -> BrainResult:
        if not endpoint_id.strip() or not name.strip():
            return BrainResult(success=False, error="Both 'endpoint_id' and 'name' are required")
        eid = endpoint_id.strip()
        record: dict[str, Any] = {
            "endpoint_id": eid,
            "name": name.strip(),
            "domain": domain.strip().lower(),
            "transport": transport.strip().lower(),
            "host": host.strip(),
            "port": int(port),
            "mcp_command": mcp_command.strip(),
            "tool_prefix": tool_prefix.strip(),
            "capabilities": capabilities or ["execute"],
        }
        self._endpoints[eid] = record
        return BrainResult(success=True, data=record)

    async def _probe_tcp(self, host: str, port: int, timeout: float = 1.5) -> bool:
        try:
            conn = asyncio.open_connection(host, port)
            _, writer = await asyncio.wait_for(conn, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _bridge_call(
        self,
        endpoint_id: str = "fusion360-bench",
        command: str = "ping",
        arguments: dict[str, Any] | None = None,
        timeout: float = 3.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Send a newline-delimited JSON command to a CAD TCP socket endpoint or simulate."""
        eid = endpoint_id.strip()
        if eid not in self._endpoints:
            return BrainResult(success=False, error=f"CAD endpoint '{eid}' is not registered")

        ep = self._endpoints[eid]
        args = arguments or {}
        if ep.get("transport") != "tcp_socket":
            return BrainResult(
                success=True,
                data={
                    "endpoint_id": eid,
                    "transport": ep.get("transport"),
                    "mcp_command": ep.get("mcp_command"),
                    "delegated_tool": f"{ep.get('tool_prefix', '')}{command}",
                    "arguments": args,
                },
            )

        host = str(ep["host"])
        port = int(ep["port"])
        payload = json.dumps({"command": command, "params": args}) + "\n"
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )
            writer.write(payload.encode("utf-8"))
            await writer.drain()
            raw_resp = await asyncio.wait_for(reader.readline(), timeout=timeout)
            writer.close()
            await writer.wait_closed()
            parsed = json.loads(raw_resp.decode("utf-8").strip() or "{}")
            return BrainResult(
                success=True,
                data={"endpoint_id": eid, "command": command, "response": parsed},
            )
        except Exception as exc:
            return BrainResult(
                success=False,
                error=f"CAD endpoint '{eid}' ({host}:{port}) unreachable: {exc}",
            )

    async def _verify_mass_delta(
        self,
        expected_volume_delta_cm3: float = 0.0,
        actual_volume_before_cm3: float | None = None,
        actual_volume_after_cm3: float | None = None,
        actual_mass_before_g: float | None = None,
        actual_mass_after_g: float | None = None,
        material: str = "steel",
        tolerance_pct: float = 2.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Verify CAD feature volume/mass delta against analytical expectation."""
        mat_key = material.strip().lower()
        density = _MATERIAL_DENSITIES_G_CM3.get(mat_key, 7.85)

        if actual_volume_before_cm3 is not None and actual_volume_after_cm3 is not None:
            actual_vol_delta = float(actual_volume_after_cm3) - float(actual_volume_before_cm3)
        elif actual_mass_before_g is not None and actual_mass_after_g is not None:
            mass_delta = float(actual_mass_after_g) - float(actual_mass_before_g)
            actual_vol_delta = mass_delta / density
        else:
            return BrainResult(
                success=False,
                error=(
                    "Provide either (actual_volume_before_cm3, actual_volume_after_cm3) "
                    "or (actual_mass_before_g, actual_mass_after_g)"
                ),
            )

        expected_vol = float(expected_volume_delta_cm3)
        expected_mass_delta = expected_vol * density
        actual_mass_delta = actual_vol_delta * density

        abs_err = abs(actual_vol_delta - expected_vol)
        denom = max(abs(expected_vol), 1e-6)
        err_pct = (abs_err / denom) * 100.0
        verified = err_pct <= float(tolerance_pct) or abs_err <= 1e-4

        return BrainResult(
            success=True,
            data={
                "verified": verified,
                "material": mat_key,
                "density_g_cm3": density,
                "expected_volume_delta_cm3": round(expected_vol, 5),
                "actual_volume_delta_cm3": round(actual_vol_delta, 5),
                "expected_mass_delta_g": round(expected_mass_delta, 4),
                "actual_mass_delta_g": round(actual_mass_delta, 4),
                "error_pct": round(err_pct, 3),
                "tolerance_pct": float(tolerance_pct),
            },
        )

    async def _enclosure_calculator(
        self,
        pcb_width_mm: float = 35.4,
        pcb_height_mm: float = 33.5,
        interior_height_mm: float = 15.0,
        wall_thickness_mm: float = 2.0,
        floor_thickness_mm: float = 2.0,
        clearance_mm: float = 2.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Compute validated 3D-printed enclosure & CNC workholding dimensions."""
        cavity_w_mm = round(float(pcb_width_mm) + float(clearance_mm), 2)
        cavity_h_mm = round(float(pcb_height_mm) + float(clearance_mm), 2)
        outer_w_mm = round(cavity_w_mm + 2.0 * float(wall_thickness_mm), 2)
        outer_h_mm = round(cavity_h_mm + 2.0 * float(wall_thickness_mm), 2)
        total_z_mm = round(float(floor_thickness_mm) + float(interior_height_mm), 2)

        # Cubiko M5 bed grid coordinates (6x5 primary + 4 half-pitch corner holes)
        cubiko_x = [round(7.0 + i * 33.2, 2) for i in range(6)]
        cubiko_y = [round(7.0 + j * 26.5, 2) for j in range(5)]

        return BrainResult(
            success=True,
            data={
                "pcb_mm": {"width": pcb_width_mm, "height": pcb_height_mm},
                "cavity_mm": {
                    "width": cavity_w_mm,
                    "height": cavity_h_mm,
                    "depth": interior_height_mm,
                    "rule": (
                        "Keep internal slide-in cavity a full square-cornered rectangle "
                        "(never chamfer internal corners)."
                    ),
                },
                "outer_shell_mm": {
                    "width": outer_w_mm,
                    "height": outer_h_mm,
                    "total_height": total_z_mm,
                },
                "fusion360_cm": {
                    "outer_rect_origin_cm": [
                        round(-outer_w_mm / 20.0, 4),
                        round(-outer_h_mm / 20.0, 4),
                    ],
                    "outer_rect_size_cm": [
                        round(outer_w_mm / 10.0, 4),
                        round(outer_h_mm / 10.0, 4),
                    ],
                    "shell_z_offset_cm": round(-float(floor_thickness_mm) / 10.0, 4),
                    "shell_extrude_height_cm": round(total_z_mm / 10.0, 4),
                    "cavity_cut_z_offset_cm": 0.0,
                    "cavity_cut_height_cm": round(float(interior_height_mm) / 10.0, 4),
                    "flat_bottom_rule": (
                        "Extrude full outer footprint from z=-floor_t to +interior_h as ONE "
                        "solid, then cut cavity from z=0 up."
                    ),
                },
                "press_fit_references_mm": {
                    "neodymium_magnet_6x2": {"diameter": 6.2, "depth": 2.1},
                    "m2_self_tap_pilot": {"diameter": 1.9},
                    "m3_self_tap_pilot": {"diameter": 2.8, "standoff_od": 6.0},
                    "m5_cubiko_clearance_slot": {"width": 5.4, "counterbore": 10.6},
                },
                "cubiko_bed_grid_mm": {
                    "x_columns": cubiko_x,
                    "y_rows": cubiko_y,
                    "half_pitch_corners": [
                        [23.6, 20.25],
                        [23.6, 99.75],
                        [156.4, 20.25],
                        [156.4, 99.75],
                    ],
                },
            },
        )

    async def _pcb2gcode_command(
        self,
        board_width_mm: float = 50.0,
        gerber_dir: str = "./gerbers",
        output_dir: str = "./cnc_out",
        spindle_rpm: int = 10000,
        **kwargs: Any,
    ) -> BrainResult:
        """Generate verified pcb2gcode CLI invocation and GRBL post-processing command."""
        mirror_axis_mm = round(float(board_width_mm) / 2.0, 3)
        feed_xy = 200 if int(spindle_rpm) >= 15000 else 120
        plunge_z = 45 if int(spindle_rpm) >= 15000 else 30

        cmd = (
            f"pcb2gcode --noconfigfile "
            f"--back={gerber_dir}/B_Cu.gbr --outline={gerber_dir}/Edge_Cuts.gbr "
            f"--drill={gerber_dir}/drills.drl --output-dir={output_dir} "
            f"--metric=1 --metricoutput=1 --zero-start=1 --mirror-axis={mirror_axis_mm}mm "
            f"--mill-diameters=0.20mm --isolation-width=0.45mm --milling-overlap=45% "
            f"--zwork=-0.06mm --mill-feed={feed_xy}mm/min --mill-vertfeed={plunge_z}mm/min "
            f"--mill-speed={int(spindle_rpm)}rpm "
            f"--drills-available=1.0mm --zdrill=-1.80mm --drill-feed=45mm/min "
            f"--nog81=1 --nom6=1 --nog64=1 "
            f"--min-milldrill-hole-diameter=2.5mm --milldrill-diameter=1.0mm --zmilldrill=-1.75mm "
            f"--cutter-diameter=1.0mm --zcut=-1.75mm --cut-infeed=0.45mm "
            f"--cut-feed=120mm/min --cut-vertfeed=30mm/min "
            f"--bridges=2.0mm --bridgesnum=4 --zbridges=-0.3mm --zsafe=1.5mm --zchange=15.0mm"
        )
        post_process = f"sed -i '' -E '/^(T[0-9]+|M0|M00|M6)$/d' {output_dir}/*.nc"

        return BrainResult(
            success=True,
            data={
                "board_width_mm": board_width_mm,
                "mirror_axis_mm": mirror_axis_mm,
                "pcb2gcode_command": cmd,
                "grbl_strip_postprocess": post_process,
                "job_sequence": [
                    "01_isolation_B_Cu.nc (30-deg 0.1mm/0.2mm V-bit, Z=-0.06mm)",
                    "02_drills_1.0mm.nc (1.0mm Ti-coated carbide end mill/drill, Z=-1.80mm)",
                    "02b_mounting_holes_M3.nc (1.0mm end mill helical bore, Z=-1.75mm)",
                    "03_cutout_Edge_Cuts.nc (1.0mm end mill 4-pass tabbed cutout, Z=-1.75mm)",
                ],
            },
        )

    async def _federate_tools(
        self,
        task_query: str = "parametric enclosure",
        max_tools: int = 8,
        **kwargs: Any,
    ) -> BrainResult:
        """Context-window-aware MCP tool multiplexer across Fusion 360, KiCad, and CAM."""
        catalog = [
            {
                "tool": "mcp__fusion360__execute_code",
                "endpoint_id": "fusion360-bench",
                "tags": ["cad", "fusion", "extrude", "sketch", "enclosure", "fillet", "boolean"],
                "verification_gate": "cad_verify_mass_delta",
            },
            {
                "tool": "mcp__fusion360__export_stl",
                "endpoint_id": "fusion360-bench",
                "tags": ["cad", "stl", "export", "3d-print", "enclosure"],
                "verification_gate": "trimesh.is_watertight",
            },
            {
                "tool": "mcp__kicad__batch_add_components",
                "endpoint_id": "kicad-eda",
                "tags": ["pcb", "kicad", "schematic", "electronics", "lcsc"],
                "verification_gate": "mcp__kicad__run_erc",
            },
            {
                "tool": "mcp__kicad__autoroute",
                "endpoint_id": "kicad-eda",
                "tags": ["pcb", "kicad", "route", "freerouting", "layout", "motor"],
                "verification_gate": "kicad-cli pcb drc (errors == 0)",
            },
            {
                "tool": "cam_pcb2gcode_command",
                "endpoint_id": "pcb2gcode-cam",
                "tags": ["cnc", "pcb", "gerber", "gcode", "isolation", "mill"],
                "verification_gate": "device_validate_gcode",
            },
        ]
        q_tokens = {w.lower() for w in task_query.replace("-", " ").split() if len(w) >= 2}
        q_low = task_query.lower()
        scored = sorted(
            catalog,
            key=lambda item: sum(1 for t in item["tags"] if t in q_tokens or t in q_low),
            reverse=True,
        )
        selected = scored[: max(1, int(max_tools))]
        return BrainResult(
            success=True,
            data={
                "task_query": task_query,
                "selected_tools": selected,
                "count": len(selected),
            },
        )

    @staticmethod
    def _box_facets(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> list[str]:
        """Return 12 ASCII STL triangular facets for an axis-aligned box."""
        tris = [
            ((0, 0, -1), (x0, y0, z0), (x1, y1, z0), (x1, y0, z0)),
            ((0, 0, -1), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)),
            ((0, 0, 1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1)),
            ((0, 0, 1), (x0, y0, z1), (x1, y1, z1), (x0, y1, z1)),
            ((0, -1, 0), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)),
            ((0, -1, 0), (x0, y0, z0), (x1, y0, z1), (x0, y0, z1)),
            ((0, 1, 0), (x0, y1, z0), (x1, y1, z1), (x1, y1, z0)),
            ((0, 1, 0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)),
            ((-1, 0, 0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)),
            ((-1, 0, 0), (x0, y0, z0), (x0, y1, z1), (x0, y1, z0)),
            ((1, 0, 0), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)),
            ((1, 0, 0), (x1, y0, z0), (x1, y1, z1), (x1, y0, z1)),
        ]
        out: list[str] = []
        for n, v1, v2, v3 in tris:
            out.append(
                f"  facet normal {n[0]} {n[1]} {n[2]}\n    outer loop\n"
                f"      vertex {v1[0]:.2f} {v1[1]:.2f} {v1[2]:.2f}\n"
                f"      vertex {v2[0]:.2f} {v2[1]:.2f} {v2[2]:.2f}\n"
                f"      vertex {v3[0]:.2f} {v3[1]:.2f} {v3[2]:.2f}\n"
                "    endloop\n  endfacet"
            )
        return out

    async def _generate_aruco_bin_stl(
        self,
        sku: str = "MCU-XIAO-ESP32C6",
        grid_x: int = 1,
        grid_y: int = 2,
        height_u: int = 3,
        **kwargs: Any,
    ) -> BrainResult:
        """Generate printable ASCII STL meshes & 3D isometric SVG for a Gridfinity ArUco bin."""
        from labclaw.brain.skills.vision import aruco_bits_4x4, sku_to_aruco_id

        clean_sku = sku.strip().upper() or "MAKERCLAW-PART"
        aid = sku_to_aruco_id(clean_sku)
        bits = aruco_bits_4x4(aid)

        # 1. Snap-In 2-Color ArUco Tile STL (36x16mm base 0..0.6mm + 6x6 ArUco blocks 0.6..1.2mm)
        tile_facets = self._box_facets(0.0, 0.0, 0.0, 36.0, 16.0, 0.6)
        for r in range(6):
            for c in range(6):
                is_black = r in (0, 5) or c in (0, 5) or bits[r - 1][c - 1] == 0
                if is_black:
                    bx = 2.0 + c * 2.0
                    by = 2.0 + (5 - r) * 2.0
                    tile_facets.extend(self._box_facets(bx, by, 0.6, bx + 2.0, by + 2.0, 1.2))
        tile_stl = (
            f"solid aruco_tile_{aid}\n" + "\n".join(tile_facets) + f"\nendsolid aruco_tile_{aid}\n"
        )

        # 2. Hollow Gridfinity Bin STL (floor + 4 walls + top front label bridge)
        wx = max(1, int(grid_x)) * 42.0
        wy = max(1, int(grid_y)) * 42.0
        hz = max(2, int(height_u)) * 7.0
        bin_facets = (
            self._box_facets(0.0, 0.0, 0.0, wx, wy, 2.4)
            + self._box_facets(0.0, 0.0, 2.4, wx, 2.0, hz)
            + self._box_facets(0.0, wy - 2.0, 2.4, wx, wy, hz)
            + self._box_facets(0.0, 2.0, 2.4, 2.0, wy - 2.0, hz)
            + self._box_facets(wx - 2.0, 2.0, 2.4, wx, wy - 2.0, hz)
            + self._box_facets(2.0, 2.0, hz - 2.2, wx - 2.0, 16.0, hz)
        )
        bin_code = f"GF-{max(1, int(grid_x))}x{max(1, int(grid_y))}x{max(2, int(height_u))}U"
        bin_stl = f"solid {bin_code}\n" + "\n".join(bin_facets) + f"\nendsolid {bin_code}\n"

        return BrainResult(
            success=True,
            data={
                "sku": clean_sku,
                "aruco_id": aid,
                "bin_code": bin_code,
                "bin_dimensions_mm": {"x": wx, "y": wy, "z": hz},
                "tile_facet_count": len(tile_facets),
                "bin_facet_count": len(bin_facets),
                "tile_stl": tile_stl,
                "bin_stl": bin_stl,
            },
        )

    async def list_tools(self) -> list[ToolInfo]:
        """Return all CAD/EDA/CAM tools."""
        return [
            ToolInfo(
                name="cad_endpoints",
                description=(
                    "List MCP-enabled CAD, EDA, and CAM endpoints (Fusion 360, KiCad, pcb2gcode)."
                ),
                skill="cad_mcp",
                category="cad",
            ),
            ToolInfo(
                name="cad_register_endpoint",
                description="Register a new MCP CAD/EDA/CAM endpoint (TCP socket, stdio, or CLI).",
                skill="cad_mcp",
                category="cad",
            ),
            ToolInfo(
                name="cad_bridge_call",
                description="Send a command to a registered CAD/EDA MCP endpoint or socket server.",
                skill="cad_mcp",
                category="cad",
            ),
            ToolInfo(
                name="cad_verify_mass_delta",
                description=(
                    "Verify CAD feature volume/mass delta against analytical expectation "
                    "(steel, PLA, 6061 aluminum, C360 brass, FR-4)."
                ),
                skill="cad_mcp",
                category="cad",
            ),
            ToolInfo(
                name="cad_enclosure_calculator",
                description=(
                    "Compute validated 3D-printed flat-bottom enclosure dimensions, PCB slide-in "
                    "clearances, magnet press-fits, and Cubiko M5 bed coordinates."
                ),
                skill="cad_mcp",
                category="cad",
            ),
            ToolInfo(
                name="cam_pcb2gcode_command",
                description=(
                    "Generate verified pcb2gcode CLI command and GRBL post-processor for "
                    "in-house CNC PCB isolation milling, drilling, and cutout."
                ),
                skill="cad_mcp",
                category="cnc",
            ),
            ToolInfo(
                name="cad_federate_tools",
                description=(
                    "Active MCP multiplexer: select relevant Fusion 360, KiCad, and CAM tools "
                    "for a task with mandatory verification gates."
                ),
                skill="cad_mcp",
                category="cad",
            ),
            ToolInfo(
                name="cad_generate_aruco_bin_stl",
                description=(
                    "Generate printable ASCII STL meshes for a Gridfinity bin and its "
                    "2-color snap-in 4x4 ArUco fiducial tile."
                ),
                skill="cad_mcp",
                category="cad",
            ),
        ]

    async def health_check(self) -> bool:
        """Return True when CAD endpoint catalog is loaded."""
        return len(self._endpoints) > 0
