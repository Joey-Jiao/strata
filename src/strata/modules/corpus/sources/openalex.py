import json
import re
import sqlite3
import time
from datetime import datetime, timezone

import httpx
from tqdm import tqdm

OPENALEX_URL = "https://api.openalex.org/works"
SELECT = "id,doi,authorships,topics,keywords,referenced_works,cited_by_count"


def _normalize_title(title: str | None) -> str:
    if not title:
        return ""
    return re.sub(r"[^a-z0-9\s]", "", title.lower()).strip()


def _word_overlap(a: str, b: str) -> float:
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / max(len(words_a), len(words_b))


def _retry_get(url, *, headers, params, timeout=30.0, max_retries=5):
    for attempt in range(max_retries):
        delay = 2 * (2 ** attempt)
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=timeout)
        except httpx.TimeoutException:
            time.sleep(delay)
            continue
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(delay)
            continue
        resp.raise_for_status()
        return resp.json()
    return None


class OpenAlexEnricher:
    def __init__(self, db_path: str, api_key: str | None = None,
                 batch_size: int = 50, fuzzy_threshold: float = 0.85):
        self._db_path = db_path
        self._batch_size = batch_size
        self._fuzzy_threshold = fuzzy_threshold
        self._headers = {}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _get(self, params: dict) -> dict | None:
        return _retry_get(OPENALEX_URL, headers=self._headers, params=params)

    def _fetch_doi_batch(self, dois: list[str]) -> dict:
        data = self._get({
            "filter": f"doi:{'|'.join(dois)}",
            "select": SELECT, "per_page": "200",
        })
        if not data:
            return {}
        return {
            (w.get("doi") or "").replace("https://doi.org/", "").lower(): w
            for w in data.get("results", [])
            if w.get("doi")
        }

    def _fetch_doi_single(self, doi: str) -> dict | None:
        data = self._get({"filter": f"doi:{doi}", "select": SELECT, "per_page": "1"})
        if not data:
            return None
        results = data.get("results", [])
        return results[0] if results else None

    def _fetch_title(self, title: str, year: int | None, fuzzy: bool = False) -> dict | None:
        params = {"search": title, "select": SELECT + ",title", "per_page": "5"}
        if year:
            params["filter"] = f"publication_year:{year}"

        data = self._get(params)
        if not data or not data.get("results"):
            return None

        best = data["results"][0]
        norm_ours = _normalize_title(title)
        norm_theirs = _normalize_title(best.get("title"))

        if norm_ours == norm_theirs:
            return best
        if fuzzy and _word_overlap(norm_ours, norm_theirs) >= self._fuzzy_threshold:
            return best
        return None

    def _write_enrichment(self, conn: sqlite3.Connection, paper_id: str, work: dict | None):
        now = datetime.now(timezone.utc).isoformat()

        if not work:
            conn.execute("UPDATE papers SET enriched_at = ? WHERE paper_id = ?", (now, paper_id))
            return

        topics = json.dumps([{
            "name": t.get("display_name", ""),
            "score": round(t.get("score", 0), 3),
            "field": (t.get("field") or {}).get("display_name", ""),
            "subfield": (t.get("subfield") or {}).get("display_name", ""),
        } for t in work.get("topics", [])])
        keywords = json.dumps([k.get("display_name", "") for k in work.get("keywords", [])])
        referenced = json.dumps([r.split("/")[-1] for r in work.get("referenced_works", [])])
        openalex_id = (work.get("id") or "").split("/")[-1]

        conn.execute(
            """UPDATE papers SET openalex_id = ?, topics = ?, keywords = ?,
                referenced_works = ?, citation_count = ?, enriched_at = ?
            WHERE paper_id = ?""",
            (openalex_id, topics, keywords, referenced, work.get("cited_by_count"), now, paper_id),
        )

        conn.execute("DELETE FROM authorships WHERE paper_id = ?", (paper_id,))
        for a in work.get("authorships", []):
            author = a.get("author") or {}
            author_id = (author.get("id") or "").split("/")[-1]
            if not author_id:
                continue
            inst = (a.get("institutions") or [{}])[0] if a.get("institutions") else {}
            conn.execute(
                """INSERT OR REPLACE INTO authorships
                    (paper_id, author_id, author_name, orcid, position,
                     is_corresponding, institution_id, institution, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    paper_id, author_id, author.get("display_name"), author.get("orcid"),
                    a.get("author_position"), 1 if a.get("is_corresponding") else 0,
                    (inst.get("id") or "").split("/")[-1] or None,
                    inst.get("display_name"), (a.get("countries") or [None])[0],
                ),
            )

    def enrich(self) -> dict:
        from ..store.schema import migrate_add_enrichment_columns

        conn = self._conn()
        migrate_add_enrichment_columns(conn)

        pending = [dict(r) for r in conn.execute(
            "SELECT paper_id, doi, title, year FROM papers WHERE enriched_at IS NULL"
        )]
        if not pending:
            conn.close()
            return {"total": 0}

        non_arxiv = [p for p in pending if p["doi"] and "arxiv" not in p["doi"].lower()]
        arxiv = [p for p in pending if p["doi"] and "arxiv" in p["doi"].lower()]
        no_doi = [p for p in pending if not p["doi"]]

        stats = {"tier1_doi_batch": 0, "tier2_doi_single": 0, "no_doi": len(no_doi), "unmatched": 0}

        if non_arxiv:
            pbar = tqdm(total=len(non_arxiv), desc="Tier 1: DOI batch")
            for i in range(0, len(non_arxiv), self._batch_size):
                batch = non_arxiv[i:i + self._batch_size]
                paper_map = {p["doi"].lower(): p["paper_id"] for p in batch}
                results = self._fetch_doi_batch([p["doi"] for p in batch])
                for doi_lower, pid in paper_map.items():
                    self._write_enrichment(conn, pid, results.get(doi_lower))
                    if doi_lower in results:
                        stats["tier1_doi_batch"] += 1
                conn.commit()
                pbar.update(len(batch))
            pbar.close()

        if arxiv:
            for i, p in enumerate(tqdm(arxiv, desc="Tier 2: DOI single")):
                work = self._fetch_doi_single(p["doi"])
                self._write_enrichment(conn, p["paper_id"], work)
                if work:
                    stats["tier2_doi_single"] += 1
                if (i + 1) % 50 == 0:
                    conn.commit()
            conn.commit()

        for p in no_doi:
            self._write_enrichment(conn, p["paper_id"], None)
        conn.commit()

        stats["unmatched"] = len(non_arxiv) + len(arxiv) - stats["tier1_doi_batch"] - stats["tier2_doi_single"]
        conn.close()
        stats["total"] = len(pending)
        return stats
