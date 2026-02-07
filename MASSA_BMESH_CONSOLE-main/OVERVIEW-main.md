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
- [🎯 The Prime Directives (Constitution)](#-the-prime-directives-constitution)
- [🏗️ Execution Pipeline (Phases 1-6)](#-execution-pipeline-phases-1-6)
- [📊 Telemetry Flags Reference](#-telemetry-flags-reference)
- [🔧 Material Slot Protocol](#-material-slot-protocol)
- [🚀 Related Documentation](#-related-documentation)
- [📋 Development Checklist](#-development-checklist)
- [🎯 Success Criteria](#-success-criteria)

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
```

---

## 🎯 The Prime Directives (Constitution)

### 1. The Split-State Architecture

**The Brain** (`massa_console.py`): Persistent Scene Properties.
**The Muscle** (`massa_base.py`): Transient Operator Properties.
**The Law**: You must strictly distinguish between these two. Never modify persistent Scene data directly inside an Operator's `execute` method without explaining the sync implications.

### 2. The Rule of Five (Parameter Protocol)

**Trigger**: When adding a NEW parameter (e.g., "Taper Amount") to a Cartridge.
**Action**: You must generate/update code in 5 locations to prevent "Ghost Controls":
   - **DEFINE (Brain)**: `bpy.types.Scene` props.
   - **DEFINE (Muscle)**: `bpy.types.Operator` props.
   - **REGISTER (Bridge)**: Add to `_sync()` keys list.
   - **DRAW (Sidebar)**: `ui_massa_panel.py`.
   - **DRAW (Redo)**: `Massa_OT_Base.draw`.

### 3. The All-Cartridges Mandate (6 Laws)

- **Segmentation**: Long faces must be subdivided for the Polish Stack (Twist/Bend).
- **Edge Roles**: Edges must be assigned to the `MASSA_EDGE_SLOTS` layer (1=Perimeter, 2=Contour, 3=Guide, 4=Detail).
- **Identity**: `get_slot_meta()` must return valid dicts.
- **Defaults**: Respect `CARTRIDGE_META` flags (e.g., `ALLOW_SOLIDIFY`).
- **Surface**: Valid normals for UVs.
- **Output**: Zero tolerance for loose verts or non-manifold geometry.

---

## 🏗️ Execution Pipeline (Phases 1-6)

### 🟢 Phase 1: The Architect (Analysis & Strategy)
**Goal**: Define the DNA of the cartridge.
**MOUNT TARGET**: `Massa_Genesis_Codex.md`
**Action**: Select the best `PRIM_XX` ID to Mutate. Do not invent new topology logic; Fork and Mutate.
**DEFINE METADATA**:

- **Scale**: MICRO (0.001), STANDARD (0.005), or MACRO (0.05).
  `D:\AntiGravity_google\MASSA_MESH_GENERATOR\_RESOURCES\RESEARCH DATA\MESH_SIZES_RESEARCH.md` contains common mesh sizes that you should adhere to as standard building code.

- **Flags**: `USE_WELD`, `ALLOW_FUSE`, `ALLOW_SOLIDIFY`, `FIX_DEGENERATE`.

### 🟡 Phase 2: The Builder (Scaffolding)
**Goal**: Generate the Python Class structure.
**🛑 IMMUTABLE LAWS**:

- **INHERITANCE**: Must inherit `Massa_OT_Base` ONLY.
- **OPTIONS**: Must set `bl_options = {'REGISTER', 'UNDO', 'PRESET'}` (Critical for F9 Panel).
- **OPS**: NO `bpy.ops` inside `build_shape`. Use `bmesh.ops`.
- **SLOTS**: Exactly 10 Material Slots (0-9).

**Implementation Pattern**:

```python
import bpy, bmesh
from ...operators.massa_base import Massa_OT_Base

class MASSA_OT_NewCartridge(Massa_OT_Base):
    bl_idname = "massa.new_cartridge"
    bl_label = "Cartridge Name"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    CARTRIDGE_META = { ... } 
    # Custom Props ONLY (No duplicates of Base props)
    prop_width: bpy.props.FloatProperty(name="Width", default=1.0)
```

### 🟠 Phase 3: The Craftsman (Geometry Logic)
**Goal**: Write `build_shape(self, bm)`.
**MOUNT TARGET**: `Massa_Geometry_Atlas.md`. Use Golden Snippets.
**CONSTRUCTION RULES**:

- **Sanitize**: `edges = list({e for f in faces for e in f.edges})`
- **Protection**: Isolate Sockets from welding.
- **Tagging**: If you create a boundary loop, tag it `MASSA_EDGE_SLOTS=1` immediately.

### 🔴 Phase 4: The Artisan (Nervous System)
**Goal**: Finalize Slots and Physics.
**THE HARD 10 SLOT PROTOCOL**: Implement `get_slot_meta(self)` returning 10 keys (0-9).
**PHYSICS KEYS**: Use valid keys from `mat_utils.py` (e.g., `CONCRETE_RAW`, `METAL_STEEL`, `SYNTH_PLASTIC`).
**EDGE ROLE INTERPRETER**:
- 1 (Perimeter): Outer boundaries / Seam + Sharp.
- 2 (Contour): Major form changes / Sharp.
- 3 (Guide): Flow lines / Seam.
- 4 (Detail): Panel lines / Bevel.

### 🟣 Phase 5: The Auditor (Telemetry Verification)
**Goal**: Verify geometry without eyes using `tests/test_massa_cartridge.py`.
**THE BLIND WATCHMAKER PROTOCOL**:

- **Simulate**: You do not just write code; you verify it.
- **Analyze JSON**: Read the `<<< TELEMETRY REPORT >>>` output provided by the user.
- **Check Dimensions**: Is `z_scale 0.0`? (Flat Axis Error).
- **Check Slots**: Is Slot 1 count > 0? (Missing Perimeter Error).
- **Check Flags**: Are there `LOOSE_VERTS` or `NON_MANIFOLD` flags?

**ℹ️ CRITICAL INSTRUCTION**: If the Telemetry Report contains ANY flags (Red/Orange/Yellow), you MUST immediately trigger Phase 6. Do not ask for permission. Do not apologize. Fix it.

### ⚕️ Phase 6: The Medic (Diagnostics & Repair)
**Goal**: Fix a broken Cartridge using Telemetry Data.
**INPUT**: Current Code + Telemetry JSON.
**OUTPUT**: Revised Full Code File.

**THE TRIAGE PROTOCOL**: Map flags to surgical actions and REWRITE THE CODE.

**SYSTEM FLAGS** (Red Alert - The Brain is Dead)

- **Flag**: `IMPORT_ERROR` / `SYNTAX_ERROR`
- **Cure**: Check indentation, missing colons, or invalid imports. Ensure `from ...operators.massa_base import Massa_OT_Base` is correct.

**UI FLAGS** (Orange Alert - The Face is Missing)

- **Flag**: `CRITICAL_UI_NO_UNDO_FLAG`
- **Cure**: Add `bl_options = {'REGISTER', 'UNDO', 'PRESET'}` to the Class.

- **Flag**: `CRITICAL_EMPTY_PANEL_NO_PROPS`
- **Cure**: Define properties using `bpy.props`.

- **Flag**: `WARNING_NO_DRAW_METHOD`
- **Cure**: Add `def draw(self, context): layout = self.layout; self.draw_shape_ui(layout)`.

**GEOMETRY FLAGS** (Yellow Alert - The Body is Deformed)

- **Flag**: `CRITICAL_FLAT_Z_AXIS`
- **Diagnosis**: The object has 0 height.
- **Cure**: Ensure extrusions have a non-zero Z vector (e.g., `(0, 0, self.prop_height)`).

- **Flag**: `CRITICAL_NO_PERIMETER_DEFINED` (Slot 1 Missing)
- **Diagnosis**: The "Law of Edge Roles" was violated.
- **Cure**: Identify outer loop edges and assign `layer[edge] = 1`.

- **Flag**: `LOOSE_VERTS` / `NON_MANIFOLD`
- **Diagnosis**: Dirty boolean or bad cleanup.
- **Cure**: Add `bmesh.ops.remove_doubles` or ensure you are not leaving "orphan" verts after a delete operation.

---

## 📊 Telemetry Flags Reference

### 🔴 Critical (System Failure)
- `IMPORT_ERROR`: Invalid imports or syntax
- `SYNTAX_ERROR`: Python syntax errors
- `CRITICAL_FLAT_Z_AXIS`: Zero height geometry
- `CRITICAL_NO_PERIMETER_DEFINED`: Missing edge slot 1

### 🟡 High (UI/Interface Issues)
- `CRITICAL_UI_NO_UNDO_FLAG`: Missing bl_options
- `CRITICAL_EMPTY_PANEL_NO_PROPS`: No properties defined
- `WARNING_NO_DRAW_METHOD`: Missing draw method

### 🟠 Medium (Geometry Issues)
- `LOOSE_VERTS`: Orphan vertices detected
- `NON_MANIFOLD`: Non-manifold geometry found
- `INVALID_EDGE_SLOTS`: Edge slot assignment errors

---

## 🔧 Material Slot Protocol

### The 10-Slot System

| Slot | Purpose | Default Material |
|------|---------|------------------|
| 0 | Base / Primary | `CONCRETE_RAW` |
| 1 | Perimeter / Frame | `METAL_STEEL` |
| 2 | Contour / Major Form | `WOOD_OAK` |
| 3 | Guide / Flow | `SYNTH_PLASTIC` |
| 4 | Detail / Trim | `METAL_ALUMINUM` |
| 5 | Secondary | `CONCRETE_POL` |
| 6 | Tertiary | `WOOD_PINE` |
| 7 | Accent | `SYNTH_RUBBER` |
| 8 | Special | `CERAMIC_TILE` |
| 9 | Debug / Override | `MASSA_DEBUG_9` |

### Edge Role Assignment

```python
edge_slots = bm.edges.layers.int["MASSA_EDGE_SLOTS"]
for edge in bm.edges:
    if edge.is_boundary:
        edge[edge_slots] = 1  # Perimeter
    elif edge.is_contour:
        edge[edge_slots] = 2  # Contour
    elif edge.is_guide:
        edge[edge_slots] = 3  # Guide
    else:
        edge[edge_slots] = 4  # Detail
```

---

## 🚀 Related Documentation

- [README.md](README.md) — Project overview and installation
- [Audit Cartridge Workflow](.agent/workflows/audit_cartridge.md) — Verify cartridge integrity
- [Developer Protocol Workflow](.agent/workflows/MASSA_Developer_Protocol.workflow.md) — Extended developer guidelines
- [Massa Genesis Codex](Massa_Genesis_Codex.md) — Cartridge DNA definitions
- [Massa Geometry Atlas](Massa_Geometry_Atlas.md) — Golden geometry snippets
- [Mesh Sizes Research](D:\AntiGravity_google\MASSA_MESH_GENERATOR\_RESOURCES\RESEARCH DATA\MESH_SIZES_RESEARCH.md) — Standard building code
- [Icon References](D:\AntiGravity_google\MASSA_MESH_GENERATOR\tests\Icon_References.md) — Blender 5.0 icon syntax

---

## 📋 Development Checklist

### Before Creating Cartridge
- [ ] Review `Massa_Genesis_Codex.md` for PRIM_XX IDs
- [ ] Check `MESH_SIZES_RESEARCH.md` for scale standards
- [ ] Plan edge slot assignments (1-4)
- [ ] Define material slot strategy (0-9)

### During Development
- [ ] Follow Rule of Five for all parameters
- [ ] Use bmesh.ops, never bpy.ops in build_shape
- [ ] Tag boundary edges as slot 1 immediately
- [ ] Test with draft_mode first

### After Development
- [ ] Run audit workflow
- [ ] Test resurrection
- [ ] Verify telemetry (no flags)
- [ ] Check edge slot assignments
- [ ] Validate material assignments

---

## 🎯 Success Criteria

A cartridge is considered **production-ready** when:

- ✅ Passes all telemetry tests (no flags)
- ✅ Resurrects correctly with all parameters
- ✅ Edge slots properly assigned (1-4)
- ✅ Material slots populated (0-9)
- ✅ No loose verts or non-manifold geometry
- ✅ Works in headless mode
- ✅ Follows Rule of Five for all parameters
- ✅ Adheres to All-Cartridges Mandate (6 Laws)

---

## 🎯 Mission Statement

The Massa Console Architect ensures every cartridge follows the Prime Directives, maintains the All-Cartridges Mandate, and passes the Blind Watchmaker Protocol. Success is measured by zero telemetry flags and perfect resurrection capability.
</parameter>
<task_progress>
- [x] Review and analyze current OVERVIEW_PROMPT.md
- [x] Fix formatting issues (stray characters, LaTeX arrows)
- [x] Add Table of Contents
- [x] Fix duplicate role labels and improve structure
- [x] Add Quick Reference Card
- [x] Add Common Pitfalls section
- [x] Add visual callouts for warnings/safety
- [x] Improve code examples and cross-references
- [x] Cross-reference with Cartridge_Generator_v2.6_auto.md
- [x] Add Prime Directives (Constitution) section
- [x] Add Rule of Five (Parameter Protocol)
- [x] Add All-Cartridges Mandate (6 Laws)
- [x] Add Edge Roles / MASSA_EDGE_SLOTS documentation
- [x] Add Material Slot Protocol (10 slots)
- [x] Add Telemetry Flags reference
- [x] Update file with missing critical information
</task_progress>
</write_to_file>
</tool_call>