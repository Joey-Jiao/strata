import typer

from strata.base.configs import ConfigService

app = typer.Typer()


def get_config() -> ConfigService:
    return ConfigService()


from .sync import sync
from .watch import watch
from .list import list_papers
from .search import search
from .info import info
from .collections import collections
from .export import export_cmd
from .stats import stats
from .doctor import doctor
