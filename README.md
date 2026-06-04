# obsidian-ai-os

A Claude Code plugin that turns an **Obsidian vault** into a persistent,
LLM-maintained research wiki. It ships the `/research-*` family of skills: build a
research directory from your vault + reading library + notebooks + GitHub repos + the
web, then query, lint, distill, and render it.

Designed to be plugged into an Obsidian vault and installed as a **real Claude Code
plugin** (no symlinks). Research output lives under `working-dir/` relative to where you
run the skills.

## Skills

### Research family

| Skill | What it does |
|---|---|
| `/research` | Conversational entry point. Init / append / query a per-topic research dir (`index.yaml` + `wiki/` + `raw/`). Ingests Obsidian, Readwise, NotebookLM, GitHub repos, web seeds, and dropped PDFs. |
| `/research-distill` | Distil a research dir into a single compact `research.md` containing only the sources actually used by a piece of content. |
| `/research-lint` | Health-check a research dir: orphans, missing hubs/comparisons, broken wikilinks, stale claims, contradictions, open questions. |
| `/research-render` | Render wiki pages into Marp decks, matplotlib charts, Obsidian Canvases, or social content briefs, filed back into `wiki/renders/`. |

The shared data contract lives in
`plugins/obsidian-ai-os/skills/research/CONVENTIONS.md` (authoritative when a `SKILL.md`
disagrees).

### Bundled CLI usage-skills

The research family drives four external CLIs. Their **usage skills** are bundled so the
plugin is self-contained (each documents commands + auth):
`obsidian-cli`, `readwise-cli`, `nlm-skill`, `brightdata-cli`. The CLI **binaries**
themselves still install separately — see below.

## Install (real plugin)

```text
/plugin marketplace add /Users/pauliusztin/Documents/01-Projects/obsidian-ai-os
/plugin install obsidian-ai-os@iusztinpaul
```

(Or point `marketplace add` at the GitHub remote once pushed.) Skill scripts reference
themselves via `${CLAUDE_PLUGIN_ROOT}`, so they resolve from the installed plugin
location — no symlinks, no path rewriting.

## Dependencies

### Python — zero setup

The helper scripts carry **PEP 723 inline metadata** and are invoked with
`uv run --script …`, so `uv` auto-installs each script's deps into an isolated env on
first run, regardless of the current directory. Nothing to install by hand. (A root
`pyproject.toml` is included for local dev only; the skills don't depend on it.)

Per-script deps: `pyyaml` (index + lint), `httpx` (image download), `pymupdf` +
`pymupdf4llm` (PDF extraction), `matplotlib` (chart render).

Requires [`uv`](https://docs.astral.sh/uv/) on PATH.

### External CLI binaries (install separately)

These power the research *sources*. `/research` runs a **Step 0.5 preflight** (`command -v`)
that detects which CLIs are installed and, for each missing one, prints a clear one-line
warning naming the lost capability + the bundled skill, then continues with whatever is
available — a missing CLI never crashes the run with `command not found`. If a web seed's
`bdata` is missing it falls back to WebFetch; if NotebookLM/Readwise/Obsidian are missing
those sources are skipped with a warning. If **all** source CLIs are missing and there are
no seeds, it stops with an explicit "no sources available — install one of …" message.

| CLI | Install | Auth | Used by |
|---|---|---|---|
| `obsidian` | install the Obsidian CLI on your PATH (see `obsidian-cli` skill) | points at your vault | `/research` vault search |
| `readwise` | `npm install -g @readwise/cli` | `readwise login-with-token <token>` | `/research` Readwise library + feed |
| `nlm` | see `nlm-skill` (Go CLI) | `nlm login` (sessions ~20 min) | `/research` NotebookLM |
| `bdata` / `brightdata` | `curl -fsSL https://cli.brightdata.com/install.sh \| bash` or `npm install -g @brightdata/cli` (Node ≥ 20) | `bdata login` | `/research` web crawl (WebFetch fallback) |
| `marp` *(optional)* | Marp CLI or Obsidian Marp plugin | — | viewing `/research-render marp` output |
| `git` | system git | — | `/research` GitHub repo ingestion |

### Assumes an Obsidian vault

`/research` reads your vault as a source (via the `obsidian` CLI) and detects Readwise
highlights synced into it. Run the skills from your vault root; research dirs are created
at `working-dir/research-<topic-slug>/` relative to that.

## What was removed / not included

- **`/research-promote`** — dropped. It graduated wiki pages into a specific PARA
  Second-Brain layout (`6 - Notes/` etc., templates, tagging rules); that vault-shape
  dependency is out of scope for a standalone plugin.
- **`*-guideline-create` handoffs** — removed from `/research-render`'s brief format. A
  brief is now just a copy-ready seed you paste wherever you like.
- **scrabble `resources/`** (profiles, datasets, glossary) — never referenced by the
  research family; not moved.

See `DEPENDENCIES.md` for the full rationale.
