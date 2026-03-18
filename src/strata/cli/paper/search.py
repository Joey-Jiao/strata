import typer

from strata.modules.paper.common import create_store
from . import app, get_config


@app.command()
def search(query: str):
    """Search papers by title, author, or abstract."""
    config = get_config()
    db, files, repo = create_store(config)

    papers, total = repo.find(query=query)
    typer.echo(f"Found {total} papers:")
    for paper in papers:
        year = paper.year or "?"
        typer.echo(f"[{paper.citation_key}] ({year}) {paper.title[:60]}")
