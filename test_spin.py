import bpy
import bmesh
import math

bm = bmesh.new()

ro = 0.2
ri = 0.18
sr = 8
sl = 4

res_out = bmesh.ops.create_circle(bm, radius=ro, segments=sr, cap_ends=False)
verts_out = res_out["verts"]
edges_out = list({e for v in verts_out for e in v.link_edges})

res_in = bmesh.ops.create_circle(bm, radius=ri, segments=sr, cap_ends=False)
verts_in = res_in["verts"]
edges_in = list({e for v in verts_in for e in v.link_edges})

res_bridge = bmesh.ops.bridge_loops(bm, edges=edges_out + edges_in)
faces_start = res_bridge["faces"]

bmesh.ops.translate(bm, verts=bm.verts, vec=(0.5, 0, 0))
bmesh.ops.spin(
    bm,
    geom=faces_start,
    angle=math.radians(-90),
    steps=sl,
    axis=(0, 1, 0),
    cent=(0, 0, 0),
    use_duplicate=False,
)

print("Total edges:", len(bm.edges))
for e in bm.edges:
    if abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001:
        print(f"Edge matched: {e.verts[0].co} to {e.verts[1].co}")
