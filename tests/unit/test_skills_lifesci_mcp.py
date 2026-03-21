"""Tests for the Life Sciences MCP skill.

Covers: protocol compliance, all 5 tool functions, health_check, configure,
lazy MCP sessions, error paths, and cached session reuse.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from labclaw.agents.tools import AgentTool
from labclaw.skills.base import CloudSkill, SkillCapability

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_mcp_result(content: Any = "mocked") -> MagicMock:
    """Create a mock MCP call_tool result with .content attribute."""
    mock = MagicMock()
    mock.content = content
    return mock


def _make_mock_session(call_tool_return: Any | None = None) -> AsyncMock:
    """Create a mock ClientSession that returns a given result on call_tool."""
    session = AsyncMock()
    if call_tool_return is None:
        call_tool_return = _make_mock_mcp_result()
    session.call_tool.return_value = call_tool_return
    session.initialize = AsyncMock()
    return session


def _patch_mcp_imports(mock_session: AsyncMock) -> Any:
    """Return a patch context that stubs out all MCP imports inside _ensure_session."""
    mock_transport = AsyncMock()
    mock_transport.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    mock_transport.__aexit__ = AsyncMock(return_value=False)

    mock_stdio_client = MagicMock(return_value=mock_transport)
    mock_client_session_cls = MagicMock(return_value=mock_session)

    mock_mcp = MagicMock()
    mock_mcp.ClientSession = mock_client_session_cls
    mock_mcp.StdioServerParameters = MagicMock()

    mock_mcp_client_stdio = MagicMock()
    mock_mcp_client_stdio.stdio_client = mock_stdio_client

    return patch.dict(
        "sys.modules",
        {
            "mcp": mock_mcp,
            "mcp.client": MagicMock(),
            "mcp.client.stdio": mock_mcp_client_stdio,
        },
    )


@pytest.fixture(autouse=True)
def _reset_module_state() -> Any:
    """Clear cached MCP sessions between tests."""
    import labclaw.skills.lifesci_mcp as mod

    mod._mcp_sessions.clear()
    mod._mcp_transports.clear()
    yield
    mod._mcp_sessions.clear()
    mod._mcp_transports.clear()


# ---------------------------------------------------------------------------
# Test: Protocol & Metadata
# ---------------------------------------------------------------------------


class TestLifeSciMCPProtocol:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        assert isinstance(LifeSciMCPSkill(), CloudSkill)

    def test_metadata_fields(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        m = LifeSciMCPSkill.metadata
        assert m.name == "lifesci_mcp"
        assert m.version == "0.1.0"
        assert SkillCapability.LITERATURE_SEARCH in m.capabilities
        assert SkillCapability.DATA_ANALYSIS in m.capabilities
        assert m.requires_api_key is False

    def test_get_tools_returns_five(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        tools = LifeSciMCPSkill().get_tools()
        assert len(tools) == 5
        names = {t.name for t in tools}
        assert names == {
            "lifesci_search_pubmed",
            "lifesci_search_biorxiv",
            "lifesci_query_chembl",
            "lifesci_query_opentargets",
            "lifesci_search_clinical_trials",
        }

    def test_tools_are_agent_tools(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        for tool in LifeSciMCPSkill().get_tools():
            assert isinstance(tool, AgentTool)
            assert tool.parameters_schema  # every tool has schema


# ---------------------------------------------------------------------------
# Test: _ensure_session
# ---------------------------------------------------------------------------


class TestEnsureSession:
    @pytest.mark.asyncio
    async def test_unknown_server_key(self) -> None:
        from labclaw.skills.lifesci_mcp import _ensure_session

        result = await _ensure_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cached_session_returned(self) -> None:
        from labclaw.skills.lifesci_mcp import _ensure_session, _mcp_sessions

        sentinel = object()
        _mcp_sessions["pubmed"] = sentinel
        result = await _ensure_session("pubmed")
        assert result is sentinel

    @pytest.mark.asyncio
    async def test_connection_failure(self) -> None:
        from labclaw.skills.lifesci_mcp import _ensure_session

        with patch.dict("sys.modules", {"mcp": MagicMock(side_effect=ImportError)}):
            with patch(
                "labclaw.skills.lifesci_mcp._ensure_session",
                wraps=_ensure_session,
            ):
                # Force import error by making mcp module raise on attribute access
                mock_mcp = MagicMock()
                mock_mcp.StdioServerParameters = MagicMock(side_effect=RuntimeError("no mcp"))
                with patch.dict("sys.modules", {"mcp": mock_mcp}):
                    result = await _ensure_session("pubmed")
                    assert result is None

    @pytest.mark.asyncio
    async def test_successful_connection(self) -> None:
        from labclaw.skills.lifesci_mcp import _ensure_session, _mcp_sessions

        mock_session = _make_mock_session()
        with _patch_mcp_imports(mock_session):
            result = await _ensure_session("pubmed")
        assert result is mock_session
        assert "pubmed" in _mcp_sessions


# ---------------------------------------------------------------------------
# Test: search_pubmed
# ---------------------------------------------------------------------------


class TestSearchPubmed:
    @pytest.mark.asyncio
    async def test_server_unavailable(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_pubmed

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _search_pubmed("CRISPR")
        assert result.success is False
        assert "PubMed" in result.error

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_pubmed

        mock_session = _make_mock_session(_make_mock_mcp_result([{"title": "Paper A"}]))
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_pubmed("CRISPR", max_results=5)
        assert result.success is True
        assert result.data["source"] == "pubmed"
        assert result.data["query"] == "CRISPR"

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_pubmed

        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = RuntimeError("network error")
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_pubmed("test")
        assert result.success is False
        assert "network error" in result.error


# ---------------------------------------------------------------------------
# Test: search_biorxiv
# ---------------------------------------------------------------------------


class TestSearchBiorxiv:
    @pytest.mark.asyncio
    async def test_server_unavailable(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _search_biorxiv("protein folding")
        assert result.success is False
        assert "bioRxiv" in result.error

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        mock_session = _make_mock_session(_make_mock_mcp_result([{"title": "Preprint B"}]))
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_biorxiv("protein folding", max_results=3)
        assert result.success is True
        assert result.data["source"] == "biorxiv"

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = ConnectionError("timeout")
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_biorxiv("test")
        assert result.success is False
        assert "timeout" in result.error


# ---------------------------------------------------------------------------
# Test: query_chembl
# ---------------------------------------------------------------------------


class TestQueryChembl:
    @pytest.mark.asyncio
    async def test_server_unavailable(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_chembl

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _query_chembl("aspirin")
        assert result.success is False
        assert "ChEMBL" in result.error

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_chembl

        mock_session = _make_mock_session(
            _make_mock_mcp_result({"compound": "aspirin", "id": "CHEMBL25"})
        )
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _query_chembl("aspirin", query_type="compound")
        assert result.success is True
        assert result.data["source"] == "chembl"
        assert result.data["query_type"] == "compound"

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_chembl

        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = ValueError("bad query")
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _query_chembl("???")
        assert result.success is False
        assert "bad query" in result.error


# ---------------------------------------------------------------------------
# Test: query_opentargets
# ---------------------------------------------------------------------------


class TestQueryOpentargets:
    @pytest.mark.asyncio
    async def test_server_unavailable(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_opentargets

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _query_opentargets("BRCA1")
        assert result.success is False
        assert "OpenTargets" in result.error

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_opentargets

        mock_session = _make_mock_session(
            _make_mock_mcp_result({"target": "BRCA1", "diseases": []})
        )
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _query_opentargets("BRCA1", query_type="target")
        assert result.success is True
        assert result.data["source"] == "opentargets"
        assert result.data["query_type"] == "target"

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_opentargets

        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = ConnectionError("slow")
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _query_opentargets("TP53")
        assert result.success is False
        assert "slow" in result.error


# ---------------------------------------------------------------------------
# Test: search_clinical_trials
# ---------------------------------------------------------------------------


class TestSearchClinicalTrials:
    @pytest.mark.asyncio
    async def test_server_unavailable(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _search_clinical_trials("lung cancer")
        assert result.success is False
        assert "ClinicalTrials" in result.error

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        mock_session = _make_mock_session(
            _make_mock_mcp_result([{"nct_id": "NCT001", "title": "Trial X"}])
        )
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_clinical_trials("lung cancer", max_results=5, status="completed")
        assert result.success is True
        assert result.data["source"] == "clinical_trials"
        assert result.data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = OSError("conn refused")
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_clinical_trials("test")
        assert result.success is False
        assert "conn refused" in result.error


# ---------------------------------------------------------------------------
# Test: health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_when_one_server_connects(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        call_count = 0

        async def _mock_ensure(key: str) -> Any:
            nonlocal call_count
            call_count += 1
            if key == "pubmed":
                return _make_mock_session()
            return None

        skill = LifeSciMCPSkill()
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            side_effect=_mock_ensure,
        ):
            assert await skill.health_check() is True
        # Should return True on first success (pubmed is first key)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_unhealthy_when_no_servers_connect(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        skill = LifeSciMCPSkill()
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            assert await skill.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_exception_continues(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        skill = LifeSciMCPSkill()
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            side_effect=RuntimeError("crash"),
        ):
            assert await skill.health_check() is False


# ---------------------------------------------------------------------------
# Test: configure
# ---------------------------------------------------------------------------


class TestConfigure:
    def test_configure_reset_clears_sessions(self) -> None:
        import labclaw.skills.lifesci_mcp as mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        # Populate cached state
        mock_transport = MagicMock()
        mock_transport.__aexit__ = AsyncMock(return_value=False)
        mod._mcp_sessions["pubmed"] = MagicMock()
        mod._mcp_transports["pubmed"] = mock_transport

        skill = LifeSciMCPSkill()
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_until_complete = MagicMock()
            skill.configure(reset=True)

        assert len(mod._mcp_sessions) == 0
        assert len(mod._mcp_transports) == 0

    def test_configure_without_reset_is_noop(self) -> None:
        import labclaw.skills.lifesci_mcp as mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        mod._mcp_sessions["pubmed"] = MagicMock()
        skill = LifeSciMCPSkill()
        skill.configure(other_param="value")
        # Sessions should still be there
        assert "pubmed" in mod._mcp_sessions

    def test_configure_reset_handles_exit_exception(self) -> None:
        import labclaw.skills.lifesci_mcp as mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        mock_transport = MagicMock()
        mod._mcp_sessions["pubmed"] = MagicMock()
        mod._mcp_transports["pubmed"] = mock_transport

        skill = LifeSciMCPSkill()
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_until_complete.side_effect = RuntimeError("loop closed")
            skill.configure(reset=True)

        # Should still clear despite exception
        assert len(mod._mcp_sessions) == 0
        assert len(mod._mcp_transports) == 0


# ---------------------------------------------------------------------------
# Test: MCP result without .content attribute
# ---------------------------------------------------------------------------


class TestMCPResultFallback:
    @pytest.mark.asyncio
    async def test_result_without_content_attribute(self) -> None:
        """When MCP result has no .content, str(result) is used."""
        from labclaw.skills.lifesci_mcp import _search_pubmed

        mock_result = "raw string result"
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = mock_result
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await _search_pubmed("test")
        assert result.success is True
        assert result.data["results"] == "raw string result"


# ---------------------------------------------------------------------------
# Test: AgentTool.execute integration
# ---------------------------------------------------------------------------


class TestToolExecution:
    @pytest.mark.asyncio
    async def test_execute_via_agent_tool(self) -> None:
        """Verify tools work through AgentTool.execute()."""
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        skill = LifeSciMCPSkill()
        tools = skill.get_tools()
        pubmed_tool = next(t for t in tools if t.name == "lifesci_search_pubmed")

        mock_session = _make_mock_session(_make_mock_mcp_result([{"title": "Test"}]))
        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ):
            result = await pubmed_tool.execute(query="neurons")
        assert result.success is True
        assert result.data["source"] == "pubmed"


# ---------------------------------------------------------------------------
# Test: MCP_SERVERS config
# ---------------------------------------------------------------------------


class TestMCPServersConfig:
    def test_all_server_keys_present(self) -> None:
        from labclaw.skills.lifesci_mcp import _MCP_SERVERS

        expected = {"pubmed", "biorxiv", "chembl", "opentargets", "clinical_trials"}
        assert set(_MCP_SERVERS.keys()) == expected

    def test_each_server_has_required_fields(self) -> None:
        from labclaw.skills.lifesci_mcp import _MCP_SERVERS

        for key, cfg in _MCP_SERVERS.items():
            assert "command" in cfg, f"{key} missing command"
            assert "args" in cfg, f"{key} missing args"
            assert "tool_name" in cfg, f"{key} missing tool_name"
            assert cfg["command"] == "uvx", f"{key} should use uvx"
