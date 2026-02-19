from strata.base.configs import ConfigService
from strata.modules.paper.store import PaperDatabase, PaperRepository, PaperFiles


def get_components(config: ConfigService):
    db_path = config.get("paper.store.database", "~/workspace/resource/paper/paper.sqlite")
    files_dir = config.get("paper.store.files_dir", "~/workspace/resource/paper/files")

    db = PaperDatabase(db_path)
    db.initialize(files_dir=files_dir)
    files = PaperFiles(files_dir)
    repo = PaperRepository(db)

    return db, files, repo
