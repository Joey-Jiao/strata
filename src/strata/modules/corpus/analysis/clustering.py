import json
import pickle
import sqlite3
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances_argmin_min
from tqdm import tqdm
from umap import UMAP

L0_LABELS = {
    "0": "NLP & LLMs",
    "1": "ML Systems & AutoML",
    "2": "Vision-Language Models",
    "3": "Federated & Distributed Learning",
    "4": "Graph Neural Networks & Time Series",
    "5": "Security: Deepfake, Watermark, Adversarial",
    "6": "Applied AI: Healthcare, Misinformation",
    "7": "3D Vision: Depth, Tracking, NeRF",
    "8": "CNN & Efficient Architectures",
    "9": "Database Systems & Data Management",
    "10": "RL, Optimization & Decision Making",
    "11": "Image Generation & Restoration",
    "12": "Object Detection & Recognition",
    "13": "ML Theory: Fairness, Tabular, Calibration",
    "14": "Recommender Systems & Information Retrieval",
}


class ClusteringPipeline:
    def __init__(
        self,
        db_path: str,
        vectors_path: str,
        model_path: str,
        umap_n_neighbors: int = 15,
        umap_n_components: int = 50,
        target_cluster_size: int = 200,
        min_cluster_size: int = 30,
        max_k: int = 15,
        max_depth: int = 6,
        threshold_margin: float = 1.5,
    ):
        self._db_path = str(Path(db_path).expanduser())
        self._vectors_path = str(Path(vectors_path).expanduser())
        self._model_path = str(Path(model_path).expanduser())
        self._umap_n_neighbors = umap_n_neighbors
        self._umap_n_components = umap_n_components
        self._target_size = target_cluster_size
        self._min_size = min_cluster_size
        self._max_k = max_k
        self._max_depth = max_depth
        self._threshold_margin = threshold_margin

    def _load_data(self) -> tuple[list[str], np.ndarray, list[str]]:
        data = np.load(self._vectors_path, allow_pickle=True)
        paper_ids = data["paper_ids"].tolist()
        vectors = data["vectors"]

        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        id_set = set(paper_ids)
        rows = conn.execute("SELECT paper_id, title, abstract FROM papers").fetchall()
        doc_map = {}
        for r in rows:
            if r["paper_id"] in id_set:
                title = r["title"] or ""
                abstract = r["abstract"] or ""
                doc_map[r["paper_id"]] = f"{title}. {abstract}" if abstract else title
        conn.close()

        docs = [doc_map.get(pid, "") for pid in paper_ids]
        return paper_ids, vectors, docs

    def _choose_k(self, n: int) -> int:
        return max(2, min(n // self._target_size, self._max_k))

    def _extract_labels(self, docs: list[str], labels: np.ndarray, n_keywords: int = 8) -> dict[int, list[str]]:
        unique_labels = sorted(set(labels))
        cluster_docs = {label: [] for label in unique_labels}
        for doc, label in zip(docs, labels):
            cluster_docs[label].append(doc)

        all_docs_flat = [" ".join(cluster_docs[l]) for l in sorted(cluster_docs)]
        if not all_docs_flat:
            return {}

        tfidf = TfidfVectorizer(stop_words="english", max_features=20000, max_df=0.5)
        tfidf_matrix = tfidf.fit_transform(all_docs_flat)
        feature_names = tfidf.get_feature_names_out()

        result = {}
        for i, label in enumerate(sorted(cluster_docs)):
            scores = tfidf_matrix[i].toarray().flatten()
            top_indices = scores.argsort()[-n_keywords:][::-1]
            result[label] = [feature_names[j] for j in top_indices]
        return result

    def _compute_threshold(self, vectors: np.ndarray, kmeans: KMeans) -> float:
        _, distances = pairwise_distances_argmin_min(vectors, kmeans.cluster_centers_)
        return float(np.max(distances) * self._threshold_margin)

    def _recursive_cluster(
        self,
        vectors: np.ndarray,
        paper_ids: list[str],
        docs: list[str],
        parent_id: str,
        level: int,
        clusters: dict,
        paper_map: dict,
        tree_nodes: dict,
        pbar: tqdm,
    ):
        n = len(paper_ids)
        if n < self._min_size * 2 or level >= self._max_depth:
            pbar.update(n)
            return

        k = self._choose_k(n)
        if k < 2:
            pbar.update(n)
            return

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(vectors)
        keywords = self._extract_labels(docs, labels)
        threshold = self._compute_threshold(vectors, kmeans)

        tree_nodes[parent_id if parent_id else "root"] = {
            "kmeans": kmeans,
            "threshold": threshold,
            "level": level,
        }

        for label in range(k):
            mask = labels == label
            count = int(mask.sum())
            if count == 0:
                continue

            cid = f"{parent_id}.{label}" if parent_id else str(label)
            kw = keywords.get(label, [])

            display_label = "_".join(kw[:4])

            clusters[cid] = {
                "parent_id": parent_id if parent_id else None,
                "level": level,
                "label": display_label,
                "keywords": kw,
                "paper_count": count,
            }

            sub_indices = np.where(mask)[0]
            for idx in sub_indices:
                paper_map[paper_ids[idx]] = cid

            sub_vectors = vectors[mask]
            sub_ids = [paper_ids[i] for i in sub_indices]
            sub_docs = [docs[i] for i in sub_indices]

            if count >= self._min_size * 2:
                self._recursive_cluster(
                    sub_vectors, sub_ids, sub_docs,
                    cid, level + 1, clusters, paper_map, tree_nodes, pbar,
                )
            else:
                pbar.update(count)

    def run(self) -> dict:
        paper_ids, vectors, docs = self._load_data()

        print("UMAP dimensionality reduction...", flush=True)
        umap_model = UMAP(
            n_neighbors=self._umap_n_neighbors,
            n_components=self._umap_n_components,
            metric="cosine",
            random_state=42,
        )
        reduced = umap_model.fit_transform(vectors)

        clusters = {}
        paper_map = {}
        tree_nodes = {}

        print("Recursive clustering...", flush=True)
        pbar = tqdm(total=len(paper_ids), desc="Clustering")
        self._recursive_cluster(reduced, paper_ids, docs, "", 0, clusters, paper_map, tree_nodes, pbar)
        pbar.close()

        self._write_results(clusters, paper_map)

        model = {
            "umap": umap_model,
            "tree": tree_nodes,
            "labels": {cid: info["label"] for cid, info in clusters.items()},
        }
        Path(self._model_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._model_path, "wb") as f:
            pickle.dump(model, f)
        print(f"Model saved to {self._model_path}", flush=True)

        level_counts = {}
        max_level = 0
        for c in clusters.values():
            l = c["level"]
            level_counts[l] = level_counts.get(l, 0) + 1
            max_level = max(max_level, l)

        return {
            "total_papers": len(paper_ids),
            "total_clusters": len(clusters),
            "max_depth": max_level,
            "by_level": level_counts,
        }

    def _write_results(self, clusters: dict, paper_map: dict):
        conn = sqlite3.connect(self._db_path, timeout=30)

        conn.execute("DROP TABLE IF EXISTS clusters")
        conn.execute("""
            CREATE TABLE clusters (
                cluster_id   TEXT PRIMARY KEY,
                parent_id    TEXT,
                level        INTEGER,
                label        TEXT,
                keywords     TEXT,
                paper_count  INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clusters_parent ON clusters(parent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clusters_level ON clusters(level)")

        for cid, info in clusters.items():
            conn.execute(
                "INSERT INTO clusters (cluster_id, parent_id, level, label, keywords, paper_count) VALUES (?, ?, ?, ?, ?, ?)",
                (cid, info["parent_id"], info["level"], info["label"], json.dumps(info["keywords"]), info["paper_count"]),
            )

        existing = {r[1] for r in conn.execute("PRAGMA table_info(papers)")}
        if "cluster_path" not in existing:
            conn.execute("ALTER TABLE papers ADD COLUMN cluster_path TEXT")

        for pid, cid in paper_map.items():
            conn.execute("UPDATE papers SET cluster_path = ? WHERE paper_id = ?", (cid, pid))

        conn.commit()
        conn.close()
