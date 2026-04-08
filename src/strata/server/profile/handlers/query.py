from mcp.types import TextContent

from strata.base.configs import ConfigService
from strata.modules.profile import ProfileReader
from strata.server.common import text


def _fmt_identity(data: dict) -> str:
    parts = [f"Name: {data.get('name', '')}"]
    if data.get("alias"):
        parts.append(f"Alias: {data['alias']}")
    if data.get("domain"):
        parts.append(f"Domain: {data['domain']}")
    if data.get("email"):
        parts.append(f"Email: {data['email']}")
    for edu in data.get("education", []):
        parts.append(f"  {edu.get('degree', '')} - {edu.get('school', '')}")
    return "\n".join(parts)


def _fmt_workspace(data: dict) -> str:
    parts = [f"Root: {data.get('root', '')}"]
    for name, area in data.get("areas", {}).items():
        desc = area.get("description", "")
        parts.append(f"\n{name}/ — {desc}")
        for proj, info in area.get("projects", {}).items():
            if isinstance(info, dict):
                pdesc = info.get("description", "")
                parts.append(f"  {proj}: {pdesc}")
                details = info.get("details", "").strip()
                if details:
                    for line in details.splitlines():
                        parts.append(f"    {line}")
            elif isinstance(info, str) and info:
                parts.append(f"  {proj}: {info}")
            else:
                parts.append(f"  {proj}")
    return "\n".join(parts)


def _fmt_hosts(data: dict) -> str:
    parts = []
    desc = data.get("description", "")
    if desc:
        parts.append(desc.strip())
        parts.append("")
    for name, info in data.get("machines", {}).items():
        if isinstance(info, str):
            parts.append(f"  {name}: {info}")
        else:
            parts.append(f"  {name}")
    return "\n".join(parts)


def _fmt_conventions(data: dict) -> str:
    parts = []
    for key, value in data.items():
        if isinstance(value, str):
            title = key.replace("_", " ").title()
            parts.append(f"## {title}\n{value.strip()}")
    return "\n\n".join(parts)


def handle_context(config: ConfigService, arguments: dict) -> list[TextContent]:
    reader = ProfileReader(config)
    parts = []

    about = reader.about()
    if about:
        parts.append(about.strip())

    identity = reader.identity()
    if identity:
        parts.append(f"## Identity\n{_fmt_identity(identity)}")

    workspace = reader.workspace()
    if workspace:
        parts.append(f"## Workspace\n{_fmt_workspace(workspace)}")

    hosts = reader.hosts()
    if hosts:
        parts.append(f"## Hosts\n{_fmt_hosts(hosts)}")

    return text("\n\n".join(parts))


def handle_conventions(config: ConfigService, arguments: dict) -> list[TextContent]:
    reader = ProfileReader(config)
    data = reader.conventions()
    if not data:
        return text("No conventions configured.")
    return text(_fmt_conventions(data))


QUERY_HANDLERS = {
    "profile_context": handle_context,
    "profile_conventions": handle_conventions,
}
