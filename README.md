# obsidian-ai-os

A Claude Code plugin that turns an **Obsidian vault** into a persistent,
LLM-maintained research wiki. It ships the `/research-*` family of skills: build a
research directory from your vault + reading library + notebooks + GitHub repos +
YouTube videos + the web, then query, lint, distill, and render it.

Designed to be plugged into an Obsidian vault and installed as a **real Claude Code
plugin** (no symlinks). Research output lives under `working-dir/` relative to where you
run the skills.

## Skills

### Research family

| Skill | What it does |
|---|---|
| `/research` | Conversational entry point. Init / append / query a per-topic research dir (`index.yaml` + `wiki/` + `raw/`). Ingests Obsidian, Readwise, NotebookLM, GitHub repos, YouTube videos, web seeds, and dropped PDFs. |
| `/research-distill` | Distil a research dir into a single compact `research.md` containing only the sources actually used by a piece of content. |
| `/research-lint` | Health-check a research dir: orphans, missing hubs/comparisons, broken wikilinks, stale claims, contradictions, open questions. |
| `/research-render` | Render wiki pages into Marp decks, matplotlib charts, Obsidian Canvases, or social content briefs, filed back into `wiki/renders/`. |

The shared data contract lives in
`plugins/obsidian-ai-os/skills/research/CONVENTIONS.md` (authoritative when a `SKILL.md`
disagrees).

#### `/research` routing modes

`/research` routes simple requests before it starts any expensive source discovery:

| Mode | Use when | Behavior |
|---|---|---|
| `query` | Ask from an existing research dir | Answers from `index.yaml` + `wiki/` first; no ingest or discovery. |
| `append-trusted` | Add one known source | Ingests that source only. |
| `append-light` | Add a few provided sources | Ingests provided sources only; no discovery rounds. |
| `append-deep` | Explicitly request deep research/discovery | Runs source discovery, rounds, rerank, and wiki updates. |
| `init` | Start a new research dir | Creates the dir; seed-only by default unless deep discovery is explicitly requested. |

Before long runs, `/research` shows a plan with the selected mode, sources to ingest,
expected runtime, and files it will write. Deep discovery is opt-in.

### Bundled CLI usage-skills

The research family drives four external CLIs. Their **usage skills** are bundled so the
plugin is self-contained (each documents commands + auth):
`obsidian-cli`, `readwise-cli`, `nlm-skill`, `brightdata-cli`. The CLI **binaries**
themselves still install separately — see below.

## Install

Two ways to install — both run from inside your Obsidian vault (or wherever you want the
skills available). No symlinks, no machine-specific paths.

Skill scripts are referenced as `${CLAUDE_PLUGIN_ROOT:-.claude}/skills/…`, so they resolve
under **either** install method: `${CLAUDE_PLUGIN_ROOT}` when installed as a Claude Code
plugin, or the `.claude/skills/` fallback when installed as plain skills.

### Option A — Claude Code plugin marketplace (recommended)

Fully supported: bundles every skill, script, and agent, and sets `${CLAUDE_PLUGIN_ROOT}`.

```text
/plugin marketplace add iusztinpaul/obsidian-ai-os
/plugin install obsidian-ai-os@iusztinpaul
```

`marketplace add` also accepts a full git URL (`https://github.com/iusztinpaul/obsidian-ai-os`)
or a local clone path if you're developing it.

### Option B — `npx skills` (Vercel skills CLI)

Uses [`vercel-labs/skills`](https://github.com/vercel-labs/skills). The subcommand is
`add` (there is no `npx skills install`); it copies skill folders into `.claude/skills/`.
**Install into project scope** (the default — run from your vault root) so the
`.claude/skills/` fallback resolves; avoid global `-g` for the script-running skills.

```bash
# Browse everything in this repo (skills are nested under plugins/, so use --full-depth):
npx skills add iusztinpaul/obsidian-ai-os --full-depth --list

# Install a specific skill by its path (most reliable):
npx skills add https://github.com/iusztinpaul/obsidian-ai-os/tree/main/plugins/obsidian-ai-os/skills/research -a claude-code

# Or install all skills from the repo to Claude Code, non-interactively:
npx skills add iusztinpaul/obsidian-ai-os --full-depth --all -a claude-code -y
```

Install at least `research` (the others — `research-lint`, `research-render` — call its
`build_index_md.py`), plus the source-CLI usage skills you want (`obsidian-cli`,
`readwise-cli`, `nlm-skill`, `brightdata-cli`). Keep them in the same scope.

## Dependencies

### Python — zero setup

The helper scripts carry **PEP 723 inline metadata** and are invoked with
`uv run --script …`, so `uv` auto-installs each script's deps into an isolated env on
first run, regardless of the current directory. Nothing to install by hand. (A root
`pyproject.toml` is included for local dev only; the skills don't depend on it.)

Per-script deps: `pyyaml` (index + lint), `httpx` (image download), `pymupdf` +
`pymupdf4llm` (PDF extraction), `youtube-transcript-api` (YouTube captions),
`matplotlib` (chart render).

Requires [`uv`](https://docs.astral.sh/uv/) on PATH.

### YouTube captions

YouTube ingestion requires no API key. `/research` fetches the public caption transcript
for YouTube URLs and writes it into `raw/youtube-<slug>.md` as a timestamped source. If a
video has captions disabled or no transcript in the requested language, that video is
skipped with a clear warning and the run continues with the other sources.

### External CLI binaries and auth (install/auth separately)

These power the research *sources*. `/research` runs a **Step 0.5 preflight** (`command -v`
for source CLIs)
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
| YouTube captions | none | none | `/research` YouTube video ingestion when public transcripts are available |

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
