import typer

from strata.modules.paper.common import create_store
from . import app, get_config


@app.command(name="list")
def list_papers(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of papers to show"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    collection: str = typer.Option(None, "--collection", "-c", help="Filter by collection path"),
):
    """List papers in local store."""
    config = get_config()
    db, files, repo = create_store(config)

    if collection:
        papers, _ = repo.find(collection=collection, limit=limit)
    elif tag:
        papers, _ = repo.find(tag=tag, limit=limit)
    else:
        papers = repo.list_all()

    for paper in papers[:limit]:
        year = paper.year or "?"
        typer.echo(f"[{paper.citation_key}] ({year}) {paper.title[:60]}")

    if len(papers) > limit:
        typer.echo(f"... and {len(papers) - limit} more")
