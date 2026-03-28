---
description: Modify or Repair an Existing Geometry Cartridge
---

# WF_CARTRIDGE_MODIFY — Modify or Repair an Existing Cartridge

Use this workflow when tasked with editing, fixing, iterating, or adding features to a cartridge that already exists in `massa/modules/cartridges/`.

> **Never overwrite a cartridge without reading it first.**

---

## Phase 0 — Read Before Touching

**Read the entire cartridge file before writing a single character:**

1. Read the file top-to-bottom. Capture:
   - `CARTRIDGE_META` — `id`, `name`, `icon`, `flags`
   - All existing `bpy.props` property names and defaults
   - `get_slot_meta()` — which slot indices are defined
   - `build_shape()` — the geometry logic and any edge/UV assignments
   - `draw_shape_ui()` — which properties appear in the Redo Panel

2. Back up by duplicating the file: `<name>_backup.py`. This is your rollback target.

3. Run the current state through AUDIT to establish a baseline:

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode AUDIT
```

Note which flags (if any) exist before your edits. You must not introduce new ones.

---

## Phase 1 — Classify the Task

Identify which category of change applies:

| Category | Indicators | Go To |
| :--- | :--- | :--- |
| **Bug / Crash** | Error on generate, Fuzz crash, exception in console | Phase 2A |
| **Topology Error** | `CRITICAL_*` flags in audit output | Phase 2B |
| **UV / Surface Error** | `CRITICAL_UV_*`, red heatmap, distorted UVs | Phase 2C |
| **Parameter Addition** | Adding a new `bpy.props` to an existing cartridge | Phase 2D |
| **UI Change** | Redo Panel layout, draw_shape_ui | Phase 2E |
| **Geometry Iteration** | Adjusting segments, scale, shape profile | Phase 2F |

---

## Phase 2A — Bug / Crash Fix

1. Reproduce the error with `debug_agent.py`:

```bash
python modules/debugging_system/debug_agent.py \
  --code "exec(open('modules/cartridges/<name>.py').read())"
```

1. Read the traceback. Identify: is it a Python syntax error, a missing import, a Blender context error (`RuntimeError: Operator called from wrong context`), or a math error?

2. **Context errors** (`bpy.ops.*` or `bpy.context` inside `build_shape`): Replace with `bmesh.ops` or `mathutils` equivalents. `bpy.ops` is forbidden inside `build_shape`.

3. **Math errors** (division by zero, `Vector` of wrong length): Add guards. Example:

```python
length = max(0.001, self.length)  # never allow zero-length extrusion
```

1. Re-run AUDIT after fix. Confirm no new flags.

---

## Phase 2B — Topology Error Fix

Look up the flag in the audit output and apply the corresponding fix:

| Flag | Fix |
| :--- | :--- |
| `CRITICAL_ZERO_AREA_FACES_N` | Find collapsed extrusions; add distance guards or delete zero-area faces with `bmesh.ops.dissolve_degenerate` |
| `CRITICAL_LOOSE_VERTS_N` | Call `bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')` |
| `CRITICAL_NON_MANIFOLD_N` | Check for open holes or T-junctions; use `bmesh.ops.fill` or fix bridge logic |
| `CRITICAL_NO_PERIMETER_DEFINED` | Tag silhouette/end-cap edges: `e[edge_slots] = 1` |
| `CRITICAL_MISSING_SLOT_LAYER` | Create the layer: `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` |
| `WARNING_THIN_FACES_N` | Faces with extreme aspect ratio — rebuild affected loops with better topology |

After each fix, re-run AUDIT to confirm the flag is gone.

---

## Phase 2C — UV / Surface Error Fix

**Step 1** — Run the UV heatmap:

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode UV_HEATMAP
```

**Step 2** — Run the UV layout inspect:

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode UV_INSPECT
```

**Diagnose from the output:**

| Problem | Cause | Fix |
| :--- | :--- | :--- |
| All UVs at (0, 0) | `CRITICAL_ZERO_UV_DATA` | Check UV strategy in `get_slot_meta`; switch from `SKIP` to `BOX` or add manual UV math |
| Overlapping islands | No seams cut | Tag edges with role 1 (Perimeter) or 3 (Guide); or switch to `UNWRAP` strategy |
| Islands outside 0-1 space | Manual UV math overflows | Normalize UV coordinates |
| UV spikes | Thin/degenerate faces in UV space | Fix topology first (Phase 2B), then re-audit UV |
| Seam lines visible on render | Seam placement is wrong | Move seam edges to less visible silhouettes; use role 3 (Guide) for natural UV cuts |

**Seam tagging quick reference:**

```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") \
             or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

# Silhouette / end-cap borders → role 1 (Perimeter): seam + sharp + bevel
# Cylinder longitudinal lines → role 3 (Guide): seam only
# Hard internal angles       → role 2 (Contour): sharp + bevel, no seam
for e in bm.edges:
    if <condition>:
        e[edge_slots] = 1  # or 2, 3, 4, 5
```

---

## Phase 2D — Adding a New Cartridge-Local Property

A cartridge-local property lives only in the operator class (not in Scene). This is simpler than a global property — it does not require the Rule of Five.

1. Add the `bpy.props` definition to the operator class body:

```python
my_new_param: bpy.props.FloatProperty(name="My Param", default=1.0, min=0.01)
```

1. Use `self.my_new_param` inside `build_shape`.

2. Add a `col.prop(self, "my_new_param")` line in `draw_shape_ui`.

3. **Critical — Resurrection safety:** Never remove or rename existing properties. The Resurrection system replays stored parameter values by name from `obj["MASSA_PARAMS"]`. Renaming a property silently breaks older objects. If a property is obsolete, keep it with a deprecation comment.

4. Run AUDIT to confirm no geometry regressions.

---

## Phase 2E — UI Change (draw_shape_ui)

The Redo Panel UI is drawn by `draw_shape_ui(self, layout)`. Rules:

- Use `layout.column(align=True)` for grouped controls.
- Use `layout.separator()` to group related parameters visually.
- Do not add `layout.operator()` calls inside `draw_shape_ui` — this breaks the Redo Panel.
- Boolean properties intended as triggers must use the **Boolean Trigger Pattern** (see `Cartridge_UI_Sweep.md` legacy reference) — store state in a Scene property, not the operator directly, if it triggers a one-time action.

---

## Phase 2F — Geometry Iteration

When refining shape (adjusting segments, scale factors, proportions):

1. Make the smallest possible targeted change.
2. Run the visual diff against the original backup to confirm the change is what was intended:

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "modules/cartridges/<name>_backup.py"}'
```

1. Run AUDIT to confirm no topology regressions were introduced.

---

## Phase 3 — Final Verification

After any change type:

```bash
# Full audit
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode AUDIT

# UV check (if geometry or UV logic was touched)
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<name>.py \
  --mode UV_INSPECT
```

**Delivery checklist:**

- [ ] Zero `CRITICAL_` flags (same or fewer than baseline)
- [ ] No `FUZZ_CRASH` events
- [ ] No existing `bpy.props` were renamed or removed
- [ ] `get_slot_meta()` still covers all face slot indices used in `build_shape`
- [ ] `draw_shape_ui` reflects any newly added properties
- [ ] Backup file removed (or kept if versioning is needed)
