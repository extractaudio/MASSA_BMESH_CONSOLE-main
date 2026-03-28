---
description: Modify the Blender 5.0 Addon : MASSA Engine, Brain, or Muscle
---

# WF_CONSOLE_MODIFY — Modify the Blender 5.0 Addon : MASSA Engine, Brain, or Muscle

Use this workflow when tasked with changing the **console** itself — not a cartridge, but the shared infrastructure: the property system, the base operator, the generation pipeline, the UI, or the surface/polish subsystems.

> **High-risk zone.** Console changes affect every cartridge. Changes to property names break the Resurrection system. Read all referenced files before touching anything.

---

## Phase 0 — Orientation: Know the Architecture

The console is split into four strictly separated layers. Know which one you are modifying before you write code.

```
Brain    massa_properties.py         Shared property DNA (Scene + Operator)
         massa_console.py            Addon registration, keymaps, global state

Muscle   operators/massa_base.py     Base operator: Resurrection, _sync(), UI tabs

Engine   modules/massa_engine.py     6-phase generation pipeline orchestrator
         modules/massa_polish.py     Bevel, solidify, twist, bend (Phase 4)
         modules/massa_surface.py    UVs, materials, physics, normals (Phase 5)
         modules/massa_sockets.py    Socket/anchor point generation
         modules/massa_builder.py    MassaBuilder helper API
         modules/seam_solvers.py     Seam detection and UV cut logic

Face     ui/ui_massa_panel.py        N-Panel cartridge browser
         ui/ui_shared.py             Shared Redo Panel tab drawing
         ui/ui_massa_pie.py          Ctrl+I pie menu
         ui/gizmo_massa.py           3D viewport gizmo (Shooter mode)
```

---

## Phase 1 — Identify the Change Type

| Task | Which Layer | Key File(s) |
| :--- | :--- | :--- |
| Add a new global property | Brain + Muscle + Face + Engine | `massa_properties.py`, `massa_base.py`, `ui_shared.py`, engine file |
| Change Resurrection logic | Muscle | `operators/massa_base.py` |
| Modify UV/seam behavior | Engine (Surface) | `massa_surface.py`, `seam_solvers.py` |
| Modify bevel/polish behavior | Engine (Polish) | `massa_polish.py` |
| Add a new Redo Panel tab or UI control | Face | `ui_shared.py`, `ui_massa_panel.py` |
| Modify 6-phase pipeline order or logic | Engine (Core) | `massa_engine.py` |
| Change addon registration or keymap | Brain | `massa_console.py` |
| Modify the MassaBuilder helper API | Engine | `massa_builder.py` |

---

## Phase 2 — Adding a Global Property (The Rule of Five)

If you are adding a new parameter that all cartridges can access (not cartridge-local), you **must** modify all five bridge points in order. Skipping any one breaks state synchronization.

**Bridge Point 1 — Brain: Define the property**

In `massa/modules/massa_properties.py`, add to the `MassaPropertiesMixin` class AND register on `bpy.types.Scene`:

```python
# In MassaPropertiesMixin:
my_new_prop: bpy.props.FloatProperty(name="My Prop", default=1.0, min=0.0)

# In register():
bpy.types.Scene.my_new_prop = bpy.props.FloatProperty(...)
# In unregister():
del bpy.types.Scene.my_new_prop
```

**Bridge Point 2 — Muscle: Confirm inheritance**

`Massa_OT_Base` inherits from `MassaPropertiesMixin`, so properties added to the mixin are automatically available on all operators. Verify the inheritance chain is intact in `operators/massa_base.py`.

**Bridge Point 3 — Bridge: Add to `_sync()` list**

In `operators/massa_base.py`, find the `_sync()` method. Add the exact property name string to the sync list:

```python
SYNC_PROPS = [
    # ... existing props ...
    "my_new_prop",   # <-- add here
]
```

This ensures the property is copied from Scene → Operator during Resurrection.

**Bridge Point 4 — Interface: Add the UI control**

In `ui/ui_shared.py`, add the UI drawing call in the appropriate Redo Panel tab:

```python
# In the correct draw_<tab>_tab() function:
col.prop(op, "my_new_prop")
```

Choose the right tab: `Shape` (geometry input), `Polish` (bevel/solidify), `UVs` (unwrap settings), `Data` (physics/metadata).

**Bridge Point 5 — Logic: Implement the behavior**

In the appropriate engine file, consume the property value:

