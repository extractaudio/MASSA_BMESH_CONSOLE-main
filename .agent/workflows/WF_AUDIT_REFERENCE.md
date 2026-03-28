---
description: Debugging Tools
---

# WF_AUDIT_REFERENCE — Debugging Tools & Flag Reference

Quick reference for all audit tools, modes, and error flags. Used by all other workflows.

---

## Tools Overview

| Tool | File | Purpose |
| :--- | :--- | :--- |
| `runner.py` | `modules/debugging_system/runner.py` | Cartridge audit runner — all audit modes |
| `debug_agent.py` | `modules/debugging_system/debug_agent.py` | Execute arbitrary Python in live Blender |
| `headless_launcher.py` | `modules/debugging_system/headless_launcher.py` | Spawns background Blender process |
| `visual_inspector.py` | `modules/debugging_system/visual_inspector.py` | Viewport rendering (used internally by runner) |
| `runner_console.py` | `modules/debugging_system/runner_console.py` | Interactive runner console |

**Setup required:** Set `BLENDER_PATH` in `modules/debugging_system/config.py` before using any tool.

---

## runner.py — All Modes

```bash
python modules/debugging_system/runner.py \
  --cartridge <path_to_cartridge.py> \
  --mode <MODE> \
  [--payload '<JSON>']
```

| Mode | What It Does | When to Use |
| :--- | :--- | :--- |
| `AUDIT` | Full geometry, topology, UV, edge slot checks. Fuzz runs automatically. | Always — run this first |
| `VISUAL_DIFF` | Red/green wireframe overlay comparing two cartridge versions | After iterating geometry |
| `UV_HEATMAP` | UV distortion heatmap (Red=bad, Blue=good) | When UV quality is suspect |
| `UV_INSPECT` | 2D UV layout in 0-1 space | To find overlaps and out-of-bounds islands |
| `PERFORMANCE` | Execution time and polycount vs. budget | When cartridge is slow or heavy |
| `CSG_DEBUG` | Visualizes hidden boolean cutter objects | When using boolean subtraction |

**Output format:** JSON between `---AUDIT_START---` and `---AUDIT_END---` markers.

**VISUAL_DIFF payload example:**

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_01_beam.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "modules/cartridges/cart_prim_01_beam_v2.py"}'
```

---

## debug_agent.py — Live State Inspection

```bash
# Inline code
python modules/debugging_system/debug_agent.py --code "<python>"

# File execution
python modules/debugging_system/debug_agent.py --file temp_inspect.py
```

**Useful inspection commands:**

```bash
# List all objects in scene
--code "import bpy; print(list(bpy.data.objects.keys()))"

# Check active object's custom properties
--code "import bpy; o=bpy.context.active_object; print(dict(o.items()))"

# Check MASSA_PARAMS on a specific object
--code "import bpy; o=bpy.data.objects['MyObj']; print(o.get('MASSA_PARAMS', 'not found'))"

# List registered MASSA operators
--code "import bpy; print([t.bl_idname for t in bpy.types.Operator.__subclasses__() if 'massa' in t.bl_idname.lower()])"

