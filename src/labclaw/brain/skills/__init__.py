"""Cloud Brain skills — pluggable makerspace and AI capabilities."""

from labclaw.brain.skills.base import CloudSkill, SkillCapability, SkillMetadata
from labclaw.brain.skills.cad_mcp import CadMcpSkill
from labclaw.brain.skills.devices import DevicesSkill
from labclaw.brain.skills.docs import DocsSkill
from labclaw.brain.skills.inventory import InventorySkill
from labclaw.brain.skills.registry import SkillRegistry

__all__ = [
    "CadMcpSkill",
    "CloudSkill",
    "DevicesSkill",
    "DocsSkill",
    "InventorySkill",
    "SkillCapability",
    "SkillMetadata",
    "SkillRegistry",
]
