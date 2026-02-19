import re
from pydantic import BaseModel, Field, computed_field


class Creator(BaseModel):
    first_name: str = ""
    last_name: str = ""
    role: str = "author"


class Attachment(BaseModel):
    path: str
    content_type: str = ""
    key: str = ""


class ZoteroItem(BaseModel):
    item_id: int
    key: str
    item_type: str
    title: str = ""
    creators: list[Creator] = Field(default_factory=list)
    date: str | None = None
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    publisher: str | None = None
    book_title: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)
    collections: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    citation_key: str | None = None

    @computed_field
    @property
    def year(self) -> int | None:
        if not self.date:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", self.date)
        return int(match.group()) if match else None

    @property
    def first_author(self) -> Creator | None:
        authors = [c for c in self.creators if c.role == "author"]
        return authors[0] if authors else None
