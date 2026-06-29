from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QComboBox, QLineEdit, QDialog, QRadioButton, QButtonGroup, QFrame,
    QCheckBox, QHeaderView, QFileDialog, QTableWidget, QTableWidgetItem,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QShortcut, QKeySequence, QUndoStack, QPainter, QColor, QFont,
)

from config import *
from models.column_definition import ColumnDef, ColumnType
from models.spreadsheet_model import SpreadsheetTableModel
from models.grade_proxy import GradeProxyModel
from widgets.spreadsheet_view import SpreadsheetView
from widgets.student_panel import StudentPanel
from core.clipboard_engine import ClipboardEngine
from repositories import subject_repo, student_repo, course_repo, grade_repo


EXPORT_MODES = [
    ("course_trimester", "Curso + Trimestre", ""),
    ("course_all", "Curso completo (3T)", ""),
    ("student", "Por alumno", ""),
    ("summary", "Resumen por trimestre", ""),
]


class ExportDialog(QDialog):
    def __init__(self, parent=None, courses=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Notas")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self.courses = courses or []
        self.result_data = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel("Selecciona el tipo de exportación")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px;")
        layout.addWidget(title)
        self.mode_group = QButtonGroup(self)
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(8)
        self.mode_radios = []
        for key, label, desc in EXPORT_MODES:
            rb = QRadioButton(f" {label}")
            rb.setStyleSheet(f"""
                QRadioButton {{ color: {COLOR_TEXT}; font-size: 13px;
                    padding: 6px 10px; border: 1px solid {COLOR_BORDER};
                    background: {COLOR_INPUT}; }}
                QRadioButton:hover {{ background: {COLOR_HOVER}; }}
                QRadioButton::indicator {{
                    width: 14px; height: 14px; border: 1px solid {COLOR_BORDER};
                    background: {COLOR_INPUT}; }}
                QRadioButton::indicator:checked {{
                    background: {COLOR_ACCENT}; border-color: {COLOR_ACCENT}; }}
            """)
            mode_layout.addWidget(rb)
            self.mode_group.addButton(rb, len(self.mode_radios))
            self.mode_radios.append((key, rb))
        layout.addLayout(mode_layout)

        opts = QHBoxLayout()
        opts.setSpacing(12)
        for label, attr, items in [
            ("Curso:", "course_combo", True),
            ("Trimestre:", "period_combo", ["T1", "T2", "T3"]),
        ]:
            ol = QVBoxLayout()
            ol.setSpacing(4)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            ol.addWidget(lbl)
            combo = QComboBox()
            combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 8px; min-height: 28px; }}")
            if isinstance(items, list):
                combo.addItems(items)
            else:
                combo.addItems(self.courses)
            ol.addWidget(combo)
            opts.addLayout(ol)
            setattr(self, attr, combo)

        sl = QVBoxLayout()
        sl.setSpacing(4)
        sl.addWidget(QLabel("Alumno:"))
        sl.itemAt(0).widget().setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.student_combo = QComboBox()
        self.student_combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 8px; min-height: 28px; }}")
        from repositories import student_repo
        students = student_repo.all()
        for s in students:
            self.student_combo.addItem(f"{s.get('code','')} - {s.get('nombre','')}", s["id"])
        sl.addWidget(self.student_combo)
        opts.addLayout(sl)
        layout.addLayout(opts)

        self.mode_group.buttonClicked.connect(self._on_mode_change)
        self._on_mode_change()

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"QPushButton {{ padding: 0 24px; height: 36px; border: none; background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }} QPushButton:hover {{ background: {COLOR_HOVER}; }}")
        cancel_btn.clicked.connect(self.reject)
        export_btn = QPushButton("Exportar")
        export_btn.setStyleSheet(f"QPushButton {{ padding: 0 24px; height: 36px; border: none; background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }} QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}")
        export_btn.clicked.connect(self._accept)
        btns.addWidget(cancel_btn)
        btns.addWidget(export_btn)
        layout.addLayout(btns)

    def _on_mode_change(self):
        btn_id = self.mode_group.checkedId()
        if btn_id < 0:
            btn_id = 0
        key = self.mode_radios[btn_id][0]
        self.course_combo.parent().setVisible(key in ("course_trimester", "course_all"))
        self.period_combo.parent().setVisible(key in ("course_trimester", "summary"))
        self.student_combo.parent().setVisible(key == "student")

    def _accept(self):
        btn_id = self.mode_group.checkedId()
        if btn_id < 0:
            QMessageBox.warning(self, "Selecciona", "Elige un tipo de exportación.")
            return
        key = self.mode_radios[btn_id][0]
        data = {"mode": key}
        if key in ("course_trimester", "course_all"):
            data["course"] = self.course_combo.currentText()
        if key in ("course_trimester", "summary"):
            data["period"] = self.period_combo.currentText()
        if key == "student":
            data["student_id"] = self.student_combo.currentData()
        self.result_data = data
        self.accept()


