from pathlib import Path

import typer

from strata.modules.paper.common import create_store
from strata.modules.paper.export import BibTeXExporter
from . import app, get_config


@app.command(name="export")
def export_cmd(
    keys: str = typer.Argument(default=None, help="Citation keys (comma-separated)"),
    output: Path = typer.Option(default=None, help="Output file"),
    all_papers: bool = typer.Option(default=False, help="Export all papers"),
):
    """Export papers to BibTeX format."""
    config = get_config()
    db, files, repo = create_store(config)
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
