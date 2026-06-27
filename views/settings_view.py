from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView,
    QDialog, QLineEdit, QComboBox, QCheckBox, QTabWidget,
    QMessageBox, QDoubleSpinBox, QColorDialog, QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from config import *
from ui_style import Input, Combo
import settings_manager as sset
from db.database import (
    VIEW_PERMISSIONS,
    get_all_roles, save_role, update_role, delete_role,
    get_role_permissions, set_role_permissions,
    get_all_users, save_user, update_user, delete_user,
    get_all_teachers, user_exists,
    get_all_school_years, get_active_school_year, get_school_year,
    create_school_year, set_active_school_year, update_school_year,
    get_db_path,
)


# ─── Dialogs ───

class RoleEditDialog(QDialog):
    def __init__(self, role=None):
        super().__init__()
        self.role = role
        self.setWindowTitle("Editar Rol" if role else "Nuevo Rol")
        self.setFixedSize(480, 420)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_BG}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(title)

        self.name_input = Input("Nombre del rol")
        self.desc_input = Input("Descripcion")
        if role:
            self.name_input.setText(role["name"])
            self.desc_input.setText(role.get("description", ""))
        layout.addWidget(self.name_input)
        layout.addWidget(self.desc_input)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        layout.addWidget(sep)

        perm_label = QLabel("Permisos")
        perm_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(perm_label)

        self.perm_checks = {}
        existing_perms = set(get_role_permissions(role["id"])) if role else set()
        for vk, vlabel in VIEW_PERMISSIONS.items():
            cb = QCheckBox(vlabel)
            cb.setChecked(vk in existing_perms)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {COLOR_TEXT};
                    font-size: 13px;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 16px; height: 16px;
                    border: 1px solid {COLOR_BORDER};
                    background: {COLOR_INPUT};
                }}
                QCheckBox::indicator:checked {{
                    background: {COLOR_ACCENT};
                    border-color: {COLOR_ACCENT};
                }}
            """)
            self.perm_checks[vk] = cb
            layout.addWidget(cb)

        layout.addStretch()

        btn_row = self._btn_row()
        layout.addLayout(btn_row)

    def _btn_row(self):
        row = QHBoxLayout()
        row.setSpacing(8)
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet(f"""
            QPushButton {{ height: 36px; border: 1px solid {COLOR_BORDER};
                background: transparent; color: {COLOR_TEXT}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)

        save = _accent_btn("Guardar")
        save.clicked.connect(self._save)
        row.addWidget(save)
        return row

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            return
        desc = self.desc_input.text().strip()
        perm_keys = [vk for vk, cb in self.perm_checks.items() if cb.isChecked()]
        if self.role:
            update_role(self.role["id"], name=name, description=desc)
            set_role_permissions(self.role["id"], perm_keys)
        else:
            rid = save_role(name, desc)
            set_role_permissions(rid, perm_keys)
        self.accept()


class UserEditDialog(QDialog):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.setWindowTitle("Editar Usuario" if user else "Nuevo Usuario")
        self.setFixedSize(400, 350)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_BG}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(title)

        self.user_input = Input("Usuario")
        if user:
            self.user_input.setText(user["username"])
        layout.addWidget(self.user_input)

        self.pass_input = Input("Contrasena")
        if user:
            self.pass_input.setText(user.get("password", ""))
        layout.addWidget(self.pass_input)

        roles = get_all_roles()
        self.role_combo = _styled_combo()
        for r in roles:
            self.role_combo.addItem(r["name"], r["id"])
        if user:
            idx = self.role_combo.findData(user["role_id"])
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)
        layout.addWidget(self.role_combo)

        self.teacher_combo = _styled_combo()
        self.teacher_combo.addItem("(Sin docente)", None)
        teachers = get_all_teachers()
        for t in teachers:
            full = f"{t['last_name']}, {t['name']}"
            self.teacher_combo.addItem(full, t["id"])
        if user and user.get("teacher_id"):
            idx = self.teacher_combo.findData(user["teacher_id"])
            if idx >= 0:
                self.teacher_combo.setCurrentIndex(idx)
        layout.addWidget(self.teacher_combo)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet(f"""
            QPushButton {{ height: 36px; border: 1px solid {COLOR_BORDER};
                background: transparent; color: {COLOR_TEXT}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        save = _accent_btn("Guardar")
        save.clicked.connect(self._save)
        btn_row.addWidget(save)

        layout.addLayout(btn_row)

    def _save(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        if not username or not password:
            return
        role_id = self.role_combo.currentData()
        teacher_id = self.teacher_combo.currentData()
        if self.user:
            update_user(self.user["id"], username=username, password=password,
                        role_id=role_id, teacher_id=teacher_id)
        else:
            save_user(username, password, role_id, teacher_id)
        self.accept()


class SchoolYearEditDialog(QDialog):
    def __init__(self, year_data=None):
        super().__init__()
        self.year_data = year_data
        self.setWindowTitle("Editar Ano Escolar" if year_data else "Nuevo Ano Escolar")
        self.setFixedSize(400, 250)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_BG}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(title)

        self.label_input = Input("Ej: 2024-2025")
        if year_data:
            self.label_input.setText(year_data.get("label", ""))
        layout.addWidget(self.label_input)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(0)
        self.amount_input.setPrefix("XAF ")
        self.amount_input.setValue(year_data.get("default_amount", 0) if year_data else 0)
        self.amount_input.setStyleSheet(f"""
            QDoubleSpinBox {{ padding: 0 12px; height: 36px;
                border: 1px solid {COLOR_BORDER}; background: {COLOR_INPUT};
                color: {COLOR_TEXT}; font-size: 13px; }}
            QDoubleSpinBox:focus {{ border-color: {COLOR_ACCENT}; }}
        """)
        layout.addWidget(self.amount_input)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        cancel = QPushButton("Cancelar")
        cancel.setStyleSheet(f"""
            QPushButton {{ height: 36px; border: 1px solid {COLOR_BORDER};
                background: transparent; color: {COLOR_TEXT}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        save = _accent_btn("Guardar")
        save.clicked.connect(self._save)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        label = self.label_input.text().strip()
        if not label:
            QMessageBox.warning(self, "Campo requerido", "El nombre del ano es obligatorio.")
            return
        if self.year_data:
            update_school_year(self.year_data["id"], label=label,
                               default_amount=self.amount_input.value())
        else:
            create_school_year(label, self.amount_input.value())
        self.accept()


# ─── Helpers ───

def _accent_btn(text):
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{ padding: 0 16px; height: 36px; border: none;
            background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; font-weight: 500; }}
        QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
    """)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def _ghost_btn(text, color=COLOR_TEXT):
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{ padding: 0 16px; height: 36px; border: 1px solid {COLOR_BORDER};
            background: transparent; color: {color}; font-size: 13px; }}
        QPushButton:hover {{ background: {COLOR_HOVER}; }}
    """)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def _danger_btn(text):
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{ padding: 0 16px; height: 36px; border: none;
            background: {COLOR_DANGER}; color: #ffffff; font-size: 13px; }}
        QPushButton:hover {{ background: {COLOR_DANGER}; }}
    """)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def _styled_combo():
    combo = QComboBox()
    combo.setStyleSheet(f"""
        QComboBox {{ padding: 0 12px; height: 36px;
            border: 1px solid {COLOR_BORDER}; background: {COLOR_INPUT};
            color: {COLOR_TEXT}; font-size: 13px; }}
        QComboBox:focus {{ border-color: {COLOR_ACCENT}; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{ background: {COLOR_SURFACE};
            color: {COLOR_TEXT}; border: 1px solid {COLOR_BORDER};
            selection-background-color: {COLOR_SIDEBAR_ACTIVE}; }}
    """)
    return combo


def _table_style():
    return f"""
        QTableWidget {{
            background: transparent; color: {COLOR_TEXT};
            border: 1px solid {COLOR_BORDER}; font-size: 13px; outline: none;
        }}
        QTableWidget::item {{
            padding: 4px 12px; border-bottom: 1px solid {COLOR_BORDER};
        }}
        QTableWidget::item:selected {{
            background: {COLOR_SIDEBAR_ACTIVE}; color: {COLOR_TEXT};
        }}
        QHeaderView::section {{
            background: {COLOR_SURFACE}; color: {COLOR_TEXT_MUTED};
            padding: 4px 12px; border: none;
            border-bottom: 1px solid {COLOR_BORDER};
            border-right: 1px solid {COLOR_BORDER};
            font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
        }}
        QHeaderView::section:last {{ border-right: none; }}
    """


def _make_table(cols, labels):
    t = QTableWidget()
    t.setColumnCount(cols)
    t.setHorizontalHeaderLabels(labels)
    t.setAlternatingRowColors(False)
    t.setShowGrid(False)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setSelectionMode(QTableWidget.SingleSelection)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(34)
    t.horizontalHeader().setStretchLastSection(True)
    t.horizontalHeader().setFixedHeight(32)
    t.setStyleSheet(_table_style())
    return t


# ─── Settings View ───

class SettingsView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(16)

        h = QLabel("Configuracion")
        h.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLOR_TEXT};")
        outer.addWidget(h)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {COLOR_BG};
                border: 1px solid {COLOR_BORDER};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {COLOR_PANEL};
                color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                border-bottom: none;
                padding: 8px 20px;
                font-size: 12px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background: {COLOR_BG};
                color: {COLOR_TEXT};
                border-bottom: 1px solid {COLOR_BG};
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLOR_HOVER};
            }}
        """)

        # ── Años Escolares ──
        sy_page = QWidget()
        sy_page.setStyleSheet(f"background: {COLOR_BG};")
        sy_layout = QVBoxLayout(sy_page)
        sy_layout.setContentsMargins(16, 16, 16, 16)
        sy_layout.setSpacing(8)
        self._build_school_years(sy_layout)
        tabs.addTab(sy_page, "Anos Escolares")

        # ── Usuarios ──
        u_page = QWidget()
        u_page.setStyleSheet(f"background: {COLOR_BG};")
        u_layout = QVBoxLayout(u_page)
        u_layout.setContentsMargins(16, 16, 16, 16)
        u_layout.setSpacing(8)
        self._build_users(u_layout)
        tabs.addTab(u_page, "Usuarios")

        # ── Roles ──
        r_page = QWidget()
        r_page.setStyleSheet(f"background: {COLOR_BG};")
        r_layout = QVBoxLayout(r_page)
        r_layout.setContentsMargins(16, 16, 16, 16)
        r_layout.setSpacing(8)
        self._build_roles(r_layout)
        tabs.addTab(r_page, "Roles y Permisos")

        # ── Apariencia ──
        a_page = QWidget()
        a_page.setStyleSheet(f"background: {COLOR_BG};")
        a_layout = QVBoxLayout(a_page)
        a_layout.setContentsMargins(16, 16, 16, 16)
        a_layout.setSpacing(8)
        self._build_appearance(a_layout)
        tabs.addTab(a_page, "Apariencia")

        # ── General ──
        g_page = QWidget()
        g_page.setStyleSheet(f"background: {COLOR_BG};")
        g_layout = QVBoxLayout(g_page)
        g_layout.setContentsMargins(16, 16, 16, 16)
        g_layout.setSpacing(8)
        self._build_general(g_layout)
        tabs.addTab(g_page, "General")

        outer.addWidget(tabs)

    # ── School Years ──

    def _build_school_years(self, layout):
        bar = QHBoxLayout()
        bar.setSpacing(8)
        new_btn = _accent_btn("Nuevo Ano")
        new_btn.clicked.connect(self._add_school_year)
        bar.addWidget(new_btn)
        reload_btn = _ghost_btn("Recargar")
        reload_btn.clicked.connect(self._load_school_years)
        bar.addWidget(reload_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self.sy_table = _make_table(3, ["Ano", "Monto", "Activo"])
        self.sy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.sy_table)

    def _load_school_years(self):
        years = get_all_school_years()
        self.sy_table.setRowCount(len(years))
        for i, y in enumerate(years):
            self.sy_table.setItem(i, 0, QTableWidgetItem(y["label"]))
            item_monto = QTableWidgetItem(f"XAF {y['default_amount']:,.0f}")
            item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.sy_table.setItem(i, 1, item_monto)
            self.sy_table.setItem(i, 2, QTableWidgetItem("Si" if y["active"] else ""))
            for col in range(3):
                it = self.sy_table.item(i, col)
                if it:
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)

    def _add_school_year(self):
        dlg = SchoolYearEditDialog()
        if dlg.exec():
            self._load_school_years()

    # ── Users ──

    def _build_users(self, layout):
        bar = QHBoxLayout()
        bar.setSpacing(8)
        add_btn = _accent_btn("Nuevo Usuario")
        add_btn.clicked.connect(self._add_user)
        bar.addWidget(add_btn)
        edit_btn = _ghost_btn("Editar")
        edit_btn.clicked.connect(self._edit_user)
        bar.addWidget(edit_btn)
        del_btn = _danger_btn("Eliminar")
        del_btn.clicked.connect(self._delete_user)
        bar.addWidget(del_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self.users_table = _make_table(4, ["Usuario", "Rol", "Docente", "Activo"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.users_table)

    def _load_users(self):
        users = get_all_users()
        self.users_table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(u["username"]))
            self.users_table.setItem(i, 1, QTableWidgetItem(u["role_name"]))
            teacher = ""
            if u.get("teacher_name"):
                teacher = f"{u['teacher_last_name']}, {u['teacher_name']}"
            self.users_table.setItem(i, 2, QTableWidgetItem(teacher))
            self.users_table.setItem(i, 3, QTableWidgetItem("Si" if u["is_active"] else "No"))
            for col in range(4):
                it = self.users_table.item(i, col)
                if it:
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)

    def _add_user(self):
        dlg = UserEditDialog()
        if dlg.exec():
            self._load_users()

    def _edit_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            return
        users = get_all_users()
        if row >= len(users):
            return
        dlg = UserEditDialog(users[row])
        if dlg.exec():
            self._load_users()

    def _delete_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            return
        users = get_all_users()
        if row >= len(users):
            return
        delete_user(users[row]["id"])
        self._load_users()

    # ── Roles ──

    def _build_roles(self, layout):
        bar = QHBoxLayout()
        bar.setSpacing(8)
        add_btn = _accent_btn("Nuevo Rol")
        add_btn.clicked.connect(self._add_role)
        bar.addWidget(add_btn)
        edit_btn = _ghost_btn("Editar Permisos")
        edit_btn.clicked.connect(self._edit_role)
        bar.addWidget(edit_btn)
        del_btn = _danger_btn("Eliminar")
        del_btn.clicked.connect(self._delete_role)
        bar.addWidget(del_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self.roles_table = _make_table(3, ["Rol", "Descripcion", "Sistema"])
        self.roles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.roles_table)

    def _load_roles(self):
        roles = get_all_roles()
        self.roles_table.setRowCount(len(roles))
        for i, r in enumerate(roles):
            self.roles_table.setItem(i, 0, QTableWidgetItem(r["name"]))
            self.roles_table.setItem(i, 1, QTableWidgetItem(r.get("description", "")))
            self.roles_table.setItem(i, 2, QTableWidgetItem("Si" if r["is_system"] else ""))
            for col in range(3):
                it = self.roles_table.item(i, col)
                if it:
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)

    def _add_role(self):
        dlg = RoleEditDialog()
        if dlg.exec():
            self._load_roles()

    def _edit_role(self):
        row = self.roles_table.currentRow()
        if row < 0:
            return
        roles = get_all_roles()
        if row >= len(roles):
            return
        dlg = RoleEditDialog(roles[row])
        if dlg.exec():
            self._load_roles()

    def _delete_role(self):
        row = self.roles_table.currentRow()
        if row < 0:
            return
        roles = get_all_roles()
        if row >= len(roles):
            return
        role = roles[row]
        if role["is_system"]:
            QMessageBox.warning(self, "Rol del sistema",
                                "No se puede eliminar un rol del sistema.")
            return
        delete_role(role["id"])
        self._load_roles()

    # ── General ──

    def _build_general(self, layout):
        info_table = QTableWidget()
        info_table.setColumnCount(2)
        info_table.setHorizontalHeaderLabels(["Propiedad", "Valor"])
        info_table.setAlternatingRowColors(False)
        info_table.setShowGrid(False)
        info_table.setSelectionMode(QTableWidget.NoSelection)
        info_table.verticalHeader().setVisible(False)
        info_table.verticalHeader().setDefaultSectionSize(32)
        info_table.horizontalHeader().setStretchLastSection(True)
        info_table.horizontalHeader().setFixedHeight(32)
        info_table.setStyleSheet(_table_style())

        info_data = [
            ("Version", APP_VERSION),
            ("Base de datos", get_db_path()),
        ]

        info_table.setRowCount(len(info_data))
        for i, (prop, val) in enumerate(info_data):
            p_item = QTableWidgetItem(prop)
            p_item.setFlags(p_item.flags() & ~Qt.ItemIsEditable)
            v_item = QTableWidgetItem(val)
            v_item.setFlags(v_item.flags() & ~Qt.ItemIsEditable)
            info_table.setItem(i, 0, p_item)
            info_table.setItem(i, 1, v_item)

        layout.addWidget(info_table)

    # ── Apariencia ──

    def _build_appearance(self, layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        gl = QGridLayout(container)
        gl.setSpacing(10)
        gl.setContentsMargins(8, 8, 8, 8)

        self._color_inputs = {}
        color_fields = [
            ("institution_name", "Nombre de la institucion", False),
            ("main_bg", "Fondo principal", True),
            ("surface_color", "Fondo de superficie", True),
            ("panel_color", "Fondo de panel", True),
            ("input_color", "Fondo de inputs", True),
            ("sidebar_bg", "Sidebar fondo", True),
            ("sidebar_hover", "Sidebar hover", True),
            ("sidebar_active", "Sidebar activo", True),
            ("accent_color", "Color de acento", True),
            ("accent_hover_color", "Acento hover", True),
            ("border_color", "Color de bordes", True),
            ("hover_color", "Color hover", True),
            ("text_color", "Texto principal", True),
            ("text_muted", "Texto secundario", True),
            ("text_dim", "Texto terciario", True),
            ("success_color", "Color exito", True),
            ("warning_color", "Color advertencia", True),
            ("danger_color", "Color peligro", True),
        ]

        current = sset.get_all()

        row = 0
        for key, label, is_color in color_fields:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
            gl.addWidget(lbl, row, 0, 1, 1)

            inp = QLineEdit(str(current.get(key, "")))
            inp.setStyleSheet(f"""
                QLineEdit {{ padding: 0 10px; height: 32px;
                    border: 1px solid {COLOR_BORDER}; background: {COLOR_INPUT};
                    color: {COLOR_TEXT}; font-size: 12px; }}
                QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}
            """)
            gl.addWidget(inp, row, 1, 1, 1)

            self._color_inputs[key] = inp

            if is_color:
                preview = QFrame()
                preview.setFixedSize(28, 28)
                preview.setStyleSheet(f"""
                    background: {current.get(key, '#000000')};
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 0px;
                """)
                gl.addWidget(preview, row, 2, 1, 1)

                pick_btn = QPushButton("...")
                pick_btn.setFixedSize(28, 28)
                pick_btn.setStyleSheet(f"""
                    QPushButton {{ border: 1px solid {COLOR_BORDER};
                        background: transparent; color: {COLOR_TEXT_MUTED};
                        font-size: 11px; }}
                    QPushButton:hover {{ background: {COLOR_HOVER}; }}
                """)
                pick_btn.clicked.connect(
                    lambda checked, k=key, p=preview, i=inp: self._pick_color(k, p, i)
                )
                gl.addWidget(pick_btn, row, 3, 1, 1)

            row += 1

        spacer_lbl = QLabel("")
        gl.addWidget(spacer_lbl, row, 0, 1, 4)
        row += 1

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        reset_btn = QPushButton("Restablecer valores")
        reset_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px;
                border: 1px solid {COLOR_BORDER};
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 12px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; color: {COLOR_DANGER}; }}
        """)
        reset_btn.clicked.connect(self._reset_appearance)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        apply_btn = QPushButton("Aplicar cambios")
        apply_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 12px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        apply_btn.clicked.connect(self._apply_appearance)
        btn_layout.addWidget(apply_btn)

        gl.addLayout(btn_layout, row, 0, 1, 4)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _pick_color(self, key, preview, input_field):
        current_color = input_field.text().strip()
        initial = QColor(current_color) if current_color and QColor.isValidColor(current_color) else QColor("#4a6cf7")
        color = QColorDialog.getColor(initial, self, f"Seleccionar color para {key}")
        if color.isValid():
            hex_color = color.name()
            input_field.setText(hex_color)
            preview.setStyleSheet(f"background: {hex_color}; border: 1px solid {COLOR_BORDER}; border-radius: 0px;")

    def _apply_appearance(self):
        updates = {}
        for key, inp in self._color_inputs.items():
            val = inp.text().strip()
            if val:
                updates[key] = val
        sset.set_many(updates)
        QMessageBox.information(self, "Apariencia",
            "Cambios guardados. Reinicia la aplicacion para ver los cambios completamente.")

    def _reset_appearance(self):
        resp = QMessageBox.question(self, "Restablecer",
            "Restablecer todos los valores de apariencia a los valores por defecto?",
            QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            sset.reset()
            self._reload_appearance()

    def _reload_appearance(self):
        current = sset.get_all()
        for key, inp in self._color_inputs.items():
            inp.setText(str(current.get(key, "")))

    # ── Refresh ──

    def refresh(self):
        self._load_school_years()
        self._load_users()
        self._load_roles()
        self._reload_appearance()
