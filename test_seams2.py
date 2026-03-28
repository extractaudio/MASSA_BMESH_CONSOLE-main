import bpy
import bmesh
import math

bm = bmesh.new()

ro = 0.2
ri = 0.18
sr = 16
sl = 8

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
        # Check if the edge is on the outer ring, inner ring, or bridging them.
        v0 = e.verts[0].co
        v1 = e.verts[1].co
        dist0 = math.hypot(v0.x, v0.z)
        dist1 = math.hypot(v1.x, v1.z)

        # A longitudinal edge connects vertices at different spin steps.
        # Its length in the XZ plane is not 0.
        # However, a radial edge also has non-zero length in XZ plane (dist0 != dist1).
        # We want longitudinal edges. For them, dist0 == dist1.

        # Also, do we want seams on the inside and outside of the elbow?
        # A straight line on the elbow. There are 2 longitudinal lines with Y=0.
        # One with X > bend_radius, one with X < bend_radius (in local cross section).
        # The original code for STRAIGHT sets seam when X > 0.
        # So we probably only want one longitudinal seam, on the outer curve or inner curve of the elbow.

        if abs(dist0 - dist1) < 0.001:
            print(f"Longitudinal dist={dist0:.3f}")
        else:
            print(f"Radial dist={dist0:.3f} to {dist1:.3f}")
