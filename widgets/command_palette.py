from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut

from config import COLOR_SURFACE, COLOR_INPUT, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_MUTED, COLOR_HOVER, COLOR_ACCENT

COMMANDS = [
    ("Inicio", "dashboard", "Ir al dashboard principal"),
    ("Notas", "grades", "Libro de calificaciones"),
    ("Estudiantes", "students", "Gestionar estudiantes"),
    ("Docentes", "teachers", "Gestionar docentes"),
    ("Asignaturas", "subjects", "Gestionar asignaturas"),
    ("Matrícula", "enrollment", "Gestión de matrícula"),
    ("Backup", "backup", "Copias de seguridad"),
    ("Configuración", "settings", "Ajustes del sistema"),
    ("Nuevo estudiante", "students:new", "Registrar un nuevo alumno"),
    ("Nuevo docente", "teachers:new", "Registrar un nuevo profesor"),
    ("Exportar notas", "grades:export", "Exportar calificaciones a Excel"),
]


class CommandPalette(QDialog):
    command_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comandos")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMaximumHeight(400)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar comando...")
        self.search.setFixedHeight(44)
        self.search.textChanged.connect(self._filter)
        self.search.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_INPUT}; border: none;
                border-bottom: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT}; font-size: 14px; padding: 0 16px;
            }}
        """)
        layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none;
                font-size: 13px; outline: none;
            }}
            QListWidget::item {{
                padding: 10px 16px; color: {COLOR_TEXT_DIM};
                border: none;
            }}
            QListWidget::item:hover {{
                background: {COLOR_HOVER}; color: {COLOR_TEXT};
            }}
            QListWidget::item:selected {{
                background: {COLOR_ACCENT}; color: #ffffff;
            }}
        """)
        self.list_widget.itemClicked.connect(self._on_click)
        layout.addWidget(self.list_widget)

        self._all_items = []
        for title, key, desc in COMMANDS:
            item = QListWidgetItem(f"{title}")
            item.setData(Qt.UserRole, key)
            item.setToolTip(desc)
            self._all_items.append(item)
            self.list_widget.addItem(item)

        self.search.setFocus()

    def _filter(self, text):
        t = text.lower()
        self.list_widget.clear()
        for item in self._all_items:
            if t in item.text().lower() or t in item.toolTip().lower():
                self.list_widget.addItem(item)

    def _on_click(self, item):
        key = item.data(Qt.UserRole)
        self.command_selected.emit(key)
        self.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.reject()
        elif key == Qt.Key_Return:
            item = self.list_widget.currentItem()
            if item:
                self._on_click(item)
        elif key == Qt.Key_Down:
            self.list_widget.setCurrentRow(
                min(self.list_widget.currentRow() + 1, self.list_widget.count() - 1)
            )
        elif key == Qt.Key_Up:
            self.list_widget.setCurrentRow(max(self.list_widget.currentRow() - 1, 0))
        else:
            super().keyPressEvent(event)
