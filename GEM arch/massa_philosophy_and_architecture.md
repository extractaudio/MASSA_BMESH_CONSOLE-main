# MASSA Philosophy and Core Architecture

> **"The Console is Law. The Cartridge is Art."**

## 1. Overview & Philosophy
MASSA is a Blender addon for generating complex, parametric 3D meshes through a modular "cartridge" system.
It operates as a **Procedural Engine** that consumes **Cartridges** (Generators).

- **The Console** handles the "Boring Stuff": UI, Undo/Redo, Material Assignment, UV Unwrapping, Physics Generation, Socket Constraints, Polish (Bevels/Chamfers), and File Management.
- **The Cartridge** handles the "Fun Stuff": Pure BMesh geometry generation (`build_shape`).

**Goal:** A Cartridge should only focus on *shape*. If it follows the **Mandates**, the Console grants it superpowers (Auto-UVs, Physics, etc.) for free.

## 2. Workflow
The general workflow of MASSA is:
`Select Cartridge → Generate → Live Edit (Redo Panel) → Resurrect / Condemn`

1. **Select**: Pick from available cartridges.
2. **Generate**: The engine runs its 6-phase pipeline (shape → edge detection → sharpness → polish → UVs/materials → output).
3. **Live Edit**: Parameters (size, segments, profiles) are changed real-time in the Blender Redo Panel.
4. **Resurrect**: Settings are stored in `obj["MASSA_PARAMS"]`. Re-select the object and press **Resurrect** to re-open its parameters.
5. **Condemn**: Finalize the object. Applies procedural logic and converts to a static Blender mesh.

## 3. Strict Architecture Split
The system adheres to a strict 4-part separation:

- **Brain (State)** (`modules/massa_properties.py`, `modules/massa_console.py`):
  Persistent state. Defines the property DNA shared by Scene and Operator. The `MassaPropertiesMixin` defines properties that exist on BOTH the Scene (UI) and the Operator (History).

- **Muscle (Operator)** (`operators/massa_base.py`):
  Execution shell (`Massa_OT_Base`). Handles:
  1. **Sync**: Copies props from Scene to Operator.
  2. **Resurrection**: Restores props from `obj["MASSA_PARAMS"]`.
  3. **UI**: Draws the Redo Panel.

- **Engine (Pipeline)** (`modules/massa_engine.py`):
  The heavy lifter containing the 6-phase pipeline:
  1. **Phase 1**: `build_shape(bm)` (The Cartridge).
  2. **Phase 2**: `auto_detect_edge_slots` (If not manually set).
  3. **Phase 3**: `auto_detect_sharp_edges` (Additive).
  4. **Phase 4**: Polish Stack (Bevel, Fuse, Solidify).
  5. **Phase 5**: Output (Mesh conversion, Material Assignment, Physics, Sockets).

- **Content (Cartridges)** (`modules/cartridges/`):
  Self-contained parametric geometry generators. Drop a new file in the folder, and it auto-registers.

## 4. Observer and Shooter
- **Shooter (Targeting)** (`operators/massa_shooter.py`): "Point & Shoot" mode. Injects location/rotation into Operator history.
- **Observer (Analytics)** (`modules/advanced_analytics.py`): Visual debugging (`debug_view`) and telemetry.
