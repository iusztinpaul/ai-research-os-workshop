---
name: research
description: Build, extend, AND query a persistent LLM-maintained wiki for any research topic. Conversational entry point that routes between five modes - query (fast read-only answer from existing wiki), append-trusted (add one known source), append-light (ingest a few provided sources only), append-deep (explicit discovery/deep research), and init (create a new research directory). Ingests from your knowledge sources (Obsidian vault + Readwise + NotebookLM + GitHub repos + YouTube videos + web seeds + user-dropped PDFs) and maintains a wiki layer (per-source pages, entities, concepts, comparisons, overview, synthesis, open questions, contradictions). Use for any research interaction - first-time research on a topic, "what do I have on X", "load my research on Y", "add this PDF to my research", "deep dive on Z", "pull together my notes on Y", "extend my research with this file". Trigger on the phrases above plus "search my research", "use my research", "find sources about X".
user_invocable: true
---

# Research

You are a research orchestrator. The user gives you a brain dump — text, images, links, whatever they have — about a topic they're exploring. Your job is to mine their knowledge sources (Obsidian vault, Readwise highlights, NotebookLM collections, web seeds, GitHub repos, and dropped PDFs) and **maintain an LLM-curated wiki** that compounds over time.

The output is a self-contained **research research directory** with three layers — `index.yaml` / `index.md` (catalog), `wiki/` (synthesis), and `raw/` (immutable sources). Future agents read only the index to understand what's there; they drill into wiki and raw selectively. The full data contract lives in `CONVENTIONS.md`.

## Step 0 - Route the request

Before touching source CLIs or writing files, classify the user's intent. Routing is a
speed and safety feature: simple questions should be answered from the existing wiki, and
deep discovery should never run unless the user clearly asks for it.

| Mode | Trigger | Pipeline | Expected runtime |
|---|---|---|---|
| **query** | Existing research dir + user asks a question, wants context loaded, filters sources, or drills into a topic/source | Read-only path. See **Query path** below. Optional Q&A save-back. No source CLI preflight, no discovery, no raw/wiki rewrite. | Seconds to <1 min |
| **append-trusted** | Existing research dir + exactly one user-vouched source ("add this PDF/link/repo/video/note") | Seed-only ingest. Step 1 -> Step 6 -> Step 6.2 -> Step 6.3 for the new source -> incremental wiki update -> Steps 6.5-8. | ~1-5 min |
| **append-light** | Existing research dir + a small provided set of sources, usually 2-5 URLs/files/repos/videos | Provided-source ingest only. No discovery rounds, no NLM sweep, no reranker. Seeds get `relevance_score: 1.0`; dedup against `index.yaml`; then Steps 1 and 6-8. | ~3-10 min |
| **append-deep** | Existing research dir + explicit discovery request ("deep research", "find more sources", "run discovery", "exhaustive", "do rounds") | Discovery ingest. Step 1, Step 2, Step 3, Step 3b, Step 4, Step 5, then Steps 6-8. Dedup against existing `index.yaml`. | ~10-30+ min |
| **init** | No matching research dir exists and the user wants a new research topic | Create `working-dir/research-<topic-slug>/`. If the user provided sources, default to seed-only init; if they explicitly ask for deep discovery, run the discovery pipeline after plan confirmation. | ~1-10 min seed-only, ~10-30+ min deep |

**How to decide:**
1. Compute the candidate `topic_slug` from the user's words (kebab-case).
2. Locate a matching research dir by explicit path, topic slug, or scanning
   `working-dir/research-*/index.yaml` for a semantic topic match.
3. If the user asks a question and a matching research dir exists, choose **query** by
   default, even when the word "research" appears. Query includes "what do I have on X",
   "summarize X", "load my research on X", "which sources mention X", and "how does X
   work?"
4. If the user provides exactly one known source and says to add/ingest it, choose
   **append-trusted**.
5. If the user provides a few concrete sources and says to add/ingest them, choose
   **append-light**.
6. Choose **append-deep** only when the user explicitly asks for discovery/deep research:
   "deep", "find more sources", "discover", "run rounds", "search my sources for more",
   "exhaustive", "comprehensive scan", or equivalent wording.
7. Choose **init** when no matching research dir exists. If the user only asked a question
   and no dir exists, ask whether to create a new research dir or answer without
   persistent research memory.
8. If multiple research dirs match, ask the user to choose. If intent is ambiguous,
   default to **query** when a dir exists; otherwise show a plan and ask.

### Routing plan / dry-run gate

Before any ingest mode writes files or starts expensive work, show a short plan. If the
user said "dry run", "plan first", "what would happen", or "do not run yet", output only
the plan and stop.

The plan must include:
- `mode_selected` and why it was selected
- `research_dir` to read/write
- `sources_to_ingest`: explicit sources with origin guesses (`web`, `youtube`, `github`,
  `pdf`, `obsidian`, etc.) or "none yet" for discovery-only deep runs
- `discovery`: whether rounds/NLM/Readwise/Obsidian search will run
- `expected_runtime`: a rough range from the table above
- `outputs_to_write`: raw files, wiki source pages, overview/synthesis updates,
  `index.yaml`, `index.md`, `log.md`
- `skip_policy`: sources already in `index.yaml` are skipped; unavailable CLIs degrade
  with warnings

Ask for confirmation before proceeding when any of these are true:
- mode is **append-deep**
- mode is **init** with discovery/deep research
- mode is **append-light** with more than 3 provided sources
- expected runtime is clearly >5 minutes after considering the actual source types
- the user explicitly requested a dry run / plan first

For **append-trusted** and small low-cost **append-light** runs (<=3 simple sources), show
the plan and proceed unless the user asked for confirmation first. For **query**, do not
show a plan; answer fast.

### Append/init preconditions
- Verify the research dir is v4 layout (`raw/` and `wiki/` directly under the research dir, no `memory/` wrapper). If it's older (v1 with raw at root, or v3 with a `memory/` wrapper), migrate it to v4 first - or instruct the user to - before ingesting.
- Read existing `index.yaml` for append modes. If `index.yaml` is missing but `index.md` and `wiki/` exist, treat the dir as read-only until the YAML index is restored; query fallback is allowed, but append/deep mutation is blocked because deduplication and index regeneration need canonical YAML. The `original_path` set is the dedup key - sources already there are skipped during research rounds and refused/skipped in seed-only modes with an "already ingested" message.
- Capture the existing `created` timestamp for append modes; pass it as `--existing-created` to `build_index_yaml.py` in Step 6.7.

### Seed-only skip list
In **append-trusted**, **append-light**, and seed-only **init**, skip Steps 2 (configure
rounds), 3 (initial queries), 3b (NLM discovery), 4 (research rounds), and 5 (rerank).
The user's seed sources get `relevance_score: 1.0`, go through Step 1 -> Step 6 -> wiki
updates -> Step 8, and are deduplicated by `original_path`.

