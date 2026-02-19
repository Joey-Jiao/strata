from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.server.common import text, lines, not_found
from ..helpers import get_components


def _short_authors(paper) -> str:
    authors = [a for a in paper.authors if a.role == "author"]
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0].last_name
    if len(authors) == 2:
        return f"{authors[0].last_name}, {authors[1].last_name}"
    return f"{authors[0].last_name} et al."


def handle_find(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, files, repo = get_components(config)
    try:
        papers, total = repo.find(
            query=arguments.get("query"),
            arxiv_id=arguments.get("arxiv_id"),
            year_from=arguments.get("year_from"),
            year_to=arguments.get("year_to"),
            author=arguments.get("author"),
            venue=arguments.get("venue"),
            tag=arguments.get("tag"),
            sort_by=arguments.get("sort_by", "relevance"),
            limit=arguments.get("limit", 20),
            offset=arguments.get("offset", 0),
        )

        if not papers:
            return text("No papers found.")

        offset = arguments.get("offset", 0)
        limit = arguments.get("limit", 20)
        header = f"Found {total} papers (showing {offset + 1}-{offset + len(papers)})\n"

        items = []
        for p in papers:
            authors = _short_authors(p)
            venue = f" | {p.venue}" if p.venue else ""
            entry = f"[{p.citation_key}] ({p.year or '?'}) {p.title}\n  {authors}{venue}"
            if p.abstract:
                abstract = p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract
                entry += f"\n  {abstract}"
            items.append(entry)

        return text(header + "\n\n".join(items))
    finally:
        db.close()


def handle_info(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, files, repo = get_components(config)
    try:
        key = arguments.get("key", "")
        paper = repo.get(key)
        if not paper:
            return not_found("Paper", key)

        authors = ", ".join(
            f"{a.first_name} {a.last_name}" for a in paper.authors if a.role == "author"
        )
        parts = [
            f"Citation Key: {paper.citation_key}",
            f"Title: {paper.title}",
            f"Authors: {authors}",
            f"Year: {paper.year or 'N/A'}",
            f"Type: {paper.item_type}",
        ]
        if paper.venue:
            parts.append(f"Venue: {paper.venue}")
        if paper.journal:
            parts.append(f"Journal: {paper.journal}")
        if paper.arxiv_id:
            parts.append(f"arXiv: {paper.arxiv_id}")
        if paper.doi:
            parts.append(f"DOI: {paper.doi}")
        if paper.url:
            parts.append(f"URL: {paper.url}")

        if paper.pdf_path:
            try:
                import fitz
                pdf_path = files.get_path(paper.citation_key)
                if pdf_path.exists():
                    doc = fitz.open(str(pdf_path))
                    parts.append(f"Pages: {len(doc)}")
                    doc.close()
            except ImportError:
                pass

        if paper.abstract:
            parts.append(f"\nAbstract:\n{paper.abstract}")
        if paper.source_collections:
            parts.append(f"\nCollections: {', '.join(paper.source_collections)}")
        if paper.source_tags:
            parts.append(f"Tags: {', '.join(paper.source_tags)}")
        return lines(*parts)
    finally:
        db.close()


def handle_browse(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, files, repo = get_components(config)
    try:
        browse_type = arguments.get("type", "tags")

        if browse_type == "tags":
            items = repo.list_tags()
            if not items:
                return text("No tags.")
            return text(f"Tags ({len(items)}):\n\n" + "\n".join(f"- {t}" for t in items))

        elif browse_type == "stats":
            stats = repo.get_stats()
            parts = [
                f"Total papers: {stats['total']}",
                f"Year range: {stats['year_min']} - {stats['year_max']}",
                f"PDFs: {stats['pdf_count']} available, {stats['no_pdf_count']} missing",
                f"Last sync: {stats['last_sync'] or 'never'}",
                "",
                "By year:",
            ]
            for year, count in stats["by_year"][:10]:
                parts.append(f"  {year}: {count}")

            db_keys = repo.list_all_keys()
            folder_keys = set(files.list_folders())
            orphan_folders = folder_keys - db_keys
            orphan_records = {k for p in repo.list_all() if p.pdf_path for k in [p.citation_key] if not files.exists(k)}
            if orphan_folders or orphan_records:
                parts.append("")
                parts.append("Anomalies:")
                if orphan_folders:
                    parts.append(f"  Orphan folders (no DB record): {len(orphan_folders)}")
                if orphan_records:
                    parts.append(f"  Missing PDFs (DB says exists): {len(orphan_records)}")

            return lines(*parts)

        else:
            return text(f"Unknown browse type: {browse_type}")
    finally:
        db.close()


LOCATE_HANDLERS = {
    "paper_locate_find": handle_find,
    "paper_locate_info": handle_info,
    "paper_locate_browse": handle_browse,
}
