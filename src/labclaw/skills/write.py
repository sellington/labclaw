"""Scientific writing skill — report and paper section generation.

Uses LLM to generate structured scientific text: abstracts, methods,
results summaries, and discussion sections grounded in experimental data.

Maps to: CONCLUDE step (report generation).
"""

from __future__ import annotations

import logging
from typing import Any

from labclaw.agents.tools import AgentTool, ToolResult
from labclaw.skills.base import CloudSkill, SkillCapability, SkillMetadata

logger = logging.getLogger(__name__)

_SECTION_PROMPTS = {
    "abstract": (
        "Write a concise scientific abstract summarizing the following findings. "
        "Include background, methods, key results, and conclusions."
    ),
    "methods": (
        "Write a Methods section describing the experimental procedures "
        "based on the following protocol and parameters."
    ),
    "results": (
        "Write a Results section presenting the following experimental data "
        "and statistical findings. Be quantitative and specific."
    ),
    "discussion": (
        "Write a Discussion section interpreting the following results "
        "in the context of the current literature. Identify limitations."
    ),
    "summary": (
        "Write a brief summary of the following experimental cycle, "
        "highlighting key discoveries and next steps."
    ),
}


async def _generate_section(
    section_type: str,
    *,
    findings: list[str] | None = None,
    data_context: str = "",
    llm_provider: Any = None,
) -> ToolResult:
    """Generate a scientific text section from findings and data."""
    try:
        if section_type not in _SECTION_PROMPTS:
            return ToolResult(
                success=False,
                error=f"Unknown section type: {section_type!r}. "
                f"Valid types: {list(_SECTION_PROMPTS.keys())}",
            )

        if not findings and not data_context:
            return ToolResult(
                success=True,
                data={"text": "", "note": "No findings or context provided"},
            )

        system_prompt = _SECTION_PROMPTS[section_type]
        content_parts = []
        if findings:
            content_parts.append("Findings:\n" + "\n".join(f"- {f}" for f in findings))
        if data_context:
            content_parts.append(f"Context:\n{data_context}")

        user_prompt = "\n\n".join(content_parts)

        if llm_provider is None:
            # Fallback: return a template-based summary
            text = _template_section(section_type, findings or [], data_context)
            return ToolResult(
                success=True,
                data={"text": text, "section_type": section_type, "llm_used": False},
            )

        result = await llm_provider.complete(
            user_prompt,
            system=system_prompt,
            temperature=0.4,
            max_tokens=2048,
        )

        return ToolResult(
            success=True,
            data={
                "text": str(result).strip(),
                "section_type": section_type,
                "llm_used": True,
            },
        )
    except Exception as exc:
        logger.warning("Scientific writing failed: %s", exc)
        return ToolResult(success=False, error=str(exc))


def _template_section(
    section_type: str,
    findings: list[str],
    data_context: str,
) -> str:
    """Generate a template-based section when no LLM is available."""
    if not findings:
        return f"[{section_type.upper()}] No findings to report."

    lines = [f"[{section_type.upper()}]"]
    for i, finding in enumerate(findings, 1):
        lines.append(f"{i}. {finding}")
    if data_context:
        lines.append(f"\nAdditional context: {data_context}")
    return "\n".join(lines)


async def _format_citation(
    title: str,
    *,
    authors: list[str] | None = None,
    year: int = 0,
    journal: str = "",
    doi: str = "",
    style: str = "apa",
) -> ToolResult:
    """Format a citation in the specified style."""
    author_str = ", ".join(authors) if authors else "Unknown"
    year_str = str(year) if year else "n.d."

    if style == "apa":
        citation = f"{author_str} ({year_str}). {title}."
        if journal:
            citation += f" {journal}."
        if doi:
            citation += f" https://doi.org/{doi}"
    else:
        citation = f"{author_str}. {title}. {journal} ({year_str})."
        if doi:
            citation += f" doi:{doi}"

    return ToolResult(
        success=True,
        data={"citation": citation, "style": style},
    )


class WriteSkill:
    """Scientific writing skill — text generation for the cloud brain."""

    metadata: SkillMetadata = SkillMetadata(
        name="write",
        version="0.1.0",
        description="Scientific writing: abstracts, methods, results, discussions, citations.",
        capabilities=[SkillCapability.SCIENTIFIC_WRITING],
        author="labclaw-core",
        requires_api_key=False,
    )

    def __init__(self, llm_provider: Any = None) -> None:
        self._llm_provider = llm_provider

    def get_tools(self) -> list[AgentTool]:
        """Return agent tools for scientific writing."""
        from functools import partial

        return [
            AgentTool(
                name="generate_section",
                description=(
                    "Generate a scientific text section (abstract, methods, "
                    "results, discussion, or summary) from findings and data."
                ),
                fn=partial(_generate_section, llm_provider=self._llm_provider),
                parameters_schema={
                    "section_type": {
                        "type": "string",
                        "description": "abstract, methods, results, discussion, summary",
                    },
                    "findings": {
                        "type": "array",
                        "description": "List of finding strings",
                    },
                    "data_context": {
                        "type": "string",
                        "description": "Additional data context",
                    },
                },
            ),
            AgentTool(
                name="format_citation",
                description="Format a scientific citation in APA or other styles.",
                fn=_format_citation,
                parameters_schema={
                    "title": {"type": "string", "description": "Paper title"},
                    "authors": {"type": "array", "description": "Author names"},
                    "year": {"type": "integer", "description": "Publication year"},
                    "journal": {"type": "string", "description": "Journal name"},
                    "doi": {"type": "string", "description": "DOI identifier"},
                    "style": {"type": "string", "description": "Citation style (apa, mla)"},
                },
            ),
        ]

    async def health_check(self) -> bool:
        """WriteSkill is always available (template fallback)."""
        return True

    def configure(self, **kwargs: Any) -> None:
        """Update LLM provider."""
        if "llm_provider" in kwargs:
            self._llm_provider = kwargs["llm_provider"]


assert isinstance(WriteSkill(), CloudSkill)
