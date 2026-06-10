# obsidian-ai-os workshop

This is the repo for the workshop at the **AI Engineer World's Fair** conference,
presented by Louis-François Bouchard and Paul Iusztin.

Why not just ask Codex?

For simple questions, you should. If you have one repo, one link, or one quick question,
open Codex or Claude Code and ask directly. That is faster.

`obsidian-ai-os` is for the cases where research should compound over time.

Codex gives you an answer. This gives Codex a reusable research workspace:

- `raw/` - copied or fetched source material
- `wiki/sources/` - per-source summaries
- `wiki/concepts/`, `wiki/entities/`, `wiki/comparisons/` - reusable synthesis pages
- `wiki/overview.md` and `wiki/synthesis.md` - the current thesis
- `index.yaml` and `index.md` - the catalog future agents read first
- `log.md` and `wiki/open-questions.md` - what happened and what to research next

The point is not to replace Codex. The point is to stop re-researching the same topic
every week.

## What this is

`obsidian-ai-os` is a set of local AI skills for building and querying a persistent
research wiki from your own sources:

- Obsidian notes
- Readwise highlights
- NotebookLM notebooks
- GitHub repos
- YouTube videos with public transcripts
- web links
- PDFs and local files

Obsidian is optional. It is just a visual IDE for browsing the generated markdown wiki.
The system can run purely through Codex or Claude Code from a normal working directory.

## Slides and video

- Slides: [] (coming soon)
- Video: [] (coming soon)

## Course

This repo is a practical demo of agentic research workflows. If you want to go deeper
into building production-grade AI agents, workflows, evals, and agent harnesses, check out
the Towards AI Agentic AI Engineering Course:

https://academy.towardsai.net

## Architecture

TODO - add architecture diagram here.

Suggested shape:

```text
user question / sources
        |
        v
  /research router
        |
        +--> query existing wiki
        +--> append known sources
        +--> run deep discovery
        |
        v
 raw sources -> source pages -> concepts/entities/comparisons
        |
        v
 index.yaml + overview.md + synthesis.md + open-questions.md
```

## Example

TODO - add one complete example here.

Suggested example:

1. Start with a question and a few sources.
2. Run `/research`.
3. Show the generated `working-dir/research-<topic>/` directory.
4. Ask a follow-up question that answers from the existing wiki instead of re-ingesting.
5. Add a YouTube video or GitHub repo and show the wiki update.

## When to use it

Use this when:

- you are researching a topic over multiple sessions
- you want sources, summaries, claims, and open questions preserved
- you want to compare several repos, papers, videos, or notes
- you want future Codex / Claude runs to reuse prior research
- you want a local markdown wiki you can inspect, edit, and version
- you want deep research to write durable artifacts, not just a chat answer

Do not use this when:

- you have one simple question
- you only need a quick answer from one link
- you do not care about saving the result
- you need a fully managed hosted knowledge base
- you want semantic search infrastructure only, without an agent workflow

## Compared to alternatives

| Tool | Best for | Limitation | Where `obsidian-ai-os` fits |
|---|---|---|---|
| Codex one-shot | Fast answers, coding help, repo Q&A | The answer is not automatically turned into a durable research workspace | Use Codex directly for simple questions; use this when the research should be reused and extended |
| NotebookLM | Chatting with a fixed set of uploaded sources | Less programmable, less agent-native, not designed around repo parsing, wiki updates, or repeated source ingestion loops | Creates local files, source pages, indexes, and synthesis that agents can keep editing |
| Deep research agents | Broad discovery and synthesis | Often produce a one-time report | Stores the report as a living wiki with raw sources, open questions, and append workflows |
| RAG / vector databases | Retrieval over large corpora | Infrastructure-heavy; retrieval alone does not create source pages, comparisons, or a thesis | Keeps the workflow lightweight and artifact-first; indexing is human/agent-readable |
| `obsidian-ai-os` | Research that compounds across notes, repos, videos, links, and follow-up questions | More setup than a one-shot prompt | Gives Codex / Claude Code a reusable research workspace |

## Skills

| Skill | What it does |
|---|---|
| `/research` | Init, append, or query a per-topic research directory. |
| `/research-distill` | Distill a research directory into a compact `research.md` for a specific piece of content. |
| `/research-lint` | Health-check a research directory for orphan sources, broken links, stale claims, contradictions, and missing hubs. |
| `/research-render` | Render wiki pages into slides, charts, canvases, or content briefs. |

The shared data contract lives in
`plugins/obsidian-ai-os/skills/research/CONVENTIONS.md`.

## Research modes

`/research` routes requests before doing expensive work:

| Mode | Use when | Behavior |
|---|---|---|
| `query` | Ask from an existing research directory | Reads `index.yaml` and `wiki/`; no ingest or discovery. |
| `append-trusted` | Add one known source | Ingests that source only. |
| `append-light` | Add a few provided sources | Ingests provided sources only; no discovery rounds. |
| `append-deep` | Explicitly request deep research | Runs source discovery, rounds, rerank, and wiki updates. |
| `init` | Start a new research directory | Creates `working-dir/research-<topic>/`. |

Deep discovery is opt-in. Long runs show a plan first: selected mode, sources to ingest,
expected runtime, and files to write.

## Install

You only need three things to get going:

