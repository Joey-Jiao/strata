from pathlib import Path

import typer

from strata.modules.corpus import create_store
from . import app, get_config


@app.command()
def doctor():
    """Diagnose corpus data quality issues."""
    config = get_config()
    db, repo = create_store(config)
    conn = db.connection()

    issues = []
    total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]

    no_abstract = conn.execute("SELECT COUNT(*) FROM papers WHERE abstract IS NULL").fetchone()[0]
    if no_abstract:
        issues.append(f"No abstract: {no_abstract} papers ({no_abstract * 100 // total}%) — cannot embed")

    has_doi_no_enrich = conn.execute(
        "SELECT COUNT(*) FROM papers WHERE doi IS NOT NULL AND openalex_id IS NULL AND enriched_at IS NOT NULL"
    ).fetchone()[0]
    if has_doi_no_enrich:
        issues.append(f"Has DOI but no OpenAlex match: {has_doi_no_enrich} — may retry with enrich")

    not_enriched = conn.execute("SELECT COUNT(*) FROM papers WHERE enriched_at IS NULL").fetchone()[0]
    if not_enriched:
        issues.append(f"Not enriched: {not_enriched} — run 'ingest --only enrich'")

    with_abstract = conn.execute("SELECT COUNT(*) FROM papers WHERE abstract IS NOT NULL").fetchone()[0]
    no_cluster = conn.execute("SELECT COUNT(*) FROM papers WHERE abstract IS NOT NULL AND cluster_path IS NULL").fetchone()[0]
    if no_cluster:
        issues.append(f"Has abstract but no cluster: {no_cluster} — run 'ingest --only cluster'")

    model_path = Path(config.get("corpus.store.cluster_model", "~/workspace/resource/corpus/cluster_model.pkl")).expanduser()
    if model_path.exists():
        import os
        model_age = os.path.getmtime(model_path)
        latest_import = conn.execute("SELECT MAX(imported_at) FROM papers").fetchone()[0]
        if latest_import:
            from datetime import datetime
            model_dt = datetime.fromtimestamp(model_age)
            typer.echo(f"Cluster model: {model_dt.strftime('%Y-%m-%d %H:%M')}")
    else:
        issues.append("No cluster model — run 'ingest --only cluster --retrain'")

    orphan_authorships = conn.execute("""
        SELECT COUNT(*) FROM authorships a
        WHERE NOT EXISTS (SELECT 1 FROM papers p WHERE p.paper_id = a.paper_id)
    """).fetchone()[0]
    if orphan_authorships:
        issues.append(f"Orphan authorships (no matching paper): {orphan_authorships}")

    vectors_path = Path(config.get("corpus.store.vectors", "~/workspace/resource/corpus/vectors.npz")).expanduser()
    if vectors_path.exists():
        import numpy as np
        data = np.load(vectors_path, allow_pickle=True)
        vec_count = len(data["paper_ids"])
        typer.echo(f"Vector cache: {vec_count} vectors")
        if vec_count < with_abstract:
            issues.append(f"Vector cache behind: {vec_count}/{with_abstract} — run 'ingest --only embed'")
    else:
        issues.append("No vector cache — run 'ingest --only embed'")

    if not issues:
        typer.echo("\nNo issues found.")
    else:
        typer.echo(f"\nIssues ({len(issues)}):")
        for issue in issues:
            typer.echo(f"  - {issue}")

    db.close()
