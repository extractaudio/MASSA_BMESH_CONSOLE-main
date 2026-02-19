
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ==============================================================================
# CARTRIDGE METADATA
#
# ==============================================================================
CARTRIDGE_META = {
    "name": "Arch_03_Stairs_Industrial",
    "id": "PRIM_21_STAIR_IND",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
    },
}


# ==============================================================================
# SLOT PROTOCOL
#
# ==============================================================================
def get_slot_meta():
    return {
        0: {"name": "Metal_Painted_Steel", "type": "MAT", "phys": "METAL_STEEL"},
        1: {"name": "Metal_Grate_Floor", "type": "MAT", "phys": "METAL_GRATE"},
        2: {"name": "Rubber_Nosing_Grip", "type": "MAT", "phys": "RUBBER"},
        3: {"name": "Safety_Caution_Yel", "type": "MAT", "phys": "PAINT"},
        4: {"name": "Metal_Raw_Scaffold", "type": "MAT", "phys": "METAL_ALUM"},
        8: {"name": "SYS_Anchor", "type": "SOCK", "phys": "AUX"},
        9: {"name": "SYS_Socket", "type": "SOCK", "phys": "AUX"},
    }


# ==============================================================================
# GEOMETRY ENGINE
# ==============================================================================
def build_shape(
    bm: bmesh.types.BMesh, prop_width=1.2, prop_height=3.0, prop_run=4.0, prop_steps=12
):
    """
    Generates Industrial Staircase using PRIM_01 (Stringers) and PRIM_04 (Treads).
    STRATEGY: Combination 1 (The Path Follower)
    """

    # 1. CALCULATE PITCH & SPACING
    rise = prop_height / prop_steps
    run_depth = prop_run / prop_steps
    stair_length = math.hypot(prop_height, prop_run)
    pitch = math.atan2(prop_height, prop_run)

    # 2. GENERATE STRINGERS (PRIM_01 LOGIC)
    # - PRIM_01 Algorithm

    channel_w = 0.05
    channel_h = 0.25

    # Define C-Channel Profile (Local 2D X/Y coords)
    profile_pts = [
        (channel_w, channel_h / 2),  # Top Flange Tip
        (0.0, channel_h / 2),  # Top Corner
        (0.0, -channel_h / 2),  # Bottom Corner
        (channel_w, -channel_h / 2),  # Bottom Flange Tip
    ]

    # PRIM_01 Golden Snippet: Perimeter Walking for UVs
    def get_u_param(x, y, pts):
        cu = 0.0
        # Calculate total perimeter length for normalization (optional, strictly metric here)
        # Using metric U allows tiling textures to match world scale.
        for i in range(len(pts)):
            p1 = pts[i]
            # If vertex matches point, return current accumulator
            if math.hypot(p1[0] - x, p1[1] - y) < 0.001:
                return cu
            if i < len(pts) - 1:
                pn = pts[i + 1]
                cu += math.hypot(pn[0] - p1[0], pn[1] - p1[1])
        return 0.0

    def create_stringer(offset_x):
        # A. Create Cap Vertices
        input_verts = []
        for px, py in profile_pts:
            # Create base profile.
            # Local construct: X=Width, Y=Height (Vertical in profile).
            # We construct on XZ plane initially.
            v = bm.verts.new(Vector((px + offset_x, 0, py)))
            input_verts.append(v)

        # B. Create Cap Face
        face_start = bm.faces.new(input_verts)
        face_start.material_index = 0  # Metal_Painted_Steel

        # C. Extrude along Y (Length)
        geom_ext = bmesh.ops.extrude_face_region(bm, geom=[face_start])

        verts_extruded = [
            v for v in geom_ext["geom"] if isinstance(v, bmesh.types.BMVert)
        ]
        faces_extruded = [
            f for f in geom_ext["geom"] if isinstance(f, bmesh.types.BMFace)
        ]

        # Move extruded verts to length
        bmesh.ops.translate(bm, verts=verts_extruded, vec=Vector((0, stair_length, 0)))

        # D. UV Logic (PRIM_01)
        uv_layer = bm.loops.layers.uv.verify()

        for f in faces_extruded:
            f.material_index = 0
            for loop in f.loops:
                v = loop.vert
                # Map U to profile perimeter, V to Length (Y)
                # Recover local profile coords:
                local_x = v.co.x - offset_x
                local_z = v.co.z

                u_val = get_u_param(local_x, local_z, profile_pts)
                v_val = v.co.y  # Length

                loop[uv_layer].uv = (u_val, v_val)

        # E. Rotate to Pitch
        # We collected all geometry (cap + extrusion)
        all_verts = input_verts + verts_extruded

        # Rotate around X-axis.
        # Positive rotation around X moves Y-axis towards Z-axis (Right Hand Rule).
        bmesh.ops.rotate(
            bm,
            verts=all_verts,
            cent=Vector((0, 0, 0)),
            matrix=Matrix.Rotation(pitch, 4, "X"),
        )

    # Generate Left and Right Stringers
    create_stringer(-prop_width / 2)
    create_stringer(prop_width / 2)

    # 3. GENERATE TREADS (PRIM_04 LOGIC)
    # - PRIM_04 Panel Logic

    tread_thick = 0.03

    for i in range(prop_steps):
        # Calculate Position
        pos_y = (i + 1) * run_depth - (run_depth / 2)  # Center of tread depth
        pos_z = (i + 1) * rise

        center = Vector((0, pos_y, pos_z))

        # Dimensions
        sx = prop_width - (channel_w * 2) - 0.02  # Width inside stringers
        sy = run_depth + 0.05  # Depth with overlap
        sz = tread_thick

        # Create Cube (Cell Gen)
        ret = bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(center)
            @ Matrix.Scale(sx, 4, (1, 0, 0))
            @ Matrix.Scale(sy, 4, (0, 1, 0))
            @ Matrix.Scale(sz, 4, (0, 0, 1)),
        )

        tread_faces = ret["faces"]

        # ASSIGN SLOTS & UVs
        uv_layer = bm.loops.layers.uv.verify()

        for f in tread_faces:
            # PRIM_04 Normal Override Check
            #
            if f.normal.z > 0.5:
                f.material_index = 1  # Metal_Grate (Top)
            elif abs(f.normal.y) > 0.9:
                f.material_index = 3  # Safety Yellow (Front/Back)
            else:
                f.material_index = 0  # Frame

            # UV: Tri-Planar Box Map
            for loop in f.loops:
                v = loop.vert
                # Top projection
                if abs(f.normal.z) > 0.5:
                    loop[uv_layer].uv = (v.co.x, v.co.y)
                # Side projection
                elif abs(f.normal.x) > 0.5:
                    loop[uv_layer].uv = (v.co.y, v.co.z)
                # Front projection
                else:
                    loop[uv_layer].uv = (v.co.x, v.co.z)

    # 4. SOCKETS
    #
    def make_socket(loc, normal_axis, slot_idx):
        # Create a small quad
        s = 0.05
        # Start at origin
        v1 = bm.verts.new(Vector((-s, -s, 0)))
        v2 = bm.verts.new(Vector((s, -s, 0)))
        v3 = bm.verts.new(Vector((s, s, 0)))
        v4 = bm.verts.new(Vector((-s, s, 0)))
        f = bm.faces.new((v1, v2, v3, v4))
        f.material_index = slot_idx

        # Rotate to align Z-up to normal_axis
        z_up = Vector((0, 0, 1))
        if normal_axis != z_up:
            rot_quat = z_up.rotation_difference(normal_axis)
            bmesh.ops.rotate(
                bm,
                verts=f.verts,
                cent=Vector((0, 0, 0)),
                matrix=rot_quat.to_matrix().to_4x4(),
            )

        # Translate to location
        bmesh.ops.translate(bm, verts=f.verts, vec=loc)

    # Anchor (Bottom Center, Z-up)
    make_socket(Vector((0, 0, 0)), Vector((0, 0, 1)), 8)

    # Joint (Top, Z-up for railing connection)
    make_socket(Vector((0, prop_run, prop_height)), Vector((0, 0, 1)), 9)

    # 5. CLEANUP
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


# ==============================================================================
# OPERATOR WRAPPER
# ==============================================================================
class MASSA_OT_PartsHandrail(bpy.types.Operator):
    """Generates a Handrail using procedural logic."""

    bl_idname = "massa.cart_parts_handrail"
    bl_label = "Build Parts Handrail"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Create a new mesh and object
        mesh = bpy.data.meshes.new("Handrail_Mesh")
        obj = bpy.data.objects.new("Handrail", mesh)

        # Link to the current collection
        context.collection.objects.link(obj)

        # Iterate inputs or use defaults (Placeholder logic for now)
        # We will use a fresh BMesh
        bm = bmesh.new()

        # Call the geometry engine
        # NOTE: Using the existing build_shape function for now, usually you would rename/refactor this
        build_shape(bm, prop_width=1.2, prop_height=3.0, prop_run=4.0, prop_steps=12)

        # Write BMesh to mesh
        bm.to_mesh(mesh)
        bm.free()

        return {"FINISHED"}


def register():
    bpy.utils.register_class(MASSA_OT_PartsHandrail)


def unregister():
    bpy.utils.unregister_class(MASSA_OT_PartsHandrail)


if __name__ == "__main__":
    register()
