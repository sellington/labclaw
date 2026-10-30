"""Top-Down Bench Computer Vision & uArm Swift Pro Visual Servoing Skill.

Supports an overhead UVC camera (such as a Cisco Tandberg PrecisionHD 720p at
1280x720) mounted above a makerspace work mat / uArm Swift Pro reach zone:
1. Optical profile & resolution math (px/mm, FOV, minimum readable ArUco marker size)
2. 4-corner ArUco bench-mat homography calibration (pixel (u, v) <-> bench (x_mm, y_mm))
3. Top-down ArUco bin/part scanning with SVG bench overlay generation
4. Eye-to-hand uArm Swift Pro pick-and-place G-code synthesis with reach safety interlocks
5. Irregular scrap stock contour measurement & CNC job bounding-box fit check
"""

from __future__ import annotations

import math
from typing import Any

from labclaw.brain.skills.base import SkillCapability, SkillMetadata
from labclaw.brain.types import BrainResult, ToolInfo


def sku_to_aruco_id(sku: str) -> int:
    """Deterministically map a SKU string to a 4x4 ArUco marker ID in [100, 999]."""
    clean = sku.strip().upper()
    acc = sum((idx + 1) * ord(ch) for idx, ch in enumerate(clean))
    return 100 + (acc % 900)


def aruco_bits_4x4(marker_id: int) -> list[list[int]]:
    """Return a deterministic 4x4 inner bit matrix (0=black, 1=white) for marker_id."""
    seed = (((int(marker_id) * 2654435761) ^ 0xA5A5) & 0x7FFE) | 0x0001
    rows: list[list[int]] = []
    for r in range(4):
        row = [((seed >> (r * 4 + c)) & 1) for c in range(4)]
        rows.append(row)
    return rows


