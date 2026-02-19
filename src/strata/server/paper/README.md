# Paper Module

MCP tools for personal academic paper library management.

## Naming Convention

```
{module}_{layer}_{action}
```

---

## Locate Layer

Metadata-based discovery and indexing operations.

| Tool                  | Description          |
| --------------------- | -------------------- |
| `paper_locate_find`   | Search and filter    |
| `paper_locate_info`   | Single paper details |
| `paper_locate_browse` | Library structure    |

### `paper_locate_find`

Search and filter papers. All conditions are AND-combined.

```
Parameters:
  query        string     Keywords (title/author/abstract)
  year_from    integer    Minimum year
  year_to      integer    Maximum year
  author       string     Author name (partial match)
  tag          string     Filter by tag
  collection   string     Filter by collection
  recent_days  integer    Only papers added in last N days
  limit        integer    Max results (default: 20)

Returns:
  List of papers: [citation_key] (year) title
```

### `paper_locate_info`

Get full metadata for a single paper.

```
Parameters:
  key    string (required)    Citation key (e.g., smith2024deep)

Returns:
  citation_key, title, authors, year, type, journal, DOI, URL,
  abstract, collections, tags
```

### `paper_locate_browse`

Browse library structure and statistics.

```
Parameters:
  type    string (required)    "collections" | "tags" | "stats"

Returns:
  - collections: list of collection paths
  - tags: list of all tags
  - stats: total count, year range, distribution
```

---

## Read Layer

Content access operations.

| Tool                | Description       |
| ------------------- | ----------------- |
| `paper_read`        | Read PDF content  |
| `paper_read_export` | Export as BibTeX  |

### `paper_read`

Read paper content from PDF.

```
Parameters:
  key     string (required)    Citation key
  mode    string               "visual" | "path" (default: visual)
  pages   string               Page range for visual mode: "1", "1-5", "1,3,5"

Returns:
  - visual: ImageContent[] (PNG at 150 DPI)
  - path: file path (for Claude Code Read tool)
```

### `paper_read_export`

Export papers as BibTeX.

```
Parameters:
  keys    string[] (required)    List of citation keys

Returns:
  BibTeX formatted text
```
