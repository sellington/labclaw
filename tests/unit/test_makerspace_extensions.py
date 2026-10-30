"""Tests for Makerspace REST endpoints, MCP tools, CLI subcommands, and brain init."""

from __future__ import annotations

import json
from unittest.mock import patch

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


class TestMakerspaceServerEndpoints:
    async def test_dashboard_html(self, client) -> None:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "MakerClaw Control Plane" in resp.text

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
