---
type: concept
name: Permission gating
aliases: [permission system, approval flow, ask/allow/deny]
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/sandboxing]], [[wiki/concepts/subagent-delegation]], [[wiki/concepts/tool-registry]], [[wiki/concepts/agent-loop]], [[wiki/concepts/mcp]], [[wiki/entities/claude-code]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 20
confidence: high
---

# Permission gating

> The mechanism by which a coding-agent harness decides whether a tool invocation (shell command, file write, spawn) executes, asks a human, or is denied — the three harnesses span the full spectrum from built-in policy engine to deliberate absence.

## Definition

Permission gating sits on the tool-execution path of the [[wiki/concepts/agent-loop]] and answers one question per call: run, ask, or deny. The three harnesses give three irreconcilable framings. opencode makes it a core declarative engine: every irreversible action funnels through one API (`ctx.ask`) evaluated against an ordered wildcard ruleset [[wiki/sources/opencode]]. hermes-agent makes it detection-based: regex pattern taxonomies gate command *content*, not tool identity [[wiki/sources/hermes-agent]]. pi ships no permission system at all — gating is a user-space extension hook plus OS-level containment [[wiki/sources/pi]].

## Key claims

- opencode's permission identity is a (capability, pattern) pair against an ordered, last-match-wins ruleset (default `ask`); merge order *is* precedence (defaults → agent → user config → session → in-session approvals), and "modes" like plan/build are just ruleset deltas. [[wiki/sources/opencode]]
- opencode's ask is async and multi-client: the tool's fiber parks on an Effect `Deferred` while a `permission.asked` event fans out; any attached UI answers over HTTP; "always" grants generalize bash commands by arity (`git push origin main` → `git push *`); rejection feedback becomes the model-facing error text. [[wiki/sources/opencode]]
- In opencode, permissions are the unifying abstraction: doom-loop safety, tool advertisement (denied tools stripped from the model's list), subagent catalogs, and truncated-output file access are all expressed as permission rules; subagent isolation is permission-based, not process-based. [[wiki/sources/opencode]]
- Two opencode engines coexist at the studied commit: production V1 (in-memory "always" grants, ask-by-default) and a V2 rewrite (action/resource/effect model, SQLite-persisted approvals, deny-by-default, saved grants never override configured denies). [[wiki/sources/opencode]]
- pi's only runtime gate is the synchronous `tool_call` extension hook chain — first block wins, with mutable `event.input` enabling argument rewriting; blocks become error tool results fed back to the model, never exceptions, and gate failures or headless trust prompts default to deny. [[wiki/sources/pi]]
- pi's project-trust gate covers *input loading* and resolves before project extensions load, so an untrusted repo cannot inject the gate code itself. [[wiki/sources/pi]]
- hermes-agent layers pattern-keyed gates: `HARDLINE_PATTERNS` block unconditionally before any bypass — no mode, `--yolo` included, can override — while ~60 `DANGEROUS_PATTERNS` route to one of three approval surfaces (CLI modal, chat-gateway `/approve` queue, auxiliary-LLM "smart" reviewer) with once/session/always scopes keyed by pattern, not literal command. [[wiki/sources/hermes-agent]]
- hermes-agent is structurally barred from editing its own policy: file tools hard-deny writes to `config.yaml`, paired with terminal-side patterns against `sed -i`/`tee`/`>` on the same targets — "an unpaired deny is theater". [[wiki/sources/hermes-agent]]
- Subagents get attenuated gating, never escalation: hermes worker threads install a non-interactive auto-deny callback (avoiding stdin deadlock); opencode children inherit only the parent's deny rules plus `external_directory` grants, with recursive spawning deny-by-default. [[wiki/sources/hermes-agent]], [[wiki/sources/opencode]]
- Sandboxed execution substitutes for gating in hermes: docker/singularity/modal/daytona backends skip the entire approval stack — isolation *is* the permission model. [[wiki/sources/hermes-agent]]

## Notable quotes

> "Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access. By default, it runs with the permissions of the user and process that launched it."
> — [[wiki/sources/pi]]

> "Permission identity is a **(capability, pattern) pair evaluated against an ordered wildcard ruleset**, not a boolean per tool — granularity is delegated to each tool's choice of pattern (command prefix, file path, subagent name, URL)."
> — [[wiki/sources/opencode]]

> "Do NOT retry this command, do NOT rephrase it, and do NOT attempt the same outcome via a different command. … Silence is not consent."
> — [[wiki/sources/hermes-agent]]

## Relationships

- **[[wiki/concepts/sandboxing]]**: the complement/substitute — pi names OS containment the only real security boundary, and hermes's sandbox backends bypass approvals entirely. [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/subagent-delegation]]**: children run under derived, attenuation-only rulesets (auto-deny callbacks, deny-rule inheritance). [[wiki/sources/hermes-agent]], [[wiki/sources/opencode]]
- **[[wiki/concepts/tool-registry]]**: gating shapes what the model even sees — opencode strips denied tools from the advertised list; hermes separates registration from exposure via toolsets. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/agent-loop]]**: gates execute on the tool-dispatch path — pi prepares tool calls sequentially precisely so gate hooks run in order. [[wiki/sources/pi]]
- **[[wiki/concepts/mcp]]**: hermes's MCP server exposes `permissions_respond`, letting external clients answer approvals. [[wiki/sources/hermes-agent]]
- **[[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]**: hermes openly indexes Claude Code's deny rules (and OpenAI Codex's smart approvals) among its influences. [[wiki/sources/hermes-agent]]

## Tensions

- **Is in-process gating worth building at all?** pi's stance is that in-process permission systems are theater and "real isolation needs to come from the operating system"; opencode builds its entire harness *around* an in-process permission engine as the unifying abstraction. hermes splits the difference — deep in-process gates locally, total bypass inside sandboxes. [[wiki/sources/pi]] vs. [[wiki/sources/opencode]]; [[wiki/sources/hermes-agent]]
- **What is the gated identity?** Declaration-based (capability, pattern) rules over tool identity in opencode vs. detection-based regex over command content in hermes — two incompatible answers to "what does a rule match?". [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]]
- **Default posture diverges**: opencode V1 asks by default (V2 moves to deny-by-default); hermes runs most shell commands unprompted; pi runs with the launching user's full permissions. [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]] vs. [[wiki/sources/pi]]

## Open questions

- How does opencode's V1→V2 migration resolve — does deny-by-default with SQLite-persisted approvals fully replace the in-memory ask-by-default engine? [[wiki/sources/opencode]]
- Is arity generalization of "always" grants (`git push origin main` → `git push *`) safe in practice, or does it over-broaden approvals? [[wiki/sources/opencode]]
- Can hermes's auxiliary-LLM "smart" reviewer be trusted as an approval surface — sources describe the mechanism but never evaluate its failure modes. [[wiki/sources/hermes-agent]]

> Synthesis: Permission gating is the sharpest differentiator among the three harnesses and arguably the axis the whole comparative study turns on. The three positions form a clean spectrum — pi externalizes the policy (hooks + OS), hermes detects risk in content with an unbypassable floor, opencode declares policy as data and makes it the organizing principle of the entire engine — and each position is load-bearing for that harness's subagent, tool-exposure, and sandboxing choices. Notably, all three converge on one point from opposite directions: the only gate everyone trusts unconditionally is the one outside the agent's own process or reach (OS isolation, hardline floors, self-edit denies).
