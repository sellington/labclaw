"""Tests for Cloud Brain server — all endpoints with mocked skills."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import SkillCapability, SkillMetadata
from labclaw.skills.server import (
    ExecuteRequest,
    ExecuteResponse,
    InventoryCategory,
    InventoryResponse,
    ToolInfo,
    _registry,
    app,
)

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


async def _stub_fn(**kwargs: Any) -> ToolResult:
    return ToolResult(success=True, data={"echo": kwargs})


async def _failing_fn(**kwargs: Any) -> ToolResult:
    return ToolResult(success=False, error="boom")


class FakeSkillA:
    """Skill with two tools."""

    metadata = SkillMetadata(
        name="alpha",
        version="1.0.0",
        description="Alpha skill",
        capabilities=[SkillCapability.DATA_ANALYSIS, SkillCapability.LITERATURE_SEARCH],
    )

    def get_tools(self) -> list[AgentTool]:
        return [
            AgentTool(
                name="alpha_search",
                description="Search alpha",
                fn=_stub_fn,
                parameters_schema={"query": {"type": "string"}},
            ),
            AgentTool(
                name="alpha_analyze",
                description="Analyze alpha",
                fn=_stub_fn,
            ),
        ]

    async def health_check(self) -> bool:
        return True

    def configure(self, **kwargs: Any) -> None:
        pass


class FakeSkillB:
    """Skill with one tool, unhealthy."""

    metadata = SkillMetadata(
        name="beta",
        version="0.5.0",
        description="Beta skill",
        capabilities=[SkillCapability.SCIENTIFIC_WRITING],
    )

    def get_tools(self) -> list[AgentTool]:
        return [
            AgentTool(
                name="beta_write",
                description="Write beta",
                fn=_failing_fn,
            ),
        ]

    async def health_check(self) -> bool:
        return False

    def configure(self, **kwargs: Any) -> None:
        pass


class BrokenToolsSkill:
    """Skill whose get_tools() raises."""

    metadata = SkillMetadata(
        name="broken",
        version="0.0.1",
        description="Broken",
        capabilities=[SkillCapability.GENERAL_REASONING],
    )

    def get_tools(self) -> list[AgentTool]:
        raise RuntimeError("cannot load tools")

    async def health_check(self) -> bool:
        raise ConnectionError("down")

    def configure(self, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _populated_registry():
    """Populate the server-level registry with fake skills, restore after."""
    old_skills = dict(_registry._skills)
    _registry._skills.clear()
    _registry._skills["alpha"] = FakeSkillA()
    _registry._skills["beta"] = FakeSkillB()
    yield
    _registry._skills.clear()
    _registry._skills.update(old_skills)


@pytest.fixture()
def client(_populated_registry):
    """TestClient with fake skills loaded (startup event skipped)."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestModels:
    def test_execute_request_defaults(self) -> None:
        req = ExecuteRequest(tool_name="foo")
        assert req.tool_name == "foo"
        assert req.arguments == {}

    def test_execute_response_defaults(self) -> None:
        resp = ExecuteResponse(success=True)
        assert resp.data is None
        assert resp.error == ""

    def test_tool_info(self) -> None:
        ti = ToolInfo(name="t", description="d")
        assert ti.parameters == {}

    def test_inventory_category(self) -> None:
        ic = InventoryCategory(
            capability="data_analysis", skill_count=1, tool_count=2, skills=["a"]
        )
        assert ic.capability == "data_analysis"

    def test_inventory_response(self) -> None:
        ir = InventoryResponse(total_skills=1, total_tools=2, categories=[])
        assert ir.total_skills == 1


# ---------------------------------------------------------------------------
# GET /brain/skills
# ---------------------------------------------------------------------------


