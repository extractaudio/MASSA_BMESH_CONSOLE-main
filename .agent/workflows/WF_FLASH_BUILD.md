---
description: Create a New Cartridge from Scratch
---

# WF_FLASH_BUILD — New Cartridge

**Use when:** The cartridge file does not exist yet.
**Do not use when:** The file exists — use `WF_FLASH_MODIFY.md`.

---

## STEP 0 — Pre-Flight Gates

Run each check. STOP if any fails.

| Check | Command / Action | Pass Condition |
| :--- | :--- | :--- |
| Blender path set | Read `modules/debugging_system/config.py` | `BLENDER_PATH` is a non-empty string |
| Cartridge folder exists | List `massa/modules/cartridges/` | Folder present |
| File does not exist | Check target filename | File is absent |

**Choose filename:** `cart_<prefix>_<NN>_<descriptor>.py`
Prefixes: `prim_` `arc_` `urb_` `ind_` `asm_` `arch_`

---

## STEP 1 — Read One Reference Cartridge

Pick the closest shape type. Read that file completely before writing anything.

| Shape | Read This File |
| :--- | :--- |
| Linear extrusion / profile | `massa/modules/cartridges/cart_prim_01_beam.py` |
| Flat panel / slab | `massa/modules/cartridges/cart_prim_04_panel.py` |
| Curve / catenary / array | `massa/modules/cartridges/cart_prim_05_catenary.py` |
| Helix / rotational / cylinder | `massa/modules/cartridges/cart_prim_11_helix.py` |

Capture from the reference: class name pattern, `CARTRIDGE_META` structure, edge tagging style, UV strategy used. Do not copy geometry logic — only structure.

---

## STEP 2 — Write the Scaffold

Create the new file. Use this **exact** structure. Replace all `<PLACEHOLDER>` values.

```python
# =============================================================
#  MASSA Cartridge — <DESCRIPTIVE NAME>
#  Category: <CATEGORY>  |  ID: <cart_id>
# =============================================================
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name":        "<Display Name>",
    "id":          "<cart_id>",
    "icon":        "MESH_CUBE",
    "scale_class": "MEDIUM",
    "flags": {
        "has_sockets":  False,
        "has_physics":  True,
        "is_symmetric": True,
        "ALLOW_CHAMFER": True,
        "USE_WELD":      False,
        "ALLOW_SOLIDIFY": False,
    }
}

class MASSA_OT_<ClassName>(Massa_OT_Base):
    bl_idname    = "massa.<cart_id>"
    bl_label     = "<Display Name>"
    bl_description = "<One sentence describing what this shape is>"
    bl_options   = {"REGISTER", "UNDO"}

    # --- Properties ---
    width:  bpy.props.FloatProperty(name="Width",  default=1.0, min=0.01, max=100.0)
    height: bpy.props.FloatProperty(name="Height", default=1.0, min=0.01, max=100.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Base",   "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Detail", "uv": "BOX", "phys": "METAL_STEEL"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Shape")
        col.prop(self, "width")
        col.prop(self, "height")

    def build_shape(self, bm):
        pass  # geometry goes here

def get_slot_meta():
    return MASSA_OT_<ClassName>().get_slot_meta()
```

---

## STEP 3 — Write `build_shape`

Fill in the `build_shape(self, bm)` method. Apply every rule below.

### Forbidden inside `build_shape`

- `bpy.ops.*` — use `bmesh.ops` instead
- `bpy.context.*` — use parameters passed to the function
- Returning early without creating geometry (causes `CRITICAL_EMPTY_MESH`)

### Required patterns

**Guard every numeric property used as a dimension or divisor:**

```python
width  = max(0.01, self.width)
height = max(0.01, self.height)
segs   = max(3, self.segments)
```

**Create the edge slot layer and tag edges before returning:**

```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") \
             or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

for e in bm.edges:
    if <is_silhouette_or_end_cap>:
        e[edge_slots] = 1  # Perimeter — seam + sharp + bevel
    elif <is_hard_internal_angle>:
        e[edge_slots] = 2  # Contour — sharp + bevel
    elif <is_uv_cut_line>:
        e[edge_slots] = 3  # Guide — seam only
```

**Assign face slot indices:**

```python
slot_layer = bm.faces.layers.int.get("MASSA_SLOT") \
             or bm.faces.layers.int.new("MASSA_SLOT")
for f in bm.faces:
    f[slot_layer] = 0  # or 1, 2, ... matching get_slot_meta keys
```

**Edge role values:**

| ID | Name | Effect |
| :--- | :--- | :--- |
| 1 | Perimeter | Seam + Sharp + Bevel |
| 2 | Contour | Sharp + Bevel (no seam) |
| 3 | Guide | Seam only (UV cuts) |
| 4 | Detail | Bevel only |
| 5 | Fold | Crease only |

---

## STEP 4 — Run the Audit Gate

```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode AUDIT
```

Parse JSON between `---AUDIT_START---` and `---AUDIT_END---`.

**Fix every `CRITICAL_` flag before proceeding.**
See `WF_FLASH_AUDIT.md` for the complete flag → fix table.
Repeat until the audit returns zero `CRITICAL_` flags.

---

## STEP 5 — UV Verification (if slots use UNWRAP or manual SKIP)

```bash
# Heatmap — Red = bad distortion, Blue = good
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode UV_HEATMAP

# Layout — check for overlaps and out-of-bounds
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode UV_INSPECT
```

Fix if: any red zones in heatmap, any islands outside 0-1 square, any overlapping islands.

---

## STEP 6 — Delivery Checklist

Every item must be YES before the task is complete.

- [ ] Zero `CRITICAL_` flags in AUDIT
- [ ] Zero `FUZZ_CRASH` events
- [ ] All `bpy.props` exposed in `draw_shape_ui`
- [ ] All face `material_index` values match `get_slot_meta` keys
- [ ] Edge slots tagged (or complex mesh <12 faces confirmed)
- [ ] All `FloatProperty` divisors have `max(0.001, ...)` guards
- [ ] `CARTRIDGE_META` complete: `name`, `id`, `icon`, `scale_class`, `flags`
- [ ] `bl_description` is a non-empty string
- [ ] File is in `massa/modules/cartridges/`
