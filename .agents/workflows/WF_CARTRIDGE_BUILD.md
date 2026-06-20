---
description: Create a New Geometry Cartridge from Scratch
---

# WF_CARTRIDGE_BUILD — Create a New Cartridge from Scratch

Use this workflow when tasked with adding a new geometry generator to `massa/modules/cartridges/`.

> **Read first:** `docs/blender-addon-docs/CARTRIDGE_MANDATE.md` and `AGENTS.md` (root) before writing any code.

---

## Phase 0 — Pre-Flight

**Verify the environment is ready:**

1. Confirm `BLENDER_PATH` is set correctly in `massa/modules/debugging_system/config.py`.
2. Confirm the `massa/modules/cartridges/` folder exists and is writable.
3. Identify the cartridge's category prefix (`prim_`, `arc_`, `urb_`, `ind_`, `asm_`, `arch_`).
4. Choose a file name: `cart_<category>_<NN>_<descriptor>.py` (e.g. `cart_prim_07_bracket.py`).

---

## Phase 1 — Archetype Selection

**Read a Golden Reference cartridge that is structurally similar to your target.**

| Shape Type | Read This First |
| :--- | :--- |
| Linear extrusions, profiles | `cart_prim_01_beam.py` |
| Panels, flat slabs, openings | `cart_prim_04_panel.py` |
| Catenary curves, arrays | `cart_prim_05_catenary.py` |
| Helical / rotational geometry | `cart_prim_11_helix.py` |

Run a read on the reference file. Note: class name, CARTRIDGE_META structure, slot definitions, edge tagging style, and UV strategy used.

---

## Phase 2 — File Scaffold

Create the new cartridge file with this structure **in order**:

```python
# =============================================================
#  MASSA Cartridge — <Descriptive Name>
#  Category: <CATEGORY>  |  ID: <cart_id>
# =============================================================
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name":       "<Display Name>",
    "id":         "<cart_id>",           # matches filename stem
    "icon":       "MESH_CUBE",           # valid Blender icon name
    "scale_class": "MEDIUM",            # MICRO / SMALL / MEDIUM / LARGE / MEGA
    "flags": {
        "has_sockets":    False,
        "has_physics":    True,
        "is_symmetric":   True,
    }
}

class MASSA_OT_<ClassName>(Massa_OT_Base):
    bl_idname  = "massa.<cart_id>"
    bl_label   = "<Display Name>"
    bl_options = {"REGISTER", "UNDO"}

    # --- Cartridge-local properties ---
    width:  bpy.props.FloatProperty(name="Width",  default=1.0, min=0.01, max=100.0)
    height: bpy.props.FloatProperty(name="Height", default=1.0, min=0.01, max=100.0)
    # ... add more as needed

    def get_slot_meta(self):
        return {
            "0": {"name": "Base",   "uv": "BOX",  "phys": "METAL_STEEL"},
            "1": {"name": "Detail", "uv": "BOX",  "phys": "METAL_STEEL"},
            # Add only the slots your geometry actually uses (0-9)
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")

    def build_shape(self, bm):
        # --- PHASE 2: Build geometry here ---
        pass

def get_slot_meta():
    return MASSA_OT_<ClassName>().get_slot_meta()
```

---

## Phase 3 — Geometry (`build_shape`)

**Rules for writing `build_shape(self, bm)`:**

- Use only `bmesh.ops`, `mathutils`, and pure Python math. **No `bpy.ops`.**
- No loose vertices. Every vertex must belong to at least one face.
- No zero-area faces. Check all extrusions and bridge calls.
- Use `MassaBuilder` for repetitive operations when available (see `WORKFLOW_BUILDER.md`).

**Edge Slot tagging** — create the layer and tag edges before returning:

```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") \
             or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

for e in bm.edges:
    # Tag based on geometry role:
    # 1 = Perimeter  (silhouette, end caps, seam + sharp + bevel)
    # 2 = Contour    (hard internal angles, sharp + bevel)
    # 3 = Guide      (UV seam cuts only — cylinders, tubes)
    # 4 = Detail     (bevel only, soft chamfers)
    # 5 = Fold       (crease / subdivision weight)
    if <is_silhouette_edge>:
        e[edge_slots] = 1
```

**UV strategy guidance per slot UV type:**

| UV Type | When to Use |
| :--- | :--- |
| `"SKIP"` | You are writing manual UVs in `build_shape`. Golden Cartridges use this. |
| `"BOX"` | Simple box-mapping is acceptable (auto, no manual math). |
| `"UNWRAP"` | Auto-unwrap using seams defined by edge slots 1 and 3. |
| `"FIT"` | Auto-fit UV islands to 0-1 space after unwrap. |

