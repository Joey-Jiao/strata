import json
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CorpusPaper(BaseModel):
    paper_id: str
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    citation_count: int | None = None
    open_access_url: str | None = None
    publication_date: str | None = None
    imported_at: str = ""

    @classmethod
    def from_s2_response(cls, data: dict) -> "CorpusPaper":
        authors = [a.get("name", "") for a in (data.get("authors") or []) if a.get("name")]
        external_ids = data.get("externalIds") or {}
        return cls(
            paper_id=data["paperId"],
            title=data.get("title") or "",
            authors=authors,
            abstract=data.get("abstract"),
            year=data.get("year"),
            venue=data.get("venue") or None,
            doi=external_ids.get("DOI"),
            arxiv_id=external_ids.get("ArXiv"),
            citation_count=data.get("citationCount"),
            open_access_url=(data.get("openAccessPdf") or {}).get("url"),
            publication_date=data.get("publicationDate"),
            imported_at=datetime.now(timezone.utc).isoformat(),
        )

    def authors_json(self) -> str:
        return json.dumps(self.authors)

    def authors_display(self) -> str:
        if not self.authors:
            return ""
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) == 2:
            return f"{self.authors[0]}, {self.authors[1]}"
        return f"{self.authors[0]} et al."
