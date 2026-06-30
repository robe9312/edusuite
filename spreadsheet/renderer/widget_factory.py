from __future__ import annotations
from typing import Any, Dict, Optional


class WidgetFactory:
    """
    Decide qué editor (`QItemEditorCreator` o similar) usar según el tipo de celda.

    Tipos soportados (v.ct o v.cellType):
      - "text"      -> QLineEdit
      - "number"    -> QDoubleSpinBox
      - "checkbox"  -> QCheckBox
      - "date"      -> QDateEdit
      - "list"      -> QComboBox (con v.dv[])
      - "richtext"  -> QPlainTextEdit

    Si la celda está bloqueada, retorna `None` => sin editor.
    """

    CELL_TYPES = {
        "text": "QLineEdit",
        "number": "QDoubleSpinBox",
        "checkbox": "QCheckBox",
        "date": "QDateEdit",
        "list": "QComboBox",
        "richtext": "QPlainTextEdit",
    }

    @staticmethod
    def resolve_class_name(v: Optional[Dict[str, Any]]) -> Optional[str]:
        if not isinstance(v, dict):
            return "QLineEdit"

        cell_type = v.get("cellType") or v.get("ct")
        if isinstance(cell_type, dict):
            cell_type = cell_type.get("t") or cell_type.get("type")

        name = (cell_type or "text").lower() if isinstance(cell_type, str) else "text"
        return WidgetFactory.CELL_TYPES.get(name, "QLineEdit")
