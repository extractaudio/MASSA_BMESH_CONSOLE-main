# MASSA Console Developer Protocol

> This workflow defines the strict protocols for understanding and modifying the `MASSA_BMESH_CONSOLE-main` addon.

---

## 📑 Table of Contents

- [1. System Architecture](#1-system-architecture-the-massa-anatomy)
  - [Brain](#-brain)
  - [Muscle](#-muscle)
  - [Engine](#-engine)
  - [Content](#-content)
- [2. Modification Protocols](#2-modification-protocols)
  - [A. Creating a New Cartridge](#a-creating-a-new-cartridge)
  - [B. Modifying UI](#b-modifying-ui)
  - [C. Adding a Global Parameter](#c-adding-a-global-parameter)
- [3. Critical Safety Checks](#3-critical-safety-checks)
- [4. Debugging & Verification](#4-debugging--verification)
- [5. Common Pitfalls](#5-common-pitfalls)
- [6. Quick Reference](#6-quick-reference)

---

## 1. System Architecture (The "Massa Anatomy")

The addon follows a strict **"Brain-Muscle-Engine"** separation pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                        MASSA CONSOLE                            │
├─────────────┬─────────────┬─────────────┬─────────────────────────┤
│   🧠 BRAIN   │   💪 MUSCLE  │   ⚙️ ENGINE  │      📦 CONTENT        │
│  Properties │  Base Op    │  Pipeline   │     Cartridges         │
│  & State    │  & Inherit  │  & Generate │     & Generators       │
└─────────────┴─────────────┴─────────────┴─────────────────────────┘
```

### 🧠 Brain

**Files:** `modules/massa_console.py`, `modules/massa_properties.py`

| Aspect | Description |
|--------|-------------|
| **Role** | Stores state and property definitions |
| **Key Concept** | `massa_properties.py` is the "DNA" — properties defined here propagate to the Console and ALL Cartridges automatically via `MassaPropertiesMixin` |

> ⚠️ **Safety Warning:** **NEVER** rename existing properties without a full repository refactor. This will break resurrection and saved presets.

### 💪 Muscle

**File:** `operators/massa_base.py`

| Aspect | Description |
|--------|-------------|
| **Role** | The Base Operator (`Massa_OT_Base`) that all cartridges inherit |
| **Responsibilities** | Handles execution, "Resurrection" (re-running parameter edits), and property syncing |

> ⚠️ **Safety Warning:** Modify `draw` or `execute` here **ONLY** if the change applies to EVERY cartridge.

### ⚙️ Engine

**File:** `modules/massa_engine.py`

| Aspect | Description |
|--------|-------------|
| **Role** | The generation pipeline (Pipeline) |
| **Pipeline Flow** | BMesh creation → Shape → Polish → Surface → Output |

> ⚠️ **Safety Warning:** This is the critical loop. Changes here affect the fundamental mesh generation logic for ALL cartridges.

### 📦 Content

**Directory:** `modules/cartridges/`

| Aspect | Description |
|--------|-------------|
| **Role** | Individual mesh generators (each cartridge = one generator) |
| **Required Methods** | Must implement `build_shape(self, bm)` and `get_slot_meta(self)` |
| **Registration** | Must be registered in `modules/cartridges/__init__.py` |

---

## 2. Modification Protocols

### A. Creating a New Cartridge

Follow this checklist when creating a new cartridge:

- [ ] **Step 1: Create File**
  
  Create `modules/cartridges/cart_my_new_thing.py`

- [ ] **Step 2: Inherit Base Class**
  
  ```python
  from ..operators.massa_base import Massa_OT_Base
  
  class MASSA_OT_MyNewThing(Massa_OT_Base):
      ...
  ```

- [ ] **Step 3: Define Metadata**
  
  ```python
  CARTRIDGE_META = {
      "name": "My New Thing",
      "version": "1.0",
      "id": "MASSA_OT_MyNewThing",
  }
  ```

- [ ] **Step 4: Implement Required Methods**
  
  ```python
  def build_shape(self, bm):
      """
      Build the mesh geometry using BMesh operations.
      
      Args:
          bm: BMesh instance to modify
          
      Returns:
          The modified BMesh
      """
      # Your geometry generation code here
      return bm
  
  def get_slot_meta(self):
      """Return metadata for this cartridge slot."""
      return CARTRIDGE_META
  ```

- [ ] **Step 5: Register the Cartridge**
  
  Open `modules/cartridges/__init__.py` and add:
  
  ```python
  # Import
  from . import cart_my_new_thing
  
  # Add to MODULES list
  MODULES = [
      # ... existing modules ...
      cart_my_new_thing,
  ]
  
  # Add class to CLASSES list
  CLASSES = [
      # ... existing classes ...
      cart_my_new_thing.MASSA_OT_MyNewThing,
  ]
  ```

### B. Modifying UI

| Aspect | Details |
|--------|---------|
| **Location** | `ui/ui_shared.py` contains the drawing logic for Tabs (Shape, Data, Polish, UVs) |
| **Panel File** | `ui/ui_massa_panel.py` contains the main panel definitions |

> ⚠️ **Rule:** Do **NOT** add UI code directly to `operators/massa_base.py`. Always delegate to `ui_shared.py`.

### C. Adding a Global Parameter

1. **Edit** `modules/massa_properties.py`:

   ```python
   my_new_param: BoolProperty(
       name="My New Parameter",
       description="What this parameter does",
       default=False,
   )
   ```

2. **Add UI** in `ui/ui_shared.py`:

   ```python
   layout.prop(props, "my_new_param")
   ```

3. **Implement Logic** in the appropriate module:
   - `modules/massa_engine.py` — if it affects mesh generation
   - `modules/massa_polish.py` — if it affects post-processing
   - `modules/massa_surface.py` — if it affects materials/UVs

---

## 3. Critical Safety Checks

### 🔄 Resurrection System

The system allows users to re-edit meshes after creation. Any new property **MUST** be handled properly:

| Component | File | Purpose |
|-----------|------|---------|
| Capture | `_capture_operator_params` in `massa_engine.py` | Saves current state |
| Restore | `Massa_OT_Base.invoke` in `operators/massa_base.py` | Restores saved state |

> 📝 **Note:** `_capture_operator_params` automatically captures RNA (Blender property system) properties. If you use non-RNA state (Python instance variables), you must manually handle serialization.

### 🖥️ Headless Safety

```python
# In operators/massa_base.py - DO NOT REMOVE
mat_utils.ensure_default_library()
```

> ⚠️ **Warning:** This call in `operators/massa_base.py` ensures material library exists before generation. Removing this will cause headless/automated tests to crash.

### 🔥 Hot Reload

The root `__init__.py` handles hot reloading for development.

> ⚠️ **Important:** If you add a **NEW module file** (e.g., `modules/massa_new_system.py`), you **MUST** add it to the reload logic in `__init__.py` to ensure it updates without restarting Blender.

---

## 4. Debugging & Verification

| Tool | Location | Purpose |
|------|----------|---------|
| **Gizmos** | `ui/gizmo_massa.py` | Viewport widgets for interactive editing |
| **Auditors** | `.agent/workflows/audit_cartridge.md` | Workflow for verifying cartridge integrity |
| **Debug System** | `modules/debugging_system/` | Bridge, runner, and auditor infrastructure |

### Running Audits

Use the audit workflow to verify cartridge integrity:

```
.agent/workflows/audit_cartridge
```

---

## 5. Common Pitfalls

### ❌ Don't Do This

| Mistake | Why It's Bad | What To Do Instead |
|---------|--------------|-------------------|
| Rename properties in `massa_properties.py` | Breaks resurrection & saved presets | Create new property, deprecate old one |
| Add UI code to `massa_base.py` | Violates separation of concerns | Use `ui_shared.py` |
| Forget to register new cartridge | Cartridge won't appear in menu | Add to both `MODULES` and `CLASSES` in `__init__.py` |
| Remove `ensure_default_library()` | Headless tests crash | Keep the call, it's required |
| Skip hot reload registration | Changes require Blender restart | Add module to `__init__.py` reload logic |
| Use non-RNA state without manual capture | Resurrection won't restore state | Either use RNA properties or manually handle in capture/restore |

### ✅ Best Practices

- Always test resurrection after adding new properties
- Run the audit workflow before committing cartridge changes
- Use descriptive names for properties (they appear in UI)
- Document cartridge-specific parameters in the class docstring

---

## 6. Quick Reference

### File Map

| File | Purpose |
|------|---------|
| `__init__.py` (root) | Addon entry point, hot reload logic |
| `modules/massa_console.py` | Console state management |
| `modules/massa_properties.py` | Property definitions (the "DNA") |
| `modules/massa_engine.py` | Generation pipeline |
| `modules/massa_polish.py` | Post-processing operations |
| `modules/massa_surface.py` | Material/UV handling |
| `operators/massa_base.py` | Base operator class |
| `ui/ui_shared.py` | Shared UI drawing functions |
| `ui/ui_massa_panel.py` | Panel definitions |
| `modules/cartridges/__init__.py` | Cartridge registration |

### Key Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `MassaPropertiesMixin` | `massa_properties.py` | Property inheritance mixin |
| `Massa_OT_Base` | `operators/massa_base.py` | Base operator for all cartridges |

### Required Cartridge Methods

```python
def build_shape(self, bm):
    """Build mesh geometry. Returns modified BMesh."""
    pass

def get_slot_meta(self):
    """Return cartridge metadata dict."""
    return CARTRIDGE_META

### Edge Slot Legend (Edge Role Interpreter)
| ID | Color | Role | Description |
|----|-------|------|-------------|
| **1** | Yellow | Perimeter | Outer boundary, Seam, Sharp |
| **2** | Blue | Contour | Major form break, Sharp |
| **3** | Red | Guide | Topological flow line, Seam |
| **4** | Green | Detail | Minor surface detail, Bevel |
| **5** | Purple | Fold | Cloth/Soft Crease, Subdivision Weighting |
```

---

## Related Documentation

- [README.md](README.md) — Project overview and installation
- [Audit Cartridge Workflow](.agent/workflows/audit_cartridge.md) — Verify cartridge integrity
- [Developer Protocol Workflow](.agent/workflows/MASSA_Developer_Protocol.workflow.md) — Extended developer guidelines
