import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from strata.base.configs import ConfigService
from .paper import TOOLS as PAPER_TOOLS, HANDLERS as PAPER_HANDLERS
from .corpus import TOOLS as CORPUS_TOOLS, HANDLERS as CORPUS_HANDLERS

server = Server("strata")

ALL_TOOLS = PAPER_TOOLS + CORPUS_TOOLS
ALL_HANDLERS = {**PAPER_HANDLERS, **CORPUS_HANDLERS}

_config: ConfigService | None = None


def get_config() -> ConfigService:
    global _config
    if _config is None:
        _config = ConfigService()
    return _config


@server.list_tools()
async def list_tools():
    return ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    handler = ALL_HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    config = get_config()
    return handler(config, arguments)


async def run_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


async def run_http(host: str, port: int):
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    import uvicorn

    session_manager = StreamableHTTPSessionManager(app=server)

    async with session_manager.run():
        app = Starlette(
            routes=[Mount("/mcp", app=session_manager.handle_request)],
        )
        config = uvicorn.Config(app, host=host, port=port, reload=True)
        uvicorn_server = uvicorn.Server(config)
        await uvicorn_server.serve()


def main(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8716):
    if transport == "http":
        asyncio.run(run_http(host, port))
    else:
        asyncio.run(run_stdio())
