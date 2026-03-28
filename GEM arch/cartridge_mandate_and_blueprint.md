# MASSA Cartridge Mandate & Blueprint

> **The "Golden Standard" for Procedural Geometry Cartridges**

All new geometry scripts must adhere to these protocols to ensure consistency, stability, and high-quality output.

## 1. What is a Golden Cartridge?
A **Golden Cartridge** is a self-contained, parametric geometry generator ("smart object") containing:
- **Metadata**: Identity, scale, and capability flags.
- **Topology**: Clean, quad-dominant geometry.
- **Data Layers**: Precise slot assignments, edge roles, and physics IDs.
- **UVs**: Manual, high-quality unwrapping.
- **Sockets**: Explicit attachment points.

## 2. File Structure & Imports
Standard imports must include Blender types, BMesh, Mathutils, and the Base Operator.
```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
```

## 3. Metadata (`CARTRIDGE_META`)
Every cartridge **must** define a `CARTRIDGE_META` dictionary at the module level.
```python
CARTRIDGE_META = {
    "name": "PRIM_01: Structural Beam",
    "id": "prim_01_beam", # MUST match bl_idname suffix
    "version": "1.0",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD", # usually "STANDARD", "MICRO", or "MACRO"
    "flags": {
        "ALLOW_SOLIDIFY": False, # Can the engine add thickness?
        "USE_WELD": True,        # Should vertices be merged?
        "ALLOW_CHAMFER": True,   # Is the geometry suitable for beveling?
        "LOCK_PIVOT": False,     # If True, keeps origin at generation start point.
        "FIX_DEGENERATE": True,
    },
}
```

## 4. Class Definition & Parameters
The operator class **must** inherit from `Massa_OT_Base`.
```python
class MASSA_OT_prim_01_beam(Massa_OT_Base):
    bl_idname = "massa.gen_prim_01_beam" # Prefix 'massa.gen_' is MANDATORY
    bl_label = "Structural Beam"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # PARAMETERS (Blender Properties)
    # Define your cartridge's configurable settings here.
    radius: bpy.props.FloatProperty(name="Radius", default=1.0, min=0.1, unit="LENGTH")
    segments: bpy.props.IntProperty(name="Segments", default=16, min=3)
```

## 5. UI Standards (`draw_shape_ui`)
Implement `draw_shape_ui(self, layout)` to expose parameters in the Sidebar/Redo panel.
- Group related properties (Dimensions, Topology, Features).
- Use `layout.separator()` for clean spacing.
- Use standard icons (`MESH_DATA`, `MOD_WIREFRAME`, `FIXED_SIZE`).

```python
    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "segments")
```

## 6. Execution Core (`build_shape`)
The core logic resides in `build_shape(self, bm)`. Modifies `bm` in place.
- **Pure BMesh**: Never use `bpy.ops` inside `build_shape`. It crashes in background mode. Use `bmesh.ops` or math.
- **No Loose Geometry**: Always run `remove_doubles` and `recalc_face_normals` at the end.
- **Context Safe**: Do not assume `bpy.context.object` exists. Work only on `bm`.

```python
    def build_shape(self, bm: bmesh.types.BMesh):
        # [PHASE 1] Shape Generation
        # (e.g., bmesh.ops.create_cone)

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
