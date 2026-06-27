from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
    QFormLayout, QDialog, QDoubleSpinBox, QDateEdit,
    QFrame, QAbstractItemView,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from db.database import (
    get_all_school_years, get_active_school_year, get_school_year,
    create_school_year, set_active_school_year, update_school_year,
    get_enrollments_by_year, upsert_enrollment, get_enrollment,
    get_enrollment_stats, get_debtors, seed_enrollment_for_year,
    get_all_students,
)
from config import *
from ui_style import Input, Combo, Table, Header, Panel


class SchoolYearDialog(QDialog):
    def __init__(self, parent=None, year_data=None):
        super().__init__(parent)
        self.year_data = year_data
        self.setWindowTitle("Editar Año Escolar" if year_data else "Nuevo Año Escolar")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setLabelAlignment(Qt.AlignRight)

        ls = f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"

        self.label_input = Input("Ej: 2024-2025")
        lbl = QLabel("Ano")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.label_input)

        spin_s = f"""
            QDoubleSpinBox {{
                padding: 0 12px; height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT}; color: {COLOR_TEXT}; font-size: 13px;
            }}
            QDoubleSpinBox:focus {{ border-color: {COLOR_ACCENT}; }}
        """
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(0)
        self.amount_input.setPrefix("XAF ")
        self.amount_input.setValue(0)
        self.amount_input.setStyleSheet(spin_s)
        lbl = QLabel("Monto del ano")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.amount_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        save_btn.clicked.connect(self._accept)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addRow(btns)

        if self.year_data:
            self._populate()

    def _populate(self):
        self.label_input.setText(self.year_data.get("label", ""))
        self.amount_input.setValue(self.year_data.get("default_amount", 0))

    def _accept(self):
        label = self.label_input.text().strip()
        if not label:
            QMessageBox.warning(self, "Campo requerido", "El ano escolar es obligatorio.")
            return
        self.data = {
            "label": label,
            "default_amount": self.amount_input.value(),
        }
        self.accept()


class PaymentDialog(QDialog):
    def __init__(self, parent=None, student_name="", enrollment_data=None):
        super().__init__(parent)
        self.enrollment_data = enrollment_data
        self.setWindowTitle(f"Pago - {student_name}" if student_name else "Registrar Pago")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setLabelAlignment(Qt.AlignRight)

        ls = f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"
        spin_s = f"""
            QDoubleSpinBox {{
                padding: 0 12px; height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT}; color: {COLOR_TEXT}; font-size: 13px;
            }}
            QDoubleSpinBox:focus {{ border-color: {COLOR_ACCENT}; }}
        """

        self.total_input = QDoubleSpinBox()
        self.total_input.setRange(0, 999999999)
        self.total_input.setDecimals(0)
        self.total_input.setPrefix("XAF ")
        self.total_input.setValue(50000)
        self.total_input.setStyleSheet(spin_s)
        lbl = QLabel("Total a pagar")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.total_input)

        self.paid_input = QDoubleSpinBox()
        self.paid_input.setRange(0, 999999999)
        self.paid_input.setDecimals(0)
        self.paid_input.setPrefix("XAF ")
        self.paid_input.setValue(0)
        self.paid_input.setStyleSheet(spin_s)
        lbl = QLabel("Monto pagado")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.paid_input)

        date_s = f"""
            QDateEdit {{
                padding: 0 12px; height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT}; color: {COLOR_TEXT}; font-size: 13px;
            }}
            QDateEdit:focus {{ border-color: {COLOR_ACCENT}; }}
        """
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setStyleSheet(date_s)
        lbl = QLabel("Fecha de pago")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.date_input)

        self.notes_input = Input("Opcional")
        lbl = QLabel("Notas")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.notes_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        save_btn.clicked.connect(self._accept)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addRow(btns)

        if self.enrollment_data:
            self._populate()

    def _populate(self):
        d = self.enrollment_data
        self.total_input.setValue(d.get("total_amount", 0))
        self.paid_input.setValue(d.get("paid_amount", 0))
        if d.get("payment_date"):
            try:
                self.date_input.setDate(QDate.fromString(d["payment_date"], "yyyy-MM-dd"))
            except Exception:
                pass
        self.notes_input.setText(d.get("notes", ""))

    def _accept(self):
        self.data = {
            "total_amount": self.total_input.value(),
            "paid_amount": self.paid_input.value(),
            "payment_date": self.date_input.date().toString("yyyy-MM-dd"),
            "notes": self.notes_input.text().strip(),
        }
        self.accept()


