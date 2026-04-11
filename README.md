# Strata

Personal knowledge and resource management platform via MCP Server.

## CLI

```
strata
├── serve                            Start MCP server
│   ├── [-t, --transport <type>]     Transport: stdio (default) or http
│   ├── [--host <addr>]              HTTP bind address (default: 0.0.0.0)
│   └── [-p, --port <port>]         HTTP port (default: 8716)
│
├── paper                            Paper/literature management (Zotero-synced)
│   ├── sync                        Sync papers from Zotero
│   │   └── [-d, --deep]            Deep sync: clear all and rebuild
│   ├── list                        List papers in local store
│   │   ├── [-n, --limit <n>]       Number of papers to show
│   │   ├── [-t, --tag <tag>]       Filter by tag
│   │   └── [-c, --collection <p>]  Filter by collection path
│   ├── search <query>              Search by title, author, or abstract (FTS5)
│   ├── info <key>                  Show paper details by citation key
│   ├── collections                 List all collections (tree view)
│   ├── export [keys]               Export papers to BibTeX
│   │   ├── [--output <file>]       Output file
│   │   └── [--all]                 Export all papers
│   ├── stats                       Show library overview
│   └── doctor                      Diagnose library issues
│
├── corpus                           Conference paper corpus management
│   ├── ingest [venue] [year]        Full pipeline: import → enrich → embed → cluster
│   │   ├── [--only <step>]          Run single step: import, enrich, embed, cluster
│   │   └── [--retrain]              Force retrain cluster model
│   ├── search <query>               Search corpus (FTS5)
│   │   ├── [-v, --venue <venue>]    Filter by venue
│   │   ├── [-y, --year <year>]      Filter by year
│   │   └── [-n, --limit <n>]        Max results
│   ├── explore [cluster_id]         Interactively explore the cluster tree
│   ├── stats                        Show corpus overview
│   └── doctor                       Diagnose data quality issues
│
└── info                             Static information and conventions
    ├── context                      Show personal context (identity, workspace, hosts)
    └── conventions                  Show coding conventions
```

## MCP Tools

```
paper_locate_find          Search and filter papers (FTS5 + filters)
paper_locate_info          Get full paper details by citation key
paper_locate_browse        Browse library structure (tags, collections, stats)
paper_read                 Read paper PDF (visual or path mode)
paper_read_export          Export papers to BibTeX

corpus_search              Search corpus papers (FTS5 + filters)
corpus_browse              Browse corpus (venues, stats, clusters)
corpus_semantic_search     Semantic similarity search (embedding ANN)
corpus_similar             Find papers similar to a given paper
corpus_authors             Search authors, view publication profiles
corpus_institutions        View institution publication statistics
```

## MCP Prompts

User-invoked slash commands to load static guides into the conversation:

```
context                    Personal context (identity, workspace, hosts, infrastructure)
code                       Coding conventions and design principles
read                       Paper reading guide, note-taking format, and interaction rules
```
