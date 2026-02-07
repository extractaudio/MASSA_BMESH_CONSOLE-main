---
description: DEBUG & REPAIR PROTOCOLS
---

# DEBUG & REPAIR PROTOCOLS

## 1. Ghost Faces (Critical)

* **Trigger:** `telemetry['ghost_faces_count'] > 0`
* **Diagnosis:** Vertices are overlapping or extrusion distance is 0.
* **Action:**
    1. Read Script. Find `bmesh.ops.create_face` or `extrude`.
    2. **FIX:** Inject `bmesh.ops.remove_doubles(bm, verts=..., dist=0.001)`.
    3. **FIX:** Ensure extrusion vector is not (0,0,0).

## 2. Non-Manifold Geometry

* **Trigger:** `telemetry['is_manifold'] == False`
* **Diagnosis:** Holes or T-Junctions.
* **Action:**
    1. Check loop indices. Ensure the last face connects to the first `(i+1)%total`.
    2. **FIX:** Add `bmesh.ops.recalc_face_normals`.

## 3. Missing Slots (Layers)

* **Trigger:** `verify_material_logic` returns FAIL.
* **Diagnosis:** BMesh Int Layers (`MAT_TAG` or `MASSA_EDGE_SLOTS`) not initialized.
* **Reference:** See `[.agent/workflows/WF_Slot_Standardization.md](file:///d:/AntiGravity_google/MASSA_BMESH_CONSOLE-main/.agent/workflows/WF_Slot_Standardization.md)` for ID definitions.
* **Fix:**
    1. Initialize layers:
        * `tag_layer = bm.faces.layers.int.new("MAT_TAG")`
        * `edge_layer = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")`
    2. Assign IDs:
        * Faces: `f[tag_layer] = 0` (BASE)
        * Edges: `e[edge_layer] = 1` (PERIMETER) or as needed (1-5).

## 4. Normal Faces (Orientation)

* **Trigger:** `telemetry['face_orientation']` or Visual Red Faces in Overlay.
* **Diagnosis:** Normals are flipped or inconsistent.
* **Action:**
    1. **FIX:** Inject `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)`.

## 5. Missing UV Seams (Unwrapping)

* **Trigger:** `len([e for e in bm.edges if e.seam]) == 0` (No Seams Found).
* **Diagnosis:** Model has not been unwrapped or marked for unwrapping.
* **Reference:** See `[.agent/workflows/WF_UVSeam.md](file:///d:/AntiGravity_google/MASSA_BMESH_CONSOLE-main/.agent/workflows/WF_UVSeam.md)` for full unwrapping logic.
* **Fix:**
    1. Select Sharp Edges: `[e for e in bm.edges if e.calc_face_angle(0) > 1.05]`
    2. Mark Seams: `e.seam = True`
    3. Unwrap: `bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.02)`
