from mcp.types import Tool

READ_TOOLS = [
    Tool(
        name="paper_read",
        description=(
            "Read paper content from PDF. "
            "Two modes available: "
            "(1) visual: renders pages as images, works everywhere; "
            "(2) path: returns file path for use with Read tool in Claude Code. "
            "Use visual mode by default. Use path mode only in Claude Code environment."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Citation key of the paper",
                },
                "mode": {
                    "type": "string",
                    "enum": ["visual", "path"],
                    "description": "Output mode: visual (images) or path (file path). Default: visual",
                },
                "pages": {
                    "type": "string",
                    "description": "Page range: '1', '1-5', '1,3,5' (default: all pages)",
                },
            },
            "required": ["key"],
        },
    ),
    Tool(
        name="paper_read_export",
        description=(
            "Export papers as BibTeX for use in LaTeX documents. "
            "Use when: user needs citations, wants to cite references in a paper, "
            "or asks for bibliography entries. Provide either keys or tag."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of citation keys to export",
                },
                "tag": {
                    "type": "string",
                    "description": "Export all papers with this tag",
                },
            },
        },
    ),
]