class _GradeStatBadge(QFrame):
    def __init__(self, label, value="—", color=COLOR_TEXT):
        super().__init__()
        self.setStyleSheet(f"background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(2)
        self.val = QLabel(str(value))
        self.val.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {color};")
        lay.addWidget(self.val)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_DIM};")
        lay.addWidget(lbl)


def _build_subject_grade_columns(subject):
    group = subject.get("name", "")
    sid = subject["id"]
    cols = [
        ColumnDef("nombre", "Alumno", ColumnType.FROZEN, width=200, align="left", frozen=True),
    ]
    for p in ("T1", "T2", "T3"):
        cols.append(ColumnDef(
            id=f"{sid}_{p}", name=p,
            col_type=ColumnType.GRADE, group=group,
            width=64, editable=True, heatmap=True,
            meta={"subject_id": sid, "period": p},
            tooltip=f"{group} {p}",
        ))
    cols.append(ColumnDef(
        id=f"{sid}_prom", name="Prom",
        col_type=ColumnType.COMPUTED, group=group,
        width=56, formula="avg", heatmap=True,
        tooltip=f"{group} Promedio",
    ))
    cols.append(ColumnDef(
        id=f"{sid}_estado", name="Estado",
        col_type=ColumnType.STATUS, group=group,
        width=56,
        tooltip=f"{group} Estado",
    ))
    return cols


class ImportPreviewDialog(QDialog):
    def __init__(self, diff, errors, summary, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vista previa de importación")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self._diff = diff
        self._accepted = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Revisa los datos antes de importar")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(title)

        stats = QHBoxLayout()
        stats.setSpacing(16)
        s = summary
        for label, val, col in [
            ("Nuevos", s.get("new", 0), COLOR_SUCCESS),
            ("Sin cambios", s.get("same", 0), COLOR_TEXT_MUTED),
            ("Conflictos", s.get("conflicts", 0), "#F9A825"),
            ("Errores", s.get("errors", 0), COLOR_DANGER),
        ]:
            box = QFrame()
            box.setStyleSheet(f"background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(12, 8, 12, 8)
            v = QLabel(str(val))
            v.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {col};")
            v.setAlignment(Qt.AlignCenter)
            bl.addWidget(v)
            l = QLabel(label)
            l.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_DIM};")
            l.setAlignment(Qt.AlignCenter)
            bl.addWidget(l)
            stats.addWidget(box)
        layout.addLayout(stats)

        if errors:
            el = QLabel("\n".join(errors[:5]))
            el.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 11px; padding: 8px; border: 1px solid {COLOR_DANGER};")
            layout.addWidget(el)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Estado", "Alumno", "Asignatura", "Nota"])
        table.setStyleSheet(f"""
            QTableWidget {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER};
                font-size: 11px; color: {COLOR_TEXT}; }}
            QHeaderView::section {{ background: {COLOR_SURFACE}; color: {COLOR_TEXT_MUTED};
                font-weight: 600; padding: 4px 8px; border: 1px solid {COLOR_BORDER}; }}
        """)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        status_colors = {"new": COLOR_SUCCESS, "conflict": "#F9A825", "same": COLOR_TEXT_MUTED, "error": COLOR_DANGER}
        for row_idx, entry in enumerate(diff):
            st = entry.get("_status", "new")
            table.insertRow(row_idx)
            s_item = QTableWidgetItem({"new": "✚ Nuevo", "conflict": "⚠ Conflicto", "same": "✓ Sin cambio", "error": "✗ Error"}.get(st, st))
            s_item.setForeground(QColor(status_colors.get(st, COLOR_TEXT)))
            table.setItem(row_idx, 0, s_item)
            table.setItem(row_idx, 1, QTableWidgetItem(entry.get("code", "")))
            from db.database import get_subject
            subj = get_subject(entry.get("subject_id"))
            table.setItem(row_idx, 2, QTableWidgetItem(subj["name"] if subj else "?"))
            sc = entry.get("score")
            table.setItem(row_idx, 3, QTableWidgetItem(str(sc) if sc is not None else ""))
        table.resizeColumnsToContents()
        layout.addWidget(table, 1)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"QPushButton {{ padding: 0 24px; height: 36px; border: none; background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }} QPushButton:hover {{ background: {COLOR_HOVER}; }}")
        cancel_btn.clicked.connect(self.reject)
        import_btn = QPushButton("Importar")
        import_btn.setStyleSheet(f"QPushButton {{ padding: 0 24px; height: 36px; border: none; background: {COLOR_SUCCESS}; color: #ffffff; font-size: 13px; font-weight: 600; }} QPushButton:hover {{ background: #3d9142; }}")
        import_btn.clicked.connect(self._accept_import)
        btns.addWidget(cancel_btn)
        btns.addWidget(import_btn)
        layout.addLayout(btns)

    def _accept_import(self):
        from exporters.excel_importer import apply_import_result
        accepted = apply_import_result(self._diff)
        self._accepted = accepted
        self.accept()


