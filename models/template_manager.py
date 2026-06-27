import json
import sqlite3
from dataclasses import dataclass, field
from typing import Optional, List

from models.column_definition import ColumnDef, ColumnType


class TemplateManager:
    def __init__(self, db_path='school.db'):
        self.db_path = db_path

    def _get_db(self):
        return sqlite3.connect(self.db_path)

    def create_template(self, name, template_type='grades', course=None, level=None, columns_json='', sheet_data=''):
        conn = self._get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO templates (name, type, course, level, columns_json, sheet_data) VALUES (?, ?, ?, ?, ?, ?)",
                (name, template_type, course, level, columns_json, sheet_data)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Template with name '{name}' already exists.")
            return None
        finally:
            conn.close()

    def get_template(self, template_id):
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            # Return as a dictionary for easier access
            columns = [
                'id', 'name', 'type', 'course', 'level', 'columns_json', 
                'sheet_data', 'created_at', 'updated_at'
            ]
            return dict(zip(columns, row))
        return None

    def list_templates(self, template_type='grades'):
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, course, level FROM templates WHERE type = ? ORDER BY name", (template_type,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def columns_from_template(self, template_id):
        template = self.get_template(template_id)
        if not template or not template['columns_json']:
            return [], None
        try:
            column_data = json.loads(template['columns_json'])
            columns = [ColumnDef(**col_dict) for col_dict in column_data]
            return columns, template
        except (json.JSONDecodeError, TypeError):
            print(f"Error decoding columns_json for template ID {template_id}.")
            return [], template

    def save_template(self, template_id, **kwargs):
        conn = self._get_db()
        cursor = conn.cursor()
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            values.append(value)
        values.append(template_id)
        query = f"UPDATE templates SET {', '.join(updates)} WHERE id = ?"
        try:
            cursor.execute(query, values)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving template {template_id}: {e}")
            return False
        finally:
            conn.close()

template_manager = TemplateManager()
