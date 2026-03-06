# MASSA BMesh Console: System Overview

This document provides a comprehensive overview of the MASSA BMesh Console addon, its architecture, core concepts, and development protocols.

---

## 1. High-Level Concept

MASSA is a procedural geometry engine for Blender. Its primary function is to generate complex `BMesh` geometry through a system of "cartridges."

The core user workflow is as follows:
1.  **Select a Cartridge**: The user chooses a desired geometry generator (a "cartridge") from a list in the Blender N-Panel.
2.  **Generate**: Pressing the "Generate" button executes the selected cartridge, creating a new mesh object in the scene.
3.  **Live Edit**: Immediately after generation, Blender's "Redo Panel" (Operator Adjust panel) appears. This panel is populated with custom parameters defined by the cartridge, allowing the user to interactively modify the mesh's properties (e.g., size, segments, complexity).
4.  **Resurrect & Condemn**:
    *   **Resurrection**: A previously generated MASSA object can be selected, and its parameters can be re-opened in the Redo Panel for further editing.
    *   **Condemnation**: The procedural object can be finalized ("condemned"), which applies all logic and converts it into a standard, static Blender mesh, no longer editable by the MASSA system.

---

## 2. System Architecture (The "Massa Anatomy")

The addon is built on a strict separation of concerns, referred to as the "Brain-Muscle-Engine" architecture.

*   **🧠 Brain (`massa_properties.py`)**:
    *   **Role**: Defines the persistent state and all shared properties for the entire system. It is the "DNA" of the addon.
    *   **Implementation**: Properties are defined in a mixin class (`MassaPropertiesMixin`) which is inherited by the base operator, making them globally available to all cartridges.
    *   **Rule**: Properties in the Brain should not be renamed, as this would break the "Resurrection" capability for older objects.

*   **💪 Muscle (`operators/massa_base.py`)**:
    *   **Role**: This is the base operator class, `Massa_OT_Base`, from which all cartridges must inherit.
    *   **Function**: It handles the core execution loop, draws the shared UI tabs (Polish, UVs, Data) in the Redo Panel, and manages the property synchronization (`_sync`) required for the Resurrection system.

*   **⚙️ Engine (`modules/massa_engine.py`)**:
    *   **Role**: The central generation pipeline that orchestrates the creation of the final mesh.
    *   **Execution Flow**: `BMesh Creation` -> `Shape` (runs cartridge logic) -> `Polish` (applies global modifiers like Twist/Bend) -> `Surface` (handles UVs and materials) -> `Output`.

*   **📦 Content (`modules/cartridges/`)**:
    *   **Role**: A directory of individual, self-contained Python scripts that act as the geometry generators. Each `.py` file is a unique cartridge that plugs into the engine.

---

## 3. The Object Lifecycle

A MASSA object progresses through several distinct states.

1.  **Generation**: A user triggers a cartridge. The `Massa_OT_Base` operator is invoked, which calls the `massa_engine` with the cartridge's parameters.
2.  **Live Editing (The Redo Panel)**: The engine generates a `BMesh` according to the cartridge's `build_shape` method. The Redo Panel appears, allowing the user to change parameters. Each change causes the operator to re-execute, and the engine regenerates the mesh from scratch with the new settings.
3.  **Resurrection**: If a user selects a previously generated (but not condemned) MASSA object, the system can read its stored properties and re-invoke the Redo Panel, allowing edits to resume as if the object were just created.
4.  **Condemnation (Finalization)**: The user finalizes the object. This is a destructive operation that applies all procedural logic, converts temporary `BMesh` data layers (like Edge Slots) into permanent mesh attributes, and leaves a standard, non-procedural Blender mesh.

---

## 4. The Cartridge Mandate

To be considered a valid "Golden Cartridge," a script must adhere to a strict contract defined in `CARTRIDGE_MANDATE.md`.

*   **Inheritance**: The main class must inherit from `Massa_OT_Base`.
*   **Metadata (`CARTRIDGE_META`)**: A module-level dictionary must be defined, containing the cartridge's `name`, `id`, `icon`, and behavior `flags` (e.g., `ALLOW_SOLIDIFY`).
*   **Geometry Logic (`build_shape`)**: The core mesh creation logic must be implemented in the `build_shape(self, bm)` method. This method receives a `BMesh` object and must modify it in place. **Crucially, the use of `bpy.ops` is strictly forbidden within this method.** All geometry must be created using `bmesh.ops` or mathematical calculations.
*   **Data Slots (`get_slot_meta`)**: A method must be defined to return a dictionary mapping up to 10 material slot indices (0-9) to their purpose (e.g., `{"name": "Surface", "uv": "SKIP", "phys": "METAL_STEEL"}`). This is fundamental for material assignment and UV strategies.
*   **UI Definition (`draw_shape_ui`)**: The cartridge-specific parameters for the Redo Panel's "Shape" tab are defined in the `draw_shape_ui(self, layout)` method.

---

## 5. Data Layers: The Soul of the Mesh

MASSA geometry is not just about vertices and faces; it is enriched with custom data that drives downstream processes.

*   **Material Slots**: Defined by `get_slot_meta`, these assign a purpose to each material index. This allows the engine to apply materials and UV strategies intelligently.
*   **Edge Slots (`MASSA_EDGE_SLOTS`)**: A custom integer `BMesh` layer is used to tag edges with a specific role, which is critical for procedural UV unwrapping and beveling.
    *   `1`: **Perimeter** (Hard edges, boundaries, UV seams)
    *   `3`: **Guide** (Topological guides, e.g., the "zipper" seam on a cylinder)
*   **Data Stamp Mandate**: Because `BMesh` custom data is lost when converting to a regular mesh, the engine has a "Data Stamp" protocol. On finalization, it reads the `MASSA_EDGE_SLOTS` layer and creates persistent Named Attributes on the mesh (e.g., `Massa_Edge_Hard`), preserving the edge role information.

---

## 6. UI: The Redo Panel & Its Rules

The Redo Panel is a volatile environment; the operator's memory is wiped every time a user changes a parameter. This "Redo Trap" requires special UI patterns.

*   **The Boolean Trigger Pattern**: To create a button that doesn't close the panel, a `BoolProperty` is used, drawn with `toggle=True`. The base operator detects when this boolean is set to `True`, executes the associated function, and immediately resets it to `False`.
*   **The Scene Proxy Pattern**: To maintain persistent data like lists, the data is stored on `bpy.types.Scene` instead of the operator itself. The UI then draws the list from the scene data.
*   **The Node Tree Hack**: To use stateful widgets like color ramps or curves, which operators cannot own, they are proxied through a dummy node tree that persists in the Blender file.

---

## 7. Development & Quality Assurance

The MASSA system is designed for stability and includes a robust set of development protocols and tools.

*   **The Rule of Five**: When adding a new global parameter, a developer must modify 5 key areas to ensure proper integration: the **Brain** (properties), **Muscle** (syncing), **Bridge** (sync list), **Interface** (UI), and **Logic** (engine).
*   **Debugging Suite (`modules/debugging_system/`)**: The addon includes a headless debugging suite for testing and verification without opening the Blender UI.
    *   `debug_agent.py`: Executes arbitrary Python code within a Blender context.
    *   `runner.py`: A powerful auditing tool to check cartridges for geometric errors (e.g., zero-area faces), UV issues, and performance regressions.
*   **Automated Auditing**: The system philosophy emphasizes "First-Time-Right" cartridges. The workflows and tools are designed to run automated telemetry and audits to catch errors, non-manifold geometry, and bad UVs before a cartridge is integrated.