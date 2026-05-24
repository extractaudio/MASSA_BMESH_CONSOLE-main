# MASSA BMESH CONSOLE — Master Reference

> **"The Console is Law. The Cartridge is Art."**

**MASSA** is a Blender 5.0 Extension (addon) for generating complex, production-ready 3D assets through a library of 130+ parametric **Cartridges**. It is a split-state procedural engine where:

- **The Console** handles everything systemic: UI, Undo/Redo, Material Assignment, UV Unwrapping, Seam Solving, Physics Generation, UCX Collision, Socket Constraints, and Polish (Bevel/Chamfer/Fuse).
- **The Cartridge** handles one thing only: Pure BMesh shape generation (`build_shape`).

If a Cartridge follows the Mandates, the Console grants it full superpowers for free — Auto-UVs, Physics IDs, UCX Colliders, Sockets — without any extra code.

---

## 📑 Table of Contents

1.  [Repository Layout](#1-repository-layout)
2.  [System Anatomy](#2-system-anatomy)
    *   [Brain — Persistent State](#brain--persistent-state)
    *   [Muscle — Operator Shell](#muscle--operator-shell)
    *   [Engine — Generation Pipeline](#engine--generation-pipeline)
    *   [Polish Stack](#polish-stack)
    *   [Seam Solver](#seam-solver)
    *   [Phase 4 — Physics & Socket Forge](#phase-4--physics--socket-forge)
    *   [Shooter — Targeting](#shooter--targeting)
    *   [Observer — Analytics](#observer--analytics)
3.  [The Cartridge Mandate](#3-the-cartridge-mandate)
    *   [File Structure & Blueprint](#a-file-structure--blueprint)
    *   [MassaBuilder — Fluent API](#b-massabuilder--fluent-api)
    *   [The Golden Rules](#c-the-golden-rules)
    *   [Slot Protocol (0-9)](#d-slot-protocol-faces-0-9)
    *   [Edge Protocol (0-5)](#e-edge-protocol-edges-0-5)
    *   [UV Strategy](#f-uv-strategy)
    *   [Physics Material IDs](#g-physics-material-ids)
    *   [Socket Protocols](#h-socket-protocols)
    *   [UI Standards](#i-ui-standards-draw_shape_ui)
4.  [Modification Workflow](#4-modification-workflow)
    *   [Adding Parameters (The Rule of Five)](#adding-parameters-the-rule-of-five)
    *   [Resurrection System](#resurrection-system)
    *   [Headless Safety](#headless-safety)
    *   [Golden Cartridge Workflow](#golden-cartridge-workflow)
5.  [Tooling & Execution Environment](#5-tooling--execution-environment)
    *   [Setup](#setup)
    *   [Audit Commands](#audit-commands)
    *   [Live State Inspection](#live-state-inspection)
    *   [Auditor Suite](#auditor-suite)
    *   [Package the Addon](#package-the-addon)
6.  [Telemetry & Troubleshooting](#6-telemetry--troubleshooting)
    *   [Topology Flags](#topology-flags)
    *   [Edge Slot Flags](#edge-slot-flags)
    *   [Surface / UV Flags](#surface--uv-flags)
    *   [UV Inspection Protocol](#uv-inspection-protocol)
    *   [Common Issues Quick-Reference](#common-issues-quick-reference)

---

## 1. Repository Layout

```
MASSA_BMESH_CONSOLE-main/
│
├── massa/                             ← Blender addon root (packaged into massa.zip)
│   ├── __init__.py                    ← Registration + hot-reload controller
│   ├── blender_manifest.toml          ← Blender 5.0 Extension manifest
│   │
│   ├── operators/
│   │   ├── massa_base.py              ← 💪 MUSCLE: Massa_OT_Base + MASSA_OT_ReRun_Active
│   │   ├── massa_tools.py             ← Condemn / Resurrect / Finalize operators
│   │   ├── massa_point_tool.py        ← Coordinate picker
│   │   └── massa_shooter.py           ← 🎯 SHOOTER: ShootDispatcher + SpawnTarget
│   │
│   ├── modules/
│   │   ├── massa_console.py           ← 🧠 BRAIN: Scene property registration
│   │   ├── massa_properties.py        ← 🧬 DNA: MassaPropertiesMixin (shared props)
│   │   ├── massa_engine.py            ← ⚙️ ENGINE: run_pipeline() + UCX/auto-rig
│   │   ├── massa_builder.py           ← 🔨 BUILDER: Fluent BMesh API (MassaBuilder)
│   │   ├── massa_polish.py            ← ✨ POLISH: Post-process modifier stack
│   │   ├── massa_surface.py           ← 🎨 SURFACE: UVs, materials, data layers
│   │   ├── massa_sockets.py           ← 🔗 SOCKETS: Socket transforms + spawning
│   │   ├── massa_nodes.py             ← 🌐 NODES: GN SDF Fuse + viz overlay trees
│   │   ├── massa_collision.py         ← 💥 COLLISION: Viewport collision overlay
│   │   ├── massa_cartridge_props.py   ← Per-cartridge property management
│   │   ├── seam_solvers.py            ← 🧵 SEAMS: UV seam algorithms
│   │   ├── advanced_analytics.py      ← 🔭 OBSERVER: Debug overlay + telemetry
│   │   │
│   │   ├── cartridges/                ← 📦 CONTENT: 130+ auto-discovered generators
│   │   │   ├── __init__.py            ← Auto-discovery scanner + register/unregister
│   │   │   ├── cart_prim_NN_*.py      ← Primitive shapes (beam, pipe, panel…)
│   │   │   ├── cart_arc_NN_*.py       ← Architectural elements (wall, stairs…)
│   │   │   ├── cart_arch_*.py         ← Architectural structures
│   │   │   ├── cart_ind_NN_*.py       ← Industrial (truss, silo, crane…)
│   │   │   ├── cart_asm_NN_*.py       ← Assemblies (HVAC, radar, cryo pod…)
│   │   │   ├── cart_urb_NN_*.py       ← Urban props (bench, bollard, kiosk…)
│   │   │   ├── cart_lnd_*.py          ← Landscape
│   │   │   ├── cart_prp_*.py          ← Props (container, rack, greeble)
│   │   │   ├── prim_con_*.py          ← Construction primitives
│   │   │   └── cart_massa_builder_example.py  ← Reference implementation
│   │   │
│   │   └── debugging_system/          ← Headless audit suite (excluded from addon zip)
│   │       ├── config.py              ← ⚠️ SET BLENDER_PATH HERE
│   │       ├── runner.py              ← Main audit entrypoint
│   │       ├── debug_agent.py         ← Live Blender state inspection
│   │       ├── launcher.py            ← Subprocess launcher helpers
│   │       ├── headless_launcher.py   ← Background Blender session spawner
│   │       ├── runner_console.py      ← Console audit runner
│   │       ├── visual_inspector.py    ← Viewport render helpers
│   │       └── auditors/
│   │           ├── massa_auditor.py        ← Core topology checks
│   │           ├── massa_edge_auditor.py   ← Edge slot and seam checks
│   │           ├── massa_surface_auditor.py ← UV and normal checks
│   │           ├── massa_fuzz_auditor.py   ← Crash testing via param randomization
│   │           ├── massa_ui_auditor.py     ← Operator and UI validation
│   │           └── massa_topology_extra.py ← Extended topology checks
│   │
│   ├── ui/
│   │   ├── ui_massa_panel.py          ← MASSA_PT_Main sidebar panel
│   │   ├── ui_massa_pie.py            ← Pie menus (Ctrl+I in 3D View)
│   │   ├── ui_shared.py               ← Tab draw functions (SHAPE/EDGES/POLISH…)
│   │   └── gizmo_massa.py             ← Viewport gizmo group
│   │
│   └── utils/
│       └── mat_utils.py               ← 📚 Material DB (MASTER_MAT_DB) + UV_MAP_ITEMS
│
├── _Scripts/
│   ├── package_massa_addon.py         ← Packages massa/ into _EXPORT/massa.zip
│   └── test_run_cartridge.py          ← External audit entrypoint (wraps runner.py)
│
├── CLAUDE.md                          ← Claude Code project instructions
├── AGENTS.md                          ← AI agent operating protocol
├── CARTRIDGE_MANDATE.md               ← Golden Cartridge creation standard
├── new_OVERVIEW-main.md               ← Full architecture overview (v6.6)
├── master_README.md                   ← This file
└── _EXPORT/                           ← Generated addon zip (git-ignored)
```

---

## 2. System Anatomy

```
Registration order (massa/__init__.py):
  1. massa_console      🧠 Brain — scene property bag
  2. massa_engine       ⚙️ Engine — pipeline
  3. Operators          💪 Muscle — execution shells
  4. cartridges         📦 Content — auto-discovered generators
  5. UI                 🖼️ Interface — panel, pie, gizmo
```

The same `__init__.py` handles **hot-reload**: if `massa_console` is already in `locals()`, all modules are reloaded in dependency order before re-discovery. No Blender restart needed during development.

---

### Brain — Persistent State

**Files:** `modules/massa_console.py`, `modules/massa_properties.py`

`MassaPropertiesMixin` is the **DNA** — a base class that holds every shared property. It is simultaneously inherited by:
- `Massa_Console_Props` (registered as `context.scene.massa_console`) — the persistent Brain
- `Massa_OT_Base` — the transient Operator (Muscle)

This means every property is accessible identically from the Scene (UI, persistence) and the Operator (execution, Redo Panel).

**Property groups in `MassaPropertiesMixin`:**

| Group | Key Properties |
|:---|:---|
| Global | `global_scale`, `draft_mode` |
| Transform | `pivot_mode`, `ui_use_rot`, `rotation`, `use_weld` |
| Shading / Edge | `edge_mode`, `edge_auto_detect`, `edge_angle`, `edge_sharp_convex_*`, `edge_sharp_concave_*` |
| Seam Logic | `seam_active`, `seam_from_angle/slots/edges`, `seam_use_peri/cont/guide/detail/fold`, `seam_bias`, `seam_solver_mode`, `seam_orient`, `seam_cluster_tol`, `seam_straightness`, `seam_cleanup_flat/thresh` |
| Auto-Unwrap | `auto_unwrap`, `auto_unwrap_use_slots`, `auto_unwrap_margin` |
| UI Tabs | `ui_tab` (SHAPE / DATA / POLISH / UVS / SLOTS / EDGES / COLLISION / SOCKETS) |
| Edge Slot Actions | `edge_slot_1_action` … `edge_slot_5_action` (IGNORE/SEAM/SHARP/CREASE/BEVEL/BOTH) |
| Edge Visualization | `viz_edge_mode` (OFF / NATIVE / SLOTS) |
| Polish | `pol_solidify_*`, `pol_bridge_*`, `pol_triangulate_*`, `pol_holes_*`, `pol_symmetrize_*`, `pol_bend_*`, `pol_taper_*`, `pol_noise_*`, `pol_smooth_*`, `pol_plate_*`, `pol_decay_*`, `pol_fuse_*`, `pol_chamfer_*`, `pol_merge_mode` |
| Data Layers Set 1 | `wear_*`, `thick_*` / `flow_*` (thickness/flow), `grav_*`, `cavity_*` |
| Data Layers Set 2 | `wear2_*`, `flow2_*`, `cover_*`, `peak_*` |
| Physics Pipeline | `phys_gen_ucx`, `phys_bake_strain`, `phys_kinematic_pin`, `phys_auto_rig`, `phys_yield_strength`, `phys_active`, `part_active` |
| Debug Preview | `debug_view` (NONE / UV / SEAM / DATA_SET_1 / DATA_SET_2 / PHYS / PARTS / PROTECT) |
| Per-Slot ×10 | `mat_i`, `phys_mat_i`, `uv_mode_i`, `uv_scale_i`, `sep_i`, `sock_i`, `off_i`, `prot_i`, `expand_i`, `collision_shape_i`, `show_coll_i`, `phys_friction_i`, `phys_bounce_i`, `phys_bond_i` |
| Sockets | `sock_enable`, `sock_constraint_type`, `sock_break_strength`, `sock_visual_size` |

> **Rule:** NEVER rename existing properties. Deprecate them instead. Renaming breaks the Resurrection system for all generated objects that have `obj["MASSA_PARAMS"]` stored with the old key name.

Current resurrection payloads include `MASSA_PARAMS_VERSION`. Known property renames must be handled in the migration table in `operators/massa_base.py`, and stale unknown keys are reported instead of being silently ignored.

---

### Muscle — Operator Shell

**File:** `operators/massa_base.py` → `Massa_OT_Base(Operator, MassaPropertiesMixin)`

The execution shell. Receives user input, syncs state, and calls the Engine.

**Lifecycle:**

```
invoke()
  ├── _sync(from_console=True)       ← Pull Console → Operator props
  ├── Resurrection path:
  │   ├── rerun_mode=True            ← Read obj["MASSA_PARAMS"], store old transform
  │   └── MASSA_TEMP_RESTORE         ← Legacy/wrapper restoration path
  ├── _inject_cartridge_defaults()   ← Apply phys → visual material mapping
  └── execute()
        ├── Delete old object (if resurrecting)
        ├── Clean UCX_/MASSA_JOINT_/SOCKET_ children
        ├── massa_engine.run_pipeline(self, context)
        ├── Apply obj_location + obj_rotation to new object
        └── _sync(from_console=False) ← Push Operator → Console props
```

**`_sync()`**: Bidirectionally copies all `MassaPropertiesMixin.__annotations__` keys between operator and `context.scene.massa_console`. Per-slot properties are discovered dynamically by matching annotation names like `mat_0`, `sep_0`, `uv_mode_0`, etc., so new slot-scoped mixin properties do not need a second hardcoded sync list.

**`MASSA_OT_ReRun_Active`** (`massa.rerun_active`): Saves `MASSA_PARAMS` + current transform to `context.scene["MASSA_TEMP_RESTORE"]`, deletes the active object, and re-fires its original operator via `bpy.ops` using the stored `massa_op_id`.

---

### Engine — Generation Pipeline

**File:** `modules/massa_engine.py` → `run_pipeline(op, context)`

Full generation pipeline from BMesh creation to final committed Blender object.

Pipeline failures are reported by phase (`Build shape`, `Edge preparation`, `Polish stack`, `Seam and surface maps`, `Output generation`) so headless and UI runs expose the failing stage instead of returning a generic cancellation.

```
Step  1   mat_utils.ensure_default_library()
Step  2   Read CARTRIDGE_META flags
Step  3   bm = bmesh.new()
Step  4   Ensure MASSA_SOCKETS face layer
Step  5 ▶ op.build_shape(bm)                          ← THE CARTRIDGE
Step  6   FIX_DEGENERATE: apply_cleanup               (flag gate)
Step  7   Ensure MASSA_EDGE_SLOTS edge layer
Step  8   auto_detect_edge_slots(bm)                  (if edge_auto_detect)
Step  9   process_edge_slots(bm, op)                  → apply Seam/Sharp/Crease/Bevel
Step 10   auto_detect_sharp_edges(bm, op)             → convex/concave sharp (additive)
Step 11   bmesh.ops.scale (global_scale)              (if ≠ 1.0)
Step 12   apply_transform_alignment(bm, pivot_mode)   (if not LOCK_PIVOT)
Step 13   gather_manifest(op)                         → manifest[0-9] + active_sockets
Step 14   apply_protection_mask(bm, manifest)
Step 15   apply_slot_inflation(bm, op)
Step 16   apply_hard_merge(bm, pol_merge_mode)
Step 17 ▶ _run_polish_stack(bm, op, flags, manifest)  (if not draft_mode)
Step 18   apply_safety_decimate(bm)
Step 19   dissolve_degenerate                         (if FIX_DEGENERATE)
Step 20   recalc_face_normals
Step 21   Remove loose verts                          (if REMOVE_LOOSE)
Step 22   write_identity_layers(bm, manifest, op)     → MASSA_PHYS_ID, MASSA_PART_ID
Step 23   calculate_physical_stats(bm, manifest)      → vol, mass → massa_temp_stats
Step 24   calculate_transforms(bm, active_sockets)    → socket_data
Step 25   tag_structure_edges(bm, op)
Step 26 ▶ Seam Solver                                 (if seam_active)
            apply_base_drivers(...)
            solve_seams(...)                          (if seam_solver_mode ≠ NONE)
            cleanup_flat_seams(...)                   (if seam_cleanup_flat)
Step 27   generate_surface_maps(bm, op, cvx, cnv)
Step 28   Apply rotation transform                    (if ui_use_rot)
Step 29 ▶ _generate_output(...)
            assign_materials(obj, op, bm)             → slot_map
            bake_strain_map(bm, op)
            bake_kinematic_anchors(obj, bm, op)
            Collect MASSA_SOCKETS faces
            Force seams from slots (auto_unwrap_use_slots)
            bm.to_mesh(mesh)
            UV unwrap per-slot (LSCM/Smart Project/BOX/FIT/TUBE)
            UV pack islands (auto_unwrap)
            spawn_socket_objects(...)
            Bevel modifier (if bevel weights present)
            Slot viz overlay (if viz_edge_mode == SLOTS)
            handle_separation(obj, op, ...)
            Phase 4: phys_gen_ucx / phys_auto_rig / Socket Forge
```

---

### Polish Stack

Executes as step 17. Each operation is gated by its `pol_*_active` toggle AND validated against cartridge `flags`. Operations run in this exact order:

| Order | Toggle Property | Flag Gate | Operation |
|:---|:---|:---|:---|
| 1 | `pol_fuse_active` | `ALLOW_FUSE` | `apply_concave_bevel` — SDF-like bevel at concave intersections |
| 2 | *(always)* | — | `recalc_face_normals` |
| 3 | `pol_solidify_active` | `ALLOW_SOLIDIFY` | `apply_solidify` — shell thickness |
| 4 | `pol_bridge_active` | — | `apply_bridge_loops` |
| 5 | `pol_holes_active` | — | `apply_fill_holes` |
| 6 | `pol_symmetrize_active` | — | `apply_symmetrize` — mirror across axis |
| 7 | `pol_taper_active` | — | `apply_taper` — XY taper with curve profile |
| 8 | `pol_bend_active` | — | `apply_bend` — bend along axis |
| 9 | `pol_plate_active` | — | `apply_plating` — panel gap + depth inset per slot |
| 10 | `pol_noise_active` | — | `apply_noise` — vertex displacement |
| 11 | `pol_smooth_active` | — | `apply_smooth` — Laplacian smooth |
| 12 | `pol_decay_active` | — | `apply_decay` — random per-face recession |
| 13 | `pol_triangulate_active` | — | `apply_triangulate` — BEAUTY or FIXED |
| 14 | `pol_chamfer_active` | `ALLOW_CHAMFER` | `apply_chamfer` — angle-filtered edge bevel |

**SDF Fuse (post-output):** When `pol_fuse_active` is on, `apply_sdf_fuse` adds a Geometry Nodes modifier (`get_or_create_sdf_fuse_tree`) to blend hard intersections. Slots with `sep_i = True` auto-apply this modifier.

---

### Seam Solver

**File:** `modules/seam_solvers.py`  
**Activated when:** `seam_active = True`

Intelligently places UV seams on the final mesh. Runs as step 26 of the pipeline.

**Sub-steps:**
1. `apply_base_drivers(bm, use_angle, angle_limit, use_slots, bias, use_edges, edge_mask)` — Seeds initial seam candidates from angle threshold and edge slot roles. The `seam_use_*` toggles (`peri/cont/guide/detail/fold`) control which edge roles are included.
2. `solve_seams(bm, mode, orient, cluster_tol, straightness, strict_slots)` — Runs the chosen algorithm.
3. `cleanup_flat_seams(bm, threshold, keep_slots)` — Removes seam edges on flat coplanar areas.

**Solver modes (`seam_solver_mode`):**

| Mode | Algorithm | Best For |
|:---|:---|:---|
| `NONE` | Angle/Driver only, no graph solver | Simple flat geometry |
| `HARD_SURFACE` | Planar graph clustering (default) | Mechanical hard-surface |
| `STRIP` | Quad strip following | Paneled surfaces |
| `SMART_TUBE` | Single-cut unroll (Zipper) | Pipes, cylinders, tubes |
| `ORGANIC` | Cylinder detective | Organic / branching forms |
| `BOX_STRIP` | Legacy wall unrolling | Architectural boxes |

`seam_orient` controls the Zipper hidden-face direction: `BACK` (default), `FRONT`, `LEFT`, `RIGHT`, `BOTTOM`.

`seam_bias` controls candidate prioritization: `BALANCED`, `CONVEX` (expose ridges for baking), `CONCAVE` (hide seams in valleys for environment work).

---

### Phase 4 — Physics & Socket Forge

Executes inside `_generate_output` after the mesh is committed to Blender. UCX generation, Auto-Rig, and Socket Forge each run in their own guarded sub-phase so one failure does not prevent the others from running. Phase 4 links helper objects through the generated object's collection when available instead of relying on `bpy.context.collection`.

**UCX Collision Generation** (`phys_gen_ucx = True`):

Generates `UCX_<ObjectName>_<SlotLabel>` collision mesh objects per active slot. Named for UE5 import convention. Each UCX object is parented to the main object, set to `WIRE` display, and hidden from render.

| `collision_shape_i` | Method |
|:---|:---|
| `BOX` | Axis-aligned bounding box via min/max vertices |
| `HULL` | `bmesh.ops.convex_hull` on slot vertices |
| `SPHERE` | Bounding sphere (max distance from centroid) |
| `CAPSULE` | Z-aligned bounding cylinder (`bmesh.ops.create_cone`) |
| `MESH` | Exact face/vertex reconstruction of the slot geometry |

**Auto-Rigger** (`phys_auto_rig = True`):

Detects detached child meshes (from `sep_i` slots), creates `MASSA_JOINT_*` empties at each child's boundary edge centroid, and adds Hinge rigid body constraints (obj1 = parent, obj2 = child). Breaking threshold = `phys_yield_strength × 1000 N`.

**Socket Forge** (`sock_enable = True`):

Collects faces tagged in the `MASSA_SOCKETS` BMesh layer, calculates center + normal per socket ID, spawns `SOCKET_<ObjectName>_<ID>` Empty objects parented to the object. Optionally adds Rigid Body Constraints:

| `sock_constraint_type` | Blender RB Type |
|:---|:---|
| `NONE` | Visual empty only |
| `FIXED` | FIXED (rigid link) |
| `HINGE` | HINGE (rotation on Z) |
| `SLIDER` | SLIDER (linear motion on Z) |
| `SPRING` | GENERIC_SPRING (elastic) |

---

### Shooter — Targeting

**File:** `operators/massa_shooter.py`  
**Operators:** `MASSA_OT_ShootDispatcher` (`massa.shoot_dispatcher`), `MASSA_OT_SpawnTarget` (`massa.spawn_target`)

"Point & Shoot" mode. Places a `Massa_Target` empty in the scene and dispatches Operators to that world location and rotation, injecting the transform into the Operator's Redo history.

---

### Observer — Analytics

**File:** `modules/advanced_analytics.py` → `MCP_Overlay`

Visual debug overlay registered via `bpy.types.SpaceView3D.draw_handler_add`. Reads `debug_view` state from the Console and draws diagnostic information — face count, slot distribution, UV stats, property state — directly in the 3D viewport. Also provides `parse_panel_ast` and `inspect_last_operator` utilities.

---

## 3. The Cartridge Mandate

> This section is the binding contract for creating new Cartridges. All new geometry scripts **must** conform to it.

### A. File Structure & Blueprint

Every Cartridge is a `.py` file placed in `massa/modules/cartridges/`. Auto-discovery scans this directory on import and registers any file that has both `CARTRIDGE_META` and a `Massa_OT_Base` subclass. **No manual registration is needed** — drop the file in the folder and reload.

**Full canonical template:**

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

# ─────────────────────────────────────────────────────
# 1. METADATA  (Required — drives auto-discovery)
# ─────────────────────────────────────────────────────
CARTRIDGE_META = {
    "name":        "PRIM_XX: My Part",        # Human-readable UI label
    "id":          "prim_xx_my_part",          # Unique ID → bl_idname suffix
    "icon":        "MESH_CUBE",                # Blender icon ID
    "scale_class": "STANDARD",                # MICRO | STANDARD | MACRO
    "flags": {
        "USE_WELD":       True,    # Merge verts by distance after build
        "ALLOW_SOLIDIFY": True,    # Can engine add shell thickness?
        "ALLOW_FUSE":     True,    # Allow SDF Fuse bevel?
        "ALLOW_CHAMFER":  True,    # Allow Chamfer polish?
        "FIX_DEGENERATE": True,    # Auto-clean zero-area faces
        "LOCK_PIVOT":     False,   # Keep origin at generation start point
        "REMOVE_LOOSE":   True,    # Delete unconnected vertices
    },
}

class MASSA_OT_prim_xx_my_part(Massa_OT_Base):
    bl_idname  = "massa.gen_prim_xx_my_part"  # MANDATORY prefix: 'massa.gen_'
    bl_label   = "PRIM_XX: My Part"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # ─────────────────────────────────────────────────
    # 2. PARAMETERS (Blender Properties)
    # ─────────────────────────────────────────────────
    radius:   FloatProperty(name="Radius",   default=1.0, min=0.1, unit="LENGTH")
    segments: IntProperty(  name="Segments", default=16,  min=3)

    # ─────────────────────────────────────────────────
    # 3. SLOT DEFINITIONS — The 'Hard 10'
    # ─────────────────────────────────────────────────
    def get_slot_meta(self):
        return {
            0: {"name": "Hull",    "uv": "BOX",    "phys": "METAL_STEEL"},
            1: {"name": "Caps",    "uv": "BOX",    "phys": "CONCRETE_RAW"},
            2: {"name": "Trim",    "uv": "TUBE_Z", "phys": "METAL_IRON"},
            9: {"name": "Anchor",  "uv": "SKIP",   "phys": "GENERIC", "sock": True},
        }

    # ─────────────────────────────────────────────────
    # 4. SHAPE UI (Redo Panel — SHAPE tab)
    # ─────────────────────────────────────────────────
    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "segments")

    # ─────────────────────────────────────────────────
    # 5. EXECUTION CORE — Pure BMesh only
    # ─────────────────────────────────────────────────
    def build_shape(self, bm: bmesh.types.BMesh):
        # [ALWAYS FIRST] Acquire edge slot layer
        edge_slots = (bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
                      or bm.edges.layers.int.new("MASSA_EDGE_SLOTS"))

        # [PHASE 1] Build geometry — NO bpy.ops allowed here
        bmesh.ops.create_cone(
            bm, cap_ends=True,
            radius1=self.radius, radius2=self.radius,
            depth=2.0, segments=self.segments
        )

        # [PHASE 2] Assign material slots to faces
        for f in bm.faces:
            f.material_index = 0                   # Default: Hull
            if abs(f.normal.z) > 0.9:
                f.material_index = 1               # Caps

        # [PHASE 3] Tag edge roles
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1                  # Perimeter → Seam + Sharp

        # [MANDATORY] Cleanup
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
```

**Reference implementations:**
- Simplest working cartridge: [`massa/modules/cartridges/cart_massa_builder_example.py`](massa/modules/cartridges/cart_massa_builder_example.py)
- Structural profiles: `cart_prim_01_beam.py`
- Complex UVs / boolean-like math: `cart_prim_04_panel.py`
- Mathematical curves / arrays: `cart_prim_05_catenary.py`, `cart_prim_11_helix.py`

---

### B. MassaBuilder — Fluent API

`MassaBuilder` ([`massa/modules/massa_builder.py`](massa/modules/massa_builder.py)) is the **preferred** tool for `build_shape`. It wraps raw `bmesh.ops` in a chainable interface, tracks `active_faces`/`active_edges`/`active_verts`, and is the primary pattern for new cartridges.

```python
from ...modules.massa_builder import MassaBuilder

def build_shape(self, bm: bmesh.types.BMesh):
    builder = MassaBuilder(bm)

    # Create geometry and immediately tag its material slot
    builder.create_box(width=2.0, depth=2.0, height=1.0,
                       center=Vector((0, 0, 0.5)))
    builder.tag_slot(0)

    # Select top face, inset, extrude, tag
    builder.select_faces_by_normal(Vector((0, 0, 1))) \
           .inset(0.2, relative=False) \
           .extrude(0.5) \
           .tag_slot(1)

    # Tag top face as socket anchor
    builder.select_faces_by_normal(Vector((0, 0, 1))) \
           .tag_socket(1)

    # Debug report + mandatory cleanup
    print(builder.report())
    builder.clean()
```

**Core methods:**

| Method | Description |
|:---|:---|
| `create_box(w, d, h, center)` | Creates box; sets `active_faces` to all box faces |
| `create_grid(x_segs, y_segs, size, center)` | Grid on XY plane |
| `create_cylinder(radius, depth, segs, center)` | Cylinder |
| `extrude(amount)` | Extrudes `active_faces` upward; `active_faces` → new top faces |
| `inset(amount, relative)` | Insets `active_faces`; `active_faces` → inner faces |
| `select_faces_by_normal(normal, threshold)` | Replaces `active_faces` by dot-product filter |
| `tag_slot(index)` | Sets `f.material_index` on all `active_faces` |
| `tag_socket(id)` | Tags `active_faces` in `MASSA_SOCKETS` int layer |
| `clean()` | `remove_doubles` + `recalc_face_normals` |
| `report()` | Returns debug string (vert/edge/face/slot counts) |

---

### C. The Golden Rules

1.  **Pure BMesh in `build_shape`**: Never call `bpy.ops.*` inside `build_shape`. It crashes in headless/background mode. Use `bmesh.ops`, `MassaBuilder`, or pure `mathutils`. If a cartridge needs initial UVs, assign them through BMesh UV loops; object/edit-mode unwraps belong in the engine output stage.
2.  **No Loose Geometry**: Always end `build_shape` with `bmesh.ops.remove_doubles` and `bmesh.ops.recalc_face_normals`. The engine's `FIX_DEGENERATE` pass provides additional safety but is not a substitute.
3.  **Inheritance**: The operator class MUST inherit `Massa_OT_Base`.
4.  **Metadata**: MUST provide valid `CARTRIDGE_META` (with `name`, `id`, `icon`, `flags`) and implement `get_slot_meta()`. Missing metadata keys currently warn for legacy compatibility, but a discovered operator missing `build_shape()` or `get_slot_meta()` is fatal and must not register.
5.  **Context Safe**: Never assume `bpy.context.object` or `bpy.context.view_layer` exists inside `build_shape`. Work only on the provided `bm` argument.
6.  **Never Rename Properties**: Renaming breaks Resurrection for existing objects. Deprecate with a migration path instead.

---

### D. Slot Protocol (Faces 0-9)

**In `build_shape`:** `f.material_index = ID`

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
| **9** | **SOCKET / ANCHOR** | Invisible attachment point — spawns Empty object |

**Per-slot Console controls (all configurable in SLOTS tab):**

| Property | Behaviour |
|:---|:---|
| `mat_i` | Visual material override |
| `phys_mat_i` | Physics material ID |
| `uv_mode_i` | UV mapping strategy |
| `uv_scale_i` | UV tiling scale |
| `sep_i` | Detach as separate child mesh |
| `prot_i` | Protect from Polish operations |
| `sock_i` | Mark as socket anchor |
| `off_i` | Face extrude offset |
| `collision_shape_i` | UCX shape: BOX/HULL/SPHERE/CAPSULE/MESH |

---

### E. Edge Protocol (Edges 0-5)

**In `build_shape`:**
```python
edge_slots = (bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
              or bm.edges.layers.int.new("MASSA_EDGE_SLOTS"))
e[edge_slots] = ROLE_ID
```

The `MASSA_EDGE_SLOTS` integer layer on BMesh edges drives all post-process shading, UV seam, and bevel operations.

| ID | Name | Default Behavior | Auto-Detection Logic |
|:---|:---|:---|:---|
| **0** | **None** | Smooth / unassigned | Any edge not matched |
| **1** | **Perimeter** | **Seam + Sharp** | End cap / side wall boundary |
| **2** | **Contour** | **Sharp** | Internal hard angles (90°+) not on perimeter |
| **3** | **Guide** | **Seam Only** | Pathfinding seam lines on cylindrical surfaces |
| **4** | **Detail** | **Ignore** | Material boundary edges, soft chamfer lines |
| **5** | **Fold** | **Ignore** | Manual only; subdivision crease / cloth pin |

**User-configurable actions** per role (EDGES tab):
`IGNORE` | `SEAM` | `SHARP` | `BOTH` (Seam+Sharp) | `CREASE` | `BEVEL`

`BEVEL` writes to `bevel_weight_edge`, the canonical Blender 4/5 edge layer. If legacy `bevel_weight` data is encountered, the engine copies it into `bevel_weight_edge` and removes the legacy layer when possible.

**Auto-detection note:** When `edge_auto_detect = True` (default), the engine automatically assigns roles 1 and 2 based on material boundaries and angle analysis. You can assign roles manually in `build_shape` and the auto-detection will layer additive sharp detection on top (`edge_sharp_convex_angle` / `edge_sharp_concave_angle` thresholds).

**Critical:** For meshes with >12 faces that use `UNWRAP` UV mode, the auditor will flag `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` if no edges are tagged with role 1 or 3. UV unwrap will fail or produce severe distortion without them.

---

### F. UV Strategy

Defined in `get_slot_meta()` under `"uv"` key. Overridable per-slot at runtime via `uv_mode_i`.

| Value | Behaviour | Best For |
|:---|:---|:---|
| `"BOX"` | Tri-planar cube mapping | Hard surface, flat panels, caps |
| `"FIT"` | Stretch UVs to fill 0–1 space | Screens, glass, single-face decals |
| `"TUBE_Z"` | Cylindrical mapping, vertical Z axis | Pipes, columns, tanks |
| `"TUBE_Y"` | Cylindrical mapping, Y axis (length) | Beams, conduits |
| `"TUBE_X"` | Cylindrical mapping, X axis (width) | Horizontal rollers |
| `"UNWRAP"` | LSCM/Angle-Based — seam-driven | Organic shapes, complex surfaces |
| `"SKIP"` | Manual UVs from `build_shape`, or Auto-Unwrap fallback | **Golden Cartridge standard** |

**Golden Cartridge UV standard:** Use `"SKIP"` and write UVs manually using `bm.loops.layers.uv.verify()` inside `build_shape`. Auto-unwrap is a fallback, not the primary standard. Manual UV assignment must remain pure BMesh and must not round-trip through temporary Blender objects.

**Manual UV pattern:**
```python
uv_layer = bm.loops.layers.uv.verify()
for f in bm.faces:
    if f.material_index == 0:
        for l in f.loops:
            u, v = calculate_uv(l.vert.co)
            l[uv_layer].uv = (u * scale_u, v * scale_v)
```

**For cylindrical objects:** Detect the 0.0→1.0 U seam crossing and shift UVs to prevent "smearing" across the seam edge.

**`auto_unwrap` global override:** When enabled, forces UV packing via Smart Project (or LSCM if seams are active), regardless of per-slot `uv_mode` settings. Islands are packed to 0–1 with `auto_unwrap_margin`.

---

### G. Physics Material IDs

The `"phys"` key in `get_slot_meta()` sets both the default visual material AND the baked `MASSA_PHYS_ID` face attribute. Valid keys from `MASTER_MAT_DB` in `mat_utils.py`:

| Category | Keys |
|:---|:---|
| **Concrete** | `CONCRETE_RAW`, `CONCRETE_POL`, `CONCRETE_BLOCK` |
| **Metal** | `METAL_STEEL`, `METAL_ALUMINUM`, `METAL_IRON`, `METAL_RUST` |
| **Wood** | `WOOD_OAK`, `WOOD_PINE`, `WOOD_PAINTED`, `WOOD_ROUGH` |
| **Synthetic** | `SYNTH_PLASTIC`, `SYNTH_RUBBER`, `SYNTH_GLASS` |
| **Other** | `CERAMIC_TILE`, `FABRIC_CANVAS`, `GENERIC` |
| **Debug Slots** | `MASSA_DEBUG_0` … `MASSA_DEBUG_9` (colored debug view) |

Each material has an associated density value (kg/m³). The engine calculates weighted-average mass from slot area fractions × slot density, stored in `massa_temp_stats`.

`GENERIC` is a valid physics ID and resolves to the real Generic visual material. Do not rely on missing or skipped material assignment as a debug-color fallback.

---

### H. Socket Protocols

Sockets are procedurally generated attachment points. **The standard method is tagging existing faces** — do not generate extra geometry just for sockets.

**Two tagging methods:**

**Method 1 — Via `get_slot_meta` (`sock: True`):** Any slot defined with `"sock": True` in the meta dict will look for faces assigned to that slot index. Their centroids and normals become socket transforms.

**Method 2 — Via `MassaBuilder.tag_socket(id)` (preferred for precision):** Tags `active_faces` in the `MASSA_SOCKETS` BMesh integer layer with the given socket ID.

```python
# Tag top face as socket anchor (in build_shape):
builder.select_faces_by_normal(Vector((0, 0, 1))) \
       .tag_socket(1)          # Socket ID 1

# Tag bottom face as anchor (origin reference):
builder.select_faces_by_normal(Vector((0, 0, -1))) \
       .tag_socket(2)          # Socket ID 2
```

**Result:** `SOCKET_<ObjectName>_<ID>` Empty objects are spawned, Z-aligned to the face normal, parented to the main object. If `sock_constraint_type ≠ NONE`, a Rigid Body Constraint is added.

---

### I. UI Standards (`draw_shape_ui`)

Implement `draw_shape_ui(self, layout)` to expose shape parameters in the SHAPE tab.

```python
def draw_shape_ui(self, layout):
    col = layout.column(align=True)
    col.label(text="Dimensions", icon="MESH_DATA")
    col.prop(self, "radius")
    col.prop(self, "height")

    layout.separator()
    col.label(text="Topology", icon="MOD_WIREFRAME")
    col.prop(self, "segments")
    col.prop(self, "use_caps")
```

Group related properties (Dimensions, Topology, Features). Use `layout.separator()` for visual spacing. Standard icons: `MESH_DATA`, `MOD_WIREFRAME`, `FIXED_SIZE`, `MOD_SOLIDIFY`.

---

## 4. Modification Workflow

### Adding Parameters (The Rule of Five)

To add a new **global** parameter shared across the Console UI and all Operators, touch all 5 locations:

1.  **Brain (Definition)**: Add the property annotation to `MassaPropertiesMixin` in `modules/massa_properties.py`. This is the canonical definition.
2.  **Brain (Scene)**: Because `Massa_Console_Props` inherits `MassaPropertiesMixin`, the property automatically appears on `context.scene.massa_console`. No extra registration needed unless you need a Scene-only override.
3.  **Bridge (Sync)**: For mixin-level properties the `_sync()` loop in `massa_base.py` handles them automatically via `MassaPropertiesMixin.__annotations__`. For operator-only properties you must add the key string manually to `_sync()`.
4.  **Interface**: Add the UI drawing logic to the appropriate tab function in `ui/ui_shared.py` (`draw_polish_tab`, `draw_uvs_tab`, `draw_data_tab`, etc.).
5.  **Logic**: Implement the effect inside the Engine pipeline in `modules/massa_polish.py`, `modules/massa_engine.py`, `modules/massa_surface.py`, or `modules/seam_solvers.py`.

### Resurrection System

Every generated Massa object carries its full parameter state and can be fully re-edited at any time.

*   **Saving**: `_capture_operator_params(op)` iterates all non-readonly RNA properties and serializes them into a plain dict stored as `obj["MASSA_PARAMS"]`. The payload includes `MASSA_PARAMS_VERSION`. The `bl_idname` (or meta-derived ID) is stored as `obj["massa_op_id"]`.
*   **Restoring**: When `Massa_OT_Base.invoke()` runs in `rerun_mode`, it reads `MASSA_PARAMS` from the target object, migrates known old keys, and calls `setattr(self, k, v)` for each current key. Material, UV, Seam, and Transform properties are intentionally skipped so Console overrides take precedence. Unknown stale keys are reported to the info bar.
*   **Redo Panel persistence**: `obj_location` and `obj_rotation` are stored as operator properties so they survive redo steps and keep the object in place while the user adjusts shape parameters live.
*   **Transform restore**: The new object's `.location` and `.rotation_euler` are set from stored values AFTER `run_pipeline()` completes, so the new mesh always lands exactly where the old one was.
*   **Golden Rule**: **NEVER rename a cartridge property or a mixin property.** Existing objects will fail to resurrect because their `MASSA_PARAMS` stores the old key name. Write a migration function that reads both old and new key names.

### Headless Safety

*   The full Engine pipeline runs in headless (background) Blender during audit.
*   **Never call `bpy.ops.*` inside `build_shape`** — no Blender context exists headlessly.
*   **Never read `bpy.context.object`** inside `build_shape` — use only the provided `bm`.
*   **Use `mat_utils.ensure_default_library()`** at the top of any method that creates/reads materials — it is headless-safe.
*   UCX, Auto-Rig, and Socket Forge operations are in `_generate_output` (outside `build_shape`) and are wrapped independently in `try/except` for graceful degradation.

### Golden Cartridge Workflow

When tasked with creating or modifying a Cartridge, execute this exact workflow:

1.  **Ingest the Mandate**: Re-read `CARTRIDGE_MANDATE.md` and this document. Refresh understanding of UV mapping, Edge Slots (1-5), and Socket Protocols.
2.  **Analyze a Reference**: Inspect an existing Golden Cartridge that closely matches the task:
    *   Structural profiles → `cart_prim_01_beam.py`
    *   Complex UVs / boolean-like math → `cart_prim_04_panel.py`
    *   Mathematical curves / arrays → `cart_prim_05_catenary.py` or `cart_prim_11_helix.py`
3.  **Execute**: Write the `build_shape` logic using only `bmesh`, `MassaBuilder`, and `mathutils`.
4.  **Verify**: Run the cartridge through the audit suite:
    ```bash
    python modules/debugging_system/runner.py --cartridge modules/cartridges/<name>.py --mode AUDIT
    python modules/debugging_system/runner.py --cartridge modules/cartridges/<name>.py --mode UV_INSPECT
    ```
    Resolve all `CRITICAL_*` flags before considering the cartridge stable.

---

## 5. Tooling & Execution Environment

> Do NOT write custom execution scripts. The built-in debugging suite covers all scenarios.

### Setup

Edit `massa/modules/debugging_system/config.py` before using any tool:

```python
# Windows
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
# macOS
BLENDER_PATH = "/Applications/Blender.app/Contents/MacOS/Blender"
# Linux
BLENDER_PATH = "/usr/bin/blender"
```

### Audit Commands

**External entrypoint (from repo root):**
```bash
python _Scripts/test_run_cartridge.py <path/to/cartridge.py> --mode <MODE>
```

**Internal entrypoint (from `massa/` directory):**
```bash
python modules/debugging_system/runner.py --cartridge <path> --mode <MODE>
```

All tools spawn a background Blender process and return JSON wrapped between `---AUDIT_START---` and `---AUDIT_END---` markers.

**Common examples:**
```bash
# Standard geometry + UV audit
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_02_pipe.py \
  --mode AUDIT

# UV distortion heatmap (Red=bad, Blue=good)
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_02_pipe.py \
  --mode UV_HEATMAP

# UV layout inspection (0-1 space, check overlaps)
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_02_pipe.py \
  --mode UV_INSPECT

# Compare two versions
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_01_beam.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "modules/cartridges/cart_prim_01_beam_v2.py"}'
```

**All available modes:**

| Mode | Purpose |
|:---|:---|
| `AUDIT` | Full geometry + topology + UV + seam + fuzz checks |
| `VISUAL_DIFF` | Red/green wireframe overlay comparing two versions |
| `UV_HEATMAP` | UV distortion heatmap (Red=bad, Blue=good) |
| `UV_INSPECT` | 2D UV layout — check overlaps and out-of-bounds |
| `PERFORMANCE` | Execution time (ms) and polycount vs budget |
| `CSG_DEBUG` | Debug boolean and bridge geometry operations |
| `RENDER` | Full render of the generated mesh |
| `SKILL_EXEC` | Execute a named skill workflow |
| `CONSOLE_AUDIT` | Validate Console architecture (Brain/Muscle sync) |

### Live State Inspection

Executes arbitrary Python inside an active headless Blender instance:

```bash
# Inline Python
python modules/debugging_system/debug_agent.py \
  --code "import bpy; print(bpy.data.objects.keys())"

# File execution (recommended for complex logic)
python modules/debugging_system/debug_agent.py --file temp_inspect.py
```

### Auditor Suite

Auditors run automatically during `AUDIT` mode. Each targets a specific concern:

| Auditor | File | What It Checks |
|:---|:---|:---|
| **Topology** | `massa_auditor.py` | Empty mesh, flat Z axis, missing slot layer, loose verts, non-manifold, zero-area, thin slivers |
| **Edge Slots** | `massa_edge_auditor.py` | Missing `MASSA_EDGE_SLOTS`, no seams on complex meshes, isolated seam edges |
| **Surface** | `massa_surface_auditor.py` | Missing UV, zero UV data, inverted normals, self-intersection, UV spikes, collapsed UVs |
| **Fuzz** | `massa_fuzz_auditor.py` | Randomizes all parameters, re-runs generation, checks for crashes |
| **UI** | `massa_ui_auditor.py` | Validates operator properties and UI draw calls |
| **Topology Extra** | `massa_topology_extra.py` | Extended topology checks beyond base auditor |

### Package the Addon

Creates `_EXPORT/massa.zip` (Blender 5.0 Extension format — `blender_manifest.toml` at ZIP root):

```bash
python _Scripts/package_massa_addon.py
```

Excluded from the package: `__pycache__/`, `.git/`, `debugging_system/`, `_pkg_env/`, test files, `.zip` files.

---

## 6. Telemetry & Troubleshooting

Audit output is JSON with a `"flags"` list. `CRITICAL_*` flags **must** be fixed. `WARNING_*` flags indicate quality issues.

### Topology Flags

| Flag | Meaning | Fix |
|:---|:---|:---|
| `CRITICAL_EMPTY_MESH` | No geometry created | Check `build_shape` logic |
| `CRITICAL_FLAT_Z_AXIS` | Geometry has zero height | Check `bmesh.ops.scale` or extrusion direction |
| `CRITICAL_MISSING_SLOT_LAYER` | No `MASSA_EDGE_SLOTS` layer | `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` |
| `CRITICAL_NO_PERIMETER_DEFINED` | No edges tagged as role 1 | Tag silhouette edges: `e[edge_slots] = 1` |
| `CRITICAL_LOOSE_VERTS_N` | N unconnected vertices | Run `bmesh.ops.remove_doubles` or delete orphans |
| `CRITICAL_NON_MANIFOLD_N` | N non-manifold edges | Check bridge/fill/boolean logic; `recalc_face_normals` |
| `CRITICAL_ZERO_AREA_FACES_N` | N zero-area faces | Check extrusion/bridge for collapsed geometry |
| `WARNING_THIN_FACES_N` | N sliver faces (Perim² / Area > 1000) | Rebuild; causes UV distortion and bevel artifacts |

### Edge Slot Flags

| Flag | Meaning | Fix |
|:---|:---|:---|
| `WARNING_MISSING_EDGE_SLOTS_LAYER` | Layer exists but no edges assigned | Assign edge roles in `build_shape` |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | Mesh >12 faces, zero seam edges | Tag role 1 (Perimeter) or role 3 (Guide) |
| `WARNING_ISOLATED_SEAM_EDGES_N` | N seam edges not connected to a loop | Ensure seam loops are continuous |

### Surface / UV Flags

| Flag | Meaning | Fix |
|:---|:---|:---|
| `CRITICAL_MISSING_UV_LAYER` | No UV layer | Set UV strategy in `get_slot_meta` or write UVs manually |
| `CRITICAL_ZERO_UV_DATA` | UV layer exists but all at (0,0) | Check UV assignment logic in `build_shape` |
| `CRITICAL_INVERTED_NORMALS` | Faces pointing inward | `bmesh.ops.recalc_face_normals` at end of `build_shape` |
| `CRITICAL_SELF_INTERSECTION` | Geometry overlaps itself | Check boolean, bridge, extrusion logic |
| `CRITICAL_UV_SPIKES_N` | N UV islands with extreme distortion | Improve seam placement (roles 1/3) or UV math |
| `CRITICAL_COLLAPSED_UVS_N` | N UV islands collapsed to a point | Fix zero-area faces (usually the root cause) |

### UV Inspection Protocol

1. Generate UV layout: `--mode UV_INSPECT`
2. Generate distortion heatmap: `--mode UV_HEATMAP`
3. **Check for:** Overlapping islands, out-of-bounds geometry, collapsed/zero-size islands, high distortion (red areas in heatmap)
4. **Fix:**
   - Collapsed? → Fix `CRITICAL_ZERO_AREA_FACES` first
   - Overlapping? → Enable `auto_unwrap`, or verify manual UV math in `build_shape`
   - Bad seams? → Ensure Edge Slot 1 (Perimeter) and 3 (Guide) are correctly tagged
   - Distorted? → Fix seam placement or switch UV strategy per slot
   - Scale off? → Adjust `uv_scale_i` in the SLOTS tab

### Common Issues Quick-Reference

| Symptom | Likely Cause | Fix |
|:---|:---|:---|
| Object disappears on Redo | Resurrection delete flow issue | Check `target_delete_name` handling in `invoke()` / `execute()` |
| UV smearing on cylinder | Missing Guide seam (role 3) | Tag one longitudinal edge: `e[edge_slots] = 3` |
| Bevel artifacts near chamfer | Thin sliver faces near bevel edges | Fix source topology; check `WARNING_THIN_FACES` |
| Double geometry on Redo | Child cleanup not matching names | UCX/Joint/Socket children must start with `UCX_`, `MASSA_JOINT_`, `SOCKET_` |
| Seams ignored by LSCM unwrap | `auto_unwrap_use_slots = False` | Enable "Use Edge Slots" in UVs tab or tag edges with role 1/3 |
| All materials appear grey | `ensure_default_library()` not called | Add `mat_utils.ensure_default_library()` before any material access |
| Physics ID = 0 on all faces | `"phys"` key missing from `get_slot_meta` | Add valid `"phys"` key to every slot in the meta dict |
| Socket empties missing | `sock_enable = False` on Console | Enable "Generate Sockets" in SOCKETS tab |
| UCX objects not generated | `phys_gen_ucx = False` on Console | Enable "Generate UCX" in COLLISION tab |
| Cartridge not discovered | Missing `CARTRIDGE_META` or no operator | Add module-level `CARTRIDGE_META` dict and a `Massa_OT_Base` subclass |

---

> **Massa Console Architect v6.6**
> *Blender 5.0 Extension — `massa_mesh_gen` v2.0.0*
> *Maintained by 3D_Massa*
