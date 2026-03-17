from strata.base.configs import ConfigService


def create_store(config: ConfigService):
    from ..store import PaperDatabase, PaperRepository, PaperFiles

    db_path = config.get("paper.store.database", "~/workspace/resource/paper/paper.sqlite")
    files_dir = config.get("paper.store.files_dir", "~/workspace/resource/paper/files")

    db = PaperDatabase(db_path)
    db.initialize()
    files = PaperFiles(files_dir)
    repo = PaperRepository(db)

    return db, files, repo


def create_syncer(config: ConfigService):
    from ..sources.zotero import ZoteroReader, ZoteroStorageManager
    from ..sync import ZoteroSync

    db, files, repo = create_store(config)

    zotero_db = config.get("paper.sources.zotero.database", "~/workspace/resource/zotero/zotero.sqlite")
    zotero_storage = config.get("paper.sources.zotero.storage_dir", "~/workspace/resource/zotero/storage")
    stop_words = set(config.get("paper.citation.stop_words", []) or [])

    reader = ZoteroReader(zotero_db)
    storage = ZoteroStorageManager(zotero_storage)
    syncer = ZoteroSync(reader, storage, db, files, stop_words)

    return db, files, repo, syncer
