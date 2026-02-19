from typing import Sequence
from mcp.types import TextContent


def text(content: str) -> list[TextContent]:
    return [TextContent(type="text", text=content)]


def lines(*parts: str) -> list[TextContent]:
    return text("\n".join(parts))


def bullet_list(title: str, items: Sequence[str]) -> list[TextContent]:
    if not items:
        return text(f"No {title.lower()} found.")
    content = [f"{title} ({len(items)}):\n"] + [f"- {item}" for item in items]
    return text("\n".join(content))


def error(message: str) -> list[TextContent]:
    return text(f"Error: {message}")


def not_found(entity: str, key: str) -> list[TextContent]:
    return text(f"{entity} not found: {key}")
