from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class DataSource(ABC):
    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def load_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int) -> Dict[Tuple[int, int], Any]:
        ...

    @abstractmethod
    def save_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int,
                   data: Dict[Tuple[int, int], Any]) -> None:
        ...

    @abstractmethod
    def row_count(self) -> int:
        ...

    @abstractmethod
    def col_count(self) -> int:
        ...

    @abstractmethod
    def flush(self) -> None:
        ...
