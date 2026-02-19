import json
from pydantic import BaseModel, Field, computed_field


class Author(BaseModel):
    first_name: str = ""
    last_name: str = ""
    role: str = "author"


class Paper(BaseModel):
    citation_key: str
    item_type: str = "article"
    title: str = ""
    authors: list[Author] = Field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    publisher: str | None = None
    book_title: str | None = None
    source_keys: list[str] = Field(default_factory=list)
    source_tags: list[str] = Field(default_factory=list)
    source_collections: list[str] = Field(default_factory=list)
    pdf_path: str | None = None
    arxiv_id: str | None = None
    venue: str | None = None
    imported_at: str | None = None
    synced_at: str | None = None
    deleted_at: str | None = None

    @computed_field
    @property
    def first_author(self) -> Author | None:
        authors = [a for a in self.authors if a.role == "author"]
        return authors[0] if authors else None

    @computed_field
    @property
    def editors(self) -> list[Author]:
        return [a for a in self.authors if a.role == "editor"]

    def authors_json(self) -> str:
        return json.dumps([a.model_dump() for a in self.authors])

    def source_keys_json(self) -> str:
        return json.dumps(self.source_keys)

    def source_tags_json(self) -> str:
        return json.dumps(self.source_tags)

    def source_collections_json(self) -> str:
        return json.dumps(self.source_collections)

    @classmethod
    def parse_authors(cls, json_str: str | None) -> list[Author]:
        if not json_str:
            return []
        data = json.loads(json_str)
        return [Author(first_name=a.get("first_name", ""), last_name=a.get("last_name", ""), role=a.get("role", "author")) for a in data]

    @classmethod
    def parse_json_list(cls, json_str: str | None) -> list[str]:
        if not json_str:
            return []
        return json.loads(json_str)
