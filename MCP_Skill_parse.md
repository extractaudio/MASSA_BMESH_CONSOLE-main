# MCP Skill Parse

This document provides a comprehensive audit of all MCP Tools and Skills defined in the Massa Modular Architect system.

## 1. Server Tools (`MCP/server.py`)

These tools are exposed to the MCP Client (AI Agent).

| Tool Name | Description | Status | Risk Assessment | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `session_launch` | Launches a Blender instance (GUI or Headless). | **Active** | **Safe** | Uses `subprocess` via `launcher.py`. |
| `generate_cartridge` | Sends a console command string to Blender. | **Active** | **Safe** | Passes string to `console_command` skill. |
| `generate_scene` | Generates a full scene from a JSON layout. | **Active** | **Caution** | Heavy loop if layout is large. Implicitly runs audit on every object created. |
| `iterate_parameters` | Updates properties of the active object and triggers "Resurrect". | **Active** | **Safe** | Dependent on active object selection. |
| `scan_telemetry` | Returns mesh stats (ghost faces, manifold status). | **Active** | **Unoptimized** | Calculates face areas in Python (slow for high-poly). |
| `scan_slots` | Returns material slot distribution. | **Active** | **Safe** | Simple iteration over polygons. |
| `scan_geometry_data` | Returns bounds, dimensions, location. | **Active** | **Safe** | Fast access to object properties. |
| `inspect_scene` | Lists objects in the scene with pagination. | **Active** | **Safe** | Limit/Offset logic prevents overload. |
| `inspect_object` | Detailed object info (modifiers, constraints). | **Active** | **Safe** | Read-only data access. |
| `scan_visuals` | Captures viewport screenshot (Base64). | **Active** | **Safe** | Dependent on OpenGL context availability. |
| `restore_selection` | Reselects the last operated object. | **Active** | **Safe** | Fixes "No Active Object" context errors. |
| `run_script` | Executes raw Python code in Blender. | **Active** | **Danger** | **High Risk.** Allows arbitrary code execution via `exec()`. Essential for repair but dangerous if unchecked. |
| `massa_generator` | Automated UI test for cartridges. | **Active** | **Safe** | Wraps operator execution. |
| `forge_bmesh` | Creates mesh from raw BMesh script. | **Active** | **Danger** | **High Risk.** Executes arbitrary code via `exec()`. |
| `file_system_edit` | Read/Write access to cartridge files. | **Active** | **Danger** | **High Risk.** Direct file system modification. |
| `list_cartridges` | Lists .py files in `modules/cartridges`. | **Active** | **Safe** | Read-only directory listing. |
| `read_library_source` | Reads content of a cartridge file. | **Active** | **Safe** | Read-only file access. |
| `list_materials` | Lists all materials in the blend file. | **Active** | **Safe** | Simple list comprehension. |
| `audit_cartridge` | Runs cartridge auditor (Background or Direct). | **Active** | **Caution** | Background mode spawns new process (heavy). Direct mode modifies scene if not careful. |
| `audit_console` | Runs console architecture auditor. | **Active** | **Caution** | Background mode spawns new process. |
| `execute_contextual_op` | Runs an operator with context override. | **Active** | **Safe** | Essential for Blender 5.0+ strict context. |
| `edit_node_graph` | Edits node trees (Geometry/Shader). | **Active** | **Safe** | Basic node operations. |
| `inspect_evaluated_data`| Gets stats from Depsgraph (Evaluated mesh). | **Active** | **Caution** | Evaluating depsgraph can be slow for complex scenes. |
| `manage_action_slots` | Manages Animation Layers (Action Slots). | **Active** | **Caution** | Relies on speculative Blender 5.0 API (`action_slots`). May fail on older builds. |
| `query_asset_browser` | Lists local assets and libraries. | **Active** | **Unoptimized** | Does not search actual Asset Browser index, only local data blocks. |
| `configure_eevee_next` | Sets EEVEE render settings. | **Active** | **Safe** | Simple property setting. |
| `organize_outliner` | Moves objects into collections. | **Active** | **Safe** | Standard collection management. |
| `verify_material_logic` | Static analysis of cartridge code. | **Active** | **Safe** | String parsing of file content. |

