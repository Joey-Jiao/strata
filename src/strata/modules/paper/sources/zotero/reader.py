import sqlite3
from pathlib import Path
from typing import Iterator

from ...models import ZoteroItem, Creator, Attachment


class ZoteroReader:
    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path).expanduser()
        if not self._db_path.exists():
            raise FileNotFoundError(f"Database not found: {self._db_path}")

    def _connect(self) -> sqlite3.Connection:
        uri = f"file:{self._db_path}?immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_item_fields(self, conn: sqlite3.Connection, item_id: int) -> dict[str, str]:
        cursor = conn.execute(
            """
            SELECT f.fieldName, iv.value
            FROM itemDataValues iv
            JOIN itemData id ON iv.valueID = id.valueID
            JOIN fields f ON id.fieldID = f.fieldID
            WHERE id.itemID = ?
            """,
            (item_id,),
        )
        return {row["fieldName"]: row["value"] for row in cursor}

    def _get_creators(self, conn: sqlite3.Connection, item_id: int) -> list[Creator]:
        cursor = conn.execute(
            """
            SELECT c.firstName, c.lastName, ct.creatorType
            FROM creators c
            JOIN itemCreators ic ON c.creatorID = ic.creatorID
            JOIN creatorTypes ct ON ic.creatorTypeID = ct.creatorTypeID
            WHERE ic.itemID = ?
            ORDER BY ic.orderIndex
            """,
            (item_id,),
        )
        return [
            Creator(
                first_name=row["firstName"] or "",
                last_name=row["lastName"] or "",
                role=row["creatorType"],
            )
            for row in cursor
        ]

    def _get_attachments(self, conn: sqlite3.Connection, item_id: int) -> list[Attachment]:
        cursor = conn.execute(
            """
            SELECT ia.path, ia.contentType, i.key
            FROM itemAttachments ia
            JOIN items i ON ia.itemID = i.itemID
            WHERE ia.parentItemID = ?
            """,
            (item_id,),
        )
        attachments = []
        for row in cursor:
            path = row["path"] or ""
            if path.startswith("storage:"):
                path = path[8:]
            elif path.startswith("attachments:"):
                path = path[12:]
            attachments.append(
                Attachment(
                    path=path,
                    content_type=row["contentType"] or "",
                    key=row["key"] or "",
                )
            )
        return attachments

    def _build_collection_paths(self, conn: sqlite3.Connection) -> dict[int, str]:
        cursor = conn.execute("SELECT collectionID, collectionName, parentCollectionID FROM collections")
        collections: dict[int, tuple[str, int | None]] = {}
        for row in cursor:
            collections[row["collectionID"]] = (row["collectionName"], row["parentCollectionID"])

        def get_path(coll_id: int) -> str:
            name, parent_id = collections[coll_id]
            if parent_id is None:
                return name
            return f"{get_path(parent_id)}/{name}"

        return {coll_id: get_path(coll_id) for coll_id in collections}

    def _get_collections(self, conn: sqlite3.Connection, item_id: int, collection_paths: dict[int, str]) -> list[str]:
        cursor = conn.execute(
            """
            SELECT c.collectionID
            FROM collections c
            JOIN collectionItems ci ON c.collectionID = ci.collectionID
            WHERE ci.itemID = ?
            """,
            (item_id,),
        )
        return [collection_paths[row["collectionID"]] for row in cursor if row["collectionID"] in collection_paths]

    def _get_tags(self, conn: sqlite3.Connection, item_id: int) -> list[str]:
        cursor = conn.execute(
            """
            SELECT t.name
            FROM tags t
            JOIN itemTags it ON t.tagID = it.tagID
            WHERE it.itemID = ?
            """,
            (item_id,),
        )
        return [row["name"] for row in cursor]

    def _build_item(
        self, conn: sqlite3.Connection, item_id: int, key: str, item_type: str, collection_paths: dict[int, str]
    ) -> ZoteroItem:
        fields = self._get_item_fields(conn, item_id)
        return ZoteroItem(
            item_id=item_id,
            key=key,
            item_type=item_type,
            title=fields.get("title", ""),
            date=fields.get("date"),
            journal=fields.get("publicationTitle"),
            volume=fields.get("volume"),
            issue=fields.get("issue"),
            pages=fields.get("pages"),
            doi=fields.get("DOI"),
            url=fields.get("url"),
            abstract=fields.get("abstractNote"),
            publisher=fields.get("publisher"),
            book_title=fields.get("bookTitle"),
            creators=self._get_creators(conn, item_id),
            attachments=self._get_attachments(conn, item_id),
            collections=self._get_collections(conn, item_id, collection_paths),
            tags=self._get_tags(conn, item_id),
        )

    def _iter_items(
        self,
        conn: sqlite3.Connection,
        collection: str | None = None,
        tag: str | None = None,
    ) -> Iterator[tuple[int, str, str]]:
        base_query = """
            SELECT DISTINCT i.itemID, i.key, it.typeName
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            LEFT JOIN deletedItems di ON i.itemID = di.itemID
        """
        conditions = ["di.itemID IS NULL", "it.typeName != 'attachment'", "it.typeName != 'note'"]
        params: list[str] = []

        if collection:
            base_query += """
                JOIN collectionItems ci ON i.itemID = ci.itemID
                JOIN collections c ON ci.collectionID = c.collectionID
            """
            conditions.append("c.collectionName = ?")
            params.append(collection)

        if tag:
            base_query += """
                JOIN itemTags itag ON i.itemID = itag.itemID
                JOIN tags t ON itag.tagID = t.tagID
            """
            conditions.append("t.name = ?")
            params.append(tag)

        query = base_query + " WHERE " + " AND ".join(conditions)
        cursor = conn.execute(query, params)
        for row in cursor:
            yield row["itemID"], row["key"], row["typeName"]

    def list_items(
        self,
        collection: str | None = None,
        tag: str | None = None,
    ) -> list[ZoteroItem]:
        with self._connect() as conn:
            collection_paths = self._build_collection_paths(conn)
            items = []
            for item_id, key, item_type in self._iter_items(conn, collection, tag):
                items.append(self._build_item(conn, item_id, key, item_type, collection_paths))
            return items

    def get_item(self, item_id: int) -> ZoteroItem | None:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT i.key, it.typeName
                FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
                LEFT JOIN deletedItems di ON i.itemID = di.itemID
                WHERE i.itemID = ? AND di.itemID IS NULL
                """,
                (item_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            collection_paths = self._build_collection_paths(conn)
            return self._build_item(conn, item_id, row["key"], row["typeName"], collection_paths)

    def get_item_by_key(self, key: str) -> ZoteroItem | None:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT i.itemID, it.typeName
                FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
                LEFT JOIN deletedItems di ON i.itemID = di.itemID
                WHERE i.key = ? AND di.itemID IS NULL
                """,
                (key,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            collection_paths = self._build_collection_paths(conn)
            return self._build_item(conn, row["itemID"], key, row["typeName"], collection_paths)

    def search(self, query: str) -> list[ZoteroItem]:
        pattern = f"%{query}%"
        with self._connect() as conn:
            collection_paths = self._build_collection_paths(conn)
            cursor = conn.execute(
                """
                SELECT DISTINCT i.itemID, i.key, it.typeName
                FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
                LEFT JOIN deletedItems di ON i.itemID = di.itemID
                LEFT JOIN itemData id ON i.itemID = id.itemID
                LEFT JOIN itemDataValues iv ON id.valueID = iv.valueID
                LEFT JOIN fields f ON id.fieldID = f.fieldID
                LEFT JOIN itemCreators ic ON i.itemID = ic.itemID
                LEFT JOIN creators c ON ic.creatorID = c.creatorID
                WHERE di.itemID IS NULL
                  AND it.typeName NOT IN ('attachment', 'note')
                  AND (
                    (f.fieldName = 'title' AND iv.value LIKE ?)
                    OR c.lastName LIKE ?
                    OR c.firstName LIKE ?
                  )
                """,
                (pattern, pattern, pattern),
            )
            items = []
            for row in cursor:
                items.append(self._build_item(conn, row["itemID"], row["key"], row["typeName"], collection_paths))
            return items

    def list_collections(self) -> list[str]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT collectionName FROM collections ORDER BY collectionName")
            return [row["collectionName"] for row in cursor]

    def list_tags(self) -> list[str]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT DISTINCT name FROM tags ORDER BY name")
            return [row["name"] for row in cursor]
