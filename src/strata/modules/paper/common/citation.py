import re
import unicodedata

from ..sources.zotero.models import ZoteroItem


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower()


def _format_author(item: ZoteroItem) -> str:
    author = item.first_author
    if not author:
        return "unknown"
    name = author.last_name or author.first_name
    return _normalize(name) or "unknown"


class CitationKeyManager:
    def __init__(self, stop_words: set[str]):
        self._stop_words = stop_words

    def _title_words(self, title: str) -> list[str]:
        words = _normalize(title).split()
        return [w for w in words if w not in self._stop_words] or words

    def generate_all(self, items: list[ZoteroItem]) -> dict[str, str]:
        items = sorted(items, key=lambda i: i.key)

        groups: dict[tuple[str, str], list[tuple[ZoteroItem, list[str]]]] = {}
        for item in items:
            author = _format_author(item)
            year = str(item.year) if item.year else ""
            words = self._title_words(item.title) if item.title else []
            groups.setdefault((author, year), []).append((item, words))

        result: dict[str, str] = {}
        used: set[str] = set()
        for (author, year), members in groups.items():
            assignments = self._assign_group(author, year, members, used)
            result.update(assignments)
            used.update(assignments.values())
        return result

    def _assign_group(
        self,
        author: str,
        year: str,
        members: list[tuple[ZoteroItem, list[str]]],
        used: set[str],
    ) -> dict[str, str]:
        local_used = set(used)
        result: dict[str, str] = {}

        for i, (item, words) in enumerate(members):
            n = self._minimum_unique_prefix(i, words, members)

            if not words:
                base = f"{author}{year}" or item.key
            else:
                base = f"{author}{year}{''.join(words[:n])}"

            key = base
            suffix = 2
            while key in local_used:
                key = f"{base}-{suffix}"
                suffix += 1

            result[item.key] = key
            local_used.add(key)

        return result

    @staticmethod
    def _minimum_unique_prefix(
        i: int,
        words: list[str],
        members: list[tuple[ZoteroItem, list[str]]],
    ) -> int:
        if len(members) == 1:
            return 1
        max_n = max(len(words), 1)
        for n in range(1, max_n + 1):
            collides = any(
                other_words[:n] == words[:n]
                for j, (_, other_words) in enumerate(members)
                if j != i
            )
            if not collides:
                return n
        return max_n
