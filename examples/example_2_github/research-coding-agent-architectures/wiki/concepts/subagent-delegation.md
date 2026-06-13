---
type: concept
name: Subagent delegation
aliases: [task tool, delegate_task, child agents, nested agents]
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/agent-loop]], [[wiki/concepts/permission-gating]], [[wiki/concepts/session-persistence]], [[wiki/concepts/context-compaction]], [[wiki/concepts/tool-registry]], [[wiki/concepts/acp]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 16
confidence: high
---

# Subagent delegation

> The pattern where a coding agent spawns a child agent to run a scoped task in an isolated context, returning only a condensed result to the parent — implemented as child sessions, child processes, or child threads depending on the harness.

## Definition

Subagent delegation lets a parent agent hand a task to a child agent whose full transcript stays out of the parent's context window; only a final result crosses back. The three harnesses agree on that contract but disagree on everything else: opencode ships it in core as the `task` tool spawning child *sessions* [[wiki/sources/opencode]]; pi deliberately ships **no** subagent machinery, expecting users to build it as an extension that spawns child OS *processes* [[wiki/sources/pi]]; hermes-agent ships it in core as the `delegate_task` tool spawning child `AIAgent` objects on in-process *threads* [[wiki/sources/hermes-agent]].

## Key claims

- All three designs share one invariant: only the child's final/condensed output returns to the parent's context — opencode returns final text as the tool result, pi's extension returns only the child's final assistant text (full transcript in a UI-only `details` channel), hermes returns a rich result envelope (summary + tokens + cost + files touched). [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- In opencode, subagents are child sessions linked by `parentID`, running the same full loop; the child transcript is inspectable and resumable via `task_id`. Isolation is permission-based, not process-based: children inherit only the parent's deny rules + `external_directory` grants, and recursive `task` spawning is deny-by-default. [[wiki/sources/opencode]]
- opencode has an experimental background mode: children run async, results are injected into the parent as synthetic messages, and running children can be promoted and steered mid-flight. [[wiki/sources/opencode]]
- pi has zero subagent machinery in core, by explicit philosophy; the canonical ~1,000-line reference extension spawns child `pi` OS processes in headless JSON mode (`pi --mode json -p --no-session`) and parses their JSONL stdout. Context isolation = process isolation. [[wiki/sources/pi]]
- pi's userland orchestration vocabulary is richer than typical task tools: single, parallel (≤8 tasks, ≤4 concurrent, 50 KB output cap), and chain mode with `{previous}` substitution. [[wiki/sources/pi]]
- hermes children run on in-process worker threads (never subprocesses), block the parent, and are attenuation-only: tools = parent's tools ∩ requested − `DELEGATE_BLOCKED_TOOLS` (`clarify`, `memory`, `send_message`, `execute_code`, recursion). There is no named-agent registry — roles and goals instead; nesting requires an `orchestrator` role plus `max_spawn_depth ≥ 2` opt-in. [[wiki/sources/hermes-agent]]
- hermes children cannot escalate to the user: a non-interactive auto-deny callback is installed per worker thread (avoiding stdin deadlock against the parent TUI), flipped to auto-approve only by explicit `delegation.subagent_auto_approve: true`. [[wiki/sources/hermes-agent]]
- hermes's `delegate_task` can even spawn a *foreign* harness as a child over ACP (`acp_command`). [[wiki/sources/hermes-agent]]

## Notable quotes

> "No sub-agents. There's many ways to do this. Spawn pi instances via tmux, or build your own with [extensions], or install a package that does it your way."
> — [[wiki/sources/pi]]

## Relationships

- **Agent loop**: every harness's child runs the same loop as the parent — a child session through opencode's shared loop, a whole child `pi` process, a child `AIAgent` instance. [[wiki/concepts/agent-loop]] [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **Permission gating**: child isolation is expressed through the permission layer — derived deny-rulesets in opencode, blocked-tool attenuation plus auto-deny callbacks in hermes. [[wiki/concepts/permission-gating]] [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]
- **Session persistence**: opencode children are real persisted sessions (resumable via `task_id`); pi's reference children run `--no-session`, i.e., ephemeral by default. [[wiki/concepts/session-persistence]] [[wiki/sources/opencode]], [[wiki/sources/pi]]
- **Context compaction**: delegation is the complementary context-economy lever — keep child transcripts out of the parent window instead of summarizing them after the fact. [[wiki/concepts/context-compaction]] [[wiki/sources/opencode]], [[wiki/sources/pi]]
- **Tool registry**: what a child may use is computed from the registry — hermes intersects/subtracts toolsets; opencode strips denied tools from the model's list. [[wiki/concepts/tool-registry]] [[wiki/sources/hermes-agent]], [[wiki/sources/opencode]]
- **ACP**: hermes uses the protocol as a delegation transport, spawning foreign harnesses as children. [[wiki/concepts/acp]] [[wiki/sources/hermes-agent]]

## Tensions

- **Core feature vs. user-space seam**: opencode and hermes bake delegation into core as a tool; pi explicitly rejects built-in subagents and ships only the extension chokepoints. [[wiki/sources/pi]] vs. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]
- **Isolation mechanism — three incompatible answers**: opencode argues permission-based isolation suffices (no processes); pi equates context isolation with process isolation; hermes uses in-process threads and *never* subprocesses. [[wiki/sources/opencode]] vs. [[wiki/sources/pi]] vs. [[wiki/sources/hermes-agent]]
- **Concurrency posture**: opencode's background mode makes children async, steerable, and promotable; hermes's `delegate_task` blocks the parent thread; pi's parallel mode allows bounded concurrency but inside one blocking extension call. [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]], [[wiki/sources/pi]]

## Open questions

- Are hermes child transcripts persisted and resumable (like opencode's `task_id` children), or lost beyond the result envelope? Sources describe persistence for opencode and ephemerality for pi, but are silent for hermes. [[wiki/sources/hermes-agent]]
- How does opencode's experimental background mode (promotion, steering, synthetic message injection) interact with its async multi-client permission asks once stabilized? [[wiki/sources/opencode]]
- None of the sources quantify the token/cost economics of delegation versus compaction as context-management strategies. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

> Synthesis: Subagent delegation is where the three harnesses' philosophies diverge most cleanly while their contract converges: all agree the parent should see only a condensed result, but each derives its isolation story from its general architecture — opencode's permission-engine-as-unifier yields session children gated by rulesets, pi's minimal core yields process children built in userland, and hermes's monolith yields thread children disciplined by toolset attenuation and auto-deny. For the comparative study, delegation is thus the best single probe: ask how a harness spawns a child, and its whole architecture answers.
