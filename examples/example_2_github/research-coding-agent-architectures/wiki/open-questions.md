# Open questions

## [2026-06-12] from ingest of 3 source(s)

### from [[wiki/concepts/acp]]
- Neither source page states who specifies ACP or which protocol version these harnesses implement — provenance and spec stability are unaddressed.
- Does ACP carry interactive permission-approval traffic (so an IDE can answer asks), or only prompt/response and edit streams? opencode's multi-client permission answering suggests yes for its architecture, but neither source says so for ACP specifically.

### from [[wiki/concepts/agent-loop]]
- How does opencode's v1 → v2 event-sourced engine rewrite change the loop itself? Sources detail its permission/store implications but not loop-level consequences. [[wiki/sources/opencode]]
- pi carries two stateful wrappers (`Agent`, used by the CLI, and the newer session-tree-aware `AgentHarness`) — which becomes canonical, and does session-tree awareness migrate into `runLoop`? [[wiki/sources/pi]]
- pi's steering/follow-up queues and hermes' steer draining suggest convergence on mid-run injection as a first-class loop concept; opencode's equivalent mechanism is not described in the sources. [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

### from [[wiki/concepts/context-compaction]]
- Both opencode ("incremental re-summarization") and pi ("memory-preserving UPDATE prompt") chain summaries of summaries — no source addresses fidelity degradation over many compaction generations. [[wiki/sources/opencode]], [[wiki/sources/pi]]
- opencode orders pruning (cheap) before summarizing (expensive); sources describe the mechanism but never compare whether prune-first measurably preserves more useful context than summarize-only designs. [[wiki/sources/opencode]]
- hermes-agent's `compression_locks` table implies concurrent compaction attempts across processes; how often this contention occurs, and what happens to in-flight turns during a split, is not covered. [[wiki/sources/hermes-agent]]

### from [[wiki/concepts/instruction-files]]
- Do subagent/child sessions re-discover instruction files independently, inherit the parent's resolved set, or get none? No source specifies.
- How does opencode's "context epochs with drift detection" mechanism behave when instruction files change mid-session, and what is the cache cost? The mechanism is named but not explained at this layer. [[wiki/sources/opencode]]
- Is hermes-agent's single-file policy a prompt-budget decision or a conflict-avoidance decision? The priority order is documented but not the rationale. [[wiki/sources/hermes-agent]]

### from [[wiki/concepts/mcp]]
- How opencode's MCP integration actually works beyond the registry diagram — discovery, configuration, and how MCP tool identities map onto its (capability, pattern) permission rules — is not covered by the source pages. [[wiki/sources/opencode]]
- Whether hermes-agent's MCP-exposed `permissions_respond` widens the attack/approval surface (remote parties answering permission asks) is not addressed. [[wiki/sources/hermes-agent]]
- Whether pi users actually rebuild MCP support as a userland extension in practice — the sources document the seam, not its uptake. [[wiki/sources/pi]]

### from [[wiki/concepts/permission-gating]]
- How does opencode's V1→V2 migration resolve — does deny-by-default with SQLite-persisted approvals fully replace the in-memory ask-by-default engine? [[wiki/sources/opencode]]
- Is arity generalization of "always" grants (`git push origin main` → `git push *`) safe in practice, or does it over-broaden approvals? [[wiki/sources/opencode]]
- Can hermes's auxiliary-LLM "smart" reviewer be trusted as an approval surface — sources describe the mechanism but never evaluate its failure modes. [[wiki/sources/hermes-agent]]

### from [[wiki/concepts/sandboxing]]
- Does hermes-agent's unconditional hardline floor still apply inside sandboxed backends? One claim says those backends "skip the entire approval stack," another says hardline patterns "block unconditionally before any bypass" — the sources don't reconcile the two. [[wiki/sources/hermes-agent]]
- pi defers isolation entirely to the user, but the sources don't document what containment setup pi expects in practice (container, VM, dedicated user), nor any threat model for network or credential access. [[wiki/sources/pi]]
- Only two of the three studied harnesses engage with sandboxing at all; where the third (opencode) sits on the in-process-gates vs. OS-boundary spectrum is unresolved in the current wiki.

### from [[wiki/concepts/session-persistence]]
- How does opencode's v1→v2 event-sourced rewrite change session semantics (the sources note the rewrite and SQLite-persisted approvals, but not the v2 session/message schema itself)? [[wiki/sources/opencode]]
- Does hermes's session-splitting preserve full resumability of pre-split lineage (can a parent row be resumed, or only its compression child)? Sources describe the split mechanics but not resume behavior. [[wiki/sources/hermes-agent]]
- pi's `AgentHarness` is described as "session-tree-aware," but the sources don't detail how it differs from `Agent` in persistence responsibilities. [[wiki/sources/pi]]

### from [[wiki/concepts/subagent-delegation]]
- Are hermes child transcripts persisted and resumable (like opencode's `task_id` children), or lost beyond the result envelope? Sources describe persistence for opencode and ephemerality for pi, but are silent for hermes. [[wiki/sources/hermes-agent]]
- How does opencode's experimental background mode (promotion, steering, synthetic message injection) interact with its async multi-client permission asks once stabilized? [[wiki/sources/opencode]]
- None of the sources quantify the token/cost economics of delegation versus compaction as context-management strategies. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

### from [[wiki/concepts/tool-registry]]
- Do opencode and pi suffer prompt-cache invalidation when the advertised tool list changes mid-session, the hazard hermes explicitly designs against? Sources don't say. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- Whether extension-registered tools in pi pass through the same file-mutation queue and sequential-prepare guarantees as the seven built-ins is not specified. [[wiki/sources/pi]]
- How opencode's plugin tools register and whether they receive the same `ctx.ask` discipline as built-ins is asserted only at the diagram level, not mechanically detailed. [[wiki/sources/opencode]]

### from [[8 - Projects/Building Your Own AI Research OS/example_2_github/research-coding-agent-architectures/wiki/entities/claude-code]]
- The corpus only sees Claude Code through emulation surfaces — how faithful are these reimplementations (pi's skills compatibility, hermes-agent's `/compact`-inspired compaction) to Claude Code's actual behavior? [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- hermes-agent ranks `AGENTS.md` above `CLAUDE.md` while opencode and pi treat them as peers — is the vendor-neutral `AGENTS.md` displacing `CLAUDE.md` as the standard instruction-file name? [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

