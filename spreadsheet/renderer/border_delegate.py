from __future__ import annotations
from typing import Any, Dict, Optional

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

from .style_renderer import StyleRenderer


class BorderDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._styles = StyleRenderer()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)

        v = index.data(Qt.UserRole)
        if not isinstance(v, dict):
            v = None
        bd = self._styles.cell_border(v)
        if not bd:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        rect = option.rect
        sides = [
            ("l", rect.left(), rect.top(), rect.left(), rect.bottom()),
            ("r", rect.right() - 1, rect.top(), rect.right() - 1, rect.bottom()),
            ("t", rect.left(), rect.top(), rect.right(), rect.top()),
            ("b", rect.left(), rect.bottom() - 1, rect.right(), rect.bottom() - 1),
        ]

        for side, x1, y1, x2, y2 in sides:
            info = bd.get(side)
            if not info:
                continue
            pen = self._border_pen(info)
            if pen is None:
                continue
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)

        painter.restore()

    @staticmethod
    def _border_pen(info: Dict[str, Any]) -> Optional[QPen]:
        style = info.get("style", 0)
        if style == 0:
            return None
        color_str = info.get("color", "#000")
        color = QColor(color_str)

        mapping = {
            1: (1, Qt.SolidLine),
            2: (2, Qt.SolidLine),
            3: (1, Qt.DashLine),
            4: (1, Qt.DotLine),
            5: (3, Qt.SolidLine),
            6: (1, Qt.CustomDashLine),
            7: (0, Qt.SolidLine),
        }
        width, qstyle = mapping.get(style, (1, Qt.SolidLine))
        return QPen(color, width, qstyle)
