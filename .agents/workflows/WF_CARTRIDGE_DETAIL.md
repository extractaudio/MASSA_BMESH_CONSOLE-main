---
description: Detail and Complete an Existing Geometry Cartridge
---

# WF_CARTRIDGE_DETAIL — Detail and Complete an Existing Cartridge

Use this workflow when tasked with enriching a cartridge that already exists and generates valid geometry, but is **incomplete** — missing parameters, undocumented slots, unexposed UI controls, or lacking the guard/description quality expected of a mature cartridge.

> **This is not a repair workflow.** If the cartridge has `CRITICAL_` flags or crashes, use `WF_CARTRIDGE_MODIFY` first. Detailing assumes a structurally valid cartridge as the baseline.

> **Never overwrite a cartridge without reading it first.**

---

## Phase 0 — Full Read and Inventory

Read the entire cartridge file and build an inventory before touching anything.

**Capture the following:**

1. **`CARTRIDGE_META`** — record `id`, `name`, `icon`, `scale_class`, all `flags` keys present.
2. **All `bpy.props`** — list every property: name, type, default, min/max, `description` (if any).
3. **`get_slot_meta()`** — list every slot index, its `name`, `uv` strategy, and `phys` tag.
4. **`build_shape()`** — note: which face indices are assigned via `f[slot_layer]`, which edge roles are tagged, and which properties are actually consumed by the geometry.
5. **`draw_shape_ui()`** — list every `col.prop` / `row.prop` / `box.prop` call. Note any properties defined in `bpy.props` that do **not** appear in the UI.
6. **`bl_description`** on the operator class — present or absent?

