# Dependencies

What the `/research-*` family needs to run as a standalone Claude Code plugin. With the
changes below, the plugin is self-contained **except for external CLI binaries and their
auth,** plus an Obsidian vault to point at.

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
| `research/scripts/youtube_extract_transcript.py` | `youtube-transcript-api` |
| `research-lint/scripts/lint_*.py` | `pyyaml` (via `_lintlib`) |
| `research-render` generated chart `.py` | `matplotlib` (header emitted by `chart_writer`) |
| `dedup_findings.py`, `github_clone.py`, `github_parse_targets.py` | stdlib only |

Only requirement: [`uv`](https://docs.astral.sh/uv/) on PATH. The root `pyproject.toml`
is kept for local dev convenience only — the skills do not rely on it.

## 2. External CLIs and auth (install + authenticate separately where needed)

Invoked by name from the skills. Their **usage skills are bundled** in this plugin
(`obsidian-cli`, `readwise-cli`, `nlm-skill`) so the agent knows the
commands, but the binaries are not — install each. Generic web pages need no CLI: they are
fetched with preinstalled `curl` + a `python3` stdlib HTML stripper (no install, no auth),
with `WebFetch` as the fallback for JS-rendered or bot-walled pages.

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
| `marp` | optional viewer | — | view in Obsidian Marp plugin |
| `git` | system git | — | GitHub ingestion unavailable |
| YouTube captions | none | none | YouTube video ingestion skipped when captions/transcripts are unavailable |

## 3. Obsidian vault (consumer-native)

The plugin assumes it runs from an Obsidian vault root:

- `/research` searches the vault via the `obsidian` CLI and treats notes as sources.
- It detects Readwise highlights that sync into the vault (Layer 2 of progressive
  disclosure).
- Research dirs are created at **`working-dir/research-<topic-slug>/`** relative to the
  current directory (the default research root).

No PARA structure, templates, or tagging-rules files are required.
