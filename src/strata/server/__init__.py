import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

from strata.base.configs import ConfigService
from .paper import register as paper_register

server = Server("strata")

_config: ConfigService | None = None


def get_config() -> ConfigService:
    global _config
    if _config is None:
        _config = ConfigService()
    return _config


paper_register(server, get_config)


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    asyncio.run(run())
