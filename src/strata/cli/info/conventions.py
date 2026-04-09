import typer

from strata.modules.info import InfoReader, fmt_conventions
from . import app, get_config


@app.command()
def conventions():
    """Show coding conventions."""
    config = get_config()
    reader = InfoReader(config)

    data = reader.conventions()
    if not data:
        typer.echo("No conventions configured.")
        return

    typer.echo(fmt_conventions(data))
