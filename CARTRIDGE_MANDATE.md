# MASSA CARTRIDGE MANDATE

> **The "Golden Standard" for Procedural Geometry Cartridges**

This document defines the strict requirements for creating a "Golden Cartridge" in the Massa system. All new geometry scripts must adhere to these protocols to ensure consistency, stability, and high-quality output.

---

## 1. Overview & Philosophy

A **Golden Cartridge** is a self-contained, parametric geometry generator. It is not just a mesh script; it is a "smart object" definition that includes:
*   **Metadata**: Identity, scale, and capability flags.
*   **Topology**: Clean, quad-dominant geometry with thoughtful edge flow.
*   **Data Layers**: Precise slot assignments (Materials), Edge Roles (Sharp/Seam/Guide), and Physics IDs.
*   **UVs**: **Manual, high-quality unwrapping** is the primary mandate. Auto-unwrapping is a fallback, not a standard.
*   **Sockets**: Explicit attachment points for the Massa ecosystem.

---

## 2. File Structure

### 2.1 Imports
Standard imports must include Blender types, BMesh, Mathutils, and the Base Operator.

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
```

### 2.2 Metadata (`CARTRIDGE_META`)
Every cartridge **must** define a `CARTRIDGE_META` dictionary at the module level.

*   **`name`**: Human-readable name (e.g., "PRIM_01: Structural Beam").
*   **`id`**: Unique internal ID (e.g., "prim_01_beam").
*   **`icon`**: Blender icon ID (e.g., "MOD_SOLIDIFY").
*   **`scale_class`**: usually "STANDARD", "MICRO", or "MACRO".
*   **`flags`**:
    *   `ALLOW_SOLIDIFY` (bool): Can the engine add thickness?
    *   `USE_WELD` (bool): Should vertices be merged?
    *   `ALLOW_CHAMFER` (bool): Is the geometry suitable for beveling?
    *   `LOCK_PIVOT` (bool): If True, keeps origin at generation start point.

**Example:**
```python
CARTRIDGE_META = {
    "name": "PRIM_01: Structural Beam",
    "id": "prim_01_beam",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}
```

### 2.3 Class Definition
The operator class **must** inherit from `Massa_OT_Base`.
*   **`bl_idname`**: Must follow `massa.gen_<id>`.
*   **`bl_label`**: Short name for the operator search.
*   **`bl_options`**: `{"REGISTER", "UNDO", "PRESET"}`.

---

## 3. Slot & Material Protocol

Golden Cartridges utilize a fixed 10-slot system (Indices 0-9).
Define this in the `get_slot_meta(self)` method.

### 3.1 `get_slot_meta` Return Dict
Returns a dictionary where keys are Slot Indices (int 0-9) and values are dicts with:
*   **`name`**: Description of the part (e.g., "Surface", "Caps").
*   **`uv`**: UV Strategy.
    *   `"SKIP"`: **MANDATORY for Golden Cartridges.** Signals that the script handles UVs manually.
    *   `"BOX"`: Fallback for simple/flat parts (e.g., Caps).
*   **`phys`**: Physics Material ID (e.g., "METAL_STEEL", "GENERIC").
*   **`sock`** (Optional): If `True`, marks this slot as a Socket Anchor (See Section 6).

**Example:**
```python
def get_slot_meta(self):
    return {
        0: {"name": "Surface", "uv": "SKIP", "phys": "METAL_IRON"},
        1: {"name": "Caps", "uv": "BOX", "phys": "METAL_IRON"},
    }
```

---

## 4. Geometry & Topology (`build_shape`)

The core logic resides in `build_shape(self, bm)`.
*   **Input**: `bm` (bmesh.types.BMesh) - The mesh to build into.
*   **Output**: Modify `bm` in place.

### 4.1 Edge Slots (`MASSA_EDGE_SLOTS`)
You **must** create or retrieve the integer layer `MASSA_EDGE_SLOTS` to define edge roles.
*   **0**: None/Smooth.
*   **1 (Perimeter)**: Hard edges, borders, potential seams.
*   **2 (Detail)**: Soft feature lines, creases.
*   **3 (Guide)**: Topological guides (e.g., longitudinal lines on a cylinder).

```python
edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
for e in bm.edges:
    if condition:
        e[edge_slots] = 1
```

### 4.2 Seams
Manual seam marking is **required** for high-quality unwrapping.
*   Mark `e.seam = True` based on geometry logic (e.g., hard angles, material boundaries, or hidden "zipper" lines).

---

## 5. UV Mandate: Manual & Precise

**Golden Cartridges do not rely on auto-unwrapping.**
You must calculate UVs mathematically within `build_shape`.

1.  **Verify Layer**: `uv_layer = bm.loops.layers.uv.verify()`
2.  **Calculate**: Iterate over faces/loops.
    *   Calculate `u` and `v` based on vertex coordinates, arc length, or polar coordinates.
    *   Apply `self.uv_scale` and `self.fit_uvs` logic.
3.  **Handle Wrapping**: For cylindrical objects, detect the 0.0 -> 1.0 seam crossing and shift UVs to prevent "smearing".

**Standard Pattern:**
```python
for f in bm.faces:
    if f.material_index == 0: # Main Surface
        for l in f.loops:
            u, v = calculate_uv(l.vert.co)
            l[uv_layer].uv = (u * scale_u, v * scale_v)
```

---

## 6. Socket Protocols

Sockets are attachment points for the Massa ecosystem.
There are two approved methods. **Method A is the Standard.**

### Method A: Post-Process (Standard)
*   **Definition**: Sockets are generated by the Engine based on slot assignments, then positioned/rotated by the Cartridge in `execute()`.
*   **Workflow**:
    1.  Define a socket slot (usually implicitly via engine, or explicitly).
    2.  Override `execute(self, context)`.
    3.  Call `super().execute(context)`.
    4.  Locate generated socket objects (Child of active object, name starts with `SOCKET_`).
    5.  Apply logic to rotate/move them.
    6.  **Cleanup**: Delete unused sockets if necessary.

**Example:**
```python
def execute(self, context):
    result = super().execute(context)
    if "FINISHED" in result:
        obj = context.active_object
        # Find and rotate socket
        for child in obj.children:
            if "Surface" in child.name:
                child.rotation_euler = (0, 0, 0) # Force Up
    return result
```

### Method B: Geometric (Complex/Micro)
*   **Definition**: The script builds specific faces with the "Socket Anchor" material slot (usually Slot 9).
*   **Workflow**:
    1.  In `get_slot_meta`, define: `9: {"name": "Anchor", "sock": True, ...}`.
    2.  In `build_shape`, create small faces (quads) representing the socket location.
    3.  Assign `material_index = 9`.
    4.  Ensure Face Normal points in the desired socket direction (Z+).
*   **Use Case**: Complex parts like Brackets where sockets must follow parametric geometry precisely.

---

## 7. UI Standards (`draw_shape_ui`)

Implement `draw_shape_ui(self, layout)` to expose parameters.
*   Group related properties (Dimensions, Topology, Features).
*   Use `layout.separator()` for clean spacing.
*   Use standard icons (`MESH_DATA`, `MOD_WIREFRAME`, `FIXED_SIZE`).

---
