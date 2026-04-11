from mcp.types import Prompt

PROMPTS = [
    Prompt(
        name="context",
        description=(
            "Personal context: who the user is, workspace structure, "
            "infrastructure projects, and machine fleet."
        ),
    ),
    Prompt(
        name="code",
        description=(
            "Coding conventions and design principles: project structure, "
            "module design, data layer, and style rules."
        ),
    ),
    Prompt(
        name="read",
        description=(
            "Paper reading guide: note-taking format, file locations, "
            "available tools, and interaction rules."
        ),
    ),
]
