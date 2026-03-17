from pathlib import Path

from pymilvus import MilvusClient

from ..configs import ConfigService


class MilvusService:
    def __init__(self, config: ConfigService):
        uri = config.get("base.milvus.uri", "./milvus.db")
        uri = str(Path(uri).expanduser())
        Path(uri).parent.mkdir(parents=True, exist_ok=True)
        self._client = MilvusClient(uri=uri)

    @property
    def client(self) -> MilvusClient:
        return self._client

    def close(self):
        self._client.close()
