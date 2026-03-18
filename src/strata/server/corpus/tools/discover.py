from mcp.types import Tool

DISCOVER_TOOLS = [
    Tool(
        name="corpus_semantic_search",
        description=(
            "Search the corpus by meaning using embedding similarity. "
            "Finds papers whose content is semantically similar to the query, even without keyword overlap. "
            "Use when: user describes a research topic or problem in natural language."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of the research topic or problem",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="corpus_similar",
        description=(
            "Find papers similar to a given paper in the corpus. "
            "Uses the paper's abstract to find semantically related work. "
            "Use when: user has a specific paper and wants to find related work."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "Paper ID (S2 paperId) to find similar papers for",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                },
            },
            "required": ["paper_id"],
        },
    ),
]
