---
type: concept
name: Knowledge graph
aliases: ["knowledge-graph memory", "property graph", "KG"]
sources: [[[wiki/sources/web-inside-neo4js-agent-memory]], [[wiki/sources/web-building-agentic-graphrag-systems]]]
related: [[[wiki/entities/neo4j]], [[wiki/entities/mcp]], [[wiki/entities/claude-code]], [[wiki/concepts/agent-memory]], [[wiki/concepts/graphrag]], [[wiki/concepts/ontology]], [[wiki/concepts/context-engineering]]]
created: 2026-06-13T09:56:44Z
last_updated: 2026-06-13T09:56:44Z
source_count: 2
mention_count: 18
confidence: medium
---

# Knowledge graph

> A structured store of typed entity nodes and relationship edges that gives an AI agent durable, mergeable memory with stable identity over time.

## Definition

A knowledge graph models information as typed nodes (entities, facts, documents) connected by typed edges (relationships), so that identity and relationships are first-class and queryable. Both sources argue this structure is what makes AI memory *durable*: file logs "fragment and rot context" and a vector index "gives you fuzzy semantic recall but no merge, no identity," whereas a graph can track whether two mentions refer to the same thing and how entities relate over time [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]. The companion article frames an agent's unified memory as naturally mapping to a knowledge graph that must track people, places, tasks, and how those relate over time [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]].

In practice both sources use **labeled property graphs** rather than RDF — the GraphRAG piece states agent stacks use property graphs over RDF, and the Neo4j piece materializes open subtypes as multi-tier labels like `:Entity:Person:Individual` [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]] [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]].

## Key claims

- Durable AI memory requires a structured graph to track identity and relationships; file logs fragment context and vector indexes lack merge and identity. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- An agent's unified memory naturally maps to a knowledge graph that tracks people, places, tasks, and their relationships over time. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- Agent stacks use labeled property graphs over RDF in practice. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- All memory tiers (short-term `:Message` chains, long-term typed `:Entity` nodes, per-run `:ReasoningTrace` trees) can live on a single graph, stitched by `:MENTIONS`, `:INITIATED_BY`, and `:TOUCHED` edges so cross-tier provenance is a one-hop query. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- Building the graph requires resolving whether two mentions are the same node: scores ≥0.95 auto-merge, <0.85 create a new node, and 0.85–0.95 create a pending `:SAME_AS` edge for review, because "a false merge is silent and unrecoverable." [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- Skipping schema design causes label explosion — LangChain's `MongoDBGraphStore` produced 17 node types and 34 relationship types from five documents, with `part_of`, `Part Of`, `part of` as three distinct types. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- The graph does not require Neo4j by default: for small-to-medium scale and 2–3 hop traversals, build on Postgres or MongoDB; reserve Neo4j for deep traversals or graph algorithms. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]] [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

## Notable quotes

> "A vector index gives you fuzzy semantic recall but no merge, no identity, and no way to know if this is the same Karpathy you knew yesterday."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]

> "Five documents produced 17 node types and 34 relationship types. This included part_of, Part Of, and part of as three separate types."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

## Relationships

- **Ontology**: a knowledge graph must be defined by an ontology first — the schema of node and relationship types is what prevents label explosion and what GraphRAG actually depends on. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/ontology]]
- **Agent memory**: knowledge-graph memory is the structural substrate that gives agent memory identity, merge, and provenance across tiers. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/agent-memory]]
- **GraphRAG**: GraphRAG retrieves over a knowledge graph via hybrid text+semantic entry points plus 2–3 hop traversal of typed edges. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/graphrag]]
- **Context engineering**: the graph is positioned as the cure for context rot and fragmentation that pure context-window or file approaches suffer. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/context-engineering]]
- **Neo4j**: the canonical (but not mandatory) graph database used to back these systems. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/neo4j]]
- **MCP**: the graph is exposed to agents through a FastMCP server with `search_memory`/`write_memory` tools. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/mcp]]
- **Claude Code**: a consuming agent harness wired to the graph via MCP. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]

## Tensions

_No notable disagreements across sources._ Both are authored by Paul Iusztin and consistently favor property graphs over RDF and single-store databases over Neo4j unless deep traversal is core.

## Open questions

- The Neo4j SDK composes retrieval (vector + traversal + time-walk) in one Cypher query but leaves final context compression to the caller — how the graph's output is condensed for the LLM context window is left unspecified. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]

> Synthesis: Across both articles the knowledge graph is treated less as a retrieval trick and more as a data-modeling discipline: its value is identity (merge/dedup via `SAME_AS` bands), relationship typing, and cross-tier provenance — all of which depend on an ontology defined up front. The recurring, opinionated takeaway is that the graph is the durable backbone of agent memory and GraphRAG, but the *database* is an implementation detail: prefer Postgres/MongoDB and labeled property graphs, reaching for Neo4j only when deep traversal or graph algorithms are central.
