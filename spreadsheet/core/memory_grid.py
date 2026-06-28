from __future__ import annotations
from typing import Dict, Optional, Tuple
from .grid import Grid
from .grid_cell import GridCell


class MemoryGrid(Grid):
    def __init__(self, rows: int = 0, cols: int = 0):
        super().__init__()
        self._cells: Dict[Tuple[int, int], GridCell] = {}
        self._rows = rows
        self._cols = cols

    def cell(self, row: int, col: int) -> GridCell:
        return self._cells.get((row, col), GridCell.blank())

    def set_cell(self, row: int, col: int, cell: GridCell) -> None:
        self._cells[(row, col)] = cell
        self._rows = max(self._rows, row + 1)
        self._cols = max(self._cols, col + 1)
        self._dirty = True

    def row_count(self) -> int:
        return self._rows

    def col_count(self) -> int:
        return self._cols

    def clear(self) -> None:
        self._cells.clear()
        self._rows = 0
        self._cols = 0

    def resize(self, rows: int, cols: int) -> None:
        self._rows = rows
        self._cols = cols

    def cell_count(self) -> int:
        return len(self._cells)
