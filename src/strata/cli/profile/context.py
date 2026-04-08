import typer

from strata.modules.profile import ProfileReader
from strata.server.profile.handlers.query import (
    _fmt_identity,
    _fmt_workspace,
    _fmt_hosts,
)
from . import app, get_config


@app.command()
def context():
    """Show personal context (identity, workspace, hosts)."""
    config = get_config()
    reader = ProfileReader(config)

    about = reader.about()
    if about:
        typer.echo(about.strip())
        typer.echo()

    identity = reader.identity()
    if identity:
        typer.echo("## Identity")
        typer.echo(_fmt_identity(identity))
        typer.echo()

    workspace = reader.workspace()
    if workspace:
        typer.echo("## Workspace")
        typer.echo(_fmt_workspace(workspace))
        typer.echo()

    hosts = reader.hosts()
    if hosts:
        typer.echo("## Hosts")
        typer.echo(_fmt_hosts(hosts))
