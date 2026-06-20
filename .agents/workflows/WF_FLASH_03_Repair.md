---
description: Workflow for the Gemini Flash Agent to parse backend debug telemetry and surgically repair Massa Geometry Cartridges.
---

# ⚡ MASSA FLASH AGENT: [STATE: REPAIR] ⚡

## 1. OBJECTIVES & PRE-REQUISITES
**Goal:** Parse JSON error telemetry from the Massa `runner.py` auditor and execute surgical fixes without breaking working geometry logic.
**Inputs:** A broken `.py` file from `massa/modules/cartridges/` and a `FAIL` or `CRITICAL` telemetry report from the backend.
**Output:** A fixed `.py` file that passes `[STATE: AUDIT]`.
**Constraints:** **DO NOT** rewrite the entire script to fix a single syntax error. Do not try to "guess" the Blender API. Rely only on the BMesh documentation and specific fix heuristics below.

## 2. THE REPAIR LOOP

### Step 1: Diagnose the Telemetry
Analyze the output from: `blender --background --python massa/modules/debugging_system/runner.py -- --cartridge path/to/script.py --mode AUDIT`

**Key Indicators:**
*   `CRITICAL_WIRE_EDGES`: Edges exist without connected faces. (Common when creating `bmesh` primitives without faces).
*   `CRITICAL_LOOSE_VERTS`: Vertices floating in space (not connected to any edges).
*   `CRITICAL_ZERO_AREA_FACES`: Faces with zero surface area.
*   `WARNING_THIN_FACES`: Very narrow faces (usually caused by boolean operations or bad scales).
*   `FUZZ_CRASH`: The parametric generation failed when given randomized input values.

### Step 2: Implement Heuristics (Anti-Hallucination Matrix)

**CRITICAL RULE:** Do not invent functions like `bmesh.ops.fix_topology(bm)`. Only use standard `bmesh.ops` like `remove_doubles` or `recalc_face_normals`.

| Error Metric | Most Common Cause | The Flash Fix Directive |
| :--- | :--- | :--- |
| **`CRITICAL_ZERO_AREA_FACES`** | Extruding without moving (`offset=0`), or scaling by `(1,1,0)`. | Inject `bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)` at the end of `build_shape`. |
| **`CRITICAL_WIRE_EDGES`** | `bmesh.ops.create_grid` without creating faces, or partial deletions. | Ensure all custom primitives generate faces, or use `bmesh.ops.delete` on non-manifold edges. |
| **`FUZZ_CRASH`** | A user property (e.g., `thickness`) was set so large it collapsed the geometry (e.g. `thickness > width / 2`). | Add strict `min` and `max` constraints to `FloatProperty` or `IntProperty` definitions. Clamp math inside `build_shape` (e.g., `safe_thick = min(self.thick, self.width / 2)`). |
| **SyntaxError / NameError** | Calling `bpy.ops.mesh.primitive_cube_add` instead of `bmesh.ops.create_cube`. | Replace all `bpy.ops` calls with `bmesh.ops`. |
| **"BMesh data removed"** | Storing a reference to a Vertex/Edge/Face and using it *after* a topology-changing operation (like `remove_doubles` or `delete`). | Re-acquire references after any topology change (e.g., `[v for v in bm.verts if ...]`). |

### Step 3: Surgical Injection
Apply the exact, minimal fix required. **Do not modify working parts of `build_shape` just because you think it could be written better.** The goal is to return a passing audit, not refactor the codebase.

### Step 4: Verification & Transition
*   Ensure your fix did not erase existing `bpy.props`, `CARTRIDGE_META`, or `bl_idname`.
*   Transition directly back to `[STATE: AUDIT]` to verify the fix.
*   If the audit returns **FAIL** again, return to `[STATE: REPAIR]` (Max 3 attempts before escalating to the user).
