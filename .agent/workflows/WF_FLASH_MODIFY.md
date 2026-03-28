---
description: Fix, Edit, or Extend an Existing Cartridge
---

# WF_FLASH_MODIFY — Modify Existing Cartridge

**Use when:** The cartridge file already exists and needs changes.
**Do not use when:** The file does not exist — use `WF_FLASH_BUILD.md`.

---

## STEP 0 — Read the File (Mandatory)

**Read the entire cartridge file before writing a single character.**

```
File location: massa/modules/cartridges/<CARTRIDGE>.py
```

Capture and record:
1. Class name and `bl_idname`
2. Every `bpy.props` property name and its default value
3. All keys in `get_slot_meta()` — which indices, UV strategy for each
4. All `f[slot_layer] = N` assignments in `build_shape()`
5. All `e[edge_slots] = N` assignments in `build_shape()`
6. Every `col.prop(self, "name")` call in `draw_shape_ui()`

---

## STEP 1 — Baseline Audit

Run immediately after reading. Record all flags.

```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode AUDIT
```

**Record baseline flags.** You must not introduce new `CRITICAL_` flags.
If the baseline already has `CRITICAL_` flags, fix those first before the requested change.

---

## STEP 2 — Classify the Change

Pick **one** category. Follow only that section.

| Category | Indicators | Go To |
| :--- | :--- | :--- |
| Bug / crash | Exception, `FUZZ_CRASH`, error on generate | §A |
| Topology flags | `CRITICAL_*` in audit output | §B |
| UV / surface flags | `CRITICAL_UV_*`, red heatmap | §C |
| Add a new property | Adding new `bpy.props` | §D |
| UI change only | `draw_shape_ui` layout | §E |
| Geometry shape change | Adjusting segments, proportions, profile | §F |

---

### §A — Bug / Crash Fix

1. Read the traceback. Identify the error type:
   - Python syntax → fix syntax
   - `RuntimeError: Operator called from wrong context` → replace `bpy.ops.*` with `bmesh.ops.*`
   - Division by zero → add `max(0.001, self.prop)` guard
   - Missing attribute → check import and class inheritance

2. Apply the minimal fix.

3. Run AUDIT. Confirm no new flags.

**Forbidden fixes:**
- Do not replace `bpy.ops` with other `bpy.ops` calls — use `bmesh.ops`
- Do not rename properties to fix a bug

---

### §B — Topology Flag Fix

Look up your flag in this table. Apply the exact fix.

| Flag | Fix |
| :--- | :--- |
| `CRITICAL_EMPTY_MESH` | `build_shape` has bad early return — trace execution path and fix |
| `CRITICAL_FLAT_Z_AXIS` | Extrusion distance is zero — add `max(0.001, dist)` guard |
| `CRITICAL_MISSING_SLOT_LAYER` | Add: `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` |
| `CRITICAL_NO_PERIMETER_DEFINED` | Tag silhouette/end-cap edges with `e[edge_slots] = 1` |
| `CRITICAL_LOOSE_VERTS_N` | `bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')` |
| `CRITICAL_NON_MANIFOLD_N` | Check for open holes or T-junctions; use `bmesh.ops.fill` |
| `CRITICAL_ZERO_AREA_FACES_N` | Find collapsed extrusions; add distance guard or `bmesh.ops.dissolve_degenerate` |
| `WARNING_THIN_FACES_N` | Rebuild affected edge loops with better topology |

After each fix, re-run AUDIT. Confirm the specific flag is gone.

---

### §C — UV / Surface Flag Fix

**Step 1 — Run UV heatmap:**
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode UV_HEATMAP
```

**Step 2 — Run UV layout:**
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode UV_INSPECT
```

**Diagnose:**

| Problem | Fix |
| :--- | :--- |
| All UVs at (0,0) / `CRITICAL_ZERO_UV_DATA` | Change slot `"uv"` from `"SKIP"` to `"BOX"` in `get_slot_meta`, or add manual UV math |
| `CRITICAL_MISSING_UV_LAYER` | Ensure seams exist (edge role 1 or 3), then switch to `"UNWRAP"` |
| Overlapping islands | Tag more edges with role 1 (Perimeter) or 3 (Guide) |
| Islands outside 0-1 space | Normalize UV coordinates in `build_shape` |
| `CRITICAL_INVERTED_NORMALS` | Add: `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` |
| `CRITICAL_UV_SPIKES_N` | Fix topology first (§B), then re-audit UV |

**UV strategy values for `get_slot_meta`:**
- `"BOX"` — auto box-map, no manual work
- `"UNWRAP"` — auto-unwrap using role 1/3 seams
- `"FIT"` — unwrap then pack to 0-1
- `"SKIP"` — manual UV math must exist in `build_shape`

---

### §D — Add a New Property

**Rules before adding:**
- Never rename an existing property
- Never remove an existing property
- New property names must not conflict with any existing name

**Required steps in order:**

1. Add `bpy.props` definition to the operator class:
```python
my_param: bpy.props.FloatProperty(
    name="My Param",
    description="What this does",
    default=1.0, min=0.01, max=100.0
)
```

2. Use `self.my_param` in `build_shape`. Add a guard:
```python
my_param = max(0.01, self.my_param)
```

3. Add to `draw_shape_ui`:
```python
col.prop(self, "my_param")
```

4. Run AUDIT. Confirm no new flags.

---

### §E — UI Change

Rules for `draw_shape_ui(self, layout)`:
- Use `layout.column(align=True)` for grouped controls
- Use `layout.separator()` between logical groups
- Use `col.label(text="Section Name")` for section headers
- **Never** call `layout.operator()` inside `draw_shape_ui`
- Every `col.prop(self, "name")` must reference a defined `bpy.props` on the class

---

### §F — Geometry Shape Change

1. Make the smallest targeted change possible.
2. Run visual diff against the original:
```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "massa/modules/cartridges/<CARTRIDGE_ORIGINAL>.py"}'
```
3. Run AUDIT. Confirm no regressions.

---

## STEP 3 — Final Verification

Run after all changes regardless of category:

```bash
python modules/debugging_system/runner.py \
  --cartridge massa/modules/cartridges/<CARTRIDGE>.py \
  --mode AUDIT
```

**Delivery checklist:**

- [ ] `CRITICAL_` flag count same or lower than baseline
- [ ] Zero `FUZZ_CRASH` events
- [ ] No existing `bpy.props` renamed or removed
- [ ] All `get_slot_meta` keys match face slot assignments in `build_shape`
- [ ] All new props appear in `draw_shape_ui`
- [ ] All `FloatProperty` divisors have `max(0.001, ...)` guards
