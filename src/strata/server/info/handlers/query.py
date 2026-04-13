from mcp.types import GetPromptResult, PromptMessage, TextContent

from strata.base.configs import ConfigService
from strata.modules.info import (
    InfoReader,
    fmt_identity,
    fmt_workspace,
    fmt_hosts,
    fmt_code,
    fmt_read,
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


def _render_code(reader: InfoReader) -> str:
    data = reader.code()
    if not data:
        return "No coding conventions configured."
    return fmt_code(data)


def _render_read(reader: InfoReader) -> str:
    data = reader.read()
    if not data:
        return "No reading config."
    return fmt_read(data)


# Tool handlers

def handle_context_tool(config: ConfigService, arguments: dict) -> list[TextContent]:
    return text(_render_context(InfoReader(config)))


def handle_code_tool(config: ConfigService, arguments: dict) -> list[TextContent]:
    return text(_render_code(InfoReader(config)))


def handle_read_tool(config: ConfigService, arguments: dict) -> list[TextContent]:
    return text(_render_read(InfoReader(config)))


TOOL_HANDLERS = {
    "info_context": handle_context_tool,
    "info_conventions": handle_code_tool,
    "info_reading": handle_read_tool,
}


# Prompt handler

def _prompt_result(description: str, content: str) -> GetPromptResult:
    return GetPromptResult(
        description=description,
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            ),
        ],
    )


def handle_prompt(config: ConfigService, name: str) -> GetPromptResult:
    reader = InfoReader(config)

    if name == "context":
        return _prompt_result(
            "Personal context and infrastructure overview",
            "Here is my personal context:\n\n" + _render_context(reader),
        )

    if name == "code":
        return _prompt_result(
            "Coding conventions and design principles",
            "Here are my coding conventions:\n\n" + _render_code(reader),
        )

    if name == "read":
        return _prompt_result(
            "Paper reading guide and note-taking format",
            _render_read(reader),
        )

    return _prompt_result("Unknown prompt", f"Unknown prompt: {name}")
