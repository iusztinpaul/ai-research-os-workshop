---
type: entity
name: Claude Code
aliases: []
sources: [[[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]]
related: [[[wiki/concepts/instruction-files]], [[wiki/concepts/context-compaction]], [[wiki/concepts/permission-gating]], [[wiki/concepts/mcp]]]
created: 2026-06-12T17:45:00
last_updated: 2026-06-12T17:45:00
source_count: 3
mention_count: 6
confidence: high
---

# Claude Code

> Anthropic's coding-agent CLI, present in this corpus not as a studied artifact but as the reference harness whose conventions all three studied harnesses adopt, emulate, or define themselves against.

## Definition

In this research, Claude Code is never examined directly — it appears through its **compatibility surfaces**: the `CLAUDE.md` instruction-file convention that all three harnesses parse [[wiki/sources/opencode]] [[wiki/sources/pi]] [[wiki/sources/hermes-agent]], the markdown-plus-frontmatter skills format pi explicitly targets [[wiki/sources/pi]], and the `/compact` and deny-rule mechanisms hermes-agent names among its design influences [[wiki/sources/hermes-agent]]. It functions as the de facto standard the field interoperates with: hermes-agent's docs frame it as a competitor whose instruction files are worth reading anyway [[wiki/sources/hermes-agent]].

## Key claims

- All three harnesses read `CLAUDE.md` files as project memory, treating Claude Code's instruction-file convention as a de facto standard each reimplements differently. [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- opencode layers `AGENTS.md`/`CLAUDE.md` project memory in a global → project → directory hierarchy, lazily attached as files are read. [[wiki/sources/opencode]]
- pi discovers `AGENTS.md`/`CLAUDE.md` global-first then root-most-first down to cwd and inlines them into the system prompt. [[wiki/sources/pi]]
- hermes-agent loads exactly one project-context source via first-match-wins priority — `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules` — ranking Claude Code's file third behind its own and the neutral standard; it "reads competitors' instruction files." [[wiki/sources/hermes-agent]]
- pi's skills system is Claude Code-compatible (markdown + frontmatter), listed by name+description and lazily read on demand — progressive disclosure positioned as pi's no-MCP alternative. [[wiki/sources/pi]]
- hermes-agent openly indexes Claude Code's `/compact` and deny rules among its influences (alongside OpenClaw and OpenAI Codex). [[wiki/sources/hermes-agent]]
- The Claude Code-style instruction-file tier stays human-curated and read-only across harnesses: pi never writes back to instruction files, and opencode pairs user-curated `AGENTS.md` with a deliberate absence of model-written memory files. [[wiki/sources/opencode]], [[wiki/sources/pi]]

## Notable quotes

> "skills (Claude Code-compatible markdown + frontmatter) are listed name+description and lazily read on demand — progressive disclosure as the no-MCP alternative."
> — [[wiki/sources/pi]]

> "The codebase also openly indexes its influences — OpenClaw's subagent prompt and MCP bridge surface, OpenAI Codex's smart approvals, Claude Code's `/compact` and deny rules."
> — [[wiki/sources/hermes-agent]]

## Relationships

- **Instruction files**: `CLAUDE.md` is the originating instance of the convention; all three harnesses parse it, each with different discovery/priority rules. [[wiki/concepts/instruction-files]] · [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- **Context compaction**: Claude Code's `/compact` is a named influence on hermes-agent's session-splitting compaction design. [[wiki/concepts/context-compaction]] · [[wiki/sources/hermes-agent]]
- **Permission gating**: Claude Code's deny rules influenced hermes-agent's paired file-tool/terminal hard-denies on its own config. [[wiki/concepts/permission-gating]] · [[wiki/sources/hermes-agent]]
- **MCP**: pi positions Claude Code-compatible skills (lazy progressive disclosure) as its replacement for MCP entirely. [[wiki/concepts/mcp]] · [[wiki/sources/pi]]

## Tensions

- Stacking vs. exclusive loading of Claude Code's instruction-file convention: opencode and pi layer multiple `AGENTS.md`/`CLAUDE.md` files (hierarchical / root-most-first), while hermes-agent loads exactly one project-context source, with `CLAUDE.md` only third in priority. [[wiki/sources/opencode]], [[wiki/sources/pi]] vs. [[wiki/sources/hermes-agent]]

## Open questions

- The corpus only sees Claude Code through emulation surfaces — how faithful are these reimplementations (pi's skills compatibility, hermes-agent's `/compact`-inspired compaction) to Claude Code's actual behavior? [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]
- hermes-agent ranks `AGENTS.md` above `CLAUDE.md` while opencode and pi treat them as peers — is the vendor-neutral `AGENTS.md` displacing `CLAUDE.md` as the standard instruction-file name? [[wiki/sources/opencode]], [[wiki/sources/pi]], [[wiki/sources/hermes-agent]]

> Synthesis: For this comparative study, Claude Code is the invisible fourth harness — the gravitational reference point none of the three repos can ignore. Its conventions split into two adoption patterns: file-format conventions (`CLAUDE.md`, skills frontmatter) are adopted wholesale as interoperability surfaces, while behavioral mechanisms (`/compact`, deny rules) are cited as inspiration but reimplemented divergently (hermes-agent's session-splitting compaction, pattern-keyed denies). That asymmetry — formats standardize, behaviors fork — is itself a finding about how the coding-agent ecosystem consolidates.
