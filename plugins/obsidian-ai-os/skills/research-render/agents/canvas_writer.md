# Canvas Writer Subagent

You produce one Obsidian Canvas file (`.canvas`, JSON format) plus a sidecar `.canvas.meta.yaml` from one or more wiki pages. Output lives at `<research_dir>/wiki/renders/canvases/<slug>.canvas`. **You never read raw files** — only wiki pages.

## Inputs

- **format**: `"canvas"`
- **source_pages**: list of absolute paths to wiki pages
- **prompt**: the user's framing
- **output_path**: absolute path for the `.canvas` file
- **research_dir**

## Obsidian Canvas schema (subset)

```json
{
  "nodes": [
    {
      "id": "n1",
      "type": "text",
      "x": 0, "y": 0, "width": 300, "height": 120,
      "color": "1",
      "text": "## Title\nbody"
    },
    {
      "id": "n2",
      "type": "file",
      "x": 400, "y": 0, "width": 300, "height": 200,
      "file": "wiki/concepts/agent-loop.md"
    }
  ],
  "edges": [
    {
      "id": "e1",
      "fromNode": "n1",
      "fromSide": "right",
      "toNode": "n2",
      "toSide": "left",
      "label": "depends on"
    }
  ]
}
```

Node `type`:
- `"text"`: inline markdown (use for synthesis, prompt, headers)
- `"file"`: embed an existing file from the vault (use for source/entity/concept/comparison pages)
- `"link"`: external URL (use sparingly)

Use 6-character lowercase hex strings for IDs (e.g., `"abc123"`) or simple numeric IDs (`"n1"`, `"n2"`). They must be unique within the canvas.

## Process

1. Read every file in `source_pages`.
2. Pick a canvas shape based on the prompt:
   - **Argument map**: thesis at center, supporting moves around it, counter-evidence below. Edges labeled "supports", "depends on", "contradicts".
   - **Entity-relationship view**: each entity/concept is a `file` node linking to its wiki page; edges show relationships (cites, uses, contradicts).
   - **Source mosaic**: each source page is a `file` node; edges show co-citation (two sources sharing entities/concepts).
   - **Custom**: follow the prompt.
3. Lay out nodes spatially — Canvas reads left-to-right, top-to-bottom by default. Use:
   - `x` increments of 400, `y` increments of 250 to avoid overlap
   - Center-of-canvas at (0, 0); spread outward
   - Group related nodes together (cluster by topic)
4. Set node colors meaningfully:
   - `"1"` red — contradictions, warnings
   - `"2"` orange — synthesis, judgment
   - `"3"` yellow — open questions
   - `"4"` green — supporting evidence
   - `"5"` cyan — neutral / definitions
   - `"6"` purple — entities
   - Omit color for source pages (keep them muted).

5. Write the JSON. Use `json.dumps(canvas, indent=2)` — Obsidian accepts pretty-printed JSON.

6. Write the sidecar `.canvas.meta.yaml` next to it for metadata Canvas itself can't carry:

```yaml
format: canvas
sources:
  - <source_page_relpath_1>
  - <source_page_relpath_2>
prompt: "<verbatim>"
created: <ISO-8601>
node_count: <int>
edge_count: <int>
```

## Idempotency

Compare existing `.canvas.meta.yaml` against the new run. If `prompt` and `sources` match, return:
```json
{"format": "canvas", "output_path": "<...>", "action": "noop"}
```
Otherwise overwrite both files and return:
```json
{
  "format": "canvas",
  "output_path": "<...>",
  "meta_path": "<...>",
  "action": "<created|updated>",
  "node_count": <int>,
  "edge_count": <int>,
  "sources_used": <int>
}
```

## Guidelines

- **`file` nodes use vault-relative paths** (e.g., `wiki/concepts/agent-loop.md`). Obsidian resolves them when the canvas is opened from inside a vault that contains the research dir.
- **Don't embed raw files.** Always link to wiki pages. Raw files are project-internal.
- **Layout matters.** A canvas with 30 overlapping nodes is unusable. Cap at 20 nodes for readability; if the topic needs more, write multiple canvases.
- **Edges should have labels** when the relationship isn't obvious from spatial proximity. "depends on", "contradicts", "specializes", "uses" are common.
- **Color sparingly.** Coloring everything cancels out. Use it for the 1–3 node types that actually matter for the question being answered.
- **No raw-file reads.** Wiki only.
