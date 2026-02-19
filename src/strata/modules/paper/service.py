from pathlib import Path

from strata.base.configs import ConfigService

from .models import ZoteroItem
from .sources import ZoteroReader, ZoteroStorageManager
from .export import generate_citation_key, CitationKeyManager, BibTeXExporter


class ZoteroService:
    def __init__(self, config: ConfigService):
        db_path = config.get("paper.sources.zotero.database", "~/Zotero/zotero.sqlite")
        storage_dir = config.get("paper.sources.zotero.storage_dir", "~/Zotero/storage")
        self._reader = ZoteroReader(db_path)
        self._storage = ZoteroStorageManager(storage_dir)
        self._exporter = BibTeXExporter()
        stop_words_list = config.get("paper.citation.stop_words", []) or []
        self._stop_words = set(stop_words_list)
        self._key_manager = CitationKeyManager(self._stop_words)
        self._output_dir = Path(config.get("paper.pdf.output_dir", "~/Documents/Papers")).expanduser()

    def _assign_citation_keys(self, items: list[ZoteroItem]) -> list[ZoteroItem]:
        key_map = self._key_manager.generate_all(items)
        for item in items:
            item.citation_key = key_map.get(item.key)
        return items

    def search(self, query: str) -> list[ZoteroItem]:
        items = self._reader.search(query)
        return self._assign_citation_keys(items)

    def get_item(self, key: str) -> ZoteroItem | None:
        item = self._reader.get_item_by_key(key)
        if item:
            item.citation_key = generate_citation_key(item, self._stop_words)
        return item

    def get_citation(self, key: str) -> str | None:
        item = self.get_item(key)
        if not item:
            return None
        return self._exporter.export_item(item)

    def list_collections(self) -> list[str]:
        return self._reader.list_collections()

    def list_tags(self) -> list[str]:
        return self._reader.list_tags()

    def list_by_collection(self, name: str) -> list[ZoteroItem]:
        items = self._reader.list_items(collection=name)
        return self._assign_citation_keys(items)

    def list_by_tag(self, tag: str) -> list[ZoteroItem]:
        items = self._reader.list_items(tag=tag)
        return self._assign_citation_keys(items)

    def list_all(self) -> list[ZoteroItem]:
        items = self._reader.list_items()
        return self._assign_citation_keys(items)

    def export_bib(self, keys: list[str], output: Path | str | None = None) -> str:
        items = []
        for key in keys:
            item = self.get_item(key)
            if item:
                items.append(item)
        bib_content = self._exporter.export_items(items)
        if output:
            output_path = Path(output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(bib_content)
        return bib_content

    def export_collection_bib(self, collection: str, output: Path | str | None = None) -> str:
        items = self.list_by_collection(collection)
        bib_content = self._exporter.export_items(items)
        if output:
            output_path = Path(output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(bib_content)
        return bib_content

    def get_pdf_path(self, key: str) -> Path | None:
        item = self._reader.get_item_by_key(key)
        if not item:
            return None
        return self._storage.get_pdf_path(item)

    def archive_pdf(self, key: str, dest_dir: Path | str | None = None) -> Path | None:
        item = self.get_item(key)
        if not item:
            return None
        target_dir = Path(dest_dir).expanduser() if dest_dir else self._output_dir
        return self._storage.archive_pdf(item, target_dir)

    def archive_pdfs(self, keys: list[str], dest_dir: Path | str | None = None) -> dict[str, Path | None]:
        target_dir = Path(dest_dir).expanduser() if dest_dir else self._output_dir
        results = {}
        for key in keys:
            results[key] = self.archive_pdf(key, target_dir)
        return results
