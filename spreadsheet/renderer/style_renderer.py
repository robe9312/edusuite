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

        font = QFont()
        ff = v.get("ff") or "Arial"
        font.setFamily(ff)
        fs = v.get("fs")
        font.setPointSize(int(fs) if fs else 11)
        if v.get("bl") == 1:
            font.setBold(True)
        if v.get("it") == 1:
            font.setItalic(True)

        font_color = self._color(v.get("fc"))
        if font_color:
            from PySide6.QtWidgets import QTableWidgetItem
            if isinstance(item, QTableWidgetItem):
                item.setForeground(font_color)

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

        from PySide6.QtWidgets import QTableWidgetItem
        if isinstance(item, QTableWidgetItem):
            item.setTextAlignment(align)
            item.setFont(font)

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
