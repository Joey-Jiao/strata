import re
import unicodedata

from ..models import ZoteroItem


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower()


def _extract_keywords(title: str, stop_words: set[str], count: int = 3) -> str:
    words = _normalize(title).split()
    keywords = [w for w in words if w not in stop_words]
    if len(keywords) < count:
        keywords = words
    return "".join(keywords[:count])


def _format_author(item: ZoteroItem) -> str:
    author = item.first_author
    if not author:
        return "unknown"
    name = author.last_name or author.first_name
    return _normalize(name) or "unknown"


def generate_citation_key(item: ZoteroItem, stop_words: set[str]) -> str:
    author = _format_author(item)
    year = str(item.year) if item.year else ""
    keywords = _extract_keywords(item.title, stop_words) if item.title else ""
    return f"{author}{year}{keywords}" or item.key


class CitationKeyManager:
    def __init__(self, stop_words: set[str]):
        self._stop_words = stop_words

    def _title_words(self, title: str) -> list[str]:
        words = _normalize(title).split()
        return [w for w in words if w not in self._stop_words] or words

    def generate_unique(self, item: ZoteroItem, existing_keys: set[str]) -> str:
        author = _format_author(item)
        year = str(item.year) if item.year else ""
        title_words = self._title_words(item.title) if item.title else []

        for count in range(1, len(title_words) + 1):
            key = f"{author}{year}{''.join(title_words[:count])}"
            if key not in existing_keys:
                return key

        base_key = f"{author}{year}{''.join(title_words)}" if title_words else f"{author}{year}"
        if base_key not in existing_keys:
            return base_key

        for i in range(2, 100):
            key = f"{base_key}-{i}"
            if key not in existing_keys:
                return key

        return base_key

    def generate_all(self, items: list[ZoteroItem]) -> dict[str, str]:
        items = sorted(items, key=lambda i: i.key)
        existing: set[str] = set()
        result: dict[str, str] = {}
        for item in items:
            key = self.generate_unique(item, existing)
            existing.add(key)
            result[item.key] = key
        return result
