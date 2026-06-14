---
name: cart-skill
description: >
  Diagnose and fix MASSA Blender cartridges in massa/modules/cartridges/.
  ALWAYS trigger immediately when the user's message begins with "Cart_skill" — this is a hard keyword trigger, no exceptions.
  Also use when the user reports: broken UV unwrap, seam errors, edge slot problems, wrong material slots (0-9), geometry shape errors,
  wrong object placement, CRITICAL audit flags, FUZZ_CRASH in test output, or any request to "fix", "repair", "audit", or "clean up" a cartridge.
  Covers three issue families: (1) UV / seam / edge-slot errors, (2) geometry / topology / shape errors, (3) material slot assignment errors.
---

# Cart-Skill — MASSA Cartridge Diagnosis & Repair

When a user message starts with **Cart_skill**, execute this skill in full.
Three issue families are handled. Classify first, then follow the matching path.

All paths below are relative to the repo root `MASSA_BMESH_CONSOLE-main/`.

---

## Step 0 — Identify the Cartridge

Extract the cartridge filename or path from the user's message.
If not given, list available cartridges:
```
mcp__blender__massa_list_cartridges
```
Or glob for the file:
```
massa/modules/cartridges/cart_*.py
```
Confirm the target before proceeding.

---

## Step 1 — Baseline Audit (mandatory, do this before anything else)

The headless audit is the only way to surface runtime crashes. Do not read source code or classify issues until you have the audit output in hand.

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```

Parse the JSON between `---AUDIT_START---` / `---AUDIT_END---`. Record every `CRITICAL_*`, `WARNING_*`, and `FUZZ_CRASH` flag — these are your repair targets. A `FUZZ_CRASH` means the cartridge crashes with random parameters; that must be fixed before anything else.

If Bash is unavailable (permissions blocked), note the limitation clearly, then proceed with static source analysis — but flag that runtime crashes may be present that static analysis cannot detect.

Also take a visual baseline if Blender MCP is connected:
```
mcp__blender__massa_spawn_cartridge   (spawn it)
mcp__blender__get_screenshot_of_window_as_image
```

---

## Step 2 — Classify the Issue

| Signal | Family |
|---|---|
| `FUZZ_CRASH` in audit output (any traceback from `build_shape`) | **B — Geometry / Topology** — fix this first, always |
| `CRITICAL_ZERO_AREA_FACES`, `CRITICAL_NON_MANIFOLD`, `CRITICAL_LOOSE_VERTS`, wrong shape, wrong proportions, wrong placement | **B — Geometry / Topology** |
| `CRITICAL_UV_*`, `WARNING_UV_*`, UV_INSPECT shows collapsed/overlapping/outside-bounds islands, seam lines visible in render, red heatmap | **A — UV / Seam / Edge Slot** |
| Wrong material on faces, faces missing material, slot indices in `build_shape` don't match `get_slot_meta`, invalid `phys` values, visual material bleed between parts | **C — Material Slot** |

A cartridge can have issues in more than one family. Fix order: **B first** (a crashing cartridge can't be UV-debugged), then C (slots drive UV strategies), then A (UVs last).

---

## Family A — UV / Seam / Edge Slot Fix

**Reference workflow:** `.agent/workflows/UV_unwrap.md`

### A1 — Inspect Current State

If Blender MCP is connected and the object is in the scene:
1. `mcp__blender__massa_get_selected_geometry` (enter Edit Mode first) — check `MASSA_EDGE_SLOTS` values, `is_seam`, `is_sharp` on all edges.
2. Run UV modes headlessly:
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_INSPECT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_HEATMAP
```
UV_INSPECT shows island layout and seam placement.
UV_HEATMAP shows distortion (blue/green = good, red = stretched).

### A2 — Diagnose from Output

| Problem | Root Cause | Fix |
|---|---|---|
| All UVs at (0,0) | `get_slot_meta` has `"SKIP"` but `build_shape` never writes UVs | Add manual UV math or change strategy to `"BOX"` / `"UNWRAP"` |
| Islands outside 0–1 space | Manual UV math overflows | Normalize with `uv_scale` / `fit_uvs` logic |
| Smeared band on one face of a closed loop | Missing wrapping fix | Apply the cylindrical seam wrapping fix (see below) |
| Overlapping islands | No seams cut | Tag edges: slot 1 for perimeter, slot 3 for hidden guide zippers |
| Isolated seam edges | Seam not forming a continuous loop | Extend the seam path to close the loop |
| UV spike / extreme distortion | Thin or degenerate face | Fix topology first (Family B), then re-audit |

