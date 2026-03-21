"""Life Science LLM skill — domain-specific reasoning for biology and medicine.

Uses Claude or other LLMs with life-science-tuned system prompts to provide
expert reasoning about biological systems, experimental design, and data.

Maps to: HYPOTHESIZE step (domain reasoning) and GENERAL_REASONING.
"""

from __future__ import annotations

import logging
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)

_LIFESCI_SYSTEM_PROMPT = (
    "You are a life science expert with deep knowledge in molecular biology, "
    "neuroscience, genomics, and experimental design. Provide scientifically "
    "rigorous analysis grounded in current understanding. When uncertain, "
    "state confidence levels and cite relevant biological mechanisms."
)

_EXPERIMENT_DESIGN_PROMPT = (
    "You are an expert in experimental design for biological research. "
    "Consider controls, sample sizes, statistical power, potential confounds, "
    "and ethical requirements. Be specific about protocols and reagents."
)


async def _reason_lifesci(
    question: str,
    *,
    context: str = "",
    domain: str = "general",
    llm_provider: Any = None,
) -> ToolResult:
    """Apply life science domain reasoning to a question."""
    try:
        if llm_provider is None:
            return ToolResult(
                success=True,
                data={
                    "answer": "",
                    "note": "No LLM provider configured for life science reasoning",
                },
            )

        prompt_parts = [question]
        if context:
            prompt_parts.append(f"\nExperimental context:\n{context}")
        if domain != "general":
            prompt_parts.append(f"\nFocus domain: {domain}")

        result = await llm_provider.complete(
            "\n".join(prompt_parts),
            system=_LIFESCI_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2048,
        )

        return ToolResult(
            success=True,
            data={
                "answer": str(result).strip(),
                "domain": domain,
                "llm_used": True,
            },
        )
    except Exception as exc:
        logger.warning("Life science reasoning failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


async def _design_experiment(
    hypothesis: str,
    *,
    constraints: str = "",
    available_equipment: list[str] | None = None,
    llm_provider: Any = None,
) -> ToolResult:
    """Design an experiment to test a hypothesis."""
    try:
        if llm_provider is None:
            return ToolResult(
                success=True,
                data={
                    "design": "",
                    "note": "No LLM provider configured for experiment design",
                },
            )

        prompt_parts = [f"Hypothesis to test:\n{hypothesis}"]
        if constraints:
            prompt_parts.append(f"\nConstraints:\n{constraints}")
        if available_equipment:
            prompt_parts.append(
                "\nAvailable equipment:\n" + "\n".join(f"- {e}" for e in available_equipment)
            )

        result = await llm_provider.complete(
            "\n".join(prompt_parts),
            system=_EXPERIMENT_DESIGN_PROMPT,
            temperature=0.4,
            max_tokens=2048,
        )

        return ToolResult(
            success=True,
            data={
                "design": str(result).strip(),
                "hypothesis": hypothesis,
                "llm_used": True,
            },
        )
    except Exception as exc:
        logger.warning("Experiment design failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


class LifeSciSkill:
    """Life Science LLM skill — domain reasoning for the cloud brain."""

    metadata: SkillMetadata = SkillMetadata(
        name="lifesci",
        version="0.1.0",
        description="Life science domain reasoning, experiment design, and biological analysis.",
        capabilities=[
            SkillCapability.HYPOTHESIS_GENERATION,
            SkillCapability.GENERAL_REASONING,
        ],
        author="labclaw-core",
        requires_api_key=False,
    )

    def __init__(self, llm_provider: Any = None) -> None:
        self._llm_provider = llm_provider

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for life science reasoning."""
        from functools import partial

        return [
            AgentTool(
                name="reason_lifesci",
                description=(
                    "Apply life science domain expertise to answer a biological "
                    "question. Provides scientifically rigorous analysis with "
                    "confidence levels."
                ),
                fn=partial(_reason_lifesci, llm_provider=self._llm_provider),
                parameters_schema={
                    "question": {"type": "string", "description": "Scientific question"},
                    "context": {"type": "string", "description": "Experimental context"},
                    "domain": {
                        "type": "string",
                        "description": "Focus domain (neuroscience, genomics, etc.)",
                    },
                },
            ),
            AgentTool(
                name="design_experiment",
                description=(
                    "Design a rigorous experiment to test a hypothesis. "
                    "Includes controls, sample sizes, and protocol details."
                ),
                fn=partial(_design_experiment, llm_provider=self._llm_provider),
                parameters_schema={
                    "hypothesis": {"type": "string", "description": "Hypothesis to test"},
                    "constraints": {"type": "string", "description": "Resource constraints"},
                    "available_equipment": {
                        "type": "array",
                        "description": "Available lab equipment",
                    },
                },
            ),
        ]

    async def health_check(self) -> bool:
        """Check if LLM provider is available."""
        if self._llm_provider is None:
            return False
        try:
            result = await self._llm_provider.complete(
                "ping",
                system="Respond with 'pong'.",
                max_tokens=10,
            )
            return bool(result)
        except Exception:
            return False

    def configure(self, **kwargs: Any) -> None:
        """Update LLM provider."""
        if "llm_provider" in kwargs:
            self._llm_provider = kwargs["llm_provider"]


assert isinstance(LifeSciSkill(), CloudSkill)
