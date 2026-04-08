import typer

from . import paper
from . import corpus
from . import profile

app = typer.Typer(help="Strata - Personal knowledge management MCP server")

app.add_typer(paper.app, name="paper", help="Paper/literature management")
app.add_typer(corpus.app, name="corpus", help="Conference paper corpus management")
app.add_typer(profile.app, name="profile", help="Personal profile and conventions")


@app.command()
def serve(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio or http"),
    host: str = typer.Option("0.0.0.0", "--host", help="HTTP bind address"),
    port: int = typer.Option(8716, "--port", "-p", help="HTTP port"),
):
    """Start MCP server."""
    from strata.server import main
    main(transport=transport, host=host, port=port)


if __name__ == "__main__":
    app()
