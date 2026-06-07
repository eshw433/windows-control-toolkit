from __future__ import annotations

import sqlite3
from pathlib import Path

from loguru import logger

from wct.config.paths import AppPaths
from wct.db.migrations import run_migrations

_SCHEMA_FILE = Path(__file__).parent / "schema.sql"


class Database:

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or AppPaths.db_path()
        self._conn: sqlite3.Connection | None = None

    def open(self) -> None:
        logger.info("Opening database: {}", self._path)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._apply_schema()
        run_migrations(self._conn)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database closed")

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not open")
        return self._conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, seq: list[tuple]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, seq)

    def fetchone(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self.conn.commit()

    def vacuum(self) -> None:
        self.conn.commit()
        self.conn.execute("VACUUM")

    def integrity_check(self) -> bool:
        row = self.fetchone("PRAGMA integrity_check")
        return bool(row and row[0] == "ok")

    def page_size(self) -> int:
        row = self.fetchone("PRAGMA page_size")
        return int(row[0]) if row else 0

    def total_size_bytes(self) -> int:
        try:
            return self._path.stat().st_size
        except OSError:
            return 0

    def begin_transaction(self) -> None:
        self.conn.execute("BEGIN")

    def rollback(self) -> None:
        self.conn.rollback()

    def _apply_schema(self) -> None:
        schema_sql = _SCHEMA_FILE.read_text(encoding="utf-8")
        self.conn.executescript(schema_sql)
        logger.debug("Database schema applied")
