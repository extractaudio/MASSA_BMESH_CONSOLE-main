---
description: DEFINITIVE MANDATES: Corrected Class-Based Structure & Logic for Geometry Cartridges.
---

# 🟢 AGENT: CARTRIDGE_MANDATES (CORRECTED)

## 1. OBJECTIVE

To standardize the Python structure of all Geometry Cartridges, ensuring seamless integration with the Massa Console. This protocol defines the **Class Structure**, **Property Logic**, and **5-Phase Execution** required for every cartridge.

---

## 2. CARTRIDGE FORMAT (CLASS STRUCTURE)

**Constraint:** All cartridges must be a Blender Operator inheriting from `Massa_OT_Base`. Parameters are defined as class properties, and logic lives in `build_shape`.

### 📝 Standard Template

```python
import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty
from mathutils import Vector, Matrix
from ...operators.massa_base import Massa_OT_Base

# ---------------------------------------------------------
# METADATA BLOCK
# ---------------------------------------------------------
CARTRIDGE_META = {
    "name": "Cartridge Name",
    "id": "cartridge_id",  # unique identifier
    "icon": "CUBE",        # Blender Icon ID
    "scale_class": "STANDARD", # STANDARD, LARGE, TINY
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
    },
}

class MASSA_OT_CartridgeName(Massa_OT_Base):
    """Docstring explaining the cartridge purpose"""

    bl_idname = "massa.gen_cartridge_id" # Must match meta ID if possible
    bl_label = "Massa Cartridge Name"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # ---------------------------------------------------------
    # PARAMETERS (Properties)
    # ---------------------------------------------------------
    radius: FloatProperty(name="Radius", default=1.0, min=0.1, unit="LENGTH")
    segments: IntProperty(name="Segments", default=16, min=3)
    
    # ---------------------------------------------------------
    # SLOT DEFINITIONS (Material & Physics)
    # ---------------------------------------------------------
    def get_slot_meta(self):
        """
        Defines the material slots available for this shape.
        Keys (0-9) map to UI Slot Tabs.
        """
        return {
            0: {"name": "Primary Material", "uv": "BOX", "phys": "GENERIC"},
            1: {"name": "Secondary Detail", "uv": "TRIPLANAR", "phys": "METAL_STEEL"},
            2: {"name": "Trim/Decal", "uv": "FIT", "phys": "PLASTIC"},
        }

    # ---------------------------------------------------------
    # UI DRAWING
    # ---------------------------------------------------------
    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "radius")
        col.prop(self, "segments")

    # ---------------------------------------------------------
    # EXECUTION CORE
    # ---------------------------------------------------------
    def build_shape(self, bm: bmesh.types.BMesh):
        """
        The geometry generation kernel.
        All logic must operate on the provided BMesh 'bm'.
        """
        
        # ---------------------------------------------------------
        # PHASE 1: SHAPE (Unique Geometry Logic)
        # ---------------------------------------------------------
        # Use 'self.prop_name' to access parameters
        # Example:
        # bmesh.ops.create_circle(bm, cap_ends=True, radius=self.radius, segments=self.segments)
        
        # ---------------------------------------------------------
        # PHASE 2: SLOTS (Material Assignment)
        # ---------------------------------------------------------
        # Mandate: Assign material_index to faces based on logic.
        # 0 = Primary, 1 = Secondary, etc.
        # for f in bm.faces:
        #     f.material_index = 0
            
        # ---------------------------------------------------------
        # PHASE 3: EDGES (Feature Definition)
        # ---------------------------------------------------------
        # Mandate: Mark edges for specific roles using the EDGE_SLOTS layer.
        # Ref: WF_Slot_Standardization.md
        
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
            
        # Example: Mark boundary as Perimeter (Slot 1)
        # for e in bm.edges:
        #     if e.is_boundary:
        #         e[edge_slots] = 1 
        
        # ---------------------------------------------------------
        # PHASE 4: UV (Unwrap Strategy)
        # ---------------------------------------------------------
        # Mandate: All faces must be mapped. 
        # Strategies: BOX, UNWRAP (Seam-based), FIT, STRIP.
        
        # ---------------------------------------------------------
        # PHASE 5: POLISH (Cleanup)
        # ---------------------------------------------------------
        # Mandate: Ensure valid topology.
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
```

---

## 3. UV UNWRAP MANDATE

**Objective:** Eliminate manual UV work by procedurally unwrapping based on geometry type.

| Strategy | Trigger | Implementation |
| :--- | :--- | :--- |
| **BOX** | Hard Surface / Blocky | `bmesh.ops.uv_project` (Cube Projection) |
| **UNWRAP** | Organic / Curved | `bmesh.ops.uv_unwrap` (Requires Seams in Phase 3) |
| **FIT** | Glass / Screens | Bounds fit to 0-1 space. |
| **STRIP** | Pipes / Trims | Follow active quads (Grid Fill). |

### 📝 Implementation Rules

1. **Seam Dependency**: If using `UNWRAP`, you **MUST** define seams in Phase 3 (Edge Slots) using ID `3` (GUIDE) or `1` (PERIMETER).
2. **No Overlaps**: Box mapping must use a scale that prevents texture bleeding.
3. **Orientation**: 'Top' of the object should generally align with UV Y-axis.

---

## 4. EDGES MANDATE (EDGE SLOTS)

**Objective:** Edges must carry logical data for the Console's Polish Stack (Bevels, Cloth, Subdivision).

### Automatic Detection Rules (Helper Logic)

* **PERIMETER (1)**: MUST be applied to all open boundaries (`edge.is_boundary`).
* **CONTOUR (2)**: MUST be applied to edges with face angles > 80 degrees (`edge.calc_face_angle() > 1.39`).

### ID Dictionary (Standard)

| ID | Name | Role | Default Behavior |
| :--- | :--- | :--- | :--- |
| **1** | **PERIMETER** | Boundary / Outline | Bevel + Seam |
| **2** | **CONTOUR** | Sharp Feature Line | Sharp + Bevel |
| **3** | **GUIDE** | Organic Seam | Seam Only (for UV Unwrap) |
| **4** | **DETAIL** | Surface Detail | Crease (Subd) |
| **5** | **FOLD** | Cloth Wrinkle/Tension | Cloth Pinning / Force Field |
