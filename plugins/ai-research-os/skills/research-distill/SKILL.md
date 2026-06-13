---
name: research-distill
description: Distill a research directory (produced by /research) into a single compact research.md containing a guideline-relative distillation of only the sources that were actually used in a piece of content. Use this skill whenever the user wants to extract used references from research, create a research appendix for an article, distill research into what was actually cited, or produce a portable reference file from a research directory. Trigger when the user says things like "distill my research", "extract used sources", "which research did I actually use", "create research.md", "compile references from research", or after finishing an article that used a research directory.
user_invocable: true
---

# Research Distill

You take a research directory (produced by `/research`) and a set of content files the user is working on, and produce a single `research.md` containing **only the sources that were actually used** in that content, distilled to just the claims, quotes, and nuances the content actually leans on. Every source keeps its full metadata + URI envelope so the writer agent can drill back to the wiki source page or raw file when it needs more depth.

This is the **audit/export side** of the research system — it answers "which sources from my research actually made it into the final content, and what specifically from each one?" The output is a working appendix sized for a writer agent's context window, not a verbatim mirror of the research directory.

## Step 1 — Gather inputs

You need two things:

### The content files
These are the files the user is actively working on — article guidelines, draft articles, notes, outlines, etc. The user may provide:
- A single file path (e.g., `Projects/Content/My Article/guideline.md`)
- A directory path (read all `.md` files in it)
- Multiple file paths
- A reference to "the current project" (look for article/guideline files in the current working directory)

Read all content files and concatenate their text into a single content corpus for matching.

### The research directory
Locate the research directory using the same logic as `/research`:
1. If the user provides a path, use it
2. Look for `research-*/` in the content's parent directory
3. Look in `working-dir/` (the default research root, relative to where the skill is run) for `research-*/`
4. If multiple exist, ask the user which one

Read `index.yaml` from the research directory.

## Step 2 — Match sources against content

For each source in `index.yaml`, determine whether it was **actually used** in the content. A source counts as "used" if either condition is met:

### Explicit references
The content mentions the source by:
- Title or partial title (e.g., "The Anatomy of an Agent Harness" or "Anatomy of an Agent Harness")
- Author name (e.g., "Mitchell Hashimoto", "Anthropic")
- URL or partial URL (e.g., "mitchellh.com", "blog.langchain.com")
- Citation number that maps to the source (e.g., "[3]" where reference 3 is this source)
- Filename reference (e.g., the `uri_highlights` or `uri_full` filename)
- NotebookLM notebook title or source URL (for `notebooklm` origin sources)
- GitHub repo URL, repo name, or any entry in `github_files` (for `github` origin sources). Only one source entry exists per repo — the `uri_full` ARCHITECTURE.md — so matching a single referenced file path is enough to include that whole entry. The module docs it links to live in the same subfolder and are available via those links, not as separate sources.
- YouTube URL, video ID, title, channel, or timestamped claim reference (for `youtube` origin sources). A timestamped mention like `12:30` near the video title or URL is enough to include the source.

### Traceable ideas
The content contains ideas, patterns, or concepts that are clearly traceable to the source. To check this:

1. Pick the best available content file for the source, in this order:
   - `uri_highlights` if set (user-curated condensation — highest signal, smallest read)
   - otherwise `uri_full` (the complete document — standard Obsidian notes, web seeds, and NotebookLM content land here because they have no Layer 2)
   - if both are `null`, fall back to the `summary` in `index.yaml` alone
2. Extract the key ideas, specific terminology, unique frameworks, or distinctive phrasings from whichever layer you read
3. Check whether those specific ideas appear (even paraphrased) in the content

**Be conservative with traceable matches.** Generic concepts like "agent loop" or "context window" appear in many sources — only match if the content uses a **specific** framing, example, or detail that's distinctive to that source. For example:
- "flush-before-discard invariant" is distinctive to the OpenClaw architecture articles
- "Ralph Loop pattern" is distinctive to the LangChain harness article
- A general mention of "ReAct" is NOT enough to match the original ReAct paper unless the content discusses specifics from it

