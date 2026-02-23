# 🤖 JULES MASSA PROTOCOL

You are operating within the `MASSA_BMESH_CONSOLE` repository. This is a procedural geometry engine for Blender 5.0. It is heavily modularized into a strict Split-State Architecture.

## 1. System Anatomy (Understand Before Modifying)

- **🧠 Brain (`modules/massa_console.py` / `modules/massa_properties.py`)**: Persistent state. Defines the DNA (properties). NEVER rename existing properties; deprecate them instead to preserve the Resurrection system.
- **💪 Muscle (`operators/massa_base.py`)**: The transient Operator. Handles execution, UI Tabs, and Resurrection via the `_sync()` method.
- **⚙️ Engine (`modules/massa_engine.py`)**: The core generation pipeline. Execution Flow: BMesh creation -> Shape -> Polish -> Surface -> Physics.
- **📦 Content (`modules/cartridges/`)**: The actual mesh generators. Each cartridge is an isolated script that must plug into the Engine.

## 2. Tooling & Execution Environment

Do not write custom execution scripts. You have a built-in headless debugging suite located in `modules/debugging_system/`. Always use these tools to verify your code and test the Blender state.

| Action | Command | Purpose |
| :--- | :--- | :--- |
| **Inspect Live State** | `python modules/debugging_system/debug_agent.py --code "import bpy; print(bpy.data.objects.keys())"` | Execute arbitrary Python inside the active headless Blender instance to inspect context. |
| **Audit Cartridge** | `python modules/debugging_system/runner.py --cartridge modules/cartridges/<name>.py --mode AUDIT` | Runs geometric checks (zero area faces, loose verts, non-manifold geometry, pinched UVs). |
| **Fuzz Test** | The `runner.py` tool automatically utilizes `auditors/massa_fuzz_auditor.py` during audits to randomize parameters and check for crashes. |
| **Visual Diff** | `python modules/debugging_system/runner.py --cartridge <path_a> --mode VISUAL_DIFF --payload '{"filename_b": "<path_b>"}'` | Generates a red/green comparison image of two cartridge versions. |

## 3. The Prime Directives for Cartridge Development

When tasked with creating or modifying a Cartridge in `modules/cartridges/`, you MUST adhere to the following rules:

1. **Inheritance**: The class must inherit from `Massa_OT_Base`.
2. **Metadata**: You must define `CARTRIDGE_META` (containing `name`, `id`, `icon`, and `flags`) at the top of the file.
3. **No `bpy.ops`**: Inside the `build_shape(self, bm)` method, you are strictly forbidden from using `bpy.ops`. You must construct geometry using `bmesh.ops` or pure math.
4. **Slot Mapping**: You must define `get_slot_meta(self)` returning up to 10 slots (0-9). These must map to valid `phys` identifiers (e.g., `METAL_STEEL`) and define a `uv` mapping strategy (e.g., `SKIP`, `BOX`, `UNWRAP`).
5. **Edge Roles (1-5)**: If you manually define edge roles in BMesh using the `MASSA_EDGE_SLOTS` integer layer, map them strictly:
   - 1 = Perimeter
   - 2 = Contour
   - 3 = Guide
   - 4 = Detail
   - 5 = Special

   **Auto-Detection:** If you do not assign these manually, the system uses intelligent geometric analysis:
   - **Slot 1 (Perimeter):** End Caps / Silhouette.
   - **Slot 3 (Guide):** Cylinder Seams / Tube Cuts (Essential for UV Unwrapping).

   **UV Auditing & Fixing:** The "Pinched UV" or distorted mapping issues can be diagnosed using the "Finalize & Inspect" operator. This tool condemns the procedural object (applying all modifiers) and immediately enters UV Editing mode with all faces selected and unpacked.

## 4. Parameter Addition Protocol (The Rule of Five)

If tasked with adding a new global parameter to the engine, you must strictly modify all 5 bridge points to ensure state synchronization:

1. **Brain**: Add the property definition to `bpy.types.Scene` via `modules/massa_properties.py`.
2. **Muscle**: Add to `bpy.types.Operator` via inheritance (handled automatically if added to `MassaPropertiesMixin`).
3. **Bridge**: Add the string name of the exact property to the `_sync()` list in `operators/massa_base.py`.
4. **Interface**: Add the UI drawing logic to the Sidebar UI in `ui/ui_shared.py`.
5. **Logic**: Implement the geometric/system logic inside the Engine pipeline (e.g., `modules/massa_polish.py`, `modules/massa_engine.py`, or `modules/massa_surface.py`).

## 5. The Golden Cartridge Workflow

Whenever you are tasked with creating or modifying a cartridge in `modules/cartridges/`, you are strictly bound by the `CARTRIDGE_MANDATE.md` file located in the root directory.

Before writing any code, you MUST execute the following workflow:

1. **Read the Mandate:** Ingest `CARTRIDGE_MANDATE.md` to refresh your understanding of manual UV mapping, Edge Slots (1-5), and Socket Protocols.
2. **Analyze a Golden Reference:** Inspect an existing "Golden Cartridge" that closely matches the new task to understand the established mathematical patterns.
   - For structural profiles: Analyze `cart_prim_01_beam.py`
   - For complex UVs and boolean-like math: Analyze `cart_prim_04_panel.py`
   - For mathematical curves/arrays: Analyze `cart_prim_05_catenary.py` or `cart_prim_11_helix.py`
3. **Execute:** Write the `build_shape` logic using purely `bmesh` and `mathutils`.
4. **Verify:** Run the `modules/debugging_system/runner.py` in AUDIT mode to ensure zero topology flags are triggered.
