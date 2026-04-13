import typer

from strata.modules.info import InfoReader, fmt_code
from . import app, get_config


@app.command()
def code():
    """Show coding conventions."""
    config = get_config()
    reader = InfoReader(config)

    data = reader.code()
    if not data:
        typer.echo("No coding conventions configured.")
        return

    typer.echo(fmt_code(data))