class _CierreHeader(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._cierre_idx = -1

    def set_cierre_idx(self, idx):
        self._cierre_idx = idx
        self.update()

    def paintSection(self, painter, rect, logicalIndex):
        if logicalIndex == self._cierre_idx:
            painter.save()
            painter.fillRect(rect, QColor("#2E7D32"))
            painter.setPen(QColor("#ffffff"))
            f = painter.font()
            f.setBold(True)
            painter.setFont(f)
            model = self.model()
            text = model.headerData(logicalIndex, Qt.Horizontal, Qt.DisplayRole) or ""
            painter.drawText(rect, Qt.AlignCenter, str(text))
            painter.restore()
            return
        super().paintSection(painter, rect, logicalIndex)


class GradesView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._current_subject = None
        self._students_data = []
        self._model = None
        self._proxy = None
        self._undo_stack = QUndoStack()
        self._clipboard = None
        self._cierre_visible = False
        self._cierre_header = None
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._build()
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_all)
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._undo_stack.redo)

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main_area = QWidget()
        layout = QVBoxLayout(main_area)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Libro de Calificaciones")
        header.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(header)

        self._subject_header = QFrame()
        self._subject_header.setStyleSheet(f"background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER};")
        self._subject_header.setFixedHeight(60)
        sh_lay = QHBoxLayout(self._subject_header)
        sh_lay.setContentsMargins(20, 0, 20, 0)
        sh_lay.setSpacing(20)

        self._subj_title = QLabel("")
        self._subj_title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_TEXT};")
        sh_lay.addWidget(self._subj_title)

        self._subj_teacher = QLabel("")
        self._subj_teacher.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        sh_lay.addWidget(self._subj_teacher)

        self._subj_course = QLabel("")
        self._subj_course.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        sh_lay.addWidget(self._subj_course)

        self._subj_students = QLabel("")
        self._subj_students.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        sh_lay.addWidget(self._subj_students)

        sh_lay.addStretch()

        self._subj_year = QLabel("")
        self._subj_year.setStyleSheet(f"""
            color: {COLOR_ACCENT}; font-size: 11px; font-weight: 600;
            padding: 3px 10px;
            border: 1px solid {COLOR_ACCENT};
        """)
        sh_lay.addWidget(self._subj_year)

        self._subject_header.setVisible(False)
        layout.addWidget(self._subject_header)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        course_lbl = QLabel("Curso:")
        course_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        filter_bar.addWidget(course_lbl)
        self.course_combo = QComboBox()
        self.course_combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 10px; min-height: 30px; min-width: 100px; }} QComboBox:focus {{ border-color: {COLOR_ACCENT}; }}")
        self.course_combo.currentTextChanged.connect(self._on_course_changed)
        filter_bar.addWidget(self.course_combo)

        subj_lbl = QLabel("Asignatura:")
        subj_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        filter_bar.addWidget(subj_lbl)
        self.subject_combo = QComboBox()
        self.subject_combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 10px; min-height: 30px; min-width: 160px; }} QComboBox:focus {{ border-color: {COLOR_ACCENT}; }}")
        self.subject_combo.currentTextChanged.connect(self._load_grades)
        filter_bar.addWidget(self.subject_combo)

        filter_bar.addStretch()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar alumno...")
        self._search_input.setFixedWidth(180)
        self._search_input.setFixedHeight(32)
        self._search_input.textChanged.connect(self._on_search)
        self._search_input.setStyleSheet(f"QLineEdit {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; font-size: 12px; padding: 0 12px; }} QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}")
        filter_bar.addWidget(self._search_input)

        self.save_btn = QPushButton("Guardar")
        self.save_btn.setStyleSheet(f"QPushButton {{ padding: 0 16px; height: 32px; border: none; background: {COLOR_SUCCESS}; color: #ffffff; font-size: 12px; }} QPushButton:hover {{ background: #3d9142; }}")
        self.save_btn.clicked.connect(self._save_all)
        filter_bar.addWidget(self.save_btn)

        export_btn = QPushButton("Exportar")
        export_btn.setStyleSheet(f"QPushButton {{ padding: 0 16px; height: 32px; border: none; background: {COLOR_ACCENT}; color: #ffffff; font-size: 12px; }} QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}")
        export_btn.clicked.connect(self._export_dialog)
        filter_bar.addWidget(export_btn)

        import_btn = QPushButton("Importar ACTA")
        import_btn.setStyleSheet(f"QPushButton {{ padding: 0 16px; height: 32px; border: none; background: #FF8F00; color: #ffffff; font-size: 12px; font-weight: 600; }} QPushButton:hover {{ background: #FF6F00; }}")
        import_btn.clicked.connect(self._import_acta)
        filter_bar.addWidget(import_btn)

        self._cierre_cb = QCheckBox("CIERRE JUNIO")
        self._cierre_cb.setStyleSheet(f"""
            QCheckBox {{ color: {COLOR_TEXT}; font-size: 12px; font-weight: 600; spacing: 6px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT}; }}
            QCheckBox::indicator:checked {{ background: #4CAF50; border-color: #4CAF50; }}
        """)
        self._cierre_cb.setCursor(Qt.PointingHandCursor)
        self._cierre_cb.toggled.connect(self._toggle_cierre)
        filter_bar.addWidget(self._cierre_cb)

        luckysheet_btn = QPushButton("Editar diseño")
        luckysheet_btn.setStyleSheet(f"QPushButton {{ padding: 0 16px; height: 32px; border: 1px solid {COLOR_BORDER}; background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 12px; }} QPushButton:hover {{ background: {COLOR_HOVER}; color: {COLOR_TEXT}; }}")
        luckysheet_btn.clicked.connect(self._open_in_luckysheet)
        filter_bar.addWidget(luckysheet_btn)

        layout.addLayout(filter_bar)

        self.spreadsheet = SpreadsheetView()
        self.spreadsheet.main_table.clicked.connect(self._on_row_click)
        self.spreadsheet.frozen_table.clicked.connect(self._on_row_click)
        layout.addWidget(self.spreadsheet, 1)

        self._clipboard = ClipboardEngine(self.spreadsheet)
        for t in [self.spreadsheet.frozen_table, self.spreadsheet.main_table]:
            QShortcut(QKeySequence("Ctrl+C"), t, self._clipboard.copy)
            QShortcut(QKeySequence("Ctrl+V"), t, self._clipboard.paste)
            QShortcut(QKeySequence("Ctrl+X"), t, self._clipboard.cut)
            QShortcut(QKeySequence("Delete"), t, self._clipboard.delete_selection)

        footer = QHBoxLayout()
        self._footer_frame = QWidget()
        self._footer_layout = QHBoxLayout(self._footer_frame)
        self._footer_layout.setContentsMargins(0, 0, 0, 0)
        self._footer_layout.setSpacing(12)
        footer.addWidget(self._footer_frame)
        footer.addStretch()
        layout.addLayout(footer)

        outer.addWidget(main_area, 1)

        self.student_panel = StudentPanel()
        self.student_panel.close_btn.clicked.connect(self._close_panel)
        outer.addWidget(self.student_panel)

    def _on_search(self, text):
        self._search_timer.start()

    def _apply_search(self):
        text = self._search_input.text().strip().lower()
        if self._proxy:
            self._proxy.set_search_text(text)

    def _on_row_click(self, index):
        row = index.row()
        if self._proxy:
            src_idx = self._proxy.mapToSource(index)
            row = src_idx.row()
        if row < 0 or row >= len(self._students_data):
            return
        self.student_panel.show_student(self._students_data[row])

    def _close_panel(self):
        self.student_panel.hide_panel()

    def _update_subject_header(self, subject, course, students):
        if not subject or not course:
            self._subject_header.setVisible(False)
            return
        self._subj_title.setText(subject.get("name", ""))
        teacher_id = subject.get("teacher_id")
        if teacher_id:
            try:
                from db.database import get_db_path
                import sqlite3
                conn = sqlite3.connect(get_db_path())
                row = conn.execute("SELECT nombre FROM teachers WHERE id=?", (teacher_id,)).fetchone()
                teacher_name = row[0] if row else ""
                conn.close()
            except Exception:
                teacher_name = ""
            self._subj_teacher.setText(f"👨‍🏫 {teacher_name}" if teacher_name else "")
            self._subj_teacher.setVisible(bool(teacher_name))
        else:
            self._subj_teacher.setVisible(False)
        self._subj_course.setText(f"📖 {course}")
        count = len(students) if students else 0
        self._subj_students.setText(f"👥 {count} estudiantes")
        self._subj_year.setText("Evaluación 2025-2026")
        self._subject_header.setVisible(True)

    def _on_course_changed(self):
        self._populate_subjects()
        self._load_grades()

    def _populate_subjects(self):
        course = self.course_combo.currentText()
        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        if course:
            subs = subject_repo.for_course(course)
            for s in subs:
                self.subject_combo.addItem(s.get("name", ""), s.get("id"))
        self.subject_combo.blockSignals(False)

    def _load_grades(self):
        course = self.course_combo.currentText()
        subj_name = self.subject_combo.currentText()
        if not course or not subj_name:
            self.spreadsheet.setModel(None)
            self._subject_header.setVisible(False)
            return

        subjects = subject_repo.for_course(course)
        subject = next((s for s in subjects if s.get("name") == subj_name), None)
        if not subject:
            self.spreadsheet.setModel(None)
            self._subject_header.setVisible(False)
            return
        self._current_subject = subject

        students = student_repo.by_course(course)
        self._students_data = students

        self._update_subject_header(subject, course, students)

        if not students:
            self.spreadsheet.setModel(None)
            return

        cols = _build_subject_grade_columns(subject)

        if self._cierre_visible and cols:
            sid = subject["id"]
            cierre_col = ColumnDef(
                id=f"{sid}_cierre", name="CIERRE JUNIO",
                col_type=ColumnType.COMPUTED, group=cols[1].group,
                width=72, formula="avg", heatmap=True,
                tooltip="Cierre Junio (promedio T1-T2-T3)",
            )
            for i, c in enumerate(cols):
                if c.id == f"{sid}_estado":
                    cols.insert(i, cierre_col)
                    break

        def load_cell(row_id, col_def):
            meta = col_def.meta
            if "subject_id" in meta and "period" in meta:
                g = grade_repo.get_grade(row_id, meta["subject_id"], meta["period"])
                if g:
                    try:
                        return float(g["score"])
                    except (ValueError, TypeError):
                        pass
            return None

        def save_cell(row_id, col_id, val):
            for col in cols:
                if col.id == col_id and col.meta:
                    meta = col.meta
                    if "subject_id" in meta and "period" in meta:
                        if val is not None:
                            grade_repo.set_grade(row_id, meta["subject_id"], meta["period"], val)
                        return

        self._model = SpreadsheetTableModel(
            cols, students,
            load_cell_fn=load_cell,
            save_cell_fn=save_cell,
            undo_stack=self._undo_stack,
            repo=grade_repo,
        )
        self._proxy = GradeProxyModel()
        self._proxy.setSourceModel(self._model)
        self.spreadsheet.setModel(self._proxy)

        if self._cierre_visible:
            cierre_idx = -1
            for i, c in enumerate(cols):
                if c.id.endswith("_cierre"):
                    cierre_idx = i
                    break
            mt = self.spreadsheet.main_table
            existing = mt.horizontalHeader()
            ch = _CierreHeader()
            ch.set_cierre_idx(cierre_idx)
            ch.setStretchLastSection(False)
            ch.setSectionResizeMode(QHeaderView.Interactive)
            mt.setHorizontalHeader(ch)
            self._cierre_header = ch
            existing.deleteLater()
        else:
            self._cierre_header = None

        self._apply_search()
        self._update_footer()

    def _toggle_cierre(self, checked):
        self._cierre_visible = checked
        self._load_grades()

    def _import_acta(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar ACTA de notas",
            "", "Excel (*.xlsx);;Todos (*)",
        )
        if not path:
            return
        from exporters.excel_importer import import_grades_from_excel
        diff, errors, summary = import_grades_from_excel(path)
        if not diff and not errors:
            QMessageBox.information(self, "Importación", "No se encontraron datos para importar.")
            return
        dlg = ImportPreviewDialog(diff, errors, summary, self)
        if dlg.exec() != QDialog.Accepted:
            return
        accepted = dlg._accepted
        QMessageBox.information(
            self, "Importación completada",
            f"{accepted} notas importadas.\n"
            f"{summary.get('same', 0)} sin cambios.\n"
            f"{summary.get('conflicts', 0)} conflictos resueltos.\n"
            + (f"{summary.get('errors', 0)} errores ignorados." if summary.get('errors') else "")
        )
        self.refresh()

    def _update_footer(self):
        while self._footer_layout.count():
            item = self._footer_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._model or not self._students_data or not self._current_subject:
            return

        sid = self._current_subject["id"]
        vals = []
        for stu in self._students_data:
            for p in ("T1", "T2", "T3"):
                g = grade_repo.get_grade(stu["id"], sid, p)
                if g:
                    try:
                        vals.append(float(g["score"]))
                    except (ValueError, TypeError):
                        pass
        if not vals:
            return

        prom = round(sum(vals) / len(vals), 1)
        approved = sum(1 for v in vals if v >= 5.0)
        failed = len(vals) - approved

        badges = [
            ("Promedio", prom, COLOR_TEXT),
            ("Aprobados", approved, COLOR_SUCCESS),
            ("Suspensos", failed, COLOR_DANGER),
            ("Notas registradas", len(vals), COLOR_TEXT_MUTED),
        ]
        for label, value, color in badges:
            self._footer_layout.addWidget(_GradeStatBadge(label, value, color))

    def _save_all(self):
        if not self._model:
            return
        count = self._model.dirty_count()
        self._model.save_dirty()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Guardado")
        msg.setText(f"{count} notas guardadas." if count else "Sin cambios.")
        msg.exec()
        self.main.refresh_stats()

    def _open_in_luckysheet(self):
        if not self._current_subject:
            return
        from services import ServiceRegistry
        ss = ServiceRegistry.instance().spreadsheet()
        subj = self._current_subject
        doc_name = f"Notas - {subj.get('name', '')}"
        docs = ss.doc_service.list_documents(search=doc_name)
        doc = docs[0] if docs else None
        if doc:
            ss.doc_service.open(doc["id"])
            editor = self.main._editor_instance
            if editor:
                ss.doc_service.load_into_editor(editor)
                self.main.stack.setCurrentWidget(editor)
                self.main.header_bar.set_breadcrumb(f"Inicio / Editor - {doc.get('name', 'Documento')}")

    def _export_dialog(self):
        courses = course_repo.all_distinct()
        if not courses:
            QMessageBox.warning(self, "Sin datos", "No hay cursos.")
            return
        dlg = ExportDialog(self, courses)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return
        data = dlg.result_data
        mode = data.get("mode")
        try:
            from exporters.excel_exporter import (
                export_grades_to_excel, export_grades_by_course_and_trimester,
                export_grades_by_student, export_grades_summary_by_trimester,
            )
            path = None
            if mode == "course_trimester":
                path = export_grades_by_course_and_trimester(data["course"], data["period"])
            elif mode == "course_all":
                path = export_grades_to_excel(data["course"])
            elif mode == "student":
                path = export_grades_by_student(data["student_id"])
            elif mode == "summary":
                path = export_grades_summary_by_trimester(data["period"])
            if path:
                QMessageBox.information(self, "Exportado", f"Excel generado:\n{path}")
            else:
                QMessageBox.warning(self, "Sin datos", "No se encontraron datos.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{e}")

    def show_student_panel(self, student_data):
        self.student_panel.show_student(student_data)

    def on_escape(self):
        self._close_panel()

    def refresh(self):
        current_course = self.course_combo.currentText()
        current_subj = self.subject_combo.currentText()
        self.course_combo.blockSignals(True)
        self.course_combo.clear()
        courses = course_repo.all_distinct()
        self.course_combo.addItems(courses)
        if current_course in courses:
            self.course_combo.setCurrentText(current_course)
        elif courses:
            self.course_combo.setCurrentText(courses[0])
        self.course_combo.blockSignals(False)
        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        if self.course_combo.currentText():
            subs = subject_repo.for_course(self.course_combo.currentText())
            for s in subs:
                self.subject_combo.addItem(s.get("name", ""), s.get("id"))
            if current_subj and any(s.get("name") == current_subj for s in subs):
                self.subject_combo.setCurrentText(current_subj)
        self.subject_combo.blockSignals(False)
        self._load_grades()
