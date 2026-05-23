# MASSA CARTRIDGE MANDATE

> **The "Golden Standard" for Procedural Geometry Cartridges**

This document defines the strict requirements for creating a "Golden Cartridge" in the Massa system. All new geometry scripts must adhere to these protocols to ensure consistency, stability, headless safety, and high-quality output (clean topology + correct UVs + working sockets + functional edge slot visualization).

The canonical reference implementation is [`massa/modules/cartridges/cart_prim_01_beam.py`](massa/modules/cartridges/cart_prim_01_beam.py). Any pattern in this document marked **"Beam Reference"** is implemented exactly that way in the beam.

---

## 📑 Table of Contents

1.  [Overview & Philosophy](#1-overview--philosophy)
2.  [File Structure](#2-file-structure)
    *   [Imports](#21-imports)
    *   [Axis Convention](#22-axis-convention)
    *   [Metadata (`CARTRIDGE_META`)](#23-metadata-cartridge_meta)
    *   [Class Definition](#24-class-definition)
3.  [Properties Protocol](#3-properties-protocol)
    *   [Required UV Properties](#31-required-uv-properties)
    *   [Profile-Driven Construction](#32-profile-driven-construction-enumproperty)
    *   [Topology Properties](#33-topology-properties-segmentation)
    *   [Soft Limits](#34-soft-limits)
4.  [Slot & Material Protocol](#4-slot--material-protocol)
    *   [`get_slot_meta` Return Dict](#41-get_slot_meta-return-dict)
    *   [Slot Conventions for Structural Cartridges](#42-slot-conventions-for-structural-cartridges)
    *   [UV Strategy per Slot](#43-uv-strategy-per-slot)
5.  [Geometry & Topology (`build_shape`)](#5-geometry--topology-build_shape)
    *   [The Phase Pattern](#51-the-phase-pattern)
    *   [Headless Safety Rules](#52-headless-safety-rules-non-negotiable)
    *   [The Clean Extrusion Idiom](#53-the-clean-extrusion-idiom-beam-reference)
    *   [Segmentation via `bisect_plane`](#54-segmentation-via-bisect_plane-beam-reference)
    *   [Face Categorization by Position](#55-face-categorization-by-position-beam-reference)
    *   [Forcing Normals Explicitly](#56-forcing-normals-explicitly-beam-reference)
    *   [Slot Assignment by Geometric Role](#57-slot-assignment-by-geometric-role)
    *   [Safety Idioms](#58-safety-idioms)
6.  [Edge Slots & Seams](#6-edge-slots--seams)
    *   [Edge Slot Layer](#61-edge-slot-layer-massa_edge_slots)
    *   [The Auto-Detect Synergy](#62-the-auto-detect-synergy)
    *   [Marking Cap Seams](#63-marking-cap-seams)
    *   [The Longitudinal Seam Algorithm](#64-the-longitudinal-seam-algorithm-beam-reference)
    *   [Segment Cut Seams](#65-segment-cut-seams-beam-reference)
7.  [UV Mandate: Manual & Precise](#7-uv-mandate-manual--precise)
    *   [Setup](#71-setup)
    *   [Dual-Mode Scaling: `uv_scale` vs `fit_uvs`](#72-dual-mode-scaling-uv_scale-vs-fit_uvs)
    *   [Arc-Length U Calculation](#73-arc-length-u-calculation-beam-reference)
    *   [Per-Slot UV Strategies](#74-per-slot-uv-strategies)
    *   [The Wrapping Fix (Cylindrical Seam)](#75-the-wrapping-fix-cylindrical-seam-beam-reference)
8.  [Socket Protocols](#8-socket-protocols)
    *   [Standard: Tag Existing Faces](#81-standard-tag-existing-faces)
    *   [Socket Object Naming](#82-socket-object-naming-convention)
    *   [Customizing Socket Orientation (`execute()` Override)](#83-customizing-socket-orientation-execute-override-beam-reference)
9.  [UI Standards (`draw_shape_ui`)](#9-ui-standards-draw_shape_ui)
10. [Edge Slot Visualization (`viz_edge_mode = SLOTS`)](#10-edge-slot-visualization-viz_edge_mode--slots)
11. [Cartridge Self-Audit Checklist](#11-cartridge-self-audit-checklist)
12. [Anatomy of the Golden Beam — End-to-End Walkthrough](#12-anatomy-of-the-golden-beam--end-to-end-walkthrough)

---

## 1. Overview & Philosophy

A **Golden Cartridge** is a self-contained, parametric geometry generator. It is not just a mesh script; it is a "smart object" definition that includes:

*   **Metadata**: Identity, scale class, and capability flags.
*   **Topology**: Clean, quad-dominant geometry with thoughtful edge flow and correct manifold structure.
*   **Normals**: Explicit per-face control where geometry requires it; never trust automatic recalc blindly on extruded profiles.
*   **Data Layers**: Precise slot assignments (Materials/Slots 0-9), Edge Roles (Sharp/Seam/Guide via `MASSA_EDGE_SLOTS`), and Physics IDs (via `phys`).
*   **UVs**: **Manual, mathematically precise unwrapping** is the primary mandate. Auto-unwrap is a fallback, not a standard. UVs must handle cylindrical/closed-loop wrapping correctly.
*   **Sockets**: Explicit attachment points derived from existing geometry — never extra helper geometry. Socket orientation may be customized via an `execute()` override.
*   **Compatibility**: Must work with `viz_edge_mode = SLOTS` (so Edge Roles 1-5 visualize correctly), the Polish Stack, the Seam Solver, UCX collision generation, and the Resurrection system.

The Console grants the Cartridge superpowers (Auto-UVs, Physics IDs, UCX Colliders, Socket Forge) for free — **but only if these protocols are followed exactly.**

---

## 2. File Structure

### 2.1 Imports

Standard imports must include Blender types, BMesh, math, Mathutils, and the Base Operator.

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
```

*Optional:* `from ...modules.massa_builder import MassaBuilder` — for fluent BMesh construction (preferred for new cartridges that fit the box/extrude/inset/tag pattern).

### 2.2 Axis Convention

> **MANDATORY for all extruded cartridges (beams, pipes, ducts, conduits, etc.):**
> - **X axis** = WIDTH
> - **Y axis** = LENGTH (extrusion direction)
> - **Z axis** = HEIGHT
>
> This is documented in the Beam Reference with the comment: `# AXIS STANDARD: Y-AXIS IS LENGTH`.
>
> Profile/cross-section geometry lives in the **XZ plane**. The extrusion happens along **+Y**. This convention ensures sockets, snap points, and downstream tools (like the Polish Stack's `pol_bend_axis`) align consistently across cartridges.

For non-extruded cartridges (towers, tanks, radial objects), Z is the primary axis of symmetry.

### 2.3 Metadata (`CARTRIDGE_META`)

Every cartridge **must** define a module-level `CARTRIDGE_META` dictionary.

**Required keys:**

| Key | Type | Description |
|:---|:---|:---|
| `name` | `str` | Human-readable label (e.g. `"PRIM_01: Structural Beam"`). Shown in pie menu and search. |
| `id` | `str` | Unique internal ID (e.g. `"prim_01_beam"`). **Must match `bl_idname` suffix** — `bl_idname = "massa.gen_<id>"`. |
| `icon` | `str` | Blender icon constant (e.g. `"MOD_SOLIDIFY"`, `"MESH_CYLINDER"`). |
| `flags` | `dict` | Capability flags (see below). |

**Optional keys:**

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `scale_class` | `str` | `"STANDARD"` | One of `"MICRO"`, `"STANDARD"`, `"MACRO"`. Used by the Polish Stack to scale bevel/chamfer widths appropriately. |
| `version` | `str` | — | Optional cartridge version string for telemetry. |

**Full flag reference** (all are optional `bool`; defaults shown):

| Flag | Default | Effect |
|:---|:---|:---|
| `ALLOW_SOLIDIFY` | `True` | If `False`, Polish Stack skips `apply_solidify` even if user enables it. Use for cartridges that already produce closed volumes (e.g. I-Beam, Pipe). |
| `ALLOW_CHAMFER` | `True` | If `False`, Polish Stack skips `apply_chamfer`. Use when geometry is too thin/dense for bevels. |
| `ALLOW_FUSE` | `True` | If `False`, Polish Stack skips SDF Fuse. |
| `USE_WELD` | `True` | If `True`, engine welds vertices by distance after `build_shape`. |
| `FIX_DEGENERATE` | `True` | If `True`, engine runs `apply_cleanup` (zero-area + thin face removal) before and after the polish stack. |
| `REMOVE_LOOSE` | `True` | If `True`, engine deletes vertices not connected to any edge. |
| `LOCK_PIVOT` | `False` | If `True`, engine skips `apply_transform_alignment` — the cartridge keeps the origin at its generation start point. Use for cartridges with intentional pivot offset (e.g. doors hinged at one edge). |

**Beam Reference example:**

```python
CARTRIDGE_META = {
    "name": "PRIM_01: Structural Beam",
    "id":   "prim_01_beam",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,   # Beam profiles are already closed volumes
        "USE_WELD":       True,
        "ALLOW_CHAMFER":  True,
    },
}
```

### 2.4 Class Definition

The operator class **must** inherit from `Massa_OT_Base`.

| Attribute | Requirement |
|:---|:---|
| `bl_idname` | Must follow `massa.gen_<id>` exactly, where `<id>` matches `CARTRIDGE_META["id"]`. |
| `bl_label` | Short user-facing name (e.g. `"PRIM_01: Beam"`). |
| `bl_options` | Must be `{"REGISTER", "UNDO", "PRESET"}`. |

```python
class MASSA_OT_PrimBeam(Massa_OT_Base):
    bl_idname  = "massa.gen_prim_01_beam"
    bl_label   = "PRIM_01: Beam"
    bl_options = {"REGISTER", "UNDO", "PRESET"}
```

The class name convention is `MASSA_OT_<CamelCase>` matching the `id`.

---

## 3. Properties Protocol

### 3.1 Required UV Properties

> Every cartridge that writes manual UVs **must** expose these two properties so the user can scale UVs without diving into per-slot Console settings:

```python
uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
fit_uvs:  BoolProperty(name="Fit UVs 0-1", default=False)
```

- `uv_scale` = world-units-per-UV-unit multiplier (when `fit_uvs = False`).
- `fit_uvs = True` = stretches UVs to fill the 0–1 square exactly (useful for decals, displays, single-instance textures).

The Beam Reference applies these via `su_s` / `sv_s` (walls) and `su_c` / `sv_c` (caps) — separate scales for separate UV strategies.

### 3.2 Profile-Driven Construction (`EnumProperty`)

Cartridges with multiple geometry variants must drive them with a single `EnumProperty` rather than separate boolean toggles. This keeps the Redo Panel clean and serializes cleanly into `MASSA_PARAMS` for Resurrection.

**Beam Reference pattern:**

```python
profile_type: EnumProperty(
    name="Profile",
    items=[
        ("BOX",       "Box / Rect",   ""),
        ("I_BEAM",    "I-Beam",       ""),
        ("C_CHANNEL", "C-Channel",    ""),
        ("T_BEAM",    "T-Beam",       ""),
        ("L_ANGLE",   "L-Angle",      ""),
    ],
    default="I_BEAM",
)
```

In `build_shape`, switch on `self.profile_type` to define a 2D point list (`pts`) for the profile, then extrude. Never duplicate the extrusion/seam/UV logic per profile — drive everything from `pts`.

### 3.3 Topology Properties (Segmentation)

Length/girth subdivision is exposed as `segments_<axis>: IntProperty`. Default `0` means "no subdivision" — the cartridge produces a clean two-cap extrusion. Higher values add interior cuts via `bmesh.ops.bisect_plane` (see §5.4).

```python
segments_y: IntProperty(name="Length Segs", default=0, min=0, soft_max=50)
```

### 3.4 Soft Limits

Use `soft_max` (and `soft_min` where applicable) for properties that have a sensible interactive range but no hard ceiling. The UI slider snaps to soft_max but typed input still accepts higher values.

```python
segments_y:        IntProperty(default=0,  min=0,   soft_max=50)
pol_smooth_iter:   IntProperty(default=1,  min=1,   max=100, soft_max=20)
pol_chamfer_width: FloatProperty(default=0.005, min=0.0, max=1.0, soft_max=0.1, step=0.001)
```

This is the same pattern the Console uses for Polish properties.

---

## 4. Slot & Material Protocol

Golden Cartridges utilize a fixed 10-slot system (Indices 0-9). Define this via `get_slot_meta(self)`.

### 4.1 `get_slot_meta` Return Dict

Returns a dictionary where keys are Slot Indices (`int` 0-9) and values are dicts:

| Key | Type | Required | Description |
|:---|:---|:---|:---|
| `name` | `str` | ✅ | Description of the part (e.g., `"Surface"`, `"Caps"`, `"Anchor"`). Used in Socket object naming. |
| `uv` | `str` | ✅ | UV Strategy — see §4.3 |
| `phys` | `str` | ✅ | Physics/Visual Material ID from `MASTER_MAT_DB` (e.g. `"METAL_IRON"`, `"CONCRETE_RAW"`, `"MASSA_DEBUG_1"`). |
| `sock` | `bool` | optional | If `True`, marks this slot as a Socket Anchor — see §8. |

**Beam Reference:**

```python
def get_slot_meta(self):
    return {
        0: {"name": "Surface", "uv": "SKIP", "phys": "METAL_IRON"},
        1: {"name": "Caps",    "uv": "BOX",  "phys": "METAL_IRON"},
    }
```

### 4.2 Slot Conventions for Structural Cartridges

For extruded structural cartridges (beam, pipe, duct, conduit, column), use this convention:

| Slot | Role | Geometry |
|:---|:---|:---|
| **0** | **Surface** (walls / shell) | Faces whose normal is NOT along the extrusion axis |
| **1** | **Caps** (end faces) | Start cap (Y ≈ 0) and end cap (Y ≈ length) |
| **2-8** | Detail / Trim / etc. | Optional |
| **9** | Socket Anchor (only if needed) | Logical attachment face — see §8 |

This keeps the wall surface (where mathematical UVs are most important) on slot 0, separate from the caps (which can use a simple analytic `"BOX"` mapping).

### 4.3 UV Strategy per Slot

The `"uv"` key tells the engine how to handle UVs for faces assigned to that slot.

| Value | When to Use |
|:---|:---|
| `"SKIP"` | **Golden Standard for any slot where you write UVs manually in `build_shape`.** The engine will not overwrite your UVs. |
| `"BOX"` | Tri-planar cube projection. Use for flat-ish surfaces like caps where analytic mapping is "good enough". |
| `"FIT"` | Stretch UVs to fill the 0–1 square. Use for single-face decals or screens. |
| `"TUBE_Z"` / `"TUBE_Y"` / `"TUBE_X"` | Cylindrical projection along the named axis. Use for radial trim if you don't want to compute it manually. |
| `"UNWRAP"` | LSCM / Angle-Based Unwrap. Requires seams to be marked (`e.seam = True` or via Edge Slots 1/3). Use as a fallback for organic/complex slots where manual UVs aren't tractable. |

> **Golden Rule:** The main "Surface" slot (slot 0 for structural cartridges) should almost always be `"SKIP"` with manual UVs. The Beam Reference uses `"SKIP"` for walls and `"BOX"` for caps.

---

## 5. Geometry & Topology (`build_shape`)

The core logic resides in `build_shape(self, bm)`.

- **Input**: `bm` (`bmesh.types.BMesh`) — the mesh to build into. Already initialized with the `MASSA_SOCKETS` face layer.
- **Output**: Modify `bm` in place. Do not return anything.

### 5.1 The Phase Pattern

Structure `build_shape` into numbered phases with comments. This makes review and debugging dramatically easier. The Beam Reference uses 7 phases:

```python
def build_shape(self, bm: bmesh.types.BMesh):
    # 1. PROFILE DEFINITION (XZ Plane)
    # 2. CREATE BASE GEOMETRY (Clean Extrusion)
    # 3. SEGMENTATION
    # 4. IDENTIFY & FORCE CAP NORMALS
    # 5. ASSIGN SLOTS
    # 6. MARK SEAMS & EDGE SLOTS
    # 7. UV MAPPING
```

Adapt the phase list to your geometry (a radial cartridge might have different phases) but always keep the **commented separators**.

### 5.2 Headless Safety Rules (Non-Negotiable)

1.  **NO `bpy.ops` INSIDE `build_shape`.** It crashes in headless/background mode used by the audit suite. Use only `bmesh.ops`, `bmesh` types, and `mathutils`.
2.  **NO `bpy.context.*` READS INSIDE `build_shape`.** Headless context is empty. The operator `self` already has every property you need.
3.  **NO `bpy.data.*` creation inside `build_shape`.** Don't make objects, meshes, materials, or collections. The Engine does that in `_generate_output`.

### 5.3 The Clean Extrusion Idiom (Beam Reference)

For extruded profiles, the canonical pattern is:

```python
# 1. Define 2D profile points in the XZ plane
pts = [(-hw, 0), (hw, 0), (hw, h), (-hw, h)]   # Box example

# 2. Create base vertices and the start cap face
base_verts = [bm.verts.new((p[0], 0.0, p[1])) for p in pts]
bm.verts.ensure_lookup_table()

try:
    start_cap = bm.faces.new(base_verts)
except ValueError:
    return                                       # Invalid profile geometry

# 3. Extrude the cap to create walls + end cap in one operation
res_ext   = bmesh.ops.extrude_face_region(bm, geom=[start_cap])
verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]

# 4. Translate the extruded verts to the final length
bmesh.ops.translate(bm, verts=verts_ext, vec=(0.0, self.length, 0.0))
```

**Why this pattern:**
- One `extrude_face_region` call produces all wall quads + end cap simultaneously. No manual stitching.
- The start cap is preserved at Y=0 with consistent winding.
- `try/except ValueError` catches degenerate profiles (collinear points, self-intersection) without crashing the operator.
- `ensure_lookup_table()` after raw `bm.verts.new` is mandatory before any `bm.verts[N]` indexing or face creation that references those verts.

### 5.4 Segmentation via `bisect_plane` (Beam Reference)

To add interior loop cuts along the extrusion, use `bmesh.ops.bisect_plane` — **not** `bmesh.ops.subdivide_edges`. Bisect produces a single clean perpendicular cut without altering existing edge topology.

```python
if self.segments_y > 0:
    step = self.length / (self.segments_y + 1)
    for i in range(1, self.segments_y + 1):
        y_cut    = i * step
        geom_all = bm.faces[:] + bm.edges[:] + bm.verts[:]
        bmesh.ops.bisect_plane(
            bm,
            geom             = geom_all,
            dist             = 0.0001,
            plane_co         = (0, y_cut, 0),
            plane_no         = (0, 1, 0),
            use_snap_center  = False,
            clear_outer      = False,
            clear_inner      = False,
        )
```

Each cut subdivides every wall face it crosses, producing a clean ring of edges at `y_cut`. These rings can be tagged as Edge Slot 3 (Guide) afterwards (see §6.5).

### 5.5 Face Categorization by Position (Beam Reference)

After extrusion + segmentation, identify which faces are caps vs walls by their median position:

```python
final_start_caps = []
final_end_caps   = []
final_walls      = []

bm.faces.ensure_lookup_table()
for f in bm.faces:
    cen = f.calc_center_median()
    if abs(cen.y) < 0.01:                           # Start cap at Y ≈ 0
        final_start_caps.append(f)
    elif abs(cen.y - self.length) < 0.01:           # End cap at Y ≈ length
        final_end_caps.append(f)
    else:
        final_walls.append(f)
```

This categorization is then used for:
- Slot assignment (caps → slot 1, walls → slot 0)
- Normal forcing (caps need outward-pointing normals)
- Seam marking (cap edges all get `e.seam = True`)
- UV strategy (caps use analytic mapping, walls use arc-length)

### 5.6 Forcing Normals Explicitly (Beam Reference)

> **Never trust `recalc_face_normals` alone on extruded profiles.** It can flip caps inward when the profile is concave (I-Beam, C-Channel). Always force cap normals manually based on their position.

```python
# Start caps must point -Y
for f in final_start_caps:
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()

# End caps must point +Y
for f in final_end_caps:
    f.normal_update()
    if f.normal.y < 0:
        f.normal_flip()

# Walls: recalc against the now-correct caps
bm.normal_update()
if final_walls:
    bmesh.ops.recalc_face_normals(bm, faces=final_walls)
```

**Key points:**
- Use `f.normal_update()` to compute the current normal from vertex order before checking it.
- Pass `faces=final_walls` (a specific list) to `recalc_face_normals` — **not** all faces. Once caps are correctly oriented, blanket recalc could flip them back.
- Call `bm.normal_update()` once between the cap fix and the wall recalc.

### 5.7 Slot Assignment by Geometric Role

Once faces are categorized, assign material indices by role — not by index ordering:

```python
for f in final_start_caps: f.material_index = 1   # Caps
for f in final_end_caps:   f.material_index = 1   # Caps
for f in final_walls:      f.material_index = 0   # Surface
```

This makes the cartridge robust against the engine reordering faces during cleanup passes.

### 5.8 Safety Idioms

| Idiom | Why |
|:---|:---|
| `bm.verts.ensure_lookup_table()` (and `.edges`, `.faces`) after raw `bm.verts.new()` / `bm.faces.new()` calls | BMesh indices are invalidated by mutations. Indexing without `ensure_lookup_table` may crash. |
| `try: f = bm.faces.new(verts) except ValueError: return` | `faces.new` raises `ValueError` if verts are collinear, duplicated, or already in a face. |
| `if not f.is_valid: continue` inside face iteration | Polish operations may delete faces mid-loop. |
| `bm.faces[:]` / `bm.edges[:]` / `bm.verts[:]` to snapshot before mutation | `bmesh.ops.bisect_plane` etc. expect a frozen list, not a live iterator. |

---

## 6. Edge Slots & Seams

### 6.1 Edge Slot Layer (`MASSA_EDGE_SLOTS`)

You **must** create or retrieve the `MASSA_EDGE_SLOTS` integer layer to assign Edge Roles.

```python
edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
# or to retrieve if it might already exist:
edge_slots = (bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
              or bm.edges.layers.int.new("MASSA_EDGE_SLOTS"))
```

| ID | Name | Default Behaviour | Use For |
|:---|:---|:---|:---|
| **0** | None | Smooth / unassigned | Default state |
| **1** | **Perimeter** | Seam + Sharp + Bevel | Outer silhouette, end-cap borders |
| **2** | **Contour** | Sharp + Bevel | Internal hard 90° angles (not perimeter) |
| **3** | **Guide** | Seam Only | Manual UV cut lines — cylinders, tubes, longitudinal cuts |
| **4** | **Detail** | Bevel Only | Small chamfers, soft feature lines (no shading change) |
| **5** | **Fold** | Crease | Subdivision crease, cloth pin (manual only) |

Per-role behaviour is user-configurable via the Console's EDGES tab (`edge_slot_N_action`), defaulting to the above.

### 6.2 The Auto-Detect Synergy

> **Beam Reference Insight (line 204):** `# REMOVED: e[edge_slots] = 1 (Let auto-detect handle Perimeters)`

The engine runs `auto_detect_edge_slots` after `build_shape` (when `edge_auto_detect = True`, the default). It assigns Edge Slot 1 (Perimeter) based on material boundaries and geometric analysis. **You usually do NOT need to tag perimeter edges manually** — let auto-detect do it.

**Manually tag only:**
- **Slot 3 (Guide)** for longitudinal seams on cylinders, tubes, and beam walls — auto-detect cannot infer these.
- **Slot 5 (Fold)** for crease weights — manual only.
- **Slot 1/2** if you specifically want to override auto-detection (e.g. a hidden internal edge that auto-detect would miss).

### 6.3 Marking Cap Seams

For all cap edges, set `e.seam = True` directly (in addition to leaving them un-tagged in `edge_slots` so auto-detect handles them as Perimeter):

```python
for f in final_start_caps + final_end_caps:
    for e in f.edges:
        e.seam = True
        # NOTE: e[edge_slots] = 1 is intentionally omitted — auto-detect handles it
```

This guarantees the cap boundary is a UV seam even if auto-detect's heuristic misses an edge.

### 6.4 The Longitudinal Seam Algorithm (Beam Reference)

For closed-loop walls (any extruded profile), you need exactly ONE seam line running the length of the extrusion to allow UV unwrapping. Use `pts[0]` (the first profile corner) as the known seam line:

```python
if pts:
    seam_x = pts[0][0]
    seam_z = pts[0][1]

    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        v1, v2 = e.verts[0], e.verts[1]

        # Both vertices must lie on the (seam_x, seam_z) line (any Y)
        on_seam_1 = (abs(v1.co.x - seam_x) < 0.005) and (abs(v1.co.z - seam_z) < 0.005)
        on_seam_2 = (abs(v2.co.x - seam_x) < 0.005) and (abs(v2.co.z - seam_z) < 0.005)

        if on_seam_1 and on_seam_2:
            e.seam            = True
            e[edge_slots]     = 3                # Slot 3: Guide
```

**Key points:**
- Tolerance `0.005` (5mm at unit scale) is loose enough to survive floating point but tight enough to avoid false positives.
- Tagging as Slot 3 (Guide) means the Console's edge viz will show this seam in the Guide color, and the seam solver will respect it.
- Both `e.seam = True` AND `e[edge_slots] = 3` are set — the first is the hard Blender seam, the second is the Massa role marker.

For non-corner profiles (circles, ellipses), pick any known vertex position as the seam guide.

### 6.5 Segment Cut Seams (Beam Reference)

When `segments_y > 0`, the bisect cuts create ring edges. Tag them as Guide so the user can manipulate them later:

```python
if self.segments_y > 0:
    for e in bm.edges:
        # Segment cuts are perpendicular to Y → both verts share Y coordinate
        if abs(e.verts[0].co.y - e.verts[1].co.y) < 0.001:
            # Filter out cap edges (Y ≈ 0 and Y ≈ length)
            if 0.01 < e.verts[0].co.y < (self.length - 0.01):
                e[edge_slots] = 3                # Slot 3: Guide
```

This geometric detection works because `bisect_plane` doesn't return a clean list of newly-created edges — we detect them by the fact that segment cuts are perpendicular to the extrusion axis.

---

## 7. UV Mandate: Manual & Precise

**Golden Cartridges do not rely on auto-unwrapping.** UVs must be calculated mathematically inside `build_shape`.

### 7.1 Setup

```python
uv_layer = bm.loops.layers.uv.verify()
```

`verify()` creates the layer if missing, returns it if present.

### 7.2 Dual-Mode Scaling: `uv_scale` vs `fit_uvs`

Every cartridge that writes manual UVs supports two modes:

| Mode | Behaviour | Use Case |
|:---|:---|:---|
| `fit_uvs = False` (default) | UVs are in world units × `uv_scale`. A 1m wall with `uv_scale = 1.0` produces UVs from 0 to 1. A 2m wall produces UVs 0 to 2 (tiles the texture). | Tiled textures, consistent texel density |
| `fit_uvs = True` | UVs are normalized so the entire surface fits within 0–1. | Single-instance textures, decals, displays |

**Beam Reference pattern:**

```python
# Walls: arc-length on U, length on V
su_s = (1.0 / perim)       if (self.fit_uvs and perim > 0) else self.uv_scale
sv_s = (1.0 / self.length) if self.fit_uvs                  else self.uv_scale

# Caps: width on U, height on V
su_c = (1.0 / self.width)  if self.fit_uvs else self.uv_scale
sv_c = (1.0 / self.height) if self.fit_uvs else self.uv_scale
```

### 7.3 Arc-Length U Calculation (Beam Reference)

For walls of an extruded profile, U is the arc length walked along the profile from the seam corner. Compute the perimeter and a `get_u(x, z)` helper:

```python
perim = sum(
    math.hypot(pts[(i+1) % len(pts)][0] - pts[i][0],
               pts[(i+1) % len(pts)][1] - pts[i][1])
    for i in range(len(pts))
)

def get_u(x, z):
    """Returns arc length from pts[0] along the profile to the point (x, z)."""
    cu = 0.0
    for i in range(len(pts)):
        p1 = pts[i]
        if math.hypot(p1[0] - x, p1[1] - z) < 0.002:
            return cu
        pn  = pts[(i+1) % len(pts)]
        cu += math.hypot(pn[0] - p1[0], pn[1] - p1[1])
    return 0.0
```

Then for each wall loop, U = `get_u(vert.x, vert.z)`, V = `vert.y`.

### 7.4 Per-Slot UV Strategies

Different slots get different UV math. The Beam Reference handles two:

```python
for f in bm.faces:
    if not f.is_valid:
        continue

    if f.material_index == 1:                    # CAPS — analytic XZ → UV
        for l in f.loops:
            u = (l.vert.co.x + hw) * su_c
            v =  l.vert.co.z       * sv_c
            l[uv_layer].uv = (u, v)

    else:                                         # WALLS — arc-length + wrapping fix
        loop_uvs = []
        for l in f.loops:
            ua = get_u(l.vert.co.x, l.vert.co.z)
            va = l.vert.co.y
            loop_uvs.append([l, ua, va])
        # ... wrapping fix (next section) ...
        for l, u, v in loop_uvs:
            l[uv_layer].uv = (u * su_s, v * sv_s)
```

### 7.5 The Wrapping Fix (Cylindrical Seam) (Beam Reference)

**This is the most-missed pattern.** For any closed-loop surface (extruded profile, cylinder, sphere), one face will span the seam — its loops have U coordinates at both ~0 and ~perimeter. Without a fix, that face renders as a smeared band across the entire texture.

**The fix:** detect spanning faces and shift the small U values up by the perimeter.

```python
# Compute all loop UVs first
loop_uvs = []
for l in f.loops:
    ua = get_u(l.vert.co.x, l.vert.co.z)
    va = l.vert.co.y
    loop_uvs.append([l, ua, va])

# Detect wrapping: if U range exceeds 50% of perimeter, this is the closing face
us = [item[1] for item in loop_uvs]
if (max(us) - min(us)) > (perim * 0.5):
    # Shift small U values up by perimeter so all loops land near max
    for item in loop_uvs:
        if item[1] < (perim * 0.5):
            item[1] += perim

# Now apply scale and write to layer
for l, u, v in loop_uvs:
    l[uv_layer].uv = (u * su_s, v * sv_s)
```

This pattern applies to any closed-loop UV mapping — pipes, tubes, columns, tanks, any radial geometry.

---

## 8. Socket Protocols

Sockets are attachment points for the Massa ecosystem (snapping, physics constraints, child placement). They are **always derived from existing geometry** — never from extra helper meshes.

### 8.1 Standard: Tag Existing Faces

**Two tagging methods:**

**Method A — Slot-based** (in `get_slot_meta`):

```python
def get_slot_meta(self):
    return {
        0: {"name": "Body",   "uv": "SKIP", "phys": "METAL_STEEL"},
        9: {"name": "Anchor", "uv": "SKIP", "phys": "GENERIC", "sock": True},
    }
```

Then in `build_shape`, assign `f.material_index = 9` to faces you want to be sockets. The engine will derive socket transforms from each tagged face's center and normal.

**Method B — Builder-based** (preferred when geometry doesn't map cleanly to a slot):

```python
from ...modules.massa_builder import MassaBuilder

builder = MassaBuilder(bm)
builder.create_box(1, 1, 1).translate(0, 0, 0.5)
builder.clean()

# Top face → Socket 2
builder.select_faces_by_normal(Vector((0, 0,  1))).tag_socket(2)
# Bottom face → Socket 1 (origin anchor)
builder.select_faces_by_normal(Vector((0, 0, -1))).tag_socket(1)
```

`tag_socket(id)` writes to the `MASSA_SOCKETS` BMesh integer layer (created automatically by the engine before `build_shape` runs).

### 8.2 Socket Object Naming Convention

The engine spawns one Empty per socket, named:

```
SOCKET_<obj_name>_<slot_name>_<index>
```

- `<obj_name>` = the operator's `bl_label` (used as object name).
- `<slot_name>` = the `name` from the corresponding slot meta (e.g. `"Surface"`, `"Anchor"`).
- `<index>` = 2-digit zero-padded index for that slot.

Knowing this name format is critical if you want to customize socket transforms in an `execute()` override (§8.3).

### 8.3 Customizing Socket Orientation (`execute()` Override) (Beam Reference)

By default, sockets are oriented with Z+ pointing along the tagged face's normal. For some cartridges (the beam being a prime example), this isn't desired — the beam's wall sockets would point sideways (±X), but you want them to point along the beam's local Z+ for consistent snapping.

**Pattern: override `execute()`, call `super().execute()`, then post-process socket children:**

```python
def execute(self, context):
    # 1. Run standard generation
    result = super().execute(context)

    # 2. Post-process: re-orient specific sockets
    if "FINISHED" in result:
        obj = context.active_object
        if obj:
            # Sockets for slot 0 ("Surface") have name prefix:
            #   SOCKET_<obj.name>_Surface
            target_prefix = f"SOCKET_{obj.name}_Surface"

            for child in obj.children:
                if child.name.startswith(target_prefix):
                    # Force identity rotation → align with beam's local Z+
                    child.rotation_euler = (0, 0, 0)

    return result
```

**Key points:**
- Always call `super().execute(context)` first and check that the result is `"FINISHED"` before post-processing.
- `context.active_object` is the just-generated object.
- Iterate `obj.children` and filter by name prefix to find specific sockets.
- Modifying `child.rotation_euler`, `child.location`, etc. is safe here because `_generate_output` has already spawned the empties.

This pattern works for any post-generation customization that requires `bpy.context` — including modifier tweaks, custom properties, drivers, etc.

---

## 9. UI Standards (`draw_shape_ui`)

Implement `draw_shape_ui(self, layout)` to expose shape parameters in the Redo Panel's SHAPE tab.

**Beam Reference pattern:**

```python
def draw_shape_ui(self, layout):
    layout.label(text="PROFILE (XZ Plane)", icon="MESH_DATA")
    layout.prop(self, "profile_type", text="")
    col = layout.column(align=True)
    col.prop(self, "width")
    col.prop(self, "height")
    if self.profile_type != "BOX":
        layout.prop(self, "thickness")

    layout.separator()
    layout.label(text="EXTRUSION (Y+)", icon="AXIS_SIDE")
    layout.prop(self, "length")

    layout.separator()
    layout.label(text="TOPOLOGY", icon="MOD_WIREFRAME")
    layout.prop(self, "segments_y")
```

**Guidelines:**

- **Group with `layout.label(text="GROUP", icon="…")`** then either `layout.prop` or a `col = layout.column(align=True); col.prop(...)` for the group's properties.
- **`layout.separator()`** between groups for vertical breathing room.
- **`align=True` on columns** for visually grouped numeric props.
- **Conditional UI**: `if self.profile_type != "BOX": layout.prop(self, "thickness")` — only show thickness when relevant.
- **Standard icons**: `MESH_DATA`, `MOD_WIREFRAME`, `FIXED_SIZE`, `MOD_SOLIDIFY`, `AXIS_SIDE`, `OUTLINER_DATA_SURFACE`.

> The `uv_scale` / `fit_uvs` properties go in the UVs tab (handled automatically by `ui_shared.draw_uvs_tab`). Do **not** include them in `draw_shape_ui`.

---

## 10. Edge Slot Visualization (`viz_edge_mode = SLOTS`)

The Console's `viz_edge_mode = SLOTS` overlay (`massa_vis_overlay`) renders each Edge Slot in a distinct color so the user can verify Edge Role assignment at a glance.

**For your cartridge's SLOTS view to look correct:**

1.  **Tag Slot 3 (Guide) edges manually** in `build_shape` — these are the most visible feedback because they should form continuous lines along extrusions, around the perimeter of cylinders, and around segment cuts.
2.  **Do NOT tag Slot 1 (Perimeter) manually** — let `edge_auto_detect` handle it. If you tag it manually AND auto-detect runs, you may double-tag and confuse the visualization. (See §6.2.)
3.  **Mark `e.seam = True` on cap boundaries** — even though they're not in `MASSA_EDGE_SLOTS`, the Console's NATIVE viz shows seams, and downstream UV tools depend on them.
4.  **Slot 3 must form continuous loops** — isolated Guide edges trigger `WARNING_ISOLATED_SEAM_EDGES_N` in the audit and look broken in SLOTS view.

The Beam Reference produces a textbook-clean SLOTS visualization:
- Slot 1 (auto): around both cap perimeters and along the four profile corners.
- Slot 3 (manual): one longitudinal line along `pts[0]` corner + rings at each segment cut.

---

## 11. Cartridge Self-Audit Checklist

Before considering a cartridge "Golden," verify all of the following:

**Structural:**
- [ ] `CARTRIDGE_META` defined with required keys (`name`, `id`, `icon`, `flags`)
- [ ] `id` matches `bl_idname` suffix exactly (`massa.gen_<id>`)
- [ ] Class inherits `Massa_OT_Base`
- [ ] `get_slot_meta()` defined with valid `phys` keys from `MASTER_MAT_DB`
- [ ] `build_shape(self, bm)` defined — no `bpy.ops`, no `bpy.context` reads
- [ ] `uv_scale` and `fit_uvs` properties present
- [ ] `draw_shape_ui(self, layout)` defined

**Geometry:**
- [ ] No loose vertices (all `bm.verts` connected to at least one edge)
- [ ] No non-manifold edges (no T-junctions, no holes)
- [ ] No zero-area faces
- [ ] No thin sliver faces (perimeter² / area < 1000)
- [ ] Cap normals point outward (caps face away from interior)
- [ ] Y-axis is length (for extruded cartridges)
- [ ] Phase-numbered comments in `build_shape`
- [ ] `bm.verts.ensure_lookup_table()` called after raw vert creation
- [ ] `try/except ValueError` around `bm.faces.new()` when verts come from user input

**Edge Slots & Seams:**
- [ ] `MASSA_EDGE_SLOTS` layer created
- [ ] At least one Slot 1 OR Slot 3 edge tagged (manually or by auto-detect)
- [ ] Slot 3 (Guide) edges form continuous loops (no isolated guides)
- [ ] Cap edges have `e.seam = True` (for extruded cartridges)
- [ ] Auto-detect synergy respected (don't double-tag Perimeter)

**UVs:**
- [ ] `bm.loops.layers.uv.verify()` called
- [ ] All non-`"SKIP"` slots produce non-zero UV data
- [ ] Wrapping fix applied for closed-loop surfaces (perim-spanning faces)
- [ ] Both `fit_uvs` modes produce sensible results
- [ ] No collapsed UVs (zero-area UV islands)
- [ ] No UV spikes (extreme distortion)

**Sockets (if used):**
- [ ] Sockets tagged on existing faces — no extra geometry created
- [ ] Slot 9 used as canonical Anchor (if applicable)
- [ ] `execute()` override (if present) calls `super().execute(context)` first

**Audit Run:**
```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<your_cartridge>.py \
  --mode AUDIT

python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<your_cartridge>.py \
  --mode UV_INSPECT

python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/<your_cartridge>.py \
  --mode UV_HEATMAP
```

**Pass criteria:** Zero `CRITICAL_*` flags. UV layout fits within 0–1 bounds when `fit_uvs = True`. No overlapping islands. Distortion heatmap is mostly blue/green (no large red areas).

---

## 12. Anatomy of the Golden Beam — End-to-End Walkthrough

[`cart_prim_01_beam.py`](massa/modules/cartridges/cart_prim_01_beam.py) is the reference implementation. Every pattern in this mandate is exercised by it. Reading it top-to-bottom alongside this section is the fastest way to internalize the Mandate.

| Lines | Phase | Pattern Demonstrated |
|:---|:---|:---|
| 1-6 | Imports | Standard imports + base operator |
| 8-18 | `CARTRIDGE_META` | All required keys + `scale_class` + capability flags |
| 21-24 | Class declaration | `bl_idname` matching `id`, full `bl_options` |
| 26-36 | `profile_type` | EnumProperty driving multi-variant geometry |
| 37-44 | Dimensions | Y-axis-is-length axis convention with comment |
| 43 | `segments_y` | `IntProperty` with `soft_max=50` |
| 47-48 | `uv_scale` / `fit_uvs` | Required dual-mode UV properties |
| 50-54 | `get_slot_meta` | Slot 0 = Surface (SKIP), Slot 1 = Caps (BOX) — structural convention |
| 56-72 | `draw_shape_ui` | Labeled groups, separators, conditional `thickness` prop |
| 74-122 | Phase 1: Profile | EnumProperty switch building 2D point list in XZ plane |
| 124-137 | Phase 2: Extrusion | Clean extrusion idiom — `verts → cap → extrude_face_region → translate` |
| 139-154 | Phase 3: Segmentation | `bisect_plane` loop with `geom_all` snapshot |
| 156-187 | Phase 4: Normals | Face categorization by position + explicit cap normal forcing + targeted wall recalc |
| 189-195 | Phase 5: Slots | Slot assignment by geometric role |
| 197-237 | Phase 6: Seams | Cap seams + longitudinal Guide algorithm + segment cut detection |
| 239-291 | Phase 7: UVs | Per-slot UV strategies + arc-length `get_u` + wrapping fix |
| 293-318 | `execute()` override | Post-process socket re-orientation via `super().execute()` + child name prefix scan |

If you've never written a Cartridge before, **read the Beam Reference first.** Then read this mandate. Then write your cartridge.

---

> **Massa Cartridge Mandate v2.0**
> *Reference: `cart_prim_01_beam.py`*
> *Maintained by 3D_Massa*