class TestListSkills:
    def test_returns_all_skills(self, client: TestClient) -> None:
        resp = client.get("/brain/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = {s["name"] for s in data}
        assert names == {"alpha", "beta"}

    def test_skill_fields(self, client: TestClient) -> None:
        resp = client.get("/brain/skills")
        alpha = next(s for s in resp.json() if s["name"] == "alpha")
        assert alpha["version"] == "1.0.0"
        assert alpha["description"] == "Alpha skill"
        assert "data_analysis" in alpha["capabilities"]


# ---------------------------------------------------------------------------
# GET /brain/tools
# ---------------------------------------------------------------------------


class TestListTools:
    def test_returns_all_tools(self, client: TestClient) -> None:
        resp = client.get("/brain/tools")
        assert resp.status_code == 200
        data = resp.json()
        names = {t["name"] for t in data}
        assert "alpha_search" in names
        assert "alpha_analyze" in names
        assert "beta_write" in names

    def test_tool_fields(self, client: TestClient) -> None:
        resp = client.get("/brain/tools")
        tool = next(t for t in resp.json() if t["name"] == "alpha_search")
        assert tool["description"] == "Search alpha"
        assert "query" in tool["parameters"]


# ---------------------------------------------------------------------------
# GET /brain/health
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_returns_health_status(self, client: TestClient) -> None:
        resp = client.get("/brain/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alpha"] is True
        assert data["beta"] is False


# ---------------------------------------------------------------------------
# POST /brain/execute
# ---------------------------------------------------------------------------


class TestExecuteTool:
    def test_execute_existing_tool(self, client: TestClient) -> None:
        resp = client.post(
            "/brain/execute",
            json={"tool_name": "alpha_search", "arguments": {"query": "test"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["echo"]["query"] == "test"

    def test_execute_missing_tool(self, client: TestClient) -> None:
        resp = client.post(
            "/brain/execute",
            json={"tool_name": "nonexistent"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "not found" in data["error"]

    def test_execute_failing_tool(self, client: TestClient) -> None:
        resp = client.post(
            "/brain/execute",
            json={"tool_name": "beta_write", "arguments": {}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["error"] == "boom"

    def test_execute_no_arguments(self, client: TestClient) -> None:
        resp = client.post(
            "/brain/execute",
            json={"tool_name": "alpha_analyze"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# GET /brain/inventory
# ---------------------------------------------------------------------------


class TestInventory:
    def test_inventory_totals(self, client: TestClient) -> None:
        resp = client.get("/brain/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_skills"] == 2
        assert data["total_tools"] == 3  # 2 from alpha + 1 from beta

    def test_inventory_categories(self, client: TestClient) -> None:
        resp = client.get("/brain/inventory")
        data = resp.json()
        cats = {c["capability"]: c for c in data["categories"]}
        assert "data_analysis" in cats
        assert "scientific_writing" in cats
        assert "literature_search" in cats
        assert cats["data_analysis"]["skill_count"] == 1
        assert cats["data_analysis"]["skills"] == ["alpha"]

    def test_inventory_tool_counts_per_category(self, client: TestClient) -> None:
        resp = client.get("/brain/inventory")
        data = resp.json()
        cats = {c["capability"]: c for c in data["categories"]}
        # alpha has 2 tools, registered under data_analysis and literature_search
        assert cats["data_analysis"]["tool_count"] == 2
        assert cats["literature_search"]["tool_count"] == 2
        # beta has 1 tool, registered under scientific_writing
        assert cats["scientific_writing"]["tool_count"] == 1


# ---------------------------------------------------------------------------
# Broken skill handling in inventory
# ---------------------------------------------------------------------------


class TestInventoryBrokenSkill:
    def test_broken_tools_counted_as_zero(self) -> None:
        """Skill whose get_tools() raises => tool_count=0 for that skill."""
        old_skills = dict(_registry._skills)
        _registry._skills.clear()
        _registry._skills["broken"] = BrokenToolsSkill()

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/brain/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_skills"] == 1
        # get_all_tools logs warning and returns empty for broken
        assert data["total_tools"] == 0
        cats = {c["capability"]: c for c in data["categories"]}
        assert cats["general_reasoning"]["tool_count"] == 0

        _registry._skills.clear()
        _registry._skills.update(old_skills)


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------


class TestStartup:
    def test_register_builtin_skills(self) -> None:
        """_register_builtin_skills populates the registry."""
        from labclaw.skills.server import _register_builtin_skills

        old_skills = dict(_registry._skills)
        _registry._skills.clear()

        with patch(
            "labclaw.skills.server._register_builtin_skills",
            wraps=_register_builtin_skills,
        ):
            _register_builtin_skills()

        assert _registry.count >= 5
        names = {s.name for s in _registry.list_skills()}
        assert "tooluniverse" in names
        assert "biomni" in names
        assert "kdense" in names
        assert "write" in names
        assert "lifesci" in names

        _registry._skills.clear()
        _registry._skills.update(old_skills)

    def test_register_idempotent(self) -> None:
        """Calling _register_builtin_skills twice does not raise."""
        from labclaw.skills.server import _register_builtin_skills

        old_skills = dict(_registry._skills)
        _registry._skills.clear()

        _register_builtin_skills()
        _register_builtin_skills()  # should not raise

        _registry._skills.clear()
        _registry._skills.update(old_skills)


# ---------------------------------------------------------------------------
# CLI: labclaw brain
# ---------------------------------------------------------------------------


class TestBrainCLI:
    def test_brain_help(self) -> None:
        """brain --help prints usage and returns."""
        import io
        import sys

        from labclaw.cli import _brain_cmd

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            _brain_cmd(["--help"])
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        assert "--port" in output
        assert "18802" in output

    def test_brain_default_port(self) -> None:
        """brain without args calls uvicorn.run with port 18802."""
        from labclaw.cli import _brain_cmd

        with patch("uvicorn.run") as mock_run:
            _brain_cmd([])
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args
            assert call_kwargs[1]["port"] == 18802
            assert call_kwargs[1]["host"] == "127.0.0.1"

    def test_brain_custom_port(self) -> None:
        """brain --port 9999 passes the custom port."""
        from labclaw.cli import _brain_cmd

        with patch("uvicorn.run") as mock_run:
            _brain_cmd(["--port", "9999"])
            call_kwargs = mock_run.call_args
            assert call_kwargs[1]["port"] == 9999

    def test_brain_cmd_in_main(self) -> None:
        """'brain' command is dispatched from main()."""
        from labclaw.cli import main

        with (
            patch("sys.argv", ["labclaw", "brain", "--help"]),
            patch("builtins.print"),
        ):
            main()  # should not raise


# ---------------------------------------------------------------------------
# Empty registry edge cases
# ---------------------------------------------------------------------------


class TestEmptyRegistry:
    def test_skills_empty(self) -> None:
        old_skills = dict(_registry._skills)
        _registry._skills.clear()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/brain/skills")
        assert resp.status_code == 200
        assert resp.json() == []
        _registry._skills.clear()
        _registry._skills.update(old_skills)

    def test_tools_empty(self) -> None:
        old_skills = dict(_registry._skills)
        _registry._skills.clear()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/brain/tools")
        assert resp.status_code == 200
        assert resp.json() == []
        _registry._skills.clear()
        _registry._skills.update(old_skills)

    def test_health_empty(self) -> None:
        old_skills = dict(_registry._skills)
        _registry._skills.clear()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/brain/health")
        assert resp.status_code == 200
        assert resp.json() == {}
        _registry._skills.clear()
        _registry._skills.update(old_skills)

    def test_inventory_empty(self) -> None:
        old_skills = dict(_registry._skills)
        _registry._skills.clear()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/brain/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_skills"] == 0
        assert data["total_tools"] == 0
        assert data["categories"] == []
        _registry._skills.clear()
        _registry._skills.update(old_skills)
