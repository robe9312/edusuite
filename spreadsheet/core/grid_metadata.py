from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ColumnMeta:
    key: str
    name: str
    width: int = 120
    frozen: bool = False
    hidden: bool = False
    editable: bool = True
    resizable: bool = True
    sortable: bool = True
    filterable: bool = True
    data_type: str = "text"
    alignment: str = "left"
    group: str = ""
    tag: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RowMeta:
    height: int = 30
    hidden: bool = False
    frozen: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FreezeConfig:
    rows: int = 0
    columns: int = 0


@dataclass
class GridMetadata:
    name: str = ""
    description: str = ""
    columns: List[ColumnMeta] = field(default_factory=list)
    rows: Dict[int, RowMeta] = field(default_factory=dict)
    freeze: FreezeConfig = field(default_factory=FreezeConfig)
    row_count: int = 0
    column_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def column(self, idx: int) -> Optional[ColumnMeta]:
        return self.columns[idx] if 0 <= idx < len(self.columns) else None

    def add_column(self, col: ColumnMeta) -> None:
        self.columns.append(col)
        self.column_count = len(self.columns)