## Step 3 — Build research.md

Create `research.md` in the same directory as the content files. The file contains one `<details>` block per matched source, ordered by `relevance_score` descending.

### File structure

```markdown
# Research Sources

> Distilled from `research-<slug>/index.yaml`
> Content: `<list of content file names>`
> Generated: YYYY-MM-DDTHH:MM:SS
> Sources used: N of M total

---

<details>
<summary>Source Title Here (score: 0.92)</summary>

<uri_highlights>path-to-highlights.md</uri_highlights>
<uri_full>path-to-full.md</uri_full>
<uri_source_page>wiki/sources/source-slug.md</uri_source_page>
<original_path>original vault or web path</original_path>
<origin>readwise</origin>
<relevance_score>0.92</relevance_score>
<tags>tag1, tag2, tag3</tags>
<summary>The index.yaml summary for this source.</summary>
<match_reason>Why this source was matched — explicit reference by title in section 3, and the "flush-before-discard" concept appears in the memory section.</match_reason>

### Relevant Claims
- Specific claim, datum, framing, or example from the source that the content draws on (one bullet per item, ≤30 words, concrete not generic).
- Another guideline-relevant claim — keep only what the content actually leans on.

### Verbatim Quotes
> "Distinctive phrase preserved exactly so the writer can cite it without re-reading raw."
> "Up to ~3 quotes per source; only when the guideline plausibly cites them or they anchor a distinctive framing."

### Nuances
- Caveat, counter-position, edge case, or qualification the guideline depends on. Omit this subsection if none apply.

### Wiki Pointers
- wiki/concepts/<slug>.md — one-phrase reason it's relevant
- wiki/entities/<slug>.md — one-phrase reason it's relevant

</details>

---

<details>
...next source...
</details>
```

### Rules for building each block

1. **`<summary>` tag** (the HTML one, child of `<details>`): Source title + score in parentheses. This is what's visible when the block is collapsed. For `github` sources, suffix the title with ` — GitHub repo` so the origin is legible at a glance (e.g., `weave-cli — GitHub repo (score: 1.00)`).

