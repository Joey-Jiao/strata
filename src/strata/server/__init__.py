import asyncio
import threading
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.modules.paper.common import create_syncer
from .paper import TOOLS as PAPER_TOOLS, HANDLERS as PAPER_HANDLERS
from .corpus import TOOLS as CORPUS_TOOLS, HANDLERS as CORPUS_HANDLERS
from .info import PROMPTS as INFO_PROMPTS, handle_prompt as handle_info_prompt

server = Server("strata")

ALL_TOOLS = PAPER_TOOLS + CORPUS_TOOLS
ALL_HANDLERS = {**PAPER_HANDLERS, **CORPUS_HANDLERS}

_config: ConfigService | None = None


def get_config() -> ConfigService:
    global _config
    if _config is None:
        _config = ConfigService()
    return _config


_paper_guard = {
    "syncer": None,
    "zotero_db": None,
    "mtime": 0.0,
    "lock": threading.Lock(),
}


def _ensure_paper_fresh(config: ConfigService) -> None:
    if _paper_guard["syncer"] is None:
        _, _, _, syncer = create_syncer(config)
        zotero_db = config.get("paper.sources.zotero.database")
        if not zotero_db:
            return
        _paper_guard["syncer"] = syncer
        _paper_guard["zotero_db"] = Path(zotero_db).expanduser()

    zdb = _paper_guard["zotero_db"]
    if zdb is None or not zdb.exists():
        return

    wal = Path(str(zdb) + "-wal")
    mtime = zdb.stat().st_mtime
    if wal.exists():
        mtime = max(mtime, wal.stat().st_mtime)

    if mtime <= _paper_guard["mtime"]:
        return

    with _paper_guard["lock"]:
        if mtime <= _paper_guard["mtime"]:
            return
        _paper_guard["syncer"].sync()
        _paper_guard["mtime"] = mtime


@server.list_tools()
async def list_tools():
    return ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    handler = ALL_HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    config = get_config()
    if name.startswith("paper_"):
        _ensure_paper_fresh(config)
    return handler(config, arguments)


@server.list_prompts()
async def list_prompts():
    return INFO_PROMPTS


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None):
    config = get_config()
    return handle_info_prompt(config, name)


async def run_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    asyncio.run(run_stdio())
