from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.modules.info import (
    InfoReader,
    fmt_identity,
    fmt_workspace,
    fmt_hosts,
    fmt_conventions,
    fmt_reading,
)
from strata.server.common import text


def _render_context(reader: InfoReader) -> str:
    parts = []
    about = reader.about()
    if about:
        parts.append(about.strip())
    identity = reader.identity()
    if identity:
        parts.append(f"## Identity\n{fmt_identity(identity)}")
    workspace = reader.workspace()
    if workspace:
        parts.append(f"## Workspace\n{fmt_workspace(workspace)}")
    hosts = reader.hosts()
    if hosts:
        parts.append(f"## Hosts\n{fmt_hosts(hosts)}")
    return "\n\n".join(parts)


def handle_context_tool(config: ConfigService, arguments: dict) -> list[TextContent]:
    return text(_render_context(InfoReader(config)))


def handle_conventions_tool(config: ConfigService, arguments: dict) -> list[TextContent]:
    reader = InfoReader(config)
    data = reader.conventions()
    if not data:
        return text("No conventions configured.")
    return text(fmt_conventions(data))


def handle_reading_tool(config: ConfigService, arguments: dict) -> list[TextContent]:
    reader = InfoReader(config)
    data = reader.reading()
    if not data:
        return text("No reading config.")
    return text(fmt_reading(data))


TOOL_HANDLERS = {
    "info_context": handle_context_tool,
    "info_conventions": handle_conventions_tool,
    "info_reading": handle_reading_tool,
}
