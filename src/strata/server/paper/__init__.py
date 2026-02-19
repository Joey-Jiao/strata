from typing import Callable
from mcp.server import Server
from mcp.types import TextContent

from strata.base.configs import ConfigService
from .tools import TOOLS
from .handlers import HANDLERS


def register(server: Server, get_config: Callable[[], ConfigService]):

    @server.list_tools()
    async def list_tools():
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        handler = HANDLERS.get(name)
        if not handler:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        config = get_config()
        return handler(config, arguments)
