---
description: Generate a BMesh cartridge following massa_mesh_gen console specs.
---

# AGENT: CARTRIDGE_GENERATOR (MASTER)

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

### 🟢 PHASE 0: SYSTEM HEALTH CHECK

**Goal:** Ensure the Host Environment (Console) is healthy before generating chips.

1. **Run System Audit:** Call `inspector.audit_console()`.
    * *Tool:* `audit_console`
2. **Verify:** Import/Registry must be PASS.

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
from ...operators.massa_base import Massa_OT_Base

# 1. METADATA & FLAGS
CARTRIDGE_META = {
    "name": "Cartridge Name",
    "id": "cart_unique_id",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD", # MICRO, STANDARD, MACRO
    "flags": {
        "USE_WELD": False,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
    },
}

class MASSA_OT_cart_unique_id(Massa_OT_Base):
    bl_idname = "massa.gen_cart_unique_id"
    bl_label = "Cartridge Label"
    bl_options = {"REGISTER", "UNDO", "PRESET"}
    
    # PROPERTIES GO HERE...

    # 2. THE HARD 10 SLOT MANDATE
    def get_slot_meta(self):
        return {
            0: {"name": "Base", "uv": "BOX", "phys": "GENERIC"},
            1: {"name": "Detail", "uv": "BOX", "phys": "GENERIC"},
            2: {"name": "Trim", "uv": "BOX", "phys": "GENERIC"},
            # ... Must handle 0-9 defined slots
            9: {"name": "Socket", "uv": "SKIP", "sock": True},
        }

    def build_shape(self, bm):
        # 3. SETUP LAYERS (Phase 4)
        tag_layer = bm.faces.layers.int.new("MAT_TAG")
        edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        
        # ... GEOMETRY LOGIC GOES HERE ...
        
        # FINALIZATION
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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

### 🟠 PHASE 4: THE SLOT SYSTEM (DEEP LOGIC)

**Goal:** procedural selection & property assignment using BMesh Layers.

#### A. THE HARD 10 (MATERIAL SLOTS - FACE)

**Mandate:** Every face must be assigned to a slot index (0-9).
**Method:** BMesh Int Layer `"MAT_TAG"`.
**Legend:**

* **0=Base**: Main Hull
* **1=Detail**: Vents/Grilles
* **2=Trim**: Borders
* **3=Glass**: Windows
* **4=Emission**: Lights
* **5=Dark**: Inner/Shadows
* **6=Accent**: Decals/Paint
* **7=Utility**: Bolts/Handles
* **8=Transparent**: Forcefields
* **9=Socket**: Internal Snapping

```python
# Create Layer
tag_layer = bm.faces.layers.int.new("MAT_TAG")

# Assign Logic
for f in new_faces:
    f[tag_layer] = 0 # Assign to Slot 0 (Base)
```

#### B. EDGE SLOTS (THE NERVOUS SYSTEM - EDGE)

**Mandate:** Edges must be tagged for their role in the "Polish Stack" (Bevels, subdivision, etc).
**Method:** BMesh Int Layer `"MASSA_EDGE_SLOTS"`.
**Legend:**

* **1=PERIMETER** (Blue): Outer boundary. Seam + Sharp + Bevel.
* **2=CONTOUR** (Green): 90° Form Break. Sharp + Bevel.
* **3=GUIDE** (Red): Topological Seam. Seam Only.
* **4=DETAIL** (Orange): Minor Surface Detail. Bevel Only.
* **5=FOLD** (Purple): Cloth/Soft Crease. Subdivision Weighting.

```python
edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
for e in bm.edges:
    if e.is_boundary:
        e[edge_slots] = 1 # PERIMETER
```

#### C. SELECTION GROUPS (PROCEDURAL)

**Goal:** Track geometry *internally* for operations (Bevel this, Extrude that).
**Constraint:** Do not confuse this with "Slots". These are Python lists.

1. **Initialize Groups:**

   ```python
   # Rename 'slots' to 'selection_groups' to avoid confusion
   selection_groups = {'to_bevel': [], 'to_extrude': []}
   ```

2. **Populate Groups:**

   ```python
   for e in bm.edges:
       if is_vertical(e):
           selection_groups['to_bevel'].append(e)
   ```

3. **Execute:**

   ```python
   bmesh.ops.bevel(bm, geom=selection_groups['to_bevel'], offset=0.1)
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

2. **Execute Audit:** Trigger the Shadow Audit.
    * **Tool:** `inspector.audit_cartridge_geometry(filename="_temp_candidate.py")`
    * *Note:* The tool internally runs the bridge logic.

3. **Ingest Telemetry (JSON):** Parse the JSON response.

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
