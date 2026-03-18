from mcp.types import Tool

PROFILE_TOOLS = [
    Tool(
        name="corpus_authors",
        description=(
            "Search for authors and view their publication profiles. "
            "Use when: user asks about a researcher's work, wants to find who publishes in a field, "
            "or needs co-authorship information."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "author": {
                    "type": "string",
                    "description": "Author name (partial match) to search for",
                },
                "author_id": {
                    "type": "string",
                    "description": "OpenAlex author ID for full profile (venues, years, co-authors)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results for search (default: 20)",
                },
            },
        },
    ),
    Tool(
        name="corpus_institutions",
        description=(
            "View institution publication statistics in the corpus. "
            "Use when: user asks about a university or company's research output at specific venues."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "institution": {
                    "type": "string",
                    "description": "Institution name (partial match)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 20)",
                },
            },
            "required": ["institution"],
        },
    ),
]
