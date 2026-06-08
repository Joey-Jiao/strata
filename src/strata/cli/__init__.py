import typer

from . import paper
from . import corpus
from . import info

app = typer.Typer(help="Strata - Personal knowledge management MCP server")

app.add_typer(paper.app, name="paper", help="Paper/literature management")
app.add_typer(corpus.app, name="corpus", help="Conference paper corpus management")
app.add_typer(info.app, name="info", help="Static information and conventions")


@app.command()
def serve():
    """Start MCP server (stdio)."""
    from strata.server import main
    main()


if __name__ == "__main__":
    app()
