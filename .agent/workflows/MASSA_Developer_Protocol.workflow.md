---
description: MASSA Console Developer Protocol (Architecture & Safety)
---

# MASSA Console Developer Protocol

This workflow defines the strict protocols for understanding and modifying the `MASSA_BMESH_CONSOLE-main` addon.

## 1. System Architecture (The "Massa Anatomy")

The addon follows a strict "Brain-Muscle-Engine" separation.

* **Brain (`massa_console.py`, `massa_properties.py`)**:
  * **Role**: Stores state and property definitions.
  * **Rule**: `massa_properties.py` is the "DNA". If you add a property here, it propagates to the Console and ALL Cartridges automatically via `MassaPropertiesMixin`.
  * **Safety**: **NEVER** rename existing properties without a full repo refactor.

* **Muscle (`operators/massa_base.py`)**:
  * **Role**: The Base Operator (`Massa_OT_Base`). All cartridges inherit this.
  * **Role**: Handles execution, "Resurrection" (re-running parameter edits), and syncing.
  * **Safety**: Modify `draw` or `execute` here **ONLY** if the change applies to EVERY cartridge.

* **Engine (`modules/massa_engine.py`)**:
  * **Role**: The generation pipeline (Pipeline).
  * **Role**: Orchestrates BMesh creation $\rightarrow$ Shape $\rightarrow$ Polish $\rightarrow$ Surface $\rightarrow$ Output.
  * **Safety**: This is the critical loop. Changes here affect the fundamental mesh generation logic.

* **Content (`modules/cartridges/`)**:
  * **Role**: Individual generators.
  * **Rule**: Must implement `build_shape(self, bm)` and `get_slot_meta(self)`.
  * **Registration**: Must be registered in `modules/cartridges/__init__.py`.

## 2. Modification Protocols

### A. Creating a New Cartridge

1. **Create File**: `modules/cartridges/cart_my_new_thing.py`.
2. **Inherit**: Class must inherit `from ..operators.massa_base import Massa_OT_Base`.
3. **Define Meta**:

    ```python
    CARTRIDGE_META = {
        "name": "My New Thing",
        "version": "1.0",
        "id": "MASSA_OT_MyNewThing",
    }
    ```

4. **Implement**: `def build_shape(self, bm): ...`
5. **Register**:
    * Open `modules/cartridges/__init__.py`.
    * Import new module: `from . import cart_my_new_thing`
    * Add module to `MODULES` list.
    * Add class to `CLASSES` list.

### B. Modifying UI

* **Location**: `ui/ui_shared.py` contains the drawing logic for Tabs (Shape, Data, Polish, UVs).
* **Rule**: Do NOT add UI code directly to `operators/massa_base.py`. Delegate to `ui_shared.py`.

### C. Adding a Global Parameter

1. **Edit**: `modules/massa_properties.py`.
2. **Add**: `my_new_param: BoolProperty(...)`.
3. **UI**: Add the draw call in `ui/ui_shared.py`.
4. **Logic**: Implement handling in `modules/massa_engine.py` (if it affects generation) or `massa_polish.py`.

## 3. Critical Safety Checks

* **Resurrection**: The system allows users to re-edit meshes. Any new property MUST be captured in `_capture_operator_params` (in `massa_engine.py`) and restored in `Massa_OT_Base.invoke`.
  * *Note*: `_capture_operator_params` automatically captures RNA properties. If you use non-RNA state, you must manually handle it.
* **Headless Safety**: `operators/massa_base.py` enforces `mat_utils.ensure_default_library()` before generation. Do not remove this, or headless tests will crash.
* **Hot Reload**: `__init__.py` (Root) handles hot reloading. If you add a NEW module file (e.g., `modules/massa_new_system.py`), you MUST add it to the reload logic in `__init__.py` to ensure it updates without restarting Blender.

## 4. Debugging & Verification

* **Gizmos**: `ui/gizmo_massa.py` handles viewport widgets.
* **Auditors**:
  * **Cartridges**: Use `.agent/workflows/audit_cartridge` to verify cartridge integrity.
  * **System**: Use `.agent/workflows/audit_console` to verify internal architecture (Addon Registry, Engine Pipeline, Redo Panel).
