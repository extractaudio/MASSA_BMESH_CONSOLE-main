---
description: Modify the MASSA Engine, Console, or Base Operator
---

# WF_FLASH_CONSOLE — Console / Engine Modification

**Use when:** Changing shared infrastructure — not a cartridge, but the engine, base operator, property system, or UI layer.
**Do not use when:** Changing a single cartridge — use `WF_FLASH_MODIFY.md`.

> **High risk.** Console changes affect every cartridge. Read all files before touching anything.

---

## STEP 0 — Architecture Map (Read This First)

| Layer | File | Responsibility |
| :--- | :--- | :--- |
| Brain | `massa/massa_properties.py` | Shared property DNA |
| Brain | `massa/massa_console.py` | Registration, keymaps, global state |
| Muscle | `massa/operators/massa_base.py` | Base operator, Resurrection, `_sync()` |
| Engine | `massa/modules/massa_engine.py` | 6-phase generation pipeline |
| Engine | `massa/modules/massa_polish.py` | Phase 4: Bevel, solidify, twist, bend |
| Engine | `massa/modules/massa_surface.py` | Phase 5: UVs, materials, normals |
| Engine | `massa/modules/massa_builder.py` | MassaBuilder fluent API |
| Engine | `massa/modules/seam_solvers.py` | Seam detection and UV cut logic |
| Face | `massa/ui/ui_shared.py` | Redo Panel tab drawing |
| Face | `massa/ui/ui_massa_panel.py` | N-Panel cartridge browser |
| Face | `massa/ui/ui_massa_pie.py` | Ctrl+I pie menu |

---

## STEP 1 — Identify Which Layer

| Task | Files to Read and Modify |
| :--- | :--- |
| Add a global property (all cartridges access it) | `massa_properties.py`, `massa_base.py`, `ui_shared.py`, relevant engine file |
| Fix Resurrection logic | `massa/operators/massa_base.py` |
| Modify UV/seam behavior | `massa_surface.py`, `seam_solvers.py` |
| Modify bevel/polish behavior | `massa_polish.py` |
| Add Redo Panel tab or UI control | `ui_shared.py`, `ui_massa_panel.py` |
| Change pipeline order/logic | `massa_engine.py` |
| Change addon registration or keymap | `massa_console.py` |
| Modify MassaBuilder API | `massa_builder.py` |

**Read all identified files completely before writing any code.**

---

## STEP 2 — Adding a Global Property (Rule of Five)

If adding a property that all cartridges can access, you **must** modify all five bridge points. Skip any one and state synchronization breaks.

### Bridge Point 1 — Brain: Define the property
File: `massa/massa_properties.py`

```python
# In MassaPropertiesMixin class body:
my_new_prop: bpy.props.FloatProperty(name="My Prop", default=1.0, min=0.0)

# In register() function:
bpy.types.Scene.my_new_prop = bpy.props.FloatProperty(name="My Prop", default=1.0, min=0.0)

# In unregister() function:
del bpy.types.Scene.my_new_prop
```

### Bridge Point 2 — Muscle: Verify inheritance
File: `massa/operators/massa_base.py`

`Massa_OT_Base` inherits from `MassaPropertiesMixin`. Verify the inheritance line is present:
```python
class Massa_OT_Base(MassaPropertiesMixin, bpy.types.Operator):
```
No code change needed here if inheritance is intact.

### Bridge Point 3 — Bridge: Add to `_sync()` list
File: `massa/operators/massa_base.py`

Find `SYNC_PROPS` list. Add the exact property name string:
```python
SYNC_PROPS = [
    # ... existing ...
    "my_new_prop",   # <-- add exactly this string
]
```

### Bridge Point 4 — Interface: Add UI control
File: `massa/ui/ui_shared.py`

In the correct `draw_<tab>_tab()` function, add:
```python
col.prop(op, "my_new_prop")
```

Tab guide:
- `draw_shape_tab()` — geometry input parameters
- `draw_polish_tab()` — bevel, solidify settings
- `draw_uvs_tab()` — unwrap/UV settings
- `draw_data_tab()` — physics, metadata

### Bridge Point 5 — Logic: Implement behavior
File: `massa_polish.py`, `massa_surface.py`, or `massa_engine.py` (whichever phase applies)

```python
# Consume the value in the appropriate phase:
if op.my_new_prop > 0:
    # apply logic
```

---

## STEP 3 — Property Safety Rules

**Never rename an existing property.**
The Resurrection system stores parameter values in `obj["MASSA_PARAMS"]` by name. Renaming breaks all previously generated objects silently.

**Never remove a property.**
If obsolete: keep the `bpy.props` definition, add a deprecation comment, optionally remove from `SYNC_PROPS`.

**Never remove a property from `SYNC_PROPS` without confirming impact.**
Removing from sync means the property will not restore during Resurrection.

---

## STEP 4 — Headless Safety Rules

The engine must work without an active Blender window.

**Forbidden patterns:**
```python
# BAD — crashes headless mode
obj = bpy.context.active_object      # module-level context access
bpy.ops.mesh.primitive_cube_add()    # bpy.ops in engine code

# GOOD — data-level API
def run(self, context, obj):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
```

Rules:
- No `bpy.context` at module level
- No `bpy.ops.*` in engine files (`massa_engine.py`, `massa_polish.py`, `massa_surface.py`, `massa_builder.py`)
- No `context.active_object` shortcuts outside operator methods

---

## STEP 5 — Test After Console Change

### Inspect live Blender state
```bash
python modules/debugging_system/debug_agent.py \
  --code "import bpy; print([t.bl_idname for t in bpy.types.Operator.__subclasses__() if 'massa' in t.bl_idname.lower()])"
```

### Verify `_sync()` list includes new property
```bash
python modules/debugging_system/debug_agent.py --code "
from massa.operators.massa_base import Massa_OT_Base
print(Massa_OT_Base.SYNC_PROPS)
"
```

### Console health check
```bash
python _Scripts/test_run_cartridge.py massa/modules/cartridges/cart_prim_01_beam.py --mode CONSOLE_AUDIT
```

### Regression check — one cartridge per category
```bash
python modules/debugging_system/runner.py --cartridge massa/modules/cartridges/cart_prim_01_beam.py --mode AUDIT
python modules/debugging_system/runner.py --cartridge massa/modules/cartridges/cart_arc_01_wall.py --mode AUDIT
python modules/debugging_system/runner.py --cartridge massa/modules/cartridges/cart_urb_01_sidewalk.py --mode AUDIT
```

All three must return zero new `CRITICAL_` flags.

---

## STEP 6 — Engine Pipeline Reference

Know which phase file to modify:

| Phase | What Happens | File |
| :--- | :--- | :--- |
| 1 | Cartridge runs `build_shape(bm)` | Cartridge file |
| 2 | `auto_detect_edge_slots()` assigns edge roles geometrically | `massa_engine.py` |
| 3 | `auto_detect_sharp_edges()` marks convex/concave edges as sharp | `massa_engine.py` |
| 4 | Polish Stack: bevel, fuse, solidify, twist, bend | `massa_polish.py` |
| 5 | Surface: UVs, materials, physics, normals | `massa_surface.py` |
| 6 | Output: BMesh → mesh, material slots, sockets | `massa_engine.py`, `massa_sockets.py` |

If modifying Phase 2 or 3: test with `cart_prim_11_helix.py` (complex edge roles).
If modifying Phase 5: always run `UV_HEATMAP` and `UV_INSPECT` after.

---

## STEP 7 — Delivery Checklist

- [ ] Rule of Five complete (if adding a global property)
- [ ] No existing property names changed or removed
- [ ] No `bpy.context` at module level in any engine file
- [ ] No `bpy.ops` in engine code (`massa_engine.py`, `massa_polish.py`, `massa_surface.py`)
- [ ] AUDIT passes on at least 3 representative cartridges — zero new `CRITICAL_` flags
- [ ] `SYNC_PROPS` list updated (if new property added)
- [ ] `bpy.types.Scene` registration/unregistration updated (if new global prop)
