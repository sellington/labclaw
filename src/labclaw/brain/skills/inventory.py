"""Makerspace Inventory skill — stock tracking, BOM validation, and reorder alerts.

Manages filaments, CNC stock blanks, cutting tools/end mills, electronics/MCUs,
fasteners, and consumables in a SQLite database with audit history.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from labclaw.brain.skills.base import SkillCapability, SkillMetadata
from labclaw.brain.types import BrainResult, ToolInfo

_DEFAULT_CATALOG: list[dict[str, Any]] = [
    {
        "sku": "FIL-PLA-MATTE-BLK",
        "name": "Bambu PLA Matte Black (1.75mm)",
        "category": "filament",
        "quantity": 2400.0,
        "unit": "g",
        "min_quantity": 500.0,
        "location": "drybox-1",
        "specs": {"diameter_mm": 1.75, "nozzle_temp_c": "190-230", "bed_temp_c": "55-60"},
        "vendor_url": "https://us.store.bambulab.com/products/pla-matte-filament",
        "backup_vendor_url": "https://www.amazon.com/s?k=1.75mm+matte+black+pla",
        "unit_cost_usd": 0.02,
    },
    {
        "sku": "FIL-LW-PLA-AERO",
        "name": "Bambu PLA Aero (Active-Foaming LW-PLA 1.75mm)",
        "category": "filament",
        "quantity": 950.0,
        "unit": "g",
        "min_quantity": 300.0,
        "location": "drybox-1",
        "specs": {"diameter_mm": 1.75, "nozzle_temp_c": "220-260", "density_g_cm3": 0.55},
        "vendor_url": "https://us.store.bambulab.com/products/pla-aero",
        "backup_vendor_url": "https://colorfabb.com/lw-pla-natural",
        "unit_cost_usd": 0.045,
    },
    {
        "sku": "CNC-FR4-150X100-2S",
        "name": "FR-4 Double-Sided Copper Clad Blank 150x100x1.6mm",
        "category": "cnc_stock",
        "quantity": 18.0,
        "unit": "sheets",
        "min_quantity": 5.0,
        "location": "cnc-cabinet-a",
        "specs": {"x_mm": 150.0, "y_mm": 100.0, "z_mm": 1.6, "copper_oz": 1.0},
        "vendor_url": "https://www.amazon.com/dp/B07R6QQ78Z",
        "backup_vendor_url": "https://www.digikey.com/en/products/filter/prototype-boards-unperforated/636",
        "unit_cost_usd": 1.25,
    },
    {
        "sku": "CNC-MDF-SPOIL-5X7",
        "name": "Sacrificial MDF Spoilboard Sheet 178x127x3.0mm",
        "category": "cnc_stock",
        "quantity": 12.0,
        "unit": "sheets",
        "min_quantity": 4.0,
        "location": "cnc-cabinet-a",
        "specs": {"x_mm": 178.0, "y_mm": 127.0, "z_mm": 3.0, "material": "MDF"},
        "vendor_url": "https://www.amazon.com/s?k=3mm+mdf+sheets+5x7",
        "backup_vendor_url": "https://www.mcmaster.com/",
        "unit_cost_usd": 0.85,
    },
    {
        "sku": "CNC-AL-CARD-86X54",
        "name": "Anodized Aluminum Business Card Blank 86x54x0.4mm",
        "category": "cnc_stock",
        "quantity": 45.0,
        "unit": "cards",
        "min_quantity": 10.0,
        "location": "cnc-cabinet-a",
        "specs": {"x_mm": 86.0, "y_mm": 54.0, "z_mm": 0.4, "surface": "anodized_insulating"},
        "vendor_url": "https://www.amazon.com/s?k=anodized+aluminum+business+card+blanks",
        "backup_vendor_url": "https://www.aliexpress.com/",
        "unit_cost_usd": 0.18,
    },
    {
        "sku": "CNC-PLY-BIRCH-3.2",
        "name": "Birch Aircraft Plywood 150x100x3.2mm (1/8 in)",
        "category": "cnc_stock",
        "quantity": 10.0,
        "unit": "sheets",
        "min_quantity": 3.0,
        "location": "cnc-cabinet-b",
        "specs": {"x_mm": 150.0, "y_mm": 100.0, "z_mm": 3.2, "material": "birch_plywood"},
        "vendor_url": "https://www.amazon.com/s?k=1%2F8+birch+aircraft+plywood",
        "backup_vendor_url": "https://makerstock.com/",
        "unit_cost_usd": 1.90,
    },
    {
        "sku": "BIT-V30-0.1MM",
        "name": "Genmitsu 30-Deg 0.1mm Tip Carbide V-Bit (1/8 in Shank)",
        "category": "cnc_tooling",
        "quantity": 8.0,
        "unit": "pcs",
        "min_quantity": 3.0,
        "location": "tool-tray-1",
        "specs": {"angle_deg": 30, "tip_mm": 0.1, "shank_mm": 3.175, "fragile_tip": True},
        "vendor_url": "https://www.sainsmart.com/collections/cnc-bits",
        "backup_vendor_url": "https://www.amazon.com/s?k=30+degree+0.1mm+v+bit+1%2F8",
        "unit_cost_usd": 1.50,
    },
    {
        "sku": "BIT-FLAT-1.0MM",
        "name": "1.0mm Ti-Coated Carbide Flat End Mill (7.0mm LOC, 1/8 in Shank)",
        "category": "cnc_tooling",
        "quantity": 6.0,
        "unit": "pcs",
        "min_quantity": 2.0,
        "location": "tool-tray-1",
        "specs": {"diameter_mm": 1.0, "flute_length_mm": 7.0, "shank_mm": 3.175, "flutes": 2},
        "vendor_url": "https://www.sainsmart.com/collections/cnc-bits",
        "backup_vendor_url": "https://www.amazon.com/s?k=1.0mm+carbide+end+mill+1%2F8+shank",
        "unit_cost_usd": 2.20,
    },
    {
        "sku": "MCU-XIAO-ESP32C6",
        "name": "Seeed Studio XIAO ESP32-C6 (Pre-Soldered)",
        "category": "electronics",
        "quantity": 4.0,
        "unit": "pcs",
        "min_quantity": 2.0,
        "location": "esd-bin-1",
        "specs": {"pcb_mm": "17.8x21.0", "mcu": "ESP32-C6", "wireless": "WiFi6/BLE/Zigbee"},
        "vendor_url": "https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32C6-p-5884.html",
        "backup_vendor_url": "https://www.digikey.com/",
        "unit_cost_usd": 5.20,
    },
    {
        "sku": "DISP-OLED-1.3-SH1106",
        "name": "Hosyond 1.3 in I2C OLED Display Module (SH1106 Blue)",
        "category": "electronics",
        "quantity": 5.0,
        "unit": "pcs",
        "min_quantity": 2.0,
        "location": "esd-bin-2",
        "specs": {"pcb_mm": "35.4x33.5", "hole_centers_mm": "30.4x28.5", "interface": "I2C"},
        "vendor_url": "https://www.amazon.com/s?k=1.3+inch+i2c+oled+sh1106",
        "backup_vendor_url": "https://www.aliexpress.com/",
        "unit_cost_usd": 3.40,
    },
    {
        "sku": "BAT-LIPO-1S-3000",
        "name": "MakerFocus 3000mAh 1S 3.7V LiPo (103665 Pouch)",
        "category": "electronics",
        "quantity": 3.0,
        "unit": "pcs",
        "min_quantity": 1.0,
        "location": "lipo-safe-bag",
        "specs": {"dimensions_mm": "66.0x35.0x10.0", "voltage_v": 3.7, "capacity_mah": 3000},
        "vendor_url": "https://www.amazon.com/s?k=3.7v+3000mah+103665+lipo",
        "backup_vendor_url": "https://www.adafruit.com/category/574",
        "unit_cost_usd": 9.95,
    },
    {
        "sku": "MAG-NEO-6X2",
        "name": "6x2mm Circular Neodymium Magnets",
        "category": "fasteners",
        "quantity": 85.0,
        "unit": "pcs",
        "min_quantity": 20.0,
        "location": "hardware-drawer-2",
        "specs": {"diameter_mm": 6.0, "thickness_mm": 2.0, "pla_press_fit_mm": "6.2x2.1"},
        "vendor_url": "https://www.amazon.com/s?k=6x2mm+neodymium+magnets",
        "backup_vendor_url": "https://www.kjmagnetics.com/",
        "unit_cost_usd": 0.08,
    },
]


class InventorySkill:
    """Makerspace Inventory skill — SQLite-backed stock & BOM management."""

    metadata: SkillMetadata = SkillMetadata(
        name="inventory",
        version="0.2.0",
        description=(
            "Makerspace inventory management: filaments, CNC stock blanks, "
            "end mills, electronics, fasteners, low-stock alerts, and BOM validation."
        ),
        capabilities=[
            SkillCapability.INVENTORY,
            SkillCapability.TOOL_EXECUTION,
        ],
    )

    def __init__(self, db_path: str | Path = ":memory:", auto_seed: bool = True) -> None:
        self._db_path = str(db_path)
        self._conn = self._init_db(self._db_path)
        if auto_seed:
            self._seed_if_empty()

    @staticmethod
    def _init_db(db_path: str) -> sqlite3.Connection:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_items (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL DEFAULT 'pcs',
                min_quantity REAL NOT NULL DEFAULT 0,
                location TEXT NOT NULL DEFAULT '',
                specs TEXT NOT NULL DEFAULT '{}',
                vendor_url TEXT NOT NULL DEFAULT '',
                backup_vendor_url TEXT NOT NULL DEFAULT '',
                unit_cost_usd REAL NOT NULL DEFAULT 0.0,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                delta REAL NOT NULL,
                new_quantity REAL NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()
        return conn

    def _seed_if_empty(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS cnt FROM inventory_items").fetchone()
        if row and int(row["cnt"]) > 0:
            return 0
        return self._insert_catalog(_DEFAULT_CATALOG)

    def _insert_catalog(self, items: list[dict[str, Any]]) -> int:
        now = datetime.now(UTC).isoformat()
        count = 0
        for item in items:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO inventory_items (
                    sku, name, category, quantity, unit, min_quantity,
                    location, specs, vendor_url, backup_vendor_url, unit_cost_usd, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["sku"],
                    item["name"],
                    item["category"],
                    float(item["quantity"]),
                    item.get("unit", "pcs"),
                    float(item.get("min_quantity", 0.0)),
                    item.get("location", ""),
                    json.dumps(item.get("specs", {})),
                    item.get("vendor_url", ""),
                    item.get("backup_vendor_url", ""),
                    float(item.get("unit_cost_usd", 0.0)),
                    now,
                ),
            )
            count += 1
        self._conn.commit()
        return count

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["specs"] = json.loads(d.get("specs") or "{}")
        d["low_stock"] = float(d["quantity"]) <= float(d["min_quantity"])
        return d

    async def execute(self, tool_name: str, **kwargs: Any) -> BrainResult:
        """Route tool execution."""
        handlers: dict[str, Any] = {
            "inventory_list": self._list_items,
            "inventory_search": self._search_items,
            "inventory_add": self._add_item,
            "inventory_update_stock": self._update_stock,
            "inventory_check_bom": self._check_bom,
            "inventory_low_stock": self._low_stock,
            "inventory_seed_defaults": self._seed_defaults,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            available = ", ".join(sorted(handlers))
            return BrainResult(
                success=False,
                error=f"Unknown tool '{tool_name}'. Available: {available}",
            )
        return await handler(**kwargs)  # type: ignore[no-any-return]

    async def _list_items(
        self,
        category: str = "",
        location: str = "",
        low_stock_only: bool = False,
        **kwargs: Any,
    ) -> BrainResult:
        clauses: list[str] = []
        params: list[Any] = []
        if category:
            clauses.append("LOWER(category) = LOWER(?)")
            params.append(category)
        if location:
            clauses.append("LOWER(location) = LOWER(?)")
            params.append(location)
        if low_stock_only:
            clauses.append("quantity <= min_quantity")

        sql = "SELECT * FROM inventory_items"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY category, sku"

        rows = self._conn.execute(sql, params).fetchall()
        items = [self._row_to_dict(r) for r in rows]
        return BrainResult(
            success=True,
            data={"items": items, "count": len(items)},
        )

    async def _search_items(self, query: str = "", **kwargs: Any) -> BrainResult:
        if not query.strip():
            return await self._list_items()
        q = f"%{query.strip().lower()}%"
        rows = self._conn.execute(
            """
            SELECT * FROM inventory_items
            WHERE LOWER(sku) LIKE ?
               OR LOWER(name) LIKE ?
               OR LOWER(category) LIKE ?
               OR LOWER(location) LIKE ?
               OR LOWER(specs) LIKE ?
            ORDER BY category, sku
            """,
            (q, q, q, q, q),
        ).fetchall()
        items = [self._row_to_dict(r) for r in rows]
        return BrainResult(
            success=True,
            data={"query": query, "items": items, "count": len(items)},
        )

    async def _add_item(
        self,
        sku: str = "",
        name: str = "",
        category: str = "consumables",
        quantity: float = 0.0,
        unit: str = "pcs",
        min_quantity: float = 0.0,
        location: str = "",
        specs: dict[str, Any] | str | None = None,
        vendor_url: str = "",
        backup_vendor_url: str = "",
        unit_cost_usd: float = 0.0,
        **kwargs: Any,
    ) -> BrainResult:
        if not sku.strip() or not name.strip():
            return BrainResult(success=False, error="Both 'sku' and 'name' are required")

        parsed_specs: dict[str, Any]
        if isinstance(specs, str):
            parsed_specs = json.loads(specs) if specs.strip() else {}
        elif isinstance(specs, dict):
            parsed_specs = specs
        else:
            parsed_specs = {}

        now = datetime.now(UTC).isoformat()
        sku_clean = sku.strip().upper()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO inventory_items (
                sku, name, category, quantity, unit, min_quantity,
                location, specs, vendor_url, backup_vendor_url, unit_cost_usd, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sku_clean,
                name.strip(),
                category.strip().lower(),
                float(quantity),
                unit.strip(),
                float(min_quantity),
                location.strip(),
                json.dumps(parsed_specs),
                vendor_url.strip(),
                backup_vendor_url.strip(),
                float(unit_cost_usd),
                now,
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM inventory_items WHERE sku = ?", (sku_clean,)
        ).fetchone()
        return BrainResult(success=True, data=self._row_to_dict(row))

    async def _update_stock(
        self,
        sku: str = "",
        delta: float | None = None,
        quantity: float | None = None,
        reason: str = "manual adjustment",
        **kwargs: Any,
    ) -> BrainResult:
        sku_clean = sku.strip().upper()
        row = self._conn.execute(
            "SELECT * FROM inventory_items WHERE UPPER(sku) = ?", (sku_clean,)
        ).fetchone()
        if row is None:
            return BrainResult(success=False, error=f"SKU '{sku}' not found in inventory")

        current_qty = float(row["quantity"])
        if quantity is not None:
            new_qty = float(quantity)
            applied_delta = new_qty - current_qty
        elif delta is not None:
            applied_delta = float(delta)
            new_qty = current_qty + applied_delta
        else:
            return BrainResult(
                success=False,
                error="Provide either 'delta' (relative change) or 'quantity' (new total)",
            )

        if new_qty < 0:
            return BrainResult(
                success=False,
                error=(
                    f"Insufficient stock for '{sku_clean}': "
                    f"have {current_qty}, requested change {applied_delta}"
                ),
            )

        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "UPDATE inventory_items SET quantity = ?, updated_at = ? WHERE sku = ?",
            (new_qty, now, row["sku"]),
        )
        self._conn.execute(
            """
            INSERT INTO inventory_transactions (sku, delta, new_quantity, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (row["sku"], applied_delta, new_qty, reason, now),
        )
        self._conn.commit()
        updated = self._conn.execute(
            "SELECT * FROM inventory_items WHERE sku = ?", (row["sku"],)
        ).fetchone()
        return BrainResult(
            success=True,
            data={
                "item": self._row_to_dict(updated),
                "delta": applied_delta,
                "previous_quantity": current_qty,
                "new_quantity": new_qty,
                "reason": reason,
            },
        )

    async def _low_stock(self, **kwargs: Any) -> BrainResult:
        return await self._list_items(low_stock_only=True)

    async def _seed_defaults(self, **kwargs: Any) -> BrainResult:
        count = self._insert_catalog(_DEFAULT_CATALOG)
        return BrainResult(
            success=True,
            data={"seeded_items": count, "message": f"Seeded {count} makerspace catalog items"},
        )

    async def _check_bom(
        self,
        items: list[dict[str, Any]] | str | None = None,
        **kwargs: Any,
    ) -> BrainResult:
        """Validate a Bill of Materials against on-hand shop inventory."""
        if isinstance(items, str):
            bom_list: list[dict[str, Any]] = json.loads(items) if items.strip() else []
        elif isinstance(items, list):
            bom_list = items
        else:
            return BrainResult(
                success=False,
                error="Provide 'items' as a list of {'item': <sku_or_name>, 'quantity': <num>}",
            )

        owned: list[dict[str, Any]] = []
        to_purchase: list[dict[str, Any]] = []
        total_purchase_cost = 0.0

        for entry in bom_list:
            query_key = str(entry.get("sku") or entry.get("item") or entry.get("name") or "")
            req_qty = float(entry.get("quantity", 1.0))
            q_like = f"%{query_key.strip().lower()}%"

            row = self._conn.execute(
                """
                SELECT * FROM inventory_items
                WHERE LOWER(sku) = LOWER(?)
                   OR LOWER(sku) LIKE ?
                   OR LOWER(name) LIKE ?
                ORDER BY CASE WHEN LOWER(sku) = LOWER(?) THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (query_key.strip(), q_like, q_like, query_key.strip()),
            ).fetchone()

            if row is not None:
                item_dict = self._row_to_dict(row)
                on_hand = float(item_dict["quantity"])
                if on_hand >= req_qty:
                    owned.append(
                        {
                            "requested": query_key,
                            "sku": item_dict["sku"],
                            "name": item_dict["name"],
                            "required_qty": req_qty,
                            "on_hand_qty": on_hand,
                            "location": item_dict["location"],
                            "cost_usd": 0.0,
                            "status": "in_stock",
                        }
                    )
                else:
                    shortfall = req_qty - on_hand
                    line_cost = round(shortfall * float(item_dict["unit_cost_usd"]), 2)
                    total_purchase_cost += line_cost
                    to_purchase.append(
                        {
                            "requested": query_key,
                            "sku": item_dict["sku"],
                            "name": item_dict["name"],
                            "required_qty": req_qty,
                            "on_hand_qty": on_hand,
                            "shortfall_qty": shortfall,
                            "vendor_url": item_dict["vendor_url"],
                            "backup_vendor_url": item_dict["backup_vendor_url"],
                            "estimated_cost_usd": line_cost,
                            "status": "partial_stock",
                        }
                    )
            else:
                search_slug = query_key.strip().replace(" ", "+")
                to_purchase.append(
                    {
                        "requested": query_key,
                        "sku": "UNLISTED",
                        "name": query_key,
                        "required_qty": req_qty,
                        "on_hand_qty": 0.0,
                        "shortfall_qty": req_qty,
                        "vendor_url": entry.get(
                            "vendor_url",
                            f"https://www.digikey.com/en/products?keywords={search_slug}",
                        ),
                        "backup_vendor_url": entry.get(
                            "backup_vendor_url", f"https://www.amazon.com/s?k={search_slug}"
                        ),
                        "estimated_cost_usd": float(entry.get("estimated_cost_usd", 0.0)),
                        "status": "not_in_inventory",
                    }
                )
                total_purchase_cost += float(entry.get("estimated_cost_usd", 0.0))

        return BrainResult(
            success=True,
            data={
                "ready_to_build": len(to_purchase) == 0,
                "owned_items": owned,
                "to_purchase": to_purchase,
                "estimated_purchase_cost_usd": round(total_purchase_cost, 2),
            },
        )

    async def list_tools(self) -> list[ToolInfo]:
        """Return all inventory tools."""
        return [
            ToolInfo(
                name="inventory_list",
                description=(
                    "List makerspace inventory items by category, location, or low-stock status."
                ),
                skill="inventory",
                category="inventory",
            ),
            ToolInfo(
                name="inventory_search",
                description=(
                    "Search filaments, CNC stock, tooling, electronics, and fasteners by keyword."
                ),
                skill="inventory",
                category="inventory",
            ),
            ToolInfo(
                name="inventory_add",
                description="Add or update a makerspace inventory item with specs and vendor URLs.",
                skill="inventory",
                category="inventory",
            ),
            ToolInfo(
                name="inventory_update_stock",
                description=(
                    "Adjust stock quantity (consume for a build or restock) with audit trail."
                ),
                skill="inventory",
                category="inventory",
            ),
            ToolInfo(
                name="inventory_check_bom",
                description=(
                    "Validate a project BOM against shop inventory; splits owned ($0) vs "
                    "shortfall items with clickable primary/backup vendor URLs."
                ),
                skill="inventory",
                category="inventory",
            ),
            ToolInfo(
                name="inventory_low_stock",
                description="List all makerspace items at or below their minimum stock threshold.",
                skill="inventory",
                category="inventory",
            ),
            ToolInfo(
                name="inventory_seed_defaults",
                description=(
                    "Seed the inventory database with the default makerspace starter catalog."
                ),
                skill="inventory",
                category="inventory",
            ),
        ]

    async def health_check(self) -> bool:
        """Verify SQLite database is operational."""
        row = self._conn.execute("SELECT 1 AS ok").fetchone()
        return bool(row and row["ok"] == 1)
