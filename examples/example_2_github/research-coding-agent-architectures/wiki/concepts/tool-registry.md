---
type: concept
name: Tool registry
aliases: [tool surface, tool execution pipeline, built-in tools]
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/agent-loop]], [[wiki/concepts/permission-gating]], [[wiki/concepts/subagent-delegation]], [[wiki/concepts/mcp]], [[wiki/concepts/instruction-files]], [[wiki/concepts/sandboxing]], [[wiki/concepts/context-compaction]], [[wiki/entities/claude-code]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 11
confidence: high
---

# Tool registry

> The harness subsystem that defines which tools exist, which subset the model actually sees, and the pipeline each tool call passes through on its way to execution.

## Definition

A tool registry is the catalog of capabilities a coding agent can invoke — file reads/writes, shell, search, delegation — plus the machinery that advertises a subset of them to the model and shepherds each call through preparation, gating, execution, and result handling. All three harnesses treat it as a primary architectural seam, but they size it very differently: opencode's registry spans built-in, MCP, and plugin tools wired into a permission service [[wiki/sources/opencode]]; pi's surface is deliberately exactly seven built-ins (`read | bash | edit | write | grep | find | ls`) with everything else pushed to user-space extensions [[wiki/sources/pi]]; hermes-agent has a singleton `ToolRegistry` where tools self-register at import time but named **toolsets** decide actual exposure [[wiki/sources/hermes-agent]].

## Key claims

- Registration and exposure are distinct concerns: hermes tools self-register into a singleton registry, but a named toolset controls what an agent sees ("registration ≠ exposure"), and mid-conversation toolset swaps are forbidden to keep the system prompt byte-stable for prompt caching. [[wiki/sources/hermes-agent]]
- opencode controls exposure through permissions instead: tools denied by the ruleset are stripped from the model's advertised tool list, making tool advertisement itself a permission-rule artifact. [[wiki/sources/opencode]]
- Execution pipelines are explicit, ordered stages: pi runs every tool through prepare → hook → execute → finalize; calls execute in parallel by default but are *prepared sequentially* so gate hooks fire in order, any tool can force a sequential batch, and file mutations serialize through a file-mutation queue. [[wiki/sources/pi]]
- Where tool execution happens diverges: opencode tools run *inside* the provider stream (`streamText`), not in a harness-side dispatch loop; hermes dispatches tool batches through a thread pool between synchronous API calls. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]
- Growth policy is doctrine, not accident: hermes' "Footprint Ladder" dictates new capability lands as skills, plugins, or MCP servers, almost never as new core tools; pi ships chokepoints (`registerTool`, `registerProvider`, the `tool_call` hook) and expects "missing" tools to be rebuilt as extensions. [[wiki/sources/hermes-agent]], [[wiki/sources/pi]]
- Tool errors are model-facing data, not exceptions: pi's gate blocks become error tool results fed back to the model; hermes' deny messages are explicit instructions ("Do NOT retry this command…"). [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- Subagent capability attenuation is computed over the registry: hermes children get parent's tools ∩ requested − `DELEGATE_BLOCKED_TOOLS` (blocking `clarify`, `memory`, `send_message`, `execute_code`, recursion). [[wiki/sources/hermes-agent]]

## Notable quotes

> "Permission identity is a **(capability, pattern) pair evaluated against an ordered wildcard ruleset**, not a boolean per tool — granularity is delegated to each tool's choice of pattern (command prefix, file path, subagent name, URL)."
> — [[wiki/sources/opencode]]

## Relationships

- **[[wiki/concepts/agent-loop]]**: the registry is the loop's effector layer — opencode executes tools inside the provider stream, hermes between synchronous loop iterations via a thread pool, pi inside its pure `runLoop` with injected side effects. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]], [[wiki/sources/pi]]
- **[[wiki/concepts/permission-gating]]**: gating attaches at the registry boundary — opencode's `ctx.ask` inside every tool, pi's first-block-wins `tool_call` hook chain, hermes' regex pattern gates over command content rather than tool identity. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/subagent-delegation]]**: delegation is itself a registry entry (`task` in opencode, `delegate_task` in hermes) or deliberately absent from core (pi). [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]], [[wiki/sources/pi]]
- **[[wiki/concepts/mcp]]**: MCP is one registry extension channel — first-class in opencode and on both client and server sides in hermes, explicitly rejected in pi. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]], [[wiki/sources/pi]]
- **[[wiki/concepts/instruction-files]]**: skills (markdown, lazily read, progressive disclosure) are pi's stated no-MCP alternative to growing the tool surface, and the hermes Footprint Ladder's preferred landing spot; pi's skill format is [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/wiki/entities/claude-code]]-compatible. [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/sandboxing]]**: in hermes, sandboxed execution backends (docker/modal/daytona) skip the registry's approval stack entirely — isolation substitutes for per-tool gating. [[wiki/sources/hermes-agent]]
- **[[wiki/concepts/context-compaction]]**: tool outputs are first-class memory pressure — opencode prunes stale tool outputs and spills oversized ones to disk with head/tail previews before resorting to summarization. [[wiki/sources/opencode]]

## Tensions

- **MCP as registry extension**: opencode and hermes-agent embrace MCP as a tool-surface growth channel; pi excludes it by philosophy, substituting TypeScript extensions and lazily-read skills. [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]] vs. [[wiki/sources/pi]]
- **Exposure-control mechanism**: opencode derives the advertised tool list from permission rules (dynamic per ruleset), while hermes freezes exposure via named toolsets for the conversation's lifetime to protect the prompt cache — two incompatible answers to the same problem. [[wiki/sources/opencode]] vs. [[wiki/sources/hermes-agent]]
- **Where new tools belong**: hermes bars new core tools by doctrine, pi bars built-in features themselves, opencode ships a comparatively full built-in registry and disciplines it with permissions — a three-way disagreement about who owns the tool surface. [[wiki/sources/hermes-agent]], [[wiki/sources/pi]], [[wiki/sources/opencode]]

## Open questions

- Do opencode and pi suffer prompt-cache invalidation when the advertised tool list changes mid-session, the hazard hermes explicitly designs against? Sources don't say. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- Whether extension-registered tools in pi pass through the same file-mutation queue and sequential-prepare guarantees as the seven built-ins is not specified. [[wiki/sources/pi]]
- How opencode's plugin tools register and whether they receive the same `ctx.ask` discipline as built-ins is asserted only at the diagram level, not mechanically detailed. [[wiki/sources/opencode]]

> Synthesis: The tool registry is where each harness's whole philosophy becomes legible: opencode unifies registry and policy (permissions decide both what runs and what the model even sees), pi shrinks the registry to seven primitives and exports the rest as a seam, and hermes splits registration from exposure to serve a cache invariant while routing growth around the core via its Footprint Ladder. For the comparative study, "how big is the registry and who may extend it" is arguably the single best one-question proxy for classifying a coding-agent harness.
