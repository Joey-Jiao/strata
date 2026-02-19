from datetime import datetime, timezone

from ..entities import Paper, Author
from .database import PaperDatabase


class PaperRepository:
    def __init__(self, db: PaperDatabase):
        self._db = db

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_paper(self, row: dict) -> Paper:
        return Paper(
            citation_key=row["citation_key"],
            item_type=row["item_type"] or "article",
            title=row["title"] or "",
            authors=Paper.parse_authors(row["authors"]),
            year=row["year"],
            journal=row["journal"],
            volume=row["volume"],
            issue=row["issue"],
            pages=row["pages"],
            doi=row["doi"],
            url=row["url"],
            abstract=row["abstract"],
            publisher=row["publisher"],
            book_title=row["book_title"],
            source_keys=Paper.parse_json_list(row["source_keys"]),
            source_tags=Paper.parse_json_list(row["source_tags"]),
            source_collections=Paper.parse_json_list(row["source_collections"]),
            pdf_path=row["pdf_path"],
            arxiv_id=row["arxiv_id"],
            venue=row["venue"],
            imported_at=row["imported_at"],
            synced_at=row["synced_at"],
            deleted_at=row["deleted_at"],
        )

    def begin(self):
        self._db.connection().execute("BEGIN")

    def commit(self):
        self._db.connection().commit()

    def rollback(self):
        self._db.connection().rollback()

    def get(self, citation_key: str) -> Paper | None:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT * FROM papers WHERE citation_key = ? AND deleted_at IS NULL",
            (citation_key,),
        )
        row = cursor.fetchone()
        return self._row_to_paper(dict(row)) if row else None

    def get_by_source_key(self, source_key: str) -> Paper | None:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT p.* FROM papers p, json_each(p.source_keys) j WHERE j.value = ? AND p.deleted_at IS NULL",
            (source_key,),
        )
        row = cursor.fetchone()
        return self._row_to_paper(dict(row)) if row else None

    def list_all(self) -> list[Paper]:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT * FROM papers WHERE deleted_at IS NULL ORDER BY year DESC, citation_key"
        )
        return [self._row_to_paper(dict(row)) for row in cursor]

    def find(
        self,
        query: str | None = None,
        arxiv_id: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        author: str | None = None,
        venue: str | None = None,
        tag: str | None = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Paper], int]:
        conn = self._db.connection()
        conditions = ["p.deleted_at IS NULL"]
        params: list = []
        use_fts = bool(query and query.strip())

        if use_fts:
            from_clause = "papers p JOIN papers_fts ON papers_fts.rowid = p.rowid"
            conditions.append("papers_fts MATCH ?")
            params.append(query)
        else:
            from_clause = "papers p"

        if arxiv_id:
            conditions.append("p.arxiv_id = ?")
            params.append(arxiv_id)
        if year_from is not None:
            conditions.append("p.year >= ?")
            params.append(year_from)
        if year_to is not None:
            conditions.append("p.year <= ?")
            params.append(year_to)
        if author:
            conditions.append("p.authors LIKE ?")
            params.append(f"%{author}%")
        if venue:
            conditions.append("p.venue = ?")
            params.append(venue)
        if tag:
            conditions.append("EXISTS (SELECT 1 FROM json_each(p.source_tags) j WHERE j.value = ?)")
            params.append(tag)

        where_clause = " AND ".join(conditions)

        if sort_by == "relevance" and use_fts:
            order = "ORDER BY papers_fts.rank"
        elif sort_by == "year":
            order = "ORDER BY p.year DESC, p.citation_key"
        else:
            order = "ORDER BY p.year DESC, p.citation_key"

        count_sql = f"SELECT COUNT(*) FROM {from_clause} WHERE {where_clause}"
        total = conn.execute(count_sql, params).fetchone()[0]

        select_sql = f"SELECT p.* FROM {from_clause} WHERE {where_clause} {order} LIMIT ? OFFSET ?"
        cursor = conn.execute(select_sql, params + [limit, offset])
        papers = [self._row_to_paper(dict(row)) for row in cursor]

        return papers, total

    def find_by_doi(self, doi: str) -> Paper | None:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT * FROM papers WHERE doi = ? AND deleted_at IS NULL",
            (doi,),
        )
        row = cursor.fetchone()
        return self._row_to_paper(dict(row)) if row else None

    def find_by_arxiv_id(self, arxiv_id: str) -> Paper | None:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT * FROM papers WHERE arxiv_id = ? AND deleted_at IS NULL",
            (arxiv_id,),
        )
        row = cursor.fetchone()
        return self._row_to_paper(dict(row)) if row else None

    def find_by_title_author_year(self, title: str, author_last: str, year: int) -> Paper | None:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT * FROM papers WHERE title = ? AND authors LIKE ? AND year = ? AND deleted_at IS NULL",
            (title, f"%{author_last}%", year),
        )
        row = cursor.fetchone()
        return self._row_to_paper(dict(row)) if row else None

    def insert(self, paper: Paper) -> Paper:
        conn = self._db.connection()
        conn.execute(
            """
            INSERT INTO papers (
                citation_key, item_type, title, authors, year,
                journal, volume, issue, pages, doi, url, abstract,
                publisher, book_title, source_keys, source_tags, source_collections,
                pdf_path, arxiv_id, venue, imported_at, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper.citation_key,
                paper.item_type,
                paper.title,
                paper.authors_json(),
                paper.year,
                paper.journal,
                paper.volume,
                paper.issue,
                paper.pages,
                paper.doi,
                paper.url,
                paper.abstract,
                paper.publisher,
                paper.book_title,
                paper.source_keys_json(),
                paper.source_tags_json(),
                paper.source_collections_json(),
                paper.pdf_path,
                paper.arxiv_id,
                paper.venue,
                paper.imported_at,
                paper.synced_at,
            ),
        )
        return paper

    def update(self, paper: Paper) -> Paper:
        conn = self._db.connection()
        conn.execute(
            """
            UPDATE papers SET
                item_type = ?, title = ?, authors = ?, year = ?,
                journal = ?, volume = ?, issue = ?, pages = ?, doi = ?, url = ?,
                abstract = ?, publisher = ?, book_title = ?, source_keys = ?,
                source_tags = ?, source_collections = ?, pdf_path = ?,
                arxiv_id = ?, venue = ?, synced_at = ?
            WHERE citation_key = ?
            """,
            (
                paper.item_type,
                paper.title,
                paper.authors_json(),
                paper.year,
                paper.journal,
                paper.volume,
                paper.issue,
                paper.pages,
                paper.doi,
                paper.url,
                paper.abstract,
                paper.publisher,
                paper.book_title,
                paper.source_keys_json(),
                paper.source_tags_json(),
                paper.source_collections_json(),
                paper.pdf_path,
                paper.arxiv_id,
                paper.venue,
                paper.synced_at,
                paper.citation_key,
            ),
        )
        return paper

    def upsert(self, paper: Paper) -> Paper:
        existing = self.get(paper.citation_key)
        if existing:
            paper.imported_at = existing.imported_at
            return self.update(paper)
        return self.insert(paper)

    def delete(self, citation_key: str) -> bool:
        conn = self._db.connection()
        cursor = conn.execute("DELETE FROM papers WHERE citation_key = ?", (citation_key,))
        return cursor.rowcount > 0

    def soft_delete(self, citation_key: str) -> bool:
        conn = self._db.connection()
        cursor = conn.execute(
            "UPDATE papers SET deleted_at = ? WHERE citation_key = ? AND deleted_at IS NULL",
            (self._now(), citation_key),
        )
        return cursor.rowcount > 0

    def update_citation_key(self, old_key: str, new_key: str, new_pdf_path: str | None = None):
        conn = self._db.connection()
        conn.execute(
            "UPDATE papers SET citation_key = ? WHERE citation_key = ?",
            (new_key, old_key),
        )
        if new_pdf_path:
            conn.execute(
                "UPDATE papers SET pdf_path = ? WHERE citation_key = ?",
                (new_pdf_path, new_key),
            )

    def add_source_key(self, citation_key: str, source_key: str):
        paper = self.get(citation_key)
        if paper and source_key not in paper.source_keys:
            paper.source_keys.append(source_key)
            conn = self._db.connection()
            conn.execute(
                "UPDATE papers SET source_keys = ? WHERE citation_key = ?",
                (paper.source_keys_json(), citation_key),
            )

    def list_source_keys(self) -> set[str]:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT j.value FROM papers p, json_each(p.source_keys) j WHERE p.deleted_at IS NULL"
        )
        return {row[0] for row in cursor}

    def list_all_keys(self) -> set[str]:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT citation_key FROM papers WHERE deleted_at IS NULL"
        )
        return {row[0] for row in cursor}

    def list_by_collection(self, collection: str) -> list[Paper]:
        conn = self._db.connection()
        cursor = conn.execute(
            """SELECT * FROM papers
               WHERE EXISTS (SELECT 1 FROM json_each(source_collections) j WHERE j.value = ?)
               AND deleted_at IS NULL
               ORDER BY year DESC, citation_key""",
            (collection,),
        )
        return [self._row_to_paper(dict(row)) for row in cursor]

    def list_collections(self) -> list[str]:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT source_collections FROM papers WHERE source_collections IS NOT NULL AND deleted_at IS NULL"
        )
        all_collections: set[str] = set()
        for row in cursor:
            all_collections.update(Paper.parse_json_list(row["source_collections"]))
        return sorted(all_collections)

    def list_tags(self) -> list[str]:
        conn = self._db.connection()
        cursor = conn.execute(
            "SELECT source_tags FROM papers WHERE source_tags IS NOT NULL AND deleted_at IS NULL"
        )
        all_tags: set[str] = set()
        for row in cursor:
            all_tags.update(Paper.parse_json_list(row["source_tags"]))
        return sorted(all_tags)

    def get_stats(self) -> dict:
        conn = self._db.connection()
        total = conn.execute("SELECT COUNT(*) FROM papers WHERE deleted_at IS NULL").fetchone()[0]
        year_range = conn.execute(
            "SELECT MIN(year), MAX(year) FROM papers WHERE deleted_at IS NULL"
        ).fetchone()
        by_year = conn.execute(
            "SELECT year, COUNT(*) as cnt FROM papers WHERE year IS NOT NULL AND deleted_at IS NULL GROUP BY year ORDER BY year DESC"
        ).fetchall()
        pdf_count = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE pdf_path IS NOT NULL AND deleted_at IS NULL"
        ).fetchone()[0]
        last_sync = conn.execute(
            "SELECT MAX(synced_at) FROM papers WHERE deleted_at IS NULL"
        ).fetchone()[0]
        return {
            "total": total,
            "year_min": year_range[0],
            "year_max": year_range[1],
            "by_year": [(row[0], row[1]) for row in by_year],
            "pdf_count": pdf_count,
            "no_pdf_count": total - pdf_count,
            "last_sync": last_sync,
        }

    def rebuild_fts(self):
        conn = self._db.connection()
        conn.execute("INSERT INTO papers_fts(papers_fts) VALUES('rebuild')")
        conn.commit()

    def delete_all(self) -> int:
        conn = self._db.connection()
        cursor = conn.execute("DELETE FROM papers")
        return cursor.rowcount
