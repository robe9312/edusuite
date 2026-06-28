from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple
from ..core.grid_range import GridRange


class SelectionMode(Enum):
    SINGLE = "single"
    ROW = "row"
    COLUMN = "column"
    RANGE = "range"
    MULTI_RANGE = "multi_range"


@dataclass
class SelectionState:
    mode: SelectionMode = SelectionMode.SINGLE
    active: Tuple[int, int] = (0, 0)
    ranges: List[GridRange] = field(default_factory=list)
    anchor: Optional[Tuple[int, int]] = None

    @property
    def current(self) -> Optional[GridRange]:
        return self.ranges[-1] if self.ranges else None

    def select_cell(self, row: int, col: int) -> None:
        self.active = (row, col)
        self.mode = SelectionMode.SINGLE
        self.ranges = [GridRange.single(row, col)]

    def select_range(self, r: GridRange) -> None:
        self.mode = SelectionMode.RANGE
        self.ranges = [r]

    def add_range(self, r: GridRange) -> None:
        self.mode = SelectionMode.MULTI_RANGE
        self.ranges.append(r)

    def clear(self) -> None:
        self.mode = SelectionMode.SINGLE
        self.ranges.clear()


class SelectionEngine:
    def __init__(self):
        self.state = SelectionState()

    def select(self, row: int, col: int) -> None:
        self.state.select_cell(row, col)

    def select_range(self, r: GridRange) -> None:
        self.state.select_range(r)

    def extend(self, row: int, col: int) -> None:
        if self.state.anchor:
            r0, c0 = self.state.anchor
            self.state.select_range(GridRange(
                min(r0, row), min(c0, col),
                max(r0, row), max(c0, col),
            ))

    def clear(self) -> None:
        self.state.clear()
