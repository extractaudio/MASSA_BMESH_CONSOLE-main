# Agent Operating Principles For Massa Blender MCP

Use this workflow before any task that touches Blender through the Massa MCP server. The goal is to keep agents precise, scene-aware, and biased toward reversible operations.

## Core Rule

Inspect before acting. Prefer specific MCP tools over arbitrary Python. Use `execute_blender_code` only when no existing tool covers the task or when you need a narrow custom read.

## First Moves

1. Call `get_mcp_server_health`.
2. If health is `degraded`, read `tool_registration_errors` before choosing tools.
3. Confirm the work mode:
   - live Blender scene
   - background `.blend` file
   - local documentation/reference lookup
4. If the task touches scene objects, call `get_objects_summary`.
5. If the task targets a named object, call `get_object_detail_summary`.
6. If the task depends on viewport state, call a screenshot or focus/navigation tool.

## Tool Preference Order

1. Purpose-built read tools:
   - `get_objects_summary`
   - `get_object_detail_summary`
   - `get_blendfile_summary_*`
   - `get_selected_geometry`
   - `ntp_list_graphs`
   - `ntp_analyze_graph`
   - `ntp_inspect_node`
2. Purpose-built write tools:
   - `mesh_boolean`
   - `mesh_clean`
   - `apply_modifiers`
   - `apply_transform`
   - `assign_edge_slot_to_selection`
   - `assign_face_material_slot_to_selection`
   - `create_socket_at_selected_face`
   - `geonodes_execute_script`
3. Bundled documentation tools:
   - `search_api_docs`
   - `search_manual_docs`
   - `get_python_api_docs`
   - `geonodes_search`
   - `geonodes_get_demo`
   - `geonodes_get_type_doc`
4. Arbitrary code:
   - `execute_blender_code`
   - `execute_blender_code_for_cli`

## Safety Checklist

Before modifying Blender state:

- Confirm the active object and selected objects are the intended targets.
- Confirm Blender mode if using edit-mode data.
- Prefer non-destructive modifiers where practical.
- If applying destructive changes, state what will change.
- Preserve user selection and mode when writing custom Python, unless changing them is the task.
- Return structured results with names, counts, warnings, and errors.

## Live Blender Versus CLI

Use live Blender socket tools when the user is looking at or editing an open scene.

Use CLI variants when the user gives a `.blend` path and wants file inspection without relying on the open Blender session.

For CLI work, remember that `synced_blend_for_cli` can create a temporary copy when the same file is open and dirty in Blender.

## Prompt Frame

```text
Use the Massa Blender MCP tools to work on this Blender task.

First inspect MCP health and the relevant scene/object state.
Prefer specific MCP tools over arbitrary Python.
Do not modify objects until you have identified the exact targets and likely side effects.
After any write, report the tool used, objects changed, warnings, and the verification read you performed.

Task:
<task>
```

## Completion Criteria

A task is ready to report when:

- The requested action or analysis was performed.
- The final answer names the tools used.
- Any modified object names are listed.
- Any warnings, fallbacks, or skipped work are explicit.
- At least one read-back verification confirms the final state when a write was performed.

