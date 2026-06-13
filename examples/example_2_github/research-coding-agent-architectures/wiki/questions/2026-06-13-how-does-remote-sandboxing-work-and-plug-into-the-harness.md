---
type: question
name: How does remote sandboxing work and how is it plugged into the harness?
asked_on: 2026-06-13
sources_cited: [wiki/sources/hermes-agent, wiki/sources/pi]
answer_doc: wiki/concepts/sandboxing.md
---

# How does remote sandboxing work and how is it plugged into the harness?

> Asked on 2026-06-13. Answered using 2 source(s) and 3 wiki page(s).

## Answer

Full answer lives at **[[wiki/concepts/sandboxing|Sandboxing]]** (see the "How remote sandboxing works & how it plugs into the harness" section).

It covers:
- Six pluggable `BaseEnvironment` backends; `env_type` from `TERMINAL_ENV`
- Remote = Modal/Daytona serverless runners with hibernating persistence
- `task_id`-scoped terminal sessions per conversation/subagent
- Wiring: `terminal_tool()` → `check_all_command_guards()` on every command
- Sandbox short-circuit returns approved immediately (`approval.py:1283-1284`)
- Only `local`/`ssh` gate; isolation = permission model

## Why this matters

Lets Paul design his own harness's execution layer knowing exactly where the security boundary sits (OS/container) vs. where in-process gating is just UX for unsandboxed runs.

> Synthesis: A source detailing Modal/Daytona's actual remote protocol (how commands ship to the runner, hibernation lifecycle, credential scoping) would extend this; so would resolving whether HARDLINE patterns survive inside sandboxes.
