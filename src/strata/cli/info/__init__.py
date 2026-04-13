import typer

from strata.base.configs import ConfigService

app = typer.Typer()


def get_config() -> ConfigService:
    return ConfigService()


from .context import context
from .code import code
