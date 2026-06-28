from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class CellType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    FORMULA = "formula"
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    COMPUTED = "computed"
    BLANK = "blank"


@dataclass
class CellValidation:
    type: str
    formula1: Optional[str] = None
    formula2: Optional[str] = None
    allow_blank: bool = True
    show_input: bool = True
    show_error: bool = True
    error_title: str = ""
    error_body: str = ""
    error_style: str = "stop"


@dataclass
class GridCell:
    value: Any = None
    display: str = ""
    data_type: CellType = CellType.TEXT
    formula: Optional[str] = None
    style_id: int = 0
    editable: bool = True
    readonly: bool = False
    metadata: dict = field(default_factory=dict)
    validation: Optional[CellValidation] = None
    tag: Optional[str] = None

    @classmethod
    def blank(cls) -> GridCell:
        return cls(value=None, display="", data_type=CellType.BLANK, editable=True)

    @classmethod
    def text(cls, value: str) -> GridCell:
        return cls(value=value, display=str(value), data_type=CellType.TEXT)

    @classmethod
    def number(cls, value: float, display: Optional[str] = None) -> GridCell:
        return cls(
            value=value,
            display=display if display is not None else str(value),
            data_type=CellType.NUMBER,
        )

    @classmethod
    def from_formula(cls, expr: str, display: str = "") -> GridCell:
        return cls(
            value=None,
            display=display,
            data_type=CellType.FORMULA,
            formula=expr,
            editable=False,
            readonly=True,
        )

    def copy(self) -> GridCell:
        return GridCell(
            value=self.value,
            display=self.display,
            data_type=self.data_type,
            formula=self.formula,
            style_id=self.style_id,
            editable=self.editable,
            readonly=self.readonly,
            metadata=dict(self.metadata),
            validation=self.validation,
            tag=self.tag,
        )
