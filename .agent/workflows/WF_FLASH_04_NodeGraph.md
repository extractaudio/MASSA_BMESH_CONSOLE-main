---
description: Inspect, create, or modify Node Graphs (Geometry Nodes, Shader, etc)
---

# WF_FLASH_04_NodeGraph

Use this workflow to safely and systematically read, modify, or author Node Graphs in Blender (such as Geometry Nodes or Shader networks) using the robust NodeToPython (NTP) and Geonodes pipeline.

## 0. Prerequisite Context
- Ensure Blender is running with the MCP add-on enabled.
- Identify the target mesh or target object.
- Identify if there is an existing Node Graph you are trying to modify.

## 1. Inspection (If modifying an existing graph)
1. Use `ntp_list_graphs` to find the exact name of the graph you need to modify.
2. Use `ntp_analyze_graph` to understand its dependencies and inputs.
3. Use `ntp_snapshot_graph` to export the graph into a readable Python representation. 

## 2. Authoring / Modification
1. Create or update a Python script utilizing Al1brn's `geonodes` Python syntax.
2. If you are unfamiliar with a specific node mapping, use `geonodes_search` or `geonodes_get_type_doc` to retrieve the Python mapping.
3. **MANDATORY**: Save your constructed Python script to `massa/modules/geonodes_library/<script_name>.py`. Do NOT treat these scripts as ephemeral. They must be committed to the repository for future maintainability.

## 3. Execution & Application
1. Execute your Python script via the `geonodes_execute_script` MCP tool.
2. You can specify a `target_object` (e.g. `target_object="Cube"`) to automatically assign the generated Geometry Node group to that object as a modifier.
3. If you leave `target_object` empty, the tool will automatically create a default Mesh object with a GeometryNodes modifier attached.
4. Verify the newly added modifier or material via `get_object_detail_summary`.

## 4. Massa Integration
If you are generating a Node Group specifically to be used by a BMesh Cartridge (e.g., `Massa_SDF_Fuse`), you may simply use `geonodes_execute_script` without a target object to ensure the NodeGroup datablock is present in the `.blend` file, and then reference the NodeGroup name in the Cartridge logic.
