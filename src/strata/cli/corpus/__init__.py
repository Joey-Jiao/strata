import typer

from strata.base.configs import ConfigService

app = typer.Typer()


def get_config() -> ConfigService:
    return ConfigService()


from .ingest import ingest
from .search import search
from .stats import stats
from .doctor import doctor
from .explore import explore