```python
# Example in massa_polish.py or massa_engine.py:
if op.my_new_prop > 0:
    # apply logic
```

---

## Phase 3 — Property Safety Rules

**Never rename an existing property.** The Resurrection system stores parameter values in `obj["MASSA_PARAMS"]` by property name. Renaming silently breaks all previously generated objects.

If a property is obsolete:

- Keep it in the code with a deprecation comment.
- Remove it from the `_sync()` list if it should stop being persisted.
- Do not remove the `bpy.props` definition.

**Never remove a property from `_sync()` without understanding the impact.** Removing from sync means the property will not restore during Resurrection, causing silently wrong geometry on old objects.

---

## Phase 4 — Headless Safety Rules

The engine must work without an active Blender window (headless batch mode, MCP agents). Follow these rules:

- **No `bpy.context` in module-level code.** Context is only valid inside operator `execute()`, `invoke()`, or `draw()` calls. Module-level access crashes headless mode.
- **No `bpy.ops.*` in engine code.** Use `bmesh.ops` or data-level API instead.
- **No `context.active_object` shortcuts** outside of the operator methods — always pass the object explicitly.

Example of unsafe code to avoid:

```python
# BAD — module-level context access
obj = bpy.context.active_object  # crashes headless

# GOOD — passed through the pipeline
def run(self, context, obj):
    ...
```

---

## Phase 5 — Testing Console Changes

**Inspect live Blender state after a change:**

```bash
python modules/debugging_system/debug_agent.py \
  --code "import bpy; print([op.bl_idname for op in bpy.types.Operator.__subclasses__()])"
```

**Run a full console health check** (addon registration, edge slots, op ID) after any console modification:

```bash
python test_run_cartridge.py massa/modules/cartridges/cart_prim_01_beam.py --mode CONSOLE_AUDIT
```

This replaces the old `runner_console.py` script. The health checks now live in `runner.py` as `CONSOLE_AUDIT` mode. Output is JSON between `---AUDIT_START---` / `---AUDIT_END---` markers, same as all other modes.

**Run a full cartridge through the pipeline** to verify the engine change doesn't break generation:

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_01_beam.py \
  --mode AUDIT
```

**Test Resurrection** by verifying the `_sync()` list includes your new property:

```bash
python modules/debugging_system/debug_agent.py --code "
import bpy
from massa.operators.massa_base import Massa_OT_Base
print(Massa_OT_Base.SYNC_PROPS)
"
```

**Test a wide sample** — after any engine change, audit at least one cartridge from each category:

```bash
# Primitives, Architecture, Urban — quick regression check
python modules/debugging_system/runner.py --cartridge modules/cartridges/cart_prim_01_beam.py --mode AUDIT
python modules/debugging_system/runner.py --cartridge modules/cartridges/cart_arc_01_wall.py --mode AUDIT
python modules/debugging_system/runner.py --cartridge modules/cartridges/cart_urb_01_sidewalk.py --mode AUDIT
```

---

## Phase 6 — Engine Pipeline Reference

Understand which phase of the pipeline your change lives in, so you modify the right file:

| Phase | What Happens | Key File |
| :--- | :--- | :--- |
| 1 | `build_shape(bm)` — cartridge generates raw BMesh | Cartridge file |
| 2 | `auto_detect_edge_slots()` — assigns edge roles geometrically | `massa_engine.py` |
| 3 | `auto_detect_sharp_edges()` — marks convex/concave edges as sharp | `massa_engine.py` |
| 4 | **Polish Stack** — bevel, fuse, solidify, twist, bend modifiers | `massa_polish.py` |
| 5 | **Surface** — UVs, materials, physics data written | `massa_surface.py` |
| 6 | **Output** — BMesh → mesh, material slots assigned, sockets created | `massa_engine.py`, `massa_sockets.py` |

If you are modifying **Phase 2 or 3** (edge detection), test with a complex cartridge like `cart_prim_11_helix.py` that has many edge roles.

If you are modifying **Phase 5** (Surface), always run `UV_HEATMAP` and `UV_INSPECT` modes after any change.

---

## Phase 7 — Delivery Checklist

- [ ] Rule of Five complete (if adding a global property)
- [ ] No existing property names changed or removed
- [ ] No `bpy.context` at module level
- [ ] No `bpy.ops` in engine or builder code
- [ ] AUDIT passes on at least 3 representative cartridges (zero new `CRITICAL_` flags)
- [ ] Resurrection tested: object generated, Blender reloaded, Resurrect applied — properties restored correctly