Run a baseline AUDIT to confirm no pre-existing flags:

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode AUDIT
```

Record the baseline flag list. You must not introduce new flags.

---

## Phase 1 — Classify the Cartridge Shape Type

Identify the cartridge's shape category. This determines which "expected parameter checklist" applies.

| Shape Category | Identifying Traits | Go To |
| :--- | :--- | :--- |
| **Linear Extrusion** | Profiled cross-section swept along an axis | Phase 2A |
| **Panel / Slab** | Flat planar surface with optional cutouts/openings | Phase 2B |
| **Rotational / Radial** | Lathe, helix, pipe, cylinder, column | Phase 2C |
| **Array / Repeat** | Chain, truss, louver, scale — count-based repetition | Phase 2D |
| **Connector / Detail** | Gusset, bolt, bracket, socket — small mechanical part | Phase 2E |
| **Organic / Terrain** | Rock, landscape, shard — irregular natural form | Phase 2F |

A cartridge may fit two categories (e.g. a corrugated panel is both Panel and Array). Apply both checklists.

---

## Phase 2A — Expected Parameters: Linear Extrusion

Cross-reference the cartridge's existing props against this expected set. Note every gap.

| Parameter | Type | Typical Default | Purpose |
| :--- | :--- | :--- | :--- |
| `width` | `FloatProperty` | 0.2, min=0.01 | Cross-section X extent |
| `height` | `FloatProperty` | 0.4, min=0.01 | Cross-section Z extent |
| `length` | `FloatProperty` | 3.0, min=0.1 | Extrusion Y axis |
| `thickness` | `FloatProperty` | 0.02, min=0.002 | Wall thickness for hollow profiles |
| `segments_y` | `IntProperty` | 0, min=0, soft_max=50 | Length-axis topology divisions |
| `uv_scale` | `FloatProperty` | 1.0, min=0.1 | Uniform UV scale multiplier |
| `fit_uvs` | `BoolProperty` | False | Pack UV islands into 0-1 space |
| `taper` | `FloatProperty` | 0.0, min=0.0 | Optional end-taper ratio |

**Also verify:** Does `build_shape` use `max(0.001, self.length)` or equivalent guard on the extrusion axis?

---

## Phase 2B — Expected Parameters: Panel / Slab

| Parameter | Type | Typical Default | Purpose |
| :--- | :--- | :--- | :--- |
| `width` | `FloatProperty` | 1.0, min=0.01 | Panel X size |
| `height` | `FloatProperty` | 1.0, min=0.01 | Panel Z/Y size |
| `depth` | `FloatProperty` | 0.05, min=0.001 | Panel thickness |
| `segments_x` | `IntProperty` | 1, min=1, max=32 | Width-axis topology divisions |
| `segments_y` | `IntProperty` | 1, min=1, max=32 | Height-axis topology divisions |
| `uv_scale` | `FloatProperty` | 1.0, min=0.1 | UV tile frequency |
| `inset` | `FloatProperty` | 0.0, min=0.0 | Optional face-inset offset for frame detail |

---

## Phase 2C — Expected Parameters: Rotational / Radial

| Parameter | Type | Typical Default | Purpose |
| :--- | :--- | :--- | :--- |
| `radius` | `FloatProperty` | 0.5, min=0.001 | Outer radius (or use `outer_radius` / `inner_radius`) |
| `height` | `FloatProperty` | 1.0, min=0.001 | Axial extent |
| `segments` | `IntProperty` | 16, min=3, max=128 | Circumferential divisions |
| `segments_h` | `IntProperty` | 1, min=1, max=64 | Height-axis divisions |
| `uv_scale` | `FloatProperty` | 1.0, min=0.1 | UV scale |
| `end_caps` | `BoolProperty` | True | Whether top/bottom caps are generated |
| `cap_type` | `EnumProperty` | `("FLAT", "NGON", "FAN")` | Cap triangulation style |

---

## Phase 2D — Expected Parameters: Array / Repeat

| Parameter | Type | Typical Default | Purpose |
| :--- | :--- | :--- | :--- |
| `count` | `IntProperty` | 4, min=1, max=200 | Number of repeated elements |
| `spacing` | `FloatProperty` | 1.0, min=0.001 | Gap or center-to-center distance |
| `offset_x/y/z` | `FloatProperty` | 0.0 | Stagger per element on respective axis |
| `scale_x/y` | `FloatProperty` | 1.0, min=0.001 | Per-element scale factor |
| `alternate` | `BoolProperty` | False | Flip/mirror every second element |

---

## Phase 2E — Expected Parameters: Connector / Detail

| Parameter | Type | Typical Default | Purpose |
| :--- | :--- | :--- | :--- |
| `thickness` | `FloatProperty` | 0.005, min=0.001 | Plate / wall thickness |
| `corner_radius` | `FloatProperty` | 0.01, min=0.0 | Fillet radius at corners |
| `has_holes` | `BoolProperty` | True | Toggle bolt holes |
| `hole_radius` | `FloatProperty` | 0.008, min=0.001 | Hole radius |
| `resolution` | `IntProperty` | 16, min=4, max=64 | Hole / curve polygon resolution |
| `uv_scale` | `FloatProperty` | 1.0, min=0.1 | UV scale |

---

## Phase 2F — Expected Parameters: Organic / Terrain

| Parameter | Type | Typical Default | Purpose |
| :--- | :--- | :--- | :--- |
| `scale_x/y/z` | `FloatProperty` | 1.0, min=0.001 | Non-uniform scale axes |
| `seed` | `IntProperty` | 0, min=0 | Randomization seed |
| `noise_scale` | `FloatProperty` | 1.0, min=0.001 | Noise frequency for displacement |
| `noise_strength` | `FloatProperty` | 0.2, min=0.0 | Displacement magnitude |
| `subdivisions` | `IntProperty` | 2, min=0, max=6 | Base subdivision level |
| `flatten_base` | `BoolProperty` | True | Snap bottom verts to ground plane |

---

## Phase 3 — Audit Completeness: Five Checks

Run each check in order and build a gap list.

### Check 1 — CARTRIDGE_META flags completeness

Expected `flags` keys for most cartridges:

```
ALLOW_SOLIDIFY   — bool: whether the Polish stack may add solidify modifier
USE_WELD         — bool: weld overlapping vertices after generation
ALLOW_CHAMFER    — bool: whether chamfer/bevel may be applied post-generation
has_sockets      — bool: whether this cartridge generates socket anchor faces
has_physics      — bool: whether physics tags on slots are meaningful
is_symmetric     — bool: whether geometry is symmetric (enables mirror optimization)
```

Note any flags absent from the current `CARTRIDGE_META["flags"]` that are relevant to the shape.

### Check 2 — Slot coverage completeness

Build two sets:
- **Declared slots**: all keys in `get_slot_meta()`
- **Used slots**: all unique `f[slot_layer] = N` values assigned in `build_shape()`

**Gaps to fix:**
- Slots used in `build_shape` but missing from `get_slot_meta()` → add slot entry
- Slots in `get_slot_meta()` that are never assigned in `build_shape` → mark as unused or remove

### Check 3 — UI exposure completeness

Build two sets:
- **Defined props**: all property names declared in the operator class
- **Exposed props**: all property names referenced in `draw_shape_ui()`

**Gaps to fix:**
- Props defined but not in UI → add `col.prop(self, "prop_name")` under the appropriate section label
- Props in UI but referencing names not defined → fix typos or add the missing prop definition

### Check 4 — Guard completeness

Scan `build_shape()` for every `self.<prop>` usage. Verify:
- Every `FloatProperty` used as a divisor has a `max(0.001, self.prop)` guard
- Every `IntProperty` used as a loop count has a `max(1, self.prop)` guard
- Every extrusion distance has a minimum value guard

### Check 5 — Description completeness

Verify:
- `bl_description` is present on the operator class (non-empty string describing what the shape is)
- Each `bpy.props` definition has a non-empty `name` (displayed in UI tooltips)
- Critical props have a `description="..."` argument (shown on hover in Blender)

---

## Phase 4 — Adding Missing Parameters

For each gap identified in Phase 2 and Phase 3, add the missing parameter following these rules:

**Rule: Never rename existing props.** Only add new ones. The Resurrection system replays values by name from `obj["MASSA_PARAMS"]`.

**Adding a new prop — required steps in order:**

1. Add the `bpy.props` definition to the operator class with appropriate `name`, `default`, `min`/`max`, and optionally `description`:

```python
# Example: adding a missing 'segments' param to a rotational cartridge
segments: bpy.props.IntProperty(
    name="Segments",
    description="Circumferential polygon count",
    default=16, min=3, max=128
)
```

2. Reference `self.segments` in `build_shape()` where the parameter is geometrically consumed. Replace any hard-coded literal it replaces.

3. Add a corresponding `col.prop(self, "segments")` in `draw_shape_ui()` under the appropriate section label.

4. If the new parameter can cause zero-division or degenerate geometry at edge values, add a guard in `build_shape()`:

```python
segs = max(3, self.segments)
```

**Adding a missing CARTRIDGE_META flag:**

```python
CARTRIDGE_META = {
    ...
    "flags": {
        ...
        "ALLOW_CHAMFER": True,   # newly added
    }
}
```

**Adding a missing slot to `get_slot_meta()`:**

```python
def get_slot_meta(self):
    return {
        ...
        2: {"name": "Trim Edge", "uv": "BOX", "phys": "METAL_CHROME"},  # newly added
    }
