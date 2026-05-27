import bpy
import bmesh

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)

for e in bm.edges:
    v1, v2 = e.verts
    if abs(v1.co.y - v2.co.y) < 0.001 and abs(v1.co.y) > 0.999:
        e.seam = True

bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)

marked_count = sum(1 for e in bm.edges if e.seam)
print(f"Edges marked with seam: {marked_count}")
