from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.modules.corpus import create_store
from strata.server.common import text, lines


def handle_authors(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, repo = create_store(config)
    try:
        author_id = arguments.get("author_id")
        if author_id:
            profile = repo.author_profile(author_id)
            if not profile:
                return text(f"Author not found: {author_id}")

            parts = [
                f"Author: {profile['name']}",
                f"Papers: {profile['paper_count']}",
            ]
            if profile["orcid"]:
                parts.append(f"ORCID: {profile['orcid']}")

            parts.append("\nVenues:")
            for venue, count in list(profile["venues"].items())[:10]:
                parts.append(f"  {venue}: {count}")

            parts.append("\nYears:")
            for year, count in list(profile["years"].items())[:10]:
                parts.append(f"  {year}: {count}")

            if profile["top_coauthors"]:
                parts.append("\nTop co-authors:")
                for ca in profile["top_coauthors"]:
                    parts.append(f"  {ca['name']} ({ca['count']} papers)")

            parts.append("\nPapers:")
            for p in profile["papers"][:20]:
                parts.append(f"  ({p['year'] or '?'}) {p['title'][:70]}")

            return lines(*parts)

        author = arguments.get("author", "")
        if not author:
            return text("Provide author name or author_id.")

        limit = arguments.get("limit", 20)
        results = repo.find_by_author(author, limit=limit)
        if not results:
            return text(f"No papers found for author: {author}")

        seen = {}
        for r in results:
            aid = r["author_id"]
            if aid not in seen:
                seen[aid] = {"name": r["author_name"], "institution": r["institution"], "papers": []}
            seen[aid]["papers"].append(r)

        items = []
        for aid, info in seen.items():
            inst = f" | {info['institution']}" if info["institution"] else ""
            items.append(f"[{aid}] {info['name']}{inst} ({len(info['papers'])} papers)")
            for p in info["papers"][:5]:
                items.append(f"  ({p['year'] or '?'}) {p['title'][:60]}")

        return text(f"Authors matching '{author}':\n\n" + "\n".join(items))
    finally:
        db.close()


def handle_institutions(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, repo = create_store(config)
    try:
        institution = arguments.get("institution", "")
        if not institution:
            return text("Institution name is required.")

        stats = repo.institution_stats(institution)
        if not stats:
            return text(f"No papers found for institution: {institution}")

        parts = [
            f"Institution: {institution}",
            f"Total papers: {stats['paper_count']}",
            "\nBy venue:",
        ]
        for venue, count in list(stats["by_venue"].items())[:10]:
            parts.append(f"  {venue}: {count}")

        parts.append("\nBy year:")
        for year, count in list(stats["by_year"].items())[:10]:
            parts.append(f"  {year}: {count}")

        return lines(*parts)
    finally:
        db.close()


PROFILE_HANDLERS = {
    "corpus_authors": handle_authors,
    "corpus_institutions": handle_institutions,
}
