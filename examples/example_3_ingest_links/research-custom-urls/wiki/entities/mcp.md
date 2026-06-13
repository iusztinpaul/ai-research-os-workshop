---
type: entity
name: Model Context Protocol (MCP)
aliases: ["MCP", "MCP server"]
sources: [[[wiki/sources/web-inside-neo4js-agent-memory]], [[wiki/sources/web-from-vibe-coding-to-real-engineering-team]], [[wiki/sources/web-building-agentic-graphrag-systems]]]
related: [[[wiki/entities/neo4j]], [[wiki/entities/claude-code]], [[wiki/concepts/agent-memory]], [[wiki/concepts/graphrag]], [[wiki/concepts/context-engineering]], [[wiki/concepts/knowledge-graph]], [[wiki/concepts/ontology]]]
created: 2026-06-13T09:56:02Z
last_updated: 2026-06-13T09:56:02Z
source_count: 3
mention_count: 8
confidence: high
---

# Model Context Protocol (MCP)

> The tool-exposure layer that wires an agent's memory and capabilities into coding harnesses — typically served via FastMCP.

## Definition

Across Paul Iusztin's three Decoding AI articles, MCP appears as the interface through which agents reach external memory and tools. In the agent-memory architecture, the `neo4j-labs/agent-memory` system exposes its capabilities through "a FastMCP server with 15 tools" alongside an SDK and 9 framework adapters [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]. In the GraphRAG system, a FastMCP-served MCP server is the fourth of five architecture components (data pipeline → memory pipeline → KG → MCP server → agent), turning a knowledge graph into something the agent reaches through `search_memory` and `write_memory` tools [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]].

MCP is therefore treated less as a standalone protocol and more as the standard delivery mechanism for unified agent memory, wired into harnesses like Claude Code or Codex. Notably, one source pushes back on MCP for certain uses, preferring direct CLIs [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]].

## Key claims

- `neo4j-labs/agent-memory` exposes its memory capabilities through a FastMCP server with 15 tools, plus an SDK and 9 framework adapters. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- GraphRAG becomes "agentic" when the agent autonomously searches and writes the knowledge graph via an MCP server built on FastMCP. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- The agent reaches the unified-memory graph through two MCP tools, `search_memory` and `write_memory`, wired into harnesses like Claude Code or Codex via assistant-memory/assistant-learn skills. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- For coding agents, direct CLIs (git, mongosh, gh) are preferred over MCP wrappers, because CLIs tap bash directly and LLMs have seen far more bash than MCP wrappers in training. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]

## Notable quotes

> "GraphRAG becomes agentic when an agent gets to write to and search the knowledge graph autonomously."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

> "Agents use direct CLIs (git, mongosh, gh) rather than MCP wrappers, because CLIs tap bash directly and LLMs have seen far more bash than MCP wrappers in training."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]

## Relationships

- **FastMCP**: the server implementation used to expose memory tools in both the agent-memory and GraphRAG architectures. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- **Claude Code**: the primary harness MCP servers (and memory tools) are wired into. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]
- **Neo4j**: the agent-memory graph whose 15 capabilities are surfaced through a FastMCP/MCP server. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/neo4j]]
- **GraphRAG**: MCP is the layer that makes GraphRAG agentic, exposing `search_memory`/`write_memory`. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/graphrag]]
- **Agent memory**: MCP is the delivery mechanism for unified agent memory over a knowledge graph. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/agent-memory]]
- **Knowledge graph / Ontology**: MCP tools query and write the typed, ontology-backed graph behind the memory. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/knowledge-graph]] [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/ontology]]

## Tensions

- The memory and GraphRAG articles treat an MCP server as the natural way to expose agent capabilities [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]], whereas the agentic-coding article deliberately avoids MCP wrappers in favor of direct CLIs for tool use [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]. The distinction appears to be context-dependent: MCP for memory read/write, CLIs for deterministic developer tooling.

## Open questions

- When does exposing a capability as an MCP tool outperform a direct CLI, and vice versa? The sources gesture at memory-vs-tooling as the dividing line but do not state an explicit rule. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]

> Synthesis: MCP is the connective tissue across all three articles — the standard way Paul exposes a knowledge-graph-backed memory (via FastMCP, `search_memory`/`write_memory`) to harnesses like Claude Code. The substantive treatment lives in the memory and GraphRAG pieces; the coding piece is the dissenting voice, preferring CLIs over MCP wrappers for developer tooling, which sharpens rather than contradicts the picture: MCP earns its place for agentic memory, not for everything.
