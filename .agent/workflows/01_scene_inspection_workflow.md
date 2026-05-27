---
description: MCP Inspection
---

# Scene Inspection Workflow

Use when answering: what is in the scene, what is missing, is the file ready, what does a `.blend` contain.

---

## Live Scene Path

1. `get_mcp_server_health` → confirm tools available.
2. `get_objects_summary` → broad picture: collections, types, hierarchy.
3. For any object of interest: `get_object_detail_summary`.
4. For file-level concerns (missing links, library state, save status):
   - `get_blendfile_summary_datablocks` — data-block counts, workspaces, render engine.
   - `get_blendfile_summary_missing_files` — broken external file references.
   - `get_blendfile_summary_of_linked_libraries` — linked library state.
   - `get_blendfile_summary_path_info` — path, save, backup, unsaved state.
   - `get_blendfile_summary_usage_guess` — likely file purpose (animation / modeling / compositing / GeoNodes…).
5. If visual state matters: `get_screenshot_of_window_as_image` or `get_screenshot_of_area_as_image`.
6. To help the user navigate: `jump_to_view3d_object_by_name` · `jump_to_tab_by_name` · `jump_to_tab_by_space_type`.

Only call what the question actually requires. A question about a single object does not require all five `get_blendfile_summary_*` calls.

---

## Background File Path (`.blend` given, no GUI)

Use `_for_cli` variants. Set `BLENDER_PATH` if Blender is not on the system PATH.

1. `get_blendfile_summary_datablocks_for_cli`
2. `get_blendfile_summary_missing_files_for_cli`
3. `get_blendfile_summary_of_linked_libraries_for_cli`
4. `get_blendfile_summary_path_info_for_cli`
5. `get_blendfile_summary_usage_guess_for_cli`
6. `execute_blender_code_for_cli` — only for a narrow query none of the summary tools cover.

> If the file is currently open and dirty in the live Blender session, `synced_blend_for_cli` will save a numbered temporary copy and run against it automatically.

---

## Key Things to Surface

- Hidden or disabled collections that explain "missing" objects.
- Missing external files or broken library links.
- Modifier stacks, shared datablocks, or unusual parenting that affect what a user sees.
- Unsaved changes or backup state relevant to the task.

---

## Avoid

- Do not open with `execute_blender_code` to dump scene state.
- Do not call `get_object_detail_summary` on every object in a large scene.
- Do not assume viewport-hidden means absent — check collection visibility.
- Do not assume object names are stable after generation; use the names returned by inspection tools.

---

## Report Shape

```
Scene: <name> / <render engine> / <active workspace>

Objects of interest:
- <name>: <type, role, notable state>

Issues found:
- <issue and evidence>

Recommended next steps:
- <step>
```

---

## Prompt Frame

```
Inspect this Blender scene using the Massa Blender MCP.

Start with health check and a broad object summary.
Call detail or file-summary tools only for what the question requires.
Do not modify the scene.
Return: scene brief, important objects, risks or missing data, recommended next steps.

Question:
<question>
```
