# Node Graph And geonodes Workflow

Use this workflow for material nodes, Geometry Nodes, compositor graphs, shader groups, world/light graphs, NodeToPython snapshots, and vendored geonodes script generation.

## Goal

Understand the graph before editing or generating code. Use NTP inspection for existing node trees and geonodes reference tools for authoring new procedural node setups.

## Existing Node Graph Inspection

1. Call `get_mcp_server_health`.
2. Call `ntp_list_graphs`.
3. Pick the graph by `graph_type` and `graph_name`.
4. Call `ntp_analyze_graph`.
5. Inspect important nodes with `ntp_inspect_node`.
6. If the user wants code, call `ntp_snapshot_graph`.

Supported graph types:

```text
MATERIAL
GEOMETRY
SHADER
COMPOSITOR
WORLD
LIGHT
LINESTYLE
```

## What To Look For

- Total node and link counts.
- Whether an output node exists.
- Orphan nodes and dead-end nodes.
- Broken links.
- Linked node groups and dependency chains.
- Node socket defaults and linked endpoints.
- RNA properties that clarify node behavior.

## geonodes Authoring Workflow

Use this path when creating or adapting procedural Geometry Nodes scripts with the vendored `geonodes` package.

1. Call `geonodes_search` with the main concept.
2. Call `geonodes_list_demos` if you need examples by tag.
3. Call `geonodes_get_demo` for the closest matching demo.
4. Call `geonodes_list_types` when unsure which public class to use.
5. Call `geonodes_get_type_doc` for specific types such as `Float`, `Mesh`, `Vector`, or `GeoNodes`.
6. Draft a small script.
7. Call `geonodes_execute_script`.
8. Read the response:
   - `created_node_groups`
   - `created_materials`
   - `stdout`
   - `traceback`
9. If a node graph was created, call `ntp_list_graphs` and `ntp_analyze_graph` to verify it exists and has outputs.

## NodeToPython Snapshot Workflow

Use `ntp_snapshot_graph` when the user wants a reproducible Python representation of an existing node graph.

1. Identify the graph with `ntp_list_graphs`.
2. Confirm structure with `ntp_analyze_graph`.
3. Inspect suspicious or central nodes with `ntp_inspect_node`.
4. Call `ntp_snapshot_graph`.
5. Report line count, byte size, whether NodeToPython had to be registered, and whether imports/defaults were included.

## Prompt Frame

```text
Use the Massa Blender MCP node graph workflow.

For existing graphs, list graphs, analyze the chosen graph, inspect important nodes, and snapshot only when useful.
For new geonodes work, search examples/docs first, read a matching demo/type doc, execute a small script, then verify the created graph.
Avoid arbitrary bpy code unless the NTP/geonodes tools cannot answer the question.

Task:
<task>
```

## Common Mistakes

- Snapshotting before analyzing the graph.
- Editing a graph without checking whether it has an output.
- Ignoring orphan/dead-end nodes that explain a visual failure.
- Assuming a geonodes type API without reading its bundled doc.
- Running a large generated script before testing the smallest useful version.

