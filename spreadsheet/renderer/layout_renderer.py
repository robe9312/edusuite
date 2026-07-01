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
    DEFAULT_ROW_HEIGHT = 19

    def __init__(self, context: RenderContext):
        self.ctx = context

    def compute(self) -> None:
        ctx = self.ctx
        sheet = ctx.sheet_data or {}

        # Prefer metadata.active_area saved by the editor
        meta = sheet.get("metadata") or {}
        aa = meta.get("active_area")
        if (aa and all(k in aa for k in ("top", "left", "bottom", "right"))
                and aa["bottom"] >= aa["top"] and aa["right"] >= aa["left"]
                and aa["bottom"] >= 0 and aa["right"] >= 0):
            ctx.top = aa["top"]
            ctx.left = aa["left"]
            ctx.bottom = aa["bottom"]
            ctx.right = aa["right"]
            return

        celldata = sheet.get("celldata") or []
        if not celldata:
            data = sheet.get("data")
            if isinstance(data, list) and len(data) > 0:
                celldata = self._data_to_celldata(data)
        config = sheet.get("config") or {}

        top, left, bottom, right = self._compute_active_area(celldata, config)
        ctx.top, ctx.left, ctx.bottom, ctx.right = top, left, bottom, right

    @staticmethod
    def _data_to_celldata(data):
        flat = []
        for r, row in enumerate(data):
            if not isinstance(row, list):
                continue
            for c, cell in enumerate(row):
                if cell is not None:
                    v = cell if isinstance(cell, dict) else {"v": cell, "m": str(cell)}
                    flat.append({"r": r, "c": c, "v": v})
        return flat

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

        # Extender área con rowlen/columnlen (pueden definir filas/cols sin datos)
        cfg_top = (config.get("rowlen") or {})
        cfg_col = (config.get("columnlen") or {})
        if isinstance(cfg_top, dict):
            for k in cfg_top:
                if str(k).isdigit():
                    i = int(k)
                    if i > max_r: max_r = i
        if isinstance(cfg_col, dict):
            for k in cfg_col:
                if str(k).isdigit():
                    i = int(k)
                    if i > max_c: max_c = i

        # Mínimo 10×5 si no hay nada
        if max_r < 0:
            max_r = 9
        if max_c < 0:
            max_c = 4

        return (0, 0, max_r, max_c)

    def column_width(self, col_index: int) -> int:
        sheet = self.ctx.sheet_data or {}
        raw = (sheet.get("config") or {}).get("columnlen") or {}
        val = self._get_length(raw, col_index)
        return val if val is not None else self.DEFAULT_COL_WIDTH

    def row_height(self, row_index: int) -> int:
        sheet = self.ctx.sheet_data or {}
        raw = (sheet.get("config") or {}).get("rowlen") or {}
        val = self._get_length(raw, row_index)
        return val if val is not None else self.DEFAULT_ROW_HEIGHT

    @staticmethod
    def _get_length(raw, index: int):
        if isinstance(raw, dict):
            key = str(index)
            return int(raw[key]) if key in raw else None
        if isinstance(raw, list):
            return int(raw[index]) if index < len(raw) and raw[index] is not None else None
        return None
