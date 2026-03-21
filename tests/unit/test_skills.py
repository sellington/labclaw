"""Tests for the cloud brain skills module.

Covers: base protocol, registry, all 5 skill adapters (real SDK integrations),
config, CLI, API router.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

# ---------------------------------------------------------------------------
# Fixtures and stubs
# ---------------------------------------------------------------------------


class StubSkill:
    """Minimal CloudSkill implementation for testing."""

    metadata = SkillMetadata(
        name="stub",
        version="0.1.0",
        description="A stub skill for testing.",
        capabilities=[SkillCapability.GENERAL_REASONING],
    )

    def get_tools(self) -> list[AgentTool]:
        async def _noop(**kwargs: Any) -> ToolResult:
            return ToolResult(success=True, data=kwargs)

        return [
            AgentTool(name="stub_tool", description="A stub tool.", fn=_noop),
        ]

    async def health_check(self) -> bool:
        return True

    def configure(self, **kwargs: Any) -> None:
        pass


class FailingSkill:
    """Skill whose tools raise exceptions."""

    metadata = SkillMetadata(
        name="failing",
        version="0.1.0",
        description="Fails on health check.",
        capabilities=[SkillCapability.DATA_ANALYSIS],
    )

    def get_tools(self) -> list[AgentTool]:
        raise RuntimeError("broken tools")

    async def health_check(self) -> bool:
        raise ConnectionError("unreachable")

    def configure(self, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Test: SkillMetadata
# ---------------------------------------------------------------------------


class TestSkillMetadata:
    def test_basic_fields(self) -> None:
        m = SkillMetadata(
            name="test",
            version="1.0.0",
            description="desc",
            capabilities=[SkillCapability.LITERATURE_SEARCH],
        )
        assert m.name == "test"
        assert m.version == "1.0.0"
        assert SkillCapability.LITERATURE_SEARCH in m.capabilities

    def test_optional_fields_default(self) -> None:
        m = SkillMetadata(
            name="x",
            version="0.1.0",
            description="d",
            capabilities=[],
        )
        assert m.author == ""
        assert m.requires_api_key is False
        assert m.api_key_env == ""


# ---------------------------------------------------------------------------
# Test: SkillCapability enum
# ---------------------------------------------------------------------------


class TestSkillCapability:
    def test_all_values(self) -> None:
        assert SkillCapability.LITERATURE_SEARCH == "literature_search"
        assert SkillCapability.HYPOTHESIS_GENERATION == "hypothesis_generation"
        assert SkillCapability.INSTRUMENT_KNOWLEDGE == "instrument_knowledge"
        assert SkillCapability.DATA_ANALYSIS == "data_analysis"
        assert SkillCapability.SCIENTIFIC_WRITING == "scientific_writing"
        assert SkillCapability.GENERAL_REASONING == "general_reasoning"


# ---------------------------------------------------------------------------
# Test: CloudSkill protocol
# ---------------------------------------------------------------------------


class TestCloudSkillProtocol:
    def test_stub_is_cloud_skill(self) -> None:
        assert isinstance(StubSkill(), CloudSkill)

    def test_failing_is_cloud_skill(self) -> None:
        assert isinstance(FailingSkill(), CloudSkill)


# ---------------------------------------------------------------------------
# Test: SkillRegistry
# ---------------------------------------------------------------------------


class TestSkillRegistry:
    def test_register_and_get(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        skill = StubSkill()
        reg.register(skill)
        assert reg.get("stub") is skill

    def test_register_duplicate_raises(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(StubSkill())

    def test_get_not_found_raises(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.get("nonexistent")

    def test_unregister(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        reg.unregister("stub")
        assert reg.count == 0

    def test_unregister_not_found_raises(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.unregister("nonexistent")

    def test_get_by_capability(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        results = reg.get_by_capability(SkillCapability.GENERAL_REASONING)
        assert len(results) == 1
        empty = reg.get_by_capability(SkillCapability.LITERATURE_SEARCH)
        assert len(empty) == 0

    def test_list_skills(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        metas = reg.list_skills()
        assert len(metas) == 1
        assert metas[0].name == "stub"

    def test_get_all_tools(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        tools = reg.get_all_tools()
        assert len(tools) == 1
        assert tools[0].name == "stub_tool"

    def test_get_all_tools_handles_failure(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(FailingSkill())
        tools = reg.get_all_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_health_check_all(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        results = await reg.health_check_all()
        assert results == {"stub": True}

    @pytest.mark.asyncio
    async def test_health_check_all_with_failure(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(FailingSkill())
        results = await reg.health_check_all()
        assert results == {"failing": False}

    def test_count(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        assert reg.count == 0
        reg.register(StubSkill())
        assert reg.count == 1

    def test_discover_entry_points_disabled(self) -> None:
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        found = reg.discover_entry_points()
        assert found == []

    @patch.dict("os.environ", {"LABCLAW_ENABLE_SKILL_PLUGINS": "1"})
    @patch("importlib.metadata.entry_points")
    def test_discover_entry_points_success(self, mock_eps: MagicMock) -> None:
        from labclaw.skills.registry import SkillRegistry

        mock_ep = MagicMock()
        mock_ep.name = "stub_ep"
        mock_ep.load.return_value = StubSkill
        mock_eps.return_value = [mock_ep]

        reg = SkillRegistry()
        found = reg.discover_entry_points()
        assert found == ["stub_ep"]
        assert reg.count == 1

    @patch.dict("os.environ", {"LABCLAW_ENABLE_SKILL_PLUGINS": "1"})
    @patch("importlib.metadata.entry_points")
    def test_discover_entry_points_failure(self, mock_eps: MagicMock) -> None:
        from labclaw.skills.registry import SkillRegistry

        mock_ep = MagicMock()
        mock_ep.name = "broken"
        mock_ep.load.side_effect = ImportError("missing")
        mock_eps.return_value = [mock_ep]

        reg = SkillRegistry()
        found = reg.discover_entry_points()
        assert found == []


# ---------------------------------------------------------------------------
# Test: ToolUniverseSkill (real SDK integration)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_tu_singleton():
    """Reset the ToolUniverse singleton before each test."""
    import labclaw.skills.tooluniverse as tu_mod

    original = tu_mod._tu_instance
    tu_mod._tu_instance = None
    yield
    tu_mod._tu_instance = original


class TestToolUniverseSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        assert isinstance(skill, CloudSkill)

    def test_metadata(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        assert skill.metadata.name == "tooluniverse"
        assert SkillCapability.INSTRUMENT_KNOWLEDGE in skill.metadata.capabilities
        assert SkillCapability.DATA_ANALYSIS in skill.metadata.capabilities
        assert SkillCapability.LITERATURE_SEARCH in skill.metadata.capabilities

    def test_get_tools_returns_four(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        tools = skill.get_tools()
        assert len(tools) == 4
        names = {t.name for t in tools}
        assert names == {"tu_run", "tu_find_tools", "tu_get_spec", "tu_list_categories"}

    @pytest.mark.asyncio
    async def test_run_tool_success(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = {"output": "data"}
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _run_tool

        result = await _run_tool("UniProt_get_entry", arguments={"accession": "P12345"})
        assert result.success is True
        assert result.data == {"output": "data"}

    @pytest.mark.asyncio
    async def test_run_tool_error_status(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = {"status": "error", "error": "bad request"}
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _run_tool

        result = await _run_tool("bad_tool")
        assert result.success is False
        assert "bad request" in result.error

    @pytest.mark.asyncio
    async def test_run_tool_exception(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.side_effect = RuntimeError("SDK crash")
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _run_tool

        result = await _run_tool("crash_tool")
        assert result.success is False
        assert "SDK crash" in result.error

    @pytest.mark.asyncio
    async def test_find_tools_success(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = {"tools": ["tool1", "tool2"]}
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _find_tools

        result = await _find_tools("protein search")
        assert result.success is True
        assert result.data == {"tools": ["tool1", "tool2"]}

    @pytest.mark.asyncio
    async def test_find_tools_fallback_pattern_search(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = {"status": "error", "error": "no match"}
        mock_tu.find_tools_by_pattern.return_value = [
            {"name": "tool_a", "description": "desc_a", "category": "cat_a"},
        ]
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _find_tools

        result = await _find_tools("protein")
        assert result.success is True
        assert result.data["source"] == "pattern_search"
        assert len(result.data["tools"]) == 1
        assert result.data["tools"][0]["name"] == "tool_a"

    @pytest.mark.asyncio
    async def test_find_tools_fallback_empty(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = {"status": "error", "error": "no match"}
        mock_tu.find_tools_by_pattern.return_value = None
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _find_tools

        result = await _find_tools("nothing")
        assert result.success is True
        assert result.data["tools"] == []

    @pytest.mark.asyncio
    async def test_find_tools_exception(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.side_effect = RuntimeError("boom")
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _find_tools

        result = await _find_tools("test")
        assert result.success is False
        assert "boom" in result.error

    @pytest.mark.asyncio
    async def test_get_tool_spec_success(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.tool_specification.return_value = {"function": {"name": "tool1"}}
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _get_tool_spec

        result = await _get_tool_spec("tool1")
        assert result.success is True
        assert result.data == {"function": {"name": "tool1"}}

    @pytest.mark.asyncio
    async def test_get_tool_spec_exception(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.tool_specification.side_effect = KeyError("not found")
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _get_tool_spec

        result = await _get_tool_spec("bad_tool")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_list_categories_success(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.get_tool_types.return_value = ["bio", "chem", "med"]
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _list_categories

        result = await _list_categories()
        assert result.success is True
        assert result.data["categories"] == ["bio", "chem", "med"]
        assert result.data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_categories_exception(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.get_tool_types.side_effect = RuntimeError("fail")
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _list_categories

        result = await _list_categories()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.return_all_loaded_tools.return_value = ["t1", "t2"]
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        assert await skill.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_empty_tools(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.return_all_loaded_tools.return_value = []
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        assert await skill.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        with patch(
            "labclaw.skills.tooluniverse._get_tu",
            side_effect=ImportError("no tooluniverse"),
        ):
            skill = ToolUniverseSkill()
            assert await skill.health_check() is False

    def test_configure_reset(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        tu_mod._tu_instance = MagicMock()
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        skill.configure(reset=True)
        assert tu_mod._tu_instance is None

    def test_configure_no_reset(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        sentinel = MagicMock()
        tu_mod._tu_instance = sentinel
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        skill.configure(other="value")
        assert tu_mod._tu_instance is sentinel

    def test_get_tu_lazy_init(self) -> None:
        mock_tu_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.return_all_loaded_tools.return_value = ["t1"]
        mock_tu_class.return_value = mock_instance

        with patch("labclaw.skills.tooluniverse.ToolUniverse", mock_tu_class, create=True):
            with patch.dict("sys.modules", {"tooluniverse": MagicMock(ToolUniverse=mock_tu_class)}):
                from labclaw.skills.tooluniverse import _get_tu

                result = _get_tu()
                assert result is mock_instance
                mock_instance.load_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_tool_no_arguments(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = "simple result"
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _run_tool

        result = await _run_tool("simple_tool")
        assert result.success is True
        mock_tu.run.assert_called_once_with({"name": "simple_tool", "arguments": {}})

    @pytest.mark.asyncio
    async def test_run_tool_error_status_unknown(self) -> None:
        import labclaw.skills.tooluniverse as tu_mod

        mock_tu = MagicMock()
        mock_tu.run.return_value = {"status": "error"}
        tu_mod._tu_instance = mock_tu

        from labclaw.skills.tooluniverse import _run_tool

        result = await _run_tool("err_tool")
        assert result.success is False
        assert result.error == "Unknown error"


# ---------------------------------------------------------------------------
# Test: BiomniSkill (real SDK integration)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_biomni_singleton():
    """Reset the Biomni agent singleton before each test."""
    import labclaw.skills.biomni as bio_mod

    original = bio_mod._biomni_agent
    bio_mod._biomni_agent = None
    yield
    bio_mod._biomni_agent = original


class TestBiomniSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        assert isinstance(BiomniSkill(), CloudSkill)

    def test_metadata(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        assert skill.metadata.name == "biomni"
        assert SkillCapability.DATA_ANALYSIS in skill.metadata.capabilities
        assert skill.metadata.requires_api_key is True

    def test_get_tools_returns_three(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        tools = BiomniSkill().get_tools()
        assert len(tools) == 3
        names = {t.name for t in tools}
        assert names == {"biomni_go", "biomni_list_tools", "biomni_add_data"}

    def test_init_custom_params(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill(llm="gpt-4", data_path="/tmp/data")
        assert skill._llm == "gpt-4"
        assert skill._data_path == "/tmp/data"

    @pytest.mark.asyncio
    async def test_biomni_go_success(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        mock_agent.go.return_value = "Analysis complete: gene X is significant"
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_go

        result = await _biomni_go("What is gene X?")
        assert result.success is True
        assert "gene X" in result.data["result"]
        assert result.data["query"] == "What is gene X?"

    @pytest.mark.asyncio
    async def test_biomni_go_exception(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        mock_agent.go.side_effect = RuntimeError("API limit")
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_go

        result = await _biomni_go("test query")
        assert result.success is False
        assert "API limit" in result.error

    @pytest.mark.asyncio
    async def test_biomni_list_tools_success(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        mock_agent.list_custom_tools.return_value = ["tool_a", "tool_b"]
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_list_tools

        result = await _biomni_list_tools()
        assert result.success is True
        assert result.data["tools"] == ["tool_a", "tool_b"]

    @pytest.mark.asyncio
    async def test_biomni_list_tools_exception(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        mock_agent.list_custom_tools.side_effect = RuntimeError("fail")
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_list_tools

        result = await _biomni_list_tools()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_biomni_add_data_success(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_add_data

        result = await _biomni_add_data("my_data", path="/tmp/data.csv", description="test data")
        assert result.success is True
        assert result.data["added"] == "my_data"
        assert result.data["path"] == "/tmp/data.csv"
        mock_agent.add_data.assert_called_once_with(
            name="my_data", path="/tmp/data.csv", description="test data"
        )

    @pytest.mark.asyncio
    async def test_biomni_add_data_exception(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        mock_agent.add_data.side_effect = FileNotFoundError("no file")
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_add_data

        result = await _biomni_add_data("bad", path="/missing")
        assert result.success is False
        assert "no file" in result.error

    @pytest.mark.asyncio
    async def test_health_check_import_success(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        with patch.dict("sys.modules", {"biomni": MagicMock(), "biomni.agent": MagicMock()}):
            assert await skill.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_import_failure(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        with patch.dict("sys.modules", {"biomni": None, "biomni.agent": None}):
            with patch("builtins.__import__", side_effect=ImportError("no biomni")):
                assert await skill.health_check() is False

    def test_configure_llm(self) -> None:
        import labclaw.skills.biomni as bio_mod

        bio_mod._biomni_agent = MagicMock()
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        skill.configure(llm="gpt-4")
        assert skill._llm == "gpt-4"
        assert bio_mod._biomni_agent is None

    def test_configure_data_path(self) -> None:
        import labclaw.skills.biomni as bio_mod

        bio_mod._biomni_agent = MagicMock()
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        skill.configure(data_path="/new/path")
        assert skill._data_path == "/new/path"
        assert bio_mod._biomni_agent is None

    def test_configure_no_reset(self) -> None:
        import labclaw.skills.biomni as bio_mod

        sentinel = MagicMock()
        bio_mod._biomni_agent = sentinel
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        skill.configure(other="value")
        assert bio_mod._biomni_agent is sentinel

    def test_get_agent_lazy_init(self) -> None:
        mock_a1_class = MagicMock()
        mock_instance = MagicMock()
        mock_a1_class.return_value = mock_instance

        mock_biomni_agent = MagicMock()
        mock_biomni_agent.A1 = mock_a1_class

        with patch.dict(
            "sys.modules",
            {"biomni": MagicMock(), "biomni.agent": mock_biomni_agent},
        ):
            from labclaw.skills.biomni import _get_agent

            result = _get_agent(llm="test-llm", data_path="/test")
            assert result is mock_instance

    @pytest.mark.asyncio
    async def test_biomni_go_truncates_long_result(self) -> None:
        import labclaw.skills.biomni as bio_mod

        mock_agent = MagicMock()
        mock_agent.go.return_value = "x" * 10000
        bio_mod._biomni_agent = mock_agent

        from labclaw.skills.biomni import _biomni_go

        result = await _biomni_go("long query")
        assert result.success is True
        assert len(result.data["result"]) <= 5000


# ---------------------------------------------------------------------------
# Test: KDenseSkill (real MCP integration)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_kdense_session():
    """Reset the K-Dense MCP session before each test."""
    import labclaw.skills.kdense as kd_mod

    orig_session = kd_mod._mcp_session
    orig_transport = kd_mod._mcp_transport
    kd_mod._mcp_session = None
    kd_mod._mcp_transport = None
    yield
    kd_mod._mcp_session = orig_session
    kd_mod._mcp_transport = orig_transport


class TestKDenseSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        assert isinstance(KDenseSkill(), CloudSkill)

    def test_metadata(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        assert skill.metadata.name == "kdense"
        assert SkillCapability.LITERATURE_SEARCH in skill.metadata.capabilities

    def test_get_tools_returns_three(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        tools = KDenseSkill().get_tools()
        assert len(tools) == 3
        names = {t.name for t in tools}
        assert names == {"kdense_find_skills", "kdense_read_skill", "kdense_list_skills"}

    @pytest.mark.asyncio
    async def test_find_skills_success(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [{"name": "skill1", "desc": "a skill"}]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _find_skills

        result = await _find_skills("bioinformatics")
        assert result.success is True
        assert result.data["query"] == "bioinformatics"
        mock_session.call_tool.assert_called_once_with(
            "find_helpful_skills",
            arguments={"description": "bioinformatics", "limit": 5},
        )

    @pytest.mark.asyncio
    async def test_find_skills_no_session(self) -> None:
        from labclaw.skills.kdense import _find_skills

        with patch("labclaw.skills.kdense._ensure_mcp_session", return_value=None):
            result = await _find_skills("test")
        assert result.success is False
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_find_skills_exception(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("MCP error"))
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _find_skills

        result = await _find_skills("test")
        assert result.success is False
        assert "MCP error" in result.error

    @pytest.mark.asyncio
    async def test_find_skills_no_content_attr(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_result = "raw string result"
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _find_skills

        result = await _find_skills("test")
        assert result.success is True
        assert result.data["skills"] == "raw string result"

    @pytest.mark.asyncio
    async def test_read_skill_success(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = "Skill document content here"
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _read_skill

        result = await _read_skill("pcr_protocol")
        assert result.success is True
        assert result.data["skill_name"] == "pcr_protocol"
        assert result.data["content"] == "Skill document content here"

    @pytest.mark.asyncio
    async def test_read_skill_no_session(self) -> None:
        from labclaw.skills.kdense import _read_skill

        with patch("labclaw.skills.kdense._ensure_mcp_session", return_value=None):
            result = await _read_skill("test")
        assert result.success is False
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_read_skill_exception(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _read_skill

        result = await _read_skill("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_read_skill_no_content_attr(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=42)
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _read_skill

        result = await _read_skill("test")
        assert result.success is True
        assert result.data["content"] == "42"

    @pytest.mark.asyncio
    async def test_list_all_skills_success(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = ["skill1", "skill2", "skill3"]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _list_all_skills

        result = await _list_all_skills()
        assert result.success is True
        mock_session.call_tool.assert_called_once_with("list_skills", arguments={})

    @pytest.mark.asyncio
    async def test_list_all_skills_no_session(self) -> None:
        from labclaw.skills.kdense import _list_all_skills

        with patch("labclaw.skills.kdense._ensure_mcp_session", return_value=None):
            result = await _list_all_skills()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_list_all_skills_exception(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _list_all_skills

        result = await _list_all_skills()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_list_all_skills_no_content_attr(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value="raw")
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import _list_all_skills

        result = await _list_all_skills()
        assert result.success is True
        assert result.data["skills"] == "raw"

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        kd_mod._mcp_session = mock_session

        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        assert await skill.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_no_session(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        with patch("labclaw.skills.kdense._ensure_mcp_session", return_value=None):
            assert await skill.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        with patch(
            "labclaw.skills.kdense._ensure_mcp_session",
            side_effect=RuntimeError("fail"),
        ):
            assert await skill.health_check() is False

    def test_configure_reset(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_transport = AsyncMock()
        kd_mod._mcp_session = MagicMock()
        kd_mod._mcp_transport = mock_transport

        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        skill.configure(reset=True)
        assert kd_mod._mcp_session is None
        assert kd_mod._mcp_transport is None

    def test_configure_reset_no_transport(self) -> None:
        import labclaw.skills.kdense as kd_mod

        kd_mod._mcp_session = MagicMock()
        kd_mod._mcp_transport = None

        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        skill.configure(reset=True)
        assert kd_mod._mcp_session is None

    def test_configure_no_reset(self) -> None:
        import labclaw.skills.kdense as kd_mod

        sentinel = MagicMock()
        kd_mod._mcp_session = sentinel

        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        skill.configure(other="value")
        assert kd_mod._mcp_session is sentinel

    @pytest.mark.asyncio
    async def test_ensure_mcp_session_cached(self) -> None:
        import labclaw.skills.kdense as kd_mod

        sentinel = AsyncMock()
        kd_mod._mcp_session = sentinel

        from labclaw.skills.kdense import _ensure_mcp_session

        result = await _ensure_mcp_session()
        assert result is sentinel

    @pytest.mark.asyncio
    async def test_ensure_mcp_session_success(self) -> None:
        """Cover the full _ensure_mcp_session connection path."""
        import labclaw.skills.kdense as kd_mod

        mock_session = AsyncMock()
        mock_transport = AsyncMock()
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_transport.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))

        mock_client_session_cls = MagicMock(return_value=mock_session)
        mock_stdio_params_cls = MagicMock()
        mock_stdio_client_fn = MagicMock(return_value=mock_transport)

        mock_mcp = MagicMock()
        mock_mcp.ClientSession = mock_client_session_cls
        mock_mcp.StdioServerParameters = mock_stdio_params_cls

        mock_mcp_client_stdio = MagicMock()
        mock_mcp_client_stdio.stdio_client = mock_stdio_client_fn

        with patch.dict(
            "sys.modules",
            {
                "mcp": mock_mcp,
                "mcp.client": MagicMock(),
                "mcp.client.stdio": mock_mcp_client_stdio,
            },
        ):
            kd_mod._mcp_session = None
            kd_mod._mcp_transport = None
            result = await kd_mod._ensure_mcp_session()
            assert result is mock_session
            mock_session.initialize.assert_called_once()
            assert kd_mod._mcp_session is mock_session
            assert kd_mod._mcp_transport is mock_transport

    @pytest.mark.asyncio
    async def test_ensure_mcp_session_connection_failure(self) -> None:
        """Cover the exception path in _ensure_mcp_session."""
        import labclaw.skills.kdense as kd_mod

        mock_mcp = MagicMock()
        mock_mcp.StdioServerParameters = MagicMock()

        mock_mcp_client_stdio = MagicMock()
        mock_transport = AsyncMock()
        mock_transport.__aenter__ = AsyncMock(side_effect=RuntimeError("connect failed"))
        mock_mcp_client_stdio.stdio_client = MagicMock(return_value=mock_transport)

        with patch.dict(
            "sys.modules",
            {
                "mcp": mock_mcp,
                "mcp.client": MagicMock(),
                "mcp.client.stdio": mock_mcp_client_stdio,
            },
        ):
            kd_mod._mcp_session = None
            result = await kd_mod._ensure_mcp_session()
            assert result is None

    def test_configure_reset_transport_aexit_fails(self) -> None:
        import labclaw.skills.kdense as kd_mod

        mock_transport = MagicMock()
        mock_loop = MagicMock()
        mock_loop.run_until_complete.side_effect = RuntimeError("loop closed")

        kd_mod._mcp_session = MagicMock()
        kd_mod._mcp_transport = mock_transport

        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        with patch("asyncio.get_event_loop", return_value=mock_loop):
            skill.configure(reset=True)
        # Should still clear session/transport despite exception
        assert kd_mod._mcp_session is None
        assert kd_mod._mcp_transport is None


# ---------------------------------------------------------------------------
# Test: WriteSkill
# ---------------------------------------------------------------------------


class TestWriteSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.write import WriteSkill

        assert isinstance(WriteSkill(), CloudSkill)

    def test_get_tools_returns_two(self) -> None:
        from labclaw.skills.write import WriteSkill

        tools = WriteSkill().get_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "generate_section" in names
        assert "format_citation" in names

    @pytest.mark.asyncio
    async def test_generate_section_template_fallback(self) -> None:
        from labclaw.skills.write import _generate_section

        result = await _generate_section("results", findings=["Found 3 patterns."])
        assert result.success is True
        assert "3 patterns" in result.data["text"]
        assert result.data["llm_used"] is False

    @pytest.mark.asyncio
    async def test_generate_section_unknown_type(self) -> None:
        from labclaw.skills.write import _generate_section

        result = await _generate_section("bogus")
        assert result.success is False
        assert "Unknown section type" in result.error

    @pytest.mark.asyncio
    async def test_generate_section_empty_input(self) -> None:
        from labclaw.skills.write import _generate_section

        result = await _generate_section("abstract")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_generate_section_with_llm(self) -> None:
        from labclaw.skills.write import _generate_section

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Generated text."

        result = await _generate_section(
            "abstract",
            findings=["Finding 1"],
            llm_provider=mock_llm,
        )
        assert result.success is True
        assert result.data["llm_used"] is True
        assert "Generated text" in result.data["text"]

    @pytest.mark.asyncio
    async def test_generate_section_llm_error(self) -> None:
        from labclaw.skills.write import _generate_section

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = RuntimeError("LLM down")

        result = await _generate_section(
            "abstract",
            findings=["F1"],
            llm_provider=mock_llm,
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_generate_section_with_data_context_only(self) -> None:
        from labclaw.skills.write import _generate_section

        result = await _generate_section("summary", data_context="Some data")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_generate_section_with_findings_and_context(self) -> None:
        from labclaw.skills.write import _generate_section

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Result text."
        result = await _generate_section(
            "results",
            findings=["F1", "F2"],
            data_context="Extra context here",
            llm_provider=mock_llm,
        )
        assert result.success is True
        assert result.data["llm_used"] is True

    @pytest.mark.asyncio
    async def test_format_citation_apa(self) -> None:
        from labclaw.skills.write import _format_citation

        result = await _format_citation(
            "Neural Dynamics",
            authors=["Smith J", "Lee K"],
            year=2024,
            journal="Nature",
            doi="10.1234/abc",
        )
        assert result.success is True
        assert "Smith" in result.data["citation"]
        assert "2024" in result.data["citation"]

    @pytest.mark.asyncio
    async def test_format_citation_non_apa(self) -> None:
        from labclaw.skills.write import _format_citation

        result = await _format_citation("Title", style="mla")
        assert result.success is True
        assert "n.d." in result.data["citation"]

    @pytest.mark.asyncio
    async def test_format_citation_mla_with_doi(self) -> None:
        from labclaw.skills.write import _format_citation

        result = await _format_citation("Title", style="mla", doi="10.1234/abc")
        assert result.success is True
        assert "doi:10.1234/abc" in result.data["citation"]

    @pytest.mark.asyncio
    async def test_health_check_always_true(self) -> None:
        from labclaw.skills.write import WriteSkill

        assert await WriteSkill().health_check() is True

    def test_configure_llm(self) -> None:
        from labclaw.skills.write import WriteSkill

        skill = WriteSkill()
        mock_llm = MagicMock()
        skill.configure(llm_provider=mock_llm)
        assert skill._llm_provider is mock_llm

    def test_template_section_no_findings(self) -> None:
        from labclaw.skills.write import _template_section

        text = _template_section("results", [], "")
        assert "[RESULTS]" in text

    def test_template_section_with_context(self) -> None:
        from labclaw.skills.write import _template_section

        text = _template_section("methods", ["Step 1"], "Extra info")
        assert "Step 1" in text
        assert "Extra info" in text


# ---------------------------------------------------------------------------
# Test: LifeSciSkill
# ---------------------------------------------------------------------------


class TestLifeSciSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.lifesci import LifeSciSkill

        assert isinstance(LifeSciSkill(), CloudSkill)

    def test_get_tools_returns_two(self) -> None:
        from labclaw.skills.lifesci import LifeSciSkill

        tools = LifeSciSkill().get_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "reason_lifesci" in names
        assert "design_experiment" in names

    @pytest.mark.asyncio
    async def test_reason_lifesci_no_llm(self) -> None:
        from labclaw.skills.lifesci import _reason_lifesci

        result = await _reason_lifesci("What is CRISPR?")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_reason_lifesci_with_llm(self) -> None:
        from labclaw.skills.lifesci import _reason_lifesci

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "CRISPR is a genome editing tool."

        result = await _reason_lifesci(
            "What is CRISPR?",
            context="Gene therapy research",
            domain="genomics",
            llm_provider=mock_llm,
        )
        assert result.success is True
        assert result.data["llm_used"] is True

    @pytest.mark.asyncio
    async def test_reason_lifesci_llm_error(self) -> None:
        from labclaw.skills.lifesci import _reason_lifesci

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = RuntimeError("fail")

        result = await _reason_lifesci("q", llm_provider=mock_llm)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_reason_lifesci_general_domain(self) -> None:
        from labclaw.skills.lifesci import _reason_lifesci

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Answer"

        result = await _reason_lifesci("q", llm_provider=mock_llm)
        assert result.success is True
        assert result.data["domain"] == "general"

    @pytest.mark.asyncio
    async def test_design_experiment_no_llm(self) -> None:
        from labclaw.skills.lifesci import _design_experiment

        result = await _design_experiment("Gene X causes behavior Y")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_design_experiment_with_llm(self) -> None:
        from labclaw.skills.lifesci import _design_experiment

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Use optogenetics to test..."

        result = await _design_experiment(
            "Gene X causes behavior Y",
            constraints="Limited to mice",
            available_equipment=["two-photon microscope"],
            llm_provider=mock_llm,
        )
        assert result.success is True
        assert result.data["llm_used"] is True

    @pytest.mark.asyncio
    async def test_design_experiment_llm_error(self) -> None:
        from labclaw.skills.lifesci import _design_experiment

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = RuntimeError("fail")

        result = await _design_experiment("hyp", llm_provider=mock_llm)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_design_experiment_no_constraints(self) -> None:
        from labclaw.skills.lifesci import _design_experiment

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Design result"

        result = await _design_experiment("hyp", llm_provider=mock_llm)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_health_check_no_llm(self) -> None:
        from labclaw.skills.lifesci import LifeSciSkill

        assert await LifeSciSkill().health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_with_llm(self) -> None:
        from labclaw.skills.lifesci import LifeSciSkill

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "pong"
        skill = LifeSciSkill(llm_provider=mock_llm)
        assert await skill.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_llm_error(self) -> None:
        from labclaw.skills.lifesci import LifeSciSkill

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = RuntimeError("fail")
        skill = LifeSciSkill(llm_provider=mock_llm)
        assert await skill.health_check() is False

    def test_configure_llm(self) -> None:
        from labclaw.skills.lifesci import LifeSciSkill

        skill = LifeSciSkill()
        mock_llm = MagicMock()
        skill.configure(llm_provider=mock_llm)
        assert skill._llm_provider is mock_llm


# ---------------------------------------------------------------------------
# Test: Config
# ---------------------------------------------------------------------------


class TestSkillsConfig:
    def test_defaults(self) -> None:
        from labclaw.config import SkillsConfig

        cfg = SkillsConfig()
        assert cfg.enabled is True
        assert cfg.auto_register_builtins is True
        assert cfg.enabled_skills == []

    def test_in_labclaw_config(self) -> None:
        from labclaw.config import LabClawConfig

        cfg = LabClawConfig()
        assert cfg.skills.enabled is True


# ---------------------------------------------------------------------------
# Test: Agent integration
# ---------------------------------------------------------------------------


class TestAgentSkillIntegration:
    def test_collect_skill_tools_empty(self) -> None:
        from labclaw.agents import _collect_skill_tools

        tools = _collect_skill_tools()
        # Global registry may or may not have skills
        assert isinstance(tools, list)

    def test_create_lab_assistant_with_skills(self) -> None:
        from labclaw.agents import create_lab_assistant

        mock_llm = MagicMock()
        runtime = create_lab_assistant(mock_llm, include_skills=True)
        assert len(runtime.tools) >= 7  # At least built-in tools

    def test_create_lab_assistant_without_skills(self) -> None:
        from labclaw.agents import create_lab_assistant

        mock_llm = MagicMock()
        runtime = create_lab_assistant(mock_llm, include_skills=False)
        assert len(runtime.tools) == 7  # Exactly built-in tools

    def test_create_experiment_designer_with_skills(self) -> None:
        from labclaw.agents import create_experiment_designer

        mock_llm = MagicMock()
        runtime = create_experiment_designer(mock_llm, include_skills=True)
        assert len(runtime.tools) >= 7


class TestCollectSkillToolsException:
    def test_exception_returns_empty(self) -> None:
        from labclaw.agents import _collect_skill_tools

        with patch(
            "labclaw.skills.registry.skill_registry",
        ) as mock_reg:
            mock_reg.get_all_tools.side_effect = RuntimeError("fail")
            tools = _collect_skill_tools()
            assert tools == []


# ---------------------------------------------------------------------------
# Test: API router
# ---------------------------------------------------------------------------


class TestSkillsAPIRouter:
    def test_list_skills_empty(self) -> None:
        from labclaw.api.routers.skills import list_skills

        # May return empty or pre-registered skills
        result = list_skills()
        assert isinstance(result, list)

    def test_list_skills_by_capability_invalid(self) -> None:
        from fastapi import HTTPException

        from labclaw.api.routers.skills import list_skills_by_capability

        with pytest.raises(HTTPException) as exc_info:
            list_skills_by_capability("bogus_capability")
        assert exc_info.value.status_code == 400

    def test_list_skill_tools(self) -> None:
        from labclaw.api.routers.skills import list_skill_tools

        result = list_skill_tools()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_skill_tool_not_found(self) -> None:
        from fastapi import HTTPException

        from labclaw.api.routers.skills import SkillExecuteRequest, execute_skill_tool

        req = SkillExecuteRequest(tool_name="nonexistent")
        with pytest.raises(HTTPException) as exc_info:
            await execute_skill_tool(req)
        assert exc_info.value.status_code == 404


class TestSkillsAPIRouterCapability:
    def test_list_by_valid_capability(self) -> None:
        from labclaw.api.routers.skills import list_skills_by_capability
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        with patch("labclaw.skills.registry.skill_registry", reg):
            result = list_skills_by_capability("general_reasoning")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_execute_skill_tool_success(self) -> None:
        from labclaw.api.routers.skills import (
            SkillExecuteRequest,
            execute_skill_tool,
        )
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        with patch("labclaw.skills.registry.skill_registry", reg):
            req = SkillExecuteRequest(tool_name="stub_tool", arguments={"x": 1})
            result = await execute_skill_tool(req)
        assert result.success is True


# ---------------------------------------------------------------------------
# Test: CLI
# ---------------------------------------------------------------------------


class TestSkillsCLI:
    def test_get_builtin_skills(self) -> None:
        from labclaw.cli import _get_builtin_skills

        classes = _get_builtin_skills()
        assert len(classes) == 5

    def test_skills_cmd_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd

        _skills_cmd([])
        captured = capsys.readouterr()
        assert "list" in captured.out
        assert "register" in captured.out

    def test_skills_cmd_list_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd
        from labclaw.skills.registry import SkillRegistry

        empty_reg = SkillRegistry()
        with patch("labclaw.skills.registry.skill_registry", empty_reg):
            _skills_cmd(["list"])
        captured = capsys.readouterr()
        assert "No skills registered" in captured.out

    def test_skills_cmd_register(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd

        with patch("labclaw.skills.registry.skill_registry") as mock_reg:
            mock_reg.register = MagicMock()
            _skills_cmd(["register"])
            captured = capsys.readouterr()
            assert "Registered" in captured.out


class TestSkillsCLIExtended:
    def test_skills_cmd_tools(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd
        from labclaw.skills.registry import SkillRegistry

        empty_reg = SkillRegistry()
        with patch("labclaw.skills.registry.skill_registry", empty_reg):
            _skills_cmd(["tools"])
        captured = capsys.readouterr()
        assert "No skill tools" in captured.out

    def test_skills_cmd_health(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd
        from labclaw.skills.registry import SkillRegistry

        empty_reg = SkillRegistry()
        with patch("labclaw.skills.registry.skill_registry", empty_reg):
            _skills_cmd(["health"])
        captured = capsys.readouterr()
        assert "No skills registered" in captured.out

    def test_skills_cmd_list_with_skills(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        with patch("labclaw.skills.registry.skill_registry", reg):
            _skills_cmd(["list"])
        captured = capsys.readouterr()
        assert "stub" in captured.out

    def test_skills_cmd_tools_with_skills(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        with patch("labclaw.skills.registry.skill_registry", reg):
            _skills_cmd(["tools"])
        captured = capsys.readouterr()
        assert "stub_tool" in captured.out

    def test_skills_cmd_health_with_skills(self, capsys: pytest.CaptureFixture[str]) -> None:
        from labclaw.cli import _skills_cmd
        from labclaw.skills.registry import SkillRegistry

        reg = SkillRegistry()
        reg.register(StubSkill())
        with patch("labclaw.skills.registry.skill_registry", reg):
            _skills_cmd(["health"])
        captured = capsys.readouterr()
        assert "OK" in captured.out


# ---------------------------------------------------------------------------
# Test: skills __init__ re-exports
# ---------------------------------------------------------------------------


class TestSkillsInit:
    def test_exports(self) -> None:
        from labclaw.skills import (
            CloudSkill,
            SkillCapability,
            SkillMetadata,
            SkillRegistry,
            skill_registry,
        )

        assert CloudSkill is not None
        assert SkillCapability is not None
        assert SkillMetadata is not None
        assert SkillRegistry is not None
        assert skill_registry is not None


# ---------------------------------------------------------------------------
# Test: LifeSciMCPSkill
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_lifesci_mcp_sessions():
    """Reset the LifeSci MCP sessions before each test."""
    import labclaw.skills.lifesci_mcp as lm_mod

    orig_sessions = dict(lm_mod._mcp_sessions)
    orig_transports = dict(lm_mod._mcp_transports)
    lm_mod._mcp_sessions.clear()
    lm_mod._mcp_transports.clear()
    yield
    lm_mod._mcp_sessions.clear()
    lm_mod._mcp_sessions.update(orig_sessions)
    lm_mod._mcp_transports.clear()
    lm_mod._mcp_transports.update(orig_transports)


class TestLifeSciMCPSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        assert isinstance(LifeSciMCPSkill(), CloudSkill)

    def test_metadata(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        skill = LifeSciMCPSkill()
        assert skill.metadata.name == "lifesci_mcp"
        assert SkillCapability.LITERATURE_SEARCH in skill.metadata.capabilities

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

    # -- _ensure_session tests --

    @pytest.mark.asyncio
    async def test_ensure_session_cached(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _ensure_session

        sentinel = AsyncMock()
        lm_mod._mcp_sessions["pubmed"] = sentinel
        result = await _ensure_session("pubmed")
        assert result is sentinel

    @pytest.mark.asyncio
    async def test_ensure_session_unknown_key(self) -> None:
        from labclaw.skills.lifesci_mcp import _ensure_session

        result = await _ensure_session("unknown_server")
        assert result is None

    @pytest.mark.asyncio
    async def test_ensure_session_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod

        mock_session = AsyncMock()
        mock_transport = AsyncMock()
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_transport.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))

        mock_client_session_cls = MagicMock(return_value=mock_session)
        mock_stdio_params_cls = MagicMock()
        mock_stdio_client_fn = MagicMock(return_value=mock_transport)

        mock_mcp = MagicMock()
        mock_mcp.ClientSession = mock_client_session_cls
        mock_mcp.StdioServerParameters = mock_stdio_params_cls

        mock_mcp_client_stdio = MagicMock()
        mock_mcp_client_stdio.stdio_client = mock_stdio_client_fn

        with patch.dict(
            "sys.modules",
            {
                "mcp": mock_mcp,
                "mcp.client": MagicMock(),
                "mcp.client.stdio": mock_mcp_client_stdio,
            },
        ):
            result = await lm_mod._ensure_session("pubmed")
            assert result is mock_session
            assert lm_mod._mcp_sessions["pubmed"] is mock_session
            assert lm_mod._mcp_transports["pubmed"] is mock_transport

    @pytest.mark.asyncio
    async def test_ensure_session_connection_failure(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod

        mock_mcp = MagicMock()
        mock_mcp.StdioServerParameters = MagicMock()

        mock_transport = AsyncMock()
        mock_transport.__aenter__ = AsyncMock(side_effect=RuntimeError("fail"))

        mock_mcp_client_stdio = MagicMock()
        mock_mcp_client_stdio.stdio_client = MagicMock(return_value=mock_transport)

        with patch.dict(
            "sys.modules",
            {
                "mcp": mock_mcp,
                "mcp.client": MagicMock(),
                "mcp.client.stdio": mock_mcp_client_stdio,
            },
        ):
            result = await lm_mod._ensure_session("pubmed")
            assert result is None

    # -- Tool function tests --

    @pytest.mark.asyncio
    async def test_search_pubmed_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_pubmed

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [{"title": "Paper 1"}]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        lm_mod._mcp_sessions["pubmed"] = mock_session

        result = await _search_pubmed("CRISPR")
        assert result.success is True
        assert result.data["source"] == "pubmed"

    @pytest.mark.asyncio
    async def test_search_pubmed_no_session(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_pubmed

        with patch("labclaw.skills.lifesci_mcp._ensure_session", return_value=None):
            result = await _search_pubmed("test")
        assert result.success is False
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_search_pubmed_exception(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_pubmed

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        lm_mod._mcp_sessions["pubmed"] = mock_session

        result = await _search_pubmed("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_search_pubmed_no_content_attr(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_pubmed

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value="raw")
        lm_mod._mcp_sessions["pubmed"] = mock_session

        result = await _search_pubmed("test")
        assert result.success is True
        assert result.data["results"] == "raw"

    @pytest.mark.asyncio
    async def test_search_biorxiv_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [{"title": "Preprint 1"}]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        lm_mod._mcp_sessions["biorxiv"] = mock_session

        result = await _search_biorxiv("neuroscience")
        assert result.success is True
        assert result.data["source"] == "biorxiv"

    @pytest.mark.asyncio
    async def test_search_biorxiv_no_session(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        with patch("labclaw.skills.lifesci_mcp._ensure_session", return_value=None):
            result = await _search_biorxiv("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_search_biorxiv_exception(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        lm_mod._mcp_sessions["biorxiv"] = mock_session

        result = await _search_biorxiv("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_search_biorxiv_no_content_attr(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_biorxiv

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=123)
        lm_mod._mcp_sessions["biorxiv"] = mock_session

        result = await _search_biorxiv("test")
        assert result.success is True
        assert result.data["results"] == "123"

    @pytest.mark.asyncio
    async def test_query_chembl_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _query_chembl

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = {"compound": "aspirin"}
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        lm_mod._mcp_sessions["chembl"] = mock_session

        result = await _query_chembl("aspirin", query_type="compound")
        assert result.success is True
        assert result.data["source"] == "chembl"

    @pytest.mark.asyncio
    async def test_query_chembl_no_session(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_chembl

        with patch("labclaw.skills.lifesci_mcp._ensure_session", return_value=None):
            result = await _query_chembl("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_query_chembl_exception(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _query_chembl

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        lm_mod._mcp_sessions["chembl"] = mock_session

        result = await _query_chembl("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_query_chembl_no_content_attr(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _query_chembl

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value="raw")
        lm_mod._mcp_sessions["chembl"] = mock_session

        result = await _query_chembl("test")
        assert result.success is True
        assert result.data["results"] == "raw"

    @pytest.mark.asyncio
    async def test_query_opentargets_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _query_opentargets

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = {"target": "BRCA1"}
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        lm_mod._mcp_sessions["opentargets"] = mock_session

        result = await _query_opentargets("BRCA1")
        assert result.success is True
        assert result.data["source"] == "opentargets"

    @pytest.mark.asyncio
    async def test_query_opentargets_no_session(self) -> None:
        from labclaw.skills.lifesci_mcp import _query_opentargets

        with patch("labclaw.skills.lifesci_mcp._ensure_session", return_value=None):
            result = await _query_opentargets("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_query_opentargets_exception(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _query_opentargets

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        lm_mod._mcp_sessions["opentargets"] = mock_session

        result = await _query_opentargets("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_query_opentargets_no_content_attr(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _query_opentargets

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value="raw")
        lm_mod._mcp_sessions["opentargets"] = mock_session

        result = await _query_opentargets("test")
        assert result.success is True
        assert result.data["results"] == "raw"

    @pytest.mark.asyncio
    async def test_search_clinical_trials_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [{"nct_id": "NCT123"}]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        lm_mod._mcp_sessions["clinical_trials"] = mock_session

        result = await _search_clinical_trials("cancer", status="active")
        assert result.success is True
        assert result.data["source"] == "clinical_trials"
        assert result.data["status"] == "active"

    @pytest.mark.asyncio
    async def test_search_clinical_trials_no_session(self) -> None:
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        with patch("labclaw.skills.lifesci_mcp._ensure_session", return_value=None):
            result = await _search_clinical_trials("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_search_clinical_trials_exception(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("fail"))
        lm_mod._mcp_sessions["clinical_trials"] = mock_session

        result = await _search_clinical_trials("test")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_search_clinical_trials_no_content_attr(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import _search_clinical_trials

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value="raw")
        lm_mod._mcp_sessions["clinical_trials"] = mock_session

        result = await _search_clinical_trials("test")
        assert result.success is True
        assert result.data["results"] == "raw"

    # -- Skill-level tests --

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        lm_mod._mcp_sessions["pubmed"] = AsyncMock()
        skill = LifeSciMCPSkill()
        assert await skill.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_all_fail(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            return_value=None,
        ):
            skill = LifeSciMCPSkill()
            assert await skill.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_exception_continues(self) -> None:
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        with patch(
            "labclaw.skills.lifesci_mcp._ensure_session",
            side_effect=RuntimeError("fail"),
        ):
            skill = LifeSciMCPSkill()
            assert await skill.health_check() is False

    def test_configure_reset(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        mock_transport = MagicMock()
        mock_loop = MagicMock()
        lm_mod._mcp_sessions["pubmed"] = MagicMock()
        lm_mod._mcp_transports["pubmed"] = mock_transport

        skill = LifeSciMCPSkill()
        with patch("asyncio.get_event_loop", return_value=mock_loop):
            skill.configure(reset=True)
        assert len(lm_mod._mcp_sessions) == 0
        assert len(lm_mod._mcp_transports) == 0

    def test_configure_reset_aexit_fails(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        mock_transport = MagicMock()
        mock_loop = MagicMock()
        mock_loop.run_until_complete.side_effect = RuntimeError("loop closed")
        lm_mod._mcp_sessions["pubmed"] = MagicMock()
        lm_mod._mcp_transports["pubmed"] = mock_transport

        skill = LifeSciMCPSkill()
        with patch("asyncio.get_event_loop", return_value=mock_loop):
            skill.configure(reset=True)
        assert len(lm_mod._mcp_sessions) == 0

    def test_configure_no_reset(self) -> None:
        import labclaw.skills.lifesci_mcp as lm_mod
        from labclaw.skills.lifesci_mcp import LifeSciMCPSkill

        sentinel = MagicMock()
        lm_mod._mcp_sessions["pubmed"] = sentinel

        skill = LifeSciMCPSkill()
        skill.configure(other="value")
        assert lm_mod._mcp_sessions["pubmed"] is sentinel


# ---------------------------------------------------------------------------
# Test: Cloud Brain Server (server.py)
# ---------------------------------------------------------------------------


class TestCloudBrainServer:
    def test_models_instantiation(self) -> None:
        from labclaw.skills.server import (
            ExecuteRequest,
            ExecuteResponse,
            InventoryCategory,
            InventoryResponse,
            ToolInfo,
        )

        req = ExecuteRequest(tool_name="test_tool", arguments={"x": 1})
        assert req.tool_name == "test_tool"
        assert req.arguments == {"x": 1}

        req_defaults = ExecuteRequest(tool_name="t")
        assert req_defaults.arguments == {}

        resp = ExecuteResponse(success=True, data={"result": "ok"})
        assert resp.success is True

        resp_err = ExecuteResponse(success=False, error="bad")
        assert resp_err.error == "bad"
        assert resp_err.data is None

        tool_info = ToolInfo(name="t1", description="desc")
        assert tool_info.name == "t1"
        assert tool_info.parameters == {}

        cat = InventoryCategory(
            capability="data_analysis",
            skill_count=2,
            tool_count=5,
            skills=["s1", "s2"],
        )
        assert cat.capability == "data_analysis"

        inv = InventoryResponse(
            total_skills=3,
            total_tools=10,
            categories=[cat],
        )
        assert inv.total_skills == 3

    def test_register_builtin_skills(self) -> None:
        from labclaw.skills.server import _register_builtin_skills, _registry

        # Clear the registry first
        for name in list(_registry._skills):
            _registry.unregister(name)

        _register_builtin_skills()
        assert _registry.count == 5

        # Calling again should not raise (duplicate silently ignored)
        _register_builtin_skills()
        assert _registry.count == 5

    @pytest.mark.asyncio
    async def test_list_skills_endpoint(self) -> None:
        from labclaw.skills.server import _register_builtin_skills, _registry, list_skills

        for name in list(_registry._skills):
            _registry.unregister(name)
        _register_builtin_skills()

        result = await list_skills()
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_list_tools_endpoint(self) -> None:
        from labclaw.skills.server import _register_builtin_skills, _registry, list_tools

        for name in list(_registry._skills):
            _registry.unregister(name)
        _register_builtin_skills()

        result = await list_tools()
        assert len(result) > 0
        assert all(hasattr(t, "name") for t in result)

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self) -> None:
        from labclaw.skills.server import _registry, health_check

        for name in list(_registry._skills):
            _registry.unregister(name)

        _registry.register(StubSkill())
        result = await health_check()
        assert isinstance(result, dict)
        assert result["stub"] is True

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self) -> None:
        from labclaw.skills.server import (
            ExecuteRequest,
            _registry,
            execute_tool,
        )

        for name in list(_registry._skills):
            _registry.unregister(name)

        _registry.register(StubSkill())
        req = ExecuteRequest(tool_name="nonexistent_tool")
        result = await execute_tool(req)
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_success(self) -> None:
        from labclaw.skills.server import (
            ExecuteRequest,
            _registry,
            execute_tool,
        )

        for name in list(_registry._skills):
            _registry.unregister(name)

        _registry.register(StubSkill())
        req = ExecuteRequest(tool_name="stub_tool", arguments={"x": 1})
        result = await execute_tool(req)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_inventory_endpoint(self) -> None:
        from labclaw.skills.server import (
            _register_builtin_skills,
            _registry,
            inventory,
        )

        for name in list(_registry._skills):
            _registry.unregister(name)
        _register_builtin_skills()

        result = await inventory()
        assert result.total_skills == 5
        assert result.total_tools > 0
        assert len(result.categories) > 0

    @pytest.mark.asyncio
    async def test_inventory_with_failing_get_tools(self) -> None:
        from labclaw.skills.server import _registry, inventory

        for name in list(_registry._skills):
            _registry.unregister(name)

        _registry.register(FailingSkill())
        result = await inventory()
        assert result.total_skills == 1

    @pytest.mark.asyncio
    async def test_lifespan(self) -> None:
        from labclaw.skills.server import _lifespan, _registry, app

        for name in list(_registry._skills):
            _registry.unregister(name)

        with patch("labclaw.skills.server._register_builtin_skills") as mock_reg:
            async with _lifespan(app):
                mock_reg.assert_called_once()

    def test_app_exists(self) -> None:
        from labclaw.skills.server import app

        assert app is not None
        assert app.title == "Cloud Brain"
