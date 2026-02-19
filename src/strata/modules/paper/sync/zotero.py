from datetime import datetime, timezone

from ..entities import Paper, Author
from ..models import ZoteroItem
from ..utils import extract_arxiv_id, normalize_venue
from ..sources.zotero import ZoteroReader, ZoteroStorageManager
from ..store import PaperDatabase, PaperRepository, PaperFiles
from ..export import CitationKeyManager

ZOTERO_TYPE_MAP = {
    "journalArticle": "article",
    "book": "book",
    "bookSection": "incollection",
    "conferencePaper": "inproceedings",
    "thesis": "thesis",
    "report": "techreport",
    "preprint": "article",
    "manuscript": "article",
}


class ZoteroSync:
    def __init__(
        self,
        reader: ZoteroReader,
        zotero_storage: ZoteroStorageManager,
        db: PaperDatabase,
        files: PaperFiles,
        stop_words: set[str] | None = None,
    ):
        self._reader = reader
        self._zotero_storage = zotero_storage
        self._repo = PaperRepository(db)
        self._files = files
        self._stop_words = stop_words or set()
        self._key_manager = CitationKeyManager(self._stop_words)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _convert_item(self, item: ZoteroItem, citation_key: str) -> Paper:
        authors = [
            Author(first_name=c.first_name, last_name=c.last_name, role=c.role)
            for c in item.creators
        ]
        return Paper(
            citation_key=citation_key,
            item_type=ZOTERO_TYPE_MAP.get(item.item_type, "misc"),
            title=item.title,
            authors=authors,
            year=item.year,
            journal=item.journal,
            volume=item.volume,
            issue=item.issue,
            pages=item.pages,
            doi=item.doi,
            url=item.url,
            abstract=item.abstract,
            publisher=item.publisher,
            book_title=item.book_title,
            source_keys=[item.key],
            source_tags=item.tags,
            source_collections=item.collections,
            arxiv_id=extract_arxiv_id(item.url, item.doi),
            venue=normalize_venue(item.journal, item.book_title),
            synced_at=self._now(),
        )

    def _sync_pdf(self, item: ZoteroItem, citation_key: str) -> str | None:
        pdf_path = self._zotero_storage.get_pdf_path(item)
        if not pdf_path:
            return None
        return self._files.store(pdf_path, citation_key)

    def _find_duplicate(self, paper: Paper) -> Paper | None:
        if paper.doi:
            existing = self._repo.find_by_doi(paper.doi)
            if existing:
                return existing
        if paper.arxiv_id:
            existing = self._repo.find_by_arxiv_id(paper.arxiv_id)
            if existing:
                return existing
        if paper.title and paper.first_author and paper.year:
            existing = self._repo.find_by_title_author_year(
                paper.title, paper.first_author.last_name, paper.year
            )
            if existing:
                return existing
        return None

    def _cascade_key(self, old_key: str, new_key: str):
        new_pdf = self._files.rename(old_key, new_key)
        self._repo.update_citation_key(old_key, new_key, new_pdf)

    def sync(self) -> tuple[list[Paper], int]:
        items = sorted(self._reader.list_items(), key=lambda i: i.key)
        zotero_keys = {item.key for item in items}

        existing_source_keys = self._repo.list_source_keys()
        orphan_keys = existing_source_keys - zotero_keys
        deleted_count = 0
        for source_key in orphan_keys:
            paper = self._repo.get_by_source_key(source_key)
            if not paper:
                continue
            remaining = [k for k in paper.source_keys if k in zotero_keys]
            if not remaining:
                self._repo.soft_delete(paper.citation_key)
                self._repo.commit()
                deleted_count += 1

        key_map = self._key_manager.generate_all(items)
        all_keys = self._repo.list_all_keys()

        results = []
        for item in items:
            existing = self._repo.get_by_source_key(item.key)
            target_key = key_map[item.key]
            paper = self._convert_item(item, target_key)

            if not existing:
                duplicate = self._find_duplicate(paper)
                if duplicate:
                    self._repo.add_source_key(duplicate.citation_key, item.key)
                    existing = duplicate

            if existing:
                if target_key != existing.citation_key and target_key not in all_keys:
                    self._cascade_key(existing.citation_key, target_key)
                    all_keys.discard(existing.citation_key)
                    all_keys.add(target_key)
                elif target_key != existing.citation_key:
                    target_key = existing.citation_key
                paper.citation_key = target_key
                paper.imported_at = existing.imported_at
                paper.source_keys = list(set(existing.source_keys + [item.key]))
                if not self._files.exists(target_key):
                    paper.pdf_path = self._sync_pdf(item, target_key)
                else:
                    paper.pdf_path = existing.pdf_path
            else:
                paper.imported_at = self._now()
                paper.pdf_path = self._sync_pdf(item, target_key)
                all_keys.add(target_key)

            results.append(self._repo.upsert(paper))
            self._repo.commit()

        self._repo.rebuild_fts()
        self._cleanup()

        return results, deleted_count

    def _cleanup(self):
        db_keys = self._repo.list_all_keys()
        for folder in self._files.list_folders():
            if folder not in db_keys:
                self._files.delete(folder)

        conn = self._repo._db.connection()
        for paper in self._repo.list_all():
            if paper.pdf_path and not self._files.exists(paper.citation_key):
                conn.execute(
                    "UPDATE papers SET pdf_path = NULL WHERE citation_key = ?",
                    (paper.citation_key,),
                )
        conn.commit()

    def deep_sync(self) -> list[Paper]:
        self._repo.delete_all()
        self._repo.commit()
        self._files.delete_all()

        items = sorted(self._reader.list_items(), key=lambda i: i.key)
        key_map = self._key_manager.generate_all(items)
        results = []
        for item in items:
            citation_key = key_map[item.key]
            paper = self._convert_item(item, citation_key)
            paper.imported_at = self._now()
            paper.pdf_path = self._sync_pdf(item, citation_key)
            results.append(self._repo.insert(paper))
        self._repo.commit()
        self._repo.rebuild_fts()

        return results

    def list_new_items(self) -> list[ZoteroItem]:
        items = self._reader.list_items()
        existing = self._repo.list_source_keys()
        return [item for item in items if item.key not in existing]
