---
name: research-render
description: Generate a multi-form answer (Marp slide deck, matplotlib chart, Obsidian Canvas, or social content brief) from one or more wiki pages in a research directory and file the output back into wiki/renders/. Outputs compound — they appear in index.yaml/index.md and can be re-rendered idempotently. One run can render several forms at once. Use when the user wants to "make a slide deck on X", "chart the comparison of A vs B", "build a canvas of how these concepts connect", "render this as Marp", or "extract a post idea / content brief from my research". Trigger on phrasings like "render", "slide deck", "chart", "canvas", "marp", "brief", "post idea", "extract ideas for social".
user_invocable: true
---

# Research Render

Wiki pages are the substrate. This skill turns them into **multi-form answers** — slide decks, charts, canvases, social briefs — and files those outputs back into `wiki/renders/<format>/<slug>.{md,png,canvas}` so they compound just like any other wiki artifact.

Four formats are supported:
- **marp** — slide deck (Marp markdown)
- **chart** — matplotlib chart (PNG + companion `.py` script for reproducibility)
- **canvas** — Obsidian Canvas (`.canvas` JSON)
- **brief** — social content brief (copy-ready Markdown for a LinkedIn post / Substack note / X thread / Reddit), a reusable idea seed you can paste into a draft

A run can produce **several formats at once** — the user picks one or many up front (Step 1), and each chosen format is rendered independently.

A fifth notional format ("table") was considered but rejected: tables are best embedded inside `comparison` wiki pages, which `/research` already produces via its `comparison_writer`. If you want a table, ask for a comparison.

## Step 1 — Gather inputs and pick the format(s)

You need:
- **format(s)** — one or more of `marp` | `chart` | `canvas` | `brief`. Resolve as follows:
  - If the user's verb pins **exactly one** format unambiguously ("make a slide deck" → `marp`, "chart this" → `chart`, "build a canvas" → `canvas`, "extract a post idea / write a brief" → `brief`), use it without asking.
  - Otherwise, present a single `AskUserQuestion` with **`multiSelect: true`** offering the four formats, so the user can pick one or render several at once. Capture the result as `selected_formats` (a list).
- **source wiki pages** — one or more paths under `<research_dir>/wiki/`. Most renders draw from a single page; canvases, decks, and briefs often draw from multiple (overview + synthesis + a few entity/concept pages).
- **prompt** — the user's framing (e.g., "compare BM25 and hybrid retrieval as a 5-slide deck for an internal tech-talk audience"). Verbatim into each render's frontmatter so future agents can reproduce. For a `brief`, the prompt also carries **the body structure the user wants** (the sections to cover) — the brief writer follows it for the body (see Format details → Brief).
- **platform** *(brief only, optional)* — LinkedIn / Substack note / X thread / Reddit / generic. Infer from the prompt; default to a platform-agnostic brief. Do not interrupt with a separate question — keep the brief lightly platform-aware and leave true platform-final copy to the user.

Locate `research_dir` the same way `/research` (query mode) and `/research-lint` do.

Steps 2–4 run **once per selected format**. When several formats are chosen, run the idempotency checks per format and spawn the format writers **in parallel** (Step 4).

## Step 2 — Compute the slug + output paths

Slug:
- If the user gave a slug (rare): use it.
- If sources are a single page: derive from that page's slug.
- If sources are multiple: derive from the prompt (≤ 6 words, kebab-case).

Output paths by format:

| Format | Path |
|---|---|
| `marp` | `<research_dir>/wiki/renders/marp/<slug>.md` |
| `chart` | `<research_dir>/wiki/renders/charts/<slug>.png` (+ `<slug>.py` next to it) |
| `canvas` | `<research_dir>/wiki/renders/canvases/<slug>.canvas` |
| `brief` | `<research_dir>/wiki/renders/briefs/<slug>.md` |

Create the format directory if it doesn't exist:
```bash
mkdir -p "<research_dir>/wiki/renders/<format>"
```

## Step 3 — Idempotency check

Run this check for each selected format (each has its own output path). If the output already exists:
- Read the existing file's frontmatter (for marp / brief, and the `.canvas.meta.yaml` sidecar for canvas) or companion `.py` (for chart).
- Compare `prompt` and `sources` to the new run.
- If identical, **return noop** without writing.
- If different, ask the user via `AskUserQuestion` whether to overwrite, suffix-with-timestamp, or skip.

## Step 4 — Spawn the format-specific subagent

Each format has a dedicated subagent that knows its output shape. Pass:
- `format`
- `source_pages` — absolute paths
- `research_topic`, `input_summary` (from `index.yaml`)
- `prompt`
- `output_path`
- `research_dir`
- `platform` — *(brief only)* the inferred platform, or `generic`