### A3 — Edge Slot Assignment in Code

Read `build_shape` in the cartridge. Retrieve/create layers at the top of the function:
```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
force_seam = bm.edges.layers.int.get("massa_force_seam") or bm.edges.layers.int.new("massa_force_seam")
```

| Slot | Role | When to use |
|---|---|---|
| 1 | Perimeter | Cap borders, visible silhouettes — let `edge_auto_detect` handle these unless overriding |
| 2 | Contour | Internal hard 90° angles |
| 3 | Guide | Longitudinal seams on cylinders/tubes, hidden zipper cuts, segment cut rings |
| 4 | Detail | Small chamfers, soft feature lines |
| 5 | Fold | Subdivision crease |

**Do NOT manually tag Slot 1** unless overriding auto-detect — double-tagging confuses the engine.

### A4 — Wrapping Fix (closed-loop surfaces)

For any extruded profile (beam, pipe, wall, column): the face that spans the seam will smear without this fix.
```python
for f in bm.faces:
    if f.material_index != 0:
        continue
    loop_uvs = [[l, get_u(l.vert.co.x, l.vert.co.z), l.vert.co.y] for l in f.loops]
    us = [item[1] for item in loop_uvs]
    if (max(us) - min(us)) > (perim * 0.5):
        for item in loop_uvs:
            if item[1] < (perim * 0.5):
                item[1] += perim
    for l, u, v in loop_uvs:
        l[uv_layer].uv = (u * su_s, v * sv_s)
```

### A5 — Live Edge Slot Fix via MCP (optional, when Blender is connected)

Workflow from `.agent/workflows/02_massa_mesh_and_slots_workflow.md`:
1. Ensure Edit Mode, select target edges.
2. `mcp__blender__massa_get_selected_geometry` — confirm current slot values.
3. `mcp__blender__massa_assign_edge_slot_to_selection` with `slot` (1–5) and `action` (`SEAM`/`SHARP`/`BOTH`/`CREASE`/`BEVEL`/`IGNORE`).
4. Re-check with `mcp__blender__massa_get_selected_geometry`.

The MCP tool also returns a **procedural cartridge snippet** — inject it into `build_shape` so the fix is permanent.

### A6 — Verify

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_INSPECT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_HEATMAP
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```
Pass criteria: zero `CRITICAL_UV_*` flags, islands within 0–1 bounds, heatmap mostly blue/green.

---

## Family B — Geometry / Topology Fix

**Reference docs:** `docs/blender-addon-docs/CARTRIDGE_MANDATE.md` (§5, §6), `.agent/workflows/WF_CARTRIDGE_MODIFY.md`

### B1 — Inspect Shape

If Blender MCP is connected:
```
mcp__blender__massa_spawn_cartridge
mcp__blender__get_objects_summary
mcp__blender__get_object_detail_summary   (target object)
mcp__blender__get_screenshot_of_window_as_image
```
Check: vertex count, face count, non-manifold edges, normals, overall proportions match intent.

For headless inspection: the AUDIT output already surfaces topology flags — parse those.

### B2 — Fix by Flag

| Flag | Fix |
|---|---|
| `CRITICAL_ZERO_AREA_FACES_N` | Add a size guard: `if self.length < 0.001: return`. Or call `bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:])` |
| `CRITICAL_LOOSE_VERTS_N` | `bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')` |
| `CRITICAL_NON_MANIFOLD_N` | Find T-junctions or open holes; use `bmesh.ops.fill` or fix bridge logic |
| `CRITICAL_NO_PERIMETER_DEFINED` | Create/retrieve `MASSA_EDGE_SLOTS` layer; tag silhouette edges with slot 1 |
| `CRITICAL_MISSING_SLOT_LAYER` | Add `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` at top of `build_shape` |
| `WARNING_THIN_FACES_N` | Rebuild the affected loops with better cross-section — usually a profile point is nearly collinear |
| `FUZZ_CRASH` | Read the traceback; protect the crashing operation with `if not f.is_valid: continue` or a size guard |

### B3 — Shape / Placement Issues (no audit flag)

