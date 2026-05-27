# MASSA BMESH CONSOLE Project Instructions

## Project Overview
**MASSA** is a Blender 5.0 Extension (addon) procedural geometry engine for generating complex, production-ready 3D assets through a library of parametric **Cartridges**. 
The architecture relies on a strictly separated split-state design to support Blender's Redo Panel (F9) while preserving persistent settings:
- **The Brain (`massa_console.py`)**: Persistent storage residing on `bpy.types.Scene`. Survives restarts and powers the Sidebar interface.
- **The Muscle (`massa_base.py`)**: Transient executor residing on `bpy.types.Operator`. Utilized directly by the Redo Panel.
- **The Bridge (`_sync()` in `massa_base.py`)**: Critical point where values are manually copied from The Brain to The Muscle.
- **The Cartridge (`modules/cartridges/*.py`)**: Specialized python modules responsible purely for BMesh shape generation (`build_shape`).

## Building and Running
The development setup supports both live-reloading within Blender and headless testing.
- **Packaging the Addon**: Run `python _Scripts/package_massa_addon.py` to create `_EXPORT/massa.zip`.
- **Debugging & Auditing**: Do not write custom execution scripts. Use the built-in debugging suite (which spawns a headless Blender process):
  - Audit a cartridge: `python massa/modules/debugging_system/runner.py --cartridge massa/modules/cartridges/<name>.py --mode AUDIT`
  - UV distortion heatmap: `... --mode UV_HEATMAP`
  - UV layout inspection: `... --mode UV_INSPECT`
  - Compare versions: `... --mode VISUAL_DIFF`
- **External Script Wrapper**: `python _Scripts/test_run_cartridge.py <path/to/cartridge.py> --mode <MODE>`
- **Live State Inspection**: `python massa/modules/debugging_system/debug_agent.py --code "<python_code>"`

*Note: Ensure `BLENDER_PATH` is correctly configured in `massa/modules/debugging_system/config.py` before running the tools.*

## Development Conventions

### Parameter Integration: The "Rule of Five"
To prevent "Ghost Controls," any new parameter must be instantiated across five specific locations:
1. Define the property within **The Brain**.
2. Define a matching property within **The Muscle**.
3. Register the property key within **The Bridge's** synchronization list (`_sync()`).
4. Draw the control in the Sidebar UI.
5. Draw the control in the Redo UI.

Enforce explicit and correct Blender property typing (e.g., `bpy.props.FloatProperty`, `IntProperty`) with `default`, `min`, and `max` kwargs.

### The Cartridge System & Mandates
All new geometry cartridges must adhere strictly to the rules laid out in `CARTRIDGE_MANDATE.md` and the 6 Laws of Compliance:
1. **Law of Segmentation**: Long faces must be subdivided for proper Polish Stack deformation.
2. **Law of Edge Roles**: Edges must be assigned to the `MASSA_EDGE_SLOTS` layer (Perimeter, Contour, Guide, Detail).
3. **Law of Identity**: Cartridges must return a dictionary of used slots via `get_slot_meta()` to drive Socket manifestations.
4. **Law of Defaults**: `CARTRIDGE_META` must explicitly define `scale_class` and structural flags.
5. **Law of Surface**: Geometry must maintain valid normals and remain watertight.
6. **Law of Output**: Zero tolerance for loose vertices or zero-area faces.

**Implementation Rules:**
- **Headless Safety**: NEVER use `bpy.ops.*` or read `bpy.context.*` inside the `build_shape` method. Use pure BMesh (`bmesh.ops`), `MassaBuilder`, and `mathutils` exclusively.
- **Strict Phase Containment**: Never bleed logic between execution phases. Cartridge logic (Phase A) must only generate base BMesh topology. Do not attempt to apply modifiers or solidify in this phase.
- **Naming Conventions**: Cartridges must use prefix-based names: `cart_prim_` (Primitives), `cart_arc_`/`cart_arch_` (Architecture), `cart_ind_` (Industrial), `cart_asm_` (Assemblies), `cart_urb_` (Urban), `cart_lnd_` (Landscape), `cart_prp_` (Props).
- **UV Strategy**: The "Golden Cartridge" standard is **manual UV unwrapping** inside `build_shape` using the `"SKIP"` strategy. Provide `uv_scale` and `fit_uvs` parameters to allow scaling without Console overrides.
- **Sockets Protocol**: Sockets are defined by tagging existing faces using `tag_socket(id)` or mapping them in `get_slot_meta()`. Do not create extraneous geometry.
- **Resurrection System**: Generated objects store their state in `obj["MASSA_PARAMS"]`. `MASSA_OT_ReRun_Active` re-fires the operator with these params. **NEVER** rename properties in `MassaPropertiesMixin` or Cartridge operators, as it breaks this system.

### Hardcoded Strings & Integration
- Never alter hardcoded string inputs for "Massa_SDF_Fuse" without refactoring the Geometry Nodes tree.
- Enforce exact string matching for vertex color layers (`Wear`, `Thick`, `Grav`) and "UVMap" renaming.

### UV Preview System
- `massa.uv_preview` / `massa.uv_preview_exit` operators provide non-destructive UV inspection by temporarily disabling GeoNodes modifiers.
- The pipeline includes a UV safety net (`_apply_emergency_box_map`) ensuring no object has entirely empty UVs.
- UV Preview stores modifier states in `obj["MASSA_UV_PREVIEW_MODS"]` — do NOT delete this key manually while in preview mode.