**If writing manual UVs (`"SKIP"`)** — assign the `uv_layer` directly in `build_shape`:

```python
uv_layer = bm.loops.layers.uv.verify()
for face in bm.faces:
    for loop in face.loops:
        loop[uv_layer].uv = Vector((u, v))  # your math here
```

**Face slot assignment** — every face must have a material_index matching your `get_slot_meta()` keys:

```python
slot_layer = bm.faces.layers.int.get("MASSA_SLOT") \
             or bm.faces.layers.int.new("MASSA_SLOT")
for f in bm.faces:
    f[slot_layer] = 0   # or 1, 2, ... per face role
```

---

## Phase 4 — Slot Definition

Complete `get_slot_meta()` — one entry per slot index actually used by your geometry.

**Slot name → role reference:**

| Index | Role | Phys Tag | Notes |
| :--- | :--- | :--- | :--- |
| 0 | BASE | `METAL_STEEL` / `CONCRETE` / etc. | Primary surface |
| 1 | DETAIL | `METAL_STEEL` | Secondary features |
| 2 | TRIM | `METAL_CHROME` | Edges, rails, borders |
| 3 | GLASS | `GLASS_CLEAR` | Transparent panels |
| 4 | EMISSION | `EMISSION` | Glowing/light surfaces |
| 5 | DARK | `RUBBER` | Dark/matte insets |
| 6 | ACCENT | `METAL_PAINTED` | Color accent faces |
| 7 | UTILITY | `PLASTIC_HARD` | Functional surfaces |
| 8 | TRANSPARENT | `GLASS_TINTED` | Semi-transparent |
| 9 | SOCKET | `SOCKET` | Snap/connection points |

Only define the indices your cartridge actually assigns. Unused slots can be omitted.

---

## Phase 5 — Audit Loop

Run the audit and fix all flags before considering the cartridge done.

**Step 1 — Standard geometry audit:**

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<your_file>.py \
  --mode AUDIT
```

Parse the JSON between `---AUDIT_START---` and `---AUDIT_END---`. Fix every `CRITICAL_` flag. Fuzz testing runs automatically — fix any `FUZZ_CRASH` flags too.

**Step 2 — UV heatmap (if slots use UNWRAP or SKIP with manual UVs):**

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<your_file>.py \
  --mode UV_HEATMAP
```

Red = bad stretching. Rework seam placement or UV math until majority is blue/green.

**Step 3 — UV layout inspect:**

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<your_file>.py \
  --mode UV_INSPECT
```

Check for: overlapping islands, out-of-bounds geometry, collapsed islands. Fix and re-run.

**Repeat steps 1-3 until zero `CRITICAL_` flags remain.**

---

## Phase 6 — Delivery Checklist

Before the cartridge is considered complete:

- [ ] Zero `CRITICAL_` flags in AUDIT mode
- [ ] Zero `FUZZ_CRASH` events under parameter randomization
- [ ] UV heatmap shows no red zones (or SKIP slots have verified manual UVs)
- [ ] All face `material_index` values match defined `get_slot_meta()` keys
- [ ] All edge slots tagged (or auto-detection confirmed sufficient via `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` absence)
- [ ] `CARTRIDGE_META` is complete (`name`, `id`, `icon`, `scale_class`, `flags`)
- [ ] File placed in `massa/modules/cartridges/` (auto-registers on Blender reload)

---

## Common Issues & Fixes

| Flag | Cause | Fix |
| :--- | :--- | :--- |
| `CRITICAL_EMPTY_MESH` | `build_shape` returned without creating geometry | Check logic flow and early returns |
| `CRITICAL_ZERO_AREA_FACES_N` | Extrusion collapsed / bridge on coincident verts | Add distance checks; use `bmesh.ops.remove_doubles` |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | >12 faces, zero edge slot 1 or 3 tagged | Tag silhouette edges as role 1 (Perimeter) |
| `CRITICAL_MISSING_UV_LAYER` | Slot uses `UNWRAP` but engine couldn't unwrap | Ensure seams exist; or switch to `BOX` |
| `CRITICAL_LOOSE_VERTS_N` | Orphan vertices from aborted operations | Call `bmesh.ops.delete` to clean up |
| `FUZZ_CRASH` | Parameter edge case crashes `build_shape` | Add `max(0.01, self.width)` guards; check divide-by-zero |
