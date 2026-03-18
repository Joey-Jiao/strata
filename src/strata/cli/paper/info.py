import typer

from strata.modules.paper.common import create_store
from . import app, get_config


@app.command()
def info(key: str):
    """Show details of a paper."""
    config = get_config()
    db, files, repo = create_store(config)

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
