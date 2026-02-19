from mcp.types import Tool

LOCATE_TOOLS = [
    Tool(
        name="paper_locate_find",
        description=(
            "Search and filter papers in the library. "
            "Supports full-text search across title/author/abstract via FTS5, plus filters. "
            "All conditions are AND-combined. "
            "Use when: user wants to find papers by topic, author, year range, tag, or venue."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Full-text search query (matches title, author, abstract via FTS5)",
                },
                "arxiv_id": {
                    "type": "string",
                    "description": "Filter by arXiv ID (e.g., 2301.12345)",
                },
                "year_from": {
                    "type": "integer",
                    "description": "Minimum year (inclusive)",
                },
                "year_to": {
                    "type": "integer",
                    "description": "Maximum year (inclusive)",
                },
                "author": {
                    "type": "string",
                    "description": "Author name (partial match)",
                },
                "venue": {
                    "type": "string",
                    "description": "Venue name (e.g., NeurIPS, ICML, arXiv)",
                },
                "tag": {
                    "type": "string",
                    "description": "Filter by tag",
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["relevance", "year"],
                    "description": "Sort order: relevance (FTS5 rank, requires query) or year (default when no query)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 20)",
                },
                "offset": {
                    "type": "integer",
                    "description": "Skip first N results for pagination (default: 0)",
                },
            },
        },
    ),
    Tool(
        name="paper_locate_info",
        description=(
            "Get full details of a specific paper by its citation key. "
            "Use when: user mentions a citation key, asks for details about a specific paper, "
            "or wants to see abstract/metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Citation key (e.g., smith2024deep)",
                },
            },
            "required": ["key"],
        },
    ),
    Tool(
        name="paper_locate_browse",
        description=(
            "Browse library structure and statistics. "
            "Use when: user asks what tags exist, wants library overview, "
            "or needs to know valid filter values before searching."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["tags", "stats"],
                    "description": "What to browse: tags or stats (year distribution, PDF coverage, last sync)",
                },
            },
            "required": ["type"],
        },
    ),
]
