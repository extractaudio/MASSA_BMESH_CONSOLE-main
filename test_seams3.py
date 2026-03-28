import bpy
import bmesh
import math

bm = bmesh.new()

ro = 0.2
ri = 0.18
sr = 16
sl = 8
bend_radius = 0.5

res_out = bmesh.ops.create_circle(bm, radius=ro, segments=sr, cap_ends=False)
verts_out = res_out["verts"]
edges_out = list({e for v in verts_out for e in v.link_edges})

res_in = bmesh.ops.create_circle(bm, radius=ri, segments=sr, cap_ends=False)
verts_in = res_in["verts"]
edges_in = list({e for v in verts_in for e in v.link_edges})

res_bridge = bmesh.ops.bridge_loops(bm, edges=edges_out + edges_in)
faces_start = res_bridge["faces"]

bmesh.ops.translate(bm, verts=bm.verts, vec=(bend_radius, 0, 0))
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

longitudinal_seams = 0
for e in bm.edges:
    if abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001:
        # Distance to origin in XZ plane
        dist0 = math.hypot(e.verts[0].co.x, e.verts[0].co.z)
        dist1 = math.hypot(e.verts[1].co.x, e.verts[1].co.z)

        # In straight mode, the seam is at x > 0 (outer curve equivalent).
        # We want longitudinal edges (dist0 == dist1)
        if abs(dist0 - dist1) < 0.001:
            # Check if it's the outer curve
            # In straight mode, x > 0 implies x > bend_radius for elbow
            if dist0 > bend_radius:
                longitudinal_seams += 1

print(f"Longitudinal outer seams: {longitudinal_seams}")
