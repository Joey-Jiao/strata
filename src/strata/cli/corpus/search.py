import typer

from strata.modules.corpus import create_store
from . import app, get_config


@app.command()
def search(
    query: str = typer.Argument(help="Search query"),
    venue: str = typer.Option(None, "--venue", "-v", help="Filter by venue"),
    year: int = typer.Option(None, "--year", "-y", help="Filter by year"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
):
    """Search papers in the corpus."""
    config = get_config()
    db, repo = create_store(config)

    papers, total = repo.search(
        query=query,
        venue=venue,
        year_from=year,
        year_to=year,
        limit=limit,
    )
    typer.echo(f"Found {total} papers:")
    for p in papers:
        authors = p.authors_display()
        year_str = p.year or "?"
        typer.echo(f"[{p.paper_id[:8]}] ({year_str}) {p.title[:60]}")
        typer.echo(f"  {authors}")

    db.close()
