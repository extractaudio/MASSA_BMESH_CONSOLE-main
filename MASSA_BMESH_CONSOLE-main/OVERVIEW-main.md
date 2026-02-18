# MASSA Console Developer Protocol

> This workflow defines the strict protocols for understanding and modifying the `MASSA_BMESH_CONSOLE-main` addon.

---

## 📑 Table of Contents

- [1. System Architecture](#1-system-architecture-the-massa-anatomy)
  - [Brain](#-brain)
  - [Muscle](#-muscle)
  - [Engine](#-engine)
  - [Content](#-content)
  - [Shooter](#-shooter)
  - [Observer](#-observer)
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

The addon follows a strict separation pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MASSA CONSOLE                                 │
├────────────┬────────────┬────────────┬────────────┬───────────┬─────────┤
│  🧠 BRAIN   │  💪 MUSCLE │  ⚙️ ENGINE │ 📦 CONTENT │ 🔫 SHOOTER│ 👁️ OBSERVER │
│ State &    │ Operator   │ Pipeline   │ Cartridges │ Target &  │ Analytics│
│ Properties │ & Sync     │ & Generate │ & Logic    │ Dispatch  │ & Vision │
└────────────┴────────────┴────────────┴────────────┴───────────┴──────────┘
```

### 🧠 Brain

**Files:** `modules/massa_console.py`, `modules/massa_properties.py`, `modules/massa_cartridge_props.py`

| Aspect | Description |
|--------|-------------|
| **Role** | Stores persistent state and property definitions. |
| **Key Concept** | `massa_properties.py` is the "DNA" — properties defined here propagate to the Console and ALL Cartridges automatically via `MassaPropertiesMixin`. `massa_cartridge_props.py` handles dynamic property group generation for cartridges. |

> ⚠️ **Safety Warning:** **NEVER** rename existing properties without a full repository refactor. This will break resurrection and saved presets.

### 💪 Muscle

**File:** `operators/massa_base.py`

| Aspect | Description |
|--------|-------------|
| **Role** | The Base Operator (`Massa_OT_Base`) that all cartridges inherit. |
| **Responsibilities** | Handles execution, "Resurrection" (re-running parameter edits), property syncing (`_sync`), and UI Tabs (SHAPE, DATA, POLISH, UVS, SLOTS, EDGES). |
| **Resurrection** | Uses `rerun_mode` and captures parameters in `MASSA_PARAMS` on the object to restore state during edits. |

> ⚠️ **Safety Warning:** Modify `draw` or `execute` here **ONLY** if the change applies to EVERY cartridge.

### ⚙️ Engine

**File:** `modules/massa_engine.py`

| Aspect | Description |
|--------|-------------|
| **Role** | The generation pipeline (Pipeline). |
| **Pipeline Flow** | BMesh creation → Shape → Polish → Surface → Physics (Phase 4) → Output. |
| **Key Features** | Handles 5 Edge Slots, Data Layers (Strain/Kinematic), and Physics generation (UCX/Joints). |

> ⚠️ **Safety Warning:** This is the critical loop. Changes here affect the fundamental mesh generation logic for ALL cartridges.

### 📦 Content

**Directory:** `modules/cartridges/`

| Aspect | Description |
|--------|-------------|
| **Role** | Individual mesh generators (each cartridge = one generator). |
| **Required Methods** | Must implement `build_shape(self, bm)` and `get_slot_meta(self)`. |

### 🔫 Shooter (Point & Shoot)

**File:** `operators/massa_shooter.py`

| Aspect | Description |
|--------|-------------|
| **Role** | Handles targeted generation without changing selection. |
| **Mechanism** | Uses `MASSA_OT_ShootDispatcher` to stage a cartridge, target a coordinate (or `Massa_Target` empty), and inject parameters dynamically. |

### 👁️ Observer (Advanced Analytics)

**File:** `modules/advanced_analytics.py`

| Aspect | Description |
|--------|-------------|
| **Role** | The "eyes" of the system. Handles synthetic vision and analysis. |
| **Components** | **Holo-Projector** (`MCP_Overlay`): 3D viewport drawing.<br>**Visual Cortex** (`capture_analytical`): Segmentation, Depth, Heatmaps.<br>**Deep Analyst**: Mesh auditing and dependency tracing.<br>**Ghost Sim**: Simulating modifier stacks. |

---

## 2. Modification Protocols

### A. Creating a New Cartridge

Follow this checklist when creating a new cartridge:

- [ ] **Step 1: Create File** (`modules/cartridges/cart_my_new_thing.py`)
- [ ] **Step 2: Inherit Base Class** (`Massa_OT_Base`)
- [ ] **Step 3: Define Metadata**
  ```python
  CARTRIDGE_META = {
      "name": "My New Thing",
      "version": "1.0",
      "id": "MASSA_OT_MyNewThing", # Must match class name or be unique
      "flags": {"ALLOW_SOLIDIFY": True, "USE_WELD": True}
  }
  ```
- [ ] **Step 4: Implement Required Methods**
  - `build_shape(self, bm)`: Use `bmesh.ops`. NO `bpy.ops`.
  - `get_slot_meta(self)`: Return dict of 10 slots (0-9) with `phys` keys (e.g., `METAL_STEEL`).
- [ ] **Step 5: Register the Cartridge** in `modules/cartridges/__init__.py`.

### B. Modifying UI

| Aspect | Details |
|--------|---------|
| **Location** | `ui/ui_shared.py` contains shared drawing logic. |
| **Panel File** | `ui/ui_massa_panel.py` defines the main panel and sub-panels. |

> ⚠️ **Rule:** Do **NOT** add UI code directly to `operators/massa_base.py`. Always delegate to `ui_shared.py`.

### C. Adding a Global Parameter

1. **Edit** `modules/massa_properties.py`.
2. **Add UI** in `ui/ui_shared.py`.
3. **Implement Logic** in `massa_engine.py`, `massa_polish.py`, or `massa_surface.py`.

---

## 3. Critical Safety Checks

### 🔄 Resurrection System

The system allows users to re-edit meshes.
- **Capture**: `_capture_operator_params` in `massa_engine.py` saves RNA properties to `obj["MASSA_PARAMS"]`.
- **Restore**: `Massa_OT_Base.invoke` checks `rerun_mode` or `MASSA_PARAMS` and restores state.
- **Transforms**: Object location/rotation are preserved during resurrection.

### 🖥️ Headless Safety

- Always keep `mat_utils.ensure_default_library()` in `massa_base.py`.
- Ensure physics generation (`phys_gen_ucx`) handles missing context gracefully.

---

## 4. Debugging & Verification

| Tool | Location | Purpose |
|------|----------|---------|
| **Gizmos** | `ui/gizmo_massa.py` | Viewport widgets. |
| **Holo-Projector** | `modules/advanced_analytics.py` | Visual debug overlays (Points/Lines/Text). |
| **Synthetic Vision** | `capture_analytical` | Render depth/segmentation passes for analysis. |
| **Auditors** | `.agent/workflows/audit_cartridge.md` | Verification workflow. |

---

## 5. Common Pitfalls

| Mistake | Why It's Bad | What To Do Instead |
|---------|--------------|-------------------|
| Rename properties | Breaks resurrection | Deprecate old, create new. |
| `bpy.ops` in `build_shape` | Crashing/Context errors | Use `bmesh.ops`. |
| Forget `mat_utils.ensure_default_library()` | Headless crash | Keep it. |
| Ignore 5 Edge Slots | Visualization errors | Assign slots 1-5 correctly. |

---

## 6. Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `massa_console.py` | Brain (State) |
| `massa_engine.py` | Engine (Pipeline) |
| `massa_base.py` | Muscle (Operator) |
| `massa_shooter.py` | Shooter (Targeting) |
| `advanced_analytics.py` | Observer (Vision) |

### Key Classes

- `MassaPropertiesMixin`: Property inheritance.
- `Massa_OT_Base`: Base operator.
- `MCP_Overlay`: Visual debugger.

---

## 🎯 The Prime Directives (Constitution)

### 1. The Split-State Architecture
**Brain** (Persistent) vs **Muscle** (Transient). Never modify Scene data directly from Operator execute without sync.

### 2. The Rule of Five (Parameter Protocol)
New params must exist in:
1. `bpy.types.Scene` (Brain)
2. `bpy.types.Operator` (Muscle)
3. `_sync()` list (Bridge)
4. `ui_massa_panel.py` (Sidebar UI)
5. `Massa_OT_Base.draw` (Redo UI)

### 3. The All-Cartridges Mandate
- **Segmentation**: Subdivide long faces.
- **Edge Roles**: Assign `MASSA_EDGE_SLOTS` (1-5).
- **Identity**: Valid `get_slot_meta`.
- **Output**: Manifold, no loose verts.

---

## 🏗️ Execution Pipeline (Phases 1-6)

### Phase 1-3: Architecture & Build
Define DNA, inherit `Massa_OT_Base`, implement `build_shape` using `bmesh.ops`.

### Phase 4: The Artisan (Physics & Slots)
- **10 Slots**: 0-9.
- **Physics**: Use valid keys (e.g., `METAL_STEEL`).
- **Edge Roles**:
  - **1**: Perimeter (Seam/Sharp)
  - **2**: Contour (Sharp)
  - **3**: Guide (Seam)
  - **4**: Detail (Bevel)
  - **5**: Special (Custom)
- **Physics Gen**: `phys_gen_ucx` creates collision hulls; `phys_auto_rig` creates joints for detached parts.

### Phase 5-6: Audit & Medic
Verify with Telemetry. Fix flags.

---

## 📊 Telemetry Flags Reference

### 🔴 Critical (System Failure)
- `IMPORT_ERROR`, `SYNTAX_ERROR`
- `CRITICAL_FLAT_Z_AXIS`: Zero height.
- `CRITICAL_NO_PERIMETER_DEFINED`: Missing Edge Slot 1.

### 🟡 High (UI/Interface)
- `CRITICAL_UI_NO_UNDO_FLAG`: Missing `bl_options`.
- `CRITICAL_EMPTY_PANEL_NO_PROPS`: No props.

### 🟠 Medium (Geometry)
- `LOOSE_VERTS`, `NON_MANIFOLD`.

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

### Edge Role Interpreter (5 Slots)

```python
edge_slots = bm.edges.layers.int["MASSA_EDGE_SLOTS"]
# 1: Perimeter, 2: Contour, 3: Guide, 4: Detail, 5: Special
```

---

## 🚀 Related Documentation

- [README.md](README.md) — Project overview.
- [Audit Cartridge Workflow](.agent/workflows/audit_cartridge.md) — Verification.
- [Massa Genesis Codex](Massa_Genesis_Codex.md) — DNA definitions.

---

## 🎯 Success Criteria

- ✅ Passes telemetry (no flags).
- ✅ Resurrects correctly (params & transforms).
- ✅ Edge slots (1-5) assigned.
- ✅ Material slots (0-9) populated.
- ✅ Physics hulls (UCX) and Joints generate correctly.
