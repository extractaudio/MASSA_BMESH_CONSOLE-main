---
description: Workflow for correcting UV seams and packing logic
---

# 🟣 AGENT: UV_SEAMS_CORRECT

## 1. IDENTITY & OBJECTIVES

**Role:** Texture Coordinate Specialist
**Specialization:** Seam Marking, UV Packing, Island Logic
**System Access:**

* **Input:** `geometry_cartridges/`
* **Validator:** `debugging_system/auditors/massa_ui_auditor.py`
* **Runtime:** "Fake Blender" Bridge (Background Process)

| 🛡️ Standard Gap | 🟢 The Antigravity Solution |
| :--- | :--- |
| **Distortion** | Procedural mapping stretches textures. **Fix:** Angle-based unwrapping on specific Seam Slots. |
| **Bleeding** | Tight margins cause texture bleed. **Fix:** Audit checks for `margin > 0.01`. |
| **View Context** | `Project_from_view` fails in background mode. **Fix:** Use mathematical projection or Context Overrides. |
| **Pinched Polys** | Zero-area UV faces. **Fix:** **Massa Auditor** detects Shoelace Formula errors. |

---

## 2. THE UNWRAPPING WORKFLOW

### 🟢 PHASE 0: SYSTEM HEALTH CHECK

**Goal:** Ensure the Engine is capable of Seam/Slot interpretation.

1. **Run System Audit:** Call `inspector.audit_console()`.
    * *Tool:* `audit_console`
2. **Verify:** `MASSA_EDGE_SLOTS` layer check must PASS.

### 🟣 PHASE 1: TOPOLOGY ANALYSIS

1. **Read Topology:** Identify sharp angles (>60 deg) and cylindrical caps.
2. **Strategy:**
    * *Hard Surface:* Smart Project with high margin.
    * *Organic/Complex:* Manual Seam Marking via Edge Slots.
    * *View Projection:* If the user requests "Project from View", you **must** use a context override or a mathematical fallback (assigning `uv_layer.data` directly), as the background auditor has no active viewport window.

### 🟠 PHASE 2: SEAM DEFINITION (PART-BASED LOGIC)

**Constraint:** Do not blindly unwrap. Analyze the geometry and apply a specific strategy.

#### 🪵 STRATEGY A: THE PLANKS (Strips/Beams)

* **Logic:** Isolate the "Ends" and cut them off. Then slice the "Length" once to unroll it.
* **Pattern:**
    1. **Caps:** Select edges at the extreme ends of the major axis. Mark Seams.
    2. **Rail:** Select ONE edge running the full length of the plank. Mark Seam.
    3. **Result:** The main body unrolls as a single consistent strip; caps are separate islands.

    ```python
    # Pseudo-code for Plank Logic
    major_axis = get_major_axis(bm) # e.g. 'X'
    sorted_faces = sort_faces_along_axis(bm, major_axis)
    # Mark seams on the first and last face loops
    mark_face_perimeter(sorted_faces[0], seam=True)
    mark_face_perimeter(sorted_faces[-1], seam=True)
    # Mark ONE longitudinal edge
    mark_edge_along_axis(bm, major_axis, count=1)
    ```

#### 🛢️ STRATEGY B: THE CYLINDER (Pipes/Poles)

* **Logic:** "Decap and Zipper".
* **Pattern:**
    1. **Caps:** Select Top and Bottom loops. Mark Seams.
    2. **Zipper:** Select ONE vertical edge connecting Top and Bottom. Mark Seam.
    3. **Result:** Cylinder unrolls into a perfect rectangle.

#### 📦 STRATEGY C: HARD SURFACE (Generic)

* **Logic:** Angle-Based detection for complex non-primitive shapes.
* **Pattern:**

    ```python
    seam_edges = []
    for e in bm.edges:
        # Mark sharp edges (>60 deg) as seams
        if e.calc_face_angle(0) > math.radians(60):
            seam_edges.append(e)
    for e in seam_edges:
        e.seam = True
    ```

### 🟣 PHASE 3: PROJECTION & PACKING

1. **Execution:**
    * If Seams exist: `bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.02)`
    * Fallback: `bpy.ops.uv.smart_project(island_margin=0.02)`
    * **Rule:** Never use `margin=0`.

### 🔴 PHASE 4: THE MASSA AUDIT (DEBUGGING LOOP)

**Goal:** Verify UV integrity using the `massa_ui_auditor` in the background.

**The Protocol:**

1. **Staging:** Save script with UV logic to `geometry_cartridges/_temp_uv_candidate.py`.
2. **Execute Bridge:** Trigger the Shadow Audit.
    * **Tool:** `inspector.audit_cartridge_geometry(filename="_temp_uv_candidate.py")`
    * *(This triggers the `massa_ui_auditor` analysis inside the background process)*.

3. **Analyze Output (JSON):**
    * ❌ **FAIL: "Pinched UV Faces" / "Massa_Fail"**
        * *Cause:* Faces have 3D area but 0 area in 2D UV space.
        * *Fix:* Switch unwrap method or increase margin.
    * ❌ **FAIL: "Context Incorrect"**
        * *Cause:* You tried `project_from_view` without a viewport override.
        * *Fix:* Switch to `smart_project` for the audit pass, or implement a `bmesh` loop to assign UVs manually by vertex coordinates.
    * ❌ **FAIL: "Island Overlap"**
        * *Cause:* Islands are intersecting.
        * *Fix:* Use `pack_islands` with a context override.
    * ✅ **PASS:** Proceed.

### 🟢 PHASE 5: DELIVERY

1. **Finalize:** Rename to valid cartridge name.
2. **Present:** Confirm *"Massa Audit Passed: No Overlaps, Buffer Safe."*
