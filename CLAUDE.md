# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code Exploration Policy

Always use jCodemunch-MCP tools for code navigation. Never fall back to Read, Grep, Glob, or Bash for code exploration.

**Exception:** Use `Read` when you need to edit a file — the agent harness requires a `Read` before `Edit`/`Write` will succeed. Use jCodemunch tools to *find and understand* code, then `Read` only the specific file you're about to modify.

**Repo identifier:** `local/MASSA_BMESH_CONSOLE-main-baadc0ec`

**Start any session:**
1. `resolve_repo { "path": "." }` — confirm the project is indexed. If not: `index_folder { "path": "." }`
2. `plan_turn { "repo": "local/MASSA_BMESH_CONSOLE-main-baadc0ec", "query": "<task>", "model": "claude-sonnet-4-6" }` before any code task

**Finding code:**
- symbol by name → `search_symbols`
- string / comment / config → `search_text`
- before opening any file → `get_file_outline` first
- one or more symbols → `get_symbol_source`

**After editing files:**
PostToolUse hooks are installed — edited files are auto-reindexed. For bulk edits (5+ files), call `register_edit` with all paths to batch-invalidate.

---

## Commands

### Package the Addon

Creates `_EXPORT/massa.zip` (Blender 5.0 Extension format, `blender_manifest.toml` at ZIP root):

```
python _Scripts/package_massa_addon.py
```

### Audit / Test a Cartridge (Headless Blender)

First, set `BLENDER_PATH` in [`massa/modules/debugging_system/config.py`](massa/modules/debugging_system/config.py).

```
python _Scripts/test_run_cartridge.py <path/to/cartridge.py> [--mode MODE]
```

**Available modes:** `AUDIT` (default), `VISUAL_DIFF`, `UV_HEATMAP`, `UV_INSPECT`, `PERFORMANCE`, `CSG_DEBUG`, `RENDER`, `SKILL_EXEC`, `CONSOLE_AUDIT`

Example:
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/cart_prim_02_pipe.py --mode AUDIT
```

Results are JSON printed to stdout (bracketed by `---AUDIT_START---` / `---AUDIT_END---` markers).

---

## Architecture

### Addon Entry Point & Registration Order

[`massa/__init__.py`](massa/__init__.py) registers everything in a strict dependency order:

1. **Console** (`massa_console`) — Blender scene property bag (`context.scene.massa_console`), the persistent shared-settings brain
2. **Engine** (`massa_engine`) — the generation pipeline
3. **Operators** (`massa_base`, `massa_tools`, `massa_point_tool`, `massa_shooter`) — Blender operator classes
4. **Cartridges** (`cartridges`) — auto-discovered parametric generators
5. **UI** (`ui_massa_panel`, `ui_massa_pie`, `gizmo_massa`) — panels, pie menus, gizmos

The same file handles hot-reload: if `massa_console` is already in `locals()`, all modules are reloaded in dependency order before re-discovery.

---

### The Cartridge System

**Cartridges** are the core content unit. Each is a self-contained `.py` file in [`massa/modules/cartridges/`](massa/modules/cartridges/) that defines a parametric mesh primitive.

**Auto-discovery** (`massa/modules/cartridges/__init__.py`) scans the directory on import, validates each file, and registers/unregisters its operator class. **No manual registration is needed** — drop a file in the folder and reload.

#### Cartridge Mandate (required for discovery)

Every cartridge **must** define:

| Requirement | Description |
|---|---|
| `CARTRIDGE_META` dict | Top-level with keys: `name`, `id`, `icon`, `flags` |
| `Massa_OT_Base` subclass | The operator class with `bl_idname` |
| `build_shape(self, bm)` method | BMesh geometry generation logic |
| `get_slot_meta(self)` method | Returns dict mapping slot index → `{name, uv, phys, sock?}` |

**Minimal `CARTRIDGE_META`:**
```python
CARTRIDGE_META = {
    "name": "My Part",
    "id": "my_part",          # used as bl_idname suffix: massa.gen_my_part
    "icon": "MESH_CUBE",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "ALLOW_FUSE": True,
    },
}
```

**Valid flags:** `USE_WELD`, `ALLOW_SOLIDIFY`, `ALLOW_FUSE`, `ALLOW_CHAMFER`, `LOCK_PIVOT`, `REMOVE_LOOSE`, `FIX_DEGENERATE`

**`get_slot_meta` example:**
```python
def get_slot_meta(self):
    return {
        0: {"name": "Body",   "uv": "BOX",    "phys": "METAL_STEEL"},
        1: {"name": "Trim",   "uv": "UNWRAP", "phys": "RUBBER"},
        9: {"name": "Socket", "uv": "SKIP",   "sock": True},
    }
