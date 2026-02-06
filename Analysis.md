# Project Analysis: Massa Modular Architect (MASSA_BMESH_CONSOLE)

## 1. Executive Summary

**Massa Modular Architect** (internally `MASSA_BMESH_CONSOLE`) is a sophisticated procedural geometry generation system for Blender 5.0. It leverages a "Cartridge" system where individual Python scripts define parametric geometry logic using Blender's BMesh API. The system is designed with a strong emphasis on automation, auditing, and AI integration, featuring a "Twin-Engine" architecture that couples an internal Blender addon with an external Model Context Protocol (MCP) server.

The project aims to provide a robust framework for generating "in-the-box" procedural assets (Primitives, Construction elements, Architecture) that are highly optimized, UV-unwrapped, and material-ready ("Slotted").

## 2. System Architecture

The system operates on a **Twin-Engine** model:

1.  **External Engine (MCP Server)**:
    -   Located in `MASSA_BMESH_CONSOLE-main/MCP/server.py`.
    -   Implements the Model Context Protocol using `FastMCP`.
    -   Exposes tools for orchestration, auditing, scene generation, and inspection.
    -   Communicates with Blender via a TCP socket (default port 5555).

2.  **Internal Engine (Blender Addon)**:
    -   Located in `MASSA_BMESH_CONSOLE-main/`.
    -   **Bridge**: `mcp_bridge.py` listens for commands from the MCP server.
    -   **Addon Core**: Implements the "Brain-Muscle-Engine" pattern for geometry generation.

### The "Massa Anatomy"

The addon code is structured into four distinct logical layers:

-   **🧠 Brain (`modules/massa_console.py`, `massa_properties.py`)**:
    -   Holds the state and property definitions ("DNA").
    -   Properties are propagated to cartridges via `MassaPropertiesMixin`.
    -   **Critical**: Renaming properties here requires a full refactor as it breaks saved states.

-   **💪 Muscle (`operators/massa_base.py`)**:
    -   Defines `Massa_OT_Base`, the base operator class.
    -   Handles execution flow, "Resurrection" (state restoration), and UI drawing delegation.
    -   Ensures context safety for Blender operations.

-   **⚙️ Engine (`modules/massa_engine.py`)**:
    -   The central generation pipeline.
    -   Orchestrates the flow: `Build Shape` -> `Edge Slots` -> `Polish` -> `Surface` -> `Output`.
    -   Handles BMesh operations, modifier application, and object creation.

-   **📦 Content (`modules/cartridges/`)**:
    -   Individual generator scripts (e.g., `cart_prim_01_beam.py`).
    -   Must implement `build_shape(bm)` and `get_slot_meta()`.
    -   Self-contained logic for specific geometry types.

## 3. Core Components

### Cartridges
Cartridges are the fundamental units of generation. They are designed to be lightweight and focused solely on geometry creation.
-   **Structure**: Inherit from `Massa_OT_Base`, define metadata (`CARTRIDGE_META`), and implement `build_shape`.
-   **Categories**: Organized by prefixes (e.g., `cart_prim_` for Primitives, `prim_con_` for Construction).
-   **Isolation**: Errors in a cartridge should not crash the host system.

### Slots
A robust system for attribute assignment:
-   **Face Slots**: Assign materials and physics IDs to faces.
-   **Edge Slots**: Assign attributes like Seams, Sharps, Creases, and Bevel Weights to edges based on ID (1-4).
-   **Auto-Detection**: The engine can automatically detect edge slots based on material boundaries.

### Resurrection System
Allows users to re-edit generated objects.
-   **Capture**: `_capture_operator_params` serializes operator properties to the object's `["MASSA_PARAMS"]` custom data.
-   **Restore**: `Massa_OT_Base.invoke` reads these parameters to restore the UI state when the operation is re-run.

## 4. MCP Integration & Workflows

The MCP server exposes a rich set of tools to AI agents, effectively making the IDE and Blender scene "agent-aware".

### Key Capabilities
-   **Session Management**: Launching Blender in GUI or Headless mode.
-   **Auditing**: Running automated audits on cartridges and the console (`audit_cartridge`, `audit_console`).
-   **Inspection**: querying scene data (`inspect_scene`, `scan_telemetry`), object data, and evaluated mesh data.
-   **Manipulation**: Generating scenes from layouts (`generate_scene`), editing node graphs, and organizing the outliner.

### Workflows (Agent Resources)
The system stores operational protocols as Markdown files in `.agent/workflows/` and exposes them as MCP resources:
-   `massa://protocol/generator_workflow`
-   `massa://protocol/audit_cartridge`
-   `massa://protocol/repair_workflow`
-   etc.

These workflows guide agents (like Cursor/Windsurf) in performing complex tasks like repairing broken cartridges or generating new ones.

## 5. Developer Protocols

Strict rules ensure stability:
1.  **Modification**:
    -   **UI**: Do not edit `massa_base.py` for UI; use `ui/ui_shared.py`.
    -   **Properties**: Do not rename existing properties; deprecate and create new ones.
    -   **Engine**: Changes in `massa_engine.py` affect *all* cartridges.
2.  **Safety**:
    -   `mat_utils.ensure_default_library()` must strictly remain in `massa_base.py` for headless safety.
    -   New modules must be registered in `__init__.py` for hot reloading.

## 6. Directory Structure Overview

```
/
├── .agent/workflows/       # Agent protocols and workflows
├── MASSA_BMESH_CONSOLE-main/
│   ├── MCP/
│   │   └── server.py       # FastMCP Server
│   ├── modules/
│   │   ├── cartridges/     # Geometry generators (Content)
│   │   ├── debugging_system/ # Auditing and bridge logic
│   │   ├── massa_console.py # Brain
│   │   ├── massa_engine.py  # Engine
│   │   └── ...
│   ├── operators/
│   │   └── massa_base.py   # Muscle
│   ├── ui/                 # UI panels and gizmos
│   ├── utils/              # Helper utilities
│   ├── __init__.py         # Addon entry point
│   └── OVERVIEW.md         # Internal developer guide
├── README.md               # General documentation
└── Analysis.md             # This file
```
