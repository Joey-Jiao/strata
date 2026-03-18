import typer

from strata.modules.paper.common import create_store
from . import app, get_config


@app.command()
def stats():
    """Show paper library overview."""
    config = get_config()
    db, files, repo = create_store(config)

    all_papers = repo.list_all()
    stats = repo.get_stats()
    folder_keys = set(files.list_folders())

    typer.echo(f"Total papers: {stats['total']}")
    typer.echo(f"Year range: {stats['year_min']} - {stats['year_max']}")
    typer.echo(f"PDFs: {stats['pdf_count']} available, {stats['no_pdf_count']} missing")
    typer.echo(f"Last sync: {stats['last_sync'] or 'never'}")

    if stats["by_year"]:
        typer.echo("\nBy year:")
        for year, count in stats["by_year"][:10]:
            typer.echo(f"  {year}: {count}")

    tags = repo.list_tags()
    if tags:
        typer.echo(f"\nTags ({len(tags)}): {', '.join(tags[:15])}")

    tree = repo.list_collections_tree()
    if tree:
        typer.echo(f"\nCollections: {len(tree)}")

    db.close()
