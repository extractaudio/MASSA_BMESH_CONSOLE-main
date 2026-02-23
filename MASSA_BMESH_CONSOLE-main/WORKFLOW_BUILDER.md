# MASSA BUILDER WORKFLOW

> **"Fluent Geometry for the Procedural Age."**

This document outlines the workflow for using the `MassaBuilder` class (`modules/massa_builder.py`) to generate procedural geometry within the Massa Console architecture.

## 1. Philosophy

The `MassaBuilder` is designed around a **Fluent Interface** pattern:
1.  **Select** geometry (faces, edges).
2.  **Act** on the selection (extrude, inset, tag).
3.  **Repeat**.

This structure allows agents (AI) and developers to write linear, readable code that describes *what* the shape is, rather than *how* to juggle BMesh vertex lists.

```python
# The Old Way (Standard BMesh)
ret = bmesh.ops.create_cube(bm, size=1.0)
verts = ret['verts']
bmesh.ops.translate(bm, vec=(0,0,1), verts=verts)
# ... manual face finding ...

# The New Way (MassaBuilder)
builder = MassaBuilder(bm)
builder.create_box(1, 1, 1, center=(0, 0, 1)) \
       .select_facing(Vector((0, 0, 1))) \
       .extrude(0.5)
```

## 2. Core Workflow

### A. Initialization
Always wrap the incoming `bm` (BMesh) at the start of your `build_shape` method.

```python
from ...modules.massa_builder import MassaBuilder

def build_shape(self, bm: bmesh.types.BMesh):
    builder = MassaBuilder(bm)
    # Start building...
```

### B. Creation
Start with a primitive.

*   `create_box(width, depth, height)`
*   `create_cylinder(radius, depth)`
*   `create_grid(x_segments, y_segments)`

### C. Selection
Most operations (Extrude, Inset, Tag) apply to the **Active Selection**.

*   `select_all_faces()`
*   `select_faces_by_normal(direction, tolerance)`: Crucial for finding "Top", "Side", "Front" faces.
*   `select_faces_by_height(min_z, max_z)`: Great for multi-story structures.
*   `select_faces_by_slot(index)`: Re-select parts you've already tagged.

### D. Modification
Transform the selected geometry.

*   `extrude(distance)`: Adds volume.
*   `inset(amount, depth)`: Adds detail/panels.
*   `translate/rotate/scale`: Moves the selection.

### E. Tagging
Assign metadata for the Console (Materials, Physics, Sockets).

*   `tag_slot(index)`: Assigns Material Slot 0-9.
*   `tag_edge_role(id)`: Marks edges for Bevels/Seams (1=Peri, 2=Contour, 3=Guide, 4=Detail, 5=Fold).
*   `tag_socket(id)`: Marks selected faces as sockets (center + normal). **No extra mesh required.**

## 3. Example Patterns

### Pattern: The "Clean Socket"
Creates a socket without generating extra geometry.

```python
# Create main shape
builder.create_box(1, 1, 1)

# Select Top Face for Socket 1 (Up)
builder.select_faces_by_normal(Vector((0, 0, 1))) \
       .tag_socket(1)

# Select Bottom Face for Socket 2 (Down/Anchor)
builder.select_faces_by_normal(Vector((0, 0, -1))) \
       .tag_socket(2)
```

### Pattern: The "Inset Panel"
Creates a tech-panel look on a surface.

```python
builder.select_faces_by_normal(Vector((0, 1, 0))) \  # Select Front
       .inset(0.1, relative=False) \                 # Create Frame
       .tag_slot(2) \                                # Tag Frame (Metal)
       .extrude(-0.05) \                             # Push In
       .tag_slot(1) \                                # Tag Inner (Detail)
       .select_faces_by_normal(Vector((0, 1, 0))) \  # Re-select inner face
       .tag_socket(1)                                # Add Socket
```

### Pattern: The "Stacked Tower"
Builds a segmented tower.

```python
builder.create_cylinder(radius=2, depth=1) \
       .select_faces_by_normal(Vector((0, 0, 1))) \  # Select Top
       .extrude(1.0) \                               # Level 2
       .scale(0.8, 0.8, 1.0) \                       # Taper
       .extrude(1.0) \                               # Level 3
       .scale(0.8, 0.8, 1.0)
```

## 4. Debugging & Agents

The `MassaBuilder` includes tools specifically for Agent introspection.

### `builder.report()`
Returns a string summary of the mesh.

```python
print(builder.report())
# Output:
# --- Mesh Report ---
# Verts: 24, Edges: 36, Faces: 14
# Volume: 2.5000
# Active Selection: 4 faces
# -------------------
```

**Agent Tip:** Call `report()` after complex steps to verify you actually selected faces before extruding. If "Active Selection" is 0, your logic failed.

**UV Audit:** Use the "Finalize & Inspect" operator in the Console UI (N-Panel or UVs Tab) to bake the procedural object and verify the UV layout in Edit Mode.

## 5. API Reference

For full API details, inspect `modules/massa_builder.py`. The class is fully documented with docstrings.
