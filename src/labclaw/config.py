"""Configuration loading for MakerClaw / LabClaw."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_SEARCH_PATHS = [
    Path("makerclaw.yaml"),
    Path("labclaw.yaml"),
    Path.home() / ".makerclaw" / "config.yaml",
    Path.home() / ".labclaw" / "config.yaml",
]


class BrainConfig(BaseModel):
    port: int = 18802
    api_keys_env: str = "LABCLAW_API_KEYS"
    rate_limit: str = "60/minute"
    max_request_size: int = 1_048_576
    max_response_size: int = 100_000


class SkillConfig(BaseModel):
    enabled: bool = True
    timeout: int = 30
    lazy_loading: bool = True


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "ANTHROPIC_API_KEY"
    temperature: float = 0.3
    max_tokens: int = 4096


class MakerspaceConfig(BaseModel):
    shop_name: str = "MakerClaw Workshop"
    inventory_db: str = str(Path.home() / ".labclaw" / "inventory.db")
    docs_dir: str = str(Path.home() / ".labclaw" / "docs")
    default_cnc_machine: str = "cubiko-cnc"
    default_printer: str = "bambu-p1s"


class LabclawConfig(BaseModel):
    brain: BrainConfig = Field(default_factory=BrainConfig)
    skills: dict[str, SkillConfig] = Field(default_factory=dict)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    makerspace: MakerspaceConfig = Field(default_factory=MakerspaceConfig)


def load_config(path: Path | None = None) -> LabclawConfig:
    """Load config from file or defaults.

    Search: explicit path -> ./makerclaw.yaml -> ./labclaw.yaml -> ~/.labclaw/config.yaml.
    """
    if path and path.exists():
        return _parse(path)
    for p in _SEARCH_PATHS:
        if p.exists():
            logger.info("Loading config from %s", p)
            return _parse(p)
    logger.debug("No config file found, using defaults")
    return LabclawConfig()


def _parse(path: Path) -> LabclawConfig:
    data = yaml.safe_load(path.read_text()) or {}
    return LabclawConfig(**data)
