# Massa Mesh And Slots Workflow

Use this workflow when the task involves mesh cleanup, booleans, modifier application, transforms, selected geometry, Massa edge slots, face material slots, or socket empties.

## Goal

Make mesh edits deliberately. Confirm the exact selected geometry before writing to it, and prefer the Massa-specific tools over custom Python.

## Read Before Write

1. Call `get_mcp_server_health`.
2. Call `get_objects_summary` if the target object is not already certain.
3. Call `get_object_detail_summary` for the target object.
4. If the task is selection-driven, call `get_selected_geometry`.
5. Confirm:
   - target object name
   - object type is `MESH`
   - current mode is correct
   - selected vertex, edge, and face counts
   - active element if the task says "this one"
   - current material indices or edge slot values when relevant

## Edge Slot Workflow

Use for seam tracing, sharp edges, bevel/crease marking, or Massa edge slot assignment.

1. User selects edges in Edit Mode.
2. Call `get_selected_geometry`.
3. Confirm selected edge indices, current edge marks, and current `MASSA_EDGE_SLOTS` values.
4. Call `assign_edge_slot_to_selection`.
5. Use one of these actions:
   - `SEAM`
   - `SHARP`
   - `BOTH`
   - `CREASE`
   - `BEVEL`
   - `IGNORE`
6. Call `get_selected_geometry` again to verify changed slot values and edge marks.

## Face Material Slot Workflow

Use when assigning selected faces to Massa material/UV/physics slots.

1. User selects faces in Edit Mode.
2. Call `get_selected_geometry`.
3. Confirm selected face indices and current `material_index` values.
4. Call `assign_face_material_slot_to_selection`.
5. Call `get_selected_geometry` again to verify changed material indices.

## Socket Workflow

Use when creating mount points from selected faces.

1. User selects one or more faces in Edit Mode.
2. Call `get_selected_geometry`.
3. Confirm face centers and normals.
4. Call `create_socket_at_selected_face`.
5. Call `get_objects_summary` or `get_object_detail_summary` to confirm the new Empty names and parenting.

## Mesh Operation Workflow

For object-level mesh operations:

- Use `mesh_boolean` for `DIFFERENCE`, `UNION`, `INTERSECT`, `SLASH`, `INSET`, or `KNIFE`.
- Use `mesh_clean` for topology cleanup.
- Use `apply_modifiers` for deterministic modifier application.
- Use `apply_transform` before geometry-dependent work when scale or rotation could affect results.

After each write:

1. Read back target object details.
2. Report whether HardOps was used or native fallback was used.
3. List warnings, skipped modifiers, new modifiers, new boolshape objects, or changed counts.

## Prompt Frame

```text
Use the Massa Blender MCP mesh workflow for this task.

Inspect MCP health and the target object first. If the task depends on selected geometry, call get_selected_geometry before changing anything.
Use the Massa mesh or seam/slot tools rather than arbitrary Python.
After writing, verify with a read-back tool and report exact object names, affected indices/counts, warnings, and fallbacks.

Task:
<task>
```

## Common Mistakes

- Assigning slots without confirming selection.
- Acting on the active object when the user named a different object.
- Forgetting Edit Mode is required for selection-driven tools.
- Treating HardOps as guaranteed. It is detected from the running Blender instance.
- Applying modifiers on objects with shape keys without reporting risk.