```

`uv` values: `"BOX"` (analytic box-map), `"UNWRAP"` (LSCM/conformal), `"SKIP"`, `"KEEP"`. Slot 9 with `"sock": True` generates a socket empty at the tagged face.

**Reference implementation:** [`massa/modules/cartridges/cart_massa_builder_example.py`](massa/modules/cartridges/cart_massa_builder_example.py)

#### Cartridge Naming Conventions

| Pattern | Category |
|---|---|
| `cart_prim_NN_name.py` | Primitives (beam, pipe, panel, …) |
| `cart_arc_NN_name.py` | Architecture elements (wall, stairs, …) |
| `cart_arch_NN_name.py` | Architectural structures |
| `cart_ind_NN_name.py` | Industrial (truss, duct, silo, …) |
| `cart_asm_NN_name.py` | Assemblies (HVAC, crane, iris door, …) |
| `cart_urb_NN_name.py` | Urban props (bench, bollard, kiosk, …) |
| `cart_lnd_NN_name.py` | Landscape |
| `cart_prp_NN_name.py` | Props (container, rack, greeble) |
| `prim_con_name.py` | Construction primitives |

---

### Generation Pipeline

`Massa_OT_Base.execute()` → `massa_engine.run_pipeline(op, context)`

Pipeline stages in order:

1. `op.build_shape(bm)` — cartridge fills the BMesh
2. Cleanup degenerate geometry (if `FIX_DEGENERATE`)
3. `auto_detect_edge_slots` + `process_edge_slots` — sets seams/sharps/crease/bevel from tagged edge slots
4. `auto_detect_sharp_edges`
5. Global scale + pivot alignment
6. `gather_manifest` → `apply_protection_mask` → `apply_slot_inflation` → `apply_hard_merge`
7. Polish stack (`_run_polish_stack`) — fuse, solidify, bridge, fill holes, symmetrize, taper, bend, noise, smooth, decay, triangulate, chamfer (each gated by `op.pol_*_active` flags and cartridge flags)
8. Seam solving (`seam_solvers.apply_base_drivers` / `solve_seams`) if `seam_active`
9. Surface map generation (`generate_surface_maps`)
10. Mesh output: material assignment, UV unwrap/pack, socket spawning, UCX collision generation, auto-rigger

Output object receives:
- `obj["massa_op_id"]` — operator ID for resurrection
- `obj["MASSA_PARAMS"]` — full serialized operator state for edit/redo

---

### MassaBuilder — Fluent BMesh Wrapper

[`massa/modules/massa_builder.py`](massa/modules/massa_builder.py) provides `MassaBuilder`, a high-level fluent API wrapping raw `bmesh` ops. Use it inside `build_shape()` instead of calling `bmesh.ops.*` directly.

```python
def build_shape(self, bm):
    builder = MassaBuilder(bm)
    builder.create_box(width=2, depth=2, height=1) \
           .tag_slot(0)                              # assign material slot
    builder.select_faces_by_normal(Vector((0,0,1))) \
           .extrude(0.5) \
           .tag_slot(1)
    builder.tag_socket(1)   # place socket empty on active faces
    builder.clean()
```

Key methods: `create_box`, `create_grid`, `create_cylinder`, `extrude`, `inset`, `select_faces_by_normal`, `tag_slot`, `tag_socket`, `clean`, `report`.

---

### Slot & Edge-Slot System

**Material slots (0–9):** Defined per-cartridge in `get_slot_meta()`. The engine compresses only used slots into the final mesh's material list (`slot_map` remaps logical → actual index).

**Edge slots (1–5):** Tagged via the `MASSA_EDGE_SLOTS` integer layer on BMesh edges. Controlled by operator properties `edge_slot_N_action`:

| Action | Effect |
|---|---|
| `SEAM` | Marks UV seam |
| `SHARP` | Marks sharp edge |
| `BOTH` | Seam + sharp |
| `CREASE` | Subdivision crease |
| `BEVEL` | Bevel weight |
| `IGNORE` | No action |

Slots 1, 3, 5 are also used as seam boundaries by the auto-unwrap system when `auto_unwrap_use_slots` is on.

---

### Resurrection / Redo System

Each generated object stores its full parameter state in `obj["MASSA_PARAMS"]`. `MASSA_OT_ReRun_Active` (bl_idname: `massa.rerun_active`) re-fires the original operator with those params, deletes the old object, and restores the transform. The Redo Panel in Blender then lets the user tweak parameters live.

Console props (`context.scene.massa_console`) act as the persistent settings store between operator invocations — synced in `invoke()` and `execute()` via `Massa_OT_Base._sync()`.

---

### Debugging System

Located in [`massa/modules/debugging_system/`](massa/modules/debugging_system/). Runs Blender headlessly to execute cartridges and return structured JSON audit results.

- **`config.py`** — set `BLENDER_PATH` here before running any scripts
- **`runner.py`** — entry point executed inside background Blender; handles all audit modes
- **`auditors/`** — individual auditor classes (`Massa_Auditor`, `Massa_Edge_Auditor`, `Massa_Surface_Auditor`, `Massa_UI_Auditor`, `massa_fuzz_auditor`)
- **`visual_inspector.py`** — renders cartridge output to image for VISUAL_DIFF / RENDER modes

The debugging system is excluded from the packaged addon ZIP.