| Format | Agent file |
|---|---|
| `marp` | `agents/marp_writer.md` |
| `chart` | `agents/chart_writer.md` |
| `canvas` | `agents/canvas_writer.md` |
| `brief` | `agents/brief_writer.md` |

Each subagent reads its source pages (these are short — entity/concept/comparison/source wiki pages, not raw files), produces the render, and returns a JSON summary on stdout. The orchestrator never reads the source pages itself.

When `selected_formats` has more than one entry, spawn all the chosen format writers **in parallel** — one Agent call per format in a single message. They're independent and write to different paths.

For `chart` only: after the writer subagent saves the `.py` script, the orchestrator runs it via `uv run --script` to produce the `.png` (the script carries a PEP 723 header declaring matplotlib, so it self-bootstraps). The script is the source of truth; the PNG is regenerable. If execution fails, the script stays on disk and the failure is surfaced — the user can fix it and re-run.

For `brief` only — **handle the `needs_guidance` return.** The brief writer is capped at ~1000 words. If covering the prompt's sections faithfully would exceed that, it writes nothing and returns `{"action": "needs_guidance", "estimated_words": N, "reason": "...", "options": [...]}`. When you get this, **do not** force the brief — surface it to the user via `AskUserQuestion`, using the writer's `reason` as context and its `options` as the choices (e.g., drop a section, split into two briefs, headline-level only, or raise the cap). Then re-spawn the brief writer with the tightened prompt (or the agreed higher cap). Don't run Steps 5–6 for a brief that returned `needs_guidance` and wasn't re-rendered.

## Step 5 — Update the index

Renders compound. After all selected formats are written, regenerate `index.md` once so the new renders appear in the navigation:

```bash
uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/build_index_md.py --research-dir "<research_dir>"
```

`index.yaml` does not need to be rebuilt — renders aren't sources, they don't have entries in the `sources:` array. The `total_wiki_pages` count is computed live by `build_index_md.py` from the wiki tree.

## Step 6 — Append log entry

One entry per format rendered (share the date when several ran together):

```markdown

## [YYYY-MM-DD] render | <format> | <slug>

- format: <marp|chart|canvas|brief>
- output: wiki/renders/<format>/<slug>.<ext>
- sources: <count> wiki page(s) — <comma-separated relpaths>
- prompt: "<verbatim prompt, truncated to 200 chars>"
```

## Step 7 — Present results

Tell the user:
- The output path (absolute) and how to view it, for **each** format rendered
  - **marp**: open in Obsidian with the Marp plugin, or `marp --watch <file>` from the CLI
  - **chart**: open the PNG in any viewer; the companion `.py` is alongside for editing
  - **canvas**: open in Obsidian (Canvas is a native plugin)
  - **brief**: open the `.md` in Obsidian; copy the body into a post draft, or use it as the idea seed for whatever content workflow you use
- For multi-page renders, the list of source pages used
- The `prompt` (so they can compare against future renders)

## Format details

### Marp

Marp is a markdown-based slide format. The output file has a YAML frontmatter block configuring the deck, then `---` separators between slides:

```yaml
---
marp: true
theme: default
paginate: true
backgroundColor: white
sources: [<wiki page paths>]
prompt: "<verbatim>"
created: <ISO-8601>
---

# Title slide

Content

---

## Second slide

- bullet
- bullet

---

...
```

The Marp Obsidian plugin renders this in-vault. Length: 5–15 slides typical; cap at 25 unless explicitly asked. Each slide ≤ 40 words of body text.

### Chart

Charts are matplotlib outputs. The writer subagent produces a `.py` script that:
- Imports matplotlib (`matplotlib.use("Agg")` for headless, then `import matplotlib.pyplot as plt`)
- Builds the figure
- Saves to a path passed in via `sys.argv[1]` (so the orchestrator can wire output paths cleanly)

Companion files:
```
wiki/renders/charts/<slug>.py    # the script (source of truth, editable)
wiki/renders/charts/<slug>.png   # the rendered chart (regenerable)
```

The script must include a frontmatter-equivalent comment block at the top:
```python
# -- render metadata --
# format: chart
# sources: <comma-separated wiki page paths>
# prompt: "<verbatim>"
# created: <ISO-8601>
# --
```

Run it via:
```bash
uv run --script "<research_dir>/wiki/renders/charts/<slug>.py" "<research_dir>/wiki/renders/charts/<slug>.png"
```

### Canvas

