"""
EduSuite — db/database.py
SQLite puro con clase Database + wrappers module-level.
10 tablas: students, teachers, subjects, grades, school_years, enrollment,
           workbooks, roles, role_permissions, users.
Columnas de students en español (nombre, sexo, edad, ...).
Migración automática desde schema anterior (full_name, sex, age, ...).
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import SUBJECTS_BY_LEVEL, COURSE_TO_LEVEL

_DB_DIR = Path(__file__).parent.parent
_DB_PATH = _DB_DIR / "school.db"

CURSOS_VALIDOS = [
    "1º ESBA A", "1º ESBA B", "1º ESBA C",
    "2º ESBA A", "2º ESBA B", "2º ESBA C",
    "3º ESBA A", "3º ESBA B",
    "4º ESBA",
    "1º BACH A", "1º BACH B",
    "2º BACH A", "2º BACH B",
]

VIEW_PERMISSIONS = {
    "inicio": "Inicio",
    "dashboard": "Panel de control",
    "grades": "Notas",
    "students": "Estudiantes",
    "teachers": "Profesores",
    "subjects": "Asignaturas",
    "enrollment": "Matrícula",
    "expenses": "Gastos",
    "editor": "Editor",
    "meta_editor": "Meta Editor",
    "backup": "Respaldo",
    "settings": "Configuracion"
}

DEFAULT_ROLE_PERMISSIONS = {
    "administrador": list(VIEW_PERMISSIONS.keys()),
    "jefe_estudios": ["dashboard", "grades", "students", "teachers", "subjects", "enrollment", "expenses"],
    "profesor": ["dashboard", "grades"],
    "secretaria": ["dashboard", "students", "enrollment", "expenses", "backup"],
}

_STUDENT_COL_MAP = {
    "full_name": "nombre", "sex": "sexo", "age": "edad",
    "phone": "telefono", "address": "domicilio",
    "course": "curso", "shift": "turno",
    "transfer": "traslado", "pending_subject": "asig_pendiente",
    "payment": "pago", "pass_level": "paso_nivel",
    "pending_payment": "pago_pendiente",
}


class Database:

    def __init__(self, db_path=None):
        self.path = Path(db_path) if db_path else _DB_PATH

    # ── Conexión ──────────────────────────────────────────────────────

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Inicialización + migración ────────────────────────────────────

    def initialize(self):
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='students'"
            ).fetchone()
            if existing:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(students)").fetchall()]
                if "full_name" in cols:
                    self._migrate_students(conn)
                else:
                    self._create_all_tables(conn)
            else:
                self._create_all_tables(conn)
        self._seed_subjects()
        self._seed_roles()
        self._seed_admin()
        self._seed_document_categories()
        self._seed_sections()
        self._migrate_documents()

    def _migrate_students(self, conn):
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript("""
            ALTER TABLE students RENAME TO students_old;

            CREATE TABLE students (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                code             TEXT UNIQUE NOT NULL,
                nombre           TEXT NOT NULL,
                sexo             TEXT,
                edad             INTEGER,
                tutor            TEXT,
                telefono         TEXT,
                domicilio        TEXT,
                curso            TEXT,
                turno            TEXT,
                traslado         TEXT DEFAULT 'NO',
                asig_pendiente   TEXT DEFAULT 'NO',
                pago             TEXT,
                paso_nivel       TEXT DEFAULT 'NO',
                pago_pendiente   TEXT DEFAULT 'NO',
                active           INTEGER DEFAULT 1,
                updated_at       TEXT DEFAULT (datetime('now'))
            );

            INSERT INTO students (
                id, code, nombre, sexo, edad, tutor, telefono, domicilio,
                curso, turno, traslado, asig_pendiente, pago, paso_nivel,
                pago_pendiente, active, updated_at
            ) SELECT
                id, code, full_name, sex, age, tutor, phone, address,
                course, shift, transfer, pending_subject, payment, pass_level,
                pending_payment, active, updated_at
            FROM students_old;

            DROP TABLE students_old;
        """)
        self._create_other_tables(conn)
        conn.execute("PRAGMA foreign_keys=ON")

    def _create_all_tables(self, conn):
        self._create_students_table(conn)
        self._create_other_tables(conn)

    def _create_students_table(self, conn):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                code             TEXT UNIQUE NOT NULL,
                nombre           TEXT NOT NULL,
                sexo             TEXT,
                edad             INTEGER,
                tutor            TEXT,
                telefono         TEXT,
                domicilio        TEXT,
                curso            TEXT,
                turno            TEXT,
                traslado         TEXT DEFAULT 'NO',
                asig_pendiente   TEXT DEFAULT 'NO',
                pago             TEXT,
                paso_nivel       TEXT DEFAULT 'NO',
                pago_pendiente   TEXT DEFAULT 'NO',
                active           INTEGER DEFAULT 1,
                updated_at       TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_students_code ON students(code);
            CREATE INDEX IF NOT EXISTS idx_students_curso ON students(curso);
        """)

    def _create_other_tables(self, conn):
        # Execute a series of CREATE TABLE statements without nested triple quotes.
        sql = '''
            CREATE TABLE IF NOT EXISTS teachers (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                code         TEXT UNIQUE NOT NULL,
                name         TEXT NOT NULL,
                last_name    TEXT NOT NULL,
                specialty    TEXT,
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS subjects (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                grade_level  TEXT,
                teacher_id   INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS grades (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id   INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                subject_id   INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                period       TEXT NOT NULL,
                score        REAL,
                obs          TEXT,
                updated_at   TEXT DEFAULT (datetime('now')),
                UNIQUE(student_id, subject_id, period)
            );

            CREATE TABLE IF NOT EXISTS school_years (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                label           TEXT UNIQUE NOT NULL,
                default_amount  REAL NOT NULL DEFAULT 0,
                active          INTEGER DEFAULT 0,
                updated_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS enrollment (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                school_year_id INTEGER NOT NULL REFERENCES school_years(id),
                total_amount   REAL    NOT NULL DEFAULT 0,
                paid_amount    REAL    NOT NULL DEFAULT 0,
                payment_date   TEXT,
                status         TEXT    NOT NULL DEFAULT 'pendiente' CHECK(status IN ('pagado','pendiente','parcial')),
                notes          TEXT,
                updated_at     TEXT    DEFAULT (datetime('now')),
                UNIQUE(student_id, school_year_id)
            );

            CREATE TABLE IF NOT EXISTS workbooks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL DEFAULT 'Editor',
                grid_key     TEXT UNIQUE NOT NULL,
                type         TEXT NOT NULL DEFAULT 'custom' CHECK(type IN ('grades','enrollment','custom')),
                subject_id   INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
                school_year_id INTEGER REFERENCES school_years(id) ON DELETE SET NULL,
                sheet_data   TEXT DEFAULT '[]',
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS roles (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT UNIQUE NOT NULL,
                description  TEXT DEFAULT '',
                is_system    INTEGER DEFAULT 0,
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS role_permissions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id  INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                view_key TEXT NOT NULL,
                UNIQUE(role_id, view_key)
            );

            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id   INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
                username     TEXT UNIQUE NOT NULL,
                password     TEXT NOT NULL DEFAULT '1234',
                role_id      INTEGER NOT NULL REFERENCES roles(id),
                is_active    INTEGER DEFAULT 1,
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            -- Triggers for timestamps
            CREATE TRIGGER IF NOT EXISTS trg_students_updated AFTER UPDATE ON students FOR EACH ROW BEGIN UPDATE students SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_teachers_updated AFTER UPDATE ON teachers FOR EACH ROW BEGIN UPDATE teachers SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_subjects_updated AFTER UPDATE ON subjects FOR EACH ROW BEGIN UPDATE subjects SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_grades_updated AFTER UPDATE ON grades FOR EACH ROW BEGIN UPDATE grades SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_school_years_updated AFTER UPDATE ON school_years FOR EACH ROW BEGIN UPDATE school_years SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_enrollment_updated AFTER UPDATE ON enrollment FOR EACH ROW BEGIN UPDATE enrollment SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_workbooks_updated AFTER UPDATE ON workbooks FOR EACH ROW BEGIN UPDATE workbooks SET updated_at = datetime('now') WHERE id = OLD.id; END;

            CREATE TABLE IF NOT EXISTS expenses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                concept      TEXT NOT NULL,
                amount       REAL NOT NULL,
                date         TEXT NOT NULL,
                notes        TEXT,
                categoria    TEXT,
                metodo       TEXT,
                responsable  TEXT,
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TRIGGER IF NOT EXISTS trg_expenses_updated AFTER UPDATE ON expenses FOR EACH ROW BEGIN UPDATE expenses SET updated_at = datetime('now') WHERE id = OLD.id; END;

            -- MetaEditor tables
            CREATE TABLE IF NOT EXISTS components (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL UNIQUE,
                type         TEXT NOT NULL,
                active       INTEGER NOT NULL DEFAULT 1,
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS component_defs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
                json_blob    TEXT NOT NULL,
                version      INTEGER NOT NULL DEFAULT 1,
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS component_perms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
                role_id     INTEGER NOT NULL REFERENCES roles(id),
                can_view    INTEGER NOT NULL DEFAULT 0,
                can_edit    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS meta_projects (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL UNIQUE,
                description  TEXT,
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS meta_versions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id   INTEGER NOT NULL REFERENCES meta_projects(id) ON DELETE CASCADE,
                version      INTEGER NOT NULL,
                json_config  TEXT NOT NULL,
                state        TEXT NOT NULL CHECK(state IN ('draft','active')) DEFAULT 'draft',
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            -- Custom sections (user-created views)
            CREATE TABLE IF NOT EXISTS custom_sections (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key  TEXT NOT NULL UNIQUE,
                name         TEXT NOT NULL,
                icon         TEXT NOT NULL DEFAULT '\U0001f4c4',
                columns_json TEXT NOT NULL DEFAULT '[]',
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS custom_section_data (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id   INTEGER NOT NULL REFERENCES custom_sections(id) ON DELETE CASCADE,
                row_data     TEXT NOT NULL DEFAULT '{}',
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TRIGGER IF NOT EXISTS trg_custom_sections_updated AFTER UPDATE ON custom_sections FOR EACH ROW BEGIN UPDATE custom_sections SET updated_at = datetime('now') WHERE id = OLD.id; END;
            CREATE TRIGGER IF NOT EXISTS trg_custom_data_updated AFTER UPDATE ON custom_section_data FOR EACH ROW BEGIN UPDATE custom_section_data SET updated_at = datetime('now') WHERE id = OLD.id; END;

            -- Document management tables
            CREATE TABLE IF NOT EXISTS document_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '\U0001f4c4',
                color TEXT DEFAULT '#6b7280',
                sort_order INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER REFERENCES document_categories(id),
                template_id INTEGER REFERENCES documents(id),
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '\U0001f4c4',
                color TEXT DEFAULT '#5e81f4',
                school_year TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                settings_json TEXT DEFAULT '{}',
                is_archived INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES documents(id),
                version INTEGER NOT NULL,
                workbook_json TEXT,
                comment TEXT DEFAULT '',
                created_by TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS document_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES documents(id),
                school_year TEXT DEFAULT '',
                course_id TEXT DEFAULT '',
                teacher_id TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                current_version INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS document_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES documents(id),
                key TEXT NOT NULL,
                value TEXT DEFAULT ''
            );

            CREATE TRIGGER IF NOT EXISTS trg_documents_updated
                AFTER UPDATE ON documents FOR EACH ROW
            BEGIN
                UPDATE documents SET updated_at = datetime('now','localtime') WHERE id = OLD.id;
            END;
'''
        try:
            conn.executescript(sql)
        except Exception:
            pass
        # ── Migration: add new columns if they don't exist ───────────────────────
        try:
            conn.execute("ALTER TABLE expenses ADD COLUMN categoria TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE expenses ADD COLUMN metodo TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE expenses ADD COLUMN responsable TEXT")
        except Exception:
            pass

        # ── Migration: custom_sections table ────────────────────────────
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS custom_sections (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key  TEXT NOT NULL UNIQUE,
                name         TEXT NOT NULL,
                icon         TEXT NOT NULL DEFAULT '📄',
                columns_json TEXT NOT NULL DEFAULT '[]',
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            )""")
        except Exception:
            pass
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS custom_section_data (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id   INTEGER NOT NULL REFERENCES custom_sections(id) ON DELETE CASCADE,
                row_data     TEXT NOT NULL DEFAULT '{}',
                created_at   TEXT DEFAULT (datetime('now')),
                updated_at   TEXT DEFAULT (datetime('now'))
            )""")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE custom_sections ADD COLUMN workbook_json TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE custom_sections ADD COLUMN description TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE custom_sections ADD COLUMN color TEXT DEFAULT '#5e81f4'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE custom_sections ADD COLUMN type TEXT DEFAULT 'spreadsheet'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE custom_sections ADD COLUMN settings_json TEXT DEFAULT '{}'")
        except Exception:
            pass

        # ── Document management tables ─────────────────────────────────────
        for ddl in [
            "CREATE TABLE IF NOT EXISTS document_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, icon TEXT DEFAULT '\U0001f4c4', color TEXT DEFAULT '#6b7280', sort_order INTEGER DEFAULT 0, is_system INTEGER DEFAULT 0)",
            "CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category_id INTEGER REFERENCES document_categories(id), template_id INTEGER REFERENCES documents(id), description TEXT DEFAULT '', icon TEXT DEFAULT '\U0001f4c4', color TEXT DEFAULT '#5e81f4', school_year TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now','localtime')), updated_at TEXT DEFAULT (datetime('now','localtime')), settings_json TEXT DEFAULT '{}', is_archived INTEGER DEFAULT 0)",
            "CREATE TABLE IF NOT EXISTS document_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL REFERENCES documents(id), version INTEGER NOT NULL, workbook_json TEXT, comment TEXT DEFAULT '', created_by TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now','localtime')))",
            "CREATE TABLE IF NOT EXISTS document_instances (id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL REFERENCES documents(id), school_year TEXT DEFAULT '', course_id TEXT DEFAULT '', teacher_id TEXT DEFAULT '', status TEXT DEFAULT 'active', current_version INTEGER DEFAULT 0)",
            "CREATE TABLE IF NOT EXISTS document_metadata (id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL REFERENCES documents(id), key TEXT NOT NULL, value TEXT DEFAULT '')",
        ]:
            try:
                conn.execute(ddl)
            except Exception:
                pass
        try:
            conn.execute("CREATE TRIGGER IF NOT EXISTS trg_documents_updated AFTER UPDATE ON documents FOR EACH ROW BEGIN UPDATE documents SET updated_at = datetime('now','localtime') WHERE id = OLD.id; END")
        except Exception:
            pass

        # ── Migration: ensure columns exist (safe for existing DBs) ────────
        def _ensure_col(table, col, ddl):
            existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if col not in existing:
                try:
                    conn.execute(ddl)
                except Exception:
                    pass

        _ensure_col("documents", "created_at",
            "ALTER TABLE documents ADD COLUMN created_at TEXT DEFAULT (datetime('now','localtime'))")
        _ensure_col("documents", "updated_at",
            "ALTER TABLE documents ADD COLUMN updated_at TEXT DEFAULT (datetime('now','localtime'))")
        _ensure_col("documents", "settings_json",
            "ALTER TABLE documents ADD COLUMN settings_json TEXT DEFAULT '{}'")
        _ensure_col("documents", "is_archived",
            "ALTER TABLE documents ADD COLUMN is_archived INTEGER DEFAULT 0")
        _ensure_col("document_versions", "created_at",
            "ALTER TABLE document_versions ADD COLUMN created_at TEXT DEFAULT (datetime('now','localtime'))")
        _ensure_col("custom_sections", "created_at",
            "ALTER TABLE custom_sections ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")
        _ensure_col("custom_sections", "updated_at",
            "ALTER TABLE custom_sections ADD COLUMN updated_at TEXT DEFAULT (datetime('now'))")
        _ensure_col("custom_sections", "workbook_json",
            "ALTER TABLE custom_sections ADD COLUMN workbook_json TEXT")
        _ensure_col("custom_sections", "settings_json",
            "ALTER TABLE custom_sections ADD COLUMN settings_json TEXT DEFAULT '{}'")
        _ensure_col("custom_sections", "editable",
            "ALTER TABLE custom_sections ADD COLUMN editable INTEGER DEFAULT 1")
        _ensure_col("custom_sections", "deletable",
            "ALTER TABLE custom_sections ADD COLUMN deletable INTEGER DEFAULT 1")
        _ensure_col("custom_sections", "visible",
            "ALTER TABLE custom_sections ADD COLUMN visible INTEGER DEFAULT 1")
        _ensure_col("custom_sections", "sort_order",
            "ALTER TABLE custom_sections ADD COLUMN sort_order INTEGER DEFAULT 0")
        _ensure_col("custom_sections", "document_id",
            "ALTER TABLE custom_sections ADD COLUMN document_id INTEGER REFERENCES documents(id)")

    def _row(self, row):
        return dict(row) if row else None

    # ── Seed ──────────────────────────────────────────────────────────

    def _seed_subjects(self):
        with self._connect() as conn:
            existing = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
            if existing > 0:
                return
            for level_key, subjects in SUBJECTS_BY_LEVEL.items():
                for name in subjects:
                    conn.execute(
                        "INSERT INTO subjects (name, grade_level) VALUES (?, ?)",
                        (name, level_key),
                    )

    def _seed_roles(self):
        with self._connect() as conn:
            for role_name, perms in DEFAULT_ROLE_PERMISSIONS.items():
                existing = conn.execute(
                    "SELECT id FROM roles WHERE name = ?", (role_name,)
                ).fetchone()
                if existing:
                    role_id = existing["id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO roles (name, description, is_system) VALUES (?, ?, 1)",
                        (role_name, ""),
                    )
                    role_id = cur.lastrowid
                for vk in perms:
                    conn.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, view_key) VALUES (?, ?)",
                        (role_id, vk),
                    )

    def _seed_admin(self):
        with self._connect() as conn:
            admin_role = conn.execute(
                "SELECT id FROM roles WHERE name = 'administrador'"
            ).fetchone()
            if not admin_role:
                return
            existing = conn.execute(
                "SELECT 1 FROM users WHERE username = 'admin'"
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO users (username, password, role_id) VALUES (?, ?, ?)",
                    ("admin", "admin", admin_role["id"]),
                )

    # ── CRUD: Estudiantes ─────────────────────────────────────────────

    def get_all_students(self, active_only=True):
        with self._connect() as conn:
            sql = "SELECT * FROM students"
            if active_only:
                sql += " WHERE active = 1"
            sql += " ORDER BY nombre"
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def get_student(self, student_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            ).fetchone())

    def get_student_by_code(self, code):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM students WHERE code = ?", (code,)
            ).fetchone())

    def get_students_by_course(self, course):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM students WHERE curso = ? AND active = 1 ORDER BY nombre",
                (course,)
            ).fetchall()]

    def get_students_by_subject(self, subject_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                """SELECT DISTINCT s.* FROM students s
                   JOIN grades g ON g.student_id = s.id
                   WHERE g.subject_id = ? AND s.active = 1
                   ORDER BY s.nombre""",
                (subject_id,),
            ).fetchall()]

    def search_students(self, query):
        with self._connect() as conn:
            like = f"%{query}%"
            return [dict(r) for r in conn.execute(
                "SELECT * FROM students WHERE (nombre LIKE ? OR code LIKE ?) AND active = 1 ORDER BY nombre",
                (like, like),
            ).fetchall()]

    def save_student(self, data):
        fields = ["code", "nombre", "sexo", "edad", "tutor", "telefono",
                   "domicilio", "curso", "turno", "traslado", "asig_pendiente",
                   "pago", "paso_nivel", "pago_pendiente"]
        vals = [data.get(f) for f in fields]
        placeholders = ", ".join(["?"] * len(fields))
        cols = ", ".join(fields)
        with self._connect() as conn:
            cur = conn.execute(
                f"INSERT INTO students ({cols}) VALUES ({placeholders})", vals
            )
            return cur.lastrowid

    def update_student(self, student_id, data):
        updatable = ["nombre", "sexo", "edad", "tutor", "telefono",
                     "domicilio", "curso", "turno", "traslado", "asig_pendiente",
                     "pago", "paso_nivel", "pago_pendiente"]
        fields = [f for f in updatable if f in data]
        if not fields:
            return
        set_clause = ", ".join(f"{f} = ?" for f in fields)
        vals = [data[f] for f in fields] + [student_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE students SET {set_clause} WHERE id = ?", vals)

    def deactivate_student(self, student_id):
        with self._connect() as conn:
            conn.execute("UPDATE students SET active = 0 WHERE id = ?", (student_id,))

    def reactivate_student(self, student_id):
        with self._connect() as conn:
            conn.execute("UPDATE students SET active = 1 WHERE id = ?", (student_id,))

    def delete_student(self, student_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))

    def student_code_exists(self, code):
        with self._connect() as conn:
            return conn.execute(
                "SELECT 1 FROM students WHERE code = ?", (code,)
            ).fetchone() is not None

    # ── CRUD: Profesores ──────────────────────────────────────────────

    def save_teacher(self, code, name, last_name, specialty=""):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO teachers (code, name, last_name, specialty) VALUES (?, ?, ?, ?)",
                (code, name, last_name, specialty),
            )
            return cur.lastrowid

    def get_teacher(self, teacher_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM teachers WHERE id = ?", (teacher_id,)
            ).fetchone())

    def get_all_teachers(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM teachers ORDER BY last_name, name"
            ).fetchall()]

    def update_teacher(self, teacher_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [teacher_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE teachers SET {set_clause} WHERE id = ?", vals)

    def delete_teacher(self, teacher_id):
        with self._connect() as conn:
            conn.execute("UPDATE subjects SET teacher_id = NULL WHERE teacher_id = ?", (teacher_id,))
            conn.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))

    def teacher_code_exists(self, code):
        with self._connect() as conn:
            return conn.execute(
                "SELECT 1 FROM teachers WHERE code = ?", (code,)
            ).fetchone() is not None

    # ── CRUD: Asignaturas ─────────────────────────────────────────────

    def save_subject(self, name, grade_level="", teacher_id=None):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO subjects (name, grade_level, teacher_id) VALUES (?, ?, ?)",
                (name, grade_level, teacher_id),
            )
            return cur.lastrowid

    def get_subject(self, subject_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM subjects WHERE id = ?", (subject_id,)
            ).fetchone())

    def get_all_subjects(self, grade_level=None):
        with self._connect() as conn:
            if grade_level:
                rows = conn.execute(
                    "SELECT * FROM subjects WHERE grade_level = ? ORDER BY name",
                    (grade_level,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM subjects ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def get_subjects_by_level(self, grade_level):
        return self.get_all_subjects(grade_level)

    def get_subjects_for_course(self, course):
        level_key = COURSE_TO_LEVEL.get(course)
        if not level_key:
            return []
        return self.get_all_subjects(grade_level=level_key)

    def get_subjects_by_group(self, group_key):
        return self.get_all_subjects(grade_level=group_key)

    def update_subject(self, subject_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [subject_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE subjects SET {set_clause} WHERE id = ?", vals)

    def delete_subject(self, subject_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    # ── CRUD: Notas ───────────────────────────────────────────────────

    def upsert_grade(self, student_id, subject_id, period, score, obs=""):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO grades (student_id, subject_id, period, score, obs)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(student_id, subject_id, period)
                   DO UPDATE SET score = excluded.score, obs = excluded.obs,
                                 updated_at = datetime('now')""",
                (student_id, subject_id, period, score, obs),
            )

    def get_grade(self, student_id, subject_id, period):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM grades WHERE student_id = ? AND subject_id = ? AND period = ?",
                (student_id, subject_id, period),
            ).fetchone())

    def get_grades_by_student(self, student_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM grades WHERE student_id = ? ORDER BY subject_id, period",
                (student_id,),
            ).fetchall()]

    def delete_grade(self, grade_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM grades WHERE id = ?", (grade_id,))

    def get_report_by_course(self, course):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                """SELECT s.nombre AS student_name, s.code,
                          sub.name AS subject_name, g.period, g.score, g.obs
                   FROM students s
                   JOIN grades g ON g.student_id = s.id
                   JOIN subjects sub ON sub.id = g.subject_id
                   WHERE s.curso = ?
                   ORDER BY s.nombre, sub.name, g.period""",
                (course,),
            ).fetchall()]

    def get_report_by_student(self, student_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                """SELECT sub.name AS subject_name, sub.grade_level,
                          g.period, g.score, g.obs
                   FROM grades g
                   JOIN subjects sub ON sub.id = g.subject_id
                   WHERE g.student_id = ?
                   ORDER BY sub.name, g.period""",
                (student_id,),
            ).fetchall()]

    def get_summary_by_trimester(self, trimester):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                """SELECT s.curso,
                          sub.name AS subject_name,
                          sub.grade_level AS level_group,
                          COUNT(g.id) AS total,
                          SUM(CASE WHEN g.score >= 5 THEN 1 ELSE 0 END) AS aprobados,
                          SUM(CASE WHEN g.score < 5 THEN 1 ELSE 0 END) AS suspensos,
                          ROUND(AVG(g.score), 2) AS promedio
                   FROM grades g
                   JOIN students s ON s.id = g.student_id
                   JOIN subjects sub ON sub.id = g.subject_id
                   WHERE g.period = ? AND s.active = 1
                   GROUP BY s.curso, sub.name
                   ORDER BY s.curso, sub.name""",
                (trimester,),
            ).fetchall()]

    
    # ── CRUD: MetaEditor Components ───────────────────────────────────────
    def create_component(self, name, comp_type, active=1):
        """Create a new component definition container."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO components (name, type, active) VALUES (?, ?, ?)",
                (name, comp_type, active),
            )
            return cur.lastrowid

    def get_component(self, component_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM components WHERE id = ?", (component_id,)
            ).fetchone())

    def get_all_components(self, active_only=True):
        with self._connect() as conn:
            sql = "SELECT * FROM components"
            if active_only:
                sql += " WHERE active = 1"
            sql += " ORDER BY name"
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def update_component(self, component_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [component_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE components SET {set_clause} WHERE id = ?", vals)

    def delete_component(self, component_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM components WHERE id = ?", (component_id,))

    # Component definitions (JSON blobs)
    def save_component_def(self, component_id, json_blob, version=None):
        """Insert a new definition version or update existing one."""
        with self._connect() as conn:
            if version is None:
                # Insert as new version = max+1
                cur = conn.execute(
                    "INSERT INTO component_defs (component_id, json_blob) VALUES (?, ?)",
                    (component_id, json_blob),
                )
                return cur.lastrowid
            else:
                conn.execute(
                    "INSERT INTO component_defs (component_id, json_blob, version) VALUES (?, ?, ?)",
                    (component_id, json_blob, version),
                )
                return conn.lastrowid

    def get_latest_component_def(self, component_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM component_defs WHERE component_id = ? ORDER BY version DESC LIMIT 1",
                (component_id,)
            ).fetchone()
            return self._row(row)

    def get_all_component_defs(self, component_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM component_defs WHERE component_id = ? ORDER BY version ASC",
                (component_id,)
            ).fetchall()
            return [self._row(r) for r in rows]

    # Permissions for components
    def set_component_permission(self, component_id, role_id, can_view=0, can_edit=0):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO component_perms (component_id, role_id, can_view, can_edit) VALUES (?, ?, ?, ?)",
                (component_id, role_id, can_view, can_edit),
            )

    def get_component_permissions(self, component_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT cp.*, r.name AS role_name FROM component_perms cp JOIN roles r ON r.id = cp.role_id WHERE cp.component_id = ?",
                (component_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── End of MetaEditor CRUD ─────────────────────────────────────────────

    # Existing functions continue below ...


    def create_school_year(self, label, default_amount=0):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO school_years (label, default_amount) VALUES (?, ?)",
                (label, default_amount),
            )
            return cur.lastrowid

    def get_school_year(self, year_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM school_years WHERE id = ?", (year_id,)
            ).fetchone())

    def get_all_school_years(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM school_years ORDER BY label DESC"
            ).fetchall()]

    def get_active_school_year(self):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM school_years WHERE active = 1"
            ).fetchone())

    def set_active_school_year(self, year_id):
        with self._connect() as conn:
            conn.execute("UPDATE school_years SET active = 0")
            conn.execute("UPDATE school_years SET active = 1 WHERE id = ?", (year_id,))

    def update_school_year(self, year_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [year_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE school_years SET {set_clause} WHERE id = ?", vals)

    # ── CRUD: Matrícula / Pagos ───────────────────────────────────────

    def _calc_enrollment_status(self, paid, total):
        if total <= 0:
            return "pendiente"
        if paid <= 0:
            return "pendiente"
        if paid >= total:
            return "pagado"
        return "parcial"

    def upsert_enrollment(self, student_id, school_year_id, total_amount,
                          paid_amount=0, payment_date="", notes=""):
        status = self._calc_enrollment_status(paid_amount, total_amount)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO enrollment
                   (student_id, school_year_id, total_amount, paid_amount,
                    payment_date, status, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(student_id, school_year_id)
                   DO UPDATE SET total_amount = excluded.total_amount,
                                 paid_amount = excluded.paid_amount,
                                 payment_date = excluded.payment_date,
                                 status = excluded.status,
                                 notes = excluded.notes,
                                 updated_at = datetime('now')""",
                (student_id, school_year_id, total_amount, paid_amount,
                 payment_date, status, notes),
            )

    def get_enrollment(self, student_id, school_year_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM enrollment WHERE student_id = ? AND school_year_id = ?",
                (student_id, school_year_id),
            ).fetchone())

    def get_enrollments_by_year(self, school_year_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                """SELECT e.*, s.code AS student_code, s.nombre AS student_name,
                          s.curso AS grade_level
                   FROM enrollment e
                   JOIN students s ON s.id = e.student_id
                   WHERE e.school_year_id = ?
                   ORDER BY s.nombre""",
                (school_year_id,),
            ).fetchall()]

    def get_enrollment_stats(self, school_year_id):
        with self._connect() as conn:
            row = conn.execute(
                """SELECT COUNT(*) AS total,
                          SUM(CASE WHEN status = 'pagado' THEN 1 ELSE 0 END) AS pagados,
                          SUM(CASE WHEN status = 'parcial' THEN 1 ELSE 0 END) AS parciales,
                          SUM(CASE WHEN status = 'pendiente' THEN 1 ELSE 0 END) AS pendientes,
                          COALESCE(SUM(total_amount), 0) AS total_esperado,
                          COALESCE(SUM(paid_amount), 0) AS total_cobrado
                   FROM enrollment WHERE school_year_id = ?""",
                (school_year_id,),
            ).fetchone()
            return dict(row)

    def get_debtors(self, school_year_id, only_unpaid=False):
        with self._connect() as conn:
            query = """SELECT e.*, s.code AS student_code, s.nombre AS student_name,
                              s.curso AS grade_level
                       FROM enrollment e
                       JOIN students s ON s.id = e.student_id
                       WHERE e.school_year_id = ?"""
            if only_unpaid:
                query += " AND e.status IN ('pendiente', 'parcial')"
            query += " ORDER BY s.nombre"
            return [dict(r) for r in conn.execute(query, (school_year_id,)).fetchall()]

    def seed_enrollment_for_year(self, school_year_id, default_amount):
        with self._connect() as conn:
            students = conn.execute("SELECT id FROM students WHERE active = 1").fetchall()
            created = 0
            for s in students:
                existing = conn.execute(
                    "SELECT 1 FROM enrollment WHERE student_id = ? AND school_year_id = ?",
                    (s["id"], school_year_id),
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO enrollment
                           (student_id, school_year_id, total_amount, paid_amount, status)
                           VALUES (?, ?, ?, 0, 'pendiente')""",
                        (s["id"], school_year_id, default_amount),
                    )
                    created += 1
            return created

    # ── Import / Sync ─────────────────────────────────────────────────

    def diff_import(self, rows):
        results = []
        with self._connect() as conn:
            for row in rows:
                code = row.get("code", "").strip()
                if not code:
                    results.append({**row, "_status": "error", "_reason": "sin código"})
                    continue
                existing = conn.execute(
                    "SELECT id FROM students WHERE code = ?", (code,)
                ).fetchone()
                if not existing:
                    results.append({**row, "_status": "error", "_reason": "código no encontrado"})
                    continue
                existing_grade = conn.execute(
                    "SELECT score, updated_at FROM grades WHERE student_id = ? AND subject_id = ? AND period = ?",
                    (existing["id"], row.get("subject_id"), row.get("period")),
                ).fetchone()
                if existing_grade is None:
                    results.append({**row, "_status": "new"})
                elif existing_grade["score"] == row.get("score"):
                    results.append({**row, "_status": "same"})
                else:
                    results.append({**row, "_status": "conflict", "_db_score": existing_grade["score"]})
        return results

    def apply_import(self, rows):
        with self._connect() as conn:
            for row in rows:
                if row.get("_status") == "same":
                    continue
                student = conn.execute(
                    "SELECT id FROM students WHERE code = ?", (row.get("code"),)
                ).fetchone()
                if not student:
                    continue
                conn.execute(
                    """INSERT INTO grades (student_id, subject_id, period, score, obs)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(student_id, subject_id, period)
                       DO UPDATE SET score = excluded.score, obs = excluded.obs,
                                     updated_at = datetime('now')""",
                    (student["id"], row["subject_id"], row["period"],
                     row["score"], row.get("obs", "")),
                )

    def diff_import_students(self, rows):
        _fields = ["nombre", "sexo", "edad", "tutor", "telefono",
                    "domicilio", "curso", "turno", "traslado", "asig_pendiente",
                    "pago", "paso_nivel", "pago_pendiente"]
        result = []
        with self._connect() as conn:
            for row in rows:
                code = row.get("code", "").strip()
                if not code:
                    result.append({**row, "status": "error", "detail": "sin código"})
                    continue
                existing = conn.execute(
                    "SELECT * FROM students WHERE code = ?", (code,)
                ).fetchone()
                if existing is None:
                    result.append({**row, "status": "new"})
                else:
                    diffs = {}
                    for f in _fields:
                        old = str(existing[f] or "").strip()
                        new = str(row.get(f) or "").strip()
                        if old != new:
                            diffs[f] = {"old": old, "new": new}
                    if diffs:
                        result.append({**row, "status": "conflict", "diffs": diffs})
                    else:
                        result.append({**row, "status": "same"})
        return result

    def apply_import_students(self, rows, accept_conflicts=False):
        _fields = ["code", "nombre", "sexo", "edad", "tutor", "telefono",
                    "domicilio", "curso", "turno", "traslado", "asig_pendiente",
                    "pago", "paso_nivel", "pago_pendiente"]
        placeholders = ", ".join(["?"] * len(_fields))
        cols = ", ".join(_fields)
        stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        with self._connect() as conn:
            for row in rows:
                status = row.get("status")
                if status == "new":
                    vals = [row.get(f) for f in _fields]
                    conn.execute(
                        f"INSERT OR IGNORE INTO students ({cols}) VALUES ({placeholders})", vals
                    )
                    stats["inserted"] += 1
                elif status == "conflict" and accept_conflicts:
                    updatable = _fields[1:]
                    set_clause = ", ".join(f"{f} = ?" for f in updatable)
                    vals = [row.get(f) for f in updatable] + [row["code"]]
                    conn.execute(
                        f"UPDATE students SET {set_clause} WHERE code = ?", vals
                    )
                    stats["updated"] += 1
                elif status in ("same", "conflict"):
                    stats["skipped"] += 1
                else:
                    stats["errors"] += 1
        return stats

    # ── Workbooks (Editor) ────────────────────────────────────────────

    def save_workbook(self, name, grid_key, type_="custom", subject_id=None,
                      school_year_id=None, sheet_data="[]"):
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO workbooks (name, grid_key, type, subject_id,
                   school_year_id, sheet_data) VALUES (?, ?, ?, ?, ?, ?)""",
                (name, grid_key, type_, subject_id, school_year_id, sheet_data),
            )
            return cur.lastrowid

    def get_workbook(self, workbook_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM workbooks WHERE id = ?", (workbook_id,)
            ).fetchone())

    def get_all_workbooks(self, type_=None):
        with self._connect() as conn:
            query = "SELECT * FROM workbooks"
            params = []
            if type_:
                query += " WHERE type = ?"
                params.append(type_)
            query += " ORDER BY updated_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def update_workbook(self, workbook_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [workbook_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE workbooks SET {set_clause} WHERE id = ?", vals)

    def delete_workbook(self, workbook_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM workbooks WHERE id = ?", (workbook_id,))

    # ── Utilidades ────────────────────────────────────────────────────

    def get_stats(self):
        with self._connect() as conn:
            students = conn.execute(
                "SELECT COUNT(*) FROM students WHERE active = 1"
            ).fetchone()[0]
            teachers = conn.execute(
                "SELECT COUNT(*) FROM teachers"
            ).fetchone()[0]
            subjects = conn.execute(
                "SELECT COUNT(*) FROM subjects"
            ).fetchone()[0]
            grades = conn.execute(
                "SELECT COUNT(*) FROM grades"
            ).fetchone()[0]
            enrollments = conn.execute(
                "SELECT COUNT(*) FROM enrollment"
            ).fetchone()[0]
            manana = conn.execute(
                "SELECT COUNT(*) FROM students WHERE active=1 AND turno='MAÑANA'"
            ).fetchone()[0]
            tarde = conn.execute(
                "SELECT COUNT(*) FROM students WHERE active=1 AND turno='TARDE'"
            ).fetchone()[0]
            traslados = conn.execute(
                "SELECT COUNT(*) FROM students WHERE active=1 AND traslado IN ('SÍ','SI')"
            ).fetchone()[0]
            repiten = conn.execute(
                "SELECT COUNT(*) FROM students WHERE active=1 AND asig_pendiente='REPITE'"
            ).fetchone()[0]
            asig_pend = conn.execute(
                """SELECT COUNT(*) FROM students WHERE active=1
                   AND asig_pendiente NOT IN ('NO','REPITE')
                   AND asig_pendiente IS NOT NULL AND asig_pendiente != ''"""
            ).fetchone()[0]
            pasan = conn.execute(
                "SELECT COUNT(*) FROM students WHERE active=1 AND paso_nivel IN ('SI','SÍ')"
            ).fetchone()[0]
            con_deuda = conn.execute(
                """SELECT COUNT(*) FROM students WHERE active=1
                   AND pago_pendiente != 'NO' AND pago_pendiente IS NOT NULL
                   AND pago_pendiente != ''"""
            ).fetchone()[0]
        return {
            "students": students, "teachers": teachers,
            "subjects": subjects, "grades": grades, "enrollments": enrollments,
            "manana": manana, "tarde": tarde,
            "traslados": traslados, "repiten": repiten,
            "asig_pendiente": asig_pend, "pasan_nivel": pasan,
            "con_deuda": con_deuda,
        }

    def get_stats_by_curso(self):
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT curso, COUNT(*) as total
                   FROM students WHERE active = 1
                   GROUP BY curso ORDER BY curso"""
            ).fetchall()
            return [dict(r) for r in rows]

    def get_dashboard_extended(self):
        with self._connect() as conn:
            stats = self.get_stats()
            courses = self.get_stats_by_curso()
            distinct = self.get_distinct_courses()

            total_students = stats["students"]
            total_grades = conn.execute("SELECT COUNT(*) FROM grades").fetchone()[0]

            evaluated = conn.execute(
                """SELECT COUNT(DISTINCT student_id) FROM grades"""
            ).fetchone()[0]

            approved = conn.execute(
                """SELECT COUNT(DISTINCT g.student_id) FROM grades g
                   JOIN (SELECT student_id, AVG(score) as avg_score
                         FROM grades GROUP BY student_id) a
                   ON a.student_id = g.student_id
                   WHERE a.avg_score >= 5"""
            ).fetchone()[0]

            failed = total_students - approved if total_students > approved else 0

            pass_rate = round(approved / evaluated * 100, 1) if evaluated else 0

            # Per-course stats
            course_stats = []
            for c in distinct:
                enrolled = conn.execute(
                    "SELECT COUNT(*) FROM students WHERE active=1 AND curso=?", (c,)
                ).fetchone()[0]
                eval_count = conn.execute(
                    "SELECT COUNT(DISTINCT s.id) FROM students s JOIN grades g ON g.student_id=s.id WHERE s.curso=?",
                    (c,),
                ).fetchone()[0]
                aprob = conn.execute(
                    """SELECT COUNT(DISTINCT g.student_id) FROM grades g
                       JOIN students s ON s.id=g.student_id
                       WHERE s.curso=? AND s.active=1
                       GROUP BY g.student_id
                       HAVING AVG(g.score) >= 5""",
                    (c,),
                ).fetchone()[0] or 0
                susp = eval_count - aprob if eval_count > aprob else 0
                course_stats.append({
                    "curso": c, "enrolled": enrolled,
                    "evaluated": eval_count,
                    "approved": aprob, "failed": susp,
                })

            # Per-subject fail stats for alerts
            subject_fails = [dict(r) for r in conn.execute(
                """SELECT sub.name, sub.grade_level,
                          COUNT(g.id) as total,
                          SUM(CASE WHEN g.score < 5 THEN 1 ELSE 0 END) as fails,
                          ROUND(AVG(g.score), 2) as avg_score
                   FROM grades g
                   JOIN subjects sub ON sub.id = g.subject_id
                   GROUP BY sub.id
                   ORDER BY fails DESC"""
            ).fetchall()]

            # Evolution across trimesters
            evolution = {}
            for p in ("T1", "T2", "T3"):
                row = conn.execute(
                    """SELECT COUNT(g.id) as total,
                              SUM(CASE WHEN g.score >= 5 THEN 1 ELSE 0 END) as approved,
                              ROUND(AVG(g.score), 2) as avg_score
                       FROM grades g WHERE g.period=?""",
                    (p,),
                ).fetchone()
                if row and row["total"]:
                    evolution[p] = dict(row)
                else:
                    evolution[p] = {"total": 0, "approved": 0, "avg_score": 0.0}

        return {
            "total_students": total_students,
            "total_grades": total_grades,
            "evaluated": evaluated,
            "approved": approved,
            "failed": failed,
            "pass_rate": pass_rate,
            "courses": course_stats,
            "subject_fails": subject_fails,
            "evolution": evolution,
            "base": stats,
        }

    def get_recent_activity(self, limit=10):
        with self._connect() as conn:
            grades = [dict(r) for r in conn.execute(
                """SELECT 'grade' as type, g.updated_at as ts, s.nombre as student,
                          sub.name as subject, g.period, g.score
                   FROM grades g
                   JOIN students s ON s.id=g.student_id
                   JOIN subjects sub ON sub.id=g.subject_id
                   WHERE g.updated_at IS NOT NULL
                   ORDER BY g.updated_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()]
            if len(grades) < limit:
                enrollments = [dict(r) for r in conn.execute(
                    """SELECT 'enrollment' as type, updated_at as ts, nombre as student, curso
                       FROM students WHERE active=1 AND updated_at IS NOT NULL
                       ORDER BY updated_at DESC LIMIT ?""",
                    (limit - len(grades),),
                ).fetchall()]
                grades.extend(enrollments)
            return grades[:limit]

    def get_distinct_courses(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT curso FROM students WHERE active = 1 AND curso != '' ORDER BY curso"
            ).fetchall()
            return [r["curso"] for r in rows]

    def export_all_to_dict(self):
        with self._connect() as conn:
            return {
                "students": [dict(r) for r in conn.execute("SELECT * FROM students").fetchall()],
                "teachers": [dict(r) for r in conn.execute("SELECT * FROM teachers").fetchall()],
                "subjects": [dict(r) for r in conn.execute("SELECT * FROM subjects").fetchall()],
                "grades": [dict(r) for r in conn.execute("SELECT * FROM grades").fetchall()],
            }

    # ── Roles y Usuarios ──────────────────────────────────────────────

    def authenticate(self, username, password):
        with self._connect() as conn:
            row = conn.execute(
                """SELECT u.id, u.username, u.role_id, r.name AS role_name,
                          u.teacher_id, t.name AS teacher_name,
                          t.last_name AS teacher_last_name
                   FROM users u
                   JOIN roles r ON r.id = u.role_id
                   LEFT JOIN teachers t ON t.id = u.teacher_id
                   WHERE u.username = ? AND u.password = ? AND u.is_active = 1""",
                (username, password),
            ).fetchone()
            return self._row(row)

    def get_role_permissions(self, role_id):
        with self._connect() as conn:
            return [r["view_key"] for r in conn.execute(
                "SELECT view_key FROM role_permissions WHERE role_id = ?", (role_id,)
            ).fetchall()]

    def get_all_roles(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM roles ORDER BY name"
            ).fetchall()]

    def save_role(self, name, description=""):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO roles (name, description) VALUES (?, ?)", (name, description)
            )
            return cur.lastrowid

    def update_role(self, role_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [role_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE roles SET {set_clause} WHERE id = ?", vals)

    def delete_role(self, role_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM roles WHERE id = ? AND is_system = 0", (role_id,))

    def set_role_permissions(self, role_id, view_keys):
        with self._connect() as conn:
            conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
            for vk in view_keys:
                conn.execute(
                    "INSERT INTO role_permissions (role_id, view_key) VALUES (?, ?)", (role_id, vk)
                )

    def get_all_users(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                """SELECT u.*, r.name AS role_name,
                          t.name AS teacher_name, t.last_name AS teacher_last_name
                   FROM users u
                   JOIN roles r ON r.id = u.role_id
                   LEFT JOIN teachers t ON t.id = u.teacher_id
                   ORDER BY u.username"""
            ).fetchall()]

    def save_user(self, username, password, role_id, teacher_id=None):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password, role_id, teacher_id) VALUES (?, ?, ?, ?)",
                (username, password, role_id, teacher_id),
            )
            return cur.lastrowid

    def update_user(self, user_id, **kwargs):
        fields = {k: v for k, v in kwargs.items() if v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [user_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", vals)

    def delete_user(self, user_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def user_exists(self, username):
        with self._connect() as conn:
            return conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone() is not None

    def change_password(self, user_id, new_password):
        with self._connect() as conn:
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))

    # ── CRUD: Gastos ──────────────────────────────────────────────────

    def save_expense(self, concept, amount, date, notes=""):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO expenses (concept, amount, date, notes) VALUES (?, ?, ?, ?)",
                (concept, amount, date, notes),
            )
            return cur.lastrowid

    def update_expense(self, expense_id, concept, amount, date, notes=""):
        with self._connect() as conn:
            conn.execute(
                "UPDATE expenses SET concept = ?, amount = ?, date = ?, notes = ? WHERE id = ?",
                (concept, amount, date, notes, expense_id),
            )

    def delete_expense(self, expense_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

    def get_expense(self, expense_id):
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM expenses WHERE id = ?", (expense_id,)
            ).fetchone())

    def get_all_expenses(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM expenses ORDER BY date DESC, id DESC"
            ).fetchall()]

    # ── CRUD: Secciones personalizadas ──────────────────────────────────

    def create_custom_section(self, section_key, name, columns_json, icon="📄", workbook_json=None, description="", color="#5e81f4", type="spreadsheet", settings_json="{}", sort_order=0, document_id=None):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO custom_sections (section_key, name, icon, columns_json, workbook_json, description, color, type, settings_json, sort_order, document_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (section_key, name, icon, columns_json, workbook_json, description, color, type, settings_json, sort_order, document_id),
            )
            return cur.lastrowid

    def update_custom_section_meta(self, section_id, name=None, description=None, color=None, type=None, icon=None, settings_json=None, editable=None, deletable=None, visible=None, sort_order=None, document_id=None):
        with self._connect() as conn:
            fields = []
            values = []
            for k, v in [("name", name), ("description", description), ("color", color), ("type", type), ("icon", icon), ("settings_json", settings_json), ("editable", editable), ("deletable", deletable), ("visible", visible), ("sort_order", sort_order), ("document_id", document_id)]:
                if v is not None:
                    fields.append(f"{k} = ?")
                    values.append(v)
            if fields:
                values.append(section_id)
                conn.execute(f"UPDATE custom_sections SET {', '.join(fields)} WHERE id = ?", values)

    def get_custom_section(self, section_id_or_key):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM custom_sections WHERE id = ? OR section_key = ?",
                (section_id_or_key, section_id_or_key),
            ).fetchone()
            return dict(row) if row else None

    def get_all_custom_sections(self, visible_only=False):
        with self._connect() as conn:
            sql = "SELECT * FROM custom_sections"
            if visible_only:
                sql += " WHERE visible = 1"
            sql += " ORDER BY sort_order ASC"
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def delete_custom_section(self, section_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM custom_section_data WHERE section_id = ?", (section_id,))
            conn.execute("DELETE FROM custom_sections WHERE id = ?", (section_id,))

    def archive_custom_section(self, section_id):
        with self._connect() as conn:
            section = conn.execute("SELECT document_id FROM custom_sections WHERE id = ?", (section_id,)).fetchone()
            if section and section["document_id"]:
                conn.execute("UPDATE documents SET is_archived = 1 WHERE id = ?", (section["document_id"],))
            conn.execute("UPDATE custom_sections SET visible = 0 WHERE id = ?", (section_id,))

    def update_section_workbook(self, section_id, workbook_json):
        with self._connect() as conn:
            conn.execute("UPDATE custom_sections SET workbook_json = ? WHERE id = ?", (workbook_json, section_id))

    def add_custom_section_row(self, section_id, row_data_json):
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO custom_section_data (section_id, row_data) VALUES (?, ?)",
                (section_id, row_data_json),
            )
            return cur.lastrowid

    def get_custom_section_rows(self, section_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM custom_section_data WHERE section_id = ? ORDER BY id ASC",
                (section_id,),
            ).fetchall()]

    def update_custom_section_row(self, row_id, row_data_json):
        with self._connect() as conn:
            conn.execute(
                "UPDATE custom_section_data SET row_data = ?, updated_at = datetime('now') WHERE id = ?",
                (row_data_json, row_id),
            )

    def delete_custom_section_row(self, row_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM custom_section_data WHERE id = ?", (row_id,))


    # ── Document Categories ───────────────────────────────────────────────

    def _seed_document_categories(self):
        categories = [
            ("GradeBook", "\U0001f4d8", "#3b82f6", 1, 1),
            ("Attendance", "\U0001f4cb", "#8b5cf6", 2, 1),
            ("Schedule", "\U0001f4c5", "#10b981", 3, 1),
            ("Inventory", "\U0001f4e6", "#f59e0b", 4, 1),
            ("Template", "\U0001f4c4", "#6b7280", 5, 1),
            ("Document", "\U0001f4c4", "#6b7280", 6, 1),
        ]
        with self._connect() as conn:
            for name, icon, color, order, system in categories:
                conn.execute(
                    "INSERT OR IGNORE INTO document_categories (name, icon, color, sort_order, is_system) VALUES (?, ?, ?, ?, ?)",
                    (name, icon, color, order, system),
                )

    # ── System Sections ────────────────────────────────────────────────────

    SYSTEM_SECTIONS = [
        ("inicio",              "Inicio",             "\U0001f3e0", 0,  False, False, True, "internal"),
        ("dashboard",           "Dashboard",          "\U0001f4ca", 1,  False, False, True, "internal"),
        ("notas",               "Notas",              "\U0001f4dd", 2,  True,  True,  True, "internal"),
        ("estudiantes",         "Estudiantes",        "\U0001f9d1\u200d\U0001f393", 3, True, True, True, "internal"),
        ("docentes",            "Docentes",           "\U0001f468\u200d\U0001f3eb", 4, True, True, True, "internal"),
        ("asignaturas",         "Asignaturas",        "\U0001f4da", 5,  True,  True,  True, "internal"),
        ("matricula",           "Matrícula",          "\U0001f4cb", 6,  True,  True,  True, "internal"),
        ("asistencia_alumnos",  "Asistencia alumnos", "\U0001f4c5", 7,  True,  True,  True, "internal"),
        ("asistencia_docentes", "Asistencia docentes","\U0001f468\u200d\U0001f3eb", 8, True, True, True, "internal"),
        ("gastos",              "Gastos",             "\U0001f4b0", 9,  True,  True,  True, "internal"),
        ("documentos",          "Documentos",         "\U0001f4c1", 10, True,  True,  True, "internal"),
        ("configuracion",       "Configuración",      "\u2699\ufe0f", 11, False, False, True, "internal"),
    ]

    def _seed_sections(self):
        with self._connect() as conn:
            cat = conn.execute(
                "SELECT id FROM document_categories WHERE name = 'Document'"
            ).fetchone()
            doc_cat_id = cat["id"] if cat else 6
            for key, name, icon, order, editable, deletable, visible, vtype in self.SYSTEM_SECTIONS:
                existing = conn.execute(
                    "SELECT id, document_id FROM custom_sections WHERE section_key = ?", (key,)
                ).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE custom_sections SET sort_order = ?, editable = ?, deletable = ?, visible = ? WHERE id = ?",
                        (order, 1 if editable else 0, 1 if deletable else 0, 1 if visible else 0, existing["id"]),
                    )
                else:
                    cur = conn.execute(
                        """INSERT INTO documents (name, category_id, icon, color, settings_json)
                           VALUES (?, ?, ?, ?, ?)""",
                        (name, doc_cat_id, icon, "#5e81f4", "{}"),
                    )
                    doc_id = cur.lastrowid
                    conn.execute(
                        "INSERT INTO document_instances (document_id, current_version) VALUES (?, 0)",
                        (doc_id,),
                    )
                    conn.execute(
                        """INSERT INTO custom_sections
                           (section_key, name, icon, columns_json, editable, deletable, visible, sort_order, document_id, type)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (key, name, icon, "[]", 1 if editable else 0, 1 if deletable else 0, 1 if visible else 0, order, doc_id, vtype),
                    )

    def _migrate_documents(self):
        with self._connect() as conn:
            migrated = conn.execute("SELECT 1 FROM documents LIMIT 1").fetchone()
            if migrated:
                return
            sections = [dict(r) for r in conn.execute("SELECT * FROM custom_sections").fetchall()]
            if not sections:
                return
            default_cat = conn.execute(
                "SELECT id FROM document_categories WHERE name = 'Document'"
            ).fetchone()
            doc_cat_id = default_cat["id"] if default_cat else 1
            for sec in sections:
                name_lower = (sec.get("name") or "").lower()
                cat_guess = "Document"
                if any(k in name_lower for k in ("asist", "attendance")):
                    cat_guess = "Attendance"
                elif any(k in name_lower for k in ("horar", "schedule")):
                    cat_guess = "Schedule"
                elif any(k in name_lower for k in ("invent", "inventory")):
                    cat_guess = "Inventory"
                elif any(k in name_lower for k in ("nota", "grade", "boletin", "report")):
                    cat_guess = "GradeBook"
                cat = conn.execute(
                    "SELECT id FROM document_categories WHERE name = ?", (cat_guess,)
                ).fetchone()
                cat_id = cat["id"] if cat else doc_cat_id
                cur = conn.execute(
                    """INSERT INTO documents (name, category_id, description, icon, color, settings_json)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (sec.get("name",""), cat_id, sec.get("description",""), sec.get("icon","\U0001f4c4"), sec.get("color","#5e81f4"), sec.get("settings_json","{}")),
                )
                doc_id = cur.lastrowid
                wb = sec.get("workbook_json")
                if wb:
                    conn.execute(
                        "INSERT INTO document_versions (document_id, version, workbook_json, comment) VALUES (?, 1, ?, 'Migrated')",
                        (doc_id, wb),
                    )
                    conn.execute(
                        "INSERT INTO document_instances (document_id, current_version) VALUES (?, 1)", (doc_id,),
                    )
                else:
                    conn.execute(
                        "INSERT INTO document_instances (document_id, current_version) VALUES (?, 0)", (doc_id,),
                    )

    # ── CRUD: Documentos ──────────────────────────────────────────────────

    def create_document(self, name, category_id=6, description="", icon="\U0001f4c4", color="#5e81f4", school_year="", settings_json="{}"):
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO documents (name, category_id, description, icon, color, school_year, settings_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, category_id, description, icon, color, school_year, settings_json),
            )
            doc_id = cur.lastrowid
            conn.execute(
                "INSERT INTO document_instances (document_id, current_version) VALUES (?, 0)", (doc_id,),
            )
            return doc_id

    def get_document(self, doc_id):
        with self._connect() as conn:
            row = conn.execute("SELECT d.*, dc.name AS category_name, dc.icon AS category_icon FROM documents d LEFT JOIN document_categories dc ON dc.id = d.category_id WHERE d.id = ?", (doc_id,)).fetchone()
            return dict(row) if row else None

    def get_all_documents(self, category_id=None, school_year=None, archived=False, search=None):
        with self._connect() as conn:
            sql = "SELECT d.*, dc.name AS category_name, dc.icon AS category_icon FROM documents d LEFT JOIN document_categories dc ON dc.id = d.category_id WHERE d.is_archived = ?"
            params = [1 if archived else 0]
            if category_id:
                sql += " AND d.category_id = ?"
                params.append(category_id)
            if school_year:
                sql += " AND d.school_year = ?"
                params.append(school_year)
            if search:
                sql += " AND d.name LIKE ?"
                params.append(f"%{search}%")
            sql += " ORDER BY d.updated_at DESC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def update_document(self, doc_id, **kwargs):
        allowed = ["name", "category_id", "description", "icon", "color", "school_year", "settings_json", "is_archived"]
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [doc_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE documents SET {set_clause} WHERE id = ?", vals)

    def delete_document(self, doc_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM document_metadata WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM document_instances WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM document_versions WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    def archive_document(self, doc_id):
        self.update_document(doc_id, is_archived=1)

    def restore_document(self, doc_id):
        self.update_document(doc_id, is_archived=0)

    def save_document_version(self, doc_id, workbook_json, comment="", created_by=""):
        with self._connect() as conn:
            max_ver = conn.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 AS next_ver FROM document_versions WHERE document_id = ?",
                (doc_id,),
            ).fetchone()[0]
            cur = conn.execute(
                "INSERT INTO document_versions (document_id, version, workbook_json, comment, created_by) VALUES (?, ?, ?, ?, ?)",
                (doc_id, max_ver, workbook_json, comment, created_by),
            )
            existing = conn.execute(
                "SELECT 1 FROM document_instances WHERE document_id = ?", (doc_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE document_instances SET current_version = ? WHERE document_id = ?",
                    (max_ver, doc_id),
                )
            else:
                conn.execute(
                    "INSERT INTO document_instances (document_id, current_version) VALUES (?, ?)",
                    (doc_id, max_ver),
                )
            return cur.lastrowid

    def get_document_versions(self, doc_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM document_versions WHERE document_id = ? ORDER BY version DESC",
                (doc_id,),
            ).fetchall()]

    def get_document_version(self, version_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM document_versions WHERE id = ?", (version_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_latest_workbook(self, doc_id):
        with self._connect() as conn:
            row = conn.execute(
                """SELECT v.* FROM document_versions v
                   JOIN document_instances i ON i.document_id = v.document_id
                   WHERE v.document_id = ? AND v.version = i.current_version
                   LIMIT 1""",
                (doc_id,),
            ).fetchone()
            return dict(row) if row else None

    def duplicate_document(self, doc_id, new_name=None):
        doc = self.get_document(doc_id)
        if not doc:
            return None
        name = new_name or f"{doc['name']} (Copia)"
        new_id = self.create_document(
            name=name,
            category_id=doc["category_id"],
            description=doc.get("description", ""),
            icon=doc.get("icon", "\U0001f4c4"),
            color=doc.get("color", "#5e81f4"),
            school_year=doc.get("school_year", ""),
        )
        wb = self.get_latest_workbook(doc_id)
        if wb and wb.get("workbook_json"):
            self.save_document_version(new_id, wb["workbook_json"], comment="Duplicado")
        return new_id

    def get_document_categories(self):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM document_categories ORDER BY sort_order"
            ).fetchall()]

    def get_document_instances(self, doc_id):
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM document_instances WHERE document_id = ?", (doc_id,)
            ).fetchall()]


# ── Singleton ──────────────────────────────────────────────────────────

_db = Database()


# ── Context manager (para acceso directo estilo old) ──────────────────

@contextmanager
def get_connection():
    conn = _db._connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Module-level convenience wrappers ─────────────────────────────────

def init_db():
    _db.initialize()


def get_db_path():
    return str(_db.path)


def row_to_dict(row):
    return dict(row) if row else None


# ── Estudiantes (wrappers aceptan keys English/Spanish) ───────────────

def _map_student_data(data):
    """Traduce keys English → Spanish si es necesario."""
    mapped = {}
    for k, v in data.items():
        mapped[_STUDENT_COL_MAP.get(k, k)] = v
    return mapped


def save_student(code, nombre=None, full_name=None, sex="", sexo="", age=None,
                 edad=None, tutor="", phone="", telefono="", address="",
                 domicilio="", course="", curso="", shift="", turno="",
                 transfer="", traslado="", pending_subject="",
                 asig_pendiente="", payment="", pago="", pass_level="",
                 paso_nivel="", pending_payment="", pago_pendiente=""):
    name = nombre or full_name
    data = _map_student_data({
        "code": code, "nombre": name, "sexo": sexo or sex, "edad": edad or age,
        "tutor": tutor, "telefono": telefono or phone,
        "domicilio": domicilio or address,
        "curso": curso or course, "turno": turno or shift,
        "traslado": traslado or transfer,
        "asig_pendiente": asig_pendiente or pending_subject,
        "pago": pago or payment, "paso_nivel": paso_nivel or pass_level,
        "pago_pendiente": pago_pendiente or pending_payment,
    })
    return _db.save_student(data)


def get_student(student_id):
    return _db.get_student(student_id)


def get_student_by_code(code):
    return _db.get_student_by_code(code)


def get_all_students(active_only=True):
    return _db.get_all_students(active_only)


def get_students_by_course(course):
    return _db.get_students_by_course(course)


def get_students_by_subject(subject_id):
    return _db.get_students_by_subject(subject_id)


def search_students(query):
    return _db.search_students(query)


def update_student(student_id, **kwargs):
    data = _map_student_data(kwargs)
    _db.update_student(student_id, data)


def deactivate_student(student_id):
    _db.deactivate_student(student_id)


def reactivate_student(student_id):
    _db.reactivate_student(student_id)


def delete_student(student_id):
    _db.delete_student(student_id)


def student_code_exists(code):
    return _db.student_code_exists(code)


# ── Profesores ────────────────────────────────────────────────────────

def save_teacher(code, name, last_name, specialty=""):
    return _db.save_teacher(code, name, last_name, specialty)


def get_teacher(teacher_id):
    return _db.get_teacher(teacher_id)


def get_all_teachers():
    return _db.get_all_teachers()


def update_teacher(teacher_id, **kwargs):
    _db.update_teacher(teacher_id, **kwargs)


def delete_teacher(teacher_id):
    _db.delete_teacher(teacher_id)


def teacher_code_exists(code):
    return _db.teacher_code_exists(code)


# ── Asignaturas ───────────────────────────────────────────────────────

def save_subject(name, grade_level="", teacher_id=None):
    return _db.save_subject(name, grade_level, teacher_id)


def get_subject(subject_id):
    return _db.get_subject(subject_id)


def get_all_subjects(grade_level=None):
    return _db.get_all_subjects(grade_level)


def get_subjects_by_level(grade_level):
    return _db.get_subjects_by_level(grade_level)


def get_subjects_for_course(course):
    return _db.get_subjects_for_course(course)


def get_subjects_by_group(group_key):
    return _db.get_subjects_by_group(group_key)


def update_subject(subject_id, **kwargs):
    _db.update_subject(subject_id, **kwargs)


def delete_subject(subject_id):
    _db.delete_subject(subject_id)


# ── Notas ─────────────────────────────────────────────────────────────

def upsert_grade(student_id, subject_id, period, score, obs=""):
    _db.upsert_grade(student_id, subject_id, period, score, obs)


def get_grade(student_id, subject_id, period):
    return _db.get_grade(student_id, subject_id, period)


def get_grades_by_student(student_id):
    return _db.get_grades_by_student(student_id)


def delete_grade(grade_id):
    _db.delete_grade(grade_id)


def get_report_by_course(course):
    return _db.get_report_by_course(course)


def get_report_by_student(student_id):
    return _db.get_report_by_student(student_id)


def get_summary_by_trimester(trimester):
    return _db.get_summary_by_trimester(trimester)


# ── Años Escolares ────────────────────────────────────────────────────

def create_school_year(label, default_amount=0):
    return _db.create_school_year(label, default_amount)


def get_school_year(year_id):
    return _db.get_school_year(year_id)


def get_all_school_years():
    return _db.get_all_school_years()


def get_active_school_year():
    return _db.get_active_school_year()


def set_active_school_year(year_id):
    _db.set_active_school_year(year_id)


def update_school_year(year_id, **kwargs):
    _db.update_school_year(year_id, **kwargs)


# ── Matrícula / Pagos ─────────────────────────────────────────────────

def upsert_enrollment(student_id, school_year_id, total_amount,
                      paid_amount=0, payment_date="", notes=""):
    _db.upsert_enrollment(student_id, school_year_id, total_amount,
                          paid_amount, payment_date, notes)


def get_enrollment(student_id, school_year_id):
    return _db.get_enrollment(student_id, school_year_id)


def get_enrollments_by_year(school_year_id):
    return _db.get_enrollments_by_year(school_year_id)


def get_enrollment_stats(school_year_id):
    return _db.get_enrollment_stats(school_year_id)


def get_debtors(school_year_id, only_unpaid=False):
    return _db.get_debtors(school_year_id, only_unpaid)


def seed_enrollment_for_year(school_year_id, default_amount):
    return _db.seed_enrollment_for_year(school_year_id, default_amount)


# ── Import / Sync ─────────────────────────────────────────────────────

def diff_import(rows):
    return _db.diff_import(rows)


def apply_import(rows):
    _db.apply_import(rows)


def diff_import_students(rows):
    return _db.diff_import_students(rows)


def apply_import_students(rows, accept_conflicts=False):
    return _db.apply_import_students(rows, accept_conflicts)


# ── Workbooks ─────────────────────────────────────────────────────────

def save_workbook(name, grid_key, type_="custom", subject_id=None,
                  school_year_id=None, sheet_data="[]"):
    return _db.save_workbook(name, grid_key, type_, subject_id,
                             school_year_id, sheet_data)


def get_workbook(workbook_id):
    return _db.get_workbook(workbook_id)


def get_all_workbooks(type_=None):
    return _db.get_all_workbooks(type_)


def update_workbook(workbook_id, **kwargs):
    _db.update_workbook(workbook_id, **kwargs)


def delete_workbook(workbook_id):
    _db.delete_workbook(workbook_id)


# ── Stats ─────────────────────────────────────────────────────────────

def get_stats():
    return _db.get_stats()


def get_stats_by_curso():
    return _db.get_stats_by_curso()


def get_distinct_courses():
    return _db.get_distinct_courses()


def get_dashboard_extended():
    return _db.get_dashboard_extended()


def get_recent_activity(limit=10):
    return _db.get_recent_activity(limit)


def export_all_to_dict():
    return _db.export_all_to_dict()


# ── Roles y Usuarios ──────────────────────────────────────────────────

def authenticate(username, password):
    return _db.authenticate(username, password)


def get_role_permissions(role_id):
    return _db.get_role_permissions(role_id)


def get_all_roles():
    return _db.get_all_roles()


def save_role(name, description=""):
    return _db.save_role(name, description)


def update_role(role_id, **kwargs):
    _db.update_role(role_id, **kwargs)


def delete_role(role_id):
    _db.delete_role(role_id)


def set_role_permissions(role_id, view_keys):
    _db.set_role_permissions(role_id, view_keys)


def get_all_users():
    return _db.get_all_users()


def save_user(username, password, role_id, teacher_id=None):
    return _db.save_user(username, password, role_id, teacher_id)


def update_user(user_id, **kwargs):
    _db.update_user(user_id, **kwargs)


def delete_user(user_id):
    _db.delete_user(user_id)


def user_exists(username):
    return _db.user_exists(username)


def change_password(user_id, new_password):
    return _db.change_password(user_id, new_password)


# ── CRUD: Gastos ──────────────────────────────────────────────────

def save_expense(concept, amount, date, notes=""):
    return _db.save_expense(concept, amount, date, notes)


def update_expense(expense_id, concept, amount, date, notes=""):
    return _db.update_expense(expense_id, concept, amount, date, notes)


def delete_expense(expense_id):
    return _db.delete_expense(expense_id)


def get_expense(expense_id):
    return _db.get_expense(expense_id)


def get_all_expenses():
    return _db.get_all_expenses()


# ── CRUD: Secciones personalizadas ──────────────────────────────────────

def create_custom_section(section_key, name, columns_json, icon="📄", workbook_json=None, description="", color="#5e81f4", type="spreadsheet", settings_json="{}", sort_order=0, document_id=None):
    return _db.create_custom_section(section_key, name, columns_json, icon, workbook_json, description, color, type, settings_json, sort_order, document_id)

def update_custom_section_meta(section_id, **kwargs):
    return _db.update_custom_section_meta(section_id, **kwargs)


def get_custom_section(section_id_or_key):
    return _db.get_custom_section(section_id_or_key)


def get_all_custom_sections(visible_only=False):
    return _db.get_all_custom_sections(visible_only=visible_only)


def archive_custom_section(section_id):
    return _db.archive_custom_section(section_id)


def update_section_workbook(section_id, workbook_json):
    return _db.update_section_workbook(section_id, workbook_json)


def delete_custom_section(section_id):
    return _db.delete_custom_section(section_id)


def add_custom_section_row(section_id, row_data_json):
    return _db.add_custom_section_row(section_id, row_data_json)


def get_custom_section_rows(section_id):
    return _db.get_custom_section_rows(section_id)


def update_custom_section_row(row_id, row_data_json):
    return _db.update_custom_section_row(row_id, row_data_json)


def delete_custom_section_row(row_id):
    return _db.delete_custom_section_row(row_id)


# ── CRUD: Documentos ──────────────────────────────────────────────────────

def create_document(name, category_id=6, description="", icon="\U0001f4c4", color="#5e81f4", school_year="", settings_json="{}"):
    return _db.create_document(name, category_id, description, icon, color, school_year, settings_json)

def get_document(doc_id):
    return _db.get_document(doc_id)

def get_all_documents(category_id=None, school_year=None, archived=False, search=None):
    return _db.get_all_documents(category_id, school_year, archived, search)

def update_document(doc_id, **kwargs):
    return _db.update_document(doc_id, **kwargs)

def delete_document(doc_id):
    return _db.delete_document(doc_id)

def archive_document(doc_id):
    return _db.archive_document(doc_id)

def restore_document(doc_id):
    return _db.restore_document(doc_id)

def save_document_version(doc_id, workbook_json, comment="", created_by=""):
    return _db.save_document_version(doc_id, workbook_json, comment, created_by)

def get_document_versions(doc_id):
    return _db.get_document_versions(doc_id)

def get_document_version(version_id):
    return _db.get_document_version(version_id)

def get_latest_workbook(doc_id):
    return _db.get_latest_workbook(doc_id)

def duplicate_document(doc_id, new_name=None):
    return _db.duplicate_document(doc_id, new_name)

def get_document_categories():
    return _db.get_document_categories()

def get_document_instances(doc_id):
    return _db.get_document_instances(doc_id)
