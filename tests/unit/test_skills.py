"""Tests for the cloud brain skills module.

Covers: base protocol, registry, all 5 skill adapters, config, CLI, API router.
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
# Test: ToolUniverseSkill
# ---------------------------------------------------------------------------


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

    def test_get_tools_returns_two(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        tools = skill.get_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "search_instruments" in names
        assert "get_instrument_protocol" in names

    @pytest.mark.asyncio
    async def test_search_instruments_unconfigured(self) -> None:
        from labclaw.skills.tooluniverse import _search_instruments

        result = await _search_instruments("microscope")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_get_protocol_unconfigured(self) -> None:
        from labclaw.skills.tooluniverse import _get_protocol

        result = await _get_protocol("inst-1")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_health_check_unconfigured(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        assert await skill.health_check() is False

    def test_configure(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        skill.configure(api_key="key123", base_url="http://example.com")
        assert skill._api_key == "key123"
        assert skill._base_url == "http://example.com"

    @pytest.mark.asyncio
    async def test_search_instruments_api_error(self) -> None:
        from labclaw.skills.tooluniverse import _search_instruments

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = ConnectionError("timeout")
            mock_client.post.side_effect = ConnectionError("timeout")
            mock_cls.return_value = mock_client

            result = await _search_instruments("test", api_key="k", base_url="http://x")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_get_protocol_api_error(self) -> None:
        from labclaw.skills.tooluniverse import _get_protocol

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = ConnectionError("timeout")
            mock_client.post.side_effect = ConnectionError("timeout")
            mock_cls.return_value = mock_client

            result = await _get_protocol("inst-1", api_key="k", base_url="http://x")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        skill = ToolUniverseSkill()
        skill.configure(api_key="k", base_url="http://x")
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = ConnectionError("timeout")
            mock_client.post.side_effect = ConnectionError("timeout")
            mock_cls.return_value = mock_client

            assert await skill.health_check() is False


# ---------------------------------------------------------------------------
# Test: KDenseSkill
# ---------------------------------------------------------------------------


class TestKDenseSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        assert isinstance(KDenseSkill(), CloudSkill)

    def test_get_tools_returns_two(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        tools = KDenseSkill().get_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "search_literature" in names
        assert "synthesize_knowledge" in names

    @pytest.mark.asyncio
    async def test_search_literature_unconfigured(self) -> None:
        from labclaw.skills.kdense import _search_literature

        result = await _search_literature("neuron firing")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_unconfigured(self) -> None:
        from labclaw.skills.kdense import _synthesize_knowledge

        result = await _synthesize_knowledge("CRISPR")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_health_check_unconfigured(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        assert await KDenseSkill().health_check() is False

    def test_configure(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        skill.configure(api_key="k", base_url="http://x")
        assert skill._api_key == "k"

    @pytest.mark.asyncio
    async def test_search_literature_api_error(self) -> None:
        from labclaw.skills.kdense import _search_literature

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = ConnectionError("fail")
            mock_httpx.AsyncClient.return_value = mock_client

            result = await _search_literature("q", api_key="k", base_url="http://x")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_api_error(self) -> None:
        from labclaw.skills.kdense import _synthesize_knowledge

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = ConnectionError("fail")
            mock_httpx.AsyncClient.return_value = mock_client

            result = await _synthesize_knowledge("q", api_key="k", base_url="http://x")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        skill.configure(api_key="k", base_url="http://x")
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = ConnectionError("fail")
            mock_httpx.AsyncClient.return_value = mock_client

            assert await skill.health_check() is False


# ---------------------------------------------------------------------------
# Test: BiomniSkill
# ---------------------------------------------------------------------------


class TestBiomniSkill:
    def test_protocol_compliance(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        assert isinstance(BiomniSkill(), CloudSkill)

    def test_get_tools_returns_two(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        tools = BiomniSkill().get_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "analyze_biomedical" in names
        assert "interpret_results" in names

    @pytest.mark.asyncio
    async def test_analyze_biomedical_unconfigured(self) -> None:
        from labclaw.skills.biomni import _analyze_biomedical

        result = await _analyze_biomedical("cell morphology")
        assert result.success is True
        assert result.data["note"]

    @pytest.mark.asyncio
    async def test_interpret_results_unconfigured(self) -> None:
        from labclaw.skills.biomni import _interpret_results

        result = await _interpret_results([{"metric": "value"}])
        assert result.success is True

    @pytest.mark.asyncio
    async def test_health_check_unconfigured(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        assert await BiomniSkill().health_check() is False

    def test_configure(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        skill.configure(api_key="k", base_url="http://x")
        assert skill._api_key == "k"

    @pytest.mark.asyncio
    async def test_analyze_api_error(self) -> None:
        from labclaw.skills.biomni import _analyze_biomedical

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = ConnectionError("fail")
            mock_httpx.AsyncClient.return_value = mock_client

            result = await _analyze_biomedical("q", api_key="k", base_url="http://x")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_interpret_api_error(self) -> None:
        from labclaw.skills.biomni import _interpret_results

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = ConnectionError("fail")
            mock_httpx.AsyncClient.return_value = mock_client

            result = await _interpret_results([], api_key="k", base_url="http://x")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        skill.configure(api_key="k", base_url="http://x")
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = ConnectionError("fail")
            mock_httpx.AsyncClient.return_value = mock_client

            assert await skill.health_check() is False


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

    @pytest.mark.asyncio
    async def test_generate_section_with_data_context_only(self) -> None:
        from labclaw.skills.write import _generate_section

        result = await _generate_section("summary", data_context="Some data")
        assert result.success is True


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


# ---------------------------------------------------------------------------
# Test: skills __init__ re-exports
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Test: API success paths (coverage for HTTP response handling)
# ---------------------------------------------------------------------------


def _make_mock_response(json_data: dict) -> MagicMock:
    """Create a mock httpx response that returns json_data."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = 200
    return resp


