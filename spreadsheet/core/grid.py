from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from .grid_cell import GridCell
from .grid_range import GridRange
from .grid_metadata import GridMetadata
from .events import EventBus


class Grid(ABC):
    def __init__(self):
        self.events = EventBus()
        self.metadata = GridMetadata()
        self._dirty: bool = False

    @abstractmethod
    def cell(self, row: int, col: int) -> GridCell:
        ...

    @abstractmethod
    def set_cell(self, row: int, col: int, cell: GridCell) -> None:
        ...

    @abstractmethod
    def row_count(self) -> int:
        ...

    @abstractmethod
    def col_count(self) -> int:
        ...

    def range(self, r: GridRange) -> List[List[GridCell]]:
        return [[self.cell(rr, cc) for cc in range(r.col_start, r.col_end + 1)]
                for rr in range(r.row_start, r.row_end + 1)]

    def set_range(self, r: GridRange, data: List[List[GridCell]]) -> None:
        for dr, row_data in enumerate(data):
            for dc, cell in enumerate(row_data):
                self.set_cell(r.row_start + dr, r.col_start + dc, cell)

    def serialize(self) -> dict:
        rows = self.row_count()
        cols = self.col_count()
        data = {}
        for r in range(rows):
            for c in range(cols):
                cell = self.cell(r, c)
                if cell.data_type != "blank" or cell.value is not None:
                    data[f"{r},{c}"] = cell
        return {
            "metadata": self.metadata,
            "data": data,
            "row_count": rows,
            "col_count": cols,
        }

    @property
    def dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False
