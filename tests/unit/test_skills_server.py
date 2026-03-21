"""Tests for Cloud Brain server — all endpoints with mocked skills."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import SkillCapability, SkillMetadata
from labclaw.skills.server import (
    MAX_REQUEST_SIZE,
    MAX_RESPONSE_SIZE,
    ExecuteRequest,
    ExecuteResponse,
    InventoryCategory,
    InventoryResponse,
    ToolInfo,
    _get_valid_keys,
    _registry,
    _verify_api_key,
    app,
)

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


async def _stub_fn(**kwargs: Any) -> ToolResult:
    return ToolResult(success=True, data={"echo": kwargs})


async def _failing_fn(**kwargs: Any) -> ToolResult:
    return ToolResult(success=False, error="boom")


async def _large_fn(**kwargs: Any) -> ToolResult:
    """Return a result larger than MAX_RESPONSE_SIZE."""
    big_data = {"payload": "x" * (MAX_RESPONSE_SIZE + 1000)}
    return ToolResult(success=True, data=big_data)


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


class FakeSkillLarge:
    """Skill with a tool that returns large responses."""

    metadata = SkillMetadata(
        name="large",
        version="0.1.0",
        description="Large response skill",
        capabilities=[SkillCapability.DATA_ANALYSIS],
    )

    def get_tools(self) -> list[AgentTool]:
        return [
            AgentTool(
                name="large_tool",
                description="Returns large data",
                fn=_large_fn,
            ),
        ]

    async def health_check(self) -> bool:
        return True

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
def _populated_registry_with_large():
    """Populate registry with fake skills including the large-response skill."""
    old_skills = dict(_registry._skills)
    _registry._skills.clear()
    _registry._skills["alpha"] = FakeSkillA()
    _registry._skills["beta"] = FakeSkillB()
    _registry._skills["large"] = FakeSkillLarge()
    yield
    _registry._skills.clear()
    _registry._skills.update(old_skills)


@pytest.fixture()
def client(_populated_registry):
    """TestClient with fake skills loaded (startup event skipped)."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def client_with_large(_populated_registry_with_large):
    """TestClient with fake skills including large-response skill."""
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


# ---------------------------------------------------------------------------
# API Key Authentication
# ---------------------------------------------------------------------------


