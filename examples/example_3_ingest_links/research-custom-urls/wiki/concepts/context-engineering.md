---
type: concept
name: Context engineering
aliases: ["context rot"]
sources: [[[wiki/sources/web-inside-neo4js-agent-memory]], [[wiki/sources/web-from-vibe-coding-to-real-engineering-team]]]
related: [[[wiki/concepts/agent-memory]], [[wiki/concepts/knowledge-graph]], [[wiki/concepts/ontology]], [[wiki/concepts/graphrag]], [[wiki/entities/neo4j]], [[wiki/entities/claude-code]], [[wiki/entities/mcp]]]
created: 2026-06-13T09:56:33Z
last_updated: 2026-06-13T09:56:33Z
source_count: 2
mention_count: 6
confidence: medium
---

# Context engineering

> The discipline of deciding what enters an agent's context window — and keeping it from fragmenting, rotting, or drowning in noise — so the agent acts on durable, canonical information rather than stale or duplicated fragments.

## Definition

Across both sources, context engineering is treated less as prompt-writing and more as managing the supply chain of information an agent reasons over. In the agent-memory piece, the failure mode is named directly: file-based logs "fragment and rot context" as a knowledge base scales, with retrieval quality degrading past roughly 50 documents, while vector indexes give fuzzy recall but "no merge, no identity" ([[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]). The remedy is structured memory — a knowledge graph with a closed ontology — so that what reaches the context window is canonical and de-duplicated rather than a noisy pile of overlapping fragments ([[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]).

In the agentic-coding piece, the same concern shows up at the level of a multi-agent engineering team: agents are deliberately anchored in compressed, durable artifacts (ADRs, a DDD glossary) so each run carries forward only the architectural and business context that matters, instead of re-deriving or hallucinating it ([[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]).

## Key claims

- File logs fragment and rot context as a knowledge base scales; pure file-based wikis degrade past ~50 documents, motivating structured memory to keep context durable. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- A vector index gives fuzzy semantic recall but no merge and no identity, so retrieved context can carry duplicate, conflicting entities rather than one canonical fact. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- Architecture Decision Records (ADRs) act as compressed architectural memory across runs, and a DDD glossary enforces one canonical name per concept — giving the agent business context, not just code context. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]
- Agents use direct CLIs (git, mongosh, gh) instead of MCP wrappers because CLIs tap bash directly and LLMs have seen far more bash than MCP wrappers in training — a context-shaping choice favoring familiar tokens. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]
- Judgment-call review loops are capped (3 attempts) because an LLM reviewer almost always has something else to say and will spiral, so caps protect the context loop from runaway noise. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]
- The retrieval algorithm composes vector similarity, multi-hop traversal, and time-ordered walks in one query, but leaves final context compression to the caller — context engineering is the caller's job. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]

## Notable quotes

> "A vector index gives you fuzzy semantic recall but no merge, no identity, and no way to know if this is the same Karpathy you knew yesterday."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]

> "The cost of vibe coding isn't abstract. It's the next feature you can't ship because you're debugging a slash-command renderer that looked finished."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]

## Relationships

- **Agent memory**: structured memory is the mechanism that defeats context rot — what context engineering manages, agent memory stores. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/agent-memory]]
- **Knowledge graph**: a graph with identity and merge is offered as the antidote to fragmented, rotting context. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/knowledge-graph]]
- **Ontology**: the closed POLE+O ontology constrains what entities can enter memory, keeping retrieved context canonical. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/ontology]]
- **GraphRAG**: graph-based retrieval is positioned as a way to feed cleaner, relationship-aware context than vector RAG alone. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/graphrag]]
- **Neo4j**: the single-graph store on which durable, de-duplicated context is maintained. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/neo4j]]
- **Claude Code**: the agent runtime whose context is engineered via ADRs, DDD glossary, and CLAUDE.md prose. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]
- **MCP**: a tool-exposure layer, partly avoided in the coding setup in favor of direct CLIs for token-familiarity reasons. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/mcp]]

## Tensions

- On MCP versus context cleanliness: the agent-memory source exposes memory through a FastMCP server with 15 tools, treating MCP as the integration surface ([[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]), while the coding source deliberately prefers direct CLIs over MCP wrappers for better-trained context ([[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-from-vibe-coding-to-real-engineering-team]]). Not a direct contradiction, but a different bet on what shapes context best.

## Open questions

- Where does context compression actually live? The retrieval layer explicitly defers it to the caller, but neither source specifies a concrete compression strategy. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]

> Synthesis: The two sources converge on a single insight from opposite ends — context rot is the enemy, and the fix is durable, canonical, de-duplicated information rather than more raw text. The memory piece engineers context at the data layer (graph, ontology, identity); the coding piece engineers it at the process layer (ADRs, glossary, capped loops, familiar CLIs). Their one live disagreement is whether MCP or direct CLIs better serve the model's context, which reads as a tactical, not foundational, split.
