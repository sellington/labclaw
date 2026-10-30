"""Unit tests for DevicesSkill (100% coverage)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from labclaw.brain.skills.devices import DevicesSkill


class TestDevicesSkill:
    async def test_list_and_register_devices(self) -> None:
        skill = DevicesSkill()
        assert await skill.health_check() is True

        all_devs = await skill.execute("device_list")
        assert all_devs.success is True
        assert all_devs.data["count"] >= 4

        cnc_only = await skill.execute("device_list", device_type="cnc")
        assert cnc_only.data["count"] == 1
        assert cnc_only.data["devices"][0]["device_id"] == "cubiko-cnc"

        err_reg = await skill.execute("device_register", device_id="", name="")
        assert err_reg.success is False

        ok_reg = await skill.execute(
            "device_register",
            device_id="prusa-mk4",
            name="Prusa MK4",
            device_type="3d_printer",
            protocol="octoprint",
            endpoint="http://192.0.2.10:5000",
        )
        assert ok_reg.success is True
        assert ok_reg.data["device_id"] == "prusa-mk4"

    async def test_unknown_tool(self) -> None:
        skill = DevicesSkill()
        res = await skill.execute("bad_tool")
        assert res.success is False

    async def test_device_status_and_http_probes(self) -> None:
        skill = DevicesSkill()

        missing = await skill.execute("device_status", device_id="no-such-device")
        assert missing.success is False

        # Status without network probe
        st = await skill.execute("device_status", device_id="cubiko-cnc", probe_network=False)
        assert st.success is True
        assert st.data["device_id"] == "cubiko-cnc"

        # Status with gSender HTTP probe
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"token": "jwt123", "state": "idle"}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_cm):
            gs = await skill.execute("device_status", device_id="cubiko-cnc", probe_network=True)
            assert gs.data["live_probe"]["reachable"] is True

            mr = await skill.execute("device_status", device_id="voron-klipper", probe_network=True)
            assert mr.data["live_probe"]["reachable"] is True

            await skill.execute(
                "device_register",
                device_id="octo-1",
                name="Octo",
                protocol="octoprint",
                endpoint="http://127.0.0.1:5000",
            )
            oc = await skill.execute("device_status", device_id="octo-1", probe_network=True)
            assert oc.data["live_probe"]["reachable"] is True

        # Network probe exception path
        mock_client.get.side_effect = RuntimeError("timeout")
        mock_client.post.side_effect = RuntimeError("timeout")
        with patch("httpx.AsyncClient", return_value=mock_cm):
            fail_probe = await skill.execute(
                "device_status", device_id="cubiko-cnc", probe_network=True
            )
            assert fail_probe.data["live_probe"]["reachable"] is False

    async def test_validate_gcode_cnc_and_printer(self) -> None:
        skill = DevicesSkill()

        empty = await skill.execute("device_validate_gcode", gcode="   ")
        assert empty.success is False

        # Valid CNC gcode
        good_cnc = await skill.execute(
            "device_validate_gcode",
            device_id="cubiko-cnc",
            gcode=(
                "; header comment\n(another comment)\nG21\n"
                "M3 S10000\nG0 X10 Y10 Z2.0\nG1 X50 Y40 Z-0.5 F120\n"
            ),
        )
        assert good_cnc.success is True
        assert good_cnc.data["safe"] is True

        # Invalid CNC gcode: T1, M0, envelope exceeded, flute exceeded, no spoilboard, over RPM
        bad_cnc = await skill.execute(
            "device_validate_gcode",
            device_id="cubiko-cnc",
            spoilboard_present=False,
            max_flute_length_mm=7.0,
            gcode="T1 M6\nM0\nM3 S25000\nG0 X200 Y150 Z50\nG1 Z-8.5 F200\n",
        )
        assert bad_cnc.data["safe"] is False
        assert len(bad_cnc.data["violations"]) >= 6
        assert len(bad_cnc.data["warnings"]) == 1

        # 3D printer temperature validation
        bad_print = await skill.execute(
            "device_validate_gcode",
            device_id="bambu-p1s",
            gcode="M104 S350\nM140 S130\nG1 X10 Y10 Z0.2 F1200\n",
        )
        assert bad_print.data["safe"] is False
        assert len(bad_print.data["violations"]) == 2

    async def test_send_command_and_safety_gates(self) -> None:
        skill = DevicesSkill()

        missing = await skill.execute("device_send_command", device_id="missing", action="home")
        assert missing.success is False

        # Emergency stop always succeeds
        estop = await skill.execute(
            "device_send_command", device_id="cubiko-cnc", action="emergency_stop"
        )
        assert estop.success is True
        assert estop.data["status"] == "stopped"

        # Offline device blocked
        skill._devices["cubiko-cnc"]["status"] = "offline"
        blocked = await skill.execute("device_send_command", device_id="cubiko-cnc", action="home")
        assert blocked.success is False

        # Restore idle status
        skill._devices["cubiko-cnc"]["status"] = "idle"

        # Unsupported capability blocked
        bad_cap = await skill.execute(
            "device_send_command", device_id="cubiko-cnc", action="laser_fire"
        )
        assert bad_cap.success is False

        # Unsafe G-code blocked
        unsafe_cmd = await skill.execute(
            "device_send_command",
            device_id="cubiko-cnc",
            action="run_gcode",
            parameters={"gcode": "T1 M6\nG0 X999"},
        )
        assert unsafe_cmd.success is False

        # Safe G-code passes
        safe_cmd = await skill.execute(
            "device_send_command",
            device_id="cubiko-cnc",
            action="run_gcode",
            parameters={"gcode": "G0 X10 Y10 Z2"},
        )
        assert safe_cmd.success is True
        assert safe_cmd.data["safety_check"] == "passed"

    async def test_feeds_and_speeds(self) -> None:
        skill = DevicesSkill()

        exact = await skill.execute(
            "device_feeds_and_speeds", material="fr4_isolation", spindle_rpm=20000
        )
        assert exact.success is True
        assert exact.data["spindle_setting"]["spindle_rpm"] == 20000

        fuzzy = await skill.execute("device_feeds_and_speeds", material="6061", spindle_rpm=10000)
        assert fuzzy.success is True
        assert fuzzy.data["profile_key"] == "aluminum_6061"

        unknown = await skill.execute("device_feeds_and_speeds", material="unobtainium")
        assert unknown.success is False

    async def test_list_tools(self) -> None:
        skill = DevicesSkill()
        tools = await skill.list_tools()
        assert len(tools) == 6
