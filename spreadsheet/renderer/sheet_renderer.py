from __future__ import annotations
from typing import Any, Dict, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
)

from .render_context import RenderContext
from .layout_renderer import LayoutRenderer
from .style_renderer import StyleRenderer
from .merge_renderer import MergeRenderer


class SheetRenderer:
    """
    Renderiza UNA hoja del workbook en un `QTableWidget`.

    Pipeline (NO hace otra cosa):
      Sheet JSON
        → Layout (área activa, tamaños)
        → Style (fuente, color, alineación, formato)
        → Merge (setSpan)
        → Widgets (placeholders en cada celda según tipo/bloqueo)
        → QTableWidget

    No sabe de la aplicación ni del dominio.
    """

    def __init__(self, context: RenderContext):
        self.ctx = context
        self._normalize_sheet()
        self.layout = LayoutRenderer(context)
        self.styles = StyleRenderer()
        self.merges = MergeRenderer(context.sheet_data)
        self.celldata_index = self._index_celldata(context.sheet_data)

    def _normalize_sheet(self) -> None:
        sheet = self.ctx.sheet_data or {}
        celldata = sheet.get("celldata")
        if isinstance(celldata, list) and len(celldata) > 0:
            return
        data = sheet.get("data")
        if isinstance(data, list) and len(data) > 0:
            flat = []
            for r, row in enumerate(data):
                if not isinstance(row, list):
                    continue
                for c, cell in enumerate(row):
                    if cell is not None:
                        v = cell if isinstance(cell, dict) else {"v": cell, "m": str(cell)}
                        flat.append({"r": r, "c": c, "v": v})
            if flat:
                sheet["celldata"] = flat

    def render(self, parent=None) -> QTableWidget:
        self.layout.compute()
        rows = self.ctx.rows()
        cols = self.ctx.cols()

        table = QTableWidget(rows, cols, parent)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setDefaultSectionSize(
            self.layout.DEFAULT_COL_WIDTH
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        for c in range(cols):
            width = self.layout.column_width(c)
            table.setColumnWidth(c, width)

        for r in range(rows):
            height = self.layout.row_height(r)
            table.setRowHeight(r, height)

        for r in range(rows):
            for c in range(cols):
                cell_data = self.celldata_index.get((r, c))
                item = QTableWidgetItem("")
                if cell_data is not None:
                    text = self.styles.display_value(cell_data)
                    item.setText(text)
                    self.styles.apply_to_item(item, cell_data)
                table.setItem(r, c, item)

        for span in self.merges.spans():
            r, c, rs, cs = span["r"], span["c"], span["rs"], span["cs"]
            if r < rows and c < cols:
                try:
                    table.setSpan(r, c, rs, cs)
                except Exception:
                    pass

        return table

    @staticmethod
    def _index_celldata(sheet: Dict[str, Any]) -> Dict[Tuple[int, int], Dict[str, Any]]:
        idx: Dict[Tuple[int, int], Dict[str, Any]] = {}
        celldata = (sheet or {}).get("celldata") or []
        for cell in celldata:
            r = cell.get("r")
            c = cell.get("c")
            v = cell.get("v")
            if r is None or c is None:
                continue
            if isinstance(v, dict):
                idx[(r, c)] = v
            elif v is not None:
                idx[(r, c)] = {"v": v}
        return idx
