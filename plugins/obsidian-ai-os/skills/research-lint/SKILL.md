---
name: research-lint
description: Health-check a research directory produced by /research. Runs seven checks — orphan sources, missing entity/concept hubs, missing comparison candidates, broken wikilinks, stale claims, contradictions, and open-question synthesis. Outputs a report; edits where safe (broken-link flags, open-question append, contradiction surfacing); flags-only otherwise. Always user-triggered, never automated. Trigger when the user says things like "lint my research", "health check my research", "check the wiki", "audit my research dir", "what's wrong with my wiki", "find orphans / contradictions / stale claims".
user_invocable: true
---

# Research Lint

You audit a research directory and surface health issues. **Lint is user-triggered, never automated.** Each pass is read-mostly: you write only to `wiki/open-questions.md`, `wiki/contradictions.md`, `index.yaml`, `index.md`, and `log.md` — never to source pages, entity pages, concept pages, or raw files.

This skill answers: "what's broken or thin in this wiki, and what should I research next?"

## Step 1 — Locate the research dir

Same logic as `/research` (query mode):
1. If the user provides a path, use it.
2. Otherwise scan `working-dir` for `research-*/` and ask if multiple exist.
3. If only one exists, use it.

Verify it's a v4 layout — `<research_dir>/raw/` and `<research_dir>/wiki/` must exist directly under the research dir (no `memory/` wrapper). If it's older (v1 with raw at root, or v3 with `memory/` wrapper), instruct the user to run `migrate_layout.py` first and stop.

## Step 2 — Pick the checks

Default: run all seven checks. The user can scope down via natural language ("just check broken links", "skip the LLM stuff"). Map their phrasing to:

| Check | Cost | Edits the wiki? |
|---|---|---|
| orphans | cheap (script) | flags only |
| missing-hubs | cheap (script) | flags only |
| missing-comparisons | cheap (script) | flags only |
| broken-links | cheap (script) | flags only |
| stale-claims | LLM | flags only |
| contradictions | LLM (slow) | appends to `wiki/contradictions.md` |
| open-questions | LLM | appends to `wiki/open-questions.md` |

The four cheap checks always run. The three LLM checks run by default but can be skipped per user request.

## Step 3 — Run the cheap checks (in parallel via bash)

Run all four mechanical scripts in parallel and collect their JSON outputs. They all read-only; safe to run any time.

```bash
SKILL_DIR="${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research-lint"
RD="<research_dir>"

uv run --script "$SKILL_DIR/scripts/lint_orphans.py" --research-dir "$RD" > "$RD/lint-orphans.json" &
uv run --script "$SKILL_DIR/scripts/lint_broken_links.py" --research-dir "$RD" > "$RD/lint-broken-links.json" &
uv run --script "$SKILL_DIR/scripts/lint_missing_hubs.py" --research-dir "$RD" > "$RD/lint-missing-hubs.json" &
uv run --script "$SKILL_DIR/scripts/lint_missing_comparisons.py" --research-dir "$RD" > "$RD/lint-missing-comparisons.json" &
wait
```

Each script prints a single-line JSON `{check: "...", findings: [...]}` describing what it found. Aggregate counts only — do not load full findings into your context window unless the user explicitly asks for the full list.

## Step 4 — Run the LLM checks (parallel subagents)

Spawn three `lint_judge` subagents in parallel using a single message with multiple Agent calls. Each gets a different `check_type`:

1. **contradictions** — reads every `wiki/sources/*.md` "Tensions" section + entity/concept "Tensions" sections; writes new contradictions to `wiki/contradictions.md`.
2. **stale-claims** — for each entity/concept page with `source_count >= 3`, checks whether the newest source contradicts older claims; flags candidates without writing.
3. **open-questions** — synthesizes gaps from wiki state into `wiki/open-questions.md`.

