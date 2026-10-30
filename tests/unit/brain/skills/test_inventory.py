"""Unit tests for InventorySkill (100% coverage)."""

from __future__ import annotations

from pathlib import Path

from labclaw.brain.skills.inventory import InventorySkill


class TestInventorySkill:
    async def test_init_with_file_db_and_auto_seed(self, tmp_path: Path) -> None:
        db_file = tmp_path / "sub" / "shop.db"
        skill = InventorySkill(db_path=db_file, auto_seed=True)
        assert await skill.health_check() is True

        # Second init on non-empty DB hits _seed_if_empty early return (returns 0)
        skill2 = InventorySkill(db_path=db_file, auto_seed=True)
        res = await skill2.execute("inventory_list")
        assert res.success is True
        assert res.data["count"] >= 10

    async def test_init_without_auto_seed(self) -> None:
        skill = InventorySkill(db_path=":memory:", auto_seed=False)
        res = await skill.execute("inventory_list")
        assert res.data["count"] == 0

        seed_res = await skill.execute("inventory_seed_defaults")
        assert seed_res.success is True
        assert seed_res.data["seeded_items"] > 0

    async def test_unknown_tool_returns_error(self) -> None:
        skill = InventorySkill()
        res = await skill.execute("nonexistent_tool")
        assert res.success is False
        assert "Unknown tool" in (res.error or "")

    async def test_list_filters_category_location_low_stock(self) -> None:
        skill = InventorySkill()
        cat_res = await skill.execute("inventory_list", category="filament")
        assert cat_res.success is True
        assert cat_res.data["count"] >= 2

        loc_res = await skill.execute("inventory_list", location="drybox-1")
        assert loc_res.success is True
        assert loc_res.data["count"] >= 2

        low_res = await skill.execute("inventory_low_stock")
        assert low_res.success is True
        assert low_res.data["count"] == 0

    async def test_search_items_with_and_without_query(self) -> None:
        skill = InventorySkill()
        empty_q = await skill.execute("inventory_search", query="   ")
        assert empty_q.success is True
        assert empty_q.data["count"] >= 10

        found = await skill.execute("inventory_search", query="XIAO")
        assert found.success is True
        assert found.data["count"] == 1
        assert found.data["items"][0]["sku"] == "MCU-XIAO-ESP32C6"

    async def test_add_item_validation_and_specs_formats(self) -> None:
        skill = InventorySkill(auto_seed=False)
        missing = await skill.execute("inventory_add", sku="", name="")
        assert missing.success is False

        # Add with dict specs
        r1 = await skill.execute(
            "inventory_add",
            sku="endmill-2mm",
            name="2.0mm O-Flute Carbide End Mill",
            category="cnc_tooling",
            quantity=5,
            min_quantity=2,
            location="tray-2",
            specs={"flutes": 1},
            vendor_url="https://example.com/1",
            backup_vendor_url="https://example.com/2",
            unit_cost_usd=3.5,
        )
        assert r1.success is True
        assert r1.data["sku"] == "ENDMILL-2MM"
        assert r1.data["specs"] == {"flutes": 1}

        # Add with JSON string specs
        r2 = await skill.execute(
            "inventory_add",
            sku="screw-m3-8",
            name="M3x8 SHCS",
            specs='{"thread": "M3"}',
        )
        assert r2.success is True
        assert r2.data["specs"] == {"thread": "M3"}

        # Add with None specs
        r3 = await skill.execute(
            "inventory_add",
            sku="tape-cnc",
            name="XFasten CNC Tape",
            specs=None,
        )
        assert r3.success is True
        assert r3.data["specs"] == {}

    async def test_update_stock_delta_quantity_and_errors(self) -> None:
        skill = InventorySkill()

        not_found = await skill.execute("inventory_update_stock", sku="MISSING-SKU", delta=-1)
        assert not_found.success is False

        no_args = await skill.execute("inventory_update_stock", sku="MCU-XIAO-ESP32C6")
        assert no_args.success is False

        insufficient = await skill.execute(
            "inventory_update_stock", sku="MCU-XIAO-ESP32C6", delta=-999
        )
        assert insufficient.success is False
        assert "Insufficient stock" in (insufficient.error or "")

        by_delta = await skill.execute(
            "inventory_update_stock",
            sku="MCU-XIAO-ESP32C6",
            delta=-1.0,
            reason="Cubli build",
        )
        assert by_delta.success is True
        assert by_delta.data["new_quantity"] == 3.0

        by_abs = await skill.execute(
            "inventory_update_stock",
            sku="MCU-XIAO-ESP32C6",
            quantity=10.0,
            reason="Restock",
        )
        assert by_abs.success is True
        assert by_abs.data["new_quantity"] == 10.0

    async def test_check_bom_owned_partial_and_unlisted(self) -> None:
        skill = InventorySkill()

        bad = await skill.execute("inventory_check_bom", items=None)
        assert bad.success is False

        # Test via JSON string
        res = await skill.execute(
            "inventory_check_bom",
            items=(
                '[{"sku": "MCU-XIAO-ESP32C6", "quantity": 2}, '
                '{"sku": "MCU-XIAO-ESP32C6", "quantity": 50}, '
                '{"item": "DRV8311H BLDC Driver", "quantity": 3, "estimated_cost_usd": 2.0}]'
            ),
        )
        assert res.success is True
        assert res.data["ready_to_build"] is False
        assert len(res.data["owned_items"]) == 1
        assert len(res.data["to_purchase"]) == 2
        assert res.data["estimated_purchase_cost_usd"] > 0

    async def test_list_tools_metadata(self) -> None:
        skill = InventorySkill()
        tools = await skill.list_tools()
        assert len(tools) == 7
        assert {t.name for t in tools} == {
            "inventory_list",
            "inventory_search",
            "inventory_add",
            "inventory_update_stock",
            "inventory_check_bom",
            "inventory_low_stock",
            "inventory_seed_defaults",
        }
