from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .base import DataSource
from ..core.grid_cell import GridCell, CellType


class WorkbookDataSource(DataSource):
    def __init__(self, sheets_data: List[dict], sheet_index: int = 0):
        self._sheets = sheets_data
        self._index = sheet_index
        self._cache: Dict[Tuple[int, int], Any] = {}

    def connect(self) -> None:
        self._parse()

    def disconnect(self) -> None:
        self._cache.clear()

    def _parse(self) -> None:
        sheet = self._sheets[self._index] if self._index < len(self._sheets) else {}
        celldata = sheet.get("celldata", [])
        data = sheet.get("data", [])

        if celldata:
            for entry in celldata:
                r, c = entry.get("r", 0), entry.get("c", 0)
                self._cache[(r, c)] = self._to_cell(entry.get("v", {}))
        elif data:
            for r, row in enumerate(data):
                for c, col in enumerate(row if row else []):
                    if col:
                        self._cache[(r, c)] = self._to_cell(col)

    def _to_cell(self, v: dict) -> GridCell:
        val = v.get("v")
        cell_type = CellType.TEXT
        if isinstance(val, (int, float)):
            cell_type = CellType.NUMBER
        elif val is None:
            cell_type = CellType.BLANK
        return GridCell(
            value=val,
            display=v.get("m", str(val) if val is not None else ""),
            data_type=cell_type,
        )

    def load_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int) -> Dict[Tuple[int, int], Any]:
        return {
            (r, c): self._cache.get((r, c), GridCell.blank())
            for r in range(row_start, row_end + 1)
            for c in range(col_start, col_end + 1)
        }

    def save_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int,
                   data: Dict[Tuple[int, int], Any]) -> None:
        self._cache.update(data)

    def row_count(self) -> int:
        if not self._cache:
            return 0
        return max(r for r, _ in self._cache) + 1 if self._cache else 0

    def col_count(self) -> int:
        if not self._cache:
            return 0
        return max(c for _, c in self._cache) + 1 if self._cache else 0

    def flush(self) -> None:
        pass
