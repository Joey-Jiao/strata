import os

from openai import OpenAI
from tqdm import tqdm


class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-3-large", dimensions: int = 3072,
                 batch_size: int = 100):
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def generate(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            input=texts,
            model=self._model,
            dimensions=self._dimensions,
        )
        return [item.embedding for item in response.data]

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for i in tqdm(range(0, len(texts), self._batch_size), desc="Embedding"):
            batch = texts[i:i + self._batch_size]
            all_embeddings.extend(self.generate(batch))
        return all_embeddings
