import sqlite3
from typing import Callable

Migration = Callable[[sqlite3.Connection, dict], None]
_registry: list[tuple[int, Migration]] = []


def register(version: int):
    def decorator(fn: Migration) -> Migration:
        _registry.append((version, fn))
        return fn
    return decorator


def run_migrations(conn: sqlite3.Connection, context: dict | None = None):
    context = context or {}
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    cursor = conn.execute("SELECT MAX(version) FROM schema_version")
    row = cursor.fetchone()
    current_version = row[0] if row[0] is not None else 0

    for version, migration in sorted(_registry):
        if version > current_version:
            try:
                migration(conn, context)
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