### Read before write
When intent is genuinely ambiguous, **default to query, not ingest.** Wrong dispatch is
expensive and may overwrite generated wiki pages; answering from existing memory is
cheap. Ingest must be opt-in by an explicit verb ("ingest", "add", "append", "deep
research", "find more sources") OR by a file/URL/PDF/repo/video drop.

## Query path

Used when Step 0 selected `query` mode. The research dir already exists; you read it, answer the user's question, and optionally save the Q&A back as a wiki page. **No writes to `raw/`, `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/comparisons/`, `wiki/repos/`, `wiki/overview.md`, `wiki/synthesis.md`, or `index.yaml` ever happen here.** Allowed writes: `wiki/questions/YYYY-MM-DD-<slug>.md` (Q&A save-back), `wiki/open-questions.md` (when the user explicitly flags an unresolved question), `index.md` (regenerated), `log.md` (append).

### Q.1 — Locate the research dir

Use the same locator logic as Step 0 (path provided / topic slug / scan `working-dir` / ask if multiple).

### Q.2 — Load the index

Read `<research_dir>/index.yaml`. The YAML is canonical and has the full schema. The MD is for humans browsing in Obsidian.

If `index.yaml` is missing but `index.md` and `wiki/` exist, continue in **read-only fallback**:
- Read `index.md` for topic, source list, scores, origins, and raw/source-page links.
- Read `wiki/overview.md` / `wiki/synthesis.md` for synthesized answers.
- Do not save Q&A, regenerate `index.md`, append to `log.md`, or mutate wiki files in fallback mode.
- Tell the user once: "`index.yaml` is missing, so I answered from `index.md` + wiki fallback. Restore/regenerate `index.yaml` before append/deep ingest."

Parse and understand:
- `topic`, `input_summary`, `total_sources`, `total_wiki_pages`
- `sources[]` — `title`, `origin`, `original_path`, `source_url`, `authors`, `published_date`, `publication`, `relevance_score`, `summary`, `tags`, `uri_full`, `uri_highlights`, `uri_source_page`, `assets`, plus origin-specific fields (`readwise_location`, `nlm_*`, `github_*`)

### Q.3 — Three+ layer progressive disclosure

For any source, read in this order and stop when the user's question is answered:

1. **Layer 1 — `summary`** in `index.yaml`. Always available, ~2–3 sentences. The default — never go deeper unless there's a reason.
2. **Layer 1.5 — `uri_source_page`** (`wiki/sources/<slug>.md`). LLM-extended summary that's denser than Layer 1 but lighter than Layer 3. Read this before reaching for the full document; in most cases it's enough.
3. **Layer 2 — `uri_highlights`**. Optional. Exists only when the source carries **manually user-curated** highlights (typically Readwise-synced). Never LLM-extracted.
4. **Layer 3 — `uri_full`**. The complete document. Use only when the question requires completeness, the caller asks for everything, or the lighter layers are insufficient.

Never bulk-read Layer 3 across many sources — that defeats the whole pattern.

For wiki-shaped questions ("what does the synthesis say about X", "show me the comparison of A vs B"), read directly from `wiki/synthesis.md`, `wiki/overview.md`, `wiki/comparisons/...`, `wiki/entities/...`, `wiki/concepts/...`, `wiki/contradictions.md`, `wiki/open-questions.md` — these are short by design.

### Q.4 — Serve the request

Match the user's request to one of these shapes:

**Query mode** ("find sources about X"): Scan summaries + tags + entity/concept frontmatter. Return matches at Layer 1.

**Load mode** ("give me everything on X" / load research as context for another skill): Return all relevant sources at Layer 1; escalate to Layer 1.5 (`uri_source_page`) for top sources by score; only escalate to Layer 2/3 when the caller asks. Be a clear citizen of the `depth` knob:
- `summary` → Layer 1 only
- `wiki` → Layer 1 + 1.5 (read source pages for top N)
- `highlights` → Layer 1 + 1.5 + Layer 2 (where present), falls through to Layer 3 when Layer 2 is null
- `full` → escalate to Layer 3 for sources the caller specifies (NOT all sources by default)

**Filter mode**: filter `sources` by `origin`, `readwise_location`, `relevance_score >= threshold`, `tags`, seeds-only (`relevance_score == 1.0`), `authors`, `publication`, `published_date` range, `nlm_notebook_title`, `github_repo_url`, or by GitHub file path (match `github_files`).

**Drill-down mode** ("tell me more about source X" / "what does the wiki say about concept Y"): For sources, escalate Layer 1 → 1.5 → 2 → 3 only as needed. For wiki concepts/entities, read the page directly.

**Compose mode** ("summarize what we know about X"): synthesize from the wiki layer (overview / synthesis / relevant entity-concept pages) — these are already the synthesis. If the wiki layer doesn't cover the question, fall back to Layer 1 of relevant sources, then Layer 1.5 if needed.

For GitHub sources: `uri_full` points at `<repo>/ARCHITECTURE.md` (a wiki hub). To drill into a specific module, read ARCHITECTURE first, find the inline link to the module doc (e.g., `[vectordb](./vectordb.md)`), and read it. Module docs are not separately indexed.

### Q.5 — Q&A save-back

After answering, decide whether to save the Q&A as wiki content. **Save when EITHER condition is met:**
- The user explicitly bookmarks ("save this", "remember this answer", "keep this"), OR
- The answer cites ≥ 2 sources (i.e., the question required synthesis across the wiki)

Otherwise, do not save — most questions are conversational and shouldn't compound.

#### The split: knowledge in the wiki, question as a slim pointer

When you save, **never put the answer body inside `wiki/questions/`.** The actual knowledge — diagrams, claims, source citations, code permalinks — lands in the wiki at the most appropriate existing location (the **knowledge doc**). The `wiki/questions/` entry stays a slim pointer: the verbatim question, a 1-line *why this matters*, and a wikilink to the knowledge doc.

This split has two purposes:

1. **Keep the questions index minimal** — future agents loading context see a thin question list, not a wall of answers. Cheap to scan, cheap to load.
2. **Enable referencing, not duplication** — one knowledge doc can be referenced by multiple question pages over time. If a similar question comes back, **enrich the existing knowledge doc** and write a new slim question page that points at it. Never duplicate.

#### Pick the landing for the knowledge doc by question scope

| Question scope | Knowledge doc lands at | Notes |
|---|---|---|
| **Repo-scoped** — drills into a single GitHub source already in the wiki | `wiki/repos/<repo>/<TOPIC>.md` (e.g. `wiki/repos/claude-code/TOOL_PATTERNS.md`) | Add a "Deep dive" cross-link from the relevant `ARCHITECTURE.md` section so a reader scrolling the architecture finds it naturally. |
| **Concept / entity drill-down** — about a concept or entity the wiki tracks | Enrich existing `wiki/concepts/<slug>.md` / `wiki/entities/<slug>.md` in place | If the concept doesn't yet have a page but the answer has enough material to start one, create it. If it's only a single-source mention, flag in `wiki/open-questions.md` for next ingest instead. |
| **Comparison** — compares ≥ 2 concepts/entities the wiki tracks | `wiki/comparisons/<a-vs-b>.md` (create or enrich) | |
| **Cross-cutting synthesis** — doesn't fit the buckets above | `wiki/notes/<topic-slug>.md` (create the `wiki/notes/` dir if absent) | Catch-all for question-driven knowledge that synthesizes across sources without being scoped to a specific repo / concept / comparison. |

**Idempotency rule**: if a knowledge doc on the same topic already exists, *update it in place*. Don't write a new doc just because the question came back. Update its frontmatter (`last_updated`, append to `spawned_by_question`), enrich the body, and the new slim question page in `wiki/questions/` points at the (now-enriched) doc.

#### Knowledge doc — content rules

The knowledge doc carries the substance of the answer:

- **Frontmatter** with `type`, `name`, `created`, `last_updated`, and `spawned_by_question` (path to the slim question page; if multiple questions have enriched this doc, list them).
- **Mermaid diagrams as first-class citizens** when the answer describes a system, a process, a hierarchy, or relationships between components. Pick the type from `agents/github_spec_writer.md` § "Mermaid guidance" (`flowchart` / `sequenceDiagram` / `classDiagram` / `mindmap` / `stateDiagram-v2`). Prefer a diagram over a prose paragraph whenever the explanation is structural.
- **Citation discipline** — every claim wikilinks to its source page (`[[wiki/sources/<slug>]]`) or its raw doc with a heading anchor (`[[wiki/repos/<repo>/ARCHITECTURE.md#<heading>|cite]]`). Code snippets get commit-pinned permalinks where applicable.
- **A final `> Synthesis:` line** with your meta-judgment + a one-sentence hint at what new sources would extend or revise this doc.

#### Slim question page — template

Write to `<research_dir>/wiki/questions/YYYY-MM-DD-<question-slug>.md`. Slugify the question to ≤ 60 chars (drop articles, lowercase, kebab-case).

```markdown
---
type: question
name: <verbatim user question, no editorializing>
asked_on: <ISO-8601 date>
sources_cited: [<wiki page paths cited by the answer>]
answer_doc: <wiki path to the knowledge doc>
---

# <verbatim user question>

> Asked on <date>. Answered using <N> source(s) and <M> wiki page(s).

## Answer

Full answer lives at **[[<answer_doc path without extension>|<doc title>]]**.

It covers:
- <one bullet per major section of the knowledge doc — 3–6 bullets max, each ≤ 12 words>

## Why this matters

<1 sentence — what the user can do with this answer>

> Synthesis: <one line — what kinds of follow-up sources or questions would extend the knowledge doc>
```

**Hard rules for the question page:**

- **No diagrams, no extended prose, no code, no per-claim citations.** Those all live in the knowledge doc.
- **Cap the question page at ~25 lines.** If you're writing more, you're putting knowledge in the wrong place — move it to the doc.
- **Use referencing, not copying.** The question page exists so future agents can ask "what questions has the user asked?" cheaply, not to re-explain answers.

If the user explicitly flagged a follow-up they want investigated next, ALSO append it to `wiki/open-questions.md` with the date and cite the question page that spawned it.

After writing both files (knowledge doc + slim question page), regenerate `index.md` (the new pages change `total_wiki_pages`):

```bash
uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/build_index_md.py --research-dir "<research_dir>"
```

### Q.6 — Append to log.md

```markdown

## [YYYY-MM-DD] query | <topic>

- question: "<verbatim, truncated to 200 chars>"
- sources cited: <count>
- wiki pages cited: <count>
- saved as: wiki/questions/<filename> (slim pointer) + <answer_doc path> (knowledge doc — new or enriched) — or "not saved"
```

If the answer wasn't saved, still log it — the log records the conversation flow even when nothing landed in `wiki/`.

### Q.7 — Present the answer

Standard answer formatting:

```
## <Question rephrased as topic line>
**From research on <topic>** — <N sources cited, M wiki pages>

<answer body with [[wikilinks]] to source pages, entity/concept pages, and where relevant `[Original](<source_url>)` links>

### Sources cited
1. <Title> (origin: <origin>, score: 0.XX) — [[wiki/sources/<slug>]] · [Original](<source_url or "n/a">)
2. ...

<if saved> 📌 Saved: knowledge at `<answer_doc path>` (new / enriched), slim pointer at `wiki/questions/<filename>`. Add to open-questions if you want me to follow up next ingest.
<if not saved> _(Not saved — single-source answer. Tell me "save this" if you want it kept.)_
```

When the caller is another skill (programmatic, not the user directly), drop the conversational framing and return structured data: a YAML-shaped block with `sources_cited`, `wiki_pages_cited`, `answer_layers_used`, `saved_question_path`, `saved_answer_doc_path`.

## Step 0.5 — Preflight: source CLI availability (ingest modes only)

This skill orchestrates external CLIs that may not be installed. **Skip this entirely for
query mode.** For ingest modes, only check the CLIs that the selected route can actually
use. Seed-only modes (`append-trusted`, `append-light`, seed-only `init`) check
seed-specific CLIs only: `git` for GitHub seeds, `bdata` for generic web seeds, and no
Obsidian/Readwise/NLM discovery check. Discovery modes (`append-deep`, `init` with
discovery) run the full source preflight. A missing CLI must never crash the run with a
cryptic `command not found`; it must degrade gracefully with a clear, named warning.

For discovery modes, run one detection pass and remember the result as `available_clis`:

```bash
for cli in obsidian readwise nlm bdata git; do
  if command -v "$cli" >/dev/null 2>&1; then
    echo "$cli: available"
  else
    echo "$cli: MISSING"
  fi
done
```

For seed-only modes, build `available_clis` from the seed list: include `git` only if a
GitHub seed is present, include `bdata` only if a generic web seed is present, and mark
other source CLIs as `not_needed`.

Degradation policy — apply per source. For every MISSING CLI that is relevant to the
selected route, **emit a loud one-line warning to the user up front** (not silently),
naming the CLI, the capability lost, the bundled usage skill, and that the run continues
without it:

| CLI | Powers | If MISSING → |
|---|---|---|
| `obsidian` | Obsidian vault search (a research source) | Warn: "⚠️ `obsidian` CLI not found — skipping your vault as a source. See the `obsidian-cli` skill to install." Drop Obsidian from `available_clis`; continue with other sources. |
| `readwise` | Readwise library + feed search | Warn: "⚠️ `readwise` CLI not found — skipping Readwise. See the `readwise-cli` skill (`npm install -g @readwise/cli`)." Continue. |
| `nlm` | NotebookLM search | Warn: "⚠️ `nlm` CLI not found — skipping NotebookLM. See the `nlm-skill`." Set `notebook_ids = []`; skip Step 3b's auth check. Continue. |
| `bdata` | Web-seed crawling + Readwise→URL fallback | Warn: "⚠️ `bdata` CLI not found — web pages will be fetched with the lower-fidelity WebFetch fallback. See the `brightdata-cli` skill." Use WebFetch. Continue. |
| `git` | GitHub repo ingestion (Step 1a) | Warn (only if the brain dump contains a GitHub URL): "⚠️ `git` not found — skipping GitHub repo(s): `<list>`." Skip Step 1a entirely; drop those seeds. Continue. |

YouTube ingestion does not require an API key. It uses public captions via
`youtube-transcript-api`; videos with unavailable captions are skipped later by the
builder with a clear per-video error.

**Hard stop condition.** For discovery modes only: if `obsidian`, `readwise`, AND `nlm`
are all MISSING **and** the brain dump carries no usable seeds (no web URL, no YouTube
URL, no `git`-able GitHub repo, no local/web PDF), there is nothing to research. Stop and
tell the user clearly:

> ❌ No research sources available. Install at least one source CLI (`obsidian`,
> `readwise`, or `nlm` — see their bundled skills) or include a seed URL/PDF, then re-run.

Otherwise proceed with whatever is available. **Pass `available_clis` into every researcher
subagent (Step 4)** so it only attempts searches for installed CLIs. Auth (not just
presence) is re-checked at point of use for `nlm` (Step 3b) and `bdata` (Step 1).

## Step 1 — Understand the brain dump

Read whatever the user provides. Extract:
- **Core topic**: What is this research about?
- **Key themes**: What are the 3-5 main concepts or angles?
- **Intent**: Are they creating content, building something, learning, or exploring?
- **Specific entities**: Names, tools, frameworks, people mentioned
- **Seed URIs**: Any URLs, file paths, or vault note references included in the brain dump. These are first-class research inputs — they serve as both context for guiding search queries AND as sources to include in the final research directory.

### Processing seed URIs

If the brain dump contains URIs, process them before moving to step 2:

1. **Vault paths** (e.g., `Notes/Some Note.md` or `[[Some Note]]`): Read the file directly. These go straight into the research output.
2. **YouTube URLs** (`youtube.com/watch`, `youtu.be`, `youtube.com/shorts`, `youtube.com/embed`, `youtube.com/live`): Treat as first-class video seeds, not generic web pages. Process them before generic web URLs. Create a seed entry with `origin: "youtube"`, `original_path: "youtube://<video_id>"`, `source_url: <url>`, `youtube_url: <url>`, `youtube_video_id: <video_id>`, `transcript_source: "transcript_api"`, `timestamps_available: true`, `relevance_score: 1.0`, and a short placeholder `summary` from the user's framing. The raw extraction happens in the Builder via `scripts/youtube_extract_transcript.py`. If captions are unavailable, the Builder records the source as skipped with the script's JSON error unless the user provided a manual transcript file.
3. **Generic web URLs** (e.g., `https://example.com/article`) — any `http(s)://` link that is **not** one of the recognized special origins below (not a vault path, not a Readwise reference, not a GitHub repo, not a NotebookLM URI, not a YouTube URL, and not a `.pdf`): **crawl it with the Bright Data CLI via the `/brightdata-cli` skill, not WebFetch.** Bright Data handles bot-blocking, CAPTCHAs, paywalled/JS-rendered pages, and geo-walls that WebFetch silently fails on, and returns clean markdown by default:

   ```bash
   # Default output is clean markdown — exactly what we want for the raw layer.
   bdata scrape "<url>" -o "working-dir/research-scrape-<slug>.md"
   # Heavy / slow pages:
   bdata scrape "<url>" --async   # then: bdata status <job-id> --wait
   ```

   - **Check availability first (presence, then auth).** Guard the binary explicitly:
     ```bash
     command -v bdata >/dev/null 2>&1 || echo "MISSING: bdata"
     ```
     If `bdata` (a.k.a. `brightdata`) is MISSING, **or** it's present but unauthenticated (`bdata config` fails), **fall back to WebFetch** so the run still completes — and tell the user once, clearly: "⚠️ Bright Data unavailable (not installed / not authenticated) — fetched `<url>` with the lower-fidelity WebFetch fallback; see the `brightdata-cli` skill and re-run for full fidelity." Never let a missing `bdata` abort the seed.
   - **Known platforms get richer extraction.** When the URL is a platform Bright Data has a dedicated pipeline for (LinkedIn, Reddit, Amazon, Instagram, TikTok, Google Maps, …), prefer `bdata pipelines <type> "<url>"` over a plain scrape for structured output (`bdata pipelines list` to see all types; full reference in the `/brightdata-cli` skill). Otherwise use `bdata scrape`. YouTube is handled by the first-class transcript path above, not by Bright Data, unless the user provides a non-YouTube video page that must be scraped as ordinary web content.
   - Capture the returned markdown as the source's `fetched_markdown` (see below) so the builder writes the raw file without re-fetching. Set `origin: "web"`, `original_path: <full url>`, `source_url: <full url>`.
4. **Readwise references**: If the user references a specific Readwise source by name, search for it via the MCP tool.
5. **NotebookLM references** (e.g., `nlm://notebook/<id>`, a notebook name, or "my NotebookLM notebook on X"): These reference an entire notebook. Do not treat the notebook itself as a seed source — instead, note the notebook ID for the NLM discovery step (Step 3b) so it's always included in the search. Individual sources within it will be discovered during the research rounds.
6. **GitHub repositories** (e.g., `https://github.com/owner/repo` or `.../tree/<branch>`): Process via the GitHub pipeline below (Step 1a). Produces one `ARCHITECTURE.md` always and one `<module>.md` per targeted module. GitHub never participates in research rounds — it is always seed-only.
7. **Local PDFs** (e.g., a path ending in `.pdf` from the user's filesystem, including paths inside the vault like `Media/some-paper.pdf`): Treat as a first-class seed. The actual extraction happens in Step 6.2 via `scripts/extract_pdf.py` — at this stage just record the seed entry with `origin: "pdf"`, `original_path: pdf://<basename>`, `source_url: null`, and a placeholder `summary` (the user's framing if they provided one, else empty — the source_writer will fill it in from extracted text in Step 6.3). Store the absolute path on the seed entry as `local_pdf_path` so Step 6.2 knows where to extract from.
8. **Web PDFs** (a URL ending in `.pdf`): Same treatment as local PDFs, but Step 6.2 will download to `raw/assets/<slug>/original.pdf` first via `httpx`, then extract. If the `httpx` download is blocked (403 / bot wall / CAPTCHA), retry the download through Bright Data (`bdata scrape "<url>" -o "raw/assets/<slug>/original.pdf"`, see `/brightdata-cli`) before giving up.

For each seed URI, create a finding entry (same format as research subagent findings — including `author`, `published_date`, `publication`, `source_url` metadata fields). For web seed URIs, also include a `fetched_markdown` field carrying the cleaned content from the Bright Data scrape (or the WebFetch fallback), so the builder can write the file directly without a re-fetch. **Seed URIs always get `relevance_score: 1.0`** — the user explicitly provided them, so they are the highest-relevance sources by definition. They skip reranking entirely and are always included in the final output. Never assign a seed URI a score lower than 1.0, and never filter one out during reranking.

### Step 1a — GitHub pipeline (per repo URL)

When the brain dump contains a GitHub repo URL, process it BEFORE writing `seeds.json`.

**Guard: requires `git`.** This pipeline shells out to `git` (via `github_clone.py`). If
`git` is MISSING (from Step 0.5), **skip the GitHub pipeline entirely** — do not attempt
the clone. Warn the user clearly: "⚠️ `git` not found — skipping GitHub repo(s): `<list of
repo URLs>`. Install git and re-run to include them." Drop those GitHub seeds and continue
with the rest of the ingest.

The GitHub pipeline never clones *into* the research directory; clones go to a reusable `.github-cache/` placed **as a sibling of the research dir** (i.e. in the research dir's parent — e.g. for `Projects/My Project/research-<slug>/` the cache lands at `Projects/My Project/.github-cache/`). This keeps each project's reusable clones next to its own folder. Only curated spec docs land in the final research dir.

**One index entry per repo.** Each repo produces a `<repo>/ARCHITECTURE.md` that acts as a wiki hub plus a set of `<repo>/<module>.md` neighbor docs. Only `ARCHITECTURE.md` is registered in `index.yaml` (`uri_full: "<repo>/ARCHITECTURE.md"`). The module docs are written to disk alongside it, but they are reached by following links inside ARCHITECTURE — they are not separate entries.

For every unique `https://github.com/<owner>/<repo>[...]` URL in the brain dump:

1. **Parse targets** — run the parser over the brain dump AND any markdown files the user referenced (e.g., an outline.md). The parser extracts repo-relative file paths + line ranges and groups them by parent directory (one "module" per dir):
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/github_parse_targets.py \
     --repo "<repo_url>" \
     --text "<brain_dump_text>" \
     --file "<linked_markdown_file_1>" \
     --file "<linked_markdown_file_2>" \
     --output "<research_dir>/github-targets-<repo>.json"
   ```
   Pass `--text` for each inline text blob and `--file` for each referenced markdown file. If no markdown files were referenced, pass only `--text`. The output JSON has `repo_url`, `owner`, `repo`, `branch`, and `modules: [...]`. An empty `modules` list means global mode (only ARCHITECTURE.md will be generated).

2. **Shallow-clone** the repo into the cache. Pass `--research-dir` so the cache lands as a sibling of the research dir (its parent), not under working memory:
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/github_clone.py \
     --repo "<repo_url>" \
     --research-dir "<research_dir>"
   ```
   The script prints `{owner, repo, branch, clone_path, commit_sha, action}` as JSON on stdout — capture these for the spec writers.

3. **If `modules` is non-empty, first spawn one `github_spec_writer` per module** IN PARALLEL (module mode) so the architecture writer in the next step can reference real, written files. Each gets:
   - `clone_path`, `repo_url`, `owner`, `repo`, `commit_sha`, `branch`, `research_topic`
   - `mode: "module"`
   - `module_path`, `module_name`, `files` (from the parser output)
   - `output_path: <research_dir>/github-staging/<repo>/<module_name>.md`

4. **Then spawn ONE `github_spec_writer` in architecture mode** to write `<research_dir>/github-staging/<repo>/ARCHITECTURE.md`. Pass the same shared inputs plus:
   - `mode: "architecture"`
   - `output_path: <research_dir>/github-staging/<repo>/ARCHITECTURE.md`
   - `module_docs`: the module entries from Step 1, each `{module_path, module_name, filename: "<module_name>.md"}`. Empty in global mode.

   The architecture writer is responsible for:
   - A dedicated **Module Index** outline section, one line per `module_docs` entry: a ≤15-word summary + a relative link to the file (e.g., `[vectordb](./vectordb.md)`).
   - Organic cross-references in the narrative — when a module is mentioned in prose ("the VDB abstraction layer…"), link inline to the module doc rather than re-explaining.

5. **Emit exactly ONE seed entry per repo**, keyed to the ARCHITECTURE doc:
   - `origin: "github"`, `relevance_score: 1.0`
   - `title: "<repo>"` (plain, not "<repo> — Architecture" — the ARCHITECTURE is the canonical view of the repo)
   - `original_path: "github://<owner>/<repo>@<commit_sha>"`
   - `source_url: https://github.com/<owner>/<repo>/tree/<commit_sha>`
   - `github_repo_url: "https://github.com/<owner>/<repo>"`
   - `github_commit_sha: <commit_sha>`
   - `github_branch: <branch>`
   - `github_files`: **union** of every file path referenced across all modules (from the parser output) — used by `/research-distill` for matching, not for indexing individual docs. Empty list in global mode.
   - `authors: ["<owner>"]` (augment from README if a clear author is declared)
   - `publication: "GitHub"`
   - `staged_spec_path`: absolute path to the staged `ARCHITECTURE.md` (builder copies from here)

   Do NOT emit separate entries for module docs — they live alongside ARCHITECTURE in the repo subfolder and are reached via its links.

Once the seed list is assembled (including the GitHub entries), write it to `<research_dir>/seeds.json` (shape: `{"seeds": [ ... ]}`) so the Builder Subagent (Step 6) can consume it without going back through the orchestrator's context.

Use the content from seed URIs to enrich your understanding of the topic. Extract additional key themes, terminology, and concepts from them. In discovery modes, these inform the search queries you generate in Step 3; in seed-only modes, they inform the per-source wiki pages and overview/synthesis updates.

Summarize your understanding back to the user in 2-3 sentences so they can correct you if needed.

## Step 2 — Configure discovery depth

Skip this step entirely for `query`, `append-trusted`, `append-light`, and seed-only
`init`. Those modes do not run research rounds; set `rounds_completed: null` for trusted
single-source ingest and `rounds_completed: 0` for light/seed-only ingest.

For `append-deep` or `init` with explicit discovery, ask only after showing the routing
plan from Step 0:

1. **How many research rounds?** Default **1** for `append-deep`, **2** for `init` with
   discovery. Suggest 3-5 only when the user explicitly asks for exhaustive coverage.
2. **How many queries per round?** Default **4 for round 1, 2 for rounds 2+**. This keeps
   new-user and demo runs practical while still allowing depth when requested.
3. **Topic slug** - short kebab-case name for the output directory (suggest one based on
   the topic).

Capture the answers as `total_rounds`, `queries_per_round = (round1_count,
subsequent_count)`, and `topic_slug`. Use the defaults when the user accepts them
unchanged.

## Step 3 — Generate initial search queries

Run this step only for `append-deep` or `init` with explicit discovery. Seed-only modes
skip directly to Step 6 after Step 1.

Based on the brain dump, generate **exactly `queries_per_round[0]` queries** (default 4) that approach the topic from different angles. The goal is focused breadth - enough to discover missing context without turning a simple request into a long research run.

Think about:
- **Direct terms**: The obvious keywords
- **Related concepts**: Adjacent ideas the user might have notes on
- **Synonyms and alternate framings**: Different ways the same idea might be expressed
- **Specific entities**: People, tools, frameworks mentioned in the brain dump
- **Broader context**: The domain or field this sits within

Write these queries down before spawning subagents — you'll refine them in later rounds.

## Step 3b — Discover NotebookLM notebooks

Run this step only for `append-deep` or `init` with explicit discovery. Seed-only modes do
not query NotebookLM.

The source coverage rule for discovery modes is non-negotiable: **every discovery run
queries every NotebookLM notebook, every time. No heuristic filtering.** This is
intentional - the reranker filters at the end; we cast the widest possible net only when
the user chose deep discovery.

1. **Check presence, then authentication.** If `nlm` was MISSING in Step 0.5, skip this
   entire step: warn "⚠️ `nlm` CLI not found — skipping NotebookLM (see the `nlm-skill`)",
   set `notebook_ids = []`, and continue. If `nlm` is present, run `nlm login --check`. If
   that fails, log a loud warning that NotebookLM will be skipped for this run (auth
   expired/absent), set `notebook_ids = []`, and continue. Do NOT silently skip in either
   case — the user needs to know NLM was offline so they can decide whether to re-run after
   installing/fixing it.

2. **List notebooks**: Run `nlm notebook list --json` to get all available notebooks with their IDs, titles, and source counts.

3. **Filter out empty notebooks only** (source_count = 0) — there's nothing to search. Every other notebook is included.

4. **Build `notebook_ids`**: A list of `{id, title}` objects covering every non-empty notebook. Pass it to every researcher subagent.

5. **User-specified notebooks**: If the user referenced specific notebooks in their brain dump (Step 1), they are already in `notebook_ids` (everything is). Note them in the report so the user knows they were prioritized in the search angles.

Cost trade-off: querying all notebooks scales with the size of the user's NLM library. For libraries above ~30 notebooks this can be slow — accept the cost; the reranker handles relevance filtering. If it becomes consistently painful, this is where a `--scope` knob would land (out of scope for now).

## Step 4 — Run research rounds

Run this step only for `append-deep` or `init` with explicit discovery.

For each round, spawn **one Research Subagent per query** in parallel using the Agent tool. Each subagent follows the instructions in `agents/researcher.md` (read that file and pass its content as the subagent prompt, along with the specific query and context).

The subagent prompt should include:
- The search query to execute
- The overall research topic (so it can assess relevance)
- The key themes from step 1
- A path for saving its results as a JSON file
- The `notebook_ids` list from Step 3b (may be empty if NLM is unavailable)
- The `available_clis` set from Step 0.5 — the researcher searches **only** the sources whose CLI is available and skips the rest (it must not call a CLI that wasn't listed as available)

**Subagent result format** (saved as JSON by each subagent — see `agents/researcher.md` Step 5 for the full schema including the metadata fields `author`, `published_date`, `publication`, `source_url`):
```json
{
  "query": "the search query",
  "findings": [
    {
      "title": "Note or highlight title",
      "original_path": "full path to source file or readwise identifier",
      "origin": "obsidian" or "readwise" or "notebooklm",
      "relevance": "high" or "medium",
      "summary": "2-3 sentence summary of why this is relevant",
      "key_concepts": ["concept1", "concept2"],
      "content_preview": "first 200 chars of the content",
      "author": "...", "published_date": "...", "publication": "...", "source_url": "..."
    }
  ]
}
```

The researcher caps its output at 15 findings per query — this keeps the candidates JSON small without discarding real coverage.

After each round completes — **all steps delegate to bash/scripts/subagents so the round's JSON never enters your context**:

1. **Deduplicate** the round's subagent outputs via script:
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/dedup_findings.py \
     --inputs <research_dir>/round-N-query-*.json \
     --output <research_dir>/round-N-deduped.json
   ```
   The script dedups by `original_path` and keeps the finding with the longest `summary`. It prints a one-line count — that's all you see.

2. **Generate next-round queries** (only if another round follows) by spawning a Gap Analyzer Subagent. Read `agents/gap_analyzer.md` and pass its content as the subagent prompt, along with:
   - `research_topic`, `input_summary`, `key_themes` from Step 1
   - `deduped_findings_path`: `<research_dir>/round-N-deduped.json`
   - `round_number`: N (the round that just completed)
   - `total_rounds`: the configured total
   - `previous_queries`: queries from all prior rounds (you have these — they're what you generated/dispatched)
   - `target_query_count`: `queries_per_round[1]` (default 3)
   - `output_path`: `<research_dir>/round-{N+1}-queries.json`

   The subagent returns only the path to its output JSON. You then read just the `queries[].query` field (via `jq -r '.queries[].query'`) to pick up the next round's queries. Never load the full analyzer output into your context.

Continue for N rounds (as configured in step 2).

## Step 5 — Rerank and filter for quality

Skip this step for `append-trusted`, `append-light`, and seed-only `init`. For those
routes, write `<research_dir>/reranked-results.json` as `{"results": []}` and continue to
Step 6 with `seeds.json` only.

The research rounds cast a wide net intentionally — now it's time to be selective. Spawn a **Reranker Subagent** that reads `agents/reranker.md` and scores every deduplicated candidate against the user's original intent.

1. **Merge per-round deduped files** into a single candidates file via script (no LLM-side merging):
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/dedup_findings.py \
     --inputs <research_dir>/round-*-deduped.json \
     --output <research_dir>/reranker-candidates.json
   ```
   The same dedup script handles cross-round deduplication.

2. **Spawn the reranker subagent** with:
   - The research topic
   - The input summary from step 1
   - The key themes from step 1
   - `candidates_path`: `<research_dir>/reranker-candidates.json`
   - `output_path`: `<research_dir>/reranked-results.json`

3. **The reranker will**:
   - Sample each candidate using the cheapest signal that's sufficient — metadata (frontmatter / header lines / `nlm source describe`) first, then `head -n 750` / `tail -n 250` via bash, and only fall back to a full file read as a last resort. If that 750/250 window comes back as mostly noise (boilerplate, nav chrome, TOC without substance) for a source that's clearly long and on-topic, widen the window before escalating to a full read. Loading every candidate's full content into the context window is forbidden (see `agents/reranker.md` Step 3 for the exact sampling order).
   - Score each candidate 0.0–1.0 based on alignment with the user's intent
   - Rewrite summaries to be sharper and more intent-aligned
   - **Pass through all candidate metadata unchanged** (`author`, `published_date`, `publication`, `source_url`, origin-specific fields) so Step 6 can build `index.yaml` directly from the reranker output — no re-sampling required
   - Return all candidates with their scores (no filtering — every source is kept)

4. **In parallel with the reranker**, kick off the seed-URI portion of the Builder Subagent (Step 6). Seed URIs (score 1.0) skip reranking entirely, so their files can be copied/fetched while the reranker scores the rest. Pass the builder a seeds-only variant with `reranked_json` = empty results and `seeds_json` = your seed list. Join with the full builder in Step 6.

5. **Use the reranker's output** for the full Step 6 builder run. The reranker's rewritten summaries become the summaries in `index.yaml`. Sorting is handled deterministically by `build_index_yaml.py` (seeds first, then score descending) — you do not sort by hand.

This step scores and ranks sources by quality — the `relevance_score` in `index.yaml` tells future agents which sources to prioritize, but nothing is discarded.

## Step 6 — Build the raw layer

The Builder Subagent copies / fetches / pipes raw source content onto disk under `<research_dir>/raw/`. It does NOT build `index.yaml` — that happens in Step 6.5 after the wiki layer is in place, so the index can include `uri_source_page` references. You, the orchestrator, should never see individual source file contents in Step 6.

1. **Compute the research-dir path**. Default: `working-dir/research-<topic-slug>/`. Override if the user specified a different output path. Create the v4 layout up front:
   ```bash
   mkdir -p "<research_dir>/raw/assets" "<research_dir>/wiki"
   ```

2. **Spawn the Builder Subagent**. Read `agents/builder.md` and pass it as the subagent prompt, along with:
   - `reranked_json`: `<research_dir>/reranked-results.json`
   - `seeds_json`: `<research_dir>/seeds.json` (from Step 1)
   - `research_dir`: the path from step 1 above (final files go here AND scratch JSONs land here too — they're cleaned up in Step 7)
   - `topic`, `input_summary`, `rounds_completed` from Step 1 / Step 2
   - `skill_dir`: `${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research` (absolute path)
   - `mode: "raw_only"` — explicitly tells the builder to skip `index.yaml` emission

   In discovery modes, if you already started the **seed-only** builder in Step 5, wait for it to finish before launching the full builder - the full run is idempotent. In seed-only modes, launch the builder once with empty reranked results and the complete `seeds.json`.

3. **The builder returns**:
   ```json
   {"built": 25, "skipped": 2, "research_dir": "/path/to/research-<slug>", "raw_files": [...], "skipped_details": [...]}
   ```
   `raw_files` is a list of `{source_idx, raw_path, original_path, slug, origin}` entries — one per successful source. You'll feed this to Step 6.2 (asset processing) and Step 6.3 (source-page writing). `skipped_details` (truncated to 10) lists sources that fetched no content.

   **Layer 2 (`uri_highlights`) rule unchanged**: populated only when the source carries manually user-curated highlights (Readwise highlights synced into the vault at `Sources/Readwise/`, and raw Readwise documents whose vault copy holds the user's highlights). For everything else, `uri_highlights` is `null` and the full content lives at `uri_full` (Layer 3).

## Step 6.2 — Asset processing (images + PDFs)

For each entry in `raw_files`, run the asset pipeline. **All bash; nothing here goes through your LLM context.**

1. **PDFs** — for any source where `origin == "pdf"` (user-dropped) or where the original is a `.pdf` URL, the Builder will have already invoked `extract_pdf.py` to extract markdown + images and preserve the original at `raw/assets/<slug>/original.pdf`. If somehow not done, run it now:
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/extract_pdf.py \
     --pdf "<original_pdf_path>" \
     --output-md "<research_dir>/raw/<slug>.md" \
     --assets-dir "<research_dir>/raw/assets/<slug>"
   ```

2. **Images** — for every successful raw markdown file, download referenced images to local assets and rewrite refs:
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/download_assets.py \
     --markdown "<research_dir>/raw/<slug>.md" \
     --assets-dir "<research_dir>/raw/assets/<slug>"
   ```
   The script is a noop when there are no remote image references. Capture the JSON it prints; the `downloaded` array becomes the source's `assets` field in the index.

3. Build a per-source `assets` list — the manifest of asset files actually present on disk under `raw/assets/<slug>/`. This goes into the index in Step 6.5.

You can run the asset pipeline for many sources in parallel via a bash loop or `xargs -P`. Failures (e.g. a 404 on an image) are non-fatal — they're logged in the JSON output and the script leaves the original URL in place.

## Step 6.3 — Write per-source wiki pages (source_writer in parallel)

For each entry in `raw_files`, spawn one **`source_writer`** subagent (see `agents/source_writer.md`) **in parallel using a single message with multiple Agent calls**. Each subagent writes exactly one `wiki/sources/<slug>.md`. **You never read the raw files yourself** — that's the source_writer's job.

Each spawn passes:
- `raw_path`: absolute path to the raw file
- `source_metadata`: the JSON object for this source from the reranker output (already has all the index fields)
- `research_topic`, `input_summary` (from Step 1)
- `existing_entities`: list of `{slug, name}` for entity pages already in `wiki/entities/`. On init runs this is empty; on append runs it's populated by `ls`-and-frontmatter-extract via bash:
  ```bash
  for f in <research_dir>/wiki/entities/*.md; do
    awk '/^---$/{c++; next} c==1 && /^name:/' "$f"
  done
  ```
- `existing_concepts`: same pattern for `wiki/concepts/`
- `assets`: the per-source asset list from Step 6.2
- `output_path`: `<research_dir>/wiki/sources/<slug>.md`

Collect the JSON outputs from each subagent. Aggregate them into a single in-memory structure (or write to `<research_dir>/source-writer-outputs.json`). You'll need:
- `entities_referenced` and `concepts_referenced` — counts per slug across sources (used in Step 6.4 to decide which entity/concept pages to write).
- `suggested_new_entities` and `suggested_new_concepts` — candidates for new pages.

## Step 6.3.5 — Discussion checkpoint (discovery modes only; default ON for >3 sources)

Before spawning the entity/concept writers in Step 6.4, surface the emerging shape to the user and let them redirect emphasis. **Skip this step entirely for append-trusted, append-light, and seed-only init** unless the user explicitly asks for a discussion checkpoint. Skip it also when the user says "skip discussion" up front or when ingest passes touched <= 3 new sources - the cost outweighs the benefit at small scale.

Compute and present (to the user, not via subagent):

1. **Top-N sources by score** (5 max) — title + score + origin + one-line summary from the source page.
2. **Entity/concept clusters** — slugs whose mention counts are about to cross the threshold (≥2). Group by which sources they co-occur in. The user's eyes here are gold: they'll spot wrong slug merges, missed aliases, or wrong emphasis.
3. **Candidate comparisons** — pairs of slugs that mutually reference each other and would qualify for a comparison page. Surface 2–3.
4. **Open-question candidates** — questions surfaced in source-writer outputs.

Use `AskUserQuestion` with the four buckets above as a single multi-select question:

```
Before writing entity/concept pages, anything to redirect?
- ☐ Drop source: <title> (it's tangential to the topic)
- ☐ Merge slugs: "ralph-loop" + "ralph_loop" → "ralph-loop"
- ☐ Add comparison: <a> vs <b>
- ☐ Save these open questions: <list>
- ☐ Proceed as-is
```

Also offer "Other" so the user can type free-form redirects ("emphasize agent-loop more in synthesis", "demote source X to score 0.3", etc.). Apply the user's edits to your in-memory aggregate **before** spawning Step 6.4 writers. Source pages that have already been written stay; you just don't propagate their entities/concepts to the wiki layer.

Discussion is opt-out — the user can always say "skip discussion" to bypass this step. But default it ON. The whole point of Karpathy's pattern is the conversational loop; this step is where it lives.

## Step 6.4 — Write entity and concept pages (wiki_page_writer in parallel)

Aggregate slug → mention counts across all source_writer outputs. Apply the threshold: an entity or concept page is created (or updated) when `mention_count >= 2` across distinct sources. Single-source mentions stay only on the source page.

For each qualifying slug, spawn one **`wiki_page_writer`** subagent (see `agents/wiki_page_writer.md`) in parallel. Pass:
- `page_type`: `"entity"` or `"concept"`
- `slug`, `name`, `aliases` (from the source_writer outputs, deduped)
- `source_pages`: list of absolute paths to the `wiki/sources/*.md` pages that mention this slug. **Only these** — the writer reads only its in-scope source pages.
- `research_topic`, `input_summary`
- `existing_page_path`: path to existing wiki/entities/<slug>.md or wiki/concepts/<slug>.md if one exists; `null` otherwise
- `output_path`: where to write

Collect the JSON outputs. Each tells you `{action: created|updated|noop, source_count, confidence, tensions_found, open_questions_surfaced}`. Aggregate `tensions_found > 0` as a flag for the lint pass; aggregate `open_questions_surfaced` for Step 6.5.

You can run dozens of these in parallel — each is bounded by its `source_pages` list and reads no raw files.

## Step 6.5 — Write overview + synthesis (wiki_summary_writer in parallel)

Spawn two `wiki_summary_writer` subagents (see `agents/wiki_summary_writer.md`) in parallel:

1. **overview** — `page_type: "overview"`, `output_path: <research_dir>/wiki/overview.md`
2. **synthesis** — `page_type: "synthesis"`, `output_path: <research_dir>/wiki/synthesis.md`

Both receive `research_dir`, `research_topic`, `input_summary`, and `existing_page_path` (if a prior overview/synthesis exists). They discover wiki state themselves via bash and respect a context budget — you don't pre-load wiki pages for them.

## Step 6.6 — Append open questions

Aggregate any `open_questions_surfaced` reported by Step 6.4 wiki_page_writer outputs. Append them to `<research_dir>/wiki/open-questions.md` with a date-stamped section:

```bash
cat >> "<research_dir>/wiki/open-questions.md" <<EOF

## [$(date -u +%Y-%m-%d)] from ingest of $(wc -l < <(echo "<raw_files>")) source(s)

- <question 1>
- <question 2>
EOF
```

If `open-questions.md` doesn't yet exist, create it with a header line: `# Open questions\n`. Lint will surface and prune these later.

## Step 6.7 — Build index.yaml + index.md

Now that the wiki layer exists, build the canonical index. **Two scripts, in order:**

1. **Augment reranked results and seeds with `uri_source_page` and `assets`** for each source (via `jq` — never load JSON in your context):
   ```bash
   # For each source in reranked-results.json, add uri_source_page and assets fields
   # using the per-source mapping you built in Step 6.3.
   jq --slurpfile aug "<research_dir>/source-augments.json" \
      '.results |= map(. + ($aug[0][.original_path] // {}))' \
      "<research_dir>/reranked-results.json" \
      > "<research_dir>/reranked-final.json"

   # Do the same for seed sources; seed-only modes rely on this file.
   jq --slurpfile aug "<research_dir>/source-augments.json" \
      '.seeds |= map(. + ($aug[0][.original_path] // {}))' \
      "<research_dir>/seeds.json" \
      > "<research_dir>/seeds-augmented.json"
   ```
   Where `<research_dir>/source-augments.json` is a `{<original_path>: {uri_source_page: "...", assets: [...]}}` map you assembled from source_writer + asset-pipeline outputs.

2. **Run `build_index_yaml.py`** to emit the canonical index:
   ```bash
   PRIOR_CREATED=$(grep '^created:' "<research_dir>/index.yaml" 2>/dev/null | awk -F"'" '{print $2}' || true)
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/build_index_yaml.py \
     --reranked "<research_dir>/reranked-final.json" \
     --seeds "<research_dir>/seeds-augmented.json" \
     --research-dir "<research_dir>" \
     --topic "<topic>" \
     --input-summary "<input_summary>" \
     --rounds <rounds_completed> \
     ${PRIOR_CREATED:+--existing-created "$PRIOR_CREATED"} \
     --output "<research_dir>/index.yaml"
   ```
   On init runs `PRIOR_CREATED` is empty (no prior index); on append runs it preserves the original `created` timestamp.

3. **Run `build_index_md.py`** to regenerate the Obsidian-readable view:
   ```bash
   uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/build_index_md.py \
     --research-dir "<research_dir>"
   ```
   This is byte-stable: identical inputs → byte-identical output. Always the last write before the log entry.

## Step 6.8 — Append to log.md

Append a structured entry. Format is non-negotiable (the `## [YYYY-MM-DD] <op> | <subject>` prefix is what makes the log greppable):

```bash
DATE=$(date -u +%Y-%m-%d)
cat >> "<research_dir>/log.md" <<EOF

## [$DATE] ingest | <topic> ($(echo <raw_files_count>) sources)

- mode: <append-trusted | append-light | append-deep | init>
- rounds: <rounds_completed>
- expected runtime shown: <rough estimate from routing plan>
- raw files added: <count>
- wiki pages written: <count> sources, <count> entities, <count> concepts, overview + synthesis updated
- open questions surfaced: <count>
- skipped: <count> ($(echo <skipped_titles | head -3>))
EOF
```

If `log.md` doesn't exist, create it with a `# Log\n` header first.

## Step 7 — Clean up intermediary files

After the research directory is built successfully, delete intermediary JSONs that live alongside the canonical artifacts (top-level only — `raw/` and `wiki/` are recursed into for nothing here):

- `round*-query*.json`
- `round*-deduped.json`
- `all-rounds-deduped.json`
- `reranker-candidates.json`
- `reranked-results.json` and `reranked-final.json`
- `seeds.json`, `seeds-augmented.json`
- `source-augments.json`
- `source-writer-outputs.json`
- `notebook-ids.json`

```bash
rm -f "<research_dir>"/*.json
```

The glob is safe: `index.yaml` is YAML (not JSON), and `raw/`/`wiki/` are subdirs the glob does not descend into. After cleanup, only `index.yaml`, `index.md`, `log.md`, `raw/`, and `wiki/` remain at the research-dir root.

## Step 8 — Present results

Tell the user:
- **Mode**: selected route (`query`, `append-trusted`, `append-light`, `append-deep`, or `init`) and whether discovery ran
- **Runtime expectation**: the estimate shown before execution, plus whether the run stayed inside that expectation
- **Sources**: "Found N sources across R rounds, scores range from S_min to S_max" + brief thematic breakdown
- **Wiki**: "Wrote X source pages, Y entity pages, Z concept pages; overview + synthesis are at `wiki/overview.md` and `wiki/synthesis.md`"
- **Open questions**: if any were surfaced, mention the count and point at `wiki/open-questions.md`
- **Skipped**: if `skipped > 0`, one-line summary
- **Path**: the research dir absolute path
- **How to use it**:
  - For a quick view: open `index.md` in Obsidian (Obsidian-readable navigation)
  - For deep reading: open `wiki/synthesis.md` (the thesis) and `wiki/overview.md` (the catalog)
  - For programmatic access: pass `index.yaml` to `/research` (query mode), which handles progressive disclosure
- **Next steps suggestion**: "Run `/research-lint` to health-check the wiki, or `/research-render marp <topic>` to export a slide deck."

## Important notes

**Search strategy — Obsidian**: Use the `obsidian` CLI for search operations: `obsidian search query="<terms>" limit=20`. Once you have the file paths from search results, read the files directly using the Read tool. See the `obsidian-cli` skill for full command reference. **Guard:** only run this if `obsidian` is in `available_clis` (presence checked in Step 0.5 via `command -v obsidian`); if it's missing, skip the vault as a source — never let `command not found` abort the search.

**Search strategy — Readwise**: Use the `readwise` CLI (not the MCP tool). For the full command reference, access the `readwise-cli` skill. **Guard:** only run this if `readwise` is in `available_clis` (presence checked in Step 0.5 via `command -v readwise`); if it's missing, skip Readwise as a source with the Step 0.5 warning — never abort on `command not found`. Readwise splits into two areas and research must cover both:

- **Library** — documents the user manually saved. Highest signal; they deliberately chose each one. This is the default scope for `reader-search-documents` (`new`, `later`, `shortlist`, `archive`).
- **Feed** — RSS subscriptions. Still high signal because the user chose to subscribe, but noisier since every new item auto-ingests. Must be searched explicitly with `--location-in feed`.

Key commands the researcher subagent uses:
- `readwise reader-search-documents --query "<query>"` — library document search (default).
- `readwise reader-search-documents --query "<query>" --location-in feed` — feed document search.
- `readwise reader-search-documents --query "<query>" --note-search "<query>"` — searches the user's own annotations written on documents (high signal). Run a feed-scoped variant too.
- `readwise readwise-search-highlights --vector-search-term "<query>"` — semantic search across all highlights (spans both areas).
- `readwise reader-get-document-details --document-id <id>` — full document content as Markdown, used for the two-layer pattern.

The researcher subagent tags each Readwise finding with `readwise_location: "library" | "feed"` so the reranker can weight library hits slightly higher when two sources look otherwise equivalent.

**File naming**: When copying files to the research dir, slugify titles to kebab-case, remove special characters, and keep filenames under 60 characters. For Readwise highlights, prefix with `readwise-`.

**Deduplication matters**: The same note can be found by multiple queries. Always deduplicate by `original_path` before building the output. For NotebookLM sources that have a `source_url`, also deduplicate against Readwise and web sources sharing the same URL — prefer the Readwise version (it carries user-curated highlights and annotations).

**Search strategy — NotebookLM**: Use the `nlm` CLI. Key commands for research:
- `nlm login --check` — verify authentication before searching
- `nlm notebook list --json` — list all notebooks with IDs and titles
- `nlm note list <nb-id>` — list user-created notes in a notebook (these are prioritized over raw sources)
- `nlm notebook query <id> "question"` — one-shot Q&A against a notebook's sources (returns AI answer with cited sources)
- `nlm source list <nb-id>` — list imported sources in a notebook with IDs and metadata
- `nlm source describe <source-id>` — AI summary and keywords for a source
- `nlm source content <source-id>` — raw text content of a source
Sessions expire in ~20 minutes. If commands fail with auth errors, skip NLM for the remainder of the research run.

**NotebookLM note vs source priority**: Notebooks contain two types of content — **notes** (user-written synthesis, right panel in the UI) and **sources** (imported articles/papers, left panel). Notes always take priority because the user deliberately created them. The researcher subagent fetches notes first via `nlm note list`, then uses `nlm notebook query` to discover relevant raw sources. Notes get `nlm_content_type: "note"` and use `nlm://note/<id>` paths; raw sources get `nlm_content_type: "source"` and use `nlm://source/<id>` paths.

**Extensibility**: This skill searches Obsidian, Readwise, and NotebookLM, and accepts web URLs + GitHub repos as seed-only URIs (GitHub handled via the Step 1a pipeline). Generic web links are crawled with the Bright Data CLI (`bdata scrape` / `bdata pipelines`) via the `/brightdata-cli` skill — see Step 1, point 2. The architecture is designed so new sources can be added by extending the researcher agent with additional search steps; the natural next step is web-search rounds via `bdata search "<query>" --json` (the researcher harvests result URLs, then scrapes the promising ones with `bdata scrape`). The orchestrator doesn't need to change — it just spawns researchers and collects results.

## Agent reference

- `agents/researcher.md` — Research Subagents (one per query per round). Read and include its content when spawning each research subagent.
- `agents/gap_analyzer.md` — Gap Analyzer Subagent. Spawned between rounds to generate the next round's queries from the previous round's deduped findings.
- `agents/reranker.md` — Reranker Subagent. Spawned after all research rounds complete.
- `agents/builder.md` — Builder Subagent. Spawned in Step 6 to produce raw files (no longer writes `index.yaml` — that moved to Step 6.7 after wiki pages exist).
- `agents/github_spec_writer.md` — GitHub Spec Writer Subagent. Spawned in Step 1a — once in architecture mode per repo, plus one per targeted module.
- `agents/source_writer.md` — Source Writer Subagent. Spawned in Step 6.3, **one per raw source in parallel**. Reads one raw file and writes `wiki/sources/<slug>.md` with extended summary, key claims, quotes, and connections; returns suggested entities/concepts.
- `agents/wiki_page_writer.md` — Wiki Page Writer Subagent (entity OR concept). Spawned in Step 6.4, **one per qualifying slug in parallel**. Aggregates from per-source pages only — never reads raw.
- `agents/wiki_summary_writer.md` — Wiki Summary Writer Subagent (overview OR synthesis). Spawned in Step 6.5, **two in parallel**. Discovers wiki state itself via bash; capped at 5 full reads.

## Script reference

- `scripts/dedup_findings.py` — Deduplicates research findings by `original_path`, keeping the entry with the longest `summary`. Used per-round and to merge all rounds into the reranker input.
- `scripts/build_index_yaml.py` — Emits canonical `index.yaml` from reranker output plus seed URIs. Handles schema, sort order, and `created`/`last_updated` semantics deterministically. Called in Step 6.7 after the wiki layer is built so `uri_source_page` and `assets` fields can be populated.
- `scripts/build_index_md.py` — Generates Obsidian-readable `index.md` from `index.yaml`. Idempotent + byte-stable. Always the last write before the log entry.
- `scripts/extract_pdf.py` — PDF → markdown via `pymupdf4llm`. Extracts images to `raw/assets/<slug>/`, preserves the original PDF, flags low-quality (scanned) PDFs. Used in Step 6.2 for user-dropped or web-fetched PDFs.
- `scripts/download_assets.py` — Scans a markdown file for remote image references, downloads them to `raw/assets/<slug>/`, and rewrites references to local paths. Used in Step 6.2 on every raw markdown file.
- `scripts/github_parse_targets.py` — Parses the brain dump (and referenced markdown files) for GitHub file references against a specific repo. Groups them into modules by parent directory. Used in Step 1a.
- `scripts/github_clone.py` — Shallow-clones a GitHub repo into a reusable `.github-cache/` placed as a sibling of the research dir (`--research-dir` → its parent) and returns the HEAD SHA. Used in Step 1a.
