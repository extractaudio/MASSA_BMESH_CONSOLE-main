import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_07: Vending Machine",
    "id": "asm_07_vending",
    "icon": "MOD_BOOLEAN",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmVending(Massa_OT_Base):
    bl_idname = "massa.gen_asm_07_vending"
    bl_label = "ASM_07: Vending Machine"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=1.2, min=0.8)
    depth: FloatProperty(name="Depth (Y)", default=0.8, min=0.5)
    height: FloatProperty(name="Height (Z)", default=2.0, min=1.5)

    shelves_count: IntProperty(name="Shelves", default=5, min=1)
    inset_depth: FloatProperty(name="Inset Depth", default=0.1, min=0.05)

    def get_slot_meta(self):
        return {
            0: {"name": "Chassis", "uv": "SKIP", "phys": "PLASTIC"},
            1: {"name": "Glass Display", "uv": "SKIP", "phys": "GLASS_PANE"},
            2: {"name": "Delivery Chute", "uv": "SKIP", "phys": "METAL_PAINTED"},
            3: {"name": "Shelves", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            9: {"name": "Socket Base", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "shelves_count")
        col.prop(self, "inset_depth")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, d, h = self.width, self.depth, self.height

        # 1. Box Chassis
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, h/2), verts=bm.verts)

        for f in bm.faces:
            f.material_index = 0 # Chassis

        # 2. Inset Front Face
        bm.faces.ensure_lookup_table()
        front_face = None
        # Front is -Y direction usually? Or +Y?
        # Standard in Blender is -Y is front view? No, -Y is front in 3D view numpad 1.
        # Let's assume -Y is front.
        for f in bm.faces:
            if f.normal.y < -0.9:
                front_face = f
                break

        if front_face:
            res = bmesh.ops.inset_individual(bm, faces=[front_face], thickness=self.inset_depth, depth=0.0)
            
            if res.get('faces'):
                inner_face = res['faces'][0]

                # 3. Split Top and Bottom
                # Bisect horizontally at 1/3 height from bottom
                res_bisect = bmesh.ops.bisect_plane(
                    bm,
                    geom=[inner_face] + list(inner_face.edges) + list(inner_face.verts), # Just the inner face
                    dist=0.0001,
                    plane_co=(0, 0, h * 0.3),
                    plane_no=(0, 0, 1),
                    use_snap_center=False,
                    clear_outer=False,
                    clear_inner=False
                )

                # Identify the two new faces
                # geom_cut contains the new edges/verts.
                # We need to find the faces again.
                bm.faces.ensure_lookup_table()
                top_face = None
                bottom_face = None
    
                # Search among faces that were part of inner_face or created from it.
                # Easiest is to search by position and normal
                for f in bm.faces:
                    if f.normal.y < -0.9 and abs(f.calc_center_median().y - (-d/2)) < 0.01:
                        if f != front_face: # It's the inset ones
                            if f.calc_center_median().z > h * 0.3:
                                top_face = f
                            else:
                                bottom_face = f
    
                if top_face:
                    # 4. Angled Glass Display
                    # Push the top edge of top_face backwards? Or the whole face backwards?
                    # "Push the top half backward for an angled glass display"
                    # This usually means the glass is angled.
                    # Let's extrude it inwards first?
                    # Or just move the vertices.
    
                    # Let's move top_face inwards (backwards in Y)
                    bmesh.ops.translate(bm, vec=(0, d*0.2, 0), verts=top_face.verts)
                    top_face.material_index = 1 # Glass
    
                    # Add Shelves inside
                    # Simple lines across the glass face?
                    # Or actual geometry inside.
                    # Since we moved the face back, we created a recess.
                    # Let's add shelf planes.
    
                    if self.shelves_count > 0:
                        # Create shelves behind the glass?
                        # Let's just create horizontal cuts on the glass face for visual
                        shelf_h = (h - h*0.3) / (self.shelves_count + 1)
                        for i in range(1, self.shelves_count + 1):
                            z = h*0.3 + i * shelf_h
                            bmesh.ops.bisect_plane(
                                bm,
                                geom=[top_face] + list(top_face.edges) + list(top_face.verts),
                                dist=0.0001,
                                plane_co=(0, 0, z),
                                plane_no=(0, 0, 1)
                            )
                        # Set shelf edges/faces?
                        # The bisect splits the face.
                        # We can inset them to make frames?
                        # Let's just leave it as split glass panels.
    
                if bottom_face:
                    # 5. Delivery Chute
                    # Push inward
                    bmesh.ops.translate(bm, vec=(0, d*0.1, 0), verts=bottom_face.verts)
                    bottom_face.material_index = 2 # Chute
    
                    # Extrude it inward to make a hole?
                    res_ext = bmesh.ops.extrude_face_region(bm, geom=[bottom_face])
                    verts_ext = [v for v in res_ext['geom'] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, verts=verts_ext, vec=(0, d*0.2, 0))
                    # Delete the face to make a hole?
                    # Or keep it as the back of the chute.
                    # Keep it.

        # 6. Sockets at Front Base
        # "Sockets emitted at the front base to snap flush with sidewalks."
        # Create small faces at the bottom front.

        # Front bottom edge is at y = -d/2, z = 0
        sock_size = 0.1

        # Create a socket face
        ret = bmesh.ops.create_grid(bm, size=sock_size, x_segments=1, y_segments=1)
        
        sock_face = None
        if ret.get('faces'):
            sock_face = ret['faces'][0]
        elif ret.get('verts'):
            # Fallback for some blender versions where faces key might be missing for simple grids
            sock_face = ret['verts'][0].link_faces[0]
            
        if sock_face:
            sock_face.material_index = 9
    
            # Position it at bottom center front, facing -Y? Or facing -Z (down) to snap to sidewalk?
            # "snap flush with sidewalks" implies the socket is on the bottom.
    
            # Rotate 180 deg around Y to face down (-Z)
            bmesh.ops.rotate(bm, verts=sock_face.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(180), 3, 'Y'))
    
            # Position at bottom center front (Z=0)
            # Location: (0, -d/2 + 0.2, 0.0)
            bmesh.ops.translate(bm, vec=(0, -d/2 + 0.2, 0.0), verts=sock_face.verts)

        # 7. UV Mapping (Strict Box)
        uv_layer = bm.loops.layers.uv.verify()

        for f in bm.faces:
            for l in f.loops:
                nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)

                scale_val = 1.0

                if nz > 0.5:
                    u, v = l.vert.co.x, l.vert.co.y
                elif ny > 0.5:
                    u, v = l.vert.co.x, l.vert.co.z
                else:
                    u, v = l.vert.co.y, l.vert.co.z

                # Apply offsets/scales if needed
                l[uv_layer].uv = (u * scale_val, v * scale_val)
