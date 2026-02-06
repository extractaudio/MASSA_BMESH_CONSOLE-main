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

## 3. Missing Slots

* **Trigger:** `scan_slots` missing expected keys.
* **Fix:** Edit script to assign `face.material_index = X` correctly.
