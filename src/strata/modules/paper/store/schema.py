import sqlite3


def initialize_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
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

        CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
        CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id) WHERE arxiv_id IS NOT NULL;

        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
            title, abstract, authors, content='papers', content_rowid='rowid'
        );

        CREATE TABLE IF NOT EXISTS collections (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            parent_id  INTEGER DEFAULT NULL REFERENCES collections(id) ON DELETE CASCADE,
            full_path  TEXT NOT NULL UNIQUE,
            source_key TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS paper_collections (
            paper_key     TEXT NOT NULL,
            collection_id INTEGER NOT NULL,
            PRIMARY KEY (paper_key, collection_id),
            FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_pc_collection ON paper_collections(collection_id);

        DROP TABLE IF EXISTS schema_version;
    """)
