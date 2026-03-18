import json

from ..common.models import CorpusPaper
from .database import CorpusDatabase


class CorpusRepository:
    def __init__(self, db: CorpusDatabase):
        self._db = db

    def _row_to_paper(self, row: dict) -> CorpusPaper:
        authors = json.loads(row["authors"]) if row["authors"] else []
        return CorpusPaper(
            paper_id=row["paper_id"],
            title=row["title"],
            authors=authors,
            abstract=row["abstract"],
            year=row["year"],
            venue=row["venue"],
            doi=row["doi"],
            arxiv_id=row["arxiv_id"],
            citation_count=row["citation_count"],
            open_access_url=row["open_access_url"],
            publication_date=row["publication_date"],
            imported_at=row["imported_at"],
        )

    def upsert(self, paper: CorpusPaper):
        conn = self._db.connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO papers (
                paper_id, title, authors, abstract, year, venue,
                doi, arxiv_id, citation_count, open_access_url,
                publication_date, imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper.paper_id, paper.title, paper.authors_json(),
                paper.abstract, paper.year, paper.venue,
                paper.doi, paper.arxiv_id, paper.citation_count,
                paper.open_access_url, paper.publication_date,
                paper.imported_at,
            ),
        )

    def upsert_batch(self, papers: list[CorpusPaper]):
        conn = self._db.connection()
        conn.executemany(
            """
            INSERT OR REPLACE INTO papers (
                paper_id, title, authors, abstract, year, venue,
                doi, arxiv_id, citation_count, open_access_url,
                publication_date, imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.paper_id, p.title, p.authors_json(),
                    p.abstract, p.year, p.venue,
                    p.doi, p.arxiv_id, p.citation_count,
                    p.open_access_url, p.publication_date,
                    p.imported_at,
                )
                for p in papers
            ],
        )
        conn.commit()

    def search(
        self,
        query: str | None = None,
        venue: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        author: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[CorpusPaper], int]:
        conn = self._db.connection()
        conditions: list[str] = []
        params: list = []
        use_fts = bool(query and query.strip())

        if use_fts:
            from_clause = "papers p JOIN papers_fts ON papers_fts.rowid = p.rowid"
            conditions.append("papers_fts MATCH ?")
            params.append(query)
        else:
            from_clause = "papers p"

        if venue:
            conditions.append("p.venue = ?")
            params.append(venue)
        if year_from is not None:
            conditions.append("p.year >= ?")
            params.append(year_from)
        if year_to is not None:
            conditions.append("p.year <= ?")
            params.append(year_to)
        if author:
            conditions.append("p.authors LIKE ?")
            params.append(f"%{author}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        if use_fts:
            order = "ORDER BY papers_fts.rank"
        else:
            order = "ORDER BY p.citation_count DESC, p.year DESC"

        total = conn.execute(
            f"SELECT COUNT(*) FROM {from_clause} WHERE {where_clause}", params
        ).fetchone()[0]

        cursor = conn.execute(
            f"SELECT p.* FROM {from_clause} WHERE {where_clause} {order} LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        papers = [self._row_to_paper(dict(row)) for row in cursor]
        return papers, total

    def list_venues(self) -> list[dict]:
        conn = self._db.connection()
        cursor = conn.execute("""
            SELECT venue, COUNT(*) as count, MIN(year) as year_min, MAX(year) as year_max
            FROM papers
            WHERE venue IS NOT NULL AND venue != ''
            GROUP BY venue
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor]

    def get_stats(self) -> dict:
        conn = self._db.connection()
        total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        venue_count = conn.execute(
            "SELECT COUNT(DISTINCT venue) FROM papers WHERE venue IS NOT NULL AND venue != ''"
        ).fetchone()[0]
        by_year = conn.execute(
            "SELECT year, COUNT(*) as cnt FROM papers WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC"
        ).fetchall()
        return {
            "total": total,
            "venue_count": venue_count,
            "by_year": [(row[0], row[1]) for row in by_year],
        }

    def rebuild_fts(self):
        conn = self._db.connection()
        conn.execute("INSERT INTO papers_fts(papers_fts) VALUES('rebuild')")
        conn.commit()

    def get(self, paper_id: str) -> CorpusPaper | None:
        conn = self._db.connection()
        row = conn.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,)).fetchone()
        return self._row_to_paper(dict(row)) if row else None

    def get_by_ids(self, paper_ids: list[str]) -> list[CorpusPaper]:
        if not paper_ids:
            return []
        conn = self._db.connection()
        placeholders = ",".join("?" for _ in paper_ids)
        cursor = conn.execute(f"SELECT * FROM papers WHERE paper_id IN ({placeholders})", paper_ids)
        by_id = {row["paper_id"]: self._row_to_paper(dict(row)) for row in cursor}
        return [by_id[pid] for pid in paper_ids if pid in by_id]

    def find_by_author(self, author: str, limit: int = 20) -> list[dict]:
        conn = self._db.connection()
        cursor = conn.execute("""
            SELECT a.author_id, a.author_name, a.institution, a.country,
                   p.paper_id, p.title, p.year, p.venue
            FROM authorships a
            JOIN papers p ON a.paper_id = p.paper_id
            WHERE a.author_name LIKE ?
            ORDER BY p.year DESC
            LIMIT ?
        """, (f"%{author}%", limit))
        return [dict(row) for row in cursor]

    def find_by_institution(self, institution: str, limit: int = 20) -> list[dict]:
        conn = self._db.connection()
        cursor = conn.execute("""
            SELECT a.institution, a.country, a.author_name,
                   p.paper_id, p.title, p.year, p.venue
            FROM authorships a
            JOIN papers p ON a.paper_id = p.paper_id
            WHERE a.institution LIKE ?
            ORDER BY p.year DESC
            LIMIT ?
        """, (f"%{institution}%", limit))
        return [dict(row) for row in cursor]

    def author_profile(self, author_id: str) -> dict | None:
        conn = self._db.connection()
        info = conn.execute(
            "SELECT author_name, orcid FROM authorships WHERE author_id = ? LIMIT 1",
            (author_id,),
        ).fetchone()
        if not info:
            return None

        papers = conn.execute("""
            SELECT p.paper_id, p.title, p.year, p.venue, a.institution, a.country, a.position
            FROM authorships a JOIN papers p ON a.paper_id = p.paper_id
            WHERE a.author_id = ?
            ORDER BY p.year DESC
        """, (author_id,)).fetchall()

        venues = {}
        years = {}
        coauthors = {}
        for p in papers:
            v = p["venue"]
            if v:
                venues[v] = venues.get(v, 0) + 1
            y = p["year"]
            if y:
                years[y] = years.get(y, 0) + 1
            for ca in conn.execute(
                "SELECT author_id, author_name FROM authorships WHERE paper_id = ? AND author_id != ?",
                (p["paper_id"], author_id),
            ):
                coauthors[ca["author_id"]] = coauthors.get(ca["author_id"], {"name": ca["author_name"], "count": 0})
                coauthors[ca["author_id"]]["count"] += 1

        top_coauthors = sorted(coauthors.values(), key=lambda x: -x["count"])[:10]

        return {
            "author_id": author_id,
            "name": info["author_name"],
            "orcid": info["orcid"],
            "paper_count": len(papers),
            "papers": [dict(p) for p in papers],
            "venues": dict(sorted(venues.items(), key=lambda x: -x[1])),
            "years": dict(sorted(years.items(), key=lambda x: -x[0])),
            "top_coauthors": top_coauthors,
        }

    def institution_stats(self, institution: str) -> dict | None:
        conn = self._db.connection()
        rows = conn.execute("""
            SELECT p.venue, p.year, COUNT(DISTINCT p.paper_id) as cnt
            FROM authorships a JOIN papers p ON a.paper_id = p.paper_id
            WHERE a.institution LIKE ?
            GROUP BY p.venue, p.year
            ORDER BY p.year DESC, cnt DESC
        """, (f"%{institution}%",)).fetchall()

        if not rows:
            return None

        total = sum(r["cnt"] for r in rows)
        by_venue = {}
        by_year = {}
        for r in rows:
            v = r["venue"]
            if v:
                by_venue[v] = by_venue.get(v, 0) + r["cnt"]
            y = r["year"]
            if y:
                by_year[y] = by_year.get(y, 0) + r["cnt"]

        return {
            "institution": institution,
            "paper_count": total,
            "by_venue": dict(sorted(by_venue.items(), key=lambda x: -x[1])),
            "by_year": dict(sorted(by_year.items(), key=lambda x: -x[0])),
        }
