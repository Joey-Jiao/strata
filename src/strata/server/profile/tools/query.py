from mcp.types import Tool

QUERY_TOOLS = [
    Tool(
        name="profile_context",
        description=(
            "Get personal context: who the user is, workspace structure, "
            "infrastructure projects, and machine fleet. Use when: starting "
            "a session, needing background about the user, understanding "
            "project layout, or deciding where to deploy or run something."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="profile_conventions",
        description=(
            "Get coding conventions and tool preferences. Use when: writing "
            "code, choosing libraries, setting up a new project, or reviewing "
            "code style. Covers Python, frontend, and general practices."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]
