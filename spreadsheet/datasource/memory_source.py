from __future__ import annotations
from typing import Any, Dict, Tuple
from .base import DataSource


class MemoryDataSource(DataSource):
    def __init__(self, rows: int = 0, cols: int = 0):
        self._data: Dict[Tuple[int, int], Any] = {}
        self._rows = rows
        self._cols = cols

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def load_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int) -> Dict[Tuple[int, int], Any]:
        return {
            (r, c): self._data.get((r, c))
            for r in range(row_start, row_end + 1)
            for c in range(col_start, col_end + 1)
        }

    def save_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int,
                   data: Dict[Tuple[int, int], Any]) -> None:
        self._data.update(data)
        self._rows = max(self._rows, row_end + 1)
        self._cols = max(self._cols, col_end + 1)

    def row_count(self) -> int:
        return self._rows

    def col_count(self) -> int:
        return self._cols

    def flush(self) -> None:
        pass
