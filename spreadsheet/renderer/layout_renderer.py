from __future__ import annotations
from typing import Any, Dict

from .render_context import RenderContext


class LayoutRenderer:
    """
    Calcula dimensiones a partir del workbook JSON:
      - Área activa (top, left, bottom, right).
      - Anchos de columna.
      - Alturas de fila.
      - Filas/columnas ocultas.

    NO pinta nada. NO modifica datos.
    Solo escribe el resultado en el `RenderContext`.
    """

    DEFAULT_COL_WIDTH = 73
    DEFAULT_ROW_HEIGHT = 20

    def __init__(self, context: RenderContext):
        self.ctx = context

    def compute(self) -> None:
        ctx = self.ctx
        sheet = ctx.sheet_data or {}
        celldata = sheet.get("celldata") or []
        config = sheet.get("config") or {}

        top, left, bottom, right = self._compute_active_area(celldata, config)
        ctx.top, ctx.left, ctx.bottom, ctx.right = top, left, bottom, right

    @staticmethod
    def _compute_active_area(celldata, config):
        max_r = -1
        max_c = -1
        for cell in celldata:
            r = cell.get("r")
            c = cell.get("c")
            if r is None or c is None:
                continue
            v = cell.get("v")
            if v is None:
                continue
            if isinstance(v, dict):
                has_content = any(
                    v.get(key) not in (None, "", " ")
                    for key in ("v", "m", "f", "ct", "bg")
                )
            else:
                has_content = bool(v)
            if has_content:
                if r > max_r:
                    max_r = r
                if c > max_c:
                    max_c = c

        cfg_top = (config.get("rowlen") or {})
        cfg_col = (config.get("columnlen") or {})

        if max_r < 0:
            max_r = max((int(k) for k in cfg_top.keys() if str(k).isdigit()), default=-1)
        if max_c < 0:
            max_c = max((int(k) for k in cfg_col.keys() if str(k).isdigit()), default=-1)

        if max_r < 0:
            max_r = 9
        if max_c < 0:
            max_c = 4

        return (0, 0, max_r, max_c)

    def column_width(self, col_index: int) -> int:
        sheet = self.ctx.sheet_data or {}
        columnlen = (sheet.get("config") or {}).get("columnlen") or {}
        if str(col_index) in columnlen:
            return int(columnlen[str(col_index)])
        return self.DEFAULT_COL_WIDTH

    def row_height(self, row_index: int) -> int:
        sheet = self.ctx.sheet_data or {}
        rowlen = (sheet.get("config") or {}).get("rowlen") or {}
        if str(row_index) in rowlen:
            return int(rowlen[str(row_index)])
        return self.DEFAULT_ROW_HEIGHT
