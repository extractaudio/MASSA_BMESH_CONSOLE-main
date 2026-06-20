---
description: Run Audits and Fix All Flags
---

# WF_FLASH_AUDIT — Audit and Fix

**Use when:** You need to run audits, parse results, or fix flags.
**This workflow is also called from:** `WF_FLASH_BUILD` (Step 4) and `WF_FLASH_MODIFY` (Steps 1 and 3).

---

## Audit Commands

### Standard Geometry Audit (always run this first)
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode AUDIT
```

### UV Heatmap (run when UV quality is in question)
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode UV_HEATMAP
```

### UV Layout Inspect (run after heatmap)
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode UV_INSPECT
```

### Visual Diff (run when comparing two versions)
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "massa/modules/cartridges/<CARTRIDGE_B>.py"}'
```

---

## Parsing Audit Output

Output is JSON. Extract the block between these markers:

```
---AUDIT_START---
{ ... JSON ... }
---AUDIT_END---
```

Flags starting with `CRITICAL_` → **must fix before delivery**.
Flags starting with `WARNING_` → should fix if possible.

---

## CRITICAL Flag Fix Table

| Flag | Exact Fix |
| :--- | :--- |
| `CRITICAL_EMPTY_MESH` | `build_shape` has bad early return or never creates geometry — trace execution and fix |
| `CRITICAL_FLAT_Z_AXIS` | Extrusion/translation on Z is zero — add `max(0.001, dist)` guard |
| `CRITICAL_MISSING_SLOT_LAYER` | Add at start of `build_shape`: `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` |
| `CRITICAL_NO_PERIMETER_DEFINED` | Tag silhouette/end-cap edges: `e[edge_slots] = 1` |
| `CRITICAL_LOOSE_VERTS_N` | Find and delete: `bmesh.ops.delete(bm, geom=<list of loose verts>, context='VERTS')` |
| `CRITICAL_NON_MANIFOLD_N` | Find open holes or T-junctions; use `bmesh.ops.fill` or fix bridge logic |
| `CRITICAL_ZERO_AREA_FACES_N` | Add distance guard before extrusion; or clean with `bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)` |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | Mesh has >12 faces with no role 1 or 3 edges — tag silhouette edges with `e[edge_slots] = 1` |
| `CRITICAL_MISSING_UV_LAYER` | Slot uses `UNWRAP` but no seams exist — add role 1/3 edge tags, then re-audit |
| `CRITICAL_ZERO_UV_DATA` | UV layer exists but all at (0,0) — check `get_slot_meta` UV strategy; switch to `"BOX"` or add manual UV math |
| `CRITICAL_INVERTED_NORMALS` | Add: `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` |
| `CRITICAL_SELF_INTERSECTION` | Boolean or extrusion overlap — check geometry logic |
| `CRITICAL_UV_SPIKES_N` | Fix topology first (zero-area faces), then re-run UV audit |
| `CRITICAL_COLLAPSED_UVS_N` | Check for zero-area faces in UV space; fix geometry and re-audit |
| `FUZZ_CRASH` | Add `max(0.001, self.prop)` on every numeric property used in build; check for divide-by-zero |

---

## WARNING Flag Fix Table

| Flag | Fix |
| :--- | :--- |
| `WARNING_THIN_FACES_N` | Rebuild affected edge loops — sliver faces cause UV and bevel artifacts |
| `WARNING_MISSING_EDGE_SLOTS_LAYER` | Layer exists but no edges assigned — tag at least silhouette edges with role 1 |
| `WARNING_ISOLATED_SEAM_EDGES_N` | Seam edges are disconnected — ensure seam loops are continuous |

---

## Fix Loop Protocol

1. Run AUDIT.
2. Read all `CRITICAL_` flags from the JSON output.
3. Fix the first flag in the table above.
4. Run AUDIT again.
5. Confirm that flag is gone.
6. Repeat from step 2 until zero `CRITICAL_` flags remain.

**Do not batch multiple flag fixes at once unless they are clearly unrelated.** Fixing one bug can resolve others; fixing all at once can introduce new ones.

---

## Edge Role Quick Reference

```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") \
             or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

# Set role on a specific edge:
e[edge_slots] = 1   # Perimeter  — seam + sharp + bevel (silhouettes, end caps)
e[edge_slots] = 2   # Contour    — sharp + bevel (hard internal angles, no seam)
e[edge_slots] = 3   # Guide      — seam only (cylinder longitudinals, UV cuts)
e[edge_slots] = 4   # Detail     — bevel only (soft chamfers)
e[edge_slots] = 5   # Fold       — crease only (subdivision weight)
```

---

## Face Slot Quick Reference

```python
slot_layer = bm.faces.layers.int.get("MASSA_SLOT") \
             or bm.faces.layers.int.new("MASSA_SLOT")

f[slot_layer] = 0   # BASE       — METAL_STEEL (primary surface, required)
f[slot_layer] = 1   # DETAIL     — METAL_STEEL (secondary features)
f[slot_layer] = 2   # TRIM       — METAL_CHROME (edges, rails)
f[slot_layer] = 3   # GLASS      — GLASS_CLEAR
f[slot_layer] = 4   # EMISSION   — EMISSION (glowing)
f[slot_layer] = 5   # DARK       — RUBBER (matte insets)
f[slot_layer] = 6   # ACCENT     — METAL_PAINTED
f[slot_layer] = 7   # UTILITY    — PLASTIC_HARD
f[slot_layer] = 8   # TRANSPARENT — GLASS_TINTED
f[slot_layer] = 9   # SOCKET     — SOCKET
```

---

## Live Blender Inspection (if audit runner is unavailable)

```bash
# List all objects in scene
python modules/debugging_system/debug_agent.py \
  --code "import bpy; print(list(bpy.data.objects.keys()))"

# Check MASSA_PARAMS on an object
python modules/debugging_system/debug_agent.py \
  --code "import bpy; o=bpy.data.objects['MyObj']; print(o.get('MASSA_PARAMS', 'not found'))"

# List registered MASSA operators
python modules/debugging_system/debug_agent.py \
  --code "import bpy; print([t.bl_idname for t in bpy.types.Operator.__subclasses__() if 'massa' in t.bl_idname.lower()])"
```