1. **Claude Code** (or Codex) — the agent that runs the skills.
2. **`uv`** — runs the helper scripts (see [Dependencies](#dependencies)).
3. **This plugin** — installed with one of the two options below.

Always run the agent from the directory where you want research saved: your Obsidian
vault root, a project root, or any working folder. Research outputs are created in a
`working-dir/` subfolder of wherever you start.

### Option A - Claude Code plugin (recommended)

Inside Claude Code, run:

```text
/plugin marketplace add iusztinpaul/obsidian-ai-os
/plugin install obsidian-ai-os@iusztinpaul
```

That's it — the `/research`, `/research-distill`, `/research-lint`, and
`/research-render` skills are now available everywhere you use Claude Code.

### Option B - local skills (for testing or development)

Use this if you want to edit the skills, test a PR branch, or run without the
marketplace plugin.

```bash
git clone https://github.com/iusztinpaul/obsidian-ai-os.git

# from the vault or project where you want to use the skills:
cd /path/to/your/vault-or-project
mkdir -p .claude/skills
cp -R /path/to/obsidian-ai-os/plugins/obsidian-ai-os/skills/* .claude/skills/
```

To test a specific branch, `git checkout <branch-name>` in the clone before copying.

> Tip: instead of copying, symlink the skills so your edits are picked up live:
> `ln -s /path/to/obsidian-ai-os/plugins/obsidian-ai-os/skills/research .claude/skills/research`

### First run

1. Open Claude Code or Codex from your vault/project directory.
2. Type `/` and confirm `research` appears in the skill list (this verifies the install).
3. Run `/research` with a topic and a couple of sources, for example:
   `/research compare LangGraph and CrewAI for multi-agent orchestration`.
4. Inspect the generated `working-dir/research-<topic>/` directory.
5. Ask a follow-up — the agent answers from the existing wiki instead of re-ingesting.

If a source CLI is missing, `/research` warns you and continues with what it can reach,
so you can start with zero extra setup and add connectors later (see
[Source CLIs](#source-clis)).

## Dependencies

Install `uv` first:

```bash
# macOS
brew install uv

# Windows
winget install --id=astral-sh.uv -e
```

The helper scripts use `uv run --script`, so script dependencies install into isolated
environments automatically.

Per-script dependencies include `pyyaml`, `httpx`, `pymupdf`, `pymupdf4llm`,
`youtube-transcript-api`, and `matplotlib`.

## Source CLIs

These are optional source connectors. Missing CLIs degrade gracefully: `/research` warns
you and continues with the sources it can access.

| CLI | Used for | Setup |
|---|---|---|
| `obsidian` | Search local Obsidian notes | Enable Obsidian CLI in Obsidian settings. On Windows, the skill also tries `%LOCALAPPDATA%\Programs\Obsidian\Obsidian.com`. |
| `readwise` | Search Readwise library and feed | `npm install -g @readwise/cli`, then authenticate. |
| `nlm` | Search NotebookLM notebooks | See the bundled `nlm-skill`. |
| `bdata` / `brightdata` | Higher-fidelity web crawling | Install Bright Data CLI and authenticate. WebFetch fallback is used if missing. |
| `git` | Ingest GitHub repos | Install system Git. |
| YouTube captions | Ingest public YouTube transcripts | No API key required. Public captions must be available. |

## Output layout

Research outputs are created under:

```text
working-dir/research-<topic>/
  index.yaml
  index.md
  log.md
  raw/
  wiki/
    overview.md
    synthesis.md
    open-questions.md
    sources/
    concepts/
    entities/
    comparisons/
```

`index.yaml` is the canonical machine-readable catalog. `index.md` is the
Obsidian-friendly view.

## Extending it - add your own feature

Every feature in this repo is a **skill**: a folder with a `SKILL.md` (the instructions
the agent reads) plus optional helper `scripts/` and `agents/`. The plugin is just a
bundle of these skill folders. Adding a feature means adding a new skill folder.

### Anatomy of a skill

```text
plugins/obsidian-ai-os/skills/<your-skill>/
  SKILL.md          # required - frontmatter + instructions
  scripts/          # optional - uv run --script helpers
  agents/           # optional - sub-agent prompts
```

`SKILL.md` starts with frontmatter that tells the agent when to invoke it:

```markdown
---
name: my-skill
description: One sentence on what it does and the phrases that should trigger it.
user_invocable: true
---

# My Skill

Step-by-step instructions the agent follows when the skill runs.
```

The `description` is what the agent matches against, so make it specific and list the
trigger phrases. Study the existing skills — `research-lint` is the simplest, `research`
is the most complete reference.

### Add a feature in four steps

1. **Create the folder.** Copy the closest existing skill as a starting point:
   `cp -R plugins/obsidian-ai-os/skills/research-lint plugins/obsidian-ai-os/skills/my-skill`
2. **Edit `SKILL.md`.** Update the `name`, `description`, and instructions. Reuse the
   shared data contract in `plugins/obsidian-ai-os/skills/research/CONVENTIONS.md` so your
   skill reads and writes the same `index.yaml` / `wiki/` layout as the others.
3. **Test locally** with Option B above (symlink the skill into `.claude/skills/`), open
   Claude Code, and confirm `/my-skill` appears and runs as expected.
4. **Register and ship it.** The skill is auto-discovered by the plugin folder, so no
   manifest edit is required to run it locally. When you want it in the published plugin,
   update the description in `.claude-plugin/marketplace.json` and
   `plugins/obsidian-ai-os/.claude-plugin/plugin.json`, then open a PR.

### Helper scripts

Put reusable logic in `scripts/` and call it with `uv run --script`. Declare
dependencies inline with [PEP 723](https://peps.python.org/pep-0723/) script metadata so
`uv` installs them into an isolated environment automatically — no global installs, no
`requirements.txt`. See
`plugins/obsidian-ai-os/skills/research/scripts/youtube_extract_transcript.py` for a
complete example.

## Notes

- Obsidian is not required. It is useful for visualizing the generated markdown wiki.
- YouTube ingestion uses public transcripts and requires no Gemini/OpenAI key.
- See `DEPENDENCIES.md` for dependency rationale and removed older features.
