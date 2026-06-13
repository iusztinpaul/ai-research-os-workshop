---
type: concept
name: ACP (Agent Client Protocol)
aliases: [Agent Client Protocol]
sources: [[[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/mcp]], [[wiki/concepts/subagent-delegation]], [[wiki/concepts/agent-loop]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 2
mention_count: 6
confidence: medium
---

# ACP (Agent Client Protocol)

> A protocol that lets editors/IDEs act as frontends to a coding-agent harness — the client-side counterpart to MCP's tool-side bridging.

## Definition

ACP (Agent Client Protocol) is the standard interface by which an IDE or editor drives a coding-agent harness as an external client. Both harnesses that implement it treat ACP as one more *surface* over their existing core rather than a separate integration layer: in opencode the ACP/IDE bridge is just another client of the engine's HTTP API and SSE event stream, interchangeable with the TUI, desktop, and web frontends [[wiki/sources/opencode]]; in hermes-agent an ACP server is one of the many faces (CLI, TUI, desktop, messaging gateway, cron) that all construct and drive the same in-process `AIAgent` object [[wiki/sources/hermes-agent]].

The two architectures reach ACP support from opposite directions: opencode's server-first design makes IDE bridging nearly free, since ACP rides the same OpenAPI/SSE contract every other client uses [[wiki/sources/opencode]], while hermes-agent bolts an ACP server onto a monolith that has no client/server split at all [[wiki/sources/hermes-agent]].

## Key claims

- In opencode, every user surface — TUI, desktop app, web app, IDE bridge (ACP), headless CLI — is an interchangeable client of one local HTTP server with an SSE event stream. [[wiki/sources/opencode]]
- opencode's server-first architecture "buys multi-client permission answering, live subagent inspection, and IDE bridging for free" — ACP support is a byproduct of the client/server split, not a bespoke subsystem. [[wiki/sources/opencode]]
- hermes-agent runs an ACP server for IDEs as one of its frontends, alongside sitting on both sides of MCP (client and server). [[wiki/sources/hermes-agent]]
- hermes-agent also uses ACP *outbound*: `delegate_task` can spawn a foreign harness as a child agent over ACP via `acp_command` — turning the protocol from an editor bridge into a cross-harness delegation mechanism. [[wiki/sources/hermes-agent]]

## Notable quotes

> "Hermes sits on both sides of MCP (client via `tools/mcp_tool.py`, server via `mcp_serve.py` exposing conversations and even `permissions_respond`) and speaks ACP to editors; `delegate_task` can even spawn a foreign harness as a child over ACP (`acp_command`)."
> — [[wiki/sources/hermes-agent]]

> "Every user surface — TUI, desktop app, web app, IDE bridge (ACP), headless CLI — is just another client of that server."
> — [[wiki/sources/opencode]]

## Relationships

- **MCP**: Complementary protocol bridge — MCP standardizes how harnesses consume/expose *tools*, ACP standardizes how *clients* (editors) drive harnesses; hermes-agent implements both sides of both. [[wiki/concepts/mcp]], [[wiki/sources/hermes-agent]]
- **Subagent delegation**: hermes-agent's `acp_command` extends delegation beyond in-process children to foreign harnesses spoken to over ACP. [[wiki/concepts/subagent-delegation]], [[wiki/sources/hermes-agent]]
- **Agent loop**: In both harnesses ACP is a thin adapter over the single shared loop (opencode's `SessionPrompt.runLoop` behind HTTP; hermes' `AIAgent.run_conversation()`), not a second execution path. [[wiki/concepts/agent-loop]], [[wiki/sources/opencode]], [[wiki/sources/hermes-agent]]

## Tensions

_No notable disagreements across sources._ The sources differ in architectural placement (RPC client of a server vs. face of a monolith), but agree on what ACP is for.

## Open questions

- Neither source page states who specifies ACP or which protocol version these harnesses implement — provenance and spec stability are unaddressed.
- Does ACP carry interactive permission-approval traffic (so an IDE can answer asks), or only prompt/response and edit streams? opencode's multi-client permission answering suggests yes for its architecture, but neither source says so for ACP specifically.

> Synthesis: ACP is the clearest marker of where each harness sits on the integration-surface spectrum in this study: opencode gets it almost free from its client/server split, hermes-agent grafts it onto a monolith and then doubles its role into a cross-harness delegation channel, and pi (per this run's scope) does not engage with it at all — suggesting ACP adoption tracks how much a harness wants to live inside other people's frontends.
