from __future__ import annotations
from typing import Any, List, Optional
from ..core.grid import Grid
from ..core.grid_cell import GridCell, CellType
from ..cache.block_cache import BlockCache


class SpreadsheetModel:
    def __init__(self, grid: Grid, cache: BlockCache):
        self._grid = grid
        self._cache = cache

    def row_count(self) -> int:
        return self._grid.row_count()

    def col_count(self) -> int:
        return self._grid.col_count()

    def header_data(self, section: int, orientation: int, role: int) -> Any:
        return None

    def data(self, row: int, col: int, role: int) -> Any:
        cell = self._cache.get(row, col) or GridCell.blank()
        return self._format(cell, role)

    def set_data(self, row: int, col: int, value: Any, role: int) -> bool:
        cell = self._parse(value)
        self._cache.set(row, col, cell)
        self._grid.set_cell(row, col, cell)
        return True

    def flags(self, row: int, col: int) -> int:
        cell = self._cache.get(row, col) or GridCell.blank()
        return 0

    def _format(self, cell: GridCell, role: int) -> Any:
        return cell.display

    def _parse(self, value: Any) -> GridCell:
        return GridCell.text(str(value))

    def flush(self) -> None:
        self._cache.flush()
