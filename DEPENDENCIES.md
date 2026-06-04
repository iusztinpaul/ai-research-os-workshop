# Dependencies

What the `/research-*` family needs to run as a standalone Claude Code plugin. With the
changes below, the plugin is self-contained **except for the external CLI binaries** and
an Obsidian vault to point at.

## 1. Python — self-bootstrapping (no setup)

Every helper script carries a **PEP 723 inline metadata** header and is invoked as
`uv run --script <path>`. `uv` reads the header and installs that script's deps into an
isolated, cached env on first run — independent of the current directory, so it works
from any vault without a project `pyproject.toml`.

| Script(s) | Declared deps |
|---|---|
| `research/scripts/build_index_md.py`, `build_index_yaml.py` | `pyyaml` |
| `research/scripts/download_assets.py` | `httpx` |
| `research/scripts/extract_pdf.py` | `pymupdf`, `pymupdf4llm` |
| `research-lint/scripts/lint_*.py` | `pyyaml` (via `_lintlib`) |
| `research-render` generated chart `.py` | `matplotlib` (header emitted by `chart_writer`) |
| `dedup_findings.py`, `github_clone.py`, `github_parse_targets.py` | stdlib only |

Only requirement: [`uv`](https://docs.astral.sh/uv/) on PATH. The root `pyproject.toml`
is kept for local dev convenience only — the skills do not rely on it.

## 2. External CLI binaries (install + auth separately)

Invoked by name from the skills. Their **usage skills are bundled** in this plugin
(`obsidian-cli`, `readwise-cli`, `nlm-skill`, `brightdata-cli`) so the agent knows the
commands, but the binaries are not — install each.

**Safeguards.** `/research` preflights every source CLI with `command -v` (Step 0.5),
warns clearly for each missing one, and degrades per the table below instead of crashing.
The researcher subagent re-guards each CLI; the builder uses `|| true` on CLI pipes and
falls through to alternatives. A missing CLI is never a hard `command not found` failure —
the run continues with the available sources, or stops with an explicit message only if
*no* source is usable.

| CLI | Install | Auth | Fallback if missing |
|---|---|---|---|
| `obsidian` | Obsidian CLI on PATH (see `obsidian-cli`) | vault-scoped | **none — required for vault search** |
| `readwise` | `npm install -g @readwise/cli` | `readwise login-with-token <token>` | source skipped |
| `nlm` | Go CLI (see `nlm-skill`) | `nlm login` (~20 min sessions) | warn + skip NotebookLM |
| `bdata` / `brightdata` | `curl -fsSL https://cli.brightdata.com/install.sh \| bash` or `npm i -g @brightdata/cli` (Node ≥ 20) | `bdata login` | WebFetch (lower fidelity) |
| `marp` | optional viewer | — | view in Obsidian Marp plugin |
| `git` | system git | — | GitHub ingestion unavailable |

## 3. Obsidian vault (consumer-native)

The plugin assumes it runs from an Obsidian vault root:

- `/research` searches the vault via the `obsidian` CLI and treats notes as sources.
- It detects Readwise highlights that sync into the vault (Layer 2 of progressive
  disclosure).
- Research dirs are created at **`working-dir/research-<topic-slug>/`** relative to the
  current directory (the default research root — was a configurable `working_memory_dir`,
  now a fixed `working-dir/`).

No PARA structure, templates, or tagging-rules files are required anymore.

## 4. Changes from the scrabble original

| Change | Why |
|---|---|
| Removed `/research-promote` | Its sole purpose was writing into a specific Second-Brain PARA vault (`6 - Notes/`, `7 - Areas/`, `8 - Projects/`, `Note Template.md`, `My Second Brain Tagging Rules.md`). No standalone target. |
| Removed `*-guideline-create` handoffs | Those skills live in scrabble; a brief is now a plain reusable seed. |
| `<working_memory_dir>` → `working-dir/` | No consumer `CLAUDE.md` to define it; fixed default relative to cwd. |
| "Second Brain" branding → "your knowledge sources / Obsidian vault" | Genericized. |
| `.claude/skills/…` + `<skill_dir>` → `${CLAUDE_PLUGIN_ROOT:-.claude}/skills/…` | Resolves under both install methods: `${CLAUDE_PLUGIN_ROOT}` for a Claude Code plugin install, and the `.claude/skills/` fallback for plain skill installs (`npx skills add`). |
| `uv run python <script>` → `uv run --script <script>` + PEP 723 headers | Self-bootstrapping Python with no project pyproject. |
| Bundled `obsidian-cli`, `readwise-cli`, `nlm-skill`, `brightdata-cli` | Self-contained usage docs for the source CLIs. |
| `resources/` (profiles, datasets, glossary) NOT moved | Never referenced by the research family. |
