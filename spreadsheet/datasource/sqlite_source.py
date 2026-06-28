from __future__ import annotations
import sqlite3
import json
from typing import Any, Dict, List, Optional, Tuple
from .base import DataSource


class SQLiteDataSource(DataSource):
    def __init__(self, db_path: str, table_name: str):
        self._db_path = db_path
        self._table = table_name
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                row INTEGER, col INTEGER, value TEXT, PRIMARY KEY(row, col)
            )
        """)
        self._conn.commit()

    def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def load_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int) -> Dict[Tuple[int, int], Any]:
        cursor = self._conn.execute(
            f"SELECT row, col, value FROM {self._table} "
            "WHERE row >= ? AND row <= ? AND col >= ? AND col <= ?",
            (row_start, row_end, col_start, col_end)
        )
        result = {}
        for r, c, v in cursor.fetchall():
            result[(r, c)] = json.loads(v)
        return result

    def save_block(self, row_start: int, col_start: int,
                   row_end: int, col_end: int,
                   data: Dict[Tuple[int, int], Any]) -> None:
        for (r, c), val in data.items():
            self._conn.execute(
                f"INSERT OR REPLACE INTO {self._table} (row, col, value) VALUES (?, ?, ?)",
                (r, c, json.dumps(val))
            )
        self._conn.commit()

    def row_count(self) -> int:
        cursor = self._conn.execute(f"SELECT MAX(row) FROM {self._table}")
        result = cursor.fetchone()[0]
        return (result or 0) + 1

    def col_count(self) -> int:
        cursor = self._conn.execute(f"SELECT MAX(col) FROM {self._table}")
        result = cursor.fetchone()[0]
        return (result or 0) + 1

    def flush(self) -> None:
        if self._conn:
            self._conn.commit()
