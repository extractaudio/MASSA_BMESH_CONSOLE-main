# Scene Inspection Workflow

Use this workflow when the user asks what is in a Blender scene, why something is missing, whether a file is ready, or what data a `.blend` contains.

## Goal

Build a reliable picture of the scene without dumping excessive data. Start broad, then inspect only the objects, datablocks, or UI areas that matter.

## Live Scene Sequence

1. Call `get_mcp_server_health`.
2. Call `get_objects_summary`.
3. If the scene seems file-oriented, call:
   - `get_blendfile_summary_datablocks`
   - `get_blendfile_summary_missing_files`
   - `get_blendfile_summary_of_linked_libraries`
   - `get_blendfile_summary_path_info`
   - `get_blendfile_summary_usage_guess`
4. For any object of interest, call `get_object_detail_summary`.
5. If visual state matters, call one of:
   - `get_screenshot_of_window_as_image`
   - `get_screenshot_of_area_as_image`
   - `get_screenshot_of_window_as_json`
6. If the user needs to see or focus an object, use:
   - `jump_to_view3d_object_by_name`
   - `jump_to_view3d_object_data_by_name`
   - `jump_to_tab_by_name`
   - `jump_to_tab_by_space_type`

## Background File Sequence

Use this path when the user gives a `.blend` file and the task can be done headlessly.

1. Use `get_blendfile_summary_datablocks_for_cli`.
2. Use `get_blendfile_summary_missing_files_for_cli`.
3. Use `get_blendfile_summary_of_linked_libraries_for_cli`.
4. Use `get_blendfile_summary_path_info_for_cli`.
5. Use `get_blendfile_summary_usage_guess_for_cli`.
6. Use `execute_blender_code_for_cli` only for a narrow query not covered by the summary tools.

## What To Look For

- Scene name, render engine, active workspace, and workspace list.
- Collection hierarchy and hidden or disabled collections.
- Object types, modifiers, parenting, materials, and shared datablocks.
- Missing external files, linked libraries, backups, and unsaved state.
- Whether the file appears oriented toward modeling, animation, rendering, compositing, geometry nodes, UV work, or video editing.

## Avoid

- Do not start with arbitrary `execute_blender_code`.
- Do not dump every object detail in a large scene.
- Do not assume viewport invisibility means an object is absent.
- Do not assume object names remain stable after creation; inspect returned names.

## Prompt Frame

```text
Inspect this Blender scene using the Massa Blender MCP.

Start with MCP health and a broad object summary. Then inspect only the relevant objects, missing files, libraries, path info, screenshots, or usage guesses needed to answer.
Do not modify the scene.
Return a concise scene brief with important objects, likely issues, and recommended next actions.

Question:
<question>
```

## Report Shape

```text
Scene:
- <scene name / render engine / workspace>

Important objects:
- <object>: <type, role, notable state>

Risks or missing data:
- <issue>

Recommended next steps:
- <step>
```

