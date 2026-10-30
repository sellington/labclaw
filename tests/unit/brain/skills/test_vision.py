"""Unit tests for VisionSkill (100% coverage)."""

from __future__ import annotations

from labclaw.brain.skills.vision import VisionSkill, aruco_bits_4x4, sku_to_aruco_id


class TestVisionSkill:
    async def test_aruco_helpers(self) -> None:
        aid = sku_to_aruco_id("MCU-XIAO-ESP32C6")
        assert 100 <= aid <= 999
        bits = aruco_bits_4x4(aid)
        assert len(bits) == 4
        assert all(len(r) == 4 for r in bits)

    async def test_camera_profile_and_calibrate_homography(self) -> None:
        skill = VisionSkill()
        assert await skill.health_check() is True

        unknown = await skill.execute("no_such_vision_tool")
        assert unknown.success is False

        prof = await skill.execute("vision_camera_profile", width_px=1280, height_px=720)
        assert prof.success is True
        assert prof.data["px_per_mm"]["x"] == 3.2

        bad_cal = await skill.execute("vision_calibrate_homography", x_min_mm=300.0, x_max_mm=100.0)
        assert bad_cal.success is False

        ok_cal = await skill.execute(
            "vision_calibrate_homography",
            x_min_mm=80.0,
            x_max_mm=305.0,
            y_min_mm=-200.0,
            y_max_mm=200.0,
        )
        assert ok_cal.success is True
        assert ok_cal.data["optical_center_mm"]["y_mm"] == 0.0

    async def test_scan_bench_and_uarm_pick_and_place(self) -> None:
        skill = VisionSkill()

        # Default detections
        scan1 = await skill.execute("vision_scan_bench")
        assert scan1.success is True
        assert scan1.data["count"] == 2
        assert "<svg" in scan1.data["svg"]

        # Custom detections
        scan2 = await skill.execute(
            "vision_scan_bench",
            detections=[{"sku": "TEST-1", "u": 640, "v": 360, "angle_deg": 45.0}],
        )
        assert scan2.success is True
        assert scan2.data["detected_bins"][0]["uarm_reachable"] is True

        # Valid uArm pick & place from pixel coordinates
        pp_ok = await skill.execute(
            "vision_uarm_pick_and_place",
            pick_u=420.0,
            pick_v=460.0,
            place_u=820.0,
            place_v=340.0,
            end_effector="suction",
        )
        assert pp_ok.success is True
        assert "M2231 V1" in pp_ok.data["gcode"]

        # Gripper end effector
        pp_grip = await skill.execute(
            "vision_uarm_pick_and_place",
            pick_x_mm=180.0,
            pick_y_mm=0.0,
            place_x_mm=200.0,
            place_y_mm=50.0,
            end_effector="gripper",
        )
        assert pp_grip.success is True
        assert "M2232 V1" in pp_grip.data["gcode"]

        # Out-of-reach & invalid Z violations
        pp_bad = await skill.execute(
            "vision_uarm_pick_and_place",
            pick_x_mm=10.0,
            pick_y_mm=0.0,
            place_x_mm=500.0,
            place_y_mm=0.0,
            pick_z_mm=-5.0,
        )
        assert pp_bad.success is False
        assert "outside uArm reach" in (pp_bad.error or "")

    async def test_measure_stock_and_list_tools(self) -> None:
        skill = VisionSkill()

        fit_norm = await skill.execute(
            "vision_measure_stock",
            stock_width_mm=100.0,
            stock_height_mm=70.0,
            job_width_mm=50.0,
            job_height_mm=40.0,
        )
        assert fit_norm.success is True
        assert fit_norm.data["fits"] is True
        assert fit_norm.data["rotate_90_deg"] is False

        fit_rot = await skill.execute(
            "vision_measure_stock",
            stock_width_mm=55.0,
            stock_height_mm=95.0,
            job_width_mm=80.0,
            job_height_mm=40.0,
        )
        assert fit_rot.data["fits"] is True
        assert fit_rot.data["rotate_90_deg"] is True

        tools = await skill.list_tools()
        assert len(tools) == 5
