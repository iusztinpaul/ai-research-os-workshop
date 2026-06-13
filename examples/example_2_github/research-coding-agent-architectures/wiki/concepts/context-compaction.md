---
type: concept
name: Context compaction
aliases: [compaction, summarization, context-window management, /compress, /compact]
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/session-persistence]], [[wiki/concepts/agent-loop]], [[wiki/concepts/subagent-delegation]], [[wiki/concepts/instruction-files]], [[wiki/entities/claude-code]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 12
confidence: high
---

# Context compaction

> The mechanism by which a harness keeps a long session inside the model's context window: when the transcript nears the limit, an LLM writes a summary that replaces older turns in the prompt — while the full history is preserved underneath.

## Definition

Context compaction (a.k.a. compression, `/compact`) is how all three studied harnesses reconcile unbounded session length with a bounded context window. The shared invariant is striking: **nothing is ever deleted**. Compaction produces an LLM-written summary layered over a durable transcript, and the prompt sent to the model becomes a derived artifact — a *view* over SQLite history in opencode [[wiki/sources/opencode]], a replay of the session tree "through the latest compaction entry" in pi [[wiki/sources/pi]], and a new child session linked by lineage in hermes-agent [[wiki/sources/hermes-agent]].

## Key claims

- In opencode, compaction is "a query, not a delete": the context window is a view anchored at the latest LLM-written structured summary (goal/progress/decisions/files template), with a preserved recent tail and incremental re-summarization; overflow replays the pending user message. [[wiki/sources/opencode]]
- opencode runs cheaper reclamation before summarizing: pruning erases stale tool outputs (protecting the last 2 turns / 40k tokens), and oversized tool outputs spill to disk with head/tail previews kept in context, readable back on demand. [[wiki/sources/opencode]]
- opencode's compactor is itself a hidden agent flowing through the same loop machinery as user-facing agents, with queued compaction work encoded in the persisted message data model. [[wiki/sources/opencode]]
- In pi, LLM context is "derived, never stored": `buildSessionContext()` replays the root-to-leaf path of the append-only JSONL tree through the latest compaction entry. Compaction triggers on `contextTokens > window − reserveTokens`, prefers turn-boundary cut points (never severing tool results from calls), re-summarizes iteratively with a memory-preserving UPDATE prompt, and cumulatively tracks read/modified files across compactions; abandoned branches can be re-injected as branch summaries. [[wiki/sources/pi]]
- pi applies compaction mid-run without restarting the loop: `prepareNextTurn` can swap context (and model) between turns, and compactions are first-class entries in the session log. [[wiki/sources/pi]]
- In hermes-agent, the default compressor of a pluggable `ContextEngine` summarizes middle turns and **splits the SQLite session** at every compaction — the old row ends with `end_reason='compression'`, a child is minted with `parent_session_id` — forming a lineage tree rather than rewriting history in place; it is the one sanctioned prompt-cache break, cross-process locked via a `compression_locks` table. [[wiki/sources/hermes-agent]]
- None of the three uses a vector store or embeddings for this; compaction-plus-persistence is the entire context-management story. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- hermes-agent explicitly indexes Claude Code's `/compact` among its influences. [[wiki/sources/hermes-agent]]

## Notable quotes

> "Compaction is a query, not a delete: history is never destroyed; the context window is a *view* anchored at the latest LLM-written structured summary."
> — [[wiki/sources/opencode]]

> "LLM context is *derived, never stored* — `buildSessionContext()` replays the root-to-leaf path through the latest compaction entry."
> — [[wiki/sources/pi]]

> "Compaction **splits the SQLite session** … rather than rewriting history in place; it is the one sanctioned prompt-cache break."
> — [[wiki/sources/hermes-agent]]

## Relationships

- **[[wiki/concepts/session-persistence]]**: compaction is defined relative to the persistence substrate — a view over an SQLite store (opencode), an entry in an append-only JSONL tree (pi), a session-split lineage in SQLite (hermes). [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/agent-loop]]**: compaction applies without restarting the loop — pi via `prepareNextTurn` context swaps, opencode via compaction work queued in the message model and run by a hidden agent. [[wiki/sources/pi]], [[wiki/sources/opencode]]
- **[[wiki/concepts/subagent-delegation]]**: the complementary window-management strategy — child transcripts stay out of the parent's context (only final text returns), reducing what compaction must absorb. [[wiki/sources/opencode]], [[wiki/sources/pi]]
- **[[wiki/concepts/instruction-files]]**: the memory tier compaction never touches — AGENTS.md/CLAUDE.md content is injected into the system prompt's stable tier, outside the summarized transcript. [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **[[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]**: named by hermes-agent as the direct influence for its `/compact` behavior. [[wiki/sources/hermes-agent]]

## Tensions

- **Session identity across a compaction**: opencode keeps one session and treats the compacted window as a view over never-destroyed history, while hermes-agent deliberately ends the session row and mints a new child per compaction — same no-deletion goal, opposite identity semantics. [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]]
- **Cache economics as a design driver**: hermes-agent frames compaction as "the one sanctioned prompt-cache break" under its byte-stable-prompt invariant; neither the opencode nor pi source pages weigh compaction against prompt-cache costs at all. [[wiki/sources/hermes-agent]] vs. [[wiki/sources/opencode]], [[wiki/sources/pi]]
- **Core vs. pluggable**: hermes-agent exposes the compressor as a swappable `ContextEngine`; opencode and pi bake their compactors into core (though pi's sits behind its general extension seams). [[wiki/sources/hermes-agent]] vs. [[wiki/sources/opencode]], [[wiki/sources/pi]]

## Open questions

- Both opencode ("incremental re-summarization") and pi ("memory-preserving UPDATE prompt") chain summaries of summaries — no source addresses fidelity degradation over many compaction generations. [[wiki/sources/opencode]], [[wiki/sources/pi]]
- opencode orders pruning (cheap) before summarizing (expensive); sources describe the mechanism but never compare whether prune-first measurably preserves more useful context than summarize-only designs. [[wiki/sources/opencode]]
- hermes-agent's `compression_locks` table implies concurrent compaction attempts across processes; how often this contention occurs, and what happens to in-flight turns during a split, is not covered. [[wiki/sources/hermes-agent]]

> Synthesis: Compaction is the strongest point of convergent evolution in this three-harness study — three independently designed systems (maximalist client/server, minimalist library, Python monolith) all landed on the same core contract: LLM-written summaries over an append-only record, with the live context recomputed rather than mutated. The interesting divergence is not *whether* to summarize but *what compaction is an event of* — a view update (opencode), a tree entry (pi), or a session-identity break driven by prompt-cache discipline (hermes-agent). That framing makes compaction a clean lens for the study's broader question of where each harness draws the line between derived state and durable state.
