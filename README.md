# ai-research-os-workshop workshop

This is the repo for the workshop at the **AI Engineer World's Fair** conference,
presented by Louis-François Bouchard ([X](https://x.com/Whats_AI) ·
[LinkedIn](https://www.linkedin.com/in/whats-ai/)) and Paul Iusztin
([X](https://x.com/pauliusztin_) · [LinkedIn](https://www.linkedin.com/in/pauliusztin/)).

Why not just ask Codex?

For simple questions, you should. If you have one repo, one link, or one quick question,
open Codex or Claude Code and ask directly. That is faster.

`ai-research-os` is for the cases where research should compound over time.

<p align="center"><img src="media/wiki_grows.png" alt="The wiki grows: a custom link, another deep-research round, or a new derivative from a question all feed the same concept" width="700"/></p>

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

`ai-research-os` is a set of local AI skills for building and querying a persistent
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

<p align="center"><img src="media/project_scoped_wiki.png" alt="Sources and deep research feed a project wiki, which an agent renders into articles, videos, and slides" width="800"/></p>

## Slides and video

- Slides: [] (coming soon)
- Video: [] (coming soon)

## Whenever You're Ready, Here's How to Go Deeper

<a href="https://academy.towardsai.net/courses/agent-engineering?utm_source=github&utm_medium=aieng&utm_campaign=2026_aieng_workshop&utm_id=researchwriter"><img src="media/course_clip.gif" alt="Agentic AI Engineering Course" width="800"/></a>

This workshop is a 2–4 hour taste. If you want to go from zero to shipping production-grade AI agents, check out our [**Agentic AI Engineering Course**](https://academy.towardsai.net/courses/agent-engineering?utm_source=github&utm_medium=aieng&utm_campaign=2026_aieng_workshop&utm_id=researchwriter), built with Towards AI.

**34 lessons. Three end-to-end portfolio projects. A certificate. And a Discord community with direct access to industry experts and us.**

Rated 5/5 by 300+ students. The first 6 lessons are free:

[**Start here →**](https://academy.towardsai.net/courses/agent-engineering?utm_source=github&utm_medium=aieng&utm_campaign=2026_aieng_workshop&utm_id=researchwriter)

## Architecture

<p align="center"><img src="media/six_block_pipeline.png" alt="Pipeline: sources flow through deep research, store raw files, index, generate wiki, and query" width="900"/></p>

Sources flow through deep research, get stored as raw files, indexed, synthesized into a
wiki, and then queried:

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

## Examples

Three end-to-end runs, each browsable in [`examples/`](examples/). Open the linked prompt
in Claude Code / Codex with `/research` to reproduce it; the screenshot shows the resulting
wiki browsed in Obsidian.

| Use case | How to use it | Output |
|---|---|---|
| **Deep research** from an outline + web resources — discover sources, summarize, and synthesize them into a topic wiki. | `/research` [`example_1_deep_research/prompt.md`](examples/example_1_deep_research/prompt.md) | <img src="media/example_1_obsidian.png" width="320"/><br/>A full research wiki on agentic harnesses, built from a content outline and reference links. |
| **Ingest GitHub repos** — compute per-repo notes (architecture, agents, memory, permissions) and cross-repo comparisons, skipping deep discovery. | `/research` [`example_2_github/prompt.md`](examples/example_2_github/prompt.md) | <img src="media/example_2_obsidian.png" width="320"/><br/>Side-by-side comparison pages across three coding-agent repositories. |
| **Ingest web links** — pull a handful of specific articles into the wiki without running deep research. | `/research` [`example_3_ingest_links/prompt.md`](examples/example_3_ingest_links/prompt.md) | <img src="media/example_3_obsidian.png" width="320"/><br/>Source pages and synthesis built from three custom URLs. |

## How to use it

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

| Tool | Best for | Limitation | Where `ai-research-os` fits |
|---|---|---|---|
| Codex one-shot | Fast answers, coding help, repo Q&A | The answer is not automatically turned into a durable research workspace | Use Codex directly for simple questions; use this when the research should be reused and extended |
| NotebookLM | Chatting with a fixed set of uploaded sources | Less programmable, less agent-native, not designed around repo parsing, wiki updates, or repeated source ingestion loops | Creates local files, source pages, indexes, and synthesis that agents can keep editing |
| Deep research agents | Broad discovery and synthesis | Often produce a one-time report | Stores the report as a living wiki with raw sources, open questions, and append workflows |
| RAG / vector databases | Retrieval over large corpora | Infrastructure-heavy; retrieval alone does not create source pages, comparisons, or a thesis | Keeps the workflow lightweight and artifact-first; indexing is human/agent-readable |
| `ai-research-os` | Research that compounds across notes, repos, videos, links, and follow-up questions | More setup than a one-shot prompt | Gives Codex / Claude Code a reusable research workspace |

## Skills

| Skill | What it does |
|---|---|
| `/research` | Init, append, or query a per-topic research directory. |
| `/research-distill` | Distill a research directory into a compact `research.md` for a specific piece of content. |
| `/research-lint` | Health-check a research directory for orphan sources, broken links, stale claims, contradictions, and missing hubs. |
| `/research-render` | Render wiki pages into slides, charts, canvases, or content briefs. |

The shared data contract lives in
`plugins/ai-research-os/skills/research/CONVENTIONS.md`.

## Research modes

`/research` routes requests before doing expensive work:

| Mode | Use when | Behavior |
|---|---|---|
| `query` | Ask from an existing research directory | Reads `index.yaml` and `wiki/`; no ingest or discovery. |
| `append` | Add the sources you provide | Ingests the provided sources only; no discovery rounds. |
| `deep` | Explicitly request deep research | Runs source discovery rounds (at a `fast`/`light`/`deep` depth preset), dedup, and wiki updates. |
| `init` | Start a new research directory | Creates `working-dir/research-<topic>/`. |

Deep discovery is opt-in and runs at one of three depth presets — `fast` (1 round, 3 queries),
`light` (2 rounds, 3 + 2 queries), or `deep` (3 rounds, 3 queries each). Long runs show a plan
first: selected mode, sources to ingest, expected runtime, and files to write.

In `query` mode the agent drills down progressively — index summary first, then the source
wiki page, then derivatives, and only the raw source if it still needs it — so the context
window stays small:

<p align="center"><img src="media/query_drilldown.png" alt="A question drills down from the index.yaml summary to the source wiki page to derivatives, reaching the raw source only if needed, keeping the context window small" width="800"/></p>

A question can also grow the wiki: it spawns new notes and comparisons off existing concepts,
and your open questions accumulate for future rounds:

<p align="center"><img src="media/questions_derivatives.png" alt="A question expands a concept into a new note and a new comparison, while your questions accumulate" width="800"/></p>

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
/plugin marketplace add iusztinpaul/ai-research-os-workshop
/plugin install ai-research-os@iusztinpaul
```

That's it — the `/research`, `/research-distill`, `/research-lint`, and
`/research-render` skills are now available everywhere you use Claude Code.

### Option B - local skills (for testing or development)

Use this if you want to edit the skills, test a PR branch, or run without the
marketplace plugin.

```bash
git clone https://github.com/iusztinpaul/ai-research-os-workshop.git

# from the vault or project where you want to use the skills:
cd /path/to/your/vault-or-project
mkdir -p .claude/skills
cp -R /path/to/ai-research-os-workshop/plugins/ai-research-os/skills/* .claude/skills/
```

To test a specific branch, `git checkout <branch-name>` in the clone before copying.

> Tip: instead of copying, symlink the skills so your edits are picked up live:
> `ln -s /path/to/ai-research-os-workshop/plugins/ai-research-os/skills/research .claude/skills/research`

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
| Web pages | Fetch generic HTML sites | None — uses preinstalled `curl` + a `python3` stdlib HTML stripper. `WebFetch` is the fallback for JS-rendered or bot-walled pages. |
| `git` | Ingest GitHub repos | Install system Git. |
| YouTube captions | Ingest public YouTube transcripts | No API key required. Public captions must be available. |

Your PARA vault (Projects, Areas, Resources, Archive) is pulled into an immutable Obsidian
snapshot — notes, resources, and highlights — that research builds on without mutating your
originals:

<p align="center"><img src="media/para_snapshot.png" alt="PARA folders (Projects, Areas, Resources, Archive) collapse into an immutable Obsidian snapshot of notes, resources, and highlights" width="800"/></p>

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

The agent reads `index.yaml` first and follows its pointers to wiki pages, derivatives, or
raw sources — the index *is* the retrieval layer, so there is no vector DB:

<p align="center"><img src="media/index_retrieval.png" alt="The agent reads index.yaml first as the retrieval layer, pointing to wiki pages, derivatives, and raw sources, with no vector DB" width="800"/></p>

## Extending it - add your own feature

Every feature in this repo is a **skill**: a folder with a `SKILL.md` (the instructions
the agent reads) plus optional helper `scripts/` and `agents/`. The plugin is just a
bundle of these skill folders. Adding a feature means adding a new skill folder.

### Anatomy of a skill

```text
plugins/ai-research-os/skills/<your-skill>/
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
   `cp -R plugins/ai-research-os/skills/research-lint plugins/ai-research-os/skills/my-skill`
2. **Edit `SKILL.md`.** Update the `name`, `description`, and instructions. Reuse the
   shared data contract in `plugins/ai-research-os/skills/research/CONVENTIONS.md` so your
   skill reads and writes the same `index.yaml` / `wiki/` layout as the others.
3. **Test locally** with Option B above (symlink the skill into `.claude/skills/`), open
   Claude Code, and confirm `/my-skill` appears and runs as expected.
4. **Register and ship it.** The skill is auto-discovered by the plugin folder, so no
   manifest edit is required to run it locally. When you want it in the published plugin,
   update the description in `.claude-plugin/marketplace.json` and
   `plugins/ai-research-os/.claude-plugin/plugin.json`, then open a PR.

### Helper scripts

Put reusable logic in `scripts/` and call it with `uv run --script`. Declare
dependencies inline with [PEP 723](https://peps.python.org/pep-0723/) script metadata so
`uv` installs them into an isolated environment automatically — no global installs, no
`requirements.txt`. See
`plugins/ai-research-os/skills/research/scripts/youtube_extract_transcript.py` for a
complete example.

## Notes

- Obsidian is not required. It is useful for visualizing the generated markdown wiki.
- YouTube ingestion uses public transcripts and requires no Gemini/OpenAI key.
- See `DEPENDENCIES.md` for dependency rationale and removed older features.
