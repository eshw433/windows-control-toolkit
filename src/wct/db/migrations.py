from __future__ import annotations

import sqlite3

from loguru import logger


_ADDED_COLUMNS: list[tuple[str, str, str]] = [
    ("process_identities", "risk_score", "INTEGER NOT NULL DEFAULT 0"),
    ("process_identities", "risk_level", "TEXT NOT NULL DEFAULT 'low'"),
    ("process_identities", "note", "TEXT NOT NULL DEFAULT ''"),
    ("process_identities", "tags", "TEXT NOT NULL DEFAULT ''"),
    ("network_connections", "service_hint", "TEXT NOT NULL DEFAULT ''"),
    ("firewall_rules", "note", "TEXT NOT NULL DEFAULT ''"),
    ("file_rules", "folder_scope", "TEXT NOT NULL DEFAULT ''"),
    ("file_rules", "note", "TEXT NOT NULL DEFAULT ''"),
    ("file_actions", "file_size", "INTEGER NOT NULL DEFAULT 0"),
    ("file_actions", "rule_name", "TEXT NOT NULL DEFAULT ''"),
    ("trust_decisions", "expires_at", "TEXT NOT NULL DEFAULT ''"),
    ("quarantine_items", "size", "INTEGER NOT NULL DEFAULT 0"),
    ("quarantine_items", "sha256", "TEXT NOT NULL DEFAULT ''"),
    ("duplicate_groups", "file_count", "INTEGER NOT NULL DEFAULT 0"),
]


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def run_migrations(conn: sqlite3.Connection) -> int:
    applied = 0
    for table, column, ddl in _ADDED_COLUMNS:
        if not _table_exists(conn, table):
            continue
        if _column_exists(conn, table, column):
            continue
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            applied += 1
            logger.debug("Migration: added {}.{}", table, column)
        except sqlite3.OperationalError as exc:
            logger.warning("Migration failed for {}.{}: {}", table, column, exc)
    if applied:
        conn.commit()
        logger.info("Applied {} schema migrations", applied)
    return applied


def reset_indexes(conn: sqlite3.Connection) -> None:
    conn.execute("REINDEX")
    conn.commit()


def dump_schema(conn: sqlite3.Connection) -> str:
    parts: list[str] = []
    for row in conn.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
    ):
        if row[0]:
            parts.append(row[0] + ";")
    return "\n".join(parts)


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return 0
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0
