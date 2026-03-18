import sqlite3
from pathlib import Path


class CorpusDatabase:
    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def initialize(self):
        from .schema import initialize_schema
        initialize_schema(self.connection())

    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
