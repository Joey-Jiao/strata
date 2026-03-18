import typer

from strata.modules.paper.common import create_store
from . import app, get_config


@app.command()
def doctor():
    """Diagnose paper library issues."""
    config = get_config()
    db, files, repo = create_store(config)

    all_papers = repo.list_all()
    db_keys = {p.citation_key for p in all_papers}
    folder_keys = set(files.list_folders())

    issues = []

    orphan_folders = folder_keys - db_keys
    if orphan_folders:
        issues.append(("Orphan folders (PDF exists, no DB record)", sorted(orphan_folders)))

    missing_pdfs = [p.citation_key for p in all_papers if p.pdf_path and not files.exists(p.citation_key)]
    if missing_pdfs:
        issues.append(("Missing PDFs (DB says exists, file missing)", sorted(missing_pdfs)))

    no_abstract = [p.citation_key for p in all_papers if not p.abstract]
    if no_abstract:
        issues.append((f"Papers without abstract ({len(no_abstract)})", no_abstract[:10]))

    no_doi = [p.citation_key for p in all_papers if not p.doi]
    if no_doi:
        issues.append((f"Papers without DOI ({len(no_doi)})", no_doi[:10]))

    if not issues:
        typer.echo("No issues found.")
        db.close()
        return

    for title, items in issues:
        typer.echo(f"\n{title}:")
        for item in items:
            typer.echo(f"  {item}")
        if len(items) < len([p for p in all_papers]):
            remaining = len([i for i in items])
            if title.startswith("Papers"):
                typer.echo(f"  ... showing first 10")

    db.close()
