---
description: Workflow for the Gemini Flash Agent to build new Massa Geometry Cartridges from scratch.
---

# ⚡ MASSA FLASH AGENT: [STATE: BUILD] ⚡

## 1. OBJECTIVES & PRE-REQUISITES
**Goal:** Generate a new, structurally sound Massa Geometry Cartridge following the strict "Golden Cartridge" `CARTRIDGE_MANDATE.md`.
**Inputs:** A concept from the user (e.g., "Build a parametric wooden crate").
**Output:** A `.py` file stored in `massa/modules/cartridges/`.
**Constraints:** Do NOT hallucinate dependencies. Follow the required `import` list exactly. Do NOT invent new class methods outside of `get_slot_meta`, `draw_shape_ui`, and `build_shape`.

## 2. THE GENERATION PROTOCOL

### Step 1: Ingest Blueprint
* Understand the user's geometric requirements.
* Determine the base `bmesh` primitive needed (`create_cube`, `create_cylinder`, `create_grid`, etc.).
* Identify what parameters (`bpy.props`) are required to make it parametric (Width, Height, Bevel Amount).

### Step 2: Write The Immutable Skeleton
**CRITICAL:** Copy this exact file structure. DO NOT deviate.

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "YOUR_NAME_HERE",
    "id": "cart_your_id_here", # Must be unique
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_your_id_here(Massa_OT_Base):
    bl_idname = "massa.gen_cart_your_id_here"
    bl_label = "Cartridge Label"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Define Your Properties Here:
    # width: FloatProperty(name="Width", default=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Base Material", "uv": "BOX", "phys": "GENERIC"},
            # Slots 1-8 if needed
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "GENERIC"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        # col.prop(self, "width")

    def build_shape(self, bm):
        # Your geometry logic goes here.

        # 1. GENERATE Base
        # e.g., result = bmesh.ops.create_cube(bm, size=self.width)

        # 2. SLOTS (Materials & Edges)
        tag_layer = bm.faces.layers.int.new("MAT_TAG")
        edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for f in bm.faces:
            f[tag_layer] = 0 # Base Material Slot 0
            f.material_index = 0

        for e in bm.edges:
            if e.is_boundary or e.calc_face_angle(0) > 1.39:
                e[edge_slots] = 1 # PERIMETER
                e.seam = True

        # 3. POLISH & UVs
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Ensure UVs are handled (Manual or via auto-fallback in Massa)
```

### Step 3: Implement Parametric Logic (`build_shape`)
* Replace the placeholder geometry logic with the actual user request.
* **Anti-Hallucination Check:** Did you use `bpy.ops`? **STOP**. Rewrite using only `bmesh.ops`.
* **Topology Check:** Always include `remove_doubles` and `recalc_face_normals` at the very end of `build_shape`.

### Step 4: Verification & Transition
* Review the generated code. Ensure all indentation is correct.
* Transition directly to `[STATE: AUDIT]` to execute the new code against the `runner.py` debugging system. Do not skip this step.
