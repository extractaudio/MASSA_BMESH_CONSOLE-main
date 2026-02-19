# MASSA CONSOLE ARCHITECTURE (v6.5)

> **"The Console is Law. The Cartridge is Art."**

This document defines the strict protocols for the **MASSA_BMESH_CONSOLE** system. It unifies the "Mandates" (Rules) with the "Architecture" (System) to ensure stability, resurrection, and clean geometry.

---

## 📑 Table of Contents

1.  [The Philosophy](#1-the-philosophy)
2.  [The Cartridge Blueprint (The 95% Standard)](#2-the-cartridge-blueprint-the-95-standard)
    *   [Class Structure](#a-class-structure)
    *   [The Golden Rules (Mandates)](#b-the-golden-rules-mandates)
    *   [Slot Protocol (Faces 0-9)](#c-slot-protocol-faces-0-9)
    *   [Edge Protocol (Edges 1-5)](#d-edge-protocol-edges-1-5)
    *   [UV Strategy](#e-uv-strategy)
3.  [System Architecture (The Anatomy)](#3-system-architecture-the-anatomy)
    *   [Brain (State)](#brain-state)
    *   [Muscle (Operator)](#muscle-operator)
    *   [Engine (Pipeline)](#engine-pipeline)
    *   [Shooter (Targeting)](#shooter-targeting)
    *   [Observer (Analytics)](#observer-analytics)
4.  [Modification Workflow](#4-modification-workflow)
    *   [Adding Parameters (The Rule of Five)](#adding-parameters-the-rule-of-five)
    *   [Resurrection System](#resurrection-system)
    *   [Headless Safety](#headless-safety)
5.  [Telemetry & Troubleshooting](#5-telemetry--troubleshooting)

---

## 1. The Philosophy

The Massa Console is a **Procedural Engine** that consumes **Cartridges** (Generators).
*   **The Console** handles the "Boring Stuff": UI, Undo/Redo, Material Assignment, UV Unwrapping, Physics Generation, Socket Constraints, Polish (Bevels/Chamfers), and File Management.
*   **The Cartridge** handles the "Fun Stuff": Pure BMesh geometry generation (`build_shape`).

**Goal:** A Cartridge should only focus on *shape*. If it follows the **Mandates**, the Console grants it superpowers (Auto-UVs, Physics, etc.) for free.

---

## 2. The Cartridge Blueprint (The 95% Standard)

To achieve "First-Time-Right" code generation, every Cartridge **MUST** follow this exact structure.

### A. Class Structure

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from ...operators.massa_base import Massa_OT_Base

# ---------------------------------------------------------
# 1. METADATA (Required)
# ---------------------------------------------------------
CARTRIDGE_META = {
    "name": "Cartridge Name",
    "id": "cart_unique_id",  # MUST match bl_idname suffix
    "version": "1.0",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD", # MICRO, STANDARD, MACRO
    "flags": {
        "USE_WELD": True,
        "ALLOW_SOLIDIFY": True, # Can this shape be hollowed?
        "FIX_DEGENERATE": True,
    },
}

class MASSA_OT_cart_unique_id(Massa_OT_Base):
    bl_idname = "massa.gen_cart_unique_id" # Prefix 'massa.gen_' is MANDATORY
    bl_label = "Cartridge Label"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # ---------------------------------------------------------
    # 2. PARAMETERS (Blender Properties)
    # ---------------------------------------------------------
    radius: bpy.props.FloatProperty(name="Radius", default=1.0, min=0.1, unit="LENGTH")
    segments: bpy.props.IntProperty(name="Segments", default=16, min=3)

    # ---------------------------------------------------------
    # 3. SLOT DEFINITIONS (The 'Hard 10')
    # ---------------------------------------------------------
    def get_slot_meta(self):
        """
        Defines the 10 Material Slots (0-9).
        Keys:
          - 'name': UI Label
          - 'phys': Physics Material (METAL_STEEL, PLASTIC, etc.)
          - 'uv': Unwrapping Strategy (BOX, UNWRAP, FIT, SKIP)
          - 'sock': (Optional) True if this slot generates sockets
        """
        return {
            0: {"name": "Base Hull",     "uv": "BOX",    "phys": "GENERIC"},
            1: {"name": "Detail Vent",   "uv": "BOX",    "phys": "MECHANICAL"},
            2: {"name": "Trim/Frame",    "uv": "STRIP",  "phys": "METAL_STEEL"},
            3: {"name": "Glass/Screen",  "uv": "FIT",    "phys": "GLASS"},
            # ... define up to 9
            9: {"name": "Socket Point",  "uv": "SKIP",   "sock": True},
        }

    # ---------------------------------------------------------
    # 4. DRAW UI (Sidebar)
    # ---------------------------------------------------------
    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "segments")

    # ---------------------------------------------------------
    # 5. EXECUTION CORE (The 'Fun Stuff')
    # ---------------------------------------------------------
    def build_shape(self, bm: bmesh.types.BMesh):
        """
        Generates geometry into the provided BMesh 'bm'.
        NO bpy.ops ALLOWED HERE. Use bmesh.ops only.
        """

        # [PHASE 1] Shape Generation
        # Example: Create Cylinder
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            radius1=self.radius,
            radius2=self.radius,
            depth=2.0,
            segments=self.segments
        )

        # [PHASE 2] Slot Assignment (Faces)
        # Mandate: All faces must have a material_index (0-9)
        for f in bm.faces:
            f.material_index = 0

        # [PHASE 3] Edge Roles (Features)
        # Mandate: Mark important edges for the Polish Stack
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1 # PERIMETER (Seam + Sharp)

        # [PHASE 4] Cleanup (Mandatory)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
```

### B. The Golden Rules (Mandates)

1.  **Pure BMesh**: Never use `bpy.ops` inside `build_shape`. It crashes in background mode. Use `bmesh.ops` or math.
2.  **No Loose Geometry**: Always run `remove_doubles` and `recalc_face_normals` at the end.
3.  **Inheritance**: Must inherit `Massa_OT_Base`.
4.  **Metadata**: Must provide valid `CARTRIDGE_META` and `get_slot_meta`.
5.  **Context Safe**: Do not assume `bpy.context.object` exists. Work only on `bm`.

### C. Slot Protocol (Faces 0-9)

**Usage:** `f.material_index = ID`

| ID | Role | Physics Default | Description |
| :--- | :--- | :--- | :--- |
| **0** | **BASE** | `GENERIC` | Main body, hull. |
| **1** | **DETAIL** | `MECHANICAL` | Vents, grilles, insets. |
| **2** | **TRIM** | `METAL_STEEL` | Frames, borders. |
| **3** | **GLASS** | `GLASS` | Windows, screens. |
| **4** | **EMISSION** | `EMISSIVE` | Lights, energy. |
| **5** | **DARK** | `RUBBER` | Inner shadows, tires. |
| **6** | **ACCENT** | `PAINT` | Decals, stripes. |
| **7** | **UTILITY** | `METAL_ROUGH` | Bolts, handles. |
| **8** | **TRANSPARENT** | `ENERGY` | Forcefields. |
| **9** | **SOCKET** | `NONE` | **Invisible**. Used for snapping points. |

### D. Edge Protocol (Edges 1-5)

**Usage:** `e[bm.edges.layers.int["MASSA_EDGE_SLOTS"]] = ID`

| ID | Name | Behavior |
| :--- | :--- | :--- |
| **1** | **PERIMETER** | **Seam + Sharp + Bevel**. The outer silhouette. |
| **2** | **CONTOUR** | **Sharp + Bevel**. Hard internal angles (90°). |
| **3** | **GUIDE** | **Seam Only**. Manual UV cut lines (for cylinders/organic). |
| **4** | **DETAIL** | **Bevel Only**. Small chamfers. No sharp shading. |
| **5** | **FOLD** | **Crease**. Subdivision weighting / Cloth pinning. |

### E. UV Strategy

Defined in `get_slot_meta()` under the `"uv"` key.

*   `"BOX"`: Tri-planar projection. Best for hard surface (Slots 0, 1, 2, 5, 7).
*   `"UNWRAP"`: LSCM Unwrap. **REQUIRES SEAMS** (Edge Slot 1 or 3). Best for organic/curved.
*   `"FIT"`: Stretches UVs to fill 0-1. Best for screens/glass (Slot 3, 4, 8).
*   `"SKIP"`: No UVs generated. (Use for Sockets).

---

## 3. System Architecture (The Anatomy)

### Brain (State)
*   **Files**: `modules/massa_console.py`, `modules/massa_properties.py`
*   **Role**: Stores persistent state.
*   **Key**: `MassaPropertiesMixin` defines properties that exist on BOTH the Scene (UI) and the Operator (History).

### Muscle (Operator)
*   **File**: `operators/massa_base.py` (`Massa_OT_Base`)
*   **Role**: The execution shell. Handles:
    1.  **Sync**: Copies props from Scene to Operator.
    2.  **Resurrection**: Restores props from `obj["MASSA_PARAMS"]`.
    3.  **UI**: Draws the Redo Panel.

### Engine (Pipeline)
*   **File**: `modules/massa_engine.py`
*   **Role**: The heavy lifter.
    1.  **Phase 1**: `build_shape(bm)` (The Cartridge).
    2.  **Phase 2**: `auto_detect_edge_slots` (If not manually set).
    3.  **Phase 3**: `auto_detect_sharp_edges` (Additive).
    4.  **Phase 4**: Polish Stack (Bevel, Fuse, Solidify).
    5.  **Phase 5**: Output (Mesh conversion, Material Assignment, Physics, Sockets).

### Shooter (Targeting)
*   **File**: `operators/massa_shooter.py`
*   **Role**: "Point & Shoot" mode.
    *   Uses `Massa_Target` empty if available.
    *   Injects location/rotation into the Operator history.

### Observer (Analytics)
*   **File**: `modules/advanced_analytics.py`
*   **Role**: Visual debugging (`debug_view`) and telemetry.

---

## 4. Modification Workflow

### Adding Parameters (The Rule of Five)
To add a new global parameter (e.g., `global_scale`), you must touch 5 places:
1.  **Definition**: `MassaPropertiesMixin` in `massa_properties.py`.
2.  **Scene**: Registered in `massa_console.py`.
3.  **Operator**: Inherited in `Massa_OT_Base`.
4.  **Sync**: Added to `_sync()` method in `massa_base.py`.
5.  **UI**: Added to `ui/ui_shared.py`.

### Resurrection System
*   **How it works**: When `execute()` runs, `_capture_operator_params` saves all settings to `obj["MASSA_PARAMS"]`.
*   **How it restores**: When `invoke()` runs, it checks if the active object has `MASSA_PARAMS`. If so, it loads them into the operator, effectively "resurrecting" the previous state.
*   **Rule**: NEVER rename properties without a migration script, or old objects will lose their settings.

### Headless Safety
*   **Rule**: The Engine often runs in background threads or unit tests where `bpy.context.view_layer` or `bpy.ops` might fail.
*   **Fix**: Use `mat_utils.ensure_default_library()` to load materials without context. Use `bmesh` for all geometry.

---

## 5. Telemetry & Troubleshooting

| Flag | Meaning | Fix |
| :--- | :--- | :--- |
| `CRITICAL_FLAT_Z_AXIS` | Geometry has 0 height. | Check `bmesh.ops.scale` or extrusion logic. |
| `LOOSE_VERTS` | Vertices not connected to edges. | Run `bmesh.ops.delete(bm, geom=loose, context="VERTS")`. |
| `NON_MANIFOLD` | Mesh has holes or T-junctions. | Run `bmesh.ops.recalc_face_normals` or check bridge logic. |
| `MISSING_SLOTS` | Face ID > 9 or < 0. | Ensure `f.material_index` is clamped 0-9. |
| `NO_SEAMS` | "UNWRAP" mode used but no seams found. | Mark edges with `e[edge_slots]=1` (Perimeter) or `3` (Guide). |

---

> **Massa Console Architect v6.5**
> *End of File*
