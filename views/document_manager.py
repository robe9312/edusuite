from __future__ import annotations
import json
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QScrollArea, QFrame,
    QSplitter, QLineEdit, QComboBox, QMenu, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QTextEdit,
    QStackedWidget, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from PySide6.QtWidgets import QHeaderView, QTableView
from config import *
from services import ServiceRegistry
from spreadsheet.services import DocumentService
from spreadsheet import MemoryGrid, SpreadsheetEngine, WorkbookAdapter, MemoryDataSource
from widgets.engine_sheet_model import EngineSheetModel


class DocumentManagerView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._doc_service: DocumentService = ServiceRegistry.instance().spreadsheet().doc_service
        self._categories: list = []
        self._documents: list = []
        self._current_doc: Optional[dict] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._build_header()
        layout.addWidget(self._header_widget)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLOR_BORDER}; }}")

        self._build_list_panel(splitter)
        self._build_detail_panel(splitter)

        splitter.setSizes([360, 600])
        layout.addWidget(splitter, 1)

        self._load_categories()
        self._refresh()

    def _build_header(self):
        self._header_widget = QFrame()
        hl = QHBoxLayout(self._header_widget)
        hl.setContentsMargins(24, 16, 24, 12)

        title = QLabel("Editor de Plantillas")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLOR_TEXT};")
        hl.addWidget(title)

        hl.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar documentos...")
        self._search.setFixedWidth(220)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_SURFACE}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                padding: 6px 12px; font-size: 13px;
            }}
        """)
        self._search.textChanged.connect(self._refresh)
        hl.addWidget(self._search)

        self._cat_filter = QComboBox()
        self._cat_filter.setStyleSheet(f"""
            QComboBox {{
                background: {COLOR_SURFACE}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                padding: 6px 12px; font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; border-left: 1px solid {COLOR_BORDER}; padding-left: 4px; content: "▾"; }}
        """)
        self._cat_filter.currentIndexChanged.connect(lambda: self._refresh())
        hl.addWidget(self._cat_filter)

        new_btn = QPushButton("+ Nuevo")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: white;
                border: none; padding: 6px 18px;
                font-weight: 600; font-size: 13px;
            }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        new_btn.clicked.connect(self._new_document)
        hl.addWidget(new_btn)

    def _build_list_panel(self, parent):
        panel = QWidget()
        panel.setStyleSheet(f"background: {COLOR_SURFACE};")
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        self._list = QListWidget()
        self._list.setFrameShape(QFrame.NoFrame)
        self._list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {COLOR_SURFACE}; color: {COLOR_TEXT};
                border: none; font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 16px;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            QListWidget::item:selected {{
                background: {COLOR_SIDEBAR_ACTIVE};
            }}
            QListWidget::item:hover {{
                background: {COLOR_HOVER};
            }}
        """)
        self._list.currentItemChanged.connect(self._on_selection)
        vl.addWidget(self._list)

        parent.addWidget(panel)

    def _build_detail_panel(self, parent):
        panel = QWidget()
        panel.setStyleSheet(f"background: {COLOR_BG};")
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        self._detail_stack = QStackedWidget()
        self._empty_detail = QLabel("Seleccione un documento\npara ver su contenido")
        self._empty_detail.setAlignment(Qt.AlignCenter)
        self._empty_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")

        self._detail_content = QWidget()
        dvl = QVBoxLayout(self._detail_content)
        dvl.setContentsMargins(0, 0, 0, 0)
        dvl.setSpacing(0)

        # Info header
        info = QFrame()
        info.setStyleSheet(f"background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};")
        il = QHBoxLayout(info)
        il.setContentsMargins(12, 10, 12, 10)

        self._detail_icon = QLabel("")
        self._detail_icon.setStyleSheet("font-size: 28px;")
        il.addWidget(self._detail_icon)

        meta = QVBoxLayout()
        self._detail_title = QLabel("")
        self._detail_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT};")
        meta.addWidget(self._detail_title)
        self._detail_meta = QLabel("")
        self._detail_meta.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIM};")
        meta.addWidget(self._detail_meta)

        self._detail_desc = QLabel("")
        self._detail_desc.setWordWrap(True)
        self._detail_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED}; padding: 2px 0;")
        self._detail_desc.setVisible(False)
        meta.addWidget(self._detail_desc)

        il.addLayout(meta, 1)

        dvl.addWidget(info)

        # Quick View (SpreadsheetEngine renderer)
        self._quick_view = QWidget()
        self._quick_view.setStyleSheet(f"background: {COLOR_SURFACE};")
        qvl = QVBoxLayout(self._quick_view)
        qvl.setContentsMargins(8, 8, 8, 8)
        self._render_container = QVBoxLayout()
        qvl.addLayout(self._render_container)
        self._render_widget: Optional[QWidget] = None
        dvl.addWidget(self._quick_view, 1)

        # Action buttons
        actions = QFrame()
        actions.setStyleSheet(f"background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};")
        al = QHBoxLayout(actions)
        al.setContentsMargins(8, 6, 8, 6)
        al.setSpacing(6)

        self._btn_edit = QPushButton("Editar")
        self._btn_edit.setCursor(Qt.PointingHandCursor)
        self._btn_edit.clicked.connect(self._edit_document)
        self._style_action_btn(self._btn_edit, COLOR_ACCENT)
        al.addWidget(self._btn_edit)

        self._btn_duplicate = QPushButton("Duplicar")
        self._btn_duplicate.setCursor(Qt.PointingHandCursor)
        self._btn_duplicate.clicked.connect(self._duplicate_document)
        self._style_action_btn(self._btn_duplicate, COLOR_TEXT)
        al.addWidget(self._btn_duplicate)

        self._btn_history = QPushButton("Historial")
        self._btn_history.setCursor(Qt.PointingHandCursor)
        self._btn_history.clicked.connect(self._show_history)
        self._style_action_btn(self._btn_history, COLOR_TEXT)
        al.addWidget(self._btn_history)

        al.addStretch()

        self._btn_delete = QPushButton("Eliminar")
        self._btn_delete.setCursor(Qt.PointingHandCursor)
        self._btn_delete.clicked.connect(self._delete_document)
        self._style_action_btn(self._btn_delete, "#ef4444")
        al.addWidget(self._btn_delete)

        dvl.addWidget(actions)

        self._detail_stack.addWidget(self._empty_detail)
        self._detail_stack.addWidget(self._detail_content)
        vl.addWidget(self._detail_stack, 1)

        parent.addWidget(panel)

    def _style_action_btn(self, btn, color):
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {color};
                border: 1px solid {color}; padding: 5px 14px;
                font-size: 12px; font-weight: 500;
            }}
            QPushButton:hover {{
                background: {color}15;
            }}
        """)

    def _refresh(self):
        cat_id = self._cat_filter.currentData()
        search = self._search.text().strip() or None
        self._documents = self._doc_service.list_documents(
            category_id=cat_id, search=search,
        )
        self._list.clear()
        for doc in self._documents:
            icon = doc.get("icon", "\U0001f4c4")
            name = doc["name"]
            cat_name = doc.get("category_name", "")
            updated = doc.get("updated_at", "")
            line1 = f"{icon}  {name}"
            line2 = f"    {cat_name}  ·  {updated}" if cat_name else f"    {updated}"
            text = f"{line1}\n{line2}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, doc["id"])
            self._list.addItem(item)
        self._detail_stack.setCurrentIndex(0)

    def _on_selection(self, current, previous):
        if not current:
            return
        doc_id = current.data(Qt.UserRole)
        doc = next((d for d in self._documents if d["id"] == doc_id), None)
        if not doc:
            return
        self._current_doc = doc
        icon = doc.get("icon", "\U0001f4c4")
        self._detail_icon.setText(icon)
        self._detail_title.setText(doc["name"])
        cat_name = doc.get("category_name", "Documento")
        updated = doc.get("updated_at", "")
        created = doc.get("created_at", "")
        desc = doc.get("description", "")
        meta_parts = [cat_name]
        if created:
            meta_parts.append(f"Creado: {created}")
        if updated:
            meta_parts.append(f"Actualizado: {updated}")
        self._detail_meta.setText("  ·  ".join(meta_parts))
        self._detail_desc.setVisible(bool(desc))
        self._detail_desc.setText(desc)
        self._detail_stack.setCurrentIndex(1)
        self._load_quick_view(doc_id)

    def _load_quick_view(self, doc_id: int):
        if self._render_widget:
            self._render_container.removeWidget(self._render_widget)
            self._render_widget.deleteLater()
            self._render_widget = None

        wb_json = self._doc_service.latest_workbook(doc_id)
        if not wb_json:
            no_data = QLabel("Vista rápida no disponible")
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
            self._render_container.addWidget(no_data)
            return

        try:
            wb_data = json.loads(wb_json) if isinstance(wb_json, str) else wb_json

            adapter = WorkbookAdapter()
            adapter.load(wb_data)
            grid = adapter.sheet(0)
            if grid is None:
                raise ValueError("Sin hoja")
            source = MemoryDataSource(grid.row_count(), grid.col_count())
            engine = SpreadsheetEngine(grid, source)

            model = EngineSheetModel(engine)
            tv = QTableView()
            tv.setModel(model)
            tv.setAlternatingRowColors(True)
            tv.setEditTriggers(QTableView.NoEditTriggers)
            tv.horizontalHeader().setStretchLastSection(True)
            tv.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            tv.verticalHeader().setDefaultSectionSize(24)
            tv.verticalHeader().setVisible(False)
            tv.setMaximumHeight(360)
            tv.setStyleSheet(f"""
                QTableView {{
                    background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
                    gridline-color: {COLOR_BORDER}; color: {COLOR_TEXT};
                    font-size: 12px; outline: none;
                }}
                QTableView::item {{
                    padding: 2px 6px;
                }}
                QHeaderView::section {{
                    background: {COLOR_PANEL}; color: {COLOR_TEXT_DIM};
                    border: none; border-bottom: 1px solid {COLOR_BORDER};
                    padding: 4px 8px; font-size: 11px;
                }}
            """)

            self._render_widget = tv
            self._render_container.addWidget(tv)

            if adapter.sheet_count() > 1:
                tabs = QLabel(f"{adapter.sheet_count()} hojas")
                tabs.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; padding: 2px 0;")
                self._render_container.addWidget(tabs)
        except Exception:
            err = QLabel("Error al renderizar vista previa")
            err.setAlignment(Qt.AlignCenter)
            err.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
            self._render_container.addWidget(err)

    def _edit_document(self):
        if not self._current_doc:
            return
        doc_id = self._current_doc["id"]
        self._doc_service.open(doc_id)
        editor = getattr(self.main, "_editor_instance", None)
        if editor:
            self._doc_service.load_into_editor(editor, doc_id)
            editor._toggle_fullscreen()

    def _duplicate_document(self):
        if not self._current_doc:
            return
        new_id = self._doc_service.duplicate(self._current_doc["id"])
        if new_id:
            self._refresh()

    def _delete_document(self):
        if not self._current_doc:
            return
        reply = QMessageBox.question(
            self, "Eliminar documento",
            f"¿Eliminar '{self._current_doc['name']}' y todas sus versiones?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._doc_service.delete(self._current_doc["id"])
        self._current_doc = None
        self._refresh()

    def _show_history(self):
        if not self._current_doc:
            return
        versions = self._doc_service.history(self._current_doc["id"])
        if not versions:
            QMessageBox.information(self, "Historial", "No hay versiones anteriores.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Historial de versiones")
        dlg.setMinimumSize(500, 400)
        dlg.setStyleSheet(f"background: {COLOR_SURFACE}; color: {COLOR_TEXT};")
        vl = QVBoxLayout(dlg)

        title = QLabel(f"Versiones de: {self._current_doc['name']}")
        title.setStyleSheet(f"font-size: 15px; font-weight: 600; padding: 8px 0;")
        vl.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        cvl = QVBoxLayout(container)
        cvl.setSpacing(6)

        for ver in versions:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{ background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; }}
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)

            info = QVBoxLayout()
            v_label = QLabel(f"Versión {ver['version']}")
            v_label.setStyleSheet(f"font-weight: 600; color: {COLOR_TEXT};")
            info.addWidget(v_label)
            if ver.get("comment"):
                c_label = QLabel(ver["comment"])
                c_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
                info.addWidget(c_label)
            d_label = QLabel(ver.get("created_at", ""))
            d_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
            info.addWidget(d_label)
            cl.addLayout(info, 1)

            if ver.get("workbook_json"):
                rollback_btn = QPushButton("Restaurar")
                rollback_btn.setCursor(Qt.PointingHandCursor)
                rollback_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; color: {COLOR_ACCENT};
                        border: 1px solid {COLOR_ACCENT};
                        padding: 4px 12px; font-size: 11px;
                    }}
                    QPushButton:hover {{ background: {COLOR_ACCENT}15; }}
                """)
                rollback_btn.clicked.connect(
                    lambda checked, v=ver["id"]: self._rollback_to(v, dlg)
                )
                cl.addWidget(rollback_btn)

            cvl.addWidget(card)
        cvl.addStretch()
        scroll.setWidget(container)
        vl.addWidget(scroll)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dlg.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: white;
                border: none; padding: 6px 16px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        vl.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.exec()

    def _rollback_to(self, version_id, dialog):
        if not self._current_doc:
            return
        reply = QMessageBox.question(
            self, "Restaurar versión",
            "¿Restaurar esta versión? Se creará una nueva versión con este contenido.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._doc_service.rollback(self._current_doc["id"], version_id)
        dialog.accept()
        self._refresh()

    def _new_document(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nuevo documento")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(f"background: {COLOR_SURFACE}; color: {COLOR_TEXT};")

        form = QFormLayout(dlg)
        form.setSpacing(10)
        form.setContentsMargins(20, 16, 20, 16)

        title_lbl = QLabel("Crear nuevo documento")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; margin-bottom: 8px;")
        form.addRow(title_lbl)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Ej: Notas 1A")
        name_input.setStyleSheet(f"""
            QLineEdit {{ background: {COLOR_PANEL}; color: {COLOR_TEXT};
            border: 1px solid {COLOR_BORDER}; padding: 6px; }}
        """)
        form.addRow("Nombre:", name_input)

        cat_combo = QComboBox()
        cat_combo.setStyleSheet(f"""
            QComboBox {{ background: {COLOR_PANEL}; color: {COLOR_TEXT};
            border: 1px solid {COLOR_BORDER}; padding: 6px; }}
        """)
        for cat in self._categories:
            cat_combo.addItem(f"{cat.get('icon', '')}  {cat['name']}", cat["id"])
        form.addRow("Categoría:", cat_combo)

        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Descripción opcional")
        desc_input.setMaximumHeight(60)
        desc_input.setStyleSheet(f"""
            QTextEdit {{ background: {COLOR_PANEL}; color: {COLOR_TEXT};
            border: 1px solid {COLOR_BORDER}; padding: 4px; }}
        """)
        form.addRow("Descripción:", desc_input)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        btns.button(QDialogButtonBox.Ok).setText("Crear")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(f"""
            QPushButton {{ background: {COLOR_ACCENT}; color: white;
            border: none; padding: 6px 16px; font-weight: 600; }}
        """)
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {COLOR_TEXT};
            border: 1px solid {COLOR_BORDER}; padding: 6px 16px; }}
        """)
        form.addRow(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        name = name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        cat_id = cat_combo.currentData()
        desc = desc_input.toPlainText().strip()

        doc_id = self._doc_service.create(
            name=name, category_id=cat_id, description=desc,
        )
        if doc_id:
            self._refresh()

    def refresh(self):
        self._load_categories()
        self._refresh()

    def _load_categories(self):
        self._categories = self._doc_service.get_categories()
        self._cat_filter.clear()
        self._cat_filter.addItem("Todas las categorías", None)
        for cat in self._categories:
            self._cat_filter.addItem(f"{cat.get('icon', '')}  {cat['name']}", cat["id"])

