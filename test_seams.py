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

def is_longitudinal_seam(e):
    # What does the original code check?
    if abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001:
        return True
    return False

c = 0
for e in bm.edges:
    if is_longitudinal_seam(e):
        c += 1

print("Original match count:", c)

def is_strait_seam(e):
    # Only pick edges that are going *along* the pipe.
    # An edge goes along the pipe if its local x,z direction is not pointing radially or tangentially in the cross section.
    # We can detect this easily: the edge connects two vertices that belong to adjacent spin steps, so they have different angles around the Y axis.

    # Let's check the math.
    pass

def new_seam_check(e):
    # A single straight seam running the length of the pipe.
    # If the pipe is spun around the Y axis, the straight seam would have constant local angle in the tube cross section.
    # Before spin, the cross section is in XY plane, but it's translated in X by bend_radius.
    # Oh wait, the cross section was created with create_circle in XY plane?
    # Let's check create_circle defaults. It's usually XY plane.
    # Yes, create_circle is in XY plane, meaning z=0.
    # Then we translate it by (bend_radius, 0, 0).
    # Then spin around (0, 1, 0), centered at (0, 0, 0).
    # This creates a pipe in the XZ plane.

    # We want a seam on the side. The side can be y=radius or y=0 and z=radius etc.
    # In the original elbow:
    # "if abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001"
    # This selects ALL edges that have y=0.
    # But y=0 is an entire circle on both sides! The cross section is a circle in XY.
    # y=0 intersects the circle at exactly 2 points (inner and outer).
    # Wait, 2 points for outer ring, 2 points for inner ring.
    # And after spin, these points become edges along the pipe.
    # BUT! There are also edges *around* the pipe at these y=0 positions? No, the edges around the pipe will ALSO have y=0 if the spin is around Y axis, because Y coordinates do not change during spin around Y axis.
    # Let's verify this.

    v0 = e.verts[0].co
    v1 = e.verts[1].co
    if abs(v0.y) < 0.001 and abs(v1.y) < 0.001:
        return True
    return False

# So the original code marks ALL edges where Y=0 as seams.
# This includes the longitudinal edges AND the radial edges at Y=0!
# We want ONLY the longitudinal edges.
# A longitudinal edge connects vertices at different spin steps.
# A radial edge connects vertices at the same spin step.
# If they are at the same spin step, the angle of the spin (around Y axis) is the same.
# Or, the distance to the origin in XZ plane is different for radial edges, but the same for longitudinal edges!

# Wait, for a longitudinal edge, the distance to the origin in XZ plane (math.hypot(x, z)) is constant! (Except for inner vs outer wall, but for a single edge, it connects v0 and v1 which are on the same wall and same cross-section position, so same distance to origin).
# Let's check distance to origin in XZ plane.
c2 = 0
for e in bm.edges:
    v0 = e.verts[0].co
    v1 = e.verts[1].co
    if abs(v0.y) < 0.001 and abs(v1.y) < 0.001:
        dist0 = math.hypot(v0.x, v0.z)
        dist1 = math.hypot(v1.x, v1.z)
        if abs(dist0 - dist1) < 0.001:
            c2 += 1
            # print(f"Longitudinal seam candidate: {v0} to {v1}")

print("Filtered match count:", c2)
