import typer

from strata.modules.paper.common import create_store
from . import app, get_config


@app.command()
def collections():
    """List all collections."""
    config = get_config()
    db, files, repo = create_store(config)

    tree = repo.list_collections_tree()
    if not tree:
        typer.echo("No collections found.")
        return
    typer.echo("Collections:")
    for c in tree:
        depth = c["full_path"].count("/")
        indent = "  " * depth
        typer.echo(f"  {indent}{c['name']} ({c['paper_count']})")