Obsidian Canvas files are JSON with a fixed schema (see Obsidian docs). The writer subagent produces a `.canvas` file with:
- A frontmatter-style metadata block as a separate sidecar (Canvas files don't carry YAML frontmatter natively) — store at `wiki/renders/canvases/<slug>.canvas.meta.yaml` for the same `sources` / `prompt` / `created` info
- Nodes: text nodes (one per source wiki page or one per claim) AND embed nodes (for any image assets the wiki references)
- Edges: directed connections representing relationships (cites, depends-on, contradicts)

Use Canvas for visual argument maps, entity-relationship views, and "how these concepts connect" overviews — anything where spatial layout adds meaning.

### Brief

A brief is a copy-ready social content seed composed from wiki pages — the kind of "executive summary for a post" that a human can paste into a draft. It is **prose, never code**, and it follows a fixed three-part spine. The body is the only flexible part — the user's prompt dictates its sections.

```markdown
---
type: brief
format: brief
platform: <linkedin | substack-note | x-thread | reddit | generic>
sources:
  - <source_page_relpath_1>
  - <source_page_relpath_2>
prompt: "<verbatim prompt>"
created: <ISO-8601 now>
---

# <Working title / hook line>

## Opening — problem → solution
<Problem told as a short story, then the solution and the transformation it brings.
Weaves in the 6 W's: why, what, how, who, where, when.>

## <Body — sections driven by the prompt>
<Whatever the user asked the body to cover.>

## Open questions
1. <highest-signal open question>
2. <second>
3. <third>

---

> Grounding: [[wiki/...]] citations + a one-line `> Synthesis:` note.
```

The spine, in order:

1. **Opening (problem → solution).** Always **start with the problem, told as a story** (a relatable scenario or pain), then continue with **the solution and the transformation** it unlocks (before → after). Across this opening, surface the **6 W's** — *why* (why it matters / why now), *what* (what the thing is), *how* (how it works at a high level), *who* (who it's for / who's involved), *where* (where it fits), *when* (when it applies). Weave them into the narrative; do **not** render them as a labeled checklist.
2. **Body — follow the user's request.** The prompt names the sections to cover; the body follows it beat-for-beat (e.g., "the 3 memory types, their dynamics, the pipeline, the triggers"). This is the flexible middle.
3. **Conclusion — 3 open questions.** Generate exactly **three open questions with the highest signal relative to the brief** — the ones a thoughtful reader (or the author) would most want answered next, and that genuinely extend or stress-test the idea. They double as the post's engagement closer and as research seeds. Generate them from the brief's own content; you may align them with the research dir's `wiki/open-questions.md` if it sharpens them, but never just copy that file wholesale.

Conventions:
- **Citations live in a footer**, not inline — the body stays paste-able. End with a `> Grounding:` line wikilinking the source pages, plus a `> Synthesis:` line (meta-judgment + what new source would extend the idea).
- **Platform-aware, lightly.** Adapt length/voice to `platform` (LinkedIn ≈ 200–400 words, Substack note shorter, X thread = punchier beats, Reddit = plainer); default `generic` ≈ the executive-summary shape. The brief is a seed — leave true platform-final shaping to the user.
- **No diagrams.** A brief is the text companion to a diagram the user already has; don't reproduce one in Mermaid.

## Important notes

- **All output goes into `wiki/renders/`.** Renders are wiki artifacts; they compound. Never write to `working-dir` or anywhere outside the research dir.
- **Source pages, not raw.** Renders read from `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/comparisons/`, `wiki/synthesis.md`, `wiki/overview.md`. They do NOT read `raw/` files. If a render needs a quote that's only in raw, the user should first promote that quote into a source page.
- **Idempotent.** Same prompt + same sources → same render. If you overwrite, log it.
- **Reproducibility for charts.** The `.py` is mandatory. A PNG without script is not allowed — it forecloses future edits.
- **Canvas is best-effort.** Obsidian's Canvas schema evolves; the writer aims for compatibility but visual layout may need touch-up in Obsidian after generation.
- **No new dependencies.** matplotlib is already in `pyproject.toml`. Marp viewing is the user's responsibility (Obsidian plugin or CLI). No additional installs.
- **Briefs are seeds, not final posts.** The brief is the upstream idea artifact; it deliberately stops short of platform-final copy. Don't over-polish it into a finished post.

## Agent reference

- `agents/marp_writer.md` — produces a `.md` Marp deck
- `agents/chart_writer.md` — produces a `.py` matplotlib script (the orchestrator runs it to make the PNG)
- `agents/canvas_writer.md` — produces a `.canvas` JSON file plus a `.meta.yaml` sidecar
- `agents/brief_writer.md` — produces a `.md` social content brief (problem→solution opening with the 6 W's, prompt-driven body, 3 high-signal open questions)
