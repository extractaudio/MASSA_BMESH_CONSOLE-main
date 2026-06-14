# Console System Directive

---

## Table of Contents

1. [Core Architecture: The "Split-State" Model](#core-architecture-the-split-state-model)
2. [Parameter Integration: The "Rule of Five"](#parameter-integration-the-rule-of-five)
3. [Cartridge Compliance: The 6 Laws](#cartridge-compliance-the-6-laws)
4. [Specialized Sub-Systems & Operations](#specialized-sub-systems--operations)
5. [Elite Automation & Code Structural Integrity](#elite-automation--code-structural-integrity)
6. [Failure State Management (The Bridge)](#failure-state-management-the-bridge)
7. [Sub-System Integration & Hardcoded Strings](#sub-system-integration--hardcoded-strings)

---

## Core Architecture: The "Split-State" Model

To successfully support Blender's Redo Panel (F9) without losing persistent settings, the system relies on a strictly separated dual-state data model.

### Components

| Component | Location | Description |
|-----------|----------|-------------|
| **The Brain** | `massa_console.py` | Persistent storage residing on `bpy.types.Scene`. Survives restarts and powers the Sidebar interface. |
| **The Muscle** | `massa_base.py` | Transient executor residing on `bpy.types.Operator`. Utilized directly by the Redo Panel. |
| **The Bridge** | `_sync()` | Critical point of failure where values are manually copied from The Brain to The Muscle. |

---

## Parameter Integration: The "Rule of Five"

To prevent the creation of "Ghost Controls," any new parameter addition must be instantiated across five specific locations:

1. Define the property within **The Brain**.
2. Define a matching property within **The Muscle**.
3. Register the property key within **The Bridge's** synchronization list.
4. Draw the control in the Sidebar UI (**The Face**).
5. Draw the control in the Redo UI.

---

## Cartridge Compliance: The 6 Laws

All `cart_*.py` files are treated as Clients of the Console and must adhere to the following strict mandates:

### Law of Segmentation
> Long faces must be subdivided to ensure the Polish Stack (Twist, Taper, Bend) deforms the mesh without breaking.

### Law of Edge Roles
> Edges must be assigned to the `MASSA_EDGE_SLOTS` layer using the 4-Slot system:
> - Perimeter
> - Contour
> - Guide
> - Detail

### Law of Identity
> Cartridges must return a dictionary of used slots via `get_slot_meta()` to drive Socket manifestations.

### Law of Defaults
> `CARTRIDGE_META` must explicitly define `scale_class` and specific structural flags to prevent the Console from applying destructive logic.

### Law of Surface
> Generated geometry must maintain valid normals for mapping and remain watertight for BVHTree calculations.

### Law of Output
> There is zero tolerance for loose vertices or zero-area faces to prevent downstream Boolean failures.

---

## Specialized Sub-Systems & Operations

The console...

### Strict Phase Containment
> Never bleed logic between execution phases. Cartridge logic (Phase A) must only generate base BMesh topology. It must never attempt to apply modifiers, smooth shading, or solidifications, as these are strictly reserved for Phase D (Polish) and Phase H (Output).

### Immutability of Pre-Calculated Data
> Once Phase E (Intelligence) calculates Seam Maps or Surface Data, subsequent phases must read this data as immutable. Do not write destructive mesh operations after Phase E.

---

## Elite Automation & Code Structural Integrity

### API Rigidity
> Operate strictly within the established bounds of Blender 5.0's `bmesh` and `bpy` modules. Do not hallucinate speculative BMesh methods. Prioritize robust, fail-safe Python backend logic over theoretical or research-oriented architectural discussions.

### Data Type Strictness
> When defining properties for The Brain or Muscle, enforce explicit and correct Blender property typing (e.g., `bpy.props.FloatProperty`, `IntProperty`, `BoolProperty`) with comprehensively defined `default`, `min`, and `max` kwargs to prevent user-input crashes.

---

## Failure State Management (The Bridge)

### Sync Auditing
> Treat the `_sync()` method in `massa_base.py` as the primary suspect during data-loss debugging. If a UI element updates but the generated mesh does not, immediately audit the `keys` list in the Bridge.

### Failsafe Defaults
> Ensure all parameters have sensible fallbacks in `_inject_smart_defaults` so the engine does not critically fault if a Cartridge omits a `CARTRIDGE_META` flag.

---

## Sub-System Integration & Hardcoded Strings

### Node Bridge Strictness
> Never alter the hardcoded string inputs for the "Massa_SDF_Fuse" modifier (e.g., "Resolution") within the Python execution unless explicitly instructed to refactor the Geometry Nodes tree concurrently.

### Data Layer Naming
> Enforce exact string matching for vertex color layers (`Wear`, `Thick`, `Grav`) and the "UVMap" rename to maintain the integrity of `mat_utils.py`.

---

## Quick Reference: File Locations

| Component | File Path |
|-----------|----------|
| Console Brain | [`massa_console.py`](massa/modules/massa_console.py) |
| Console Muscle | [`massa_base.py`](massa/operators/massa_base.py) |
| Sync Bridge | `_sync()` in `massa_base.py` |
| Material Utils | [`mat_utils.py`](massa/utils/mat_utils.py) |

---

*Document generated from `Console_System_Directive.md`*
