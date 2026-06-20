---
description: MCP Mesh and edges
---

# Massa Mesh And Slots Workflow

Use for: mesh cleanup, booleans, modifier application, transforms, Massa edge slots, face material slots, socket empties.

---

## Read Before Any Write

1. `get_mcp_server_health` → confirm tools loaded.
2. `get_objects_summary` if the target object is not certain.
3. `get_object_detail_summary` for the target object.
4. For selection-driven tasks: the user **must be in Edit Mode** with geometry selected in Blender first, then call `get_selected_geometry`.

Confirm before proceeding:
- Target object name and type is `MESH`.
- Blender mode matches what the tool requires (Edit Mode for selection tools; Object Mode for modifier/transform tools).
- Selected element counts (from `get_selected_geometry`) match intent.

---

## Edge Slot Workflow

Requires: user in **Edit Mode**, edges selected.

1. `get_selected_geometry` — confirm edge indices, current `MASSA_EDGE_SLOTS` values, `is_seam`, `is_sharp`, `bevel_weight`.
2. `assign_edge_slot_to_selection` with the target slot (0–5) and action:
   - `SEAM` · `SHARP` · `BOTH` · `CREASE` · `BEVEL` · `IGNORE`
3. `get_selected_geometry` — verify the new slot values and edge marks.

---

## Face Material Slot Workflow

Requires: user in **Edit Mode**, faces selected.

1. `get_selected_geometry` — confirm face indices and current `material_index` values.
2. `assign_face_material_slot_to_selection` with the target slot index (0–9).
3. `get_selected_geometry` — verify changed material indices.

---

## Socket Workflow

Requires: user in **Edit Mode**, one or more faces selected.

1. `get_selected_geometry` — confirm face centres and normals are as intended.
2. `create_socket_at_selected_face` — specify parenting and alignment as needed.
3. `get_objects_summary` or `get_object_detail_summary` — confirm new Empty names, parenting, and position.

---

## Mesh Operation Workflow

Requires: **Object Mode** (target object selected).

| Goal | Tool |
|---|---|
| Boolean cut / union / intersect / slash | `mesh_boolean` |
| Topology cleanup (merge, dissolve, degenerate) | `mesh_clean` |
| Apply modifiers | `apply_modifiers` |
| Apply location / rotation / scale | `apply_transform` |

After each write:
- Call `get_object_detail_summary` on the target.
- Report: HardOps used or native fallback (`used_hardops` field), warnings, new/removed modifiers, vertex/face count change.
- For `apply_modifiers`: flag any shape-key risk before running.

---

## Common Mistakes

- **Skipping `get_selected_geometry`** before assignment — slots write to whatever Blender has selected, not to what the agent assumed.
- **Wrong object** — acting on the active object when the user named a different one. Always name-check.
- **Wrong mode** — selection tools silently fail or corrupt state if Blender is in Object Mode.
- **HardOps is not guaranteed** — always check `used_hardops` in the response; native fallback may not support `SLASH` or `INSET`.
- **Apply with shape keys** — `apply_modifiers` will warn; report the warning to the user before committing.
- **Heavy operations + 300 s timeout** — very large meshes or complex booleans may hit the socket timeout. Warn the user on large inputs.

---

## Prompt Frame

```
Use the Massa Blender MCP mesh workflow.

Inspect health and the target object first.
For selection-driven tasks, call get_selected_geometry before any write.
Use Massa mesh/slot tools — not arbitrary Python.
After writing: verify with a read-back tool and report object names,
affected indices/counts, HardOps fallback status, warnings, and errors.

Task:
<task>
```
