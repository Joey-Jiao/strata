import typer

from strata.modules.profile import ProfileReader
from strata.server.profile.handlers.query import _fmt_conventions
from . import app, get_config


@app.command()
def conventions():
    """Show coding conventions."""
    config = get_config()
    reader = ProfileReader(config)

    data = reader.conventions()
    if not data:
        typer.echo("No conventions configured.")
        return

    typer.echo(_fmt_conventions(data))
