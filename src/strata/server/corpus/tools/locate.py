from mcp.types import Tool

LOCATE_TOOLS = [
    Tool(
        name="corpus_search",
        description=(
            "Search the corpus of conference papers (bulk-imported from Semantic Scholar). "
            "Supports full-text search across title/abstract/authors via FTS5, plus filters. "
            "All conditions are AND-combined. "
            "Use when: user wants to find papers from specific conferences/venues beyond the personal library."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Full-text search query (matches title, abstract, authors via FTS5)",
                },
                "venue": {
                    "type": "string",
                    "description": "Filter by venue (e.g., NeurIPS, ICML, ACL)",
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
        name="corpus_browse",
        description=(
            "Browse corpus structure and statistics. "
            "Use when: user asks what venues are available, wants corpus overview, "
            "or needs to know valid filter values before searching the corpus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["venues", "stats", "clusters"],
                    "description": "What to browse: venues (paper counts and year ranges), stats (totals, year distribution), or clusters (topic hierarchy with keywords)",
                },
            },
            "required": ["type"],
        },
    ),
]
