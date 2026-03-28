# MASSA Edge and Topology Protocol

> **Controlling Geometry Polish through Edge Roles**

In MASSA, you tag edges in `build_shape()` to guide the Polish Stack (Bevel, Subdiv, Sharpness) and UV Unwrapper downstream.

## 1. The `MASSA_EDGE_SLOTS` Layer
You **must** create or retrieve the integer layer `MASSA_EDGE_SLOTS` to define edge roles.

**Implementation Example:**
```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
if not edge_slots:
    edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

for e in bm.edges:
    if condition:
        e[edge_slots] = 1 # Perimeter
```

## 2. Standard Edge Roles (1-5)
| ID | Name | Behavior | Auto-Detection Logic |
| :--- | :--- | :--- | :--- |
| **0** | **None** | Smooth / unassigned. | |
| **1** | **PERIMETER** | **Seam + Sharp + Bevel**. The outer silhouette and end-cap borders. | Edges separating "End Caps" (Top/Bottom) from "Walls" (Sides). |
| **2** | **CONTOUR** | **Sharp + Bevel**. Hard internal angles (90°+) not on the perimeter. | Sharp edges not on the perimeter. |
| **3** | **GUIDE** | **Seam Only**. Manual UV cut lines for cylinders, tubes, and organic surfaces. | Pathfinding walks along "Wall" geometry to connect End Caps. |
| **4** | **DETAIL** | **Bevel Only**. Small chamfers and soft feature lines. No sharp shading. | Material boundaries or internal details. |
| **5** | **FOLD** | **Crease**. Subdivision surface weighting and cloth pinning. | N/A (Manual only). |

## 3. Seams & UV Strategy
Manual seam marking is **required** for high-quality unwrapping.
- Mark `e.seam = True` based on geometry logic (e.g., hard angles, material boundaries, or hidden "zipper" lines).
- Seams explicitly mapped into edge roles (`1` or `3`) ensure the pipeline unwrap correctly, especially in "UNWRAP" face strategies.

## 4. Socket Attachment Topology
Sockets are attachment points for the Massa ecosystem.
**Standard Method: Tag Existing Faces.**
Do not generate extra geometry (like grids) just for sockets. Instead, select existing faces that represent logical connection points (e.g., wall ends, column caps) and tag them using `MassaBuilder`.

**Workflow:**
1. In `get_slot_meta`, define: `9: {"name": "Anchor", "sock": True, ...}`.
2. In `build_shape`, use `builder.clean()` to merge geometry.
3. Select the desired connection faces (e.g., using `select_faces_by_normal`).
4. Call `builder.tag_socket(id)`.
5. **Socket Anchor (Slot 9)**: Defines the object's origin/base. Ensure geometry is built relative to (0,0,0) as the anchor. If a face exists at the anchor (e.g. Column Bottom), tag it as a socket or Slot 9.

**Example using `builder`:**
```python
# Create Geometry
builder.create_box(1, 1, 1).translate(0, 0, 0.5)
builder.clean()

# Tag Top Face as Socket 2
builder.select_faces_by_normal(Vector((0, 0, 1))) \
       .tag_socket(2)

# Tag Bottom Face as Socket 1 (Anchor)
builder.select_faces_by_normal(Vector((0, 0, -1))) \
       .tag_socket(1)
```

## 5. Topology Rules
- **Pure BMesh:** NO `bpy.ops` allowed in `build_shape`. Use `bmesh.ops` exclusively.
- **Clean Geometry:** Clean, quad-dominant geometry.
- **No Loose Geometry:** Always run `bmesh.ops.remove_doubles` and `bmesh.ops.recalc_face_normals` at the very end.
- **Clamping:** Ensure geometric parameters are safely clamped so inputs cannot collapse the geometry.
