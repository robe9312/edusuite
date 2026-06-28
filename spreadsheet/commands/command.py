from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...

    @abstractmethod
    def redo(self) -> None:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    def merge(self, other: Command) -> bool:
        return False


@dataclass
class CellChange:
    row: int
    col: int
    old_cell: Any
    new_cell: Any


class SetCellCommand(Command):
    def __init__(self, grid: Any, changes: List[CellChange],
                 desc: str = "Edit cell"):
        self._grid = grid
        self._changes = changes
        self._desc = desc
        self._executed = False

    def execute(self) -> None:
        if self._executed:
            return
        for ch in self._changes:
            self._grid.set_cell(ch.row, ch.col, ch.new_cell)
        self._executed = True

    def undo(self) -> None:
        for ch in self._changes:
            self._grid.set_cell(ch.row, ch.col, ch.old_cell)

    def redo(self) -> None:
        self.execute()

    @property
    def description(self) -> str:
        return self._desc

    def merge(self, other: Command) -> bool:
        if not isinstance(other, SetCellCommand):
            return False
        self._changes.extend(other._changes)
        return True


class InsertRowColumnCommand(Command):
    def __init__(self, grid: Any, dim: str, index: int, count: int = 1):
        self._grid = grid
        self._dim = dim
        self._index = index
        self._count = count

    def execute(self) -> None:
        pass

    def undo(self) -> None:
        pass

    def redo(self) -> None:
        self.execute()

    @property
    def description(self) -> str:
        return f"Insert {self._count} {self._dim}(s) at {self._index}"
