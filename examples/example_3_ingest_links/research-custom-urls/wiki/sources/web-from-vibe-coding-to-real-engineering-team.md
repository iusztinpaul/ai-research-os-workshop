---
type: source
title: From Vibe Coding to a Real Engineering Team
original_path: https://www.decodingai.com/p/squid-my-agentic-coding-setup-may-2026
raw_file: raw/web-from-vibe-coding-to-real-engineering-team.md
assets: []
authors: ["Paul Iusztin"]
published_date: 2026-05-12
relevance_score: 1.0
ingested: 2026-06-13T09:53:48Z
last_updated: 2026-06-13T09:53:48Z
entities: []
concepts: []
---

# From Vibe Coding to a Real Engineering Team

> [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|Raw source]] · [Original](https://www.decodingai.com/p/squid-my-agentic-coding-setup-may-2026) · score 1.00 · web

## Summary
This article documents **Squid**, an opinionated six-agent Claude Code setup ([iusztinpaul/squid](https://github.com/iusztinpaul/squid)) that ships features the way a real software team does. It opens with a failure story: the author tried to vibe code a TypeScript harness (TUI, agent loop, tools, MCP, skills, slash commands), got output that compiled and looked finished but broke at the edges, and deleted the whole codebase. The reframing is the core argument — you cannot one-shot whole applications, but you can one-shot big features if you scope them right and run them through a real engineering process. The author labels this **agentic coding** (you are the mastermind, agents write the code) as distinct from vibe coding. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]

The system splits work across six specialized agents so that no agent both writes code and decides whether the code is correct: a merged product-manager/architect, a TDD software engineer, an adversarial tester, a diff-only PR reviewer, an on-call CI agent, and an optional human-gated self-improve meta-agent. Agents are anchored in the project's own documentation — **Architecture Decision Records (ADRs)** acting as compressed architectural memory across runs, and a **Domain-Driven Design (DDD) glossary** enforcing one canonical name per concept so Claude Code gets business context, not just code context. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team#Keeping Up With Documentation: ADRs & DDD Glossary|excerpt]]

The orchestration is exposed as two skills over the same agent team. The long-running **`/night`** skill takes one input (a human-written feature spec) and produces one output (a merged PR with green CI), with two human gates and five retry caps. The lean **`/day`** skill is the inner SWE+tester loop for surgical edits. A separate **`/scaffold`** skill replaces cookiecutter templates with "agentic templates" — good practices encoded as skills and CLAUDE.md prose, with tooling pulled fresh via Context7 and structure organized by bounded context rather than by file type. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team#The Night Skill. The End-To-End Workflow.|excerpt]]

## Key claims
- You can't one-shot whole applications, but you can one-shot big features if you scope them right and run them through a real engineering process. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]
- No single agent both writes code and decides whether the code is correct; correctness is separated across roles. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]
- Agents use direct CLIs (git, mongosh, gh) rather than MCP wrappers, because CLIs tap bash directly and LLMs have seen far more bash than MCP wrappers in training. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]
- ADRs serve as compressed architectural memory across runs, and a DDD glossary gives shared business vocabulary, anchoring code in the domain. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]
- Judgment-call review loops are capped (3 attempts) because an LLM reviewer almost always has something else to say and will spiral. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]
- Trust is bounded: the tester now accepts the SWE's formatting/happy-path reports and only runs the adversarial edge-case pass itself, fixing the slowest redundancy. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]
- Cookiecutter/Copier templates are a maintenance tax; "agentic templates" encode practices in Markdown and pull tooling dynamically via Context7. [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|cite]]

## Notable quotes
> "This is known as agentic coding. Not vibe coding. You're using agents to write the whole codebase, but you are still the mastermind behind everything."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|location]]

> "The cost of vibe coding isn't abstract. It's the next feature you can't ship because you're debugging a slash-command renderer that looked finished."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|location]]

> "The orchestrator acts as a manager. It never writes code itself, never runs tests itself, and never reviews the diff itself."
> — [[8 - Projects/Building Your Own AI Research OS/example_3_ingest_links/research-custom-urls/raw/web-from-vibe-coding-to-real-engineering-team|location]]

## What's distinctive here
- A concrete, role-separated multi-agent coding org with explicit retry caps and exactly two human gates — a falsifiable engineering process, not a vibe.
- The `/night` vs `/day` split: one agent team, two orchestrators tuned for correctness-first long runs versus snappy surgical edits.
- "Agentic templates" as a replacement for cookiecutter/Copier — practices as prose (CLAUDE.md + skills), structure by bounded context, tooling resolved on demand via Context7.

```mermaid
flowchart TD
    SPEC[Human feature spec] --> PM[Product Manager / Architect\nADR + DDD glossary + task plan]
    PM --> G1{{Human gate 1: approve plan\n(opt /grill-me)}}
    G1 --> LOOP[Inner loop x5]
    subgraph LOOP
      SWE[Software Engineer\nred-green TDD] --> TST[Tester\nadversarial e2e]
      TST -->|fail| SWE
    end
    LOOP --> ACC[PM acceptance review x3]
    ACC --> PRR[PR Reviewer diff-only x3]
    PRR --> ONCALL[On-call agent\nwatch CI x5]
    ONCALL --> G2{{Human gate 2: PR ready}}
    G2 -.optional.-> SI[Self-improve meta-agent\nhuman-gated]
```

## Connections
- **Entities**: Squid (iusztinpaul/squid), Claude Code, Claude Opus, Claude Sonnet, Paul Iusztin, Decoding AI, Context7, Matt Pocock, MCP, Slack
- **Concepts**: agentic-coding, vibe-coding, multi-agent-system, claude-code, mcp, agent-loop, skills, slash-commands, context-engineering, agentic-templates, architecture-decision-record, domain-driven-design, test-driven-development, human-in-the-loop, orchestrator-agent

> Synthesis: This is the agentic-coding pillar of the three-source set — it grounds the shared Claude Code / MCP / skills / slash-commands / context-engineering vocabulary in a working multi-agent engineering team, complementing the agent-memory and GraphRAG sources that share the same primitives.
