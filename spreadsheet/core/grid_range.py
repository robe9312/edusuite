from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, List, Tuple


@dataclass(frozen=True)
class GridRange:
    row_start: int
    col_start: int
    row_end: int
    col_end: int

    @classmethod
    def single(cls, row: int, col: int) -> GridRange:
        return cls(row, col, row, col)

    @classmethod
    def column(cls, col: int, row_start: int, row_end: int) -> GridRange:
        return cls(row_start, col, row_end, col)

    @classmethod
    def row(cls, row: int, col_start: int, col_end: int) -> GridRange:
        return cls(row, col_start, row, col_end)

    @classmethod
    def all(cls) -> GridRange:
        return cls(0, 0, -1, -1)

    @property
    def rows(self) -> int:
        return self.row_end - self.row_start + 1 if self.row_end >= self.row_start else 0

    @property
    def cols(self) -> int:
        return self.col_end - self.col_start + 1 if self.col_end >= self.col_start else 0

    @property
    def is_single(self) -> bool:
        return self.rows == 1 and self.cols == 1

    def contains(self, row: int, col: int) -> bool:
        return self.row_start <= row <= self.row_end and self.col_start <= col <= self.col_end

    def iter_cells(self) -> Iterator[Tuple[int, int]]:
        for r in range(self.row_start, self.row_end + 1):
            for c in range(self.col_start, self.col_end + 1):
                yield r, c

    def offset(self, dr: int, dc: int) -> GridRange:
        return GridRange(
            self.row_start + dr, self.col_start + dc,
            self.row_end + dr, self.col_end + dc,
        )

    def union(self, other: GridRange) -> GridRange:
        return GridRange(
            min(self.row_start, other.row_start),
            min(self.col_start, other.col_start),
            max(self.row_end, other.row_end),
            max(self.col_end, other.col_end),
        )

    def intersection(self, other: GridRange) -> GridRange:
        return GridRange(
            max(self.row_start, other.row_start),
            max(self.col_start, other.col_start),
            min(self.row_end, other.row_end),
            min(self.col_end, other.col_end),
        )

    def to_list(self) -> List[dict]:
        return [
            {"row_start": self.row_start, "col_start": self.col_start,
             "row_end": self.row_end, "col_end": self.col_end}
        ]