---

## 2. Bridge Skills (`MCP/mcp_bridge.py`)

These skills are executed inside the Blender process (Main Thread).

| Skill ID | Description | Status | Risk Assessment | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `execute_contextual_op` | Finds window/area and runs op with override. | **Active** | **Safe** | Robust context finding logic. |
| `edit_node_graph` | Modifies node trees. | **Active** | **Safe** | Basic error handling for missing nodes. |
| `inspect_evaluated_data` | Accesses `evaluated_depsgraph_get()`. | **Active** | **Caution** | Heavy computation for dense meshes/geometry nodes. |
| `manage_action_slots` | API for Action Slots. | **Active** | **Caution** | Experimental API usage. |
| `query_asset_browser` | Iterates objects/materials for asset tags. | **Active** | **Unoptimized** | Only finds assets marked in current file + linked libraries. Not a full search. |
| `configure_eevee_next` | Sets scene properties. | **Active** | **Safe** | |
| `audit_cartridge_direct` | Calls `runner.execute_audit`. | **Active** | **Caution** | Runs full cartridge execution logic in main thread. |
| `audit_console_direct` | Calls `runner_console`. | **Active** | **Safe** | |
| `console_command` | Calls `bpy.ops.massa.console_parse`. | **Active** | **Safe** | Dependent on Massa Console addon registration. |
| `set_redo_prop` | Sets attributes on active object. | **Active** | **Safe** | Uses `setattr` blindly, but wrapped in try/except. |
| `get_telemetry` | Calls `analyze_mesh()`. | **Active** | **Unoptimized** | `analyze_mesh` builds a new BMesh and checks all faces. Slow on >100k poly. |
| `get_slots` | Calls `analyze_slots()`. | **Active** | **Safe** | |
| `get_bounds` | Calls `analyze_bounds()`. | **Active** | **Safe** | |
| `get_vision` | Calls `capture_viewport()`. | **Active** | **Caution** | Requires OpenGL context. May return black/empty if window is minimized or background. |
| `get_scene_info` | Iterates `bpy.data.objects`. | **Active** | **Safe** | Pagination limits load. |
| `get_object_info` | Gathers deep object stats. | **Active** | **Safe** | |
| `execute_code` | `exec()` with `bpy` and `bmesh`. | **Active** | **Danger** | Arbitrary code execution. |
| `create_bmesh` | `exec()` with BMesh environment. | **Active** | **Danger** | Arbitrary code execution. |
| `test_generator_ui` | Finds operator by ID and executes it. | **Active** | **Safe** | Uses standard operator execution path. |
| `restore_last_selection` | Selects object by name. | **Active** | **Safe** | |
| `get_materials` | Lists material names. | **Active** | **Safe** | |
| `organize_outliner` | Moves objects to collections. | **Active** | **Safe** | |
| `inspect_cartridge_live` | Creates, captures, and optionally deletes. | **Active** | **Caution** | Viewport capture can be flaky. Logic duplicated from `test_generator_ui`. |
| `create_scene` | Iterates layout list and creates objects. | **Active** | **Caution** | "Audit" step runs `analyze_mesh` for every object created. **Potential Performance Bottleneck.** |

## Summary of Risks

1.  **Arbitrary Code Execution (`run_script`, `forge_bmesh`):** These tools use `exec()`. While necessary for an "Engineer Agent" to fix code, they bypass all safety checks.
2.  **Performance Bottlenecks:**
    *   `create_scene`: If `audit=True` (default), it runs a full BMesh analysis for *every* object created. For a scene with 100 objects, this is 100 BMesh creations/destructions.
    *   `get_telemetry`: Runs `analyze_mesh` which is unoptimized for high-poly meshes (calculates face area for every face in Python).
3.  **Experimental APIs:** `manage_action_slots` relies on Blender 5.0 features that may change or not exist in all builds.
4.  **Context Sensitivity:** `get_vision` and `execute_contextual_op` rely heavily on finding the correct window/area context. This is notoriously difficult in Blender and may fail if the window is minimized or the layout is non-standard.
