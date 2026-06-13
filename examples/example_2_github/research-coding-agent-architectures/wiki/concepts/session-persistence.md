---
type: concept
name: Session persistence
aliases: [session storage, session model, state.db, JSONL sessions]
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/agent-loop]], [[wiki/concepts/context-compaction]], [[wiki/concepts/subagent-delegation]], [[wiki/concepts/permission-gating]], [[wiki/concepts/instruction-files]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 11
confidence: high
---

# Session persistence

> How a coding-agent harness durably records conversation/agent state so that runs are resumable, history is never destroyed, and the LLM context becomes a *view* derived from the persisted log.

## Definition

Session persistence is the storage substrate beneath the agent loop: the durable record of messages, tool calls, and run state that survives crashes and restarts. Across all three harnesses the design converges on an append-only, never-delete log from which the model's context window is *derived* rather than stored — but the storage shapes diverge sharply: opencode uses a SQLite event-sourced store [[wiki/sources/opencode]], pi uses a per-session append-only JSONL **tree** on disk [[wiki/sources/pi]], and hermes-agent uses a shared SQLite `state.db` whose sessions split into lineage rows at compaction [[wiki/sources/hermes-agent]]. pi's design notes push the broadest framing: the session is *all* durable agent state — model switches, compactions, and labels are first-class entries — not just transcript history [[wiki/sources/pi]].

## Key claims

- All three persist transcripts without a vector store: opencode is explicit that it has "no vector store, no embedding memory" [[wiki/sources/opencode]]; pi has "no vector store, no cross-session knowledge carryover" [[wiki/sources/pi]]; hermes stores SQLite transcripts with FTS5 keyword search instead of embeddings [[wiki/sources/hermes-agent]].
- Persistence enables resumability as a core loop property in opencode: the loop is stateless between iterations and re-derives intent from persisted messages each iteration, so crash recovery and "continue" are the same code path; queued subtask/compaction control flow is encoded in the persisted message data model itself. [[wiki/sources/opencode]]
- pi's session log is tree-shaped, not linear: entries carry `id` + `parentId`, "where you are" is a leaf pointer, and `buildSessionContext()` replays the root-to-leaf path through the latest compaction entry — context is derived, never stored. Nothing is deleted; abandoned branches can be re-injected as branch summaries. [[wiki/sources/pi]]
- Compaction interacts with persistence non-destructively in all three: opencode treats compaction as "a query, not a delete" (the window is a view anchored at the latest summary) [[wiki/sources/opencode]]; pi records compactions as entries in the tree [[wiki/sources/pi]]; hermes **splits the session** — ending the old SQLite row with `end_reason='compression'` and minting a child with `parent_session_id`, cross-process locked via a `compression_locks` table — rather than rewriting history in place. [[wiki/sources/hermes-agent]]
- Subagent state rides on the session model: opencode subagents are child sessions linked by `parentID`, inspectable and resumable via `task_id` [[wiki/sources/opencode]]; pi's reference extension spawns children with `--no-session`, deliberately leaving child runs unpersisted [[wiki/sources/pi]].
- Persistence is expanding beyond transcripts in opencode: the v2 rewrite is event-sourced and persists permission approvals in SQLite (saved grants that never override configured denies). [[wiki/sources/opencode]]
- pi adds small durability craftsmanship: lazy first-flush (no session file until the first assistant message) and cloud-sync-ignore xattrs on session files. [[wiki/sources/pi]]

## Notable quotes

> "Treat session as all durable agent state, not just transcript history."
> — [[wiki/sources/pi]]

> "opencode has no vector store, no embedding memory, and no model-written 'memory file'."
> — [[wiki/sources/opencode]]

## Relationships

- **[[wiki/concepts/agent-loop]]**: opencode's loop is history-driven — each iteration re-derives intent from persisted messages, making the session log the loop's actual state machine. [[wiki/sources/opencode]]
- **[[wiki/concepts/context-compaction]]**: compaction is the main consumer of the persistence layer; all three keep full history and represent compaction as an anchor, entry, or session split on top of it. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/subagent-delegation]]**: whether child runs get sessions at all is a design axis — parentID-linked child sessions (opencode) vs. `--no-session` child processes (pi). [[wiki/sources/opencode]], [[wiki/sources/pi]]
- **[[wiki/concepts/permission-gating]]**: opencode v2 persists approval grants in the same SQLite store, folding policy state into session state. [[wiki/sources/opencode]]
- **[[wiki/concepts/instruction-files]]**: instruction files (AGENTS.md/CLAUDE.md/MEMORY.md) are the cross-session memory channel that sits *outside* the per-session log in all three harnesses. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

## Tensions

- **Database vs. flat file**: opencode and hermes persist to SQLite (opencode converging on event-sourcing in v2; hermes a shared `state.db` with FTS5), while pi deliberately uses plain append-only JSONL files per session. [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]] vs. [[wiki/sources/pi]]
- **Where branching lives**: pi puts branches *inside* one log (id/parentId tree with a leaf pointer); hermes branches *across* session rows (lineage tree via `parent_session_id` splits at compaction); opencode keeps one session and anchors a view at the latest summary. Three different answers to what a session's identity is across compaction. [[wiki/sources/pi]] vs. [[wiki/sources/hermes-agent]] vs. [[wiki/sources/opencode]]
- **Cross-session carryover**: pi explicitly persists nothing across sessions beyond instruction files, while hermes layers curated MEMORY.md/USER.md and external provider plugins on top of its transcripts. [[wiki/sources/pi]] vs. [[wiki/sources/hermes-agent]]

## Open questions

- How does opencode's v1→v2 event-sourced rewrite change session semantics (the sources note the rewrite and SQLite-persisted approvals, but not the v2 session/message schema itself)? [[wiki/sources/opencode]]
- Does hermes's session-splitting preserve full resumability of pre-split lineage (can a parent row be resumed, or only its compression child)? Sources describe the split mechanics but not resume behavior. [[wiki/sources/hermes-agent]]
- pi's `AgentHarness` is described as "session-tree-aware," but the sources don't detail how it differs from `Agent` in persistence responsibilities. [[wiki/sources/pi]]

> Synthesis: Session persistence is where the three harnesses agree on principle and diverge on substrate. The shared principle — append-only history, context as a derived view, compaction as a non-destructive marker — is arguably the strongest cross-harness convergence in this study, and it makes resumability a free consequence of storage design rather than a feature. The divergence (event-sourced SQLite vs. JSONL tree vs. session-splitting lineage rows) tracks each harness's overall pole: opencode's server-grade database engine, pi's inspectable user-space files, hermes's monolith-wide shared state.db. Watching whether opencode v2 folds ever more state (permissions, events) into the session store is the clearest signal of where the "session = all durable agent state" thesis is heading.
