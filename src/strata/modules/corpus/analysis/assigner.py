import pickle
import sqlite3
from pathlib import Path

import numpy as np
from sklearn.metrics import pairwise_distances_argmin_min


class ClusterAssigner:
    def __init__(self, model_path: str, db_path: str, vectors_path: str):
        self._model_path = str(Path(model_path).expanduser())
        self._db_path = str(Path(db_path).expanduser())
        self._vectors_path = str(Path(vectors_path).expanduser())

        with open(self._model_path, "rb") as f:
            model = pickle.load(f)
        self._umap = model["umap"]
        self._tree = model["tree"]
        self._labels = model["labels"]

    def _traverse(self, vector: np.ndarray) -> tuple[str, bool]:
        current_id = "root"
        cluster_path = ""

        while current_id in self._tree:
            node = self._tree[current_id]
            kmeans = node["kmeans"]
            threshold = node["threshold"]

            label = kmeans.predict(vector.reshape(1, -1))[0]
            _, dist = pairwise_distances_argmin_min(vector.reshape(1, -1), kmeans.cluster_centers_)
            distance = dist[0]

            if distance > threshold:
                return cluster_path, True

            new_path = f"{cluster_path}.{label}" if cluster_path else str(label)
            cluster_path = new_path
            current_id = new_path

        return cluster_path, False

    def assign(self, embeddings: np.ndarray, paper_ids: list[str]) -> list[tuple[str, str, bool]]:
        reduced = self._umap.transform(embeddings)

        results = []
        for i, pid in enumerate(paper_ids):
            cluster_path, is_emerging = self._traverse(reduced[i])
            results.append((pid, cluster_path, is_emerging))
        return results

    def assign_new(self) -> dict:
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row

        assigned_ids = {r["paper_id"] for r in conn.execute(
            "SELECT paper_id FROM papers WHERE cluster_path IS NOT NULL"
        )}

        data = np.load(self._vectors_path, allow_pickle=True)
        all_ids = data["paper_ids"].tolist()
        all_vectors = data["vectors"]

        pending = [(i, pid) for i, pid in enumerate(all_ids) if pid not in assigned_ids]
        if not pending:
            conn.close()
            return {"assigned": 0, "emerging": 0}

        indices = [i for i, _ in pending]
        pids = [pid for _, pid in pending]
        vectors = all_vectors[indices]

        results = self.assign(vectors, pids)

        assigned = 0
        emerging = 0
        for pid, cluster_path, is_emerging in results:
            conn.execute(
                "UPDATE papers SET cluster_path = ? WHERE paper_id = ?",
                (cluster_path, pid),
            )
            if is_emerging:
                emerging += 1
            else:
                assigned += 1

        conn.commit()
        conn.close()
        return {"assigned": assigned, "emerging": emerging}
