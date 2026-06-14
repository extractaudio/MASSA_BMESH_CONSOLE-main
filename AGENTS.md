# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Code Exploration Policy

Always use jCodemunch-MCP tools for code navigation. Never fall back to Read, Grep, Glob, or Bash for code exploration.

Call the jcodemunch_guide tool and strictly follow its instructions.

**Exception:** Use `Read` when you need to edit a file — the agent harness requires a `Read` before `Edit`/`Write` will succeed. Use jCodemunch tools to *find and understand* code, then `Read` only the specific file you're about to modify.

**Repo identifier:** `local/MASSA_BMESH_CONSOLE-main-baadc0ec`

If `resolve_repo` returns a different repo identifier for this checkout, use the returned identifier for all later jCodemunch calls in the same session.

**Start any session:**

1. `resolve_repo { "path": "." }` — confirm the project is indexed. If not: `index_folder { "path": "." }`
2. `plan_turn { "repo": "local/MASSA_BMESH_CONSOLE-main-baadc0ec", "query": "<task>", "model": "Codex-sonnet-4-6" }` before any code task

**Finding code:**

- symbol by name → `search_symbols`
- string / comment / config → `search_text`
- before opening any file → `get_file_outline` first
- one or more symbols → `get_symbol_source`

**jCodemunch v1.108.22 tool surface:**

- **Indexing:** `index_repo`, `index_folder`, `summarize_repo`, `index_file`
- **Discovery:** `list_repos`, `resolve_repo`, `suggest_queries`, `get_repo_outline`, `get_file_tree`, `get_file_outline`
- **Search & Retrieval:** `search_symbols`, `get_symbol_source`, `get_context_bundle`, `get_file_content`, `search_text`, `search_columns`, `get_ranked_context`, `assemble_task_context`
- **Relationships:** `find_importers`, `find_references`, `check_references`, `get_dependency_graph`, `get_class_hierarchy`, `get_related_symbols`, `get_call_hierarchy`, `find_implementations`
- **Impact & Safety:** `get_blast_radius`, `check_rename_safe`, `check_delete_safe`, `get_impact_preview`, `get_changed_symbols`, `plan_refactoring`, `get_symbol_provenance`, `get_pr_risk_profile`
- **Architecture:** `get_dependency_cycles`, `get_coupling_metrics`, `get_layer_violations`, `get_extraction_candidates`, `get_cross_repo_map`, `get_tectonic_map`, `get_signal_chains`, `render_diagram`, `get_project_intel`, `list_workspaces`, `get_group_contracts`
- **Quality & Metrics:** `get_symbol_complexity`, `get_churn_rate`, `get_hotspots`, `get_repo_health`, `diff_health_radar`, `get_file_risk`, `get_symbol_importance`, `get_repo_map`, `find_similar_symbols`, `find_dead_code`, `get_dead_code_v2`, `get_untested_symbols`, `search_ast`, `winnow_symbols`
- **Diffs & Embeddings:** `get_symbol_diff`, `embed_repo`
- **Session-Aware Routing:** `plan_turn`, `get_session_context`, `get_session_snapshot`, `register_edit`, `digest`
- **Utilities:** `get_session_stats`, `analyze_perf`, `tune_weights`, `check_embedding_drift`, `invalidate_cache`, `test_summarizer`, `audit_agent_config`, `get_watch_status`
- **Runtime Trace Ingest & Analytics:** `import_runtime_signal`, `get_runtime_coverage`, `find_hot_paths`, `find_unused_paths`, `get_redaction_log`
- **Runtime Tier Switching:** `set_tool_tier`, `announce_model`
- **Self-Guide:** `jcodemunch_guide`

**After editing files:**
PostToolUse hooks are installed — edited files are auto-reindexed. For bulk edits (5+ files), call `register_edit` with all paths to batch-invalidate.

---

## Commands

### Verification Policy

Prefer the smallest targeted verification that proves the change. Do not run a broad "full Python test sequence" from Superpowers by default.

- Avoid `py_compile` / Python import sweeps unless the user asks or the edit specifically needs syntax verification.
- If Python verification is needed, prefer commands that do not leave `__pycache__` files, or clean generated cache files afterward.
- For cartridge geometry changes, use one focused Blender audit mode first. Add UV/visual modes only when the change directly affects UVs or rendering.
- Package the addon only when packaging behavior changed, the user asks for an export, or release readiness matters.

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

---

### UV Preview System

**File:** `operators/massa_uv_preview.py`
**Operators:** `MASSA_OT_UV_Preview` (`massa.uv_preview`), `MASSA_OT_UV_Preview_Exit` (`massa.uv_preview_exit`)

Non-destructive UV inspection. Temporarily disables interfering modifiers (SDF Fuse, Viz Overlay, Bevel) and enters Edit Mode so the UV Editor shows pipeline-generated UVs. Modifier states are stored in `obj["MASSA_UV_PREVIEW_MODS"]` and restored on exit.

The pipeline's `_generate_output()` includes a UV safety net that applies emergency box-mapping to any faces with all-zero UV coordinates, ensuring UV Preview always shows meaningful data.
