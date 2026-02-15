# MASSA_BMESH_CONSOLE

## Dependencies

> pip install fake-bpy-module-latest
> pip install -r MASSA_BMESH_CONSOLE-main/MCP/requirements.txt

## Debugging methods

### Error debugging triggers

- if there is an error that stops the installation or generation of the addon. Attempt to fix the source of the error (Cartridge) and not modify the system files, just the cartridges, unless specified to.

- If an error prohibits the Cartridges geometry script from generating. Attempt to fix (Repair) cartridge to work without loosing parameters and functionality.

- If any of the parameters in the Redo menu create errors when changing. (Use the Redo panel to test the parameters in 'Shape' tab of the console.)

### Telemetry debugging triggers

[important : telemetry scan must deliver an accurate measurement statistics and visualization to the MCP agent!]

- Incorrect mesh generation (failed attempt at geometry scripting). IF the geometry cartridge's desired values do not align with the audit, Attempt to fix the cartridge script until the desired result is measured and correctly generating.

- discover hidden faced (unnecessary), zero face issues (doubling faces). Fix by re-writing the geometry cartridge script to delete the ghost faces, and zero fighting issues between the geometry cartridges. Cleaning the mesh.

### Slot Debugging triggers

[The agent must see the face IDs that the cartridge generates]

- Audit Face Slots. Determines wether the current slots names, placement, and material/physics ID tag (and Shader) are applied correctly

### Edge Slot Debugging triggers

#### IMPORTANT : The MCP server must accurately parse the objects wireframe topology. Visual parsing can be VERY important here to create an intellegent seam finder within the MCP

- Visualize Seam Placement Visually parses the selected object and its topology and places seams according to how the seams (Edge slot) should be placed on the shapes within the cartridges, allowing them to unwrap upon generation.

- Reattempt Seams (if undesired seam results) attempt re-visualized the geometry and try another attempt at the seams until the UV unwrap shows no pinching UV maps.


## cartridge_forge.py
Tools for creating, managing, and versioning geometry cartridges.

create_primitive_cartridge
: Generates a new BMesh cartridge from primitives (Cube, Cylinder, etc.).
write_cartridge_script
: Writes raw Python code to a cartridge file (for Redo/Fixes).
read_cartridge_script
: Reads the content of an existing cartridge.
list_geometry_cartridges
 (NEW): Lists all available geometry cartridge files in the library.
duplicate_cartridge
 (NEW): Creates a copy/backup of a cartridge for versioning.

## inspector.py
Tools for auditing, verifying, and visualizing geometry data.

audit_cartridge_geometry
: Runs the headless "Shadow Audit" (Phase 6) for topology and stability.
inspect_viewport
: Captures a visual snapshot of the mesh (Wireframe, Material, etc.).
stress_test_ui_parameters
: Simulates user parameter changes to verify stability.
run_blender_analysis
: Runs deep analysis tools (Print3D, UV Overlap, Face Area).
visual_regression_diff
: [Phase 1] Overlays wireframes of two versions to visualize changes.
inspect_uv_heatmap
: [Phase 2] Generates a heatmap of UV stretching.
audit_performance
: [Phase 3] Checks execution time and polycount against budgets.
debug_csg_tree
: [Phase 4] Visualizes hidden boolean "cutter" objects.
visualize_edge_slots
 (NEW): [Phase 4] Highlights specific edge slots (seams, bevels) to verify procedural selection logic.
verify_material_logic
 (NEW): [Phase 4] Static analysis to ensure the cartridge correctly retrieves the MAT_TAG layer for material assignment dynamics.

## mechanic.py
Tools for automated code injection and quick fixes.

repair_topology_logic
: Injects mandatory Phase 3 cleanup (remove_doubles, recalc_face_normals).
fix_uv_pinching
: Adjusts UV smart_project margins to prevent pinching.
resolve_context_errors
: Replaces viewport-dependent bpy.ops with data-dependent bmesh.ops.
ensure_imports
: Checks for and adds missing imports (bpy, bmesh, mathutils).
check_scale_safety
: [Phase 5] Detects microscopic parameters that lead to merge errors.
inject_boolean_jitter
: [Phase 5] Injects random offsets to prevent co-planar boolean failures.
inject_standard_slots
: [Phase 5] Injects the mandatory
slots
 dictionary if missing.
