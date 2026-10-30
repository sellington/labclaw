"""Tests for _register_defaults exception handlers in brain/__init__.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from labclaw.brain.skills.registry import SkillRegistry


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the global registry before each test."""
    import labclaw.brain as brain_mod

    brain_mod._registry = None
    yield
    brain_mod._registry = None


class TestRegisterDefaultsGenericException:
    """Cover the generic Exception handler for Write registration."""

    def test_write_generic_exception_caught(self) -> None:
        """When WriteSkill() raises a non-ImportError, it's caught and logged."""
        import labclaw.brain as brain_mod

        registry = SkillRegistry()

        with patch(
            "labclaw.brain.skills.write.WriteSkill",
            side_effect=ValueError("write init boom"),
        ):
            brain_mod._register_defaults(registry)

        assert "write" not in registry.list_skills()
        assert "inventory" in registry.list_skills()
