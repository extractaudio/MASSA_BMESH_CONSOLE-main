---
description: Workflow for the Gemini Flash Agent to modify existing Massa Geometry Cartridges without erasing context.
---

# ⚡ MASSA FLASH AGENT: [STATE: MODIFY] ⚡

## 1. OBJECTIVES & PRE-REQUISITES
**Goal:** Surgically augment an existing `.py` cartridge based on user request (e.g., "Add a Bevel slider to the crate").
**Inputs:** A target `.py` file from `massa/modules/cartridges/` and the user's specific modification request.
**Constraints:** **DO NOT** rewrite the entire file from scratch. **DO NOT** erase existing properties or metadata. If modifying the class signature, keep the `bl_idname` identical.

## 2. THE MODIFICATION PROTOCOL

### Step 1: Read & Preserve Context
* Use the file reading tools to ingest the full source of the target cartridge.
* Identify the exact location of:
  * `CARTRIDGE_META`
  * The Class definition (`class MASSA_OT_...`)
  * `get_slot_meta`
  * `draw_shape_ui`
  * `build_shape`

**Anti-Erasure Mandate:**
The Flash model must keep a mental copy of all properties (`FloatProperty`, `IntProperty`, etc.) defined in the original script. **Never delete a property unless explicitly instructed.** The Console relies on these for data persistence (Resurrection System).

### Step 2: Formulate the Surgical Plan
Identify *where* the change needs to happen:
* **Scenario A: New Parameter**
  1. Add property definition to the class body.
  2. Add `col.prop(self, "new_prop")` to `draw_shape_ui`.
  3. Integrate `self.new_prop` into `build_shape` logic.
* **Scenario B: New Geometry Logic**
  1. Only modify the targeted section inside `build_shape`.
  2. Ensure BMesh layer variables (e.g., `edge_slots`) are still valid.
* **Scenario C: Adjusting Metadata**
  1. Modify only the targeted key within `CARTRIDGE_META` or `get_slot_meta`. Do not erase other keys.

### Step 3: Execute the Patch (Search and Replace)
Use targeted patching (e.g., Git-style diffs) to apply the modifications instead of returning the entire file. If you must output the full script, double-check that **every** existing property, import, and slot is still present.

### Step 4: Verification & Transition
* Review the modified code for syntax errors.
* **Crucial:** Did you delete `CARTRIDGE_META`? Did you rename `bl_idname`? If yes, **STOP** and revert.
* Transition directly to `[STATE: AUDIT]` to execute the newly modified code against the `runner.py` debugging system. Do not skip this step.
