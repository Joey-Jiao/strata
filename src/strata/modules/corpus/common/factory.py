import os
from pathlib import Path

from strata.base.configs import ConfigService


def create_store(config: ConfigService):
    from ..store import CorpusDatabase, CorpusRepository

    db_path = config.get("corpus.store.database", "~/workspace/resource/corpus/main.sqlite")
    db = CorpusDatabase(db_path)
    db.initialize()
    repo = CorpusRepository(db)
    return db, repo


def create_importer(config: ConfigService):
    from ..sources import S2Importer

    db, repo = create_store(config)
    api_key = config.get("corpus.s2.api_key", None)
    timeout = config.get("corpus.s2.timeout", 60)
    importer = S2Importer(repo, api_key, timeout=timeout)
    return db, repo, importer


def create_enricher(config: ConfigService):
    from ..sources import OpenAlexEnricher

    db_path = config.get("corpus.store.database", "~/workspace/resource/corpus/main.sqlite")
    db_path = str(Path(db_path).expanduser())
    api_key = os.getenv("OPENALEX_API_KEY") or config.get("corpus.openalex.api_key", None)
    batch_size = config.get("corpus.openalex.batch_size", 50)
    fuzzy_threshold = config.get("corpus.openalex.fuzzy_threshold", 0.85)
    return OpenAlexEnricher(db_path, api_key, batch_size=batch_size, fuzzy_threshold=fuzzy_threshold)


def create_embedding_generator(config: ConfigService):
    from ..sources import EmbeddingGenerator

    model = config.get("corpus.embedding.model", "text-embedding-3-large")
    dimensions = config.get("corpus.embedding.dimensions", 3072)
    batch_size = config.get("corpus.embedding.batch_size", 100)
    return EmbeddingGenerator(model=model, dimensions=dimensions, batch_size=batch_size)


def create_vector_store(config: ConfigService):
    from ..vectors import VectorStore

    db_path = config.get("corpus.store.embedding", "~/workspace/resource/corpus/embedding.db")
    dimensions = config.get("corpus.embedding.dimensions", 3072)
    return VectorStore(db_path, dimensions=dimensions)


def create_vector_cache(config: ConfigService):
    from ..vectors import VectorCache

    path = config.get("corpus.store.vectors", "~/workspace/resource/corpus/vectors.npz")
    return VectorCache(path)


def create_clustering_pipeline(config: ConfigService):
    from ..analysis import ClusteringPipeline

    db_path = str(Path(config.get("corpus.store.database", "~/workspace/resource/corpus/main.sqlite")).expanduser())
    vectors_path = str(Path(config.get("corpus.store.vectors", "~/workspace/resource/corpus/vectors.npz")).expanduser())
    model_path = str(Path(config.get("corpus.store.cluster_model", "~/workspace/resource/corpus/cluster_model.pkl")).expanduser())
    return ClusteringPipeline(db_path, vectors_path, model_path)


def create_cluster_assigner(config: ConfigService):
    from ..analysis import ClusterAssigner

    model_path = str(Path(config.get("corpus.store.cluster_model", "~/workspace/resource/corpus/cluster_model.pkl")).expanduser())
    db_path = str(Path(config.get("corpus.store.database", "~/workspace/resource/corpus/main.sqlite")).expanduser())
    vectors_path = str(Path(config.get("corpus.store.vectors", "~/workspace/resource/corpus/vectors.npz")).expanduser())
    return ClusterAssigner(model_path, db_path, vectors_path)


def create_cluster_labeler(config: ConfigService):
    from ..analysis import ClusterLabeler

    db_path = str(Path(config.get("corpus.store.database", "~/workspace/resource/corpus/main.sqlite")).expanduser())
    model_path = str(Path(config.get("corpus.store.cluster_model", "~/workspace/resource/corpus/cluster_model.pkl")).expanduser())
    return ClusterLabeler(db_path, model_path)
