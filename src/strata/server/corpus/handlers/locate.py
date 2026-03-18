from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.modules.corpus import create_store
from strata.server.common import text, lines


def handle_search(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, repo = create_store(config)
    try:
        papers, total = repo.search(
            query=arguments.get("query"),
            venue=arguments.get("venue"),
            year_from=arguments.get("year_from"),
            year_to=arguments.get("year_to"),
            author=arguments.get("author"),
            limit=arguments.get("limit", 20),
            offset=arguments.get("offset", 0),
        )

        if not papers:
            return text("No papers found in corpus.")

        offset = arguments.get("offset", 0)
        limit = arguments.get("limit", 20)
        header = f"Found {total} papers (showing {offset + 1}-{offset + len(papers)})\n"

        items = []
        for p in papers:
            authors = p.authors_display()
            venue = f" | {p.venue}" if p.venue else ""
            citations = f" | Citations: {p.citation_count}" if p.citation_count else ""
            entry = f"[{p.paper_id}] ({p.year or '?'}) {p.title}\n  {authors}{venue}{citations}"
            if p.abstract:
                abstract = p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract
                entry += f"\n  {abstract}"
            items.append(entry)

        return text(header + "\n\n".join(items))
    finally:
        db.close()


def handle_browse(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, repo = create_store(config)
    try:
        browse_type = arguments.get("type", "venues")

        if browse_type == "venues":
            venues = repo.list_venues()
            if not venues:
                return text("No venues in corpus.")
            items = []
            for v in venues:
                year_range = f"{v['year_min']}-{v['year_max']}" if v["year_min"] != v["year_max"] else str(v["year_min"] or "?")
                items.append(f"- {v['venue']} ({v['count']} papers, {year_range})")
            return text(f"Venues ({len(venues)}):\n\n" + "\n".join(items))

        elif browse_type == "stats":
            stats = repo.get_stats()
            parts = [
                f"Total papers: {stats['total']}",
                f"Venues: {stats['venue_count']}",
                "",
                "By year:",
            ]
            for year, count in stats["by_year"][:15]:
                parts.append(f"  {year}: {count}")
            return lines(*parts)

        elif browse_type == "clusters":
            import json
            conn = db.connection()
            try:
                clusters = conn.execute(
                    "SELECT cluster_id, parent_id, level, label, keywords, paper_count FROM clusters ORDER BY level, paper_count DESC"
                ).fetchall()
            except Exception:
                return text("No clusters available. Run 'strata corpus ingest --only cluster' first.")
            if not clusters:
                return text("No clusters found.")
            items = []
            for c in clusters:
                indent = "  " * c["level"]
                kw = json.loads(c["keywords"]) if c["keywords"] else []
                kw_str = ", ".join(kw[:5])
                items.append(f"{indent}[{c['cluster_id']}] {c['label']} ({c['paper_count']})\n{indent}  {kw_str}")
            return text(f"Topic hierarchy ({len(clusters)} clusters):\n\n" + "\n".join(items))

        else:
            return text(f"Unknown browse type: {browse_type}")
    finally:
        db.close()


LOCATE_HANDLERS = {
    "corpus_search": handle_search,
    "corpus_browse": handle_browse,
}
