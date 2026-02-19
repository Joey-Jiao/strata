import os
from pathlib import Path

from .migrations import register
from ..utils import extract_arxiv_id, normalize_venue


def _table_exists(conn, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _alter_existing(conn):
    conn.execute("""
        CREATE TABLE papers_new (
            citation_key       TEXT PRIMARY KEY,
            item_type          TEXT DEFAULT 'article',
            title              TEXT NOT NULL,
            authors            TEXT,
            year               INTEGER,
            journal            TEXT,
            volume             TEXT,
            issue              TEXT,
            pages              TEXT,
            doi                TEXT,
            url                TEXT,
            abstract           TEXT,
            publisher          TEXT,
            book_title         TEXT,
            source_keys        TEXT,
            source_tags        TEXT,
            source_collections TEXT,
            pdf_path           TEXT,
            arxiv_id           TEXT,
            venue              TEXT,
            imported_at        TEXT,
            synced_at          TEXT,
            deleted_at         TEXT
        )
    """)
    conn.execute("""
        INSERT INTO papers_new (
            citation_key, item_type, title, authors, year,
            journal, volume, issue, pages, doi, url, abstract,
            publisher, book_title, source_keys, source_tags,
            source_collections, pdf_path, imported_at, synced_at
        )
        SELECT
            citation_key, item_type, title, authors, year,
            journal, volume, issue, pages, doi, url, abstract,
            publisher, book_title, json_array(source_key), tags,
            collections, pdf_path, updated_at, source_modified
        FROM papers
    """)
    conn.execute("DROP TABLE papers")
    conn.execute("ALTER TABLE papers_new RENAME TO papers")
    conn.execute("CREATE INDEX idx_papers_year ON papers(year)")
    conn.execute("CREATE INDEX idx_papers_title ON papers(title)")
    conn.execute("CREATE UNIQUE INDEX idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL")
    conn.execute("CREATE UNIQUE INDEX idx_papers_arxiv_id ON papers(arxiv_id) WHERE arxiv_id IS NOT NULL")


def _extract_derived_fields(conn):
    rows = conn.execute("SELECT citation_key, url, doi, journal, book_title FROM papers").fetchall()
    for row in rows:
        key, url, doi, journal, book_title = row
        arxiv_id = extract_arxiv_id(url, doi)
        venue = normalize_venue(journal, book_title)
        if arxiv_id or venue:
            updates = []
            params = []
            if arxiv_id:
                updates.append("arxiv_id = ?")
                params.append(arxiv_id)
            if venue:
                updates.append("venue = ?")
                params.append(venue)
            params.append(key)
            conn.execute(f"UPDATE papers SET {', '.join(updates)} WHERE citation_key = ?", params)


def _create_fresh(conn):
    conn.executescript("""
        CREATE TABLE papers (
            citation_key       TEXT PRIMARY KEY,
            item_type          TEXT DEFAULT 'article',
            title              TEXT NOT NULL,
            authors            TEXT,
            year               INTEGER,
            journal            TEXT,
            volume             TEXT,
            issue              TEXT,
            pages              TEXT,
            doi                TEXT,
            url                TEXT,
            abstract           TEXT,
            publisher          TEXT,
            book_title         TEXT,
            source_keys        TEXT,
            source_tags        TEXT,
            source_collections TEXT,
            pdf_path           TEXT,
            arxiv_id           TEXT,
            venue              TEXT,
            imported_at        TEXT,
            synced_at          TEXT,
            deleted_at         TEXT
        );

        CREATE INDEX idx_papers_year ON papers(year);
        CREATE INDEX idx_papers_title ON papers(title);
        CREATE UNIQUE INDEX idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL;
        CREATE UNIQUE INDEX idx_papers_arxiv_id ON papers(arxiv_id) WHERE arxiv_id IS NOT NULL;
    """)


def _create_fts(conn):
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
            title, abstract, authors, content='papers', content_rowid='rowid'
        )
    """)
    conn.execute("""
        INSERT INTO papers_fts(rowid, title, abstract, authors)
        SELECT rowid, title, COALESCE(abstract, ''), COALESCE(authors, '')
        FROM papers
    """)


def _migrate_files(conn, files_dir: str | None):
    if not files_dir:
        return
    files_path = Path(files_dir).expanduser()
    if not files_path.exists():
        return
    for pdf in list(files_path.glob("*.pdf")):
        stem = pdf.stem
        folder = files_path / stem
        folder.mkdir(exist_ok=True)
        dest = folder / "paper.pdf"
        os.rename(pdf, dest)
        new_path = f"{stem}/paper.pdf"
        conn.execute(
            "UPDATE papers SET pdf_path = ? WHERE pdf_path = ?",
            (new_path, pdf.name),
        )


@register(1)
def migration_001(conn, context: dict):
    if _table_exists(conn, "papers"):
        _alter_existing(conn)
        _extract_derived_fields(conn)
    else:
        _create_fresh(conn)
    _create_fts(conn)
    _migrate_files(conn, context.get("files_dir"))