2. **Metadata XML tags**: One tag per field from `index.yaml`:
   - `<uri_highlights>`: Filename of the key-highlights file
   - `<uri_full>`: Filename of the full document file, or `null` if none
   - `<uri_source_page>`: The Layer 1.5 wiki source page (`wiki/sources/<slug>.md`) if present in `index.yaml`, else `null`. This is the writer agent's primary drill-down target when it needs more depth than the distilled body provides without jumping all the way to raw.
   - `<original_path>`: The original vault path or URL
   - `<origin>`: `obsidian`, `readwise`, `web`, `notebooklm`, `github`, `pdf`, or `youtube`
   - `<relevance_score>`: The numeric relevance score from `index.yaml` (1.0 = seed; otherwise derived from the researcher's high/medium tag)
   - `<tags>`: Comma-separated tag list
   - `<summary>`: The source summary from index.yaml
   - `<readwise_location>`: (Readwise sources only) `library` (user manually saved) or `feed` (ingested from an RSS subscription the user chose). Emit this tag only when `origin` is `readwise` and the field is present in `index.yaml`.
   - `<nlm_source_id>`: (NotebookLM sources only) The NLM source UUID
   - `<nlm_notebook_title>`: (NotebookLM sources only) The notebook's human-readable title
   - `<github_repo_url>`, `<github_commit_sha>`, `<github_branch>`, `<github_files>`: (GitHub sources only) Emit these when `origin` is `github`. `<github_files>` is a comma-separated list of the referenced file paths — surfacing it here makes the distilled `research.md` self-contained for audit.
   - `<youtube_video_id>`, `<youtube_url>`, `<youtube_channel>`, `<duration_seconds>`, `<transcript_source>`, `<transcript_language>`, `<transcript_language_code>`, `<transcript_is_generated>`, `<timestamps_available>`: (YouTube sources only) Emit these when present in `index.yaml`.

3. **`<match_reason>`**: A 1-2 sentence explanation of why this source was included — what explicit reference or traceable idea linked it to the content. This helps the user (and future agents) understand the connection.

4. **Distilled body**: Replace the source's prose with a guideline-relative distillation. Each block has up to four subsections — emit any subsection only if it has content for this source; omit it entirely otherwise. **Do not** reproduce the raw layer verbatim; the URI tags above already point at it.

   #### Subsections

   - **`### Relevant Claims`** — One bullet per specific claim, datum, framing, or example from the source that the content draws on (or directly supports). Each bullet is one line, ≤30 words, concrete. Generic concepts the source shares with many others ("uses an agent loop", "RAG matters") never earn a bullet — only source-distinctive content does. If the source contributes nothing the content actually leans on beyond an explicit citation, this subsection can be a single bullet naming what was cited.
   - **`### Verbatim Quotes`** — Up to ~3 short quotes preserved **byte-for-byte** (punctuation, casing, ellipses included), rendered as Markdown blockquotes. Only include quotes the guideline plausibly cites or that anchor a distinctive framing the writer agent might want to reproduce. This is the only lossless element of the body — it exists so the writer never round-trips to raw just to cite a phrase. When uncertain about exact wording, **prefer pulling the phrase as a quote** rather than paraphrasing it into a Relevant Claims bullet.
   - **`### Nuances`** — Caveats, counter-positions, edge cases, scope limits, or qualifications from the source that the guideline depends on or could miss without. Skip the subsection if none apply.
   - **`### Wiki Pointers`** — Paths (relative to the research dir) of `wiki/concepts/<slug>.md`, `wiki/entities/<slug>.md`, `wiki/comparisons/<a>-vs-<b>.md`, or `wiki/questions/<file>.md` pages that exist on disk and are relevant to this content via this source. One bullet per pointer, with a one-phrase reason. These are drill-down targets, not embedded content. Skip the subsection if no relevant wiki pages exist for this source.

   #### Read order for building the body

   Read in this order and stop once you have enough signal to populate the subsections:

   1. **`uri_source_page`** (`wiki/sources/<slug>.md`) if present — already condensed Layer 1.5 by the `source_writer` agent (extended summary, key claims, quotes, connections, entities, concepts). This is the **primary** distillation seed. Pull claims and quote candidates from here first.
   2. **`uri_highlights`** if present (Readwise-curated highlights — high signal per token, good for quote sourcing).
   3. **`uri_full`** as fallback, or to confirm exact wording for verbatim quotes.
   4. **`summary`** from `index.yaml` if every layer above is missing.

   Then re-read the content corpus and filter aggressively: keep only items the content actually draws on or plausibly cites. Everything else stays in the raw file, reachable via `<uri_full>` / `<uri_source_page>`.

   #### Length

   Soft cap **~300 words per source body** (sum across all subsections). Exceed it only when nuance genuinely demands. If the only available layer is `summary`, the body may be just one or two bullets — that's the expected shape, not an error. Note any missing layers in `<match_reason>`.

   #### GitHub repos

   GitHub sources use the same four-subsection contract with two adjustments: rename `### Relevant Claims` to `### Relevant Contracts`, and rename `### Wiki Pointers` to `### Module Pointers`. Soft cap rises to **~500 words** to accommodate the breadth across modules.

   - **`### Relevant Contracts`** — One bullet per guideline-relevant module. Each bullet names the module and summarises (≤30 words) the interface, behaviour, contract, or data structure the content draws on, including the names of key types/functions/files the guideline references. Only modules that pass the unchanged relevance check (`github_files` entry, module name mention, or specific traceable idea) earn a bullet.
   - **`### Verbatim Quotes`** — Same rules. Quotes can come from `ARCHITECTURE.md` or any module spec.
   - **`### Nuances`** — Design tradeoffs, invariants, init-time/order constraints, or scope limits the guideline relies on.
   - **`### Module Pointers`** — `repos/<repo>/ARCHITECTURE.md` plus one bullet per guideline-relevant module spec file (`repos/<repo>/<module>.md`). Module-doc filename is the kebab-case of the leaf parent directory name (e.g., `src/pkg/vectordb/interfaces.go` → `<repo>/vectordb.md`, `src/cmd/eval/run.go` → `<repo>/eval.md`); if the computed filename doesn't exist, consult ARCHITECTURE's Module Index outline for the correct slug. List relevant modules in the order they appear in ARCHITECTURE's Module Index (alphabetical fallback). These are pointers only — never embed module specs verbatim. Surface the trigger (file path or distinctive idea) for each module in `<match_reason>` so the user can audit relevance.

   #### Missing layers

   If `uri_source_page`, `uri_highlights`, and `uri_full` are all `null` or missing on disk (rare — fetch failure during `/research`): emit only the metadata block, set the body to a single line under `### Relevant Claims` noting "Source body unavailable; see `<match_reason>` for citation context", and explain in `<match_reason>` which layers were missing.

5. **Separator**: Use `---` between each `<details>` block for readability.

## Step 4 — Report results

Tell the user:
- **Mode**: "compact distillation" — the body of each source is a guideline-relative distillation; full raw text stays one hop away via `<uri_full>` / `<uri_source_page>`.
- How many sources were matched out of the total (e.g., "12 of 25 research sources were used in your content"). GitHub repos count as **one source** regardless of how many module pointers were listed — report the relevant-module subset separately (e.g., "weave-cli: 4 of 21 module specs pointed to (vectordb, pipeline, agents, evaluation)") so the user sees which modules were judged relevant. If you considered a module borderline and excluded it, mention it in the borderline-cases section so the user can add it back manually.
- A brief breakdown by match type (e.g., "8 explicit references, 4 traceable ideas")
- The path to `research.md`
- **Token estimate** for `research.md` — rough count via `chars / 4`. Helps the user budget the writer agent's context.
- Any sources that were borderline — close to matching but not quite — so the user can decide whether to include them

## Important notes

- **The contract is lossy on prose, lossless on metadata + URIs + verbatim quotes.** Distil the source body relative to the guideline; the URI envelope and quoted phrases must remain exact so the writer agent can audit and cite without round-tripping to raw unless it chooses to. Never paraphrase a sentence into a Verbatim Quote — if the wording matters, copy it byte-for-byte; if it doesn't matter that much, turn it into a Relevant Claims bullet instead. Paraphrase loss inside a quote block is the main failure mode.
- **Read-only on the research directory.** Never modify the research directory or its files.
- **Be conservative.** It's better to miss a borderline source than to include one that wasn't actually used. The user can always add sources manually. When in doubt about a traceable match, mention it in the report as a borderline case rather than including it.
- **Handle missing files gracefully.** If a layer referenced in `index.yaml` (`uri_source_page`, `uri_highlights`, `uri_full`) doesn't exist on disk, fall back through the read-order list; if all are missing, see the "Missing layers" note in rule 4. It's normal for `uri_highlights` to be `null` for most non-Readwise sources and for `uri_source_page` to be `null` on very early research dirs — that's the expected shape, not an error.
- **The content corpus is everything.** Read ALL provided content files — articles, guidelines, outlines, notes. A source might be referenced in the outline but not the final article, and it should still count.
- **Seed URIs (score 1.0) are not auto-included.** Even though they were user-provided in the research phase, they should only appear in `research.md` if the content actually uses them. The question is "was it used?", not "was it important to the research?"
