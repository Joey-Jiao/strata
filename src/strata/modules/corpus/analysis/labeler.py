import json
import os
import pickle
import sqlite3
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

SYSTEM_PROMPT = """You are a research taxonomy labeler. Given a cluster of academic papers, generate a concise theme label (3-7 words) that captures the core research topic.

Rules:
- Be specific enough to distinguish from sibling clusters
- Be general enough to cover all papers in the cluster
- Use standard academic terminology
- No acronyms unless universally known (e.g., GAN, NLP, RL)
- Output ONLY the label, nothing else"""


def _build_prompt(cluster: dict) -> str:
    parts = []
    if cluster.get("parent_label"):
        parts.append(f"Parent topic: \"{cluster['parent_label']}\"")
    if cluster.get("sibling_labels"):
        parts.append(f"Sibling topics: {cluster['sibling_labels']}")
    parts.append(f"This cluster ({cluster['paper_count']} papers):")
    if cluster.get("top_titles"):
        parts.append("  Top papers:")
        for t in cluster["top_titles"]:
            parts.append(f"    - {t}")
    if cluster.get("keywords"):
        parts.append(f"  Keywords: {', '.join(cluster['keywords'][:8])}")
    if cluster.get("top_venues"):
        parts.append(f"  Top venues: {cluster['top_venues']}")
    return "\n".join(parts)


class ClusterLabeler:
    def __init__(self, db_path: str, model_path: str, batch_size: int = 20):
        self._db_path = str(Path(db_path).expanduser())
        self._model_path = str(Path(model_path).expanduser())
        self._batch_size = batch_size
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _load_clusters(self) -> dict[str, dict]:
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row

        clusters = {}
        for row in conn.execute("SELECT * FROM clusters ORDER BY level, cluster_id"):
            cid = row["cluster_id"]
            keywords = json.loads(row["keywords"]) if row["keywords"] else []

            top_titles = [r[0] for r in conn.execute("""
                SELECT title FROM papers
                WHERE cluster_path LIKE ? AND title IS NOT NULL
                ORDER BY citation_count DESC LIMIT 5
            """, (f"{cid}%",))]

            venue_rows = conn.execute("""
                SELECT venue, COUNT(*) as cnt FROM papers
                WHERE cluster_path LIKE ? AND venue IS NOT NULL
                GROUP BY venue ORDER BY cnt DESC LIMIT 3
            """, (f"{cid}%",)).fetchall()
            top_venues = ", ".join(f"{r['venue'][:30]} ({r['cnt']})" for r in venue_rows)

            parent_id = row["parent_id"]
            siblings = [r["label"] for r in conn.execute(
                "SELECT label FROM clusters WHERE parent_id = ? AND cluster_id != ?",
                (parent_id, cid),
            )] if parent_id else []

            parent_label = None
            if parent_id:
                p = conn.execute("SELECT label FROM clusters WHERE cluster_id = ?", (parent_id,)).fetchone()
                parent_label = p["label"] if p else None

            clusters[cid] = {
                "cluster_id": cid,
                "level": row["level"],
                "parent_id": parent_id,
                "parent_label": parent_label,
                "sibling_labels": siblings[:8],
                "paper_count": row["paper_count"],
                "keywords": keywords,
                "top_titles": top_titles,
                "top_venues": top_venues,
                "current_label": row["label"],
            }

        conn.close()
        return clusters

    def _generate_labels(self, prompts: list[str]) -> list[str]:
        labels = []
        for prompt in prompts:
            resp = self._client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            label = resp.choices[0].message.content.strip().strip('"').strip("'")
            labels.append(label)
        return labels

    def run(self) -> dict:
        from .clustering import L0_LABELS

        clusters = self._load_clusters()
        levels = sorted(set(c["level"] for c in clusters.values()), reverse=True)

        new_labels = {}
        for cid, label in L0_LABELS.items():
            new_labels[cid] = label

        for level in tqdm(levels, desc="Levels"):
            level_clusters = [c for c in clusters.values() if c["level"] == level and c["cluster_id"] not in new_labels]

            for c in level_clusters:
                if c["parent_id"] and c["parent_id"] in new_labels:
                    c["parent_label"] = new_labels[c["parent_id"]]
                sibling_ids = [s["cluster_id"] for s in clusters.values()
                               if s["parent_id"] == c["parent_id"] and s["cluster_id"] != c["cluster_id"]]
                c["sibling_labels"] = [new_labels.get(sid, clusters[sid]["current_label"]) for sid in sibling_ids[:8]]

            for i in tqdm(range(0, len(level_clusters), self._batch_size),
                         desc=f"L{level}", leave=False):
                batch = level_clusters[i:i + self._batch_size]
                prompts = [_build_prompt(c) for c in batch]
                labels = self._generate_labels(prompts)
                for c, label in zip(batch, labels):
                    new_labels[c["cluster_id"]] = label

        self._write_labels(new_labels)
        return {"labeled": len(new_labels)}

    def _write_labels(self, labels: dict[str, str]):
        conn = sqlite3.connect(self._db_path, timeout=30)
        for cid, label in labels.items():
            conn.execute("UPDATE clusters SET label = ? WHERE cluster_id = ?", (label, cid))
        conn.commit()
        conn.close()

        if Path(self._model_path).exists():
            with open(self._model_path, "rb") as f:
                model = pickle.load(f)
            model["labels"] = labels
            with open(self._model_path, "wb") as f:
                pickle.dump(model, f)
