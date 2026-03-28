# MASSA System Mechanics and Safety

> **Ensuring Operator Execution, Resurrection, and UI State**

The MASSA Engine is built to be non-destructive until finalized. These systems handle persistence and debugging.

## 1. Resurrection System
- **How it works**: When `execute()` runs, `_capture_operator_params` saves all current operator settings to the object's custom properties dict `obj["MASSA_PARAMS"]`.
- **How it restores**: When `invoke()` runs, the operator checks if the active object has `MASSA_PARAMS`. If so, it loads them into the operator, effectively "resurrecting" the previous state into the Redo Panel.
- **Rule**: NEVER rename Blender properties in your class without a migration script. Doing so will cause old objects to lose their settings when resurrected.

## 2. Headless Safety & Testing
- **Rule**: The Engine often runs in background threads, unit tests, or CI where `bpy.context.view_layer` or `bpy.ops` might fail.
- **Context Free**: Cartridges must not access `bpy.context` inside `build_shape`.
- **Materials**: Use `mat_utils.ensure_default_library()` to load materials without a viewport context.
- **Pre-Flight Parameter Validation**: Cartridges must ensure relational variables are recalculated and hard-clamped *before* executing any `bmesh.ops` inside `build_shape`. Blender's native UI property bounds do not account for relative parameter collisions (e.g., `radius_inner` becoming larger than `radius_outer`).

## 3. The "Rule of Five" (Modifying the Engine)
If you need to add a new *global* parameter to the engine (e.g., `global_scale`), you must touch 5 places. (Note: This does not apply to Cartridge-specific parameters):
1. **Definition**: `MassaPropertiesMixin` in `massa_properties.py`.
2. **Scene**: Registered in `massa_console.py`.
3. **Operator**: Inherited in `Massa_OT_Base`.
4. **Sync**: Added to `_sync()` method in `massa_base.py`.
5. **UI**: Added to `ui/ui_shared.py`.

## 4. Telemetry, Debugging, & Troubleshooting
The MASSA Debugging system triggers telemetry to parse topology.

### Common Telemetry Flags & Fixes
| Flag | Meaning | Fix |
| :--- | :--- | :--- |
| `CRITICAL_FLAT_Z_AXIS` | Geometry has 0 height. | Check `bmesh.ops.scale` or extrusion logic. |
| `LOOSE_VERTS` | Vertices not connected to edges. | Run `bmesh.ops.delete(bm, geom=loose, context="VERTS")`. |
| `NON_MANIFOLD` | Mesh has holes or T-junctions. | Run `bmesh.ops.recalc_face_normals` or check bridge logic. |
| `MISSING_SLOTS` | Face ID > 9 or < 0. | Ensure `f.material_index` is clamped 0-9. |
| `NO_SEAMS` | "UNWRAP" mode used but no seams found. | Mark edges with `e[edge_slots]=1` (Perimeter) or `3` (Guide). |

### UI and Geometry Triggers
- **Incorrect Mesh Generation**: If geometry is wrong or overlapping, fix the *cartridge script*. Delete ghost faces and resolve fighting.
- **Hidden/Ghost Faces**: Occurs with co-planar faces or zero-area faces. Use `bmesh.ops.remove_doubles`.
- **Slot and Edge Debugging**: Check slot IDs, materials, and placement manually to verify the exact topology output against `get_slot_meta`. Ensure edge slots (Seams/Bevels) are placed accurately to allow correct UV unwrapping without pinching.

## 5. UI Convention
Cartridges should group parameters cleanly in `draw_shape_ui`.
- Group properties with related dimensions, features, and topology settings.
- Avoid using specific, niche language—keep parameter names generalized (e.g., 'Width' instead of 'Wall Width') for consistency.
