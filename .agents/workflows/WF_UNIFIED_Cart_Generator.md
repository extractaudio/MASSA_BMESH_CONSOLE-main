---
description: Generate a BMesh cartridge following the Unified Protocol v2.8
---

# 🟢 AGENT: CARTRIDGE_GENERATOR_v2.8 (MASTER)

## 1. GAP ANALYSIS & OBJECTIVES

*The bridge between procedural intent and BMesh precision.*

| Generation Gap | 🟢 The Antigravity Solution |
| :--- | :--- |
| **Context Blindness** | Agents cannot see if code fails in a specific Blender context. **Fix:** Use `bridge.py` to run code in a headless instance. |
| **Topology Decay** | LLMs often generate zero-area faces or non-manifold edges. **Fix:** Mandatory `bmesh` cleanup passes and topological audits. |
| **Selection Drift** | Indices change after operations, breaking selection logic. **Fix:** The **Edge Slot System** (Phase 4) tracks geometry by property, not index. |
| **Feedback Loop** | User debugs the code. **Fix:** The Agent debugs the code via the Shadow Audit loop (Phase 6). |

---

## 2. THE MONOLITHIC PIPELINE

### 🟣 PHASE 1: INGESTION & INTENT

**Goal:** Translate user prompt into geometric constraints.

1. **Deconstruct Request:** Identify the primitive base (Cube, Cylinder, Convex Hull) and modifiers.
2. **Define Strategy:**
    * **Primitive:** Use `bmesh.ops.create_*`.
    * **Constructive Logic:** Extrude, Bevel, Boolean.
    * **Rule:** Prefer `bmesh` operators over `bpy.ops`. BMesh is data-only and stable in background processes.

### 🔵 PHASE 2: CARTRIDGE STRUCTURE (IMMUTABLE)

**Goal:** Establish the strict file format.
**Constraint:** You must use this exact skeleton. Do not deviate.

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

def generate_geometry():
    # 1. SETUP
    mesh = bpy.data.meshes.new('Created_Mesh')
    obj = bpy.data.objects.new('Created_Object', mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # ... GEOMETRY LOGIC GOES HERE ...
    
    # FINALIZATION
    bm.to_mesh(mesh)
    bm.free()
    return obj
```

### 🟣 PHASE 3: GEOMETRY CONSTRUCTION

**Goal:** Generate the primary shape using BMesh.

* **Creation:** Instantiate primitives (Cube, Cylinder, IcoSphere).
* **Transformation:** Apply Scale, Rotate, Translate on `bm.verts`.
* **Cleanup (Mandatory):** Every generation step must end with a check for doubles to prevent "Zero-Face" errors later.

```python
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
```

### 🟠 PHASE 4: THE EDGE SLOT SYSTEM (CRITICAL)

**Goal:** Procedural selection management.
**Constraint:** NEVER select edges by index number (e.g., `bm.edges[4]`) as indices shift. Use Slots.

1. **Initialize Slots:** Create lists to hold specific geometry for later operations.

    ```python
    slots = {'bevel': [], 'seam': [], 'subd': [], 'connector_top': []}
    ```

2. **Populate Slots (Geometric Logic):** Select based on properties (position, direction, length).
    *Example: "Select all vertical edges for the 'bevel' slot."*

    ```python
    for e in bm.edges:
        # Check if edge is vertical (Z difference exists, X/Y diff is near 0)
        is_vertical = abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1
        if is_vertical:
            slots['bevel'].append(e)
    ```

3. **Execute Slots:** Apply operations only to the specific slots.

    ```python
    bmesh.ops.bevel(bm, geom=slots['bevel'], offset=0.1)
    ```

### 🟣 PHASE 5: UV & MATERIAL FINALIZATION

**Goal:** Prepare the surface for rendering.

* **Material Slots:** Create and assign material slots on the Object.
* **UV Unwrapping:**
  * **Constraint:** Do not use `bpy.ops.uv.smart_project` without parameters.
  * **Required:** `bpy.ops.uv.smart_project(island_margin=0.02)` to prevent bleeding/pinching errors during audit.

### 🔴 PHASE 6: THE SHADOW AUDIT (DEBUGGING LOOP)

**Goal:** Mathematically verify the geometry using the "Fake Blender" Bridge. (CRITICAL STEP)
*This phase replaces the manual review. You must execute the code to verify it.*

**The Loop Protocol:**

1. **Staging:** Save the current code to: `geometry_cartridges/_temp_candidate.py`
    *Do not overwrite any final files yet.*

2. **Execute Bridge:** Run the background auditor in the terminal:

    ```bash
    python debugging_system/bridge.py geometry_cartridges/_temp_candidate.py
    ```

3. **Ingest Telemetry (JSON):** Parse the JSON response from the bridge.

4. **Decision Matrix:**
    * ❌ **CASE A: STATUS == "FAIL"**
        * **Trigger:** "Zero-Area Faces", "Pinched UVs", "Non-Manifold".
        * **Action:** Consult the Debugging Heuristics (Section 3). Rewrite `_temp_candidate.py` with fixes.
        * **Repeat:** Return to Step 2. (Max Retries: 3).
    * ❌ **CASE B: STATUS == "SYSTEM_FAILURE"**
        * **Trigger:** Syntax Error or Blender Crash.
        * **Action:** Fix Python syntax. Simplify geometry.
        * **Repeat:** Return to Step 2.
    * ✅ **CASE C: STATUS == "PASS"**
        * **Trigger:** Audit confirms clean geometry.
        * **Action:** Proceed to Phase 7.

### 🟢 PHASE 7: DELIVERY

**Goal:** Hand off the validated artifact.

1. **Finalization:** Rename `_temp_candidate.py` to `geometry_cartridges/[descriptive_name].py`.
2. **Presentation:** Present the code to the user with the certification: "Audit Complete: Topology Valid, Slots Valid."

---

## 3. DEBUGGING HEURISTICS (CHEAT SHEET)

*Use these technical solutions when Phase 6 fails.*

| Error Message | Diagnosis | Technical Solution |
| :--- | :--- | :--- |
| **"Zero-Area Faces"** | Vertices overlap perfectly, or scaling via (1,1,0). | 1. Ensure `bmesh.ops.remove_doubles` is called in Phase 3.<br>2. Check Vector math for zero-scaling. |
| **"Pinched UVs"** | UV islands overlap or have no area. | 1. Increase margin in `smart_project(island_margin=0.03)`.<br>2. Ensure Seams (from Phase 4 Slots) are marked properly. |
| **"Context Incorrect"** | Using Viewport-only operators in background. | Replace `bpy.ops.mesh.primitive_...` with `bmesh.ops.create_...`. |
| **"Edge Slot Empty"** | Bevel/Op failed because no edges were selected. | Check your geometric logic in Phase 4. Ensure your selection threshold (e.g. `z > 0.1`) matches the model scale. |