def _make_async_client_mock(
    get_response: MagicMock | None = None,
    post_response: MagicMock | None = None,
) -> MagicMock:
    """Create a mock httpx.AsyncClient context manager."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    if get_response is not None:
        client.get = AsyncMock(return_value=get_response)
    if post_response is not None:
        client.post = AsyncMock(return_value=post_response)
    return client


class TestToolUniverseAPISuccess:
    @pytest.mark.asyncio
    async def test_search_instruments_success(self) -> None:
        from labclaw.skills.tooluniverse import _search_instruments

        resp = _make_mock_response({"tools": [{"id": "t1"}], "total": 1})
        client = _make_async_client_mock(get_response=resp)
        with patch("httpx.AsyncClient", return_value=client):
            result = await _search_instruments("microscope", api_key="k", base_url="http://x")
        assert result.success is True
        assert len(result.data["results"]) == 1

    @pytest.mark.asyncio
    async def test_get_protocol_success(self) -> None:
        from labclaw.skills.tooluniverse import _get_protocol

        resp = _make_mock_response({"protocol": "steps...", "parameters": {"p1": "v1"}})
        client = _make_async_client_mock(get_response=resp)
        with patch("httpx.AsyncClient", return_value=client):
            result = await _get_protocol("inst-1", api_key="k", base_url="http://x")
        assert result.success is True
        assert result.data["protocol"] == "steps..."

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        from labclaw.skills.tooluniverse import ToolUniverseSkill

        resp = _make_mock_response({})
        client = _make_async_client_mock(get_response=resp)
        skill = ToolUniverseSkill()
        skill.configure(api_key="k", base_url="http://x")
        with patch("httpx.AsyncClient", return_value=client):
            assert await skill.health_check() is True


class TestKDenseAPISuccess:
    @pytest.mark.asyncio
    async def test_search_literature_success(self) -> None:
        from labclaw.skills.kdense import _search_literature

        resp = _make_mock_response({"results": [{"title": "Paper A"}], "total": 1})
        client = _make_async_client_mock(get_response=resp)
        with patch("httpx.AsyncClient", return_value=client):
            result = await _search_literature(
                "neuron",
                year_from=2020,
                year_to=2025,
                api_key="k",
                base_url="http://x",
            )
        assert result.success is True
        assert len(result.data["papers"]) == 1

    @pytest.mark.asyncio
    async def test_synthesize_knowledge_success(self) -> None:
        from labclaw.skills.kdense import _synthesize_knowledge

        resp = _make_mock_response(
            {
                "synthesis": "Summary text",
                "key_findings": ["f1"],
                "cited_papers": ["p1"],
            }
        )
        client = _make_async_client_mock(post_response=resp)
        with patch("httpx.AsyncClient", return_value=client):
            result = await _synthesize_knowledge(
                "CRISPR",
                context_papers=["paper1"],
                api_key="k",
                base_url="http://x",
            )
        assert result.success is True
        assert result.data["synthesis"] == "Summary text"

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        resp = _make_mock_response({})
        client = _make_async_client_mock(get_response=resp)
        skill = KDenseSkill()
        skill.configure(api_key="k", base_url="http://x")
        with patch("httpx.AsyncClient", return_value=client):
            assert await skill.health_check() is True


class TestBiomniAPISuccess:
    @pytest.mark.asyncio
    async def test_analyze_biomedical_success(self) -> None:
        from labclaw.skills.biomni import _analyze_biomedical

        resp = _make_mock_response(
            {
                "analysis": "Cell analysis result",
                "confidence": 0.95,
                "references": ["r1"],
            }
        )
        client = _make_async_client_mock(post_response=resp)
        with patch("httpx.AsyncClient", return_value=client):
            result = await _analyze_biomedical("cell morphology", api_key="k", base_url="http://x")
        assert result.success is True
        assert result.data["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_interpret_results_success(self) -> None:
        from labclaw.skills.biomni import _interpret_results

        resp = _make_mock_response(
            {
                "interpretation": "Biologically significant",
                "significance": "High",
                "followup": ["exp1"],
            }
        )
        client = _make_async_client_mock(post_response=resp)
        with patch("httpx.AsyncClient", return_value=client):
            result = await _interpret_results([{"metric": "v"}], api_key="k", base_url="http://x")
        assert result.success is True
        assert result.data["biological_significance"] == "High"

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        resp = _make_mock_response({})
        client = _make_async_client_mock(get_response=resp)
        skill = BiomniSkill()
        skill.configure(api_key="k", base_url="http://x")
        with patch("httpx.AsyncClient", return_value=client):
            assert await skill.health_check() is True


class TestBiomniHealthCheckExcept:
    @pytest.mark.asyncio
    async def test_health_check_enters_except(self) -> None:
        from labclaw.skills.biomni import BiomniSkill

        skill = BiomniSkill()
        skill._api_key = "key"
        skill._base_url = "http://x"
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(side_effect=ConnectionError("net"))
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("httpx.AsyncClient", return_value=mock_client):
            assert await skill.health_check() is False


class TestKDenseHealthCheckExcept:
    @pytest.mark.asyncio
    async def test_health_check_enters_except(self) -> None:
        from labclaw.skills.kdense import KDenseSkill

        skill = KDenseSkill()
        skill._api_key = "key"
        skill._base_url = "http://x"
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(side_effect=ConnectionError("net"))
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("httpx.AsyncClient", return_value=mock_client):
            assert await skill.health_check() is False


class TestWriteAdditionalCoverage:
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
    async def test_format_citation_mla_with_doi(self) -> None:
        from labclaw.skills.write import _format_citation

        result = await _format_citation("Title", style="mla", doi="10.1234/abc")
        assert result.success is True
        assert "doi:10.1234/abc" in result.data["citation"]


class TestCollectSkillToolsException:
    def test_exception_returns_empty(self) -> None:
        from labclaw.agents import _collect_skill_tools

        with patch(
            "labclaw.skills.registry.skill_registry",
        ) as mock_reg:
            mock_reg.get_all_tools.side_effect = RuntimeError("fail")
            tools = _collect_skill_tools()
            assert tools == []


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