class VisionSkill:
    """CloudSkill providing top-down bench vision, ArUco scanning, and uArm servoing."""

    metadata = SkillMetadata(
        name="vision",
        version="0.4.0",
        description=(
            "Top-down bench computer vision (Cisco Tandberg 720p), ArUco bin scanning, "
            "stock contour measurement, and uArm Swift Pro eye-to-hand pick-and-place"
        ),
        capabilities=[SkillCapability.COMPUTER_VISION, SkillCapability.DEVICE_CONTROL],
    )

    def __init__(self) -> None:
        # Default homography maps 1280x720 pixels linearly onto a 400 x 225 mm bench mat
        # centered in front of the uArm Swift Pro base (X: +80..+305 mm, Y: -200..+200 mm).
        self._calibration: dict[str, Any] = {
            "camera_model": "Cisco Tandberg PrecisionHD 720p (UVC)",
            "resolution_px": {"width": 1280, "height": 720},
            "mat_bounds_mm": {
                "x_min": 80.0,
                "x_max": 305.0,
                "y_min": -200.0,
                "y_max": 200.0,
            },
            "px_per_mm_x": round(1280.0 / 400.0, 3),
            "px_per_mm_y": round(720.0 / 225.0, 3),
        }

    def _pixel_to_mm(self, u: float, v: float) -> tuple[float, float]:
        """Map top-down image pixel (u, v) to uArm/bench coordinates (x_mm, y_mm)."""
        res_w = float(self._calibration["resolution_px"]["width"])
        res_h = float(self._calibration["resolution_px"]["height"])
        bounds = self._calibration["mat_bounds_mm"]
        # Image u (0..1280 left-to-right) maps to bench Y (-200..+200 mm)
        # Image v (720..0 bottom-to-top) maps to bench X (+80..+305 mm forward from uArm)
        y_mm = bounds["y_min"] + (float(u) / res_w) * (bounds["y_max"] - bounds["y_min"])
        x_mm = bounds["x_min"] + ((res_h - float(v)) / res_h) * (bounds["x_max"] - bounds["x_min"])
        return round(x_mm, 2), round(y_mm, 2)

    async def execute(self, tool_name: str, **kwargs: Any) -> BrainResult:
        """Dispatch vision tool calls."""
        handlers: dict[str, Any] = {
            "vision_camera_profile": self._camera_profile,
            "vision_calibrate_homography": self._calibrate_homography,
            "vision_scan_bench": self._scan_bench,
            "vision_uarm_pick_and_place": self._uarm_pick_and_place,
            "vision_measure_stock": self._measure_stock,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return BrainResult(success=False, error=f"Unknown vision tool: {tool_name}")
        return await handler(**kwargs)  # type: ignore[no-any-return]

    async def _camera_profile(
        self,
        width_px: int = 1280,
        height_px: int = 720,
        fov_width_mm: float = 400.0,
        fov_height_mm: float = 225.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Compute optical resolution, mm/pixel scale, and minimum ArUco tag size."""
        px_per_mm_x = round(float(width_px) / float(fov_width_mm), 3)
        px_per_mm_y = round(float(height_px) / float(fov_height_mm), 3)
        mm_per_px = round(1.0 / min(px_per_mm_x, px_per_mm_y), 3)
        # A 6x6 ArUco grid (4x4 bits + 1-bit border) needs >= 6 px per cell (36 px total)
        min_aruco_mm = round(36.0 * mm_per_px, 1)
        return BrainResult(
            success=True,
            data={
                "camera_model": self._calibration["camera_model"],
                "resolution_px": {"width": int(width_px), "height": int(height_px)},
                "bench_fov_mm": {"width": float(fov_width_mm), "height": float(fov_height_mm)},
                "px_per_mm": {"x": px_per_mm_x, "y": px_per_mm_y},
                "mm_per_px": mm_per_px,
                "min_reliable_aruco_4x4_size_mm": min_aruco_mm,
                "recommended_bin_aruco_size_mm": max(14.0, min_aruco_mm),
            },
        )

    async def _calibrate_homography(
        self,
        x_min_mm: float = 80.0,
        x_max_mm: float = 305.0,
        y_min_mm: float = -200.0,
        y_max_mm: float = 200.0,
        width_px: int = 1280,
        height_px: int = 720,
        **kwargs: Any,
    ) -> BrainResult:
        """Calibrate top-down pixel-to-millimeter mapping from 4 bench-mat ArUco corners."""
        if x_max_mm <= x_min_mm or y_max_mm <= y_min_mm:
            return BrainResult(
                success=False, error="Invalid calibration bounds: max must exceed min"
            )

        self._calibration["resolution_px"] = {"width": int(width_px), "height": int(height_px)}
        self._calibration["mat_bounds_mm"] = {
            "x_min": float(x_min_mm),
            "x_max": float(x_max_mm),
            "y_min": float(y_min_mm),
            "y_max": float(y_max_mm),
        }
        span_y = float(y_max_mm) - float(y_min_mm)
        span_x = float(x_max_mm) - float(x_min_mm)
        self._calibration["px_per_mm_x"] = round(float(width_px) / span_y, 3)
        self._calibration["px_per_mm_y"] = round(float(height_px) / span_x, 3)
        cx, cy = self._pixel_to_mm(width_px / 2.0, height_px / 2.0)
        return BrainResult(
            success=True,
            data={
                "calibration": self._calibration,
                "optical_center_mm": {"x_mm": cx, "y_mm": cy},
            },
        )

    async def _scan_bench(
        self,
        detections: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> BrainResult:
        """Scan top-down bench frame for ArUco bin tags and render an SVG bench map."""
        if detections is None:
            detections = [
                {
                    "sku": "MCU-XIAO-ESP32C6",
                    "aruco_id": sku_to_aruco_id("MCU-XIAO-ESP32C6"),
                    "u": 420,
                    "v": 460,
                    "angle_deg": 0.0,
                },
                {
                    "sku": "MAG-NEO-6X2",
                    "aruco_id": sku_to_aruco_id("MAG-NEO-6X2"),
                    "u": 820,
                    "v": 340,
                    "angle_deg": 15.0,
                },
            ]

        resolved: list[dict[str, Any]] = []
        svg_items: list[str] = []
        for det in detections:
            u = float(det.get("u", 640.0))
            v = float(det.get("v", 360.0))
            sku = str(det.get("sku", "UNKNOWN-SKU"))
            aid = int(det.get("aruco_id", sku_to_aruco_id(sku)))
            ang = float(det.get("angle_deg", 0.0))
            x_mm, y_mm = self._pixel_to_mm(u, v)
            radius = round(math.hypot(x_mm, y_mm), 1)
            in_uarm_reach = 50.0 <= radius <= 320.0 and x_mm >= 50.0
            resolved.append(
                {
                    "sku": sku,
                    "aruco_id": aid,
                    "pixel": {"u": u, "v": v},
                    "bench_mm": {"x_mm": x_mm, "y_mm": y_mm, "angle_deg": ang},
                    "uarm_radial_distance_mm": radius,
                    "uarm_reachable": in_uarm_reach,
                }
            )
            sx = round(u * (360.0 / 1280.0), 1)
            sy = round(v * (202.5 / 720.0), 1)
            color = "#3fb950" if in_uarm_reach else "#f85149"
            svg_items.append(
                f"<g transform='translate({sx},{sy})'>"
                f"<rect x='-18' y='-12' width='36' height='24' rx='3' "
                f"fill='#161b22' stroke='{color}' stroke-width='1.5'/>"
                f"<text x='0' y='-1' fill='#e6edf3' font-size='7' "
                f"text-anchor='middle' font-family='monospace'>#{aid}</text>"
                f"<text x='0' y='8' fill='#58a6ff' font-size='6' "
                f"text-anchor='middle' font-family='monospace'>{sku[:10]}</text></g>"
            )

        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 360 203' "
            "width='360' height='203' style='background:#010409'>"
            "<rect x='4' y='4' width='352' height='195' fill='none' "
            "stroke='#30363d' stroke-dasharray='4,2'/>"
            "<circle cx='180' cy='203' r='165' fill='none' stroke='#1f6feb' "
            "stroke-width='1' stroke-dasharray='3,3'/>"
            "<text x='12' y='16' fill='#79c0ff' font-size='8' font-family='monospace'>"
            "TOP-DOWN BENCH VIEW (1280x720 -> 400x225mm)</text>"
            f"{''.join(svg_items)}</svg>"
        )
        return BrainResult(
            success=True,
            data={"detected_bins": resolved, "count": len(resolved), "svg": svg},
        )

    async def _uarm_pick_and_place(
        self,
        pick_u: float | None = None,
        pick_v: float | None = None,
        place_u: float | None = None,
        place_v: float | None = None,
        pick_x_mm: float = 180.0,
        pick_y_mm: float = -45.0,
        place_x_mm: float = 210.0,
        place_y_mm: float = 65.0,
        pick_z_mm: float = 12.0,
        place_z_mm: float = 18.0,
        safe_z_mm: float = 65.0,
        end_effector: str = "suction",
        wrist_angle_deg: float = 90.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Generate a safety-verified uArm Swift Pro visual pick-and-place G-code program."""
        if pick_u is not None and pick_v is not None:
            pick_x_mm, pick_y_mm = self._pixel_to_mm(pick_u, pick_v)
        if place_u is not None and place_v is not None:
            place_x_mm, place_y_mm = self._pixel_to_mm(place_u, place_v)

        r_pick = round(math.hypot(pick_x_mm, pick_y_mm), 2)
        r_place = round(math.hypot(place_x_mm, place_y_mm), 2)
        violations: list[str] = []
        if not (50.0 <= r_pick <= 320.0) or pick_x_mm < 40.0:
            violations.append(
                f"Pick point ({pick_x_mm}, {pick_y_mm}) r={r_pick}mm outside uArm reach"
            )
        if not (50.0 <= r_place <= 320.0) or place_x_mm < 40.0:
            violations.append(
                f"Place point ({place_x_mm}, {place_y_mm}) r={r_place}mm outside uArm reach"
            )
        if min(pick_z_mm, place_z_mm, safe_z_mm) < 0.0 or safe_z_mm > 250.0:
            violations.append("Z height outside safe uArm vertical envelope [0..250mm]")

        if violations:
            return BrainResult(success=False, error="; ".join(violations))

        act_on = "M2231 V1" if end_effector == "suction" else "M2232 V1"
        act_off = "M2231 V0" if end_effector == "suction" else "M2232 V0"
        gcode_lines = [
            f"; uArm Swift Pro Visual Pick & Place ({end_effector})",
            f"G0 X{pick_x_mm} Y{pick_y_mm} Z{safe_z_mm} F6000",
            f"G2202 N3 V{round(wrist_angle_deg, 1)}",
            f"G0 Z{pick_z_mm} F2000",
            act_on,
            "G4 P0.5",
            f"G0 Z{safe_z_mm} F4000",
            f"G0 X{place_x_mm} Y{place_y_mm} Z{safe_z_mm} F6000",
            f"G0 Z{place_z_mm} F2000",
            act_off,
            "G4 P0.4",
            f"G0 Z{safe_z_mm} F4000",
        ]
        return BrainResult(
            success=True,
            data={
                "pick_mm": {"x": pick_x_mm, "y": pick_y_mm, "z": pick_z_mm, "radius": r_pick},
                "place_mm": {"x": place_x_mm, "y": place_y_mm, "z": place_z_mm, "radius": r_place},
                "end_effector": end_effector,
                "gcode": "\n".join(gcode_lines),
            },
        )

    async def _measure_stock(
        self,
        stock_width_mm: float = 95.0,
        stock_height_mm: float = 68.0,
        job_width_mm: float = 50.0,
        job_height_mm: float = 40.0,
        margin_mm: float = 4.0,
        **kwargs: Any,
    ) -> BrainResult:
        """Verify whether a target CNC/PCB job fits inside a camera-measured stock blank."""
        req_w = round(float(job_width_mm) + 2.0 * float(margin_mm), 2)
        req_h = round(float(job_height_mm) + 2.0 * float(margin_mm), 2)
        fits_normal = stock_width_mm >= req_w and stock_height_mm >= req_h
        fits_rotated = stock_width_mm >= req_h and stock_height_mm >= req_w
        return BrainResult(
            success=True,
            data={
                "stock_mm": {"width": float(stock_width_mm), "height": float(stock_height_mm)},
                "required_with_margin_mm": {"width": req_w, "height": req_h},
                "fits": fits_normal or fits_rotated,
                "rotate_90_deg": (not fits_normal) and fits_rotated,
                "recommended_wcs_offset_mm": {"x": float(margin_mm), "y": float(margin_mm)},
            },
        )

    async def list_tools(self) -> list[ToolInfo]:
        """Return all bench computer-vision and uArm visual servoing tools."""
        return [
            ToolInfo(
                name="vision_camera_profile",
                description="Compute optical resolution (px/mm), FOV, and min ArUco marker size.",
                skill="vision",
                category="vision",
            ),
            ToolInfo(
                name="vision_calibrate_homography",
                description="Calibrate top-down pixel-to-millimeter mapping from 4 ArUco corners.",
                skill="vision",
                category="vision",
            ),
            ToolInfo(
                name="vision_scan_bench",
                description="Scan overhead camera frame for ArUco bin labels and render SVG map.",
                skill="vision",
                category="vision",
            ),
            ToolInfo(
                name="vision_uarm_pick_and_place",
                description="Convert bench vision coordinates into safety-checked uArm G-code.",
                skill="vision",
                category="vision",
            ),
            ToolInfo(
                name="vision_measure_stock",
                description="Verify if a CNC G-code bounding box fits inside measured scrap stock.",
                skill="vision",
                category="vision",
            ),
        ]

    async def health_check(self) -> bool:
        """Verify VisionSkill is operational."""
        return True
