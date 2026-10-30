"""Tests for Makerspace REST endpoints, MCP tools, CLI subcommands, and brain init."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

import labclaw.brain as brain_mod
from labclaw.brain.server import _reset_api_keys, app
from labclaw.brain.skills.registry import SkillRegistry
from labclaw.cli import main
from labclaw.mcp.server import (
    labclaw_cad,
    labclaw_devices,
    labclaw_docs,
    labclaw_inventory,
)


@pytest.fixture(autouse=True)
def _reset_state():
    brain_mod._registry = None
    _reset_api_keys()
    yield
    brain_mod._registry = None
    _reset_api_keys()


@pytest.fixture()
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestBrainRegisterDefaultsExceptions:
    def test_handles_makerspace_skill_init_failures(self) -> None:
        reg = SkillRegistry()
        with (
            patch(
                "labclaw.brain.skills.inventory.InventorySkill",
                side_effect=RuntimeError("db fail"),
            ),
            patch(
                "labclaw.brain.skills.devices.DevicesSkill",
                side_effect=RuntimeError("dev fail"),
            ),
            patch(
                "labclaw.brain.skills.cad_mcp.CadMcpSkill",
                side_effect=RuntimeError("cad fail"),
            ),
            patch(
                "labclaw.brain.skills.docs.DocsSkill",
                side_effect=RuntimeError("docs fail"),
            ),
        ):
            brain_mod._register_defaults(reg)

        assert "inventory" not in reg.list_skills()
        assert "devices" not in reg.list_skills()
        assert "cad_mcp" not in reg.list_skills()
        assert "docs" not in reg.list_skills()

    def test_apply_shop_profile_missing_and_valid(self, tmp_path, monkeypatch) -> None:
        reg = SkillRegistry()
        missing = brain_mod.apply_shop_profile(reg, tmp_path / "nope.yaml")
        assert missing == {"inventory": 0, "devices": 0, "cad_endpoints": 0, "docs": 0}

        profile_file = tmp_path / "shop.yaml"
        profile_file.write_text(
            "inventory:\n"
            "  - sku: CUSTOM-1\n"
            "    name: Custom Part\n"
            "    category: electronics\n"
            "    quantity: 5\n"
            "devices:\n"
            "  - device_id: custom-printer\n"
            "    name: Custom Printer\n"
            "    device_type: 3d_printer\n"
            "cad_endpoints:\n"
            "  - endpoint_id: custom-cad\n"
            "    name: Custom CAD\n"
            "docs:\n"
            "  - slug: custom-sop\n"
            "    title: Custom SOP\n"
            "    category: sop\n"
            "    content: '# Custom'\n"
        )
        monkeypatch.setenv("LABCLAW_PROFILE", str(profile_file))
        brain_mod._register_defaults(reg)
        assert "custom-printer" in reg._skills["devices"]._devices  # type: ignore[attr-defined]
        assert "custom-cad" in reg._skills["cad_mcp"]._endpoints  # type: ignore[attr-defined]
        assert "custom-sop" in reg._skills["docs"]._docs  # type: ignore[attr-defined]


class TestMakerspaceServerEndpoints:
    async def test_dashboard_html(self, client) -> None:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "MakerClaw Control Plane" in resp.text

        setup_resp = await client.get("/setup")
        assert setup_resp.status_code == 200
        assert "MakerClaw Setup Wizard" in setup_resp.text

        prof_resp = await client.post(
            "/brain/profile",
            json={
                "shop_name": "Test FabLab",
                "devices": [{"device_id": "laser-1", "name": "CO2 Laser", "device_type": "laser"}],
            },
        )
        assert prof_resp.status_code == 200
        assert prof_resp.json()["applied"]["devices"] == 1

    async def test_inventory_endpoints(self, client) -> None:
        r1 = await client.get("/brain/inventory?category=filament")
        assert r1.status_code == 200
        assert r1.json()["success"] is True

        r2 = await client.get("/brain/inventory?query=XIAO")
        assert r2.status_code == 200
        assert r2.json()["data"]["count"] == 1

    async def test_devices_and_cad_and_docs_endpoints(self, client) -> None:
        rd = await client.get("/brain/devices?device_type=cnc")
        assert rd.status_code == 200
        assert rd.json()["data"]["count"] == 1

        rc = await client.get("/brain/cad?domain=cad_cam")
        assert rc.status_code == 200
        assert rc.json()["data"]["count"] >= 2

        rdoc1 = await client.get("/brain/docs")
        assert rdoc1.status_code == 200
        assert rdoc1.json()["data"]["count"] >= 4

        rdoc2 = await client.get("/brain/docs?query=cubiko")
        assert rdoc2.status_code == 200
        assert rdoc2.json()["data"]["count"] >= 1


class TestMakerspaceMcpTools:
    async def test_mcp_inventory_actions(self) -> None:
        assert json.loads(await labclaw_inventory(action="list"))["success"] is True
        assert json.loads(await labclaw_inventory(action="search", query="PLA"))["success"] is True
        assert json.loads(await labclaw_inventory(action="low_stock"))["success"] is True
        assert (
            json.loads(
                await labclaw_inventory(action="update_stock", sku="MCU-XIAO-ESP32C6", delta=-1.0)
            )["success"]
            is True
        )
        assert (
            json.loads(
                await labclaw_inventory(
                    action="check_bom",
                    bom_json='[{"sku": "MCU-XIAO-ESP32C6", "quantity": 1}]',
                )
            )["success"]
            is True
        )

    async def test_mcp_devices_actions(self) -> None:
        assert json.loads(await labclaw_devices(action="list"))["success"] is True
        assert (
            json.loads(await labclaw_devices(action="status", device_id="cubiko-cnc"))["success"]
            is True
        )
        assert (
            json.loads(await labclaw_devices(action="feeds", material="fr4_isolation"))["success"]
            is True
        )
        assert (
            json.loads(await labclaw_devices(action="validate_gcode", gcode="G21\nG0 X10 Y10 Z2"))[
                "success"
            ]
            is True
        )
        assert (
            json.loads(
                await labclaw_devices(action="command", device_id="cubiko-cnc", command="home")
            )["success"]
            is True
        )

    async def test_mcp_cad_actions(self) -> None:
        assert json.loads(await labclaw_cad(action="endpoints"))["success"] is True
        assert json.loads(await labclaw_cad(action="enclosure"))["success"] is True
        assert (
            json.loads(
                await labclaw_cad(
                    action="verify_mass",
                    expected_volume_delta_cm3=1.0,
                    actual_mass_before_g=0.0,
                    actual_mass_after_g=7.85,
                )
            )["success"]
            is True
        )
        assert json.loads(await labclaw_cad(action="pcb2gcode"))["success"] is True

    async def test_mcp_docs_actions(self) -> None:
        assert json.loads(await labclaw_docs(action="list"))["success"] is True
        assert json.loads(await labclaw_docs(action="search", query="cubiko"))["success"] is True
        assert (
            json.loads(await labclaw_docs(action="get", slug="sop-cnc-cubiko"))["success"] is True
        )
        assert (
            json.loads(
                await labclaw_docs(
                    action="save",
                    slug="test-sop",
                    title="Test SOP",
                    content="# Test",
                )
            )["success"]
            is True
        )
        assert (
            json.loads(await labclaw_docs(action="generate_sop", title="CNC SOP"))["success"]
            is True
        )


class TestMakerspaceCliCommands:
    def test_cli_maker_demo(self, capsys) -> None:
        with patch("sys.argv", ["makerclaw", "demo", "--maker"]):
            main()
        out = capsys.readouterr().out
        assert "MakerClaw Makerspace Control Plane Demo" in out
        assert "bom_validation" in out

    def test_cli_inventory_list_and_search(self, capsys) -> None:
        with patch("sys.argv", ["makerclaw", "inventory", "--category", "filament"]):
            main()
        assert "FIL-PLA-MATTE-BLK" in capsys.readouterr().out

        with patch("sys.argv", ["makerclaw", "inventory", "--search", "XIAO"]):
            main()
        assert "MCU-XIAO-ESP32C6" in capsys.readouterr().out

    def test_cli_devices(self, capsys) -> None:
        with patch("sys.argv", ["makerclaw", "devices", "--type", "cnc"]):
            main()
        out = capsys.readouterr().out
        assert "cubiko-cnc" in out
        assert "fusion360-bench" in out

    def test_cli_docs_list_and_search(self, capsys) -> None:
        with patch("sys.argv", ["makerclaw", "docs"]):
            main()
        assert "sop-cnc-cubiko" in capsys.readouterr().out

        with patch("sys.argv", ["makerclaw", "docs", "--search", "spoilboard"]):
            main()
        assert "sop-cnc-cubiko" in capsys.readouterr().out

    def test_cli_simulators_starts_uvicorn(self) -> None:
        with (
            patch("sys.argv", ["makerclaw", "simulators", "--port", "18899"]),
            patch("asyncio.run") as mock_run,
            patch("builtins.print"),
        ):
            main()
        mock_run.assert_called_once()
        coro = mock_run.call_args[0][0]
        coro.close()  # silence "coroutine never awaited" RuntimeWarning

    def test_start_simulators_runs_http_and_fusion_tcp(self) -> None:
        """_start_simulators starts the Fusion TCP server and the uvicorn HTTP server."""
        from labclaw.cli import _start_simulators

        dummy_fusion = MagicMock()
        dummy_fusion.close = MagicMock()
        dummy_fusion.wait_closed = AsyncMock()
        with (
            patch(
                "labclaw.simulators.start_fusion_tcp_simulator",
                new=AsyncMock(return_value=dummy_fusion),
            ) as mock_fusion,
            patch("uvicorn.Config"),
            patch("uvicorn.Server") as mock_server_cls,
            patch("builtins.print"),
        ):
            mock_server = mock_server_cls.return_value
            mock_server.serve = AsyncMock()
            _start_simulators(port=18899, host="127.0.0.1")
        mock_fusion.assert_called_once_with(host="127.0.0.1", port=19876)
        mock_server.serve.assert_called_once()
        dummy_fusion.close.assert_called_once()
        dummy_fusion.wait_closed.assert_called_once()


class TestHardwareAndCadSimulators:
    async def test_moonraker_and_gsender_http_simulators(self) -> None:
        import makerclaw
        from labclaw.simulators import create_simulator_app

        assert makerclaw.__version__ == "0.3.0"
        sim_app = create_simulator_app()
        async with AsyncClient(
            transport=ASGITransport(app=sim_app), base_url="http://sim"
        ) as sim_client:
            q = await sim_client.get("/printer/objects/query")
            assert q.status_code == 200
            assert q.json()["result"]["status"]["print_stats"]["state"] == "standby"

            sc = await sim_client.post("/printer/gcode/script", json={"script": "G28"})
            assert sc.json()["result"] == "ok"

            st = await sim_client.post(
                "/printer/print/start",
                json={"filename": "gear.gcode", "filament_used_g": 9.5},
            )
            assert st.json()["print_stats"]["state"] == "printing"

            pa = await sim_client.post("/printer/print/pause")
            assert pa.json()["state"] == "paused"

            ca = await sim_client.post("/printer/print/cancel")
            assert ca.json()["state"] == "cancelled"

            si = await sim_client.post("/api/signin")
            tok = si.json()["token"]

            ct = await sim_client.get(f"/api/controllers?token={tok}")
            assert ct.json()[0]["authenticated"] is True

            gc = await sim_client.post("/api/gcode", json={"script": "G0 X10 Y10\nG1 Z-0.06"})
            assert gc.json()["lines"] == 2

            ov = await sim_client.get("/api/version")
            assert ov.json()["server"] == "1.10.0-sim"

    async def test_fusion_tcp_simulator(self) -> None:
        import asyncio

        from labclaw.simulators import handle_fusion_command, start_fusion_tcp_simulator

        scene = {"bodies": []}
        assert handle_fusion_command({"command": "ping"}, scene)["pong"] is True
        assert handle_fusion_command({"command": "create_box", "params": {"width": 2}}, scene)["ok"]
        assert handle_fusion_command({"command": "get_scene_info"}, scene)["body_count"] == 1
        assert handle_fusion_command({"command": "extrude"}, scene)["command"] == "extrude"

        server = await start_fusion_tcp_simulator(host="127.0.0.1", port=0)
        port = server.sockets[0].getsockname()[1]
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(b'{"command": "ping"}\n')
            await writer.drain()
            line = await reader.readline()
            writer.close()
            await writer.wait_closed()
            assert json.loads(line.decode())["pong"] is True
        finally:
            server.close()
            await server.wait_closed()
