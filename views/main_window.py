#!/usr/bin/env python3
"""
MainWindow simplificado para mostrar solo planillas educativas.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from db.database import get_all_custom_sections, get_custom_section
from config import APP_NAME, COLOR_BG, COLOR_PRIMARY
from widgets.workbook_renderer import WorkbookRenderView
from widgets.meta_editor import MetaEditorWidget as MetaEditor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Planillas Educativas")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 800)

        # Widgets principales
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar para listar planillas
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setStyleSheet(f"background: {COLOR_BG}; border: none;")
        self.sidebar.itemClicked.connect(self._on_planilla_selected)

        # Área principal
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {COLOR_BG};")

        # Splitter para permitir redimensionar
        splitter = QSplitter()
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.stack)
        splitter.setSizes([200, 800])

        root.addWidget(splitter)

        # Cargar planillas
        self._load_planillas()

        # Mostrar mensaje inicial si no hay planillas
        if self.sidebar.count() == 0:
            self._show_welcome_message()

    def _load_planillas(self):
        """Cargar todas las planillas disponibles."""
        self.sidebar.clear()
        sections = get_all_custom_sections()
        
        for section in sections:
            item = QListWidgetItem(section.get("name", "Planilla sin nombre"))
            item.setData(Qt.UserRole, section["id"])
            item.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
            self.sidebar.addItem(item)

    def _on_planilla_selected(self, item):
        """Mostrar la planilla seleccionada."""
        section_id = item.data(Qt.UserRole)
        section = get_custom_section(section_id)
        
        if not section:
            QMessageBox.warning(self, "Error", "No se encontró la planilla seleccionada.")
            return

        # Crear o reutilizar vista de planilla
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if hasattr(widget, "section_id") and widget.section_id == section_id:
                self.stack.setCurrentWidget(widget)
                return

        # Crear nueva vista
        view = WorkbookRenderView(section)
        view.section_id = section_id
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)

    def _show_welcome_message(self):
        """Mostrar mensaje de bienvenida cuando no hay planillas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("No hay planillas creadas")
        label.setStyleSheet("font-size: 18px; color: #666;")
        layout.addWidget(label)
        
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def edit_current_planilla(self):
        """Abrir el MetaEditor para la planilla actual."""
        current = self.stack.currentWidget()
        if hasattr(current, "section_id"):
            editor = MetaEditor(current.section_id)
            if editor.exec() == MetaEditor.Accepted:
                # Recargar la planilla después de editar
                current.reload()
                self._load_planillas()  # Refrescar la lista