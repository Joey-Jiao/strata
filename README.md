# Strata

Personal knowledge/resource management platform via MCP Server.

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
│   ├── watch                       Watch Zotero for changes and auto-sync
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
└── corpus                           Conference paper corpus management
    ├── ingest [venue] [year]        Full pipeline: import → enrich → embed → cluster
    │   ├── [--only <step>]          Run single step: import, enrich, embed, cluster
    │   └── [--retrain]              Force retrain cluster model
    ├── search <query>               Search corpus (FTS5)
    │   ├── [-v, --venue <venue>]    Filter by venue
    │   ├── [-y, --year <year>]      Filter by year
    │   └── [-n, --limit <n>]        Max results
    ├── explore [cluster_id]         Interactively explore the cluster tree
    ├── stats                        Show corpus overview
    └── doctor                       Diagnose data quality issues
```

## Explore

Interactive cluster tree browser. Navigate a 6-level hierarchy of 2864 research topics derived from 62K papers across 11 top venues.

```
$ strata corpus explore

======================================================================
Root clusters:
  [ 0] NLP & LLMs (8321)
  [ 7] 3D Vision: Depth, Tracking, NeRF (5936)
  [ 4] Graph Neural Networks & Time Series (5519)
  ...

→ 0

======================================================================
[0] NLP & LLMs (8321 papers)
  Keywords: moral, gsm8k, sarcasm, absa, tom, gec
  Venues: NeurIPS (120), ICML (95), ICLR (80), ACL (75)

  Subtopics (15):
    [ 0] Prompt Engineering and Instruction Tuning (899)
    [ 5] LLM Evaluation and Human Preference (843)
    [ 4] LLM Reasoning and Prompting (802)
    ...

→ 5

======================================================================
[0.5] LLM Evaluation and Human Preference (843 papers)
  Path: NLP & LLMs → LLM Evaluation and Human Preference
  ...

  Subtopics (4):
    [ 0] Language Model Evaluation and Benchmarks (295)
    [ 1] ...

→ u          (go back up)
→ 0.5.0.1   (jump to any cluster by full path)
→ n          (next page, on leaf nodes)
→ q          (quit)
```

At leaf nodes, papers are listed by citation count:

```
  Papers (1-20 of 81):
    2024 NeurIPS [ 523] Chatbot Arena: An Open Platform for Evaluating...
    2023 ICML    [ 312] Large Language Models Are Not Yet Human-Level...
    2024 ACL     [ 187] ...
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
