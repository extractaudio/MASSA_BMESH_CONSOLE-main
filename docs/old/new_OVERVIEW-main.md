# MASSA CONSOLE ARCHITECTURE (v6.6)

> **"The Console is Law. The Cartridge is Art."**

This document defines the strict protocols for the **MASSA_BMESH_CONSOLE** system. It unifies the "Mandates" (Rules) with the "Architecture" (System) to ensure stability, resurrection, and clean geometry.

---

## 📑 Table of Contents

1.  [The Philosophy](#1-the-philosophy)
2.  [The Cartridge Blueprint (The 95% Standard)](#2-the-cartridge-blueprint-the-95-standard)
    *   [Class Structure](#a-class-structure)
    *   [MassaBuilder — Fluent API](#b-massabuilder--fluent-api)
    *   [The Golden Rules (Mandates)](#c-the-golden-rules-mandates)
    *   [Slot Protocol (Faces 0-9)](#d-slot-protocol-faces-0-9)
    *   [Edge Protocol (Edges 0-5)](#e-edge-protocol-edges-0-5)
    *   [UV Strategy](#f-uv-strategy)
    *   [Physics Material IDs](#g-physics-material-ids)
3.  [System Architecture (The Anatomy)](#3-system-architecture-the-anatomy)
    *   [Brain (State)](#brain-state)
    *   [Muscle (Operator)](#muscle-operator)
    *   [Engine (Pipeline)](#engine-pipeline)
    *   [Polish Stack](#polish-stack)
    *   [Seam Solver](#seam-solver)
    *   [Shooter (Targeting)](#shooter-targeting)
    *   [Observer (Analytics)](#observer-analytics)
    *   [Phase 4 — Physics & Socket Forge](#phase-4--physics--socket-forge)
4.  [Modification Workflow](#4-modification-workflow)
    *   [Adding Parameters (The Rule of Five)](#adding-parameters-the-rule-of-five)
    *   [Resurrection System](#resurrection-system)
    *   [Headless Safety](#headless-safety)
5.  [Tooling & Execution Environment](#5-tooling--execution-environment)
6.  [Telemetry & Troubleshooting](#6-telemetry--troubleshooting)

---

## 1. The Philosophy

**MASSA** is a Blender 5.0 addon for generating complex, production-ready 3D assets — architectural structures, industrial equipment, urban furniture, mechanical assemblies, and more — through a library of 130+ parametric **Cartridges**. Every generated object stays fully live and editable (via Blender's Redo Panel) until explicitly finalized. The engine automatically handles UVs, physics materials, edge sharpness, seam solving, bevels, UCX collision, and socket constraints; cartridge authors only need to define shape.

The Massa Console is a **Procedural Engine** that consumes **Cartridges** (Generators).

*   **The Console** handles the "Boring Stuff": UI, Undo/Redo, Material Assignment, UV Unwrapping, Physics Generation, Socket Constraints, Polish (Bevels/Chamfers/Fuse), Seam Solving, and Data Layer Baking.
*   **The Cartridge** handles the "Fun Stuff": Pure BMesh geometry generation (`build_shape`).

**Goal:** A Cartridge should only focus on *shape*. If it follows the **Mandates**, the Console grants it superpowers (Auto-UVs, Physics, UCX Collision, Socket Forge) for free.

---

## 2. The Cartridge Blueprint (The 95% Standard)

To achieve "First-Time-Right" code generation, every Cartridge **MUST** follow this exact structure.

### A. Class Structure

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

# ---------------------------------------------------------
# 1. METADATA (Required for auto-discovery)
# ---------------------------------------------------------
CARTRIDGE_META = {
    "name": "PRIM_XX: Cartridge Name",    # Human-readable UI label
    "id":   "prim_xx_name",               # MUST match bl_idname suffix
    "icon": "MESH_CUBE",                   # Blender icon ID
    "scale_class": "STANDARD",            # MICRO | STANDARD | MACRO
    "flags": {
        "USE_WELD":       True,            # Merge verts by distance
        "ALLOW_SOLIDIFY": True,            # Can engine add thickness?
        "ALLOW_FUSE":     True,            # Allow SDF Fuse bevel?
        "ALLOW_CHAMFER":  True,            # Allow Chamfer polish?
        "FIX_DEGENERATE": True,            # Auto-clean zero-area faces
        "LOCK_PIVOT":     False,           # Keep origin at gen start point
        "REMOVE_LOOSE":   True,            # Delete unconnected vertices
    },
}

class MASSA_OT_prim_xx_name(Massa_OT_Base):
    bl_idname = "massa.gen_prim_xx_name"  # Prefix 'massa.gen_' is MANDATORY
    bl_label  = "PRIM_XX: Cartridge Name"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # ---------------------------------------------------------
    # 2. PARAMETERS (Blender Properties)
    # ---------------------------------------------------------
    radius:   bpy.props.FloatProperty(name="Radius",   default=1.0, min=0.1,  unit="LENGTH")
    segments: bpy.props.IntProperty(  name="Segments", default=16,  min=3)

    # ---------------------------------------------------------
    # 3. SLOT DEFINITIONS — The 'Hard 10' (0-9)
    # ---------------------------------------------------------
    def get_slot_meta(self):
        """
        Maps Slot Index (0-9) → {name, uv, phys, sock?}.
        'phys' drives the Visual Material default AND the Physics ID layer.
        """
        return {
            0: {"name": "Hull",    "uv": "BOX",    "phys": "METAL_STEEL"},
            1: {"name": "Detail",  "uv": "BOX",    "phys": "CONCRETE_RAW"},
            2: {"name": "Trim",    "uv": "TUBE_Z", "phys": "METAL_IRON"},
            9: {"name": "Socket",  "uv": "SKIP",   "phys": "GENERIC", "sock": True},
        }

    # ---------------------------------------------------------
    # 4. SHAPE UI (Redo Panel — SHAPE tab)
    # ---------------------------------------------------------
    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "segments")

    # ---------------------------------------------------------
    # 5. EXECUTION CORE — "The Fun Stuff"
    # ---------------------------------------------------------
    def build_shape(self, bm: bmesh.types.BMesh):
        """
        Generates geometry into 'bm'. NO bpy.ops allowed here.
        Use bmesh.ops or MassaBuilder (preferred) for all geometry.
        """
        # [PHASE 1] Acquire edge slot layer (ALWAYS do this first)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") \
                     or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # [PHASE 2] Build geometry using bmesh.ops or MassaBuilder
        ret = bmesh.ops.create_cone(
            bm, cap_ends=True,
            radius1=self.radius, radius2=self.radius,
            depth=2.0, segments=self.segments
        )

        # [PHASE 3] Assign material slots to faces
        for f in bm.faces:
            f.material_index = 0  # All to Hull by default

        # Assign caps to a different slot
        for f in bm.faces:
            if abs(f.normal.z) > 0.9:
                f.material_index = 1  # Caps → Detail slot

        # [PHASE 4] Tag edge roles (drives Seam/Sharp/Bevel post-process)
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1  # Perimeter → Seam + Sharp + Bevel

        # [PHASE 5] Tag socket face (optional)
        for f in bm.faces:
            if f.normal.z > 0.9:
                f.material_index = 9  # Top face → Socket slot

        # [PHASE 6] Mandatory cleanup
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
```

---

### B. MassaBuilder — Fluent API

`MassaBuilder` ([`massa/modules/massa_builder.py`](massa/modules/massa_builder.py)) is the **preferred** way to generate geometry inside `build_shape`. It wraps raw `bmesh.ops` behind a chainable interface and tracks `active_faces`, `active_edges`, and `active_verts` automatically.

```python
from ...modules.massa_builder import MassaBuilder

def build_shape(self, bm: bmesh.types.BMesh):
    builder = MassaBuilder(bm)

    # 1. Create base geometry
    builder.create_box(width=2.0, depth=2.0, height=1.0,
                       center=Vector((0, 0, 0.5)))
    builder.tag_slot(0)                           # Assign slot 0 to active faces

    # 2. Select top face and extrude a step
    builder.select_faces_by_normal(Vector((0, 0, 1))) \
           .inset(0.2, relative=False) \
           .extrude(0.5) \
           .tag_slot(1)                           # Step sides → slot 1

    # 3. Re-select top, assign accent material
    builder.select_faces_by_normal(Vector((0, 0, 1))) \
           .tag_slot(2)

    # 4. Tag top face as socket anchor
    builder.select_faces_by_normal(Vector((0, 0, 1))) \
           .tag_socket(1)

    # 5. Always clean at the end
    print(builder.report())
    builder.clean()
```

**Core `MassaBuilder` methods:**

| Method | Description |
|:---|:---|
| `create_box(w, d, h, center)` | Creates a box, sets `active_faces` |
| `create_grid(x_segs, y_segs, size, center)` | Grid on XY plane |
| `create_cylinder(radius, depth, segs, center)` | Cylinder |
| `extrude(amount)` | Extrudes `active_faces`, updates `active_faces` to new top |
| `inset(amount, relative)` | Insets `active_faces`, returns inner ring |
| `select_faces_by_normal(normal, threshold)` | Replaces `active_faces` by normal direction |
| `tag_slot(index)` | Assigns `material_index` to `active_faces` |
| `tag_socket(id)` | Tags `active_faces` in `MASSA_SOCKETS` layer |
| `clean()` | `remove_doubles` + `recalc_face_normals` |
| `report()` | Returns debug string: vert/edge/face/slot counts |

---

### C. The Golden Rules (Mandates)

1.  **Pure BMesh Inside `build_shape`**: Never call `bpy.ops.*` inside `build_shape`. It crashes in headless/background mode. Use `bmesh.ops`, `MassaBuilder`, or pure `mathutils`.
2.  **No Loose Geometry**: Always run `bmesh.ops.remove_doubles` and `bmesh.ops.recalc_face_normals` at the end. The engine also runs `FIX_DEGENERATE` cleanup automatically if the flag is set.
3.  **Inheritance**: Must inherit `Massa_OT_Base` (which inherits `MassaPropertiesMixin`).
4.  **Metadata**: Must provide valid `CARTRIDGE_META` with all required keys (`name`, `id`, `icon`, `flags`) and implement `get_slot_meta()`.
5.  **Context Safe**: Do not assume `bpy.context.object` or `bpy.context.view_layer` exists inside `build_shape`. Work only on `bm`.
6.  **Never Rename Properties**: Renaming any property on `MassaPropertiesMixin` or a Cartridge breaks the Resurrection system for all existing generated objects that have `obj["MASSA_PARAMS"]` stored. Deprecate with a migration path instead.

---

### D. Slot Protocol (Faces 0-9)

**Assignment in `build_shape`:** `f.material_index = ID`

The 10-slot system provides semantic material zones. All faces must be assigned a slot index (0–9). Un-assigned faces default to `0`. Slot 9 is the canonical Socket/Anchor slot.

| ID | Semantic Role | Suggested Use |
|:---|:---|:---|
| **0** | **BASE / HULL** | Main body, structural shell |
| **1** | **DETAIL** | Vents, grilles, recessed panels |
| **2** | **TRIM / FRAME** | Borders, lips, rims |
| **3** | **GLASS / SCREEN** | Windows, displays, transparencies |
| **4** | **EMISSION** | Lights, indicator strips, energy |
| **5** | **DARK** | Inner cavities, tire rubber, shadow areas |
| **6** | **ACCENT** | Decals, stripes, markings |
| **7** | **UTILITY** | Bolts, rivets, small hardware |
| **8** | **TRANSPARENT** | Force fields, ghost surfaces |
| **9** | **SOCKET / ANCHOR** | Invisible attachment point (spawns Empty) |

**Slot behaviours driven by Console properties (per slot `i`):**

| Property | Behaviour |
|:---|:---|
| `mat_i` | Visual material override |
| `phys_mat_i` | Physics material ID |
| `uv_mode_i` | UV mapping strategy |
| `uv_scale_i` | UV tiling scale |
| `sep_i` | Detach slot as separate child mesh |
| `prot_i` | Protect slot from Polish operations |
| `sock_i` | Mark slot as socket anchor |
| `off_i` | Face extrude offset |
| `collision_shape_i` | UCX shape: BOX/HULL/SPHERE/CAPSULE/MESH |

---

### E. Edge Protocol (Edges 0-5)

**Assignment in `build_shape`:**
```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") \
             or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
e[edge_slots] = ROLE_ID
```

The `MASSA_EDGE_SLOTS` integer layer on BMesh edges drives all post-process shading and UV operations. Default Blender edge state is left clean by the engine unless a role is assigned.

| ID | Name | Default Behavior | Auto-Detection Logic |
|:---|:---|:---|:---|
| **0** | **None** | Smooth / unassigned | Any edge not matched below |
| **1** | **Perimeter** | **Seam + Sharp** (default; configurable) | Edges between End Caps and side walls |
| **2** | **Contour** | **Sharp** (default) | Internal hard angles (90°+) not on perimeter |
| **3** | **Guide** | **Seam Only** (default) | Pathfinding seam lines on cylindrical surfaces |
| **4** | **Detail** | **Ignore** (default) | Material boundary edges, soft chamfer lines |
| **5** | **Fold** | **Ignore** (default) | Manual only; subdivision crease / cloth pin |

**User-configurable actions** (per-slot in the EDGES tab):

`IGNORE` | `SEAM` | `SHARP` | `BOTH` (Seam+Sharp) | `CREASE` | `BEVEL`

**Auto-Detection:** If `edge_auto_detect = True` (the default), the engine runs `auto_detect_edge_slots` after `build_shape`. This will assign roles based on material boundaries and geometric analysis, then layer on additive sharp detection using the `edge_sharp_convex_angle` / `edge_sharp_concave_angle` thresholds. You can override auto-detection by assigning roles manually in `build_shape` and setting `edge_auto_detect = False` on the operator.

---

### F. UV Strategy

Defined in `get_slot_meta()` under the `"uv"` key, and overridable per-slot in the SLOTS tab via `uv_mode_i`.

| Value | Behaviour | Best For |
|:---|:---|:---|
| `"BOX"` | Tri-planar cube mapping | Hard surface, flat panels, caps |
| `"FIT"` | Stretch UVs to fill 0–1 space | Screens, glass, single-face decals |
| `"TUBE_Z"` | Cylindrical mapping, vertical axis | Pipes, columns, tanks |
| `"TUBE_Y"` | Cylindrical mapping, length axis | Beams, conduits |
| `"TUBE_X"` | Cylindrical mapping, width axis | Horizontal rollers |
| `"UNWRAP"` | LSCM/Angle-Based Unwrap (seam-driven) | Organic shapes, complex surfaces |
| `"SKIP"` | Manual UVs from `build_shape`, or Auto-Unwrap fallback | Golden Cartridges (see Mandate §5) |

**Golden Cartridge UV standard:** Use `"SKIP"` and write UVs manually in `build_shape` via `bm.loops.layers.uv.verify()`. Auto-unwrap is a fallback, not the standard.

**`auto_unwrap` global override:** When enabled on the Console, forces UV packing via Smart Project (or LSCM if seams/slots are active), regardless of per-slot `uv_mode` settings. Islands are packed to 0–1 bounds with `auto_unwrap_margin`.

---

### G. Physics Material IDs

The `"phys"` key in `get_slot_meta()` sets both the default visual material AND the baked physics ID. Valid keys come from `MASTER_MAT_DB` in `mat_utils.py`:

**Structural:** `CONCRETE_RAW`, `CONCRETE_POL`, `CONCRETE_BLOCK`  
**Metals:** `METAL_STEEL`, `METAL_ALUMINUM`, `METAL_IRON`, `METAL_RUST`  
**Wood:** `WOOD_OAK`, `WOOD_PINE`, `WOOD_PAINTED`, `WOOD_ROUGH`  
**Synthetics:** `SYNTH_PLASTIC`, `SYNTH_RUBBER`, `SYNTH_GLASS`  
**Other:** `CERAMIC_TILE`, `FABRIC_CANVAS`, `GENERIC`  
**Debug:** `MASSA_DEBUG_0` through `MASSA_DEBUG_9` (colored debug slots)

The `phys_id` is baked into a `MASSA_PHYS_ID` integer face attribute for export pipelines (UE5 Chaos, etc.).

---

## 3. System Architecture (The Anatomy)

```
massa/__init__.py          ← Registration + hot-reload controller
│
├── modules/massa_console.py       🧠 BRAIN   — Persistent scene state
├── modules/massa_properties.py    🧬 DNA     — Shared property mixin
├── operators/massa_base.py        💪 MUSCLE  — Operator shell + UI
├── modules/massa_engine.py        ⚙️ ENGINE  — Generation pipeline
├── modules/massa_builder.py       🔨 BUILDER — Fluent BMesh API
├── modules/cartridges/            📦 CONTENT — Auto-discovered generators
├── modules/massa_polish.py        ✨ POLISH  — Post-process modifiers
├── modules/massa_surface.py       🎨 SURFACE — Materials, UVs, data layers
├── modules/massa_sockets.py       🔗 SOCKETS — Socket transforms + spawning
├── modules/seam_solvers.py        🧵 SEAMS   — UV seam solving algorithms
├── modules/massa_nodes.py         🌐 NODES   — GN viz overlay tree
├── modules/massa_collision.py     💥 COLLIDE — Collision viewport overlay
├── modules/advanced_analytics.py  🔭 OBSERVE — Debug overlay + telemetry
├── operators/massa_shooter.py     🎯 SHOOTER — Point-and-shoot targeting
├── ui/                            🖼️ UI      — Panel, pie menu, gizmo
└── utils/mat_utils.py             📚 DB      — Material database + UV items
```

---

### Brain (State)

*   **Files**: `modules/massa_console.py`, `modules/massa_properties.py`
*   **Role**: Persistent state shared across all operator invocations.
*   **Key**: `MassaPropertiesMixin` is the **DNA** — defines all shared properties that exist simultaneously on the Scene (`context.scene.massa_console`) and every Operator instance. The mixin is inherited by both `Massa_Console_Props` (Brain) and `Massa_OT_Base` (Muscle).
*   **Property groups** (defined in `MassaPropertiesMixin`):
    *   **Global**: `global_scale`, `draft_mode`
    *   **Transform**: `pivot_mode`, `ui_use_rot`, `rotation`, `use_weld`
    *   **Shading / Edge Logic**: `edge_mode`, `edge_auto_detect`, `edge_angle`, `edge_sharp_convex_*`, `edge_sharp_concave_*`
    *   **Seam Logic**: `seam_active`, `seam_from_angle`, `seam_from_slots`, `seam_from_edges`, `seam_use_peri/cont/guide/detail/fold`, `seam_bias`, `seam_solver_mode`, `seam_orient`, `seam_cluster_tol`, `seam_straightness`, `seam_cleanup_flat/thresh`
    *   **Auto-Unwrap**: `auto_unwrap`, `auto_unwrap_use_slots`, `auto_unwrap_margin`
    *   **UI Tab**: `ui_tab` (SHAPE / DATA / POLISH / UVS / SLOTS / EDGES / COLLISION / SOCKETS)
    *   **Edge Slot Actions**: `edge_slot_1_action` … `edge_slot_5_action`
    *   **Edge Viz**: `viz_edge_mode` (OFF / NATIVE / SLOTS)
    *   **Polish**: `pol_solidify_*`, `pol_bridge_*`, `pol_triangulate_*`, `pol_holes_*`, `pol_symmetrize_*`, `pol_bend_*`, `pol_taper_*`, `pol_noise_*`, `pol_smooth_*`, `pol_plate_*`, `pol_decay_*`, `pol_fuse_*`, `pol_chamfer_*`, `pol_merge_mode`
    *   **Data Layers (Set 1)**: `wear_*`, `thick_*`, `flow_*`, `grav_*`, `cavity_*`
    *   **Data Layers (Set 2)**: `wear2_*`, `flow2_*`, `cover_*`, `peak_*`
    *   **Physics Pipeline**: `phys_gen_ucx`, `phys_bake_strain`, `phys_kinematic_pin`, `phys_auto_rig`, `phys_yield_strength`, `phys_active`, `part_active`
    *   **Debug View**: `debug_view` (NONE / UV / SEAM / DATA_SET_1 / DATA_SET_2 / PHYS / PARTS / PROTECT)
    *   **Per-Slot (×10)**: `mat_i`, `phys_mat_i`, `uv_mode_i`, `uv_scale_i`, `sep_i`, `sock_i`, `off_i`, `prot_i`, `expand_i`, `collision_shape_i`, `show_coll_i`, `phys_friction_i`, `phys_bounce_i`, `phys_bond_i`
    *   **Sockets**: `sock_enable`, `sock_constraint_type`, `sock_break_strength`, `sock_visual_size`

---

### Muscle (Operator)

*   **File**: `operators/massa_base.py` → `Massa_OT_Base`
*   **Role**: The execution shell. Receives user input, syncs state, and calls the engine.
*   **Lifecycle**:
    1.  **`invoke()`**: Syncs Console → Operator (`_sync(from_console=True)`), handles Resurrection (restores `MASSA_PARAMS` from the target object), injects cartridge-specific material defaults (`_inject_cartridge_defaults`), then calls `execute()`.
    2.  **`execute()`**: Deletes old object if resurrecting, cleans UCX/Joint children, runs `massa_engine.run_pipeline(self, context)`, applies stored transform (`obj_location`, `obj_rotation`), syncs Operator → Console.
    3.  **`draw()`**: Renders the Redo Panel UI, delegating to `ui_shared` tab functions.
*   **`_sync(from_console)`**: Bidirectionally syncs all `MassaPropertiesMixin` properties plus all 10 per-slot properties between the operator instance and `context.scene.massa_console`.
*   **`_get_cartridge_meta()`**: Reads `CARTRIDGE_META` from the operator's module.

**`MASSA_OT_ReRun_Active`** (`massa.rerun_active`): Reads `massa_op_id` from the active object, saves `MASSA_PARAMS` + transform to `context.scene["MASSA_TEMP_RESTORE"]`, deletes the object, and re-fires the original operator via `bpy.ops`.

---

### Engine (Pipeline)

*   **File**: `modules/massa_engine.py` → `run_pipeline(op, context)`
*   **Role**: Full generation pipeline from BMesh creation to final Blender object.

**Execution order:**

```
1.  Ensure mat library (mat_utils.ensure_default_library)
2.  Read CARTRIDGE_META flags
3.  bm = bmesh.new()
4.  Ensure MASSA_SOCKETS face layer exists
5.  ── op.build_shape(bm)  ──────────────────────── The Cartridge
6.  FIX_DEGENERATE: apply_cleanup (zero-area + thin faces)  [if flag]
7.  Ensure MASSA_EDGE_SLOTS layer exists
8.  auto_detect_edge_slots(bm)  [if edge_auto_detect]
9.  process_edge_slots(bm, op)  → apply Seam/Sharp/Crease/Bevel
10. auto_detect_sharp_edges(bm, op)  → additive convex/concave sharp
11. bmesh.ops.scale (global_scale) [if ≠ 1.0]
12. apply_transform_alignment(bm, pivot_mode)  [if not LOCK_PIVOT]
13. gather_manifest(op)  → builds manifest[0-9] + active_sockets list
14. apply_protection_mask(bm, manifest)
15. apply_slot_inflation(bm, op)
16. apply_hard_merge(bm, pol_merge_mode)
17. ── _run_polish_stack(bm, op, flags, manifest)  [if not draft_mode]
18. apply_safety_decimate(bm)
19. dissolve_degenerate  [if FIX_DEGENERATE]
20. recalc_face_normals
21. Remove loose verts  [if REMOVE_LOOSE]
22. write_identity_layers(bm, manifest, op)  → MASSA_PHYS_ID, MASSA_PART_ID
23. calculate_physical_stats(bm, manifest)  → vol, mass → massa_temp_stats
24. calculate_transforms(bm, active_sockets)  → socket_data
25. tag_structure_edges(bm, op)  → convex/concave edge tag
26. ── seam solver  [if seam_active]
       apply_base_drivers(bm, ...)
       solve_seams(bm, mode, ...)  [if seam_solver_mode ≠ NONE]
       cleanup_flat_seams(bm, ...)  [if seam_cleanup_flat]
27. generate_surface_maps(bm, op, cvx, cnv)
28. Apply rotation transform  [if ui_use_rot]
29. ── _generate_output(op, context, bm, socket_data, manifest)
```

---

### Polish Stack

Runs as step 17 of the pipeline (`_run_polish_stack`), gated by `op.draft_mode == False`. Each operation is independently toggled by its `pol_*_active` property AND validated against the cartridge's `flags` dict.

| Order | Toggle | Flag Gate | Operation |
|:---|:---|:---|:---|
| 1 | `pol_fuse_active` | `ALLOW_FUSE` | `apply_concave_bevel` — SDF-like bevel at concave intersections |
| 2 | *(always)* | — | `recalc_face_normals` — clean normals after fuse |
| 3 | `pol_solidify_active` | `ALLOW_SOLIDIFY` | `apply_solidify` — add shell thickness |
| 4 | `pol_bridge_active` | — | `apply_bridge_loops` — bridge selected edge loops |
| 5 | `pol_holes_active` | — | `apply_fill_holes` — fill open holes |
| 6 | `pol_symmetrize_active` | — | `apply_symmetrize` — mirror across axis |
| 7 | `pol_taper_active` | — | `apply_taper` — XY taper with curve profile |
| 8 | `pol_bend_active` | — | `apply_bend` — bend along axis by angle |
| 9 | `pol_plate_active` | — | `apply_plating` — panel gap + depth inset per slot |
| 10 | `pol_noise_active` | — | `apply_noise` — vertex displacement noise |
| 11 | `pol_smooth_active` | — | `apply_smooth` — Laplacian smooth |
| 12 | `pol_decay_active` | — | `apply_decay` — random per-face recession |
| 13 | `pol_triangulate_active` | — | `apply_triangulate` — BEAUTY or FIXED |
| 14 | `pol_chamfer_active` | `ALLOW_CHAMFER` | `apply_chamfer` — angle-filtered bevel |

**Post-Polish (always runs):** `apply_safety_decimate`, `dissolve_degenerate`, `recalc_face_normals`, remove loose verts.

**SDF Fuse (post-output):** If `pol_fuse_active` is on, `apply_sdf_fuse` adds a Geometry Nodes modifier using `get_or_create_sdf_fuse_tree()` to blend hard intersections. Slots with `sep_i = True` auto-apply this modifier.

---

### Seam Solver

*   **File**: `modules/seam_solvers.py`
*   **Activated when**: `seam_active = True`
*   **Purpose**: Intelligently places UV seams on the final mesh to produce clean, distortion-free UV islands.

**Pipeline** (step 26):

1.  `apply_base_drivers(bm, use_angle, angle_limit, use_slots, bias, use_edges, edge_mask)` — Marks initial seam candidates from angle threshold and/or edge slot roles (controlled by `seam_use_peri/cont/guide/detail/fold` toggles).
2.  `solve_seams(bm, mode, orient, cluster_tol, straightness, strict_slots)` — Runs the chosen solver algorithm.
3.  `cleanup_flat_seams(bm, threshold, keep_slots)` — Removes seam edges that lie on flat coplanar areas (reduces seam noise).

**Solver modes (`seam_solver_mode`):**

| Mode | Algorithm | Best For |
|:---|:---|:---|
| `NONE` | Angle/Driver only, no solver | Simple flat shapes |
| `HARD_SURFACE` | Planar graph clustering | Mechanical hard-surface |
| `STRIP` | Quad strip following | Paneled surfaces |
| `SMART_TUBE` | Single-cut unroll (Zipper) | Pipes, cylinders, tubes |
| `ORGANIC` | Cylinder detective | Organic / branching forms |
| `BOX_STRIP` | Legacy wall unrolling | Architectural boxes |

`seam_orient` controls the "zipper" hidden-face direction for `SMART_TUBE` / `ORGANIC` (`BACK`, `FRONT`, `LEFT`, `RIGHT`, `BOTTOM`).

---

### Shooter (Targeting)

*   **File**: `operators/massa_shooter.py`
*   **Operators**: `MASSA_OT_ShootDispatcher`, `MASSA_OT_SpawnTarget`
*   **Role**: "Point & Shoot" mode. Places a `Massa_Target` empty in the scene, then dispatches operators to that location/rotation. Injects location and rotation into the operator history for the Redo Panel.

---

### Observer (Analytics)

*   **File**: `modules/advanced_analytics.py`
*   **Class**: `MCP_Overlay`
*   **Role**: Visual debug overlay and telemetry. Reads `debug_view` state and draws diagnostic information on-screen via `bpy.types.SpaceView3D.draw_handler_add`.
*   **Functions**: `get_overlay`, `parse_panel_ast`, `inspect_last_operator` — Parses and overlays property state and mesh telemetry (face count, slot distribution, UV stats) in the 3D viewport.

---

### Phase 4 — Physics & Socket Forge

Runs inside `_generate_output` after the mesh is committed to Blender.

**UCX Collision Generation** (`phys_gen_ucx = True`):
Generates per-slot `UCX_<ObjectName>_<SlotLabel>` collision meshes. Supports five shape types (configurable via `collision_shape_i` per slot):

| Shape | Method |
|:---|:---|
| `BOX` | Axis-aligned bounding box |
| `HULL` | `bmesh.ops.convex_hull` on slot vertices |
| `SPHERE` | Bounding sphere |
| `CAPSULE` | Z-aligned bounding cylinder |
| `MESH` | Exact geometry reconstruction |

UCX objects are parented to the main object, set to `WIRE` display, and hidden from render. Named for UE5 import convention.

**Auto-Rigger** (`phys_auto_rig = True`):
Detects detached child meshes (from `sep_i` slots) and auto-creates `MASSA_JOINT_*` empty objects at each child's boundary edge centroid. Adds Hinge rigid body constraints between parent and child. Breaking threshold is `phys_yield_strength × 1000`.

**Socket Forge** (`sock_enable = True`):
Collects faces tagged in the `MASSA_SOCKETS` BMesh layer (via `builder.tag_socket(id)`), calculates center and Z-aligned normal per socket ID, spawns `SOCKET_<ObjectName>_<ID>` Empty objects parented to the object. Optionally adds Rigid Body Constraints of type `FIXED`, `HINGE`, `SLIDER`, or `SPRING` based on `sock_constraint_type`.

---

## 4. Modification Workflow

### Adding Parameters (The Rule of Five)

To add a new **global** parameter shared between the Console UI and all Operators, you **must** touch exactly 5 locations:

1.  **Brain (Definition)**: Add the property annotation to `MassaPropertiesMixin` in `modules/massa_properties.py`. This is the single source of truth.
2.  **Brain (Scene Registration)**: Verify the property is picked up by `Massa_Console_Props` in `modules/massa_console.py`. Because `Massa_Console_Props` inherits `MassaPropertiesMixin`, any property added to the mixin automatically appears on `context.scene.massa_console`. No manual scene registration needed unless the property requires a non-standard `bpy.types.Scene` override.
3.  **Bridge (Sync List)**: Add the exact property string name to the sync loop inside `Massa_OT_Base._sync()` in `operators/massa_base.py`. The sync method iterates `MassaPropertiesMixin.__annotations__.keys()` automatically, so **for mixin-level properties this is already handled** — you only need to add manually for operator-only props.
4.  **Interface**: Add the UI drawing logic to the appropriate tab function in `ui/ui_shared.py` (e.g., `draw_polish_tab`, `draw_uvs_tab`, `draw_data_tab`).
5.  **Logic**: Implement the effect inside the Engine pipeline — typically in `modules/massa_polish.py`, `modules/massa_engine.py`, `modules/massa_surface.py`, or `modules/seam_solvers.py`.

### Resurrection System

The Resurrection system allows any generated Massa object to be fully re-edited at any time.

*   **How it's saved**: `_capture_operator_params(op)` iterates all non-readonly RNA properties and serializes them into a plain Python dict stored as `obj["MASSA_PARAMS"]`. The operator's `bl_idname` is stored as `obj["massa_op_id"]`.
*   **How it restores**: When `Massa_OT_Base.invoke()` runs and `rerun_mode = True` (or `MASSA_TEMP_RESTORE` is on the scene), it reads `MASSA_PARAMS` from the target object and calls `setattr(self, k, v)` for each key. Material/UV/Seam/Transform properties are intentionally skipped so Console overrides take precedence.
*   **Redo Panel persistence**: The operator's properties are saved in Blender's undo history. `obj_location` and `obj_rotation` are stored as operator properties so they survive redo steps and keep the object in place while the user adjusts shape parameters.
*   **Golden Rule**: **NEVER rename a cartridge property.** Existing objects will fail to resurrect because their `MASSA_PARAMS` stores the old key name. If a rename is unavoidable, write a migration function that reads both old and new key names.

### Headless Safety

*   The Engine and all `build_shape` methods often run in background (headless) Blender.
*   **Never call `bpy.ops.*` inside `build_shape`**. Ops require a full Blender context that doesn't exist headlessly.
*   **Never read `bpy.context.object`** inside `build_shape`. Use only the provided `bm`.
*   **Use `mat_utils.ensure_default_library()`** at the top of any method that creates materials — it is safe to call in headless mode.
*   **UCX and Socket Forge** operations are in `_generate_output` (outside `build_shape`) and are protected by `try/except` blocks with graceful degradation.

---

## 5. Tooling & Execution Environment

> **Do not write custom execution scripts.** The built-in debugging suite at `massa/modules/debugging_system/` covers all audit and test scenarios.

### Setup

Edit `massa/modules/debugging_system/config.py` before using any tool:

```python
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
# macOS: "/Applications/Blender.app/Contents/MacOS/Blender"
# Linux: "/usr/bin/blender"
```

### Tool Reference

All tools spawn a background Blender process and return JSON wrapped in `---AUDIT_START---` / `---AUDIT_END---` markers.

**External entrypoint (from repo root):**

```bash
python _Scripts/test_run_cartridge.py <path/to/cartridge.py> --mode <MODE>
```

**Internal entrypoint (from `massa/` directory):**

```bash
python modules/debugging_system/runner.py --cartridge <path> --mode <MODE>
```

**Live state inspection** (requires an active headless Blender instance):

```bash
# Inline Python
python modules/debugging_system/debug_agent.py --code "import bpy; print(bpy.data.objects.keys())"

# File execution (recommended for complex logic)
python modules/debugging_system/debug_agent.py --file temp_inspect.py
```

### Audit Modes

| Mode | Purpose |
|:---|:---|
| `AUDIT` | Full geometry + topology + UV + seam + fuzz checks (default) |
| `VISUAL_DIFF` | Red/green wireframe overlay comparing two cartridge versions |
| `UV_HEATMAP` | Renders UV distortion heatmap (Red=bad, Blue=good) |
| `UV_INSPECT` | Renders 2D UV layout — check overlaps and out-of-bounds islands |
| `PERFORMANCE` | Execution time (ms) and polycount against budget thresholds |
| `CSG_DEBUG` | Debug boolean/bridge geometry operations |
| `RENDER` | Full render output of the generated mesh |
| `SKILL_EXEC` | Execute a named skill workflow |
| `CONSOLE_AUDIT` | Validates the Console architecture (Brain/Muscle sync) |

**Visual Diff example:**

```bash
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_01_beam.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "modules/cartridges/cart_prim_01_beam_v2.py"}'
```

### Auditor Suite (runs automatically during AUDIT mode)

| Auditor | File | Checks |
|:---|:---|:---|
| **Topology** | `massa_auditor.py` | Empty mesh, flat Z axis, missing slot layer, loose verts, non-manifold, zero-area faces, thin sliver faces |
| **Edge Slots** | `massa_edge_auditor.py` | Missing `MASSA_EDGE_SLOTS` layer, no seams on complex meshes (>12 faces), isolated seam edges |
| **Surface** | `massa_surface_auditor.py` | Missing UV layer, zero UV data, inverted normals, self-intersections, UV spikes, collapsed UVs |
| **Fuzz** | `massa_fuzz_auditor.py` | Randomizes parameters and re-runs generation to catch crashes on edge-case inputs |
| **UI** | `massa_ui_auditor.py` | Validates operator properties and UI draw calls |
| **Topology Extra** | `massa_topology_extra.py` | Extended topology checks beyond base auditor |

### Package the Addon

Creates `_EXPORT/massa.zip` (Blender 5.0 Extension format — `blender_manifest.toml` at ZIP root):

```bash
python _Scripts/package_massa_addon.py
```

The packaging script excludes: `__pycache__/`, `.git/`, `debugging_system/`, `_pkg_env/`, test files, and other dev artifacts.

---

## 6. Telemetry & Troubleshooting

Audit results are returned as JSON with a `"flags"` array. Flags prefixed `CRITICAL_` must be fixed before a cartridge is considered stable. `WARNING_` flags indicate quality issues.

### Topology Flags (`massa_auditor.py`)

| Flag | Meaning | Fix |
|:---|:---|:---|
| `CRITICAL_EMPTY_MESH` | No geometry was created | Check `build_shape` logic; ensure at least one face |
| `CRITICAL_FLAT_Z_AXIS` | Geometry has zero height (bounding box Z = 0) | Check `bmesh.ops.scale` vec or extrusion direction |
| `CRITICAL_MISSING_SLOT_LAYER` | No `MASSA_EDGE_SLOTS` layer found | Create layer: `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` |
| `CRITICAL_NO_PERIMETER_DEFINED` | No edges tagged as role 1 (Perimeter) | Tag silhouette edges: `e[edge_slots] = 1` |
| `CRITICAL_LOOSE_VERTS_N` | N vertices with no connected edges | Run `bmesh.ops.remove_doubles` or delete orphans explicitly |
| `CRITICAL_NON_MANIFOLD_N` | N non-manifold edges (holes or T-junctions) | Check bridge/fill logic; run `recalc_face_normals` |
| `CRITICAL_ZERO_AREA_FACES_N` | N faces with 0.0 area | Check extrusion and bridge ops for collapsed geometry |
| `WARNING_THIN_FACES_N` | N sliver faces (Perimeter² / Area > 1000) | Rebuild those faces; causes UV distortion and bevel artifacts |

### Edge Slot Flags (`massa_edge_auditor.py`)

| Flag | Meaning | Fix |
|:---|:---|:---|
| `WARNING_MISSING_EDGE_SLOTS_LAYER` | Layer exists but no edges are assigned | Assign edge roles in `build_shape` |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | Mesh has >12 faces but zero seam edges | Tag edges with role 1 (Perimeter) or role 3 (Guide) |
| `WARNING_ISOLATED_SEAM_EDGES_N` | N seam edges not connected to a loop | Ensure seam loops are continuous; isolated seams cause UV distortion |

### Surface / UV Flags (`massa_surface_auditor.py`)

| Flag | Meaning | Fix |
|:---|:---|:---|
| `CRITICAL_MISSING_UV_LAYER` | No UV layer on the final mesh | Set UV strategy in `get_slot_meta` or write UVs manually |
| `CRITICAL_ZERO_UV_DATA` | UV layer exists but all UVs are at (0, 0) | Check UV assignment logic in `build_shape` |
| `CRITICAL_INVERTED_NORMALS` | Faces pointing inward | Run `bmesh.ops.recalc_face_normals` at end of `build_shape` |
| `CRITICAL_SELF_INTERSECTION` | Geometry overlaps itself | Check boolean, bridge, and extrusion logic |
| `CRITICAL_UV_SPIKES_N` | N UV islands with extreme distortion | Improve seam placement (roles 1/3) or UV math |
| `CRITICAL_COLLAPSED_UVS_N` | N UV islands collapsed to a point | Check for zero-area faces in UV space; often caused by `CRITICAL_ZERO_AREA_FACES` |

### UV Inspection Protocol

When verifying a new or modified cartridge, always generate and check the UV layout:

```bash
python modules/debugging_system/runner.py --cartridge <path> --mode UV_INSPECT
```

**Check for:**
- Overlapping islands (darker areas in UV space)
- Out-of-bounds geometry (outside 0–1 square)
- Collapsed/zero-size islands

**Fix protocol:**
1. **Collapsed?** → Check `CRITICAL_ZERO_AREA_FACES` first. Fix topology.
2. **Overlapping?** → Add `auto_unwrap = True` or verify manual UV math in `build_shape`.
3. **Bad seams?** → Ensure Edge Slot 1 (Perimeter) and Slot 3 (Guide) are tagged on the right edges.
4. **Distorted?** → Use `UV_HEATMAP` mode; fix seam placement or switch UV strategy.
5. **Scale off?** → Adjust `uv_scale_i` property per slot.

### Common Issues Quick-Reference

| Symptom | Likely Cause | Fix |
|:---|:---|:---|
| Object disappears on Redo | `target_delete_name` issue in Resurrection | Check `invoke()` / `execute()` delete flow |
| UV smearing on cylinder | Missing Guide seam (role 3) | Tag one longitudinal edge: `e[edge_slots] = 3` |
| Bevel artifacts on chamfer | Thin sliver faces near bevel edges | Fix source topology; run `WARNING_THIN_FACES` audit |
| Double geometry on Redo | Child cleanup not catching custom names | Ensure UCX/Joint/Socket names start with `UCX_`, `MASSA_JOINT_`, `SOCKET_` |
| Seams ignored by unwrap | `auto_unwrap_use_slots = False` | Enable "Use Edge Slots" in UVs tab, or set seams via role 1/3 |
| Materials all grey | `ensure_default_library()` not called | Add `mat_utils.ensure_default_library()` at top of `execute()` |
| Physics ID = 0 on all faces | `phys` key missing from `get_slot_meta` | Add valid `"phys"` key to each slot in the meta dict |

---

> **Massa Console Architect v6.6**
> *Blender 5.0 Extension — Maintained by 3D_Massa*
> *End of File*
