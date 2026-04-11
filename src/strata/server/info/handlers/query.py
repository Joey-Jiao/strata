from mcp.types import GetPromptResult, PromptMessage, TextContent

from strata.base.configs import ConfigService
from strata.modules.info import (
    InfoReader,
    fmt_identity,
    fmt_workspace,
    fmt_hosts,
    fmt_conventions,
    fmt_reading,
)


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


def _render_conventions(reader: InfoReader) -> str:
    data = reader.conventions()
    if not data:
        return "No conventions configured."
    return fmt_conventions(data)


def _render_reading(reader: InfoReader) -> str:
    data = reader.reading()
    if not data:
        return "No reading config."
    return fmt_reading(data)


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
            "Here are my coding conventions:\n\n" + _render_conventions(reader),
        )

    if name == "read":
        return _prompt_result(
            "Paper reading guide and note-taking format",
            _render_reading(reader),
        )

    return _prompt_result("Unknown prompt", f"Unknown prompt: {name}")
