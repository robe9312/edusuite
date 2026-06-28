from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple


class ClipboardFormat(Enum):
    TEXT = "text"
    CSV = "csv"
    GRID_CELLS = "grid_cells"
    FORMULA = "formula"


@dataclass
class ClipboardData:
    format: ClipboardFormat
    data: Any
    source_range: Optional[Tuple[int, int, int, int]] = None


class Clipboard:
    def __init__(self):
        self._content: Optional[ClipboardData] = None

    def copy(self, data: ClipboardData) -> None:
        self._content = data

    def cut(self, data: ClipboardData) -> None:
        self._content = data

    def paste(self) -> Optional[ClipboardData]:
        return self._content

    def has_data(self) -> bool:
        return self._content is not None

    def clear(self) -> None:
        self._content = None
