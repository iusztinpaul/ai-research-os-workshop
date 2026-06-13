---
type: concept
name: Ontology
aliases: ["POLE+O ontology", "POLE-O"]
sources: [[[wiki/sources/web-inside-neo4js-agent-memory]], [[wiki/sources/web-building-agentic-graphrag-systems]]]
related: [[[wiki/concepts/graphrag]], [[wiki/concepts/knowledge-graph]], [[wiki/concepts/agent-memory]], [[wiki/concepts/context-engineering]], [[wiki/entities/neo4j]], [[wiki/entities/mcp]], [[wiki/entities/claude-code]]]
created: 2026-06-13T09:56:55Z
last_updated: 2026-06-13T09:56:55Z
source_count: 2
mention_count: 11
confidence: medium
---

# Ontology

> The schema/type system that defines which entity and relationship types a knowledge graph is allowed to hold — and, per both sources, the hard, must-come-first part of building [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/graphrag|GraphRAG]] and [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/agent-memory|agent memory]].

## Definition

An ontology is the closed (or partly closed) type system that constrains what nodes and edges a [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/knowledge-graph|knowledge graph]] can contain. In the agent-memory blueprint it takes the concrete form of **POLE+O** — Person, Object, Location, Event, Organization — a five-type taxonomy borrowed from intelligence analysis where every entity is exactly one type, with open subtypes materialized as multi-tier [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/neo4j|Neo4j]] labels such as `:Entity:Person:Individual` [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]. The GraphRAG piece reframes the whole problem around this idea: GraphRAG "isn't a retrieval algorithm, it's a data modeling problem," so the ontology must be designed before any extraction or retrieval is attempted [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]].

## Key claims

- The ontology is the starting point of GraphRAG; it is a data-modeling problem, not a retrieval one, and the schema must precede extraction. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- Skipping ontology design causes label explosion: LangChain's `MongoDBGraphStore` produced 17 node types and 34 relationship types from just five documents, including `part_of`, `Part Of`, and `part of` as three separate types. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- The agent-memory system uses a closed five-type ontology, POLE+O (Person, Object, Location, Event, Organization); every entity is exactly one type, with open subtypes as multi-tier Neo4j labels. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- Beyond entities, the ontology includes `:Fact` nodes for generic single-concept claims and `:Preference` nodes carrying a `SUPERSEDED_BY` relationship. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- A practical "Global Ontology" can split into a deterministically-built Document Ontology (DOCUMENT/CHUNK) and an LLM-extracted Person Ontology (PERSON/TASK/EPISODE/PREFERENCE). [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- Three extraction modes follow from how strictly the ontology binds: structured (schema-guided), semi-structured (lineage/metadata, no LLM), and unstructured (LLM invents labels, for discovery only). [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]
- Agent stacks adopt labeled property graphs over RDF, with the ontology expressed as typed labels and edges. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

## Notable quotes

> "GraphRAG isn't a retrieval algorithm, it's a data modeling problem."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

> "Five documents produced 17 node types and 34 relationship types. This included part_of, Part Of, and part of as three separate types."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

> "POLE+O (Person, Object, Location, Event, Organization), borrowed from intelligence-analysis taxonomies; every entity is exactly one type."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]

## Relationships

- **GraphRAG**: ontology is the prerequisite design step that GraphRAG is built on; both sources make it the first move before extraction or retrieval. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/graphrag]]
- **Knowledge graph**: the ontology defines the allowed node/edge vocabulary that fills the knowledge graph. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/knowledge-graph]]
- **Agent memory**: POLE+O plus `:Fact`/`:Preference` types form the schema of long-term agent memory. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/agent-memory]]
- **Context engineering**: a constrained ontology counters context rot/fragmentation by keeping retrieved memory typed and merge-able rather than fuzzy. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/concepts/context-engineering]]
- **Neo4j**: subtypes are materialized as multi-tier Neo4j labels (`:Entity:Person:Individual`). [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/neo4j]]
- **MCP**: the ontology-shaped graph is exposed to agents through MCP `search_memory`/`write_memory` tools served via FastMCP. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/mcp]]
- **Claude Code**: in the worked example, Claude Code appears as an `Object`-typed entity inside the ontology and as a harness that reads/writes the graph. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]

## Tensions

_No notable disagreements across sources._ Both treat ontology design as the decisive, must-come-first step; the GraphRAG piece supplies the failure-mode argument (label explosion) while the agent-memory piece supplies the concrete closed schema (POLE+O), and the two are complementary rather than conflicting.

## Open questions

- How fixed should POLE+O be in practice? The agent-memory source treats the five top types as closed but subtypes as open, leaving the boundary of "closed enough" unspecified. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-inside-neo4js-agent-memory]]
- When does an unstructured (LLM-invents-labels) discovery pass safely feed back into the curated ontology without reintroducing label explosion? [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/sources/web-building-agentic-graphrag-systems]]

> Synthesis: Across both Decoding AI pieces, ontology is the load-bearing concept — the deliberate, upfront type system that turns scattered data into a coherent, queryable graph. The GraphRAG article argues negatively (skip it and you get uncontrolled label explosion), while the agent-memory article argues positively with a named, closed schema (POLE+O plus Fact/Preference). Together they frame ontology design, not retrieval cleverness, as the real engineering work behind durable agent memory.
