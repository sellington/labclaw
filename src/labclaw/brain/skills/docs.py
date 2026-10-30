"""Makerspace Documentation, SOPs, and Engineering Reasoning skill.

Provides a searchable Markdown knowledge base of shop SOPs, machine safety
checklists, design rules, and build logs, plus LLM/template-backed SOP
generation and makerspace engineering reasoning.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from labclaw.brain.skills.base import SkillCapability, SkillMetadata
from labclaw.brain.types import BrainResult, ToolInfo
from labclaw.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

_DEFAULT_SOPS: dict[str, dict[str, Any]] = {
    "sop-cnc-cubiko": {
        "slug": "sop-cnc-cubiko",
        "title": "Genmitsu Cubiko Desktop CNC Router — Setup, Probing & Safety SOP",
        "category": "cnc",
        "tags": ["cubiko", "cnc", "grbl", "gsender", "spoilboard", "probing"],
        "content": (
            "# Genmitsu Cubiko CNC Setup & Safety SOP\n\n"
            "## 1. Work Envelope & Mechanical Specs\n"
            "- Working Envelope: 150 mm (X) x 110 mm (Y) x 40 mm (Z)\n"
            "- Bed Plate: 180 x 120 x 5.5 mm Al, 34x M5x0.8 grid (33.2x26.5mm pitch)\n"
            "- Spindle: ER11 collet (3.175mm), 10,000 RPM ($30=10000) or 20,000 RPM ($30=20000)\n\n"
            "## 2. Mandatory Spoilboard & Probing Safety Rules\n"
            "1. NEVER drill/through-cut into bare PLA: tape >= 3.0mm sacrificial MDF spoilboard.\n"
            "2. NEVER probe 0.1mm V-bits on the mechanical tool-setter button.\n"
            "3. NEVER use bare continuity probing on anodized Al (use 0.08mm paper drag test).\n"
            "4. gSender Probe Config: defaultFirmware='Grbl' and zProbe thickness=0mm."
        ),
    },
    "sop-pcb-milling": {
        "slug": "sop-pcb-milling",
        "title": "In-House FR-4 PCB Milling & pcb2gcode Workflow",
        "category": "pcb",
        "tags": ["pcb", "fr4", "pcb2gcode", "isolation", "kicad", "cubiko"],
        "content": (
            "# In-House FR-4 PCB Milling SOP\n\n"
            "## 1. Capability Boundary (In-House Cubiko vs. JLCPCB)\n"
            "- In-House (Cubiko): 1-2 layer down to 0.25mm trace/space, >= 0.50mm IC pitch.\n"
            "- JLCPCB (7-10 Days): 4-layer boards, dense thermal vias, < 0.40mm pitch WQFN.\n\n"
            "## 2. Milling & Dust Trapping Sequence\n"
            "1. Run dry electrical height-map probe (00_probe_heatmap_4x4.nc or center kiss).\n"
            "2. Detach both alligator clips.\n"
            "3. Apply 3-4 drops of water+dish soap or IPA (NEVER silicone oil on copper).\n"
            "4. Run 01_isolation_B_Cu.nc -> swap to 1.0mm end mill -> run drills & cutout."
        ),
    },
    "sop-3d-printing": {
        "slug": "sop-3d-printing",
        "title": "FDM 3D Printing & Parametric Enclosure Design Rules",
        "category": "3d_printing",
        "tags": ["3d-printing", "bambu", "pla", "enclosure", "press-fit", "fusion360"],
        "content": (
            "# FDM 3D Printing & Enclosure Design SOP\n\n"
            "## 1. Flat-Bottom Shell Rule\n"
            "- Extrude full outer footprint from Z=-floor_t to Z=+interior_h as ONE solid.\n\n"
            "## 2. Full-Rectangle PCB Insertion Envelope\n"
            "- Keep internal slide-in cavities square-cornered (PCB + 2.0mm clearance).\n"
            "- Validate insertion vectors: use a removable slide-in tray.\n\n"
            "## 3. Validated PLA Press-Fit Clearances\n"
            "- 6x2 mm Neodymium Magnet: Ø6.2 mm x 2.1 mm deep pocket\n"
            "- M2 Self-Tapping Pilot: Ø1.9 mm | M3 Pilot: Ø2.8 mm in Ø6.0 mm boss"
        ),
    },
    "sop-kicad-eda": {
        "slug": "sop-kicad-eda",
        "title": "KiCad 10 Schematic Capture, Freerouting & DRC Gate SOP",
        "category": "electronics",
        "tags": ["kicad", "eda", "erc", "drc", "freerouting", "jlcpcb"],
        "content": (
            "# KiCad 10 EDA & PCB Layout SOP\n\n"
            "1. Scoped Symbol Discovery: Query one library at a time to avoid 30s MCP timeouts.\n"
            "2. ERC Zero-Violation Gate: Place PWR_FLAG only on externally fed rails.\n"
            "3. Autorouting: Run Freerouting, fill GND pours after, verify 0 DRC errors."
        ),
    },
}


class DocsSkill:
    """Makerspace Documentation, SOP Knowledge Base, and Engineering Advisor."""

    metadata: SkillMetadata = SkillMetadata(
        name="docs",
        version="0.2.0",
        description=(
            "Makerspace SOPs, machine manuals, safety checklists, project build "
            "documentation, and hardware/manufacturing domain reasoning."
        ),
        capabilities=[
            SkillCapability.DOCUMENTATION,
            SkillCapability.REASONING,
            SkillCapability.WRITING,
        ],
    )

    def __init__(
        self,
        docs_dir: str | Path | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._docs_dir = Path(docs_dir) if docs_dir else None
        self._llm_provider = llm_provider
        self._docs: dict[str, dict[str, Any]] = {k: dict(v) for k, v in _DEFAULT_SOPS.items()}
        if self._docs_dir is not None:
            self._load_disk_docs(self._docs_dir)

    def _load_disk_docs(self, directory: Path) -> None:
        if not directory.exists():
            return
        for md_file in sorted(directory.glob("*.md")):
            slug = md_file.stem
            text = md_file.read_text(encoding="utf-8")
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            title = lines[0].lstrip("# ").strip() if lines else slug
            self._docs[slug] = {
                "slug": slug,
                "title": title,
                "category": "custom",
                "tags": [slug],
                "content": text,
            }

    async def execute(self, tool_name: str, **kwargs: Any) -> BrainResult:
        """Route tool execution."""
        handlers: dict[str, Any] = {
            "docs_list": self._list_docs,
            "docs_search": self._search_docs,
            "docs_get": self._get_doc,
            "docs_save": self._save_doc,
            "docs_generate_sop": self._generate_sop,
            "maker_reason": self._maker_reason,
            "design_project": self._design_project,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            available = ", ".join(sorted(handlers))
            return BrainResult(
                success=False,
                error=f"Unknown tool '{tool_name}'. Available: {available}",
            )
        return await handler(**kwargs)  # type: ignore[no-any-return]

    async def _list_docs(self, category: str = "", **kwargs: Any) -> BrainResult:
        docs = list(self._docs.values())
        if category:
            c = category.strip().lower()
            docs = [d for d in docs if str(d.get("category", "")).lower() == c]
        summaries = [
            {
                "slug": d["slug"],
                "title": d["title"],
                "category": d["category"],
                "tags": d.get("tags", []),
            }
            for d in docs
        ]
        return BrainResult(
            success=True,
            data={"docs": summaries, "count": len(summaries)},
        )

    async def _search_docs(self, query: str = "", **kwargs: Any) -> BrainResult:
        if not query.strip():
            return await self._list_docs()
        q = query.strip().lower()
        matches: list[dict[str, Any]] = []
        for d in self._docs.values():
            haystack = " ".join(
                [
                    str(d.get("slug", "")),
                    str(d.get("title", "")),
                    str(d.get("category", "")),
                    " ".join(d.get("tags", [])),
                    str(d.get("content", "")),
                ]
            ).lower()
            if q in haystack:
                matches.append(dict(d))
        return BrainResult(
            success=True,
            data={"query": query, "results": matches, "count": len(matches)},
        )

    async def _get_doc(self, slug: str = "", **kwargs: Any) -> BrainResult:
        s = slug.strip()
        if s not in self._docs:
            return BrainResult(
                success=False,
                error=f"Document '{s}' not found. Available: {', '.join(sorted(self._docs))}",
            )
        return BrainResult(success=True, data=dict(self._docs[s]))

    async def _save_doc(
        self,
        slug: str = "",
        title: str = "",
        content: str = "",
        category: str = "sop",
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> BrainResult:
        if not slug.strip() or not title.strip() or not content.strip():
            return BrainResult(
                success=False,
                error="'slug', 'title', and 'content' are all required",
            )
        clean_slug = slug.strip().lower().replace(" ", "-")
        doc = {
            "slug": clean_slug,
            "title": title.strip(),
            "category": category.strip().lower(),
            "tags": tags or [category.strip().lower()],
            "content": content,
        }
        self._docs[clean_slug] = doc
        if self._docs_dir is not None:
            self._docs_dir.mkdir(parents=True, exist_ok=True)
            (self._docs_dir / f"{clean_slug}.md").write_text(content, encoding="utf-8")
        return BrainResult(success=True, data=doc)

    async def _generate_sop(
        self,
        title: str = "Machine Operation SOP",
        machine_or_process: str = "Genmitsu Cubiko CNC",
        materials: str = "FR-4 / 6061 Aluminum / PLA",
        notes: str = "",
        **kwargs: Any,
    ) -> BrainResult:
        """Generate a structured Makerspace SOP (via LLM or deterministic template)."""
        if self._llm_provider is not None:
            try:
                prompt = (
                    f"Generate a concise Makerspace Standard Operating Procedure (SOP):\n"
                    f"Title: {title}\nMachine/Process: {machine_or_process}\n"
                    f"Materials: {materials}\nAdditional Notes: {notes}"
                )
                text = await self._llm_provider.complete(
                    prompt,
                    system=(
                        "You are a Principal Makerspace & Mechatronics Engineer "
                        "writing clear shop SOPs."
                    ),
                    temperature=0.3,
                    max_tokens=2048,
                )
                return BrainResult(
                    success=True,
                    data={"title": title, "markdown": str(text).strip(), "mode": "llm"},
                )
            except Exception as exc:
                logger.warning("LLM SOP generation failed, falling back to template: %s", exc)

        markdown = (
            f"# {title}\n\n"
            f"- **Equipment / Process:** {machine_or_process}\n"
            f"- **Approved Materials:** {materials}\n\n"
            "## 1. Pre-Flight Safety & Interlocks\n"
            "- Verify workholding clamps, sacrificial MDF spoilboard, and E-stop reachability.\n"
            "- Validate G-code bounding box against machine travel limits before starting.\n\n"
            "## 2. Operating Procedure\n"
            "1. Home all axes and set Work Coordinate System (WCS) X/Y/Z datum.\n"
            "2. Verify tool stickout, collet runout, and feeds/speeds profile.\n"
            f"3. Execute job while monitoring first pass adhesion / chips. {notes}\n\n"
            "## 3. Post-Job Cleanup & Inspection\n"
            "- Park spindle/printhead, vacuum debris, and verify dimensions with calipers."
        )
        return BrainResult(
            success=True,
            data={"title": title, "markdown": markdown, "mode": "template"},
        )

    async def _maker_reason(
        self,
        question: str = "",
        domain: str = "makerspace",
        context: str = "",
        **kwargs: Any,
    ) -> BrainResult:
        """Answer a makerspace/hardware engineering question grounded in shop SOPs."""
        if not question.strip():
            return BrainResult(success=False, error="'question' is required")

        # Find relevant SOP snippets
        q_words = [w.lower() for w in question.split() if len(w) >= 3]
        matched_sops: list[str] = []
        for doc in self._docs.values():
            body_lower = (doc["title"] + " " + doc["content"]).lower()
            if any(w in body_lower for w in q_words):
                matched_sops.append(f"[{doc['slug']}] {doc['title']}:\n{doc['content']}")

        if self._llm_provider is not None:
            try:
                sop_context = "\n\n".join(matched_sops[:2])
                full_prompt = f"Question ({domain}): {question}"
                if context:
                    full_prompt += f"\nContext: {context}"
                if sop_context:
                    full_prompt += f"\nShop SOP Reference:\n{sop_context}"
                ans = await self._llm_provider.complete(
                    full_prompt,
                    system=(
                        "You are the MakerClaw Shop Brain — an expert in CAD (Fusion 360), "
                        "PCB EDA (KiCad), CNC machining (GRBL/Cubiko), and mechatronics."
                    ),
                    temperature=0.3,
                    max_tokens=2048,
                )
                return BrainResult(
                    success=True,
                    data={
                        "answer": str(ans).strip(),
                        "domain": domain,
                        "referenced_sops": [
                            d["slug"]
                            for d in self._docs.values()
                            if any(w in (d["title"] + d["content"]).lower() for w in q_words)
                        ],
                    },
                )
            except Exception as exc:
                return BrainResult(success=False, error=str(exc))

        # Deterministic knowledge-base synthesis when no external LLM key is configured
        synthesis = (
            matched_sops[0]
            if matched_sops
            else (
                f"Makerspace Engineering Guidance ({domain}): Verify machine work envelope, "
                "on-hand inventory BOM, and CAD volume/mass deltas before fabrication."
            )
        )
        return BrainResult(
            success=True,
            data={
                "answer": synthesis,
                "domain": domain,
                "mode": "sop_knowledge_base",
            },
        )

    async def _design_project(
        self,
        description: str = "",
        **kwargs: Any,
    ) -> BrainResult:
        """Generate a 5-phase hardware/makerspace build plan."""
        if not description.strip():
            return BrainResult(success=False, error="'description' is required")

        plan = {
            "project_description": description,
            "phases": [
                "Phase 1: Master Engineering Spec, Envelope Math & On-Hand BOM Audit",
                "Phase 2: KiCad MCP Schematic Capture & Zero-Violation ERC",
                "Phase 3: PCB Layout (Freerouting / DRC=0) & Cubiko CNC vs JLCPCB Routing",
                "Phase 4: Parametric Mechanical CAD (Fusion 360 MCP) & Mass-Delta Verification",
                "Phase 5: Firmware Bring-Up, G-Code Safety Validation & Assembly Verification",
            ],
        }
        return BrainResult(success=True, data=plan)

    async def list_tools(self) -> list[ToolInfo]:
        """Return all documentation and makerspace advisor tools."""
        return [
            ToolInfo(
                name="docs_list",
                description="List makerspace SOPs, machine manuals, and design rule guides.",
                skill="docs",
                category="docs",
            ),
            ToolInfo(
                name="docs_search",
                description=(
                    "Search shop SOPs, CNC/3D-printer checklists, and CAD/PCB rules by keyword."
                ),
                skill="docs",
                category="docs",
            ),
            ToolInfo(
                name="docs_get",
                description="Read a complete makerspace SOP or documentation entry by slug.",
                skill="docs",
                category="docs",
            ),
            ToolInfo(
                name="docs_save",
                description="Create or update a Markdown SOP, machine manual, or build log.",
                skill="docs",
                category="docs",
            ),
            ToolInfo(
                name="docs_generate_sop",
                description=(
                    "Generate a structured Makerspace SOP or safety checklist "
                    "for a machine or process."
                ),
                skill="docs",
                category="docs",
            ),
            ToolInfo(
                name="maker_reason",
                description=(
                    "Answer makerspace, CAD, CNC, 3D printing, and PCB engineering "
                    "questions grounded in shop SOPs."
                ),
                skill="docs",
                category="reasoning",
            ),
            ToolInfo(
                name="design_project",
                description=(
                    "Generate a 5-phase makerspace hardware, CAD, PCB, and firmware build plan."
                ),
                skill="docs",
                category="reasoning",
            ),
        ]

    async def health_check(self) -> bool:
        """Always healthy — built-in SOP knowledge base is always available."""
        return len(self._docs) > 0
