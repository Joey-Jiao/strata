from typing import Optional

import typer
from tqdm import tqdm

from strata.modules.corpus import (
    create_store, create_importer, create_enricher,
    create_embedding_generator, create_vector_store, create_vector_cache,
    create_clustering_pipeline, create_cluster_assigner, create_cluster_labeler,
)
from . import app, get_config


def _run_import(config, venue: str, year: int):
    db, repo, importer = create_importer(config)
    try:
        count = importer.import_venue_year(venue, year)
        typer.echo(f"Imported {count} papers.")
    finally:
        db.close()


def _run_enrich(config):
    enricher = create_enricher(config)
    stats = enricher.enrich()
    if stats.get("total", 0) == 0:
        typer.echo("Nothing to enrich.")
        return
    for tier, count in stats.items():
        typer.echo(f"  {tier}: {count}")


def _run_embed(config):
    db, repo = create_store(config)
    cache = create_vector_cache(config)
    generator = create_embedding_generator(config)

    try:
        if len(cache) == 0:
            vector_store = create_vector_store(config)
            milvus_count = vector_store.count()
            if milvus_count > 0:
                typer.echo(f"Backfilling cache from Milvus ({milvus_count} vectors)...")
                pids, vecs = vector_store.export_all()
                cache.append(pids, vecs)
                cache.save()
                typer.echo(f"Cache backfilled: {len(cache)} vectors")
            vector_store.close()

        existing = cache.existing_ids()
        conn = db.connection()
        cursor = conn.execute(
            "SELECT paper_id, title, abstract FROM papers WHERE abstract IS NOT NULL"
        )
        pending = [(r["paper_id"], r["title"], r["abstract"]) for r in cursor if r["paper_id"] not in existing]

        if not pending:
            typer.echo(f"Nothing to embed. ({len(cache)} vectors in cache)")
            return

        typer.echo(f"Embedding {len(pending)} papers (skipped {len(existing)} existing)...")
        texts = [f"{title}\n{abstract}" for _, title, abstract in pending]
        paper_ids = [pid for pid, _, _ in pending]

        vectors = generator.generate_batch(texts)

        cache.append(paper_ids, vectors)
        cache.save()
        typer.echo(f"Saved to cache ({len(cache)} total vectors)")
    finally:
        db.close()

    typer.echo("Writing to vector store...")
    vector_store = create_vector_store(config)
    batch_size = 500
    for i in tqdm(range(0, len(paper_ids), batch_size), desc="Inserting"):
        vector_store.insert(paper_ids[i:i + batch_size], vectors[i:i + batch_size])
    typer.echo(f"Done. Total in store: {vector_store.count()}")
    vector_store.close()


def _run_cluster(config, retrain: bool = False):
    from pathlib import Path
    model_path = config.get("corpus.store.cluster_model", "~/workspace/resource/corpus/cluster_model.pkl")
    model_exists = Path(model_path).expanduser().exists()

    if model_exists and not retrain:
        typer.echo("Assigning new papers to existing clusters...")
        assigner = create_cluster_assigner(config)
        stats = assigner.assign_new()
        typer.echo(f"Done. Assigned: {stats['assigned']}, emerging: {stats['emerging']}")
    else:
        pipeline = create_clustering_pipeline(config)
        typer.echo("Training cluster model (UMAP + recursive K-Means)...")
        stats = pipeline.run()
        by_level = stats.get("by_level", {})
        level_str = ", ".join(f"L{k}: {v}" for k, v in sorted(by_level.items()))
        typer.echo(f"Done. {stats['total_clusters']} clusters ({level_str})")

        typer.echo("Generating cluster labels...")
        labeler = create_cluster_labeler(config)
        label_stats = labeler.run()
        typer.echo(f"Labeled {label_stats['labeled']} clusters.")


@app.command()
def ingest(
    venue: Optional[str] = typer.Argument(None, help="Venue name (e.g., NeurIPS, ICML)"),
    year: Optional[int] = typer.Argument(None, help="Publication year"),
    only: Optional[str] = typer.Option(None, help="Run only: import, enrich, embed, or cluster"),
    retrain: bool = typer.Option(False, "--retrain", help="Force retrain cluster model"),
):
    """Ingest papers: import → enrich → embed → cluster.

    Full pipeline (requires venue+year):
      strata corpus ingest NeurIPS 2025

    Single step:
      strata corpus ingest --only enrich
      strata corpus ingest --only embed
      strata corpus ingest --only cluster
      strata corpus ingest --only cluster --retrain
    """
    config = get_config()

    if only:
        if only == "import":
            if not venue or not year:
                typer.echo("import requires venue and year arguments.")
                raise typer.Exit(1)
            _run_import(config, venue, year)
        elif only == "enrich":
            _run_enrich(config)
        elif only == "embed":
            _run_embed(config)
        elif only == "cluster":
            _run_cluster(config, retrain=retrain)
        elif only == "label":
            typer.echo("Generating cluster labels...")
            labeler = create_cluster_labeler(config)
            label_stats = labeler.run()
            typer.echo(f"Labeled {label_stats['labeled']} clusters.")
        else:
            typer.echo(f"Unknown step: {only}. Use: import, enrich, embed, cluster, label")
            raise typer.Exit(1)
        return

    if not venue or not year:
        typer.echo("Full ingest requires venue and year. Use --only for single steps.")
        raise typer.Exit(1)

    typer.echo(f"=== Import: {venue} {year} ===")
    _run_import(config, venue, year)

    typer.echo("=== Enrich ===")
    _run_enrich(config)

    typer.echo("=== Embed ===")
    _run_embed(config)

    typer.echo("=== Cluster ===")
    _run_cluster(config)
