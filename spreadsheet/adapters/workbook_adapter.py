from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict

from ..core.grid_cell import GridCell, CellType
from ..core.memory_grid import MemoryGrid


class WorkbookAdapter:
    def __init__(self):
        self._sheets: List[MemoryGrid] = []
        self._sheet_meta: List[dict] = []
        self._name: str = ""

    def load(self, workbook_data: Any) -> None:
        self._sheets.clear()
        self._sheet_meta.clear()

        if isinstance(workbook_data, str):
            workbook_data = json.loads(workbook_data)

        if isinstance(workbook_data, list):
            raw_sheets = workbook_data
        elif isinstance(workbook_data, dict):
            raw_sheets = workbook_data.get("data", workbook_data.get("sheets", []))
            self._name = workbook_data.get("title", workbook_data.get("name", ""))
        else:
            raw_sheets = []

        for sheet in raw_sheets:
            grid = MemoryGrid()
            meta = {
                "name": sheet.get("name", sheet.get("index", "Sheet")),
                "index": sheet.get("index", str(len(self._sheets))),
                "color": sheet.get("color", ""),
                "order": sheet.get("order", len(self._sheets)),
                "row": sheet.get("row", 0),
                "column": sheet.get("column", 0),
                "status": sheet.get("status", 0),
                "celldata": sheet.get("celldata"),
                "data": sheet.get("data"),
            }

            celldata = sheet.get("celldata")
            if isinstance(celldata, list) and len(celldata) > 0:
                for entry in celldata:
                    r, c = entry.get("r", 0), entry.get("c", 0)
                    v = entry.get("v", {})
                    grid.set_cell(r, c, self._lucky_to_grid(v))
            else:
                data = sheet.get("data")
                if isinstance(data, list) and len(data) > 0:
                    for r, row in enumerate(data):
                        if not isinstance(row, list):
                            continue
                        for c, cell in enumerate(row):
                            if cell is not None:
                                if isinstance(cell, dict):
                                    grid.set_cell(r, c, self._lucky_to_grid(cell))
                                else:
                                    grid.set_cell(r, c, GridCell.text(str(cell)))

            self._sheets.append(grid)
            self._sheet_meta.append(meta)

    def save(self) -> List[dict]:
        result = []
        for i, grid in enumerate(self._sheets):
            meta = self._sheet_meta[i] if i < len(self._sheet_meta) else {}
            rows = grid.row_count()
            cols = grid.col_count()
            celldata = []
            for r in range(rows):
                for c in range(cols):
                    cell = grid.cell(r, c)
                    if cell.data_type != CellType.BLANK or cell.value is not None:
                        celldata.append({
                            "r": r, "c": c,
                            "v": self._grid_to_lucky(cell),
                        })

            sheet = dict(meta)
            sheet["celldata"] = celldata
            sheet["row"] = max(rows, meta.get("row", 0))
            sheet["column"] = max(cols, meta.get("column", 0))
            result.append(sheet)

        return result

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def sheet_count(self) -> int:
        return len(self._sheets)

    def sheet(self, index: int = 0) -> Optional[MemoryGrid]:
        if 0 <= index < len(self._sheets):
            return self._sheets[index]
        return None

    def sheet_meta(self, index: int = 0) -> dict:
        if 0 <= index < len(self._sheet_meta):
            return dict(self._sheet_meta[index])
        return {}

    def set_sheet_meta(self, index: int, **kwargs) -> None:
        if 0 <= index < len(self._sheet_meta):
            self._sheet_meta[index].update(kwargs)

    def add_sheet(self, name: str = "Sheet") -> MemoryGrid:
        grid = MemoryGrid()
        self._sheets.append(grid)
        self._sheet_meta.append({
            "name": name,
            "index": str(len(self._sheets) - 1),
            "color": "",
            "order": len(self._sheets) - 1,
            "row": 0, "column": 0, "status": 0,
        })
        return grid

    def remove_sheet(self, index: int) -> None:
        if 0 <= index < len(self._sheets):
            del self._sheets[index]
            del self._sheet_meta[index]

    def to_grid(self, sheet_index: int = 0) -> Optional[MemoryGrid]:
        return self.sheet(sheet_index)

    def from_grid(self, grid: MemoryGrid, sheet_index: int = 0) -> None:
        if 0 <= sheet_index < len(self._sheets):
            self._sheets[sheet_index] = grid

    def summary(self) -> dict:
        from ..core.grid_range import GridRange
        total_rows = 0
        total_cols = 0
        total_cells = 0
        for g in self._sheets:
            total_rows = max(total_rows, g.row_count())
            total_cols = max(total_cols, g.col_count())
            total_cells += g.cell_count()
        return {
            "sheets": self.sheet_count(),
            "rows": total_rows,
            "cols": total_cols,
            "cells": total_cells,
            "name": self._name,
        }

    def _lucky_to_grid(self, v: dict) -> GridCell:
        val = v.get("v")
        ct = CellType.TEXT
        if isinstance(val, (int, float)):
            if isinstance(val, float):
                ct = CellType.NUMBER
            else:
                ct = CellType.NUMBER
        elif val is None:
            ct = CellType.BLANK
        formula = v.get("f")
        if formula:
            ct = CellType.FORMULA
        return GridCell(
            value=val,
            display=v.get("m", str(val) if val is not None else ""),
            data_type=ct,
            formula=v.get("f"),
        )

    def _grid_to_lucky(self, cell: GridCell) -> dict:
        v = {"v": cell.value, "m": cell.display}
        if cell.formula:
            v["f"] = cell.formula
        return v
