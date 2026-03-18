import signal
import time

import typer

from strata.modules.paper.common import create_syncer
from strata.modules.paper.sync import ZoteroWatcher
from . import app, get_config


@app.command()
def watch():
    """Watch Zotero for changes and sync automatically."""
    config = get_config()
    db, files, repo, syncer = create_syncer(config)
    zotero_db = config.get("paper.sources.zotero.database")

    typer.echo("Initial sync...")
    papers, deleted = syncer.sync()
    typer.echo(f"Synced {len(papers)} papers, deleted {deleted}.")

    running = True

    def on_change():
        typer.echo("Change detected, syncing...")
        new_papers, del_count = syncer.sync()
        typer.echo(f"Synced {len(new_papers)} papers, deleted {del_count}.")

    def stop_handler(signum, frame):
        nonlocal running
        running = False
        typer.echo("\nStopping...")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    watcher = ZoteroWatcher(zotero_db, on_change)
    watcher.start()
    typer.echo(f"Watching {zotero_db} for changes... (Ctrl+C to stop)")

    while running:
        time.sleep(1)

    watcher.stop()
    db.close()
    typer.echo("Stopped.")