Pass each subagent:
- `check_type`
- `research_dir`
- `research_topic`, `input_summary` (read from `index.yaml`)
- `output_path` (only for contradictions and open-questions; `null` for stale-claims since it's flag-only)

Each returns a JSON summary on stdout: `{check_type, findings_count, written: true|false, flags: [...]}`. The orchestrator aggregates flags into the final report.

## Step 5 — Apply the safe edits

Some checks generate *additive* edits the lint pass should apply automatically. Others generate *flags* the user must act on.

| Check | Auto-apply | Notes |
|---|---|---|
| orphans | NO | flag only — user decides whether to delete the source or add a wiki citation |
| missing-hubs | NO | flag — user can /research it or accept the absence |
| missing-comparisons | NO | flag — user can `/research-render comparison <a> <b>` if they want |
| broken-links | NO | flag — wiki page may be missing because not yet promoted, or because the link is genuinely wrong |
| stale-claims | NO | flag — needs human judgment |
| contradictions | YES | append to `wiki/contradictions.md` (the page is meant to grow) |
| open-questions | YES | append new questions to `wiki/open-questions.md` |

After any auto-apply edits land, regenerate the index:

```bash
# If contradictions.md or open-questions.md changed, count_wiki_pages may have moved.
PRIOR_CREATED=$(grep '^created:' "<research_dir>/index.yaml" | awk -F"'" '{print $2}')
# Re-run build_index_yaml.py is unnecessary because no source data changed,
# but build_index_md.py must regenerate to reflect new pages in the index.
uv run --script ${CLAUDE_PLUGIN_ROOT:-.claude}/skills/research/scripts/build_index_md.py --research-dir "<research_dir>"
```

## Step 6 — Append to log.md

```bash
DATE=$(date -u +%Y-%m-%d)
cat >> "<research_dir>/log.md" <<EOF

## [$DATE] lint | <topic>

- orphans: <count>
- missing-hubs: <count>
- missing-comparisons: <count>
- broken-links: <count>
- stale-claims: <count flagged>
- contradictions: <count appended to contradictions.md>
- open-questions: <count appended to open-questions.md>
EOF
```

## Step 7 — Present the report

Structure the report so the user can scan it and act:

```
## Lint report — <topic>
Research dir: <path>
Run at: <ISO-8601>

### Summary
- Total sources: <N>, total wiki pages: <M>
- Issues found: <orphans> orphans · <missing_hubs> missing hubs · <broken> broken links · <stale> stale claims · <contradictions> contradictions · <open_questions> open questions

### Action items (need your decision)
1. Orphans (<N>) — sources never cited by the wiki:
   - <title> (origin: <origin>, score: 0.XX)
   - ... (capped at 5 shown; full list in <research_dir>/lint-orphans.json)
2. Missing hubs (<N>) — concepts/entities mentioned ≥3 times with no page:
   - "<concept>" appears in <X> source pages
   - ...
3. Broken links (<N>):
   - [[wiki/concepts/foo]] referenced from [[wiki/sources/abc]] but the file doesn't exist
   - ...
4. Stale claims (<N>): see <research_dir>/lint-stale-claims.json

### Auto-applied edits
- <K> contradictions appended to [[wiki/contradictions.md]]
- <L> open questions appended to [[wiki/open-questions.md]]

### Next steps
- For each orphan: decide delete vs. add wiki citation
- For missing hubs: run /research with the concept name, OR accept the absence
- For missing comparisons: run /research-render comparison <a> <b>
- For broken links: edit the source file, OR remove the reference
```

Cap the bulleted lists at 5 items per category. Point users at the JSON files in `<research_dir>/` for the full lists. After they review, the JSONs can be deleted (`rm <research_dir>/lint-*.json`) — they are scratch.

## Important notes

- **You are read-mostly.** The only files you write to are: `wiki/contradictions.md`, `wiki/open-questions.md`, `index.md` (regenerated), and `log.md` (append). Never touch source pages, entity pages, concept pages, or raw files.
- **Subagents do the LLM work.** Do not load source pages or wiki pages into your own context — spawn subagents (or use scripts) for everything content-heavy.
- **Idempotent.** Re-running lint should produce no new edits if the wiki hasn't changed (modulo `last_updated` and the log entry). Contradictions and open-questions append only when genuinely new.
- **Cheap before expensive.** Always run the 4 mechanical scripts first; their findings can sharpen the LLM checks (e.g., the contradictions subagent only needs to read pages with `source_count >= 2`).

## Agent reference

- `agents/lint_judge.md` — Lint Judge Subagent. Generic agent dispatched for `contradictions`, `stale-claims`, and `open-questions` checks via a `check_type` input.

## Script reference

- `scripts/lint_orphans.py` — Finds sources in `index.yaml` whose `original_path` and `uri_full` are never wikilinked from any wiki page.
- `scripts/lint_broken_links.py` — Scans every wiki page for `[[wikilinks]]` and flags any that don't resolve to an existing file.
- `scripts/lint_missing_hubs.py` — Counts entity/concept name mentions across source pages; flags those with ≥3 mentions and no `wiki/entities/<slug>.md` or `wiki/concepts/<slug>.md`.
- `scripts/lint_missing_comparisons.py` — Pairs entity/concept pages by mutual `[[wikilink]]` references; flags pairs with ≥2 mutual citations and no comparison page.
