def fmt_identity(data: dict) -> str:
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


def fmt_workspace(data: dict) -> str:
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


def fmt_hosts(data: dict) -> str:
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


def fmt_code(data: dict) -> str:
    parts = []
    for key, value in data.items():
        if isinstance(value, str):
            title = key.replace("_", " ").title()
            parts.append(f"## {title}\n{value.strip()}")
    return "\n\n".join(parts)


def fmt_read(data: dict) -> str:
    parts = []

    about = data.get("about", "")
    if about:
        parts.append(about.strip())

    tools = data.get("tools", "")
    if tools:
        parts.append(f"## Tools\n{tools.strip()}")

    notes = data.get("notes", {})
    if notes:
        sections = []
        for kind in ("single", "collection"):
            info = notes.get(kind, {})
            if not info:
                continue
            path = info.get("path", "")
            desc = info.get("description", "").strip()
            template = info.get("template", "").strip()
            block = f"### {kind.title()} Paper Notes\n**Path**: `{path}`\n{desc}"
            if template:
                block += f"\n\n**Template**:\n```markdown\n{template}\n```"
            sections.append(block)
        if sections:
            parts.append(f"## Notes\n" + "\n\n".join(sections))

    rules = data.get("rules", [])
    if rules:
        items = "\n".join(f"- {r}" for r in rules)
        parts.append(f"## Rules\n{items}")

    return "\n\n".join(parts)
