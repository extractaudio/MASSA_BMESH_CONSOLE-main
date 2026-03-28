# MASSA_BMESH_CONSOLE

> **A procedural geometry engine for Blender — generate complex, parametric 3D meshes through a modular "cartridge" system.**

MASSA is a Blender addon that lets you select a **Cartridge** (a parametric geometry generator), generate it into the scene, tune its parameters live in the Redo Panel, and finalize or resurrect it at any time. Every object stays procedural until you explicitly condemn it. The engine handles UVs, materials, physics data, and edge sharpness automatically — cartridges only need to define shape.

---

## Workflow

```
Select Cartridge → Generate → Live Edit (Redo Panel) → Resurrect / Condemn
```

1. **Select**: Pick from 130+ cartridges in the N-Panel (or Ctrl+I pie menu), organized by category: Primitives, Architecture, Industrial, Urban, Assembly, Construction.
2. **Generate**: The engine runs its 6-phase pipeline — shape → edge detection → sharpness → polish → UVs/materials → output.
3. **Live Edit**: The Blender Redo Panel opens immediately with cartridge-specific parameters (size, segments, profiles, etc.) for real-time geometry changes.
4. **Resurrect**: Re-select any previously generated object and press **Resurrect** to re-open its parameters. All settings are stored in `obj["MASSA_PARAMS"]`.
5. **Condemn**: Finalize the object — applies all procedural logic and converts to a static Blender mesh.

---

## Installation

**Prerequisites:** Blender 4.0+ (tested on 5.0). No external Python dependencies needed inside Blender.

```
# For the headless debugging suite only (not required for normal addon use):
pip install fake-bpy-module-latest
pip install -r MCP/requirements.txt
```

1. Zip the `massa/` folder.
2. In Blender: Edit → Preferences → Add-ons → Install → select the zip.
3. Enable "MASSA BMesh Console".
4. Configure `BLENDER_PATH` in `massa/modules/debugging_system/config.py` if using the headless debug suite.

---

## Documentation Map

| File | Purpose |
| :--- | :--- |
| **README.md** *(this file)* | System overview, workflow, debugging reference |
| **new_OVERVIEW-main.md** | Full architecture spec — Brain, Muscle, Engine, Cartridge Blueprint, Protocols |
| **AGENTS.md** | Protocol for AI agents modifying the system |
| **CARTRIDGE_MANDATE.md** | Requirements for writing a "Golden Cartridge" |
| `massa/System_Overview.md` | Developer quick-reference |
| `massa/SETUP.md` | Headless debug suite setup |

---

## Architecture Summary

The system follows a strict **Brain → Muscle → Engine → Content** split:

- **Brain** (`modules/massa_properties.py`): Persistent state. Defines the property DNA shared by Scene and Operator.
- **Muscle** (`operators/massa_base.py`): Execution shell. Handles UI tabs, Resurrection, and state sync.
- **Engine** (`modules/massa_engine.py`): 6-phase generation pipeline — shape, edge roles, sharpness, polish, surface, output.
- **Content** (`modules/cartridges/`): 130+ self-contained parametric geometry generators. Drop a new file in the folder and it auto-registers.

See [new_OVERVIEW-main.md](new_OVERVIEW-main.md) for the full architecture specification.

---

## Debugging Methods

### Error Debugging Triggers

- If there is an error that stops the installation or generation of the addon — attempt to fix the source of the error (the Cartridge), not the system files, unless specifically directed to.
- If an error prohibits the Cartridge's geometry script from generating — attempt to Repair the cartridge without losing its parameters and functionality.
- If any parameters in the Redo menu cause errors when changed — use the Redo Panel **Shape** tab to test parameters.

### Telemetry Debugging Triggers

`[Important: telemetry scan must deliver accurate measurement statistics and visualization to the MCP agent]`

- **Incorrect mesh generation**: If the geometry cartridge's desired values do not align with the audit, fix the cartridge script until the desired result is measured and correctly generating.
- **Hidden/ghost faces**: Zero-area or doubled faces — fix by rewriting the geometry cartridge to delete ghost faces and resolve face-fighting issues.

### Slot Debugging Triggers

`[The agent must see the face IDs that the cartridge generates]`

- **Audit Face Slots**: Determines whether current slot names, placement, and material/physics ID tags (and Shaders) are applied correctly.

### Edge Slot Debugging Triggers

`[IMPORTANT: The MCP server must accurately parse the object's wireframe topology. Visual parsing is critical for intelligent seam finding.]`

- **Visualize Seam Placement**: Parses the selected object's topology and places seams according to how Edge Slots should be placed on the shapes within the cartridges, allowing them to unwrap correctly.
- **Reattempt Seams**: If seam results are undesired, re-visualize the geometry and retry until the UV unwrap shows no pinching.

---

## MCP Tool Reference

### cartridge_forge.py
Tools for creating, managing, and versioning geometry cartridges.

- `create_primitive_cartridge` — Generates a new BMesh cartridge from primitives (Cube, Cylinder, etc.).
- `write_cartridge_script` — Writes raw Python code to a cartridge file (for Redo/Fixes).
- `read_cartridge_script` — Reads the content of an existing cartridge.
- `list_geometry_cartridges` — Lists all available geometry cartridge files in the library.
- `duplicate_cartridge` — Creates a copy/backup of a cartridge for versioning.

### inspector.py
Tools for auditing, verifying, and visualizing geometry data.

- `audit_cartridge_geometry` — Runs the headless "Shadow Audit" (Phase 6) for topology and stability.
- `inspect_viewport` — Captures a visual snapshot of the mesh (Wireframe, Material, etc.).
- `stress_test_ui_parameters` — Simulates user parameter changes to verify stability.
- `run_blender_analysis` — Runs deep analysis tools (Print3D, UV Overlap, Face Area).
- `visual_regression_diff` — [Phase 1] Overlays wireframes of two versions to visualize changes.
- `inspect_uv_heatmap` — [Phase 2] Generates a heatmap of UV stretching.
- `audit_performance` — [Phase 3] Checks execution time and polycount against budgets.
- `debug_csg_tree` — [Phase 4] Visualizes hidden boolean "cutter" objects.
- `visualize_edge_slots` — [Phase 4] Highlights specific edge slots (seams, bevels) to verify procedural selection logic.
- `verify_material_logic` — [Phase 4] Static analysis to ensure the cartridge correctly retrieves the MAT_TAG layer for material assignment dynamics.

### mechanic.py
Tools for automated code injection and quick fixes.

- `repair_topology_logic` — Injects mandatory Phase 3 cleanup (remove_doubles, recalc_face_normals).
- `fix_uv_pinching` — Adjusts UV smart_project margins to prevent pinching.
- `resolve_context_errors` — Replaces viewport-dependent `bpy.ops` with data-dependent `bmesh.ops`.
- `ensure_imports` — Checks for and adds missing imports (bpy, bmesh, mathutils).
- `check_scale_safety` — [Phase 5] Detects microscopic parameters that lead to merge errors.
- `inject_boolean_jitter` — [Phase 5] Injects random offsets to prevent co-planar boolean failures.
- `inject_standard_slots` — [Phase 5] Injects the mandatory `slots` dictionary if missing.
