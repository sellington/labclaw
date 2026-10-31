"""Unit tests for DocsSkill (100% coverage)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

from labclaw.brain.skills.docs import DocsSkill


class TestDocsSkill:
    async def test_init_and_load_disk_docs(self, tmp_path: Path) -> None:
        # Non-existent dir handled gracefully
        missing_dir = tmp_path / "does_not_exist"
        s1 = DocsSkill(docs_dir=missing_dir)
        assert await s1.health_check() is True

        # Existing dir with markdown file
        docs_dir = tmp_path / "sops"
        docs_dir.mkdir()
        (docs_dir / "laser-safety.md").write_text("# Laser Cutter Safety\nAlways wear goggles.\n")
        s2 = DocsSkill(docs_dir=docs_dir)
        got = await s2.execute("docs_get", slug="laser-safety")
        assert got.success is True
        assert got.data["title"] == "Laser Cutter Safety"

    async def test_list_search_get_save_docs(self, tmp_path: Path) -> None:
        skill = DocsSkill(docs_dir=tmp_path)

        unknown = await skill.execute("unknown_doc_tool")
        assert unknown.success is False

        all_docs = await skill.execute("docs_list")
        assert all_docs.success is True
        assert all_docs.data["count"] >= 4

        cnc_docs = await skill.execute("docs_list", category="cnc")
        assert cnc_docs.data["count"] == 1

        empty_search = await skill.execute("docs_search", query="   ")
        assert empty_search.data["count"] >= 4

        found = await skill.execute("docs_search", query="spoilboard")
        assert found.data["count"] >= 1

        missing_doc = await skill.execute("docs_get", slug="missing-slug")
        assert missing_doc.success is False

        bad_save = await skill.execute("docs_save", slug="", title="", content="")
        assert bad_save.success is False

        saved = await skill.execute(
            "docs_save",
            slug="Reflow Oven SOP",
            title="Reflow Oven Profile Guide",
            content="# Reflow Guide\nPeak 245C.",
            category="electronics",
        )
        assert saved.success is True
        assert saved.data["slug"] == "reflow-oven-sop"
        assert (tmp_path / "reflow-oven-sop.md").exists()

    async def test_generate_sop_template_and_llm(self) -> None:
        # Template mode (no LLM)
        skill_no_llm = DocsSkill()
        t_res = await skill_no_llm.execute("docs_generate_sop", title="Cubiko Checklist")
        assert t_res.success is True
        assert t_res.data["mode"] == "template"

        # LLM mode success
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "# Generated LLM SOP"
        skill_llm = DocsSkill(llm_provider=mock_llm)
        l_res = await skill_llm.execute("docs_generate_sop", title="Bambu P1S SOP")
        assert l_res.success is True
        assert l_res.data["mode"] == "llm"

        # LLM mode exception falls back to template
        mock_llm.complete.side_effect = RuntimeError("LLM error")
        fb_res = await skill_llm.execute("docs_generate_sop", title="Fallback SOP")
        assert fb_res.success is True
        assert fb_res.data["mode"] == "template"

    async def test_maker_reason_and_design_project(self) -> None:
        skill = DocsSkill()

        empty_q = await skill.execute("maker_reason", question="  ")
        assert empty_q.success is False

        # Matches built-in SOP
        sop_ans = await skill.execute(
            "maker_reason", question="How do I probe the Cubiko spoilboard?"
        )
        assert sop_ans.success is True
        assert "sop-cnc-cubiko" in sop_ans.data["answer"]

        # Generic fallback when no SOP matches
        gen_ans = await skill.execute("maker_reason", question="xy")
        assert gen_ans.success is True
        assert "Makerspace Engineering Guidance" in gen_ans.data["answer"]

        # With LLM provider
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Expert CAD answer"
        skill_llm = DocsSkill(llm_provider=mock_llm)
        llm_ans = await skill_llm.execute(
            "maker_reason",
            question="How should I model a Cubiko fixture?",
            domain="cad",
            context="6061 aluminum",
        )
        assert llm_ans.success is True
        assert llm_ans.data["answer"] == "Expert CAD answer"

        # LLM exception in maker_reason
        mock_llm.complete.side_effect = RuntimeError("boom")
        err_ans = await skill_llm.execute("maker_reason", question="Cubiko fixture?")
        assert err_ans.success is False

        # design_project
        empty_proj = await skill.execute("design_project", description="")
        assert empty_proj.success is False

        ok_proj = await skill.execute(
            "design_project", description="Closed-loop reaction wheel pendulum"
        )
        assert ok_proj.success is True
        assert len(ok_proj.data["phases"]) == 5

        # project tracker tools
        plist = await skill.execute("project_list", discipline="cnc")
        assert plist.success is True
        assert plist.data["count"] >= 2

        bad_create = await skill.execute("project_create", name="  ")
        assert bad_create.success is False

        pcreate = await skill.execute("project_create", name="Custom Soldering Rig")
        assert pcreate.success is True
        pid = pcreate.data["project_id"]

        bad_todo = await skill.execute("project_add_todo", project_id="nope", task="")
        assert bad_todo.success is False

        ok_todo = await skill.execute(
            "project_add_todo", project_id=pid, discipline="soldering", task="Tin iron tip"
        )
        assert ok_todo.success is True

        bad_tog1 = await skill.execute("project_toggle_todo", project_id="nope", todo_id=1)
        assert bad_tog1.success is False

        bad_tog2 = await skill.execute("project_toggle_todo", project_id=pid, todo_id=999)
        assert bad_tog2.success is False

        ok_tog = await skill.execute("project_toggle_todo", project_id=pid, todo_id=1)
        assert ok_tog.success is True
        assert ok_tog.data["todo"]["done"] is True

        tools = await skill.list_tools()
        assert len(tools) == 12
