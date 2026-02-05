# 🔵 AGENT: CARTRIDGE_ITERATOR_v2.8 (ADDITION MODE)

## 1. GAP ANALYSIS & OBJECTIVES

*The protocol for safely expanding existing geometry cartridges.*

| Iteration Gap | 🟢 The Antigravity Solution |
| :--- | :--- |
| **Destructive Overwrite** | Agents often delete previous logic to add new features. **Fix:** The **Preservation Protocol** (Phase 2) identifies "Safe Zones" vs "Injection Points". |
| **Index Shift** | Adding geometry changes vertex indices, breaking old selections. **Fix:** **Edge Slot Extension** (Phase 4) selects new geometry independently. |
| **Regression** | New features might break the manifold status of old geometry. **Fix:** The **Shadow Audit** (Phase 6) runs the *entire* file to catch regressions. |
| **Variable Clashing** | Overwriting `verts` or `edges` variables breaks prior logic. **Fix:** Mandate **Unique Variable Naming** for new additions. |

---

## 2. THE ADDITIVE PIPELINE

### 🟣 PHASE 1: INGESTION & CONTEXT

**Goal:** Parse the existing Python file and the new User Request.

1. **Read Source:** Load the existing `geometry_cartridges/[target_file].py`.
2. **Identify State:**
    * Locate the `bm` (BMesh) initialization.
    * Locate the **Finalization Block** (`to_mesh`, `free`, `return`).
3. **Define Addition Strategy:**
    * *Append:* Add geometry to empty space (e.g., adding a turret to a tank hull).
    * *Modify:* Select existing geometry via Slots and alter it (e.g., beveling the tank edges).

### 🔵 PHASE 2: PRESERVATION PROTOCOL

**Goal:** Maintain the file integrity while preparing for injection.

**Constraint:** You must rewrite the **ENTIRE** file. Do not output snippets.

* **Keep:** Imports, Header, `bmesh.new()`, and existing geometry logic.
* **Keep:** The `slots = {...}` dictionary initialization.
* **Target:** The **Injection Point** is strictly *after* existing logic but *before* the Finalization Block.

```python
    # ... EXISTING CODE ...
    
    # [INJECTION POINT START]
    # New logic goes here
    # [INJECTION POINT END]

    # FINALIZATION (Keep this at the end)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.to_mesh(mesh)
```

### 🟣 PHASE 3: SURGICAL CONSTRUCTION

**Goal:** Create new geometry or modify existing shapes using BMesh.

* **Safety Check:** Always call `bm.verts.ensure_lookup_table()` before starting new operations to account for previous geometry changes.
* **Creation:**
  * **New Primitive:** `bmesh.ops.create_cube(bm, ...)`
  * **Boolean:** If adding details, use `bmesh.ops.boolean` carefully.
* **Variable Isolation (Crucial):** Capture the return of your new operations into new variables (e.g., `new_verts`) so you don't accidentally select the old geometry.

### 🟠 PHASE 4: EDGE SLOT EXTENSION (CRITICAL)

**Goal:** Manage selections for the NEW geometry without breaking OLD slots.

1. **Extend Dictionary:**
    * **Rule:** Do not overwrite `slots`.
    * **Add:** New keys for the new features.

    ```python
    slots['new_feature_name'] = []
    ```

2. **Geometric Selection (The Delta):**
    * **Constraint:** You cannot rely on indices (0, 1, 2) as the old geometry took those.
    * **Method:** Select based on "Last Created" variables from Phase 3.

    *Example: specific selection of NEW geometry*

    ```python
    # We select edges that belong to the new logic we just wrote
    for v in new_verts:
        for e in v.link_edges:
            slots['antenna_spikes'].append(e)
    ```

3. **Execute Operations:** Apply modifiers only to the new slots.

    ```python
    bmesh.ops.bevel(bm, geom=slots['antenna_spikes'], ...)
    ```

### 🟣 PHASE 5: UV RE-INTEGRATION

**Goal:** Update the UV map to include the new geometry.

1. **Refine Seams:** Mark seams on the new `slots['...']`.
    * **Note:** Existing seams should remain marked (boolean `e.seam` is persistent).
2. **Global Unwrap:** Because geometry changed, the UV map is invalid.
    * **Action:** You must re-run the `smart_project` or `unwrap` command on the entire mesh at the end.

    ```python
    bpy.ops.uv.smart_project(island_margin=0.02)
    ```

### 🔴 PHASE 6: THE SHADOW AUDIT (REGRESSION TESTING)

**Goal:** Verify the new addition didn't break the old file.

**The Loop Protocol:**

1. **Staging:** Save the full, updated code to: `geometry_cartridges/_temp_iteration.py`
2. **Execute Bridge:**

    ```bash
    python debugging_system/bridge.py geometry_cartridges/_temp_iteration.py
    ```

3. **Decision Matrix:**
    * ❌ **CASE A: STATUS == "FAIL"**
        * **Trigger:** "Zero-Area Faces" (often caused by new geometry overlapping old).
        * **Action:** Check the intersection between old and new. Add specific cleanup for the new region.
        * **Repeat:** Return to Step 1.
    * ❌ **CASE B: STATUS == "SYSTEM_FAILURE"**
        * **Trigger:** "KeyError" (You tried to access a slot you deleted) or Syntax Error.
        * **Action:** Restore the slots definition from Phase 4.
    * ✅ **CASE C: STATUS == "PASS"**
        * **Trigger:** Audit confirms the combined geometry is valid.
        * **Action:** Proceed to Phase 7.

### 🟢 PHASE 7: DELIVERY (VERSIONING)

**Goal:** Update the codebase.

1. **Versioning:** Do not overwrite the original immediately if version control is desired.
2. **Save as:** `geometry_cartridges/[original_name]_v2.py` (or overwrite if instructed).
3. **Presentation:** Present the Full Code (not just the diff).
4. **Certify:** "Iteration Complete: New Geometry Added, Topology Valid, Slots Extended."

---

## 3. ITERATION SPECIFIC HEURISTICS

| Error Message | Diagnosis | Technical Solution |
| :--- | :--- | :--- |
| **"NameError: slots not defined"** | You inserted code that uses slots before slots was defined. | Ensure injection happens after the `slots = {...}` line but before Finalization. |
| **"Zero-Area Faces" (Regression)** | Your new geometry is Z-fighting with the old geometry. | Use `bmesh.ops.translate` to move the new detail slightly (e.g., 0.001 units). |
| **"Boolean Failure"** | The old geometry wasn't watertight, so the new Boolean failed. | Run `bmesh.ops.remove_doubles` before the boolean operation. |
