"""Cover WriteSkill LLM exception branch."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


class TestWriteSectionException:
    """_write_section catches LLM exception and returns BrainResult(success=False)."""

    @pytest.mark.asyncio
    async def test_write_section_llm_exception_returns_error(self) -> None:
        from labclaw.brain.skills.write import WriteSkill

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = RuntimeError("LLM unavailable")
        skill = WriteSkill(llm_provider=mock_llm)

        result = await skill.execute("write_section", section="methods", context="Protocol")
        assert result.success is False
        assert "LLM unavailable" in (result.error or "")
