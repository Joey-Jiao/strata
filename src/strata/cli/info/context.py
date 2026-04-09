import typer

from strata.modules.info import InfoReader, fmt_identity, fmt_workspace, fmt_hosts
from . import app, get_config


@app.command()
def context():
    """Show personal context (identity, workspace, hosts)."""
    config = get_config()
    reader = InfoReader(config)

    about = reader.about()
    if about:
        typer.echo(about.strip())
        typer.echo()

    identity = reader.identity()
    if identity:
        typer.echo("## Identity")
        typer.echo(fmt_identity(identity))
        typer.echo()

    workspace = reader.workspace()
    if workspace:
        typer.echo("## Workspace")
        typer.echo(fmt_workspace(workspace))
        typer.echo()

    hosts = reader.hosts()
    if hosts:
        typer.echo("## Hosts")
        typer.echo(fmt_hosts(hosts))
