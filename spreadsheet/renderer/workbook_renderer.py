from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout, QLabel

from .render_context import RenderContext
from .sheet_renderer import SheetRenderer


class WorkbookRenderer:
    """
    Orquestador principal del renderer de Workbook.

    Recibe:
      - Workbook JSON (dict)
      - Theme y config (opcional)

    Produce:
      - Un `QStackedWidget` con una página por hoja.

    Reglas:
      - Itera hojas.
      - Crea un `SheetRenderer` por hoja.
      - NO conoce estilos ni widgets específicos.
    """

    def __init__(self, workbook: Optional[Dict[str, Any]] = None, theme: str = "default"):
        self.workbook: Dict[str, Any] = workbook or {}
        self.theme = theme

    def render(self, parent: Optional[QWidget] = None) -> QStackedWidget:
        stack = QStackedWidget(parent)

        sheets = self._sheets()
        if not sheets:
            empty = QLabel("Esta sección no contiene una plantilla Luckysheet válida.")
            stack.addWidget(empty)
            return stack

        for idx, sheet_data in enumerate(sheets):
            ctx = RenderContext(
                workbook=self.workbook,
                sheet_index=idx,
                sheet_name=sheet_data.get("name", f"Sheet{idx+1}"),
                sheet_data=sheet_data,
                theme=self.theme,
            )
            try:
                sheet = SheetRenderer(ctx).render(parent=stack)
            except Exception:
                sheet = QLabel(f"Error al renderizar '{ctx.sheet_name}'.")
            stack.addWidget(sheet)

        return stack

    def _sheets(self) -> List[Dict[str, Any]]:
        wb = self.workbook or {}
        if isinstance(wb.get("sheets"), list) and wb["sheets"]:
            return wb["sheets"]
        if isinstance(wb, list) and wb:
            return wb
        return []

    @classmethod
    def from_json(cls, json_str: str, theme: str = "default") -> "WorkbookRenderer":
        data: Any = json.loads(json_str) if json_str else {}
        if isinstance(data, dict) and "sheetData" in data:
            sheets = data.get("sheetData") or []
            return cls(workbook={"sheets": sheets}, theme=theme)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return cls(workbook={"sheets": data}, theme=theme)
        if isinstance(data, dict):
            return cls(workbook=data, theme=theme)
        return cls()
