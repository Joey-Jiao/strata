from pathlib import Path

from pymilvus import MilvusClient, DataType

COLLECTION = "corpus_papers"


class VectorStore:
    def __init__(self, db_path: str, dimensions: int = 3072):
        self._db_path = str(Path(db_path).expanduser())
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._dimensions = dimensions
        self._client = MilvusClient(uri=self._db_path)
        self._ensure_collection()

    def _ensure_collection(self):
        if self._client.has_collection(COLLECTION):
            return
        schema = self._client.create_schema()
        schema.add_field("paper_id", DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self._dimensions)

        index_params = self._client.prepare_index_params()
        index_params.add_index(field_name="vector", metric_type="COSINE", index_type="AUTOINDEX")

        self._client.create_collection(
            collection_name=COLLECTION,
            schema=schema,
            index_params=index_params,
        )

    def existing_ids(self) -> set[str]:
        ids = set()
        last_id = ""
        batch = 10000
        while True:
            filter_expr = f'paper_id > "{last_id}"' if last_id else ""
            results = self._client.query(
                collection_name=COLLECTION,
                filter=filter_expr,
                output_fields=["paper_id"],
                limit=batch,
            )
            if not results:
                break
            batch_ids = sorted(r["paper_id"] for r in results)
            ids.update(batch_ids)
            last_id = batch_ids[-1]
            if len(results) < batch:
                break
        return ids

    def insert(self, paper_ids: list[str], vectors: list[list[float]]):
        data = [{"paper_id": pid, "vector": vec} for pid, vec in zip(paper_ids, vectors)]
        self._client.upsert(collection_name=COLLECTION, data=data)

    def search(self, query_vector: list[float], limit: int = 20, paper_ids: list[str] | None = None) -> list[dict]:
        search_params = {"metric_type": "COSINE"}
        filter_expr = ""
        if paper_ids:
            ids_str = ", ".join(f'"{pid}"' for pid in paper_ids)
            filter_expr = f"paper_id in [{ids_str}]"

        results = self._client.search(
            collection_name=COLLECTION,
            data=[query_vector],
            limit=limit,
            output_fields=["paper_id"],
            search_params=search_params,
            filter=filter_expr if filter_expr else None,
        )
        return [{"paper_id": hit["entity"]["paper_id"], "score": hit["distance"]} for hit in results[0]]

    def export_all(self) -> tuple[list[str], list[list[float]]]:
        paper_ids = []
        vectors = []
        last_id = ""
        batch = 500
        while True:
            filter_expr = f'paper_id > "{last_id}"' if last_id else ""
            results = self._client.query(
                collection_name=COLLECTION,
                filter=filter_expr,
                output_fields=["paper_id", "vector"],
                limit=batch,
            )
            if not results:
                break
            results.sort(key=lambda r: r["paper_id"])
            paper_ids.extend(r["paper_id"] for r in results)
            vectors.extend(r["vector"] for r in results)
            last_id = results[-1]["paper_id"]
            if len(results) < batch:
                break
        return paper_ids, vectors

    def count(self) -> int:
        stats = self._client.get_collection_stats(COLLECTION)
        return stats.get("row_count", 0)

    def close(self):
        self._client.close()
