---
description: Workflow for discovering and reusing existing cartridge logic before generation.
---

# 🔵 AGENT: CARTRIDGE_SEARCH_PROTOCOL (DISCOVERY MODE)

## 1. OBJECTIVE & PHILOSOPHY

*The "Hive Mind" Protocol: Don't reinvent the wheel. Steal from the best.*

| Discovery Gap | 🟢 The Antigravity Solution |
| :--- | :--- |
| **Blind Generation** | Agents write generic BMesh code that ignores established project patterns. **Fix:** **Library Introspection** allows the agent to mimic successful cartridges. |
| **Inconsistent Slots** | New cartridges use different slot naming conventions than old ones. **Fix:** **Source Analysis** ensures slot alignment across the library. |
| **Syntax Hallucination** | Agents guess API calls. **Fix:** **Snippet Extraction** provides proven, working code blocks. |

---

## 2. THE DISCOVERY PIPELINE

### 🟣 PHASE 1: THE LIBRARY SCAN (ARCHITECT LOOP)

**Goal:** Identify potential reference cartridges based on the user's request.
**Tool:** `list_cartridges()`

1. **Trigger:** User asks for a shape (e.g., "Make a sci-fi crate").
2. **Action:** Call `list_cartridges()` to see what exists.
3. **Filter:** Look for keywords in filenames.
    * *Request:* "Crate" -> *Match:* `cart_prim_09_box.py`, `cart_prop_crate_01.py`
    * *Request:* "Pipe" -> *Match:* `cart_prim_02_pipe.py`

### 🔵 PHASE 2: SOURCE EXTRACTION (CONTEXT AWARENESS)

**Goal:** Read the code of the most relevant cartridge.
**Tool:** `read_library_source(filename="...")`

1. **Selection:** Choose the best match from Phase 1.
2. **Action:** Call `read_library_source` on that file.
3. **Analysis:**
    * **Geometry Logic:** How did they build the base shape? (Primitives vs Manual Verts)
    * **Slot Logic:** How are materials assigned? (e.g., `slots['body']`, `slots['trim']`)
    * **Parameter Handling:** How are `self.width` or `self.segments` used?

### 🟠 PHASE 3: SNIPPET HARVESTING

**Goal:** Extract reusable blocks to ensure consistency.

* **The "Golden Blocks" to Steal:**
    1. **The Header:** Imports and `bmesh.new()` setup.
    2. **The Slot Definition:** `selection_groups = {...}` or `slots = {...}`.
    3. **The Finalization:** `bmesh.ops.remove_doubles(...)` and `bm.to_mesh(...)`.
    4. **Specific Logic:** If the user wants "pipes like the existing ones", copy the cylinder creation and seam logic exactly.

### 🟢 PHASE 4: SYNTHESIS

**Goal:** Combine the found knowledge with the new request.

* **Pattern Matching:**
  * *If* the reference uses `bmesh.ops.create_cube`, *Then* the new script should likely start there too.
  * *If* the reference uses a specific "Edge Slot" tag for seams (e.g., `layer[e] = 2`), *Then* the new script **MUST** use that same tag to be compatible with the Console's polish system.

---

## 3. SEARCH HEURISTICS

| Scenario | Action |
| :--- | :--- |
| **"Make a variant of X"** | **MANDATORY SEARCH.** Find "X" in the library first. |
| **"Fix the UVs on this"** | **SEARCH.** Look at `cart_prim_02_pipe.py` for correct Seam logic. |
| **"Create a new primitive"** | **SEARCH.** Check `cart_prim_01_cube.py` for the standard boilerplate. |
| **"I want a complex asset"** | **SEARCH.** Find the closest primitive base (e.g., Tank -> Box) to start from. |