```

---

## Phase 5 — Comparing Against a Similar Reference Cartridge

After Phase 4 additions, compare the updated cartridge against a Golden Reference of the same shape category. See `WF_AUDIT_REFERENCE.md` for the Golden Reference list.

Run a side-by-side property inventory:

1. Read the reference cartridge.
2. List its `bpy.props`.
3. For each prop in the reference that is semantically applicable to the target cartridge and still absent: decide — add it, or document why it was intentionally omitted.

**Do not blindly copy all reference props.** Only add props that are genuinely applicable to the shape. A louver blade should not have `hole_radius` just because a gusset does.

---

## Phase 6 — Final Verification

After all additions:

```bash
# Full geometry audit — must match or improve baseline flag count
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode AUDIT

# UV check (run if any slot UV strategy or new geometry was added)
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode UV_INSPECT

# UI auditor (validates draw_shape_ui prop references match defined props)
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode AUDIT
```

Parse the JSON output between `---AUDIT_START---` and `---AUDIT_END---`. Fix any new `CRITICAL_` flags introduced by detailing work before marking the task complete.

---

## Delivery Checklist

- [ ] Zero `CRITICAL_` flags (same or fewer than baseline)
- [ ] All bpy.props shape-category expected parameters are present (or intentional omissions noted)
- [ ] Every prop in the operator class is exposed in `draw_shape_ui()`
- [ ] Every slot index used in `build_shape()` is declared in `get_slot_meta()`
- [ ] No declared slots are unreachable dead code (assign or remove)
- [ ] All `FloatProperty` divisors and `IntProperty` loop counts have guards in `build_shape()`
- [ ] `bl_description` is present and non-empty on the operator class
- [ ] All new props have `name` and optionally `description` arguments
- [ ] `CARTRIDGE_META["flags"]` includes all relevant flag keys
- [ ] No existing `bpy.props` were renamed or removed
- [ ] `draw_shape_ui` uses `layout.separator()` and section labels to group related params visually
- [ ] `get_slot_meta()` keys are integers, not strings (unless legacy — do not change format if uncertain)
