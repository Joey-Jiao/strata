from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.modules.corpus import create_store, create_vector_store, create_embedding_generator
from strata.server.common import text, not_found


def _format_results(papers, scores=None):
    items = []
    for i, p in enumerate(papers):
        score = f" (score: {scores[i]:.3f})" if scores else ""
        authors = p.authors_display()
        venue = f" | {p.venue}" if p.venue else ""
        citations = f" | Citations: {p.citation_count}" if p.citation_count else ""
        entry = f"[{p.paper_id}]{score} ({p.year or '?'}) {p.title}\n  {authors}{venue}{citations}"
        if p.abstract:
            abstract = p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract
            entry += f"\n  {abstract}"
        items.append(entry)
    return items


def handle_semantic_search(config: ConfigService, arguments: dict) -> list[TextContent]:
    limit = arguments.get("limit", 10)
    query = arguments.get("query", "")
    if not query:
        return text("Query is required.")

    generator = create_embedding_generator(config)
    vector_store = create_vector_store(config)
    db, repo = create_store(config)

    try:
        query_vector = generator.generate([query])[0]
        results = vector_store.search(query_vector, limit=limit)

        if not results:
            return text("No similar papers found.")

        paper_ids = [r["paper_id"] for r in results]
        scores = [r["score"] for r in results]
        papers = repo.get_by_ids(paper_ids)

        items = _format_results(papers, scores)
        header = f"Semantic search: {len(papers)} results\n"
        return text(header + "\n\n".join(items))
    finally:
        db.close()
        vector_store.close()


def handle_similar(config: ConfigService, arguments: dict) -> list[TextContent]:
    paper_id = arguments.get("paper_id", "")
    limit = arguments.get("limit", 10)

    db, repo = create_store(config)
    try:
        paper = repo.get(paper_id)
        if not paper:
            return not_found("Paper", paper_id)
        if not paper.abstract:
            return text(f"Paper {paper_id} has no abstract for similarity search.")

        query_text = f"{paper.title}\n{paper.abstract}"
    finally:
        db.close()

    generator = create_embedding_generator(config)
    query_vector = generator.generate([query_text])[0]

    vector_store = create_vector_store(config)
    db, repo = create_store(config)
    try:
        results = vector_store.search(query_vector, limit=limit + 1)
        results = [r for r in results if r["paper_id"] != paper_id][:limit]

        if not results:
            return text("No similar papers found.")

        paper_ids = [r["paper_id"] for r in results]
        scores = [r["score"] for r in results]
        papers = repo.get_by_ids(paper_ids)

        items = _format_results(papers, scores)
        header = f"Papers similar to: {paper.title}\n\n"
        return text(header + "\n\n".join(items))
    finally:
        db.close()
        vector_store.close()


DISCOVER_HANDLERS = {
    "corpus_semantic_search": handle_semantic_search,
    "corpus_similar": handle_similar,
}