When the shape looks wrong visually:
1. Read `build_shape` top-to-bottom using jCodemunch (`get_symbol_source`).
2. Identify which phase produces the wrong geometry (profile definition, extrusion, segmentation, cap normal forcing).
3. Make the targeted fix — smallest possible change.
4. Run VISUAL_DIFF against a backup:
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode VISUAL_DIFF \
  --payload '{"filename_b": "massa/modules/cartridges/<name>_backup.py"}'
```

### B4 — Headless Safety Rules (non-negotiable)

- No `bpy.ops` inside `build_shape` — use `bmesh.ops` only.
- No `bpy.context` reads inside `build_shape`.
- No `bpy.data` creation inside `build_shape`.
- Call `bm.verts.ensure_lookup_table()` (and `.edges`, `.faces`) after any `bm.verts.new()` call.
- Wrap `bm.faces.new(verts)` in `try/except ValueError`.

### B5 — Verify

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```
Zero new `CRITICAL_*` flags vs baseline. No new `FUZZ_CRASH`.
If geometry was changed, also screenshot from Blender MCP and confirm visually.

---

## Family C — Material Slot Fix

**Reference:** `.agent/workflows/02_massa_mesh_and_slots_workflow.md`

### C1 — Read Current Slot State

Two things to check — both matter:

**1. Index coverage:** Read `get_slot_meta()` and note every slot index defined. Read `build_shape` and note every `f.material_index = N` assignment. Every index used in `build_shape` must appear in `get_slot_meta`, and every slot in `get_slot_meta` should be used by at least one face.

**2. Phys value validity:** For every slot in `get_slot_meta`, verify the `phys` value is a real key in `MASTER_MAT_DB`. Invalid phys values (`"METAL_CHECKERPLATE"`, `"METAL_PAINTED"`, `"DEBUG_9"`, etc.) silently fall back to a default material at runtime. Valid keys include: `METAL_IRON`, `METAL_STEEL`, `CONCRETE_RAW`, `RUBBER`, `GLASS_CLEAR`, `FABRIC_ROUGH`, `WOOD_OAK`, `PLASTIC_HARD`, `GENERIC`, `MASSA_DEBUG_1` through `MASSA_DEBUG_9`.

If Blender MCP is connected (Edit Mode, faces selected):
```
mcp__blender__massa_get_selected_geometry   → check material_index per face
```

### C2 — Fix Mismatches

| Problem | Fix |
|---|---|
| `build_shape` uses slot index not in `get_slot_meta` | Add the missing slot to `get_slot_meta` with correct `name`, `uv`, `phys` |
| `get_slot_meta` defines a slot but no faces use it | Either remove the unused slot or assign the correct faces to it |
| Invalid `phys` value (not in `MASTER_MAT_DB`) | Replace with the closest valid key (e.g. `METAL_CHECKERPLATE` → `METAL_IRON`) |
| Socket slot not on index 9 | Move socket faces to `material_index = 9`, set `"sock": True` and `"uv": "SKIP"` in `get_slot_meta[9]` |

Valid `uv` strategies: `"SKIP"`, `"BOX"`, `"FIT"`, `"TUBE_Z"`, `"TUBE_Y"`, `"TUBE_X"`, `"UNWRAP"`.
Use `"SKIP"` for any slot where `build_shape` writes UVs manually.

### C3 — Live MCP Face Slot Assignment

If fixing face assignments interactively (Blender connected, Edit Mode, faces selected):
1. `mcp__blender__massa_get_selected_geometry` — confirm current `material_index`.
2. `mcp__blender__massa_assign_face_material_slot_to_selection` with target slot index.
3. `mcp__blender__massa_get_selected_geometry` — verify.

Then mirror the fix back into `build_shape` (`f.material_index = N` on the correct faces).

### C4 — Verify

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```
Confirm `get_slot_meta` covers all indices used in `build_shape`. No new flags.

---

## Step 3 — Final Delivery Checklist

Before reporting done:

- [ ] Zero `CRITICAL_*` flags (same or fewer than baseline)
- [ ] No `FUZZ_CRASH` events
- [ ] No existing `bpy.props` renamed or removed
- [ ] `get_slot_meta()` covers all face slot indices used in `build_shape`
- [ ] `draw_shape_ui` reflects any newly added properties
- [ ] UV islands within 0–1 bounds when `fit_uvs = True`
- [ ] Backup file removed (or noted if kept for versioning)

Report: what was found, what was changed, audit result before and after.
