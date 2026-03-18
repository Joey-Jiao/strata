import json
import sqlite3

import typer

from strata.modules.corpus import create_store
from strata.modules.corpus.common.venues import short_venue
from . import app, get_config


def _get_conn(config):
    db, repo = create_store(config)
    return db, db.connection()


def _show_node(conn, cluster_id, page=0, page_size=20):
    row = conn.execute(
        "SELECT * FROM clusters WHERE cluster_id = ?", (cluster_id,)
    ).fetchone()
    if not row:
        typer.echo(f"Cluster not found: {cluster_id}")
        return

    kw = json.loads(row["keywords"]) if row["keywords"] else []

    path_parts = cluster_id.split(".")
    path_labels = []
    acc = ""
    for p in path_parts:
        acc = f"{acc}.{p}" if acc else p
        r = conn.execute("SELECT label FROM clusters WHERE cluster_id = ?", (acc,)).fetchone()
        if r:
            path_labels.append(r["label"])

    typer.echo(f"\n{'=' * 70}")
    typer.echo(f"[{cluster_id}] {row['label']} ({row['paper_count']} papers)")
    if len(path_labels) > 1:
        typer.echo(f"  Path: {' → '.join(path_labels)}")
    typer.echo(f"  Keywords: {', '.join(kw[:8])}")

    venues = conn.execute("""
        SELECT venue, COUNT(*) as cnt FROM papers
        WHERE cluster_path LIKE ? AND venue IS NOT NULL
        GROUP BY venue ORDER BY cnt DESC LIMIT 5
    """, (f"{cluster_id}%",)).fetchall()
    if venues:
        venue_str = ", ".join(f"{short_venue(v['venue'])} ({v['cnt']})" for v in venues)
        typer.echo(f"  Venues: {venue_str}")

    children = conn.execute(
        "SELECT cluster_id, label, paper_count FROM clusters WHERE parent_id = ? ORDER BY paper_count DESC",
        (cluster_id,)
    ).fetchall()

    if children:
        typer.echo(f"\n  Subtopics ({len(children)}):")
        for c in children:
            suffix = c["cluster_id"].rsplit(".", 1)[-1]
            typer.echo(f"    [{suffix:>2}] {c['label']} ({c['paper_count']})")
    else:
        total = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE cluster_path = ?", (cluster_id,)
        ).fetchone()[0]
        offset = page * page_size
        papers = conn.execute("""
            SELECT title, year, venue, citation_count FROM papers
            WHERE cluster_path = ?
            ORDER BY citation_count DESC
            LIMIT ? OFFSET ?
        """, (cluster_id, page_size, offset)).fetchall()

        if papers:
            typer.echo(f"\n  Papers ({offset + 1}-{offset + len(papers)} of {total}):")
            for p in papers:
                v = short_venue(p["venue"])
                cite = p["citation_count"] or 0
                typer.echo(f"    {p['year'] or '?'} {v:<7} [{cite:>4}] {p['title'][:55]}")


@app.command()
def explore(start: str = typer.Argument("", help="Starting cluster ID (empty for root)")):
    """Interactively explore the cluster tree.

    Commands: id to enter child, u/up, n/next page, b/back page, q quit.
    """
    config = get_config()
    db, conn = _get_conn(config)
    conn.row_factory = sqlite3.Row

    current = start if start else None
    page = 0

    while True:
        if current is None:
            roots = conn.execute(
                "SELECT cluster_id, label, paper_count FROM clusters WHERE level = 0 ORDER BY paper_count DESC"
            ).fetchall()
            typer.echo(f"\n{'=' * 70}")
            typer.echo("Root clusters:")
            for r in roots:
                typer.echo(f"  [{r['cluster_id']:>2}] {r['label']} ({r['paper_count']})")
        else:
            _show_node(conn, current, page=page)

        typer.echo("")
        try:
            cmd = input("→ ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("q", "quit", "exit"):
            break
        elif cmd in ("u", "up", ".."):
            if current is None:
                continue
            parts = current.rsplit(".", 1)
            current = parts[0] if len(parts) > 1 else None
            page = 0
        elif cmd in ("n", "next"):
            page += 1
        elif cmd in ("b", "back", "prev"):
            page = max(0, page - 1)
        elif conn.execute("SELECT 1 FROM clusters WHERE cluster_id = ?", (cmd,)).fetchone():
            current = cmd
            page = 0
        elif current and conn.execute("SELECT 1 FROM clusters WHERE cluster_id = ?", (f"{current}.{cmd}",)).fetchone():
            current = f"{current}.{cmd}"
            page = 0
        elif cmd:
            typer.echo(f"Unknown: {cmd}")

    db.close()
