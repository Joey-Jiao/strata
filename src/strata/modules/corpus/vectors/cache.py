from pathlib import Path

import numpy as np


class VectorCache:
    def __init__(self, path: str):
        self._path = Path(path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._paper_ids: list[str] = []
        self._vectors: np.ndarray | None = None
        self._load()

    def _load(self):
        if not self._path.exists():
            return
        data = np.load(self._path, allow_pickle=True)
        self._paper_ids = data["paper_ids"].tolist()
        self._vectors = data["vectors"]

    def save(self):
        if self._vectors is None or len(self._paper_ids) == 0:
            return
        np.savez(
            self._path,
            paper_ids=np.array(self._paper_ids, dtype=object),
            vectors=self._vectors,
        )

    @property
    def paper_ids(self) -> list[str]:
        return self._paper_ids

    @property
    def vectors(self) -> np.ndarray | None:
        return self._vectors

    def existing_ids(self) -> set[str]:
        return set(self._paper_ids)

    def append(self, paper_ids: list[str], vectors: list[list[float]]):
        new_vectors = np.array(vectors, dtype=np.float32)
        if self._vectors is None:
            self._vectors = new_vectors
        else:
            self._vectors = np.vstack([self._vectors, new_vectors])
        self._paper_ids.extend(paper_ids)

    def __len__(self) -> int:
        return len(self._paper_ids)