# Verify _sync() list on base operator
--code "from massa.operators.massa_base import Massa_OT_Base; print(Massa_OT_Base.SYNC_PROPS)"
```

---

## Auditors — What Each Checks

All auditors run automatically during `AUDIT` mode via the `auditors/` sub-package.

| Auditor | File | Checks |
| :--- | :--- | :--- |
| **Topology** | `massa_auditor.py` | Empty mesh, flat Z, missing slot layer, loose verts, non-manifold edges, zero-area faces, thin sliver faces |
| **Edge Slots** | `massa_edge_auditor.py` | Missing `MASSA_EDGE_SLOTS` layer, no seams on complex meshes (>12 faces), isolated seam edges |
| **Surface** | `massa_surface_auditor.py` | Missing UV layer, zero UV data, inverted normals, self-intersections, UV spikes, collapsed UV islands |
| **Fuzz** | `massa_fuzz_auditor.py` | Randomizes parameters, re-runs `build_shape`, checks for crashes and topology corruption |
| **UI** | `massa_ui_auditor.py` | Validates operator properties and `draw_shape_ui` draw calls |
| **Topology Extra** | `massa_topology_extra.py` | Extended topology checks beyond the base auditor |

---

## All Audit Flags — Complete Reference

### CRITICAL — Must Fix Before Delivery

| Flag | Source | Meaning | Fix |
| :--- | :--- | :--- | :--- |
| `CRITICAL_EMPTY_MESH` | Topology | No geometry created | Check `build_shape` logic and early returns |
| `CRITICAL_FLAT_Z_AXIS` | Topology | Geometry has zero height (2D only) | Check scale/extrusion logic |
| `CRITICAL_MISSING_SLOT_LAYER` | Topology | No `MASSA_EDGE_SLOTS` int layer | Create: `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` |
| `CRITICAL_NO_PERIMETER_DEFINED` | Topology | Zero edges tagged as role 1 | Tag silhouette/end-cap edges: `e[edge_slots] = 1` |
| `CRITICAL_LOOSE_VERTS_N` | Topology | N orphaned vertices | Delete: `bmesh.ops.delete(bm, geom=[v], context='VERTS')` |
| `CRITICAL_NON_MANIFOLD_N` | Topology | N non-manifold edges (holes or T-junctions) | Fix bridge/fill logic; run `recalc_face_normals` |
| `CRITICAL_ZERO_AREA_FACES_N` | Topology | N faces with 0.0 area | Check all extrusions for collapsed geometry; add distance guards |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | Edge Slots | 3D mesh >12 faces with zero seam edges | Tag role 1 (Perimeter) or 3 (Guide) on appropriate edges |
| `CRITICAL_MISSING_UV_LAYER` | Surface | No UV layer on output mesh | Set UV strategy in `get_slot_meta`; or write manual UVs |
| `CRITICAL_ZERO_UV_DATA` | Surface | UV layer exists but all UVs at (0, 0) | Check UV strategy; for SKIP, verify manual UV math in `build_shape` |
| `CRITICAL_INVERTED_NORMALS` | Surface | Faces pointing inward | `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` |
| `CRITICAL_SELF_INTERSECTION` | Surface | Geometry overlaps itself | Check boolean and extrusion logic |
| `CRITICAL_UV_SPIKES_N` | Surface | N UV islands with extreme distortion | Improve seam placement; fix topology first |
| `CRITICAL_COLLAPSED_UVS_N` | Surface | N UV islands collapsed to a point | Check for zero-area faces in UV space |
| `FUZZ_CRASH` | Fuzz | Crash under randomized parameters | Add `max(0.001, self.prop)` guards; check divide-by-zero |

### WARNING — Should Fix

| Flag | Source | Meaning | Fix |
| :--- | :--- | :--- | :--- |
| `WARNING_THIN_FACES_N` | Topology | N sliver faces (Perimeter² / Area > 1000) | Causes bevel artifacts and UV distortion — rebuild affected loops |
| `WARNING_MISSING_EDGE_SLOTS_LAYER` | Edge Slots | Layer exists but no edges assigned | Assign edge roles in `build_shape` |
| `WARNING_ISOLATED_SEAM_EDGES_N` | Edge Slots | N disconnected/isolated seam edges | Ensure seam loops are continuous |

---

## Edge Role Reference

Assigned to edges via the `MASSA_EDGE_SLOTS` integer layer.

| ID | Name | Effect | Use For |
| :--- | :--- | :--- | :--- |
| 0 | **None** | Smooth, no special treatment | Default / interior |
| 1 | **Perimeter** | Seam + Sharp + Bevel | Silhouette, end caps, outer borders |
| 2 | **Contour** | Sharp + Bevel (no seam) | Hard internal angles (90°+) |
| 3 | **Guide** | Seam Only | UV cut lines — cylinder longitudinals, tube seams |
| 4 | **Detail** | Bevel Only (no sharp) | Soft chamfers, small feature lines |
| 5 | **Fold** | Crease (no sharp/bevel) | Subdivision weighting, cloth pinning |

**Auto-detection fallback:** If no edges are tagged manually, the engine analyzes geometry:

- End caps and silhouette edges → role 1 (Perimeter)
- Cylinder seam lines / tube cuts → role 3 (Guide)

---

## Face Slot (Material Slot) Reference

All faces must have a `material_index` matching a key in `get_slot_meta()`.

| Index | Role | Default Physics | Notes |
| :--- | :--- | :--- | :--- |
| 0 | BASE | `METAL_STEEL` | Primary surface — required |
| 1 | DETAIL | `METAL_STEEL` | Secondary features |
| 2 | TRIM | `METAL_CHROME` | Edges, rails, borders |
| 3 | GLASS | `GLASS_CLEAR` | Transparent panels |
| 4 | EMISSION | `EMISSION` | Glowing / light-emitting surfaces |
| 5 | DARK | `RUBBER` | Dark/matte insets |
| 6 | ACCENT | `METAL_PAINTED` | Color accent faces |
| 7 | UTILITY | `PLASTIC_HARD` | Functional/mechanical surfaces |
| 8 | TRANSPARENT | `GLASS_TINTED` | Semi-transparent |
| 9 | SOCKET | `SOCKET` | Snap / connection point faces |

---

## UV Strategy Reference

Set per-slot in `get_slot_meta()` under the `"uv"` key.

| Strategy | Behavior | When to Use |
| :--- | :--- | :--- |
| `"SKIP"` | Engine skips this slot; manual UVs must be written in `build_shape` | Golden Cartridges with precise UV math |
| `"BOX"` | Engine applies box-mapping automatically | Simple rectangular geometry |
| `"UNWRAP"` | Engine unwraps using seams from edge slots 1 and 3 | Organic or irregular geometry with good seams |
| `"FIT"` | Engine unwraps and fits islands to 0-1 space | When packing efficiency matters |

---

## Golden Reference Cartridges

When auditing or writing a new cartridge, compare against these verified clean examples:

| Pattern | Reference File |
| :--- | :--- |
| Linear extrusions | `cart_prim_01_beam.py` |
| Panels with openings | `cart_prim_04_panel.py` |
| Mathematical curves | `cart_prim_05_catenary.py` |
| Helical / rotational | `cart_prim_11_helix.py` |
