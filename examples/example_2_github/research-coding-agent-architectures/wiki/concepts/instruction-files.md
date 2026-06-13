---
type: concept
name: Instruction files
aliases: [AGENTS.md, CLAUDE.md, project memory files, rules files]
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/context-compaction]], [[wiki/concepts/session-persistence]], [[wiki/concepts/subagent-delegation]], [[wiki/concepts/mcp]], [[wiki/entities/claude-code]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 7
confidence: high
---

# Instruction files

> User-curated markdown files (AGENTS.md, CLAUDE.md, .hermes.md, .cursorrules) that a coding-agent harness discovers in the filesystem and injects into the model's prompt as durable, human-maintained project memory.

## Definition

Instruction files are the cross-harness convention for persistent project memory: markdown files the *user* writes and the *agent* reads, discovered by walking the filesystem hierarchy and inlined into the system prompt or context. All three harnesses treat them as the only durable, cross-session knowledge channel curated by humans — none uses a vector store, and none lets the model rewrite these files [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]].

Where the harnesses diverge is *how many* files apply and *when* they load: opencode layers them (global → project → directory) and lazily attaches directory-level files as the agent reads files there [[wiki/sources/opencode]]; pi discovers global-first then root-most-first down to cwd and inlines everything at prompt time [[wiki/sources/pi]]; hermes-agent picks exactly one project-context source by first-match-wins priority (`.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`) and freezes it into the prompt's byte-stable tier to protect prompt caching [[wiki/sources/hermes-agent]].

## Key claims

- Instruction files are one explicit layer of a deliberately non-neural memory stack: opencode's four layers include AGENTS.md/CLAUDE.md project memory alongside SQLite transcripts, compaction, and disk caches — with no vector store, no embeddings. [[wiki/sources/opencode]]
- pi's memory model is exactly two things: a per-session append-only JSONL tree plus prompt-time AGENTS.md/CLAUDE.md instruction files; instruction files are the *only* cross-session carryover. [[wiki/sources/pi]]
- The agent never writes instruction files: pi "never writes back to instruction files; there is no agent-writable memory file," and opencode likewise ships no model-written memory file. [[wiki/sources/pi]], [[wiki/sources/opencode]]
- hermes-agent reads competitors' instruction files (AGENTS.md, CLAUDE.md, .cursorrules) but loads exactly one project-context source, first-match-wins, into the stable prompt tier. [[wiki/sources/hermes-agent]]
- hermes-agent splits the role in two: read-only instruction files for project context, plus separate agent-writable curated memory (MEMORY.md/USER.md) injected as a frozen snapshot, with writes threat-scanned and passed through the same staged-approval gate as file writes. [[wiki/sources/hermes-agent]]
- pi pairs instruction files with lazily-loaded skills (Claude Code-compatible markdown + frontmatter, listed name+description, read on demand) — progressive disclosure as its no-MCP alternative. [[wiki/sources/pi]]
- opencode adds instruction "context epochs" with drift detection as a distinctive mechanism around instruction handling. [[wiki/sources/opencode]]

## Notable quotes

> "opencode has no vector store, no embedding memory, and no model-written 'memory file'."
> — [[wiki/sources/opencode]]

> "`AGENTS.md`/`CLAUDE.md` are discovered global-first then root-most-first down to cwd and inlined into the system prompt"
> — [[wiki/sources/pi]]

## Relationships

- **[[wiki/concepts/context-compaction]]**: instruction files are the stable, human-curated complement to compaction's machine-written summaries — the two layers that survive when transcript detail is reclaimed. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/session-persistence]]**: in pi, sessions persist transcripts but carry no knowledge across sessions; instruction files are the lone cross-session memory channel. [[wiki/sources/pi]]
- **[[wiki/concepts/mcp]]**: pi positions skill files (instruction-file-adjacent markdown) with progressive disclosure as its explicit alternative to MCP. [[wiki/sources/pi]]
- **[[wiki/concepts/subagent-delegation]]**: sources detail what children inherit (permissions, tools) but not whether they re-resolve instruction files — see open questions. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]
- **[[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]**: CLAUDE.md is read by all three harnesses as a compatible convention, and pi's skill format is described as Claude Code-compatible. [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

## Tensions

- **Layered merge vs. single source**: opencode merges a global → project → directory hierarchy and pi inlines every discovered file, while hermes-agent deliberately loads exactly one project-context file (first-match-wins) — opposite answers to whether instruction context should compose or stay singular. [[wiki/sources/opencode]], [[wiki/sources/pi]] vs. [[wiki/sources/hermes-agent]]
- **Lazy vs. frozen loading**: opencode attaches directory-level instruction files lazily as the agent touches those paths, whereas hermes-agent freezes instruction content into a byte-stable system prompt for cache warmth — dynamic relevance vs. prompt-cache discipline. [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]]

## Open questions

- Do subagent/child sessions re-discover instruction files independently, inherit the parent's resolved set, or get none? No source specifies.
- How does opencode's "context epochs with drift detection" mechanism behave when instruction files change mid-session, and what is the cache cost? The mechanism is named but not explained at this layer. [[wiki/sources/opencode]]
- Is hermes-agent's single-file policy a prompt-budget decision or a conflict-avoidance decision? The priority order is documented but not the rationale. [[wiki/sources/hermes-agent]]

> Synthesis: Instruction files are the quiet consensus of this comparative study — amid sharply divergent stances on permissions, subagents, and server architecture, all three harnesses converge on human-written markdown as the durable memory substrate and refuse to let the model edit it. The interesting variation is entirely in resolution policy (layered, exhaustive, or single-source) and load timing (lazy vs. cache-frozen), which tracks each harness's broader identity: opencode's dynamic context machinery, pi's inline-everything minimalism, and hermes-agent's prompt-caching orthodoxy.