class EnrollmentView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        h = Header("Matricula y Pagos")
        layout.addWidget(h)

        year_bar = QHBoxLayout()
        year_bar.setSpacing(10)

        lbl = QLabel("Ano escolar")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        year_bar.addWidget(lbl)

        self.year_combo = Combo()
        self.year_combo.setMinimumWidth(200)
        self.year_combo.currentIndexChanged.connect(self._on_year_change)
        year_bar.addWidget(self.year_combo)

        self.year_amount_label = QLabel("")
        self.year_amount_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
        year_bar.addWidget(self.year_amount_label)

        new_year_btn = QPushButton("Nuevo Ano")
        new_year_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        new_year_btn.clicked.connect(self._new_school_year)
        year_bar.addWidget(new_year_btn)

        seed_btn = QPushButton("Cargar Estudiantes")
        seed_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_SUCCESS}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: #3d9142; }}
        """)
        seed_btn.clicked.connect(self._seed_students)
        year_bar.addWidget(seed_btn)

        year_bar.addStretch()
        layout.addLayout(year_bar)

        stats_panel = Panel()
        sl = stats_panel.layout()
        self.stats_label = QLabel("Selecciona un ano escolar")
        self.stats_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        sl.addWidget(self.stats_label)
        layout.addWidget(stats_panel)

        export_bar = QHBoxLayout()
        export_bar.setSpacing(8)
        export_bar.addStretch()

        export_all_btn = QPushButton("Exportar todo")
        export_all_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        export_all_btn.clicked.connect(self._export_all)
        export_bar.addWidget(export_all_btn)

        export_debtors_btn = QPushButton("Exportar deudores")
        export_debtors_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_DANGER}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: #b71c1c; }}
        """)
        export_debtors_btn.clicked.connect(self._export_debtors)
        export_bar.addWidget(export_debtors_btn)

        layout.addLayout(export_bar)

        self.table = Table()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "CODIGO", "ESTUDIANTE", "CURSO", "TOTAL", "PAGADO",
            "DEUDA", "ESTADO", "ACCIONES",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

    def _on_year_change(self):
        self._load_data()

    def _new_school_year(self):
        dlg = SchoolYearDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                year_id = create_school_year(d["label"], d["default_amount"])
                set_active_school_year(year_id)

                resp = QMessageBox.question(
                    self, "Cargar estudiantes",
                    "Cargar todos los estudiantes activos en la matricula de este ano?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if resp == QMessageBox.Yes:
                    seed_enrollment_for_year(year_id, d["default_amount"])

                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _seed_students(self):
        year_id = self.year_combo.currentData()
        if not year_id:
            QMessageBox.warning(self, "Sin ano", "Selecciona o crea un ano escolar primero.")
            return
        year = get_school_year(year_id)
        try:
            created = seed_enrollment_for_year(year_id, year["default_amount"])
            QMessageBox.information(self, "Cargados", f"{created} estudiantes anadidos a la matricula.")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _edit_payment(self, enrollment_id, student_name, student_id, school_year_id):
        enr = None
        for row_data in getattr(self, "_current_data", []):
            if row_data["id"] == enrollment_id:
                enr = row_data
                break
        dlg = PaymentDialog(self, student_name, enr)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                upsert_enrollment(
                    student_id, school_year_id,
                    d["total_amount"], d["paid_amount"],
                    d["payment_date"], d["notes"],
                )
                self._load_data()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _status_text(self, status):
        if status == "pagado":
            return "Pagado"
        elif status == "parcial":
            return "Parcial"
        return "Pendiente"

    def _load_data(self):
        year_id = self.year_combo.currentData()
        if not year_id:
            self.table.setRowCount(0)
            self.stats_label.setText("Selecciona un ano escolar")
            return

        enrollments = get_enrollments_by_year(year_id)
        stats = get_enrollment_stats(year_id)
        self._current_data = enrollments

        self.table.setRowCount(len(enrollments))
        for i, e in enumerate(enrollments):
            name = e.get('student_name', '')
            total = e.get("total_amount", 0)
            paid = e.get("paid_amount", 0)
            debt = total - paid
            status = e.get("status", "pendiente")

            self.table.setItem(i, 0, QTableWidgetItem(e.get("student_code", "")))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(e.get("grade_level", "")))

            total_item = QTableWidgetItem(f"XAF {total:,.0f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 3, total_item)

            paid_item = QTableWidgetItem(f"XAF {paid:,.0f}")
            paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            paid_item.setForeground(QColor(COLOR_SUCCESS) if paid >= total else QColor(COLOR_WARNING))
            self.table.setItem(i, 4, paid_item)

            debt_item = QTableWidgetItem(f"XAF {debt:,.0f}")
            debt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            debt_item.setForeground(QColor(COLOR_DANGER) if debt > 0 else QColor(COLOR_TEXT_DIM))
            self.table.setItem(i, 5, debt_item)

            self.table.setItem(i, 6, QTableWidgetItem(self._status_text(status)))

            actions = QWidget()
            act_layout = QHBoxLayout(actions)
            act_layout.setContentsMargins(2, 0, 2, 0)
            act_layout.setSpacing(4)

            pay_btn = QPushButton("$")
            pay_btn.setFixedSize(28, 24)
            pay_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {COLOR_BORDER};
                    background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 11px; }}
                QPushButton:hover {{ background: {COLOR_HOVER}; }}
            """)
            pay_btn.clicked.connect(
                lambda checked, eid=e["id"], nm=name, sid=e["student_id"], syid=year_id:
                    self._edit_payment(eid, nm, sid, syid)
            )
            act_layout.addWidget(pay_btn)
            act_layout.addStretch()
            self.table.setCellWidget(i, 7, actions)

        if stats:
            debt_total = stats["total_esperado"] - stats["total_cobrado"]
            self.stats_label.setText(
                f"Total: {stats['total']}  |  "
                f"{stats['pagados']} pagados  |  "
                f"{stats['parciales']} parcial  |  "
                f"{stats['pendientes']} pendiente  |  "
                f"XAF {stats['total_esperado']:,.0f} esperado  |  "
                f"XAF {stats['total_cobrado']:,.0f} cobrado  |  "
                f"XAF {debt_total:,.0f} pendiente"
            )

    def _export_all(self):
        year_id = self.year_combo.currentData()
        if not year_id:
            QMessageBox.warning(self, "Sin ano", "Selecciona un ano escolar.")
            return
        try:
            from exporters.excel_exporter import export_enrollment_list
            path = export_enrollment_list(year_id, only_debtors=False)
            QMessageBox.information(self, "Exportado", f"Lista completa:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _export_debtors(self):
        year_id = self.year_combo.currentData()
        if not year_id:
            QMessageBox.warning(self, "Sin ano", "Selecciona un ano escolar.")
            return
        try:
            from exporters.excel_exporter import export_enrollment_list
            path = export_enrollment_list(year_id, only_debtors=True)
            QMessageBox.information(self, "Exportado", f"Lista de deudores:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh(self):
        self.year_combo.blockSignals(True)
        self.year_combo.clear()

        years = get_all_school_years()
        for y in years:
            prefix = "> " if y["active"] else ""
            label = f"{prefix}{y['label']}"
            self.year_combo.addItem(label, y["id"])
            if y["active"]:
                self.year_combo.setCurrentIndex(self.year_combo.count() - 1)

        active_year = get_active_school_year()
        if active_year:
            self.year_amount_label.setText(
                f"Monto: XAF {active_year['default_amount']:,.0f}"
            )
        self.year_combo.blockSignals(False)
        self._load_data()
