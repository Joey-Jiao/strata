import typer

from strata.modules.paper.common import create_syncer
from . import app, get_config


@app.command()
def sync(deep: bool = typer.Option(False, "--deep", "-d", help="Deep sync: clear all and rebuild")):
    """Sync papers from Zotero to local store."""
    config = get_config()
    db, files, repo, syncer = create_syncer(config)

    if deep:
        typer.echo("Deep syncing (clearing and rebuilding)...")
        papers = syncer.deep_sync()
        typer.echo(f"Rebuilt with {len(papers)} papers.")
    else:
        typer.echo("Syncing from Zotero...")
        papers, deleted = syncer.sync()
        typer.echo(f"Synced {len(papers)} papers, deleted {deleted}.")
