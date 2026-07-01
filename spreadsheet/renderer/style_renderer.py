from __future__ import annotations
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


class StyleRenderer:
    """
    Aplica estilo visual a partir de los metadatos de la celda (`v`/`ct`/`bg`/`ff`/`fc`/`ht`/`vt`/`bd`).

    No modifica el valor de la celda. Solo expone helpers.
    """

    @staticmethod
    def _color(value: Any) -> Optional[QColor]:
        if not value:
            return None
        s = str(value)
        if s.startswith("#") and len(s) in (7, 9):
            return QColor(s)
        return QColor(s)

    def apply_to_item(self, item, v: Optional[Dict[str, Any]]) -> None:
        """Aplica el estilo de una celda Luckysheet a un QTableWidgetItem."""
        if not isinstance(v, dict):
            return

        bg = v.get("bg")
        if bg:
            c = self._color(bg)
            if c:
                from PySide6.QtWidgets import QTableWidgetItem
                item.setBackground(c) if isinstance(item, QTableWidgetItem) else None

        font = self.cell_font(v)
        from PySide6.QtWidgets import QTableWidgetItem
        if isinstance(item, QTableWidgetItem):
            item.setFont(font)

        font_color = self._color(v.get("fc"))
        if font_color:
            if isinstance(item, QTableWidgetItem):
                item.setForeground(font_color)

        align = int(self.cell_alignment(v))
        if isinstance(item, QTableWidgetItem):
            item.setTextAlignment(align)

    def cell_font(self, v: Optional[Dict[str, Any]]) -> QFont:
        font = QFont()
        if not isinstance(v, dict):
            return font
        ff = v.get("ff") or "Arial"
        font.setFamily(ff)
        fs = v.get("fs")
        font.setPointSize(int(fs) if fs else 11)
        if v.get("bl") == 1:
            font.setBold(True)
        if v.get("it") == 1:
            font.setItalic(True)
        return font

    def cell_foreground(self, v: Optional[Dict[str, Any]]) -> Optional[QColor]:
        if not isinstance(v, dict):
            return None
        return self._color(v.get("fc"))

    def cell_background(self, v: Optional[Dict[str, Any]]) -> Optional[QColor]:
        if not isinstance(v, dict):
            return None
        return self._color(v.get("bg"))

    def cell_alignment(self, v: Optional[Dict[str, Any]]) -> Qt.AlignmentFlag:
        if not isinstance(v, dict):
            return Qt.AlignLeft | Qt.AlignVCenter
        ht = v.get("ht")
        vt = v.get("vt")
        align = Qt.AlignVCenter
        if ht == 0:
            align |= Qt.AlignLeft
        elif ht == 1:
            align |= Qt.AlignCenter
        elif ht == 2:
            align |= Qt.AlignRight
        if vt == 0:
            align |= Qt.AlignTop
        elif vt == 1:
            align |= Qt.AlignVCenter
        elif vt == 2:
            align |= Qt.AlignBottom
        return align

    def cell_wrap(self, v: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(v, dict):
            return False
        tb = v.get("tb")
        if tb in (1, "1", True):
            return True
        ct = v.get("ct")
        if isinstance(ct, dict):
            tb2 = ct.get("tb")
            if tb2 in (1, "1", True):
                return True
        return False

    def cell_border(self, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(v, dict):
            return None
        return v.get("bd")

    def display_value(self, v: Optional[Dict[str, Any]]) -> str:
        """Retorna el valor a mostrar: resultado de fórmula si existe, sino texto crudo."""
        if not isinstance(v, dict):
            return ""
        m = v.get("m")
        if m not in (None, ""):
            return str(m)
        val = v.get("v")
        if val is None:
            return ""
        if isinstance(val, (int, float)):
            return str(val)
        return str(val)
