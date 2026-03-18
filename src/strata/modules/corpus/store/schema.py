import sqlite3


def initialize_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            paper_id         TEXT PRIMARY KEY,
            openalex_id      TEXT,
            title            TEXT NOT NULL,
            authors          TEXT,
            abstract         TEXT,
            year             INTEGER,
            venue            TEXT,
            doi              TEXT,
            arxiv_id         TEXT,
            citation_count   INTEGER,
            open_access_url  TEXT,
            publication_date TEXT,
            topics           TEXT,
            keywords         TEXT,
            referenced_works TEXT,
            imported_at      TEXT NOT NULL,
            enriched_at      TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_corpus_year ON papers(year);
        CREATE INDEX IF NOT EXISTS idx_corpus_venue ON papers(venue);
        CREATE INDEX IF NOT EXISTS idx_corpus_doi ON papers(doi);

        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
            title, abstract, authors, content='papers', content_rowid='rowid'
        );

        CREATE TABLE IF NOT EXISTS authorships (
            paper_id         TEXT NOT NULL,
            author_id        TEXT NOT NULL,
            author_name      TEXT,
            orcid            TEXT,
            position         TEXT,
            is_corresponding INTEGER DEFAULT 0,
            institution_id   TEXT,
            institution      TEXT,
            country          TEXT,
            PRIMARY KEY (paper_id, author_id),
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );

        CREATE INDEX IF NOT EXISTS idx_authorships_author ON authorships(author_id);
        CREATE INDEX IF NOT EXISTS idx_authorships_institution ON authorships(institution_id);
    """)


def migrate_add_enrichment_columns(conn: sqlite3.Connection):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(papers)")}
    new_columns = {
        "openalex_id": "TEXT",
        "topics": "TEXT",
        "keywords": "TEXT",
        "referenced_works": "TEXT",
        "enriched_at": "TEXT",
    }
    for col, col_type in new_columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE papers ADD COLUMN {col} {col_type}")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS authorships (
            paper_id         TEXT NOT NULL,
            author_id        TEXT NOT NULL,
            author_name      TEXT,
            orcid            TEXT,
            position         TEXT,
            is_corresponding INTEGER DEFAULT 0,
            institution_id   TEXT,
            institution      TEXT,
            country          TEXT,
            PRIMARY KEY (paper_id, author_id),
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_corpus_doi ON papers(doi)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_authorships_author ON authorships(author_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_authorships_institution ON authorships(institution_id)")
    conn.commit()
