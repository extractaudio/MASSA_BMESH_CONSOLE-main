import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ==============================================================================
# CARTRIDGE METADATA
#
# ==============================================================================
CARTRIDGE_META = {
    "name": "Massa_Ind_Staircase",
    "id": "PRIM_21_STAIR",
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
    """

    # 1. CALCULATE PITCH & SPACING
    rise = prop_height / prop_steps
    run_depth = prop_run / prop_steps

    # 2. GENERATE STRINGERS (PRIM_01 LOGIC)
    # - PRIM_01 Algorithm

    channel_w = 0.05
    channel_h = 0.25

    # Define C-Channel Profile (Local XY for simple extrusion, will rotate later)
    # 2D Profile Points for UV Walking
    profile_pts = [
        (channel_w, channel_h / 2),  # Top Flange Tip
        (0.0, channel_h / 2),  # Top Corner
        (0.0, -channel_h / 2),  # Bottom Corner
        (channel_w, -channel_h / 2),  # Bottom Flange Tip
    ]

    # Helper: PRIM_01 Golden Snippet (Perimeter Walking)
    # Calculates 'U' based on Euclidean distance along the profile
    def get_u_param(x, y, pts):
        cu = 0.0
        total_len = 0.0
        # Calculate total length first for normalization (optional, here we keep metric)
        for i in range(len(pts) - 1):
            total_len += math.hypot(
                pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            )

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
        # Create Verts for the Cap
        input_verts = []
        for px, py in profile_pts:
            # Create base profile. We orient it so 'Y' is up/down in profile space,
            # which maps to Z in world space eventually.
            # Local construct: X=Width, Y=Height.
            v = bm.verts.new(Vector((px + offset_x, 0, py)))
            input_verts.append(v)

        # Connect Face (Cap)
        face_start = bm.faces.new(input_verts)
        face_start.material_index = 0  # Metal_Painted_Steel

        # EXTRUDE (PRIM_01 Base Extrusion)
        # Extrude along Y (Length) initially
        stair_length = math.hypot(prop_height, prop_run)
        geom_ext = bmesh.ops.extrude_face_region(bm, geom=[face_start])

        verts_extruded = [
            v for v in geom_ext["geom"] if isinstance(v, bmesh.types.BMVert)
        ]
        faces_extruded = [
            f for f in geom_ext["geom"] if isinstance(f, bmesh.types.BMFace)
        ]

        # Move extruded verts to length
        bmesh.ops.translate(bm, verts=verts_extruded, vec=Vector((0, stair_length, 0)))

        # UV MAPPING (The PRIM_01 Logic)
        uv_layer = bm.loops.layers.uv.verify()

        # Process Side Walls (The Extrusion)
        for f in faces_extruded:
            f.material_index = 0
            # Identify if this is a wall or a cap?
            # In extrude_face_region, the new faces are the walls.
            for loop in f.loops:
                v = loop.vert
                # Map U to profile perimeter, V to Length (Y)
                # We need to recover the local X/Z relative to the profile start
                # Since we translated Y, the X and Z coords are constant along the beam.
                local_x = v.co.x - offset_x
                local_z = v.co.z

                u_val = get_u_param(local_x, local_z, profile_pts)
                v_val = v.co.y  # Length

                loop[uv_layer].uv = (u_val, v_val)

        # ROTATE TO PITCH
        # Now we rotate the whole stringer to the stair angle
        # Pitch angle is atan(rise/run)
        pitch = math.atan2(prop_height, prop_run)

        # Collect all geometry created (cap + extrusion)
        all_verts = input_verts + verts_extruded

        # Rotation around X-axis (Pitch up)
        bmesh.ops.rotate(
            bm,
            verts=all_verts,
            cent=Vector((0, 0, 0)),
            matrix=Matrix.Rotation(
                -pitch, 4, "X"
            ),  # Negative to pitch up from Y-forward?
            # Wait, if we extruded Y forward, we need to rotate around X.
            # Stair goes Y+ and Z+.
            # If we rotate Y-axis vector by -pitch, it goes up?
            # Let's use strict vector math.
        )

        # Fix rotation direction: We want (0,1,0) to become (0, run, rise).normalized
        # Actually easier to just rotate by -pitch around X if we started flat.
        # But let's verify orientation.
        # If we just force the verts to the correct slope:
        # It's better to rotate.

        rot_mat = Matrix.Rotation(-pitch, 4, "X")  # Blender X is side-to-side.
        # Verify: Y is forward. Rotate around X.
        # If angle is positive (slope up), we rotate X positive?
        # Right Hand Rule: Thumb X+, fingers curl Y+ to Z+.
        # So Positive Rotation moves Y up to Z.
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
        pos_y = (i + 1) * run_depth - (run_depth / 2)  # Center of tread
        pos_z = (i + 1) * rise

        center = Vector((0, pos_y, pos_z))

        # Create Cube
        # scale X = width inside stringers
        # scale Y = run_depth
        # scale Z = thickness
        sx = prop_width - (channel_w * 2) - 0.02  # Gap
        sy = run_depth + 0.05  # Overlap
        sz = tread_thick

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
            # PRIM_04 Normal Override
            # - "STRICT CHECK: If it points down, FLIP IT UP"
            # Note: We don't flip geometry here, just checking for material assignment

            if f.normal.z > 0.5:
                f.material_index = 1  # Metal_Grate (Top)
            elif abs(f.normal.y) > 0.9:
                f.material_index = 3  # Safety Yellow (Front/Back)
            else:
                f.material_index = 0  # Frame

            # Tri-Planar Box Map for Grates
            for loop in f.loops:
                v = loop.vert
                # Top projection
                if f.normal.z > 0.5 or f.normal.z < -0.5:
                    loop[uv_layer].uv = (v.co.x, v.co.y)
                else:
                    loop[uv_layer].uv = (v.co.y, v.co.z)

    # 4. SOCKETS
    #
    def make_socket(loc, axis, slot_idx):
        # Create a small quad aligned to axis
        # Simplified: Just a small quad at location
        s = 0.05
        # Basic quad on ground plane, then rotate
        v1 = bm.verts.new(loc + Vector((-s, -s, 0)))
        v2 = bm.verts.new(loc + Vector((s, -s, 0)))
        v3 = bm.verts.new(loc + Vector((s, s, 0)))
        v4 = bm.verts.new(loc + Vector((-s, s, 0)))
        f = bm.faces.new((v1, v2, v3, v4))
        f.material_index = slot_idx
        # If axis is not Z, we would rotate. Assuming Z-up for anchor.

    # Anchor
    make_socket(Vector((0, 0, 0)), Vector((0, 0, 1)), 8)

    # Joint (Top)
    make_socket(Vector((0, prop_run, prop_height)), Vector((0, 0, 1)), 9)

    # 5. CLEANUP
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


# ==============================================================================
# OPERATOR
# ==============================================================================
class MASSA_OT_ArchStairsIndustrial(bpy.types.Operator):
    bl_idname = "massa.arch_stairs_industrial"
    bl_label = "Build Industrial Staircase"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mesh = bpy.data.meshes.new(CARTRIDGE_META["name"])
        obj = bpy.data.objects.new(CARTRIDGE_META["name"], mesh)
        context.collection.objects.link(obj)

        bm = bmesh.new()
        build_shape(bm)
        bm.to_mesh(mesh)
        bm.free()

        # Initialize Slots
        meta = get_slot_meta()
        for i in range(10):
            if i in meta:
                mat_name = meta[i]["name"]
                mat = bpy.data.materials.get(mat_name)
                if not mat:
                    mat = bpy.data.materials.new(mat_name)
                obj.data.materials.append(mat)
            else:
                obj.data.materials.append(None)

        return {"FINISHED"}


def register():
    bpy.utils.register_class(MASSA_OT_ArchStairsIndustrial)


def unregister():
    bpy.utils.unregister_class(MASSA_OT_ArchStairsIndustrial)


if __name__ == "__main__":
    register()
