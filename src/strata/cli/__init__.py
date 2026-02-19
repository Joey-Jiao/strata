import typer

from . import paper

app = typer.Typer(help="Strata - Personal knowledge management MCP server")

app.add_typer(paper.app, name="paper", help="Paper/literature management")


@app.command()
def serve():
    """Start MCP server."""
    from strata.server import main
    main()


if __name__ == "__main__":
    app()
