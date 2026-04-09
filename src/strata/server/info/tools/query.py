from mcp.types import Tool

TOOLS = [
    Tool(
        name="info_context",
        description=(
            "Get personal context: who the user is, workspace structure, "
            "infrastructure projects, and machine fleet. Use when: starting "
            "a session, needing background about the user, understanding "
            "project layout, or deciding where to deploy or run something."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="info_conventions",
        description=(
            "Get coding conventions and design principles. Use when: writing "
            "code, choosing libraries, setting up a new project, or reviewing "
            "code style. Covers project structure, module design, data layer, "
            "and style rules."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="info_reading",
        description=(
            "Get paper reading guide: note-taking format, file locations, "
            "available tools, and interaction rules. Use when: the user wants "
            "to read a paper, discuss a paper, or take notes on a paper."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
]
