import sqlite3
from pathlib import Path


class PaperDatabase:
    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self, files_dir: str | None = None):
        from . import migration_001  # noqa: F401
        from .migrations import run_migrations
        conn = self.connection()
        run_migrations(conn, {"files_dir": files_dir})

    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "PaperDatabase":
        self._conn = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
