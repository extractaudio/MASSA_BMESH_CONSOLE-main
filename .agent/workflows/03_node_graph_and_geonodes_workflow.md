---
description: MCP node graph
---

# Node Graph And geonodes Workflow

Use for: material nodes, Geometry Nodes, compositor, shader groups, world/light graphs, NodeToPython snapshots, vendored geonodes script generation.

---

## Path A — Inspect An Existing Node Graph

Use when the graph already exists in Blender.

1. `get_mcp_server_health`.
2. `ntp_list_graphs` → pick the graph by `graph_type` and `graph_name`.
   - Types: `MATERIAL` · `GEOMETRY` · `SHADER` · `COMPOSITOR` · `WORLD` · `LIGHT` · `LINESTYLE`
3. `ntp_analyze_graph` → check for: output node present, orphan/dead-end nodes, broken links, linked group dependencies, complexity score.
4. `ntp_inspect_node` for any node that looks suspicious or is central to the task.
5. `ntp_snapshot_graph` only if the user explicitly wants reproducible Python code.
   - Report: line count, byte size, whether NodeToPython had to be registered.

**Do not snapshot before analyzing.** Analysis often reveals the problem before code export is needed.

---

## Path B — Author A New geonodes Script

Use when creating a new Geometry Nodes setup with the vendored `geonodes` package.

1. `geonodes_search` — search the main concept to find relevant demos and docs.
2. `geonodes_list_demos` — browse by tag when `geonodes_search` returns too broad a result.
3. `geonodes_get_demo` — read the closest matching demo in full.
4. `geonodes_list_types` — check available public classes if the right type is unclear.
5. `geonodes_get_type_doc` — read the reference for specific types (`Float`, `Mesh`, `Vector`, etc.). Do not assume API without reading the doc.
6. Draft the smallest script that proves the core idea.
7. `geonodes_execute_script`.
8. Read the response:
   - `created_node_groups` / `created_materials` — confirm something was created.
   - `stdout` — check for warnings from the script.
   - `traceback` — if present: **read the full traceback before modifying the script**. The error type and line number are always there; do not guess.
9. If a node group was created: `ntp_list_graphs` + `ntp_analyze_graph` to confirm it exists and has an output node.

---

## Common Mistakes

- Snapshotting a graph before analyzing it — analysis is faster and usually sufficient.
- Editing a graph without checking whether an output node exists first.
- Ignoring orphan or dead-end nodes that explain a visual failure.
- Assuming a `geonodes` type API without reading its bundled markdown doc.
- Running a large or complex script on first attempt — start minimal, expand only after the core works.
- Treating a `traceback` in `geonodes_execute_script` output as a partial success — any traceback means the script failed.

---

## Prompt Frame

```
Use the Massa Blender MCP node graph workflow.

For existing graphs: list → analyze → inspect suspicious nodes → snapshot only if requested.
For new geonodes work: search → read demo → read type doc → execute minimal script → verify created graph.
Read traceback fully before modifying a failing script.
Avoid arbitrary bpy code unless NTP and geonodes tools cannot answer.

Task:
<task>
```
