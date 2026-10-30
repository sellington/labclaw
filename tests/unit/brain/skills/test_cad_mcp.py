"""Unit tests for CadMcpSkill (100% coverage)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from labclaw.brain.skills.cad_mcp import CadMcpSkill


class TestCadMcpSkill:
    async def test_list_and_register_endpoints(self) -> None:
        skill = CadMcpSkill()
        assert await skill.health_check() is True

        res = await skill.execute("cad_endpoints")
        assert res.success is True
        assert res.data["count"] >= 4

        filtered = await skill.execute("cad_endpoints", domain="eda_pcb")
        assert filtered.data["count"] == 1

        # With probe=True
        with patch.object(skill, "_probe_tcp", new_callable=AsyncMock, return_value=True):
            probed = await skill.execute("cad_endpoints", probe=True)
            assert all(ep["reachable"] is True for ep in probed.data["endpoints"])

        bad_reg = await skill.execute("cad_register_endpoint", endpoint_id="", name="")
        assert bad_reg.success is False

        ok_reg = await skill.execute(
            "cad_register_endpoint",
            endpoint_id="openscad-cli",
            name="OpenSCAD Headless",
            domain="cad_cam",
            transport="cli",
            port=0,
        )
        assert ok_reg.success is True
        assert ok_reg.data["endpoint_id"] == "openscad-cli"

    async def test_unknown_tool(self) -> None:
        skill = CadMcpSkill()
        res = await skill.execute("unknown_cad_tool")
        assert res.success is False

    async def test_probe_tcp_success_and_failure(self) -> None:
        skill = CadMcpSkill()
        mock_writer = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            new_callable=AsyncMock,
            return_value=(MagicMock(), mock_writer),
        ):
            assert await skill._probe_tcp("127.0.0.1", 9876) is True

        with patch(
            "asyncio.open_connection",
            new_callable=AsyncMock,
            side_effect=OSError("refused"),
        ):
            assert await skill._probe_tcp("127.0.0.1", 9876) is False

    async def test_bridge_call_tcp_and_stdio(self) -> None:
        skill = CadMcpSkill()

        missing = await skill.execute("cad_bridge_call", endpoint_id="no-endpoint")
        assert missing.success is False

        # Non-TCP endpoint returns delegation info
        stdio_res = await skill.execute(
            "cad_bridge_call", endpoint_id="kicad-eda", command="run_drc"
        )
        assert stdio_res.success is True
        assert stdio_res.data["delegated_tool"] == "mcp__kicad__run_drc"

        # TCP endpoint success
        mock_reader = AsyncMock()
        mock_reader.readline.return_value = b'{"pong": true}\n'
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            new_callable=AsyncMock,
            return_value=(mock_reader, mock_writer),
        ):
            tcp_ok = await skill.execute(
                "cad_bridge_call", endpoint_id="fusion360-bench", command="ping"
            )
            assert tcp_ok.success is True
            assert tcp_ok.data["response"] == {"pong": True}

        # TCP endpoint failure
        with patch(
            "asyncio.open_connection",
            new_callable=AsyncMock,
            side_effect=OSError("connect timeout"),
        ):
            tcp_err = await skill.execute(
                "cad_bridge_call", endpoint_id="fusion360-bench", command="ping"
            )
            assert tcp_err.success is False

    async def test_verify_mass_delta(self) -> None:
        skill = CadMcpSkill()

        err = await skill.execute("cad_verify_mass_delta", expected_volume_delta_cm3=1.0)
        assert err.success is False

        vol_ok = await skill.execute(
            "cad_verify_mass_delta",
            expected_volume_delta_cm3=2.5,
            actual_volume_before_cm3=10.0,
            actual_volume_after_cm3=12.5,
            material="pla",
        )
        assert vol_ok.success is True
        assert vol_ok.data["verified"] is True

        mass_ok = await skill.execute(
            "cad_verify_mass_delta",
            expected_volume_delta_cm3=1.0,
            actual_mass_before_g=0.0,
            actual_mass_after_g=7.85,
            material="steel",
        )
        assert mass_ok.success is True
        assert mass_ok.data["verified"] is True

    async def test_enclosure_and_pcb2gcode_calculators(self) -> None:
        skill = CadMcpSkill()

        enc = await skill.execute("cad_enclosure_calculator", pcb_width_mm=35.4, pcb_height_mm=33.5)
        assert enc.success is True
        assert enc.data["cavity_mm"]["width"] == 37.4
        assert len(enc.data["cubiko_bed_grid_mm"]["x_columns"]) == 6

        p2g = await skill.execute("cam_pcb2gcode_command", board_width_mm=40.0, spindle_rpm=20000)
        assert p2g.success is True
        assert "--mirror-axis=20.0mm" in p2g.data["pcb2gcode_command"]

        tools = await skill.list_tools()
        assert len(tools) == 6