class TestAPIKeyAuth:
    def test_no_keys_configured_allows_access(self, client: TestClient) -> None:
        """Without LABCLAW_API_KEYS env, all requests pass (open access)."""
        resp = client.get("/brain/skills")
        assert resp.status_code == 200

    def test_valid_key_allows_access(self, _populated_registry) -> None:
        """Valid API key returns 200."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": "key-abc,key-def"}):
            c = TestClient(app, raise_server_exceptions=False)
            resp = c.get("/brain/skills", headers={"X-API-Key": "key-abc"})
            assert resp.status_code == 200

    def test_invalid_key_returns_403(self, _populated_registry) -> None:
        """Invalid API key returns 403."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": "key-abc,key-def"}):
            c = TestClient(app, raise_server_exceptions=False)
            resp = c.get("/brain/skills", headers={"X-API-Key": "wrong-key"})
            assert resp.status_code == 403
            assert "Invalid or missing API key" in resp.json()["detail"]

    def test_missing_key_returns_403(self, _populated_registry) -> None:
        """No API key header when keys are configured returns 403."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": "key-abc"}):
            c = TestClient(app, raise_server_exceptions=False)
            resp = c.get("/brain/skills")
            assert resp.status_code == 403

    def test_auth_applies_to_post(self, _populated_registry) -> None:
        """Auth also guards POST endpoints."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": "key-abc"}):
            c = TestClient(app, raise_server_exceptions=False)
            resp = c.post(
                "/brain/execute",
                json={"tool_name": "alpha_search", "arguments": {"query": "test"}},
            )
            assert resp.status_code == 403

    def test_auth_post_with_valid_key(self, _populated_registry) -> None:
        """POST with valid key succeeds."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": "key-abc"}):
            c = TestClient(app, raise_server_exceptions=False)
            resp = c.post(
                "/brain/execute",
                json={"tool_name": "alpha_search", "arguments": {"query": "test"}},
                headers={"X-API-Key": "key-abc"},
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True

    def test_get_valid_keys_empty_string(self) -> None:
        """Empty LABCLAW_API_KEYS returns empty set."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": ""}):
            assert _get_valid_keys() == set()

    def test_get_valid_keys_strips_whitespace(self) -> None:
        """Keys are stripped of whitespace."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": " key1 , key2 , "}):
            assert _get_valid_keys() == {"key1", "key2"}

    def test_get_valid_keys_unset(self) -> None:
        """Unset LABCLAW_API_KEYS returns empty set."""
        with patch.dict("os.environ", {}, clear=True):
            assert _get_valid_keys() == set()

    @pytest.mark.asyncio
    async def test_verify_api_key_anonymous(self) -> None:
        """No keys configured returns 'anonymous'."""
        with patch.dict("os.environ", {}, clear=True):
            result = await _verify_api_key(api_key=None)
            assert result == "anonymous"

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self) -> None:
        """Valid key returns the key."""
        with patch.dict("os.environ", {"LABCLAW_API_KEYS": "test-key"}):
            result = await _verify_api_key(api_key="test-key")
            assert result == "test-key"

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self) -> None:
        """Invalid key raises HTTPException(403)."""
        from fastapi import HTTPException

        with (
            patch.dict("os.environ", {"LABCLAW_API_KEYS": "test-key"}),
            pytest.raises(HTTPException) as exc_info,
        ):
            await _verify_api_key(api_key="bad-key")
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Response Size Limits
# ---------------------------------------------------------------------------


class TestResponseSizeLimits:
    def test_large_response_is_truncated(self, client_with_large: TestClient) -> None:
        """Responses exceeding MAX_RESPONSE_SIZE are truncated."""
        resp = client_with_large.post(
            "/brain/execute",
            json={"tool_name": "large_tool", "arguments": {}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["truncated"] is True
        assert data["data"]["size"] > MAX_RESPONSE_SIZE
        assert len(data["data"]["preview"]) == MAX_RESPONSE_SIZE

    def test_normal_response_not_truncated(self, client: TestClient) -> None:
        """Normal-sized responses are not truncated."""
        resp = client.post(
            "/brain/execute",
            json={"tool_name": "alpha_search", "arguments": {"query": "test"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "truncated" not in (data["data"] or {})


# ---------------------------------------------------------------------------
# Request Size Limits
# ---------------------------------------------------------------------------


class TestRequestSizeLimits:
    def test_oversized_request_returns_413(self, _populated_registry) -> None:
        """Request with Content-Length > MAX_REQUEST_SIZE returns 413."""
        c = TestClient(app, raise_server_exceptions=False)
        huge_body = "x" * (MAX_REQUEST_SIZE + 1)
        resp = c.post(
            "/brain/execute",
            content=huge_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(huge_body)),
            },
        )
        assert resp.status_code == 413
        assert "Request body too large" in resp.json()["detail"]

    def test_normal_request_passes(self, client: TestClient) -> None:
        """Normal-sized request passes the middleware."""
        body = json.dumps({"tool_name": "alpha_search", "arguments": {"query": "ok"}})
        resp = client.post(
            "/brain/execute",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    def test_rate_limit_key_with_api_key(self) -> None:
        """Rate limit key uses X-API-Key if present."""
        # Create a mock request-like object
        from unittest.mock import MagicMock

        from labclaw.skills.server import _rate_limit_key

        request = MagicMock()
        request.headers = {"X-API-Key": "my-key"}
        assert _rate_limit_key(request) == "my-key"

    def test_rate_limit_key_falls_back_to_ip(self) -> None:
        """Rate limit key falls back to remote address when no API key."""
        from unittest.mock import MagicMock

        from labclaw.skills.server import _rate_limit_key

        request = MagicMock()
        request.headers = {}
        request.client.host = "1.2.3.4"
        # get_remote_address uses request.client.host
        result = _rate_limit_key(request)
        # Without X-API-Key, falls back to get_remote_address
        assert result is not None

    def test_rate_limit_handler_exists(self) -> None:
        """App has a rate limit exception handler registered."""
        from slowapi.errors import RateLimitExceeded

        handlers = app.exception_handlers
        assert RateLimitExceeded in handlers

    def test_limiter_attached_to_app(self) -> None:
        """Limiter is attached to app.state."""
        from labclaw.skills.server import limiter

        assert app.state.limiter is limiter

    @pytest.mark.asyncio
    async def test_rate_limit_handler_returns_429(self) -> None:
        """The rate limit exception handler returns a 429 JSONResponse."""
        from unittest.mock import MagicMock

        from slowapi.errors import RateLimitExceeded

        from labclaw.skills.server import _rate_limit_handler

        request = MagicMock()
        # RateLimitExceeded expects a Limit object; mock it
        mock_limit = MagicMock()
        mock_limit.error_message = None
        exc = RateLimitExceeded(mock_limit)
        response = await _rate_limit_handler(request, exc)
        assert response.status_code == 429
        assert b"Rate limit exceeded" in response.body
