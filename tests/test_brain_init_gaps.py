"""Cover brain/__init__.py WriteSkill registration failure."""

from __future__ import annotations

from unittest.mock import patch

from labclaw.brain.skills.registry import SkillRegistry


class TestRegisterDefaultsWriteFailure:
    """_register_defaults handles Write constructor failure gracefully."""

    def test_write_exception_logged_gracefully(self) -> None:
        import labclaw.brain as brain_mod

        registry = SkillRegistry()

        with patch(
            "labclaw.brain.skills.write.WriteSkill",
            side_effect=RuntimeError("Write init failed"),
        ):
            brain_mod._register_defaults(registry)

        names = registry.list_skills()
        assert "write" not in names
        assert "inventory" in names
        assert "docs" in names
