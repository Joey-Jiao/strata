import typer

from strata.modules.corpus import create_store
from . import app, get_config


@app.command()
def stats():
    """Show corpus overview."""
    config = get_config()
    db, repo = create_store(config)

    conn = db.connection()
    s = repo.get_stats()

    typer.echo(f"Total papers: {s['total']}")
    typer.echo(f"Venues: {s['venue_count']}")

    enriched = conn.execute("SELECT COUNT(*) FROM papers WHERE openalex_id IS NOT NULL").fetchone()[0]
    total_authorships = conn.execute("SELECT COUNT(*) FROM authorships").fetchone()[0]
    typer.echo(f"Enriched (OpenAlex): {enriched} ({enriched * 100 // s['total']}%)")
    typer.echo(f"Authorships: {total_authorships}")

    with_abstract = conn.execute("SELECT COUNT(*) FROM papers WHERE abstract IS NOT NULL").fetchone()[0]
    typer.echo(f"With abstract: {with_abstract} ({with_abstract * 100 // s['total']}%)")

    with_cluster = conn.execute("SELECT COUNT(*) FROM papers WHERE cluster_path IS NOT NULL").fetchone()[0]
    try:
        cluster_count = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]
        typer.echo(f"Clusters: {cluster_count}, assigned: {with_cluster}")
    except Exception:
        pass

    if s["by_year"]:
        typer.echo("\nBy year:")
        for year, count in s["by_year"][:10]:
            typer.echo(f"  {year}: {count}")

    venues = repo.list_venues()
    if venues:
        typer.echo("\nVenues:")
        for v in venues:
            typer.echo(f"  {v['venue']}: {v['count']} papers")

    db.close()
