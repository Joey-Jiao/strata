import signal
import time
from pathlib import Path

import typer

from strata.base.configs import ConfigService
from strata.modules.paper.sources.zotero import ZoteroReader, ZoteroStorageManager
from strata.modules.paper.store import PaperDatabase, PaperRepository, PaperFiles
from strata.modules.paper.sync import ZoteroSync, ZoteroWatcher
from strata.modules.paper.export import BibTeXExporter

app = typer.Typer()


def get_config() -> ConfigService:
    return ConfigService()


def get_components(config: ConfigService):
    db_path = config.get("paper.store.database", "~/workspace/resource/paper/paper.sqlite")
    files_dir = config.get("paper.store.files_dir", "~/workspace/resource/paper/files")
    zotero_db = config.get("paper.sources.zotero.database", "~/workspace/resource/zotero/zotero.sqlite")
    zotero_storage = config.get("paper.sources.zotero.storage_dir", "~/workspace/resource/zotero/storage")
    stop_words = set(config.get("paper.citation.stop_words", []) or [])

    db = PaperDatabase(db_path)
    db.initialize(files_dir=files_dir)
    files = PaperFiles(files_dir)
    reader = ZoteroReader(zotero_db)
    zotero_stor = ZoteroStorageManager(zotero_storage)
    repo = PaperRepository(db)
    syncer = ZoteroSync(reader, zotero_stor, db, files, stop_words)

    return db, files, reader, zotero_stor, repo, syncer


@app.command()
def sync(deep: bool = typer.Option(False, "--deep", "-d", help="Deep sync: clear all and rebuild")):
    """Sync papers from Zotero to local store."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)

    if deep:
        typer.echo("Deep syncing (clearing and rebuilding)...")
        papers = syncer.deep_sync()
        typer.echo(f"Rebuilt with {len(papers)} papers.")
    else:
        typer.echo("Syncing from Zotero...")
        papers, deleted = syncer.sync()
        typer.echo(f"Synced {len(papers)} papers, deleted {deleted}.")


@app.command()
def watch():
    """Watch Zotero for changes and sync automatically."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)
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


@app.command(name="list")
def list_papers(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of papers to show"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    collection: str = typer.Option(None, "--collection", "-c", help="Filter by collection path"),
):
    """List papers in local store."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)

    if collection:
        papers = repo.list_by_collection(collection)
    elif tag:
        papers, _ = repo.find(tag=tag, limit=limit)
    else:
        papers = repo.list_all()

    for paper in papers[:limit]:
        year = paper.year or "?"
        typer.echo(f"[{paper.citation_key}] ({year}) {paper.title[:60]}")

    if len(papers) > limit:
        typer.echo(f"... and {len(papers) - limit} more")


@app.command()
def search(query: str):
    """Search papers by title, author, or abstract."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)

    papers, total = repo.find(query=query)
    typer.echo(f"Found {total} papers:")
    for paper in papers:
        year = paper.year or "?"
        typer.echo(f"[{paper.citation_key}] ({year}) {paper.title[:60]}")


@app.command(name="export")
def export_cmd(
    keys: str = typer.Argument(default=None, help="Citation keys (comma-separated)"),
    output: Path = typer.Option(default=None, help="Output file"),
    all_papers: bool = typer.Option(default=False, help="Export all papers"),
):
    """Export papers to BibTeX format."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)
    exporter = BibTeXExporter()

    if all_papers:
        papers = repo.list_all()
    elif keys:
        key_list = [k.strip() for k in keys.split(",")]
        papers = [repo.get(k) for k in key_list]
        papers = [p for p in papers if p]
    else:
        typer.echo("Specify citation keys or use --all")
        raise typer.Exit(1)

    bib = exporter.export_papers(papers)

    if output:
        output.write_text(bib)
        typer.echo(f"Exported {len(papers)} papers to {output}")
    else:
        typer.echo(bib)


@app.command()
def info(key: str):
    """Show details of a paper."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)

    paper = repo.get(key)
    if not paper:
        typer.echo(f"Paper not found: {key}")
        raise typer.Exit(1)

    typer.echo(f"Citation Key: {paper.citation_key}")
    typer.echo(f"Title: {paper.title}")
    authors = ", ".join(f"{a.first_name} {a.last_name}" for a in paper.authors if a.role == "author")
    typer.echo(f"Authors: {authors}")
    typer.echo(f"Year: {paper.year or 'N/A'}")
    typer.echo(f"Type: {paper.item_type}")
    if paper.venue:
        typer.echo(f"Venue: {paper.venue}")
    if paper.journal:
        typer.echo(f"Journal: {paper.journal}")
    if paper.arxiv_id:
        typer.echo(f"arXiv: {paper.arxiv_id}")
    if paper.doi:
        typer.echo(f"DOI: {paper.doi}")
    if paper.pdf_path:
        typer.echo(f"PDF: {paper.pdf_path}")
    if paper.source_collections:
        typer.echo(f"Collections: {', '.join(paper.source_collections)}")
    if paper.source_tags:
        typer.echo(f"Tags: {', '.join(paper.source_tags)}")


@app.command()
def collections():
    """List all collections."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)

    colls = repo.list_collections()
    if not colls:
        typer.echo("No collections found.")
        return
    typer.echo("Collections:")
    for c in colls:
        typer.echo(f"  {c}")


@app.command()
def check():
    """Validate PDF/DB consistency and report anomalies."""
    config = get_config()
    db, files, reader, zotero_stor, repo, syncer = get_components(config)

    all_papers = repo.list_all()
    db_keys = {p.citation_key for p in all_papers}
    folder_keys = set(files.list_folders())

    orphan_folders = folder_keys - db_keys
    missing_pdfs = []
    no_pdf = []
    for p in all_papers:
        if p.pdf_path:
            if not files.exists(p.citation_key):
                missing_pdfs.append(p.citation_key)
        else:
            no_pdf.append(p.citation_key)

    typer.echo(f"Total papers: {len(all_papers)}")
    typer.echo(f"PDF folders: {len(folder_keys)}")
    typer.echo(f"Papers without PDF: {len(no_pdf)}")

    if orphan_folders:
        typer.echo(f"\nOrphan folders ({len(orphan_folders)}):")
        for f in sorted(orphan_folders):
            typer.echo(f"  {f}")

    if missing_pdfs:
        typer.echo(f"\nMissing PDFs ({len(missing_pdfs)}):")
        for k in sorted(missing_pdfs):
            typer.echo(f"  {k}")

    if not orphan_folders and not missing_pdfs:
        typer.echo("\nNo anomalies found.")
