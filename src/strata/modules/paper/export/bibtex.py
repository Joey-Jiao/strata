from ..entities import Paper
from ..models import ZoteroItem

ITEM_TYPE_MAP = {
    "journalArticle": "article",
    "book": "book",
    "bookSection": "incollection",
    "conferencePaper": "inproceedings",
    "thesis": "phdthesis",
    "report": "techreport",
    "webpage": "misc",
    "preprint": "article",
    "manuscript": "unpublished",
}


class BibTeXExporter:
    def __init__(self):
        self._type_map = ITEM_TYPE_MAP.copy()

    def _escape(self, value: str) -> str:
        value = value.replace("\\", r"\\")
        value = value.replace("{", r"\{")
        value = value.replace("}", r"\}")
        value = value.replace("&", r"\&")
        value = value.replace("%", r"\%")
        value = value.replace("$", r"\$")
        value = value.replace("#", r"\#")
        value = value.replace("_", r"\_")
        return value

    def _format_people(self, people: list) -> str:
        parts = []
        for p in people:
            if p.last_name and p.first_name:
                parts.append(f"{p.last_name}, {p.first_name}")
            elif p.last_name:
                parts.append(p.last_name)
            elif p.first_name:
                parts.append(p.first_name)
        return " and ".join(parts)

    def _build_entry(self, entry_type: str, cite_key: str, fields: list[tuple[str, str | None]]) -> str:
        entry_lines = [f"@{entry_type}{{{cite_key},"]
        for name, value in fields:
            if value:
                escaped = self._escape(value)
                entry_lines.append(f"  {name} = {{{escaped}}},")
        entry_lines.append("}")
        return "\n".join(entry_lines)

    def export_item(self, item: ZoteroItem) -> str:
        entry_type = self._type_map.get(item.item_type, "misc")
        cite_key = item.citation_key or item.key
        authors = [c for c in item.creators if c.role == "author"]
        editors = [c for c in item.creators if c.role == "editor"]
        fields = [
            ("title", item.title),
            ("author", self._format_people(authors)),
            ("editor", self._format_people(editors)),
            ("year", str(item.year) if item.year else None),
            ("journal", item.journal),
            ("booktitle", item.book_title),
            ("volume", item.volume),
            ("number", item.issue),
            ("pages", item.pages),
            ("publisher", item.publisher),
            ("doi", item.doi),
            ("url", item.url),
            ("abstract", item.abstract),
        ]
        return self._build_entry(entry_type, cite_key, fields)

    def export_items(self, items: list[ZoteroItem]) -> str:
        return "\n\n".join(self.export_item(item) for item in items)

    def export_paper(self, paper: Paper) -> str:
        entry_type = paper.item_type or "misc"
        authors = [a for a in paper.authors if a.role == "author"]
        editors = [a for a in paper.authors if a.role == "editor"]
        fields = [
            ("title", paper.title),
            ("author", self._format_people(authors)),
            ("editor", self._format_people(editors)),
            ("year", str(paper.year) if paper.year else None),
            ("journal", paper.journal),
            ("booktitle", paper.book_title),
            ("volume", paper.volume),
            ("number", paper.issue),
            ("pages", paper.pages),
            ("publisher", paper.publisher),
            ("doi", paper.doi),
            ("url", paper.url),
            ("abstract", paper.abstract),
        ]
        return self._build_entry(entry_type, paper.citation_key, fields)

    def export_papers(self, papers: list[Paper]) -> str:
        return "\n\n".join(self.export_paper(p) for p in papers)
