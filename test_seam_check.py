import math
import bmesh
import bpy

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

longitudinal_seams = 0
for e in bm.edges:
    if abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001:
        dist0 = math.hypot(e.verts[0].co.x, e.verts[0].co.z)
        dist1 = math.hypot(e.verts[1].co.x, e.verts[1].co.z)

        if abs(dist0 - dist1) < 0.001:
            if dist0 > bend_radius:
                longitudinal_seams += 1
                e.seam = True

print(f"Longitudinal outer seams: {longitudinal_seams}")

# Now let's test what happens when straight is built with bisect plane.
# Wait, for the STRAIGHT mode:
# `e.verts[0].co.x > 0 and abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001`
# The cross-section is a circle with `y=0` giving `x = +ro, -ro, +ri, -ri`.
# Since we only check `e.verts[0].co.x > 0`, it matches both `x=+ro` and `x=+ri`.
# Both are the "outer side" of the pipe (positive X).
# Also, does it match the radial edges at the cuts?
# Wait, `abs(v0.y) < 0.001 and abs(v1.y) < 0.001`!
# `bisect_plane` generates new faces and edges at the cuts.
# Do the new radial edges at `y=0` get marked as seams in straight mode?
# Yes, if they are at `y=0` and `x>0`!
# Oh no, straight mode might be generating radial seams too!

bm_straight = bmesh.new()
res_out = bmesh.ops.create_circle(bm_straight, radius=ro, segments=sr, cap_ends=False)
verts_out = res_out["verts"]
edges_out = list({e for v in verts_out for e in v.link_edges})

res_in = bmesh.ops.create_circle(bm_straight, radius=ri, segments=sr, cap_ends=False)
verts_in = res_in["verts"]
edges_in = list({e for v in verts_in for e in v.link_edges})

res_bridge = bmesh.ops.bridge_loops(bm_straight, edges=edges_out + edges_in)
faces_start = res_bridge["faces"]

res_ext = bmesh.ops.extrude_face_region(bm_straight, geom=faces_start)
verts_top = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
bmesh.ops.translate(bm_straight, verts=verts_top, vec=(0, 0, 2.0))
# Segments
step = 2.0 / sl
for i in range(1, sl):
    geom_all = bm_straight.faces[:] + bm_straight.edges[:] + bm_straight.verts[:]
    bmesh.ops.bisect_plane(
        bm_straight,
        geom=geom_all,
        dist=0.0001,
        plane_co=(0, 0, i * step),
        plane_no=(0, 0, 1),
    )

straight_seams = 0
straight_long_seams = 0
straight_radial_seams = 0

for e in bm_straight.edges:
    if (
        e.verts[0].co.x > 0
        and abs(e.verts[0].co.y) < 0.001
        and abs(e.verts[1].co.y) < 0.001
    ):
        straight_seams += 1

        # Determine if it's longitudinal or radial
        if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.001:
            straight_long_seams += 1
        else:
            straight_radial_seams += 1

print(f"Straight total seams: {straight_seams}")
print(f"Straight longitudinal seams: {straight_long_seams}")
print(f"Straight radial seams: {straight_radial_seams}")
