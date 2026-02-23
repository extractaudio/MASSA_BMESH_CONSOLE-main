import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_16: Pressure Vessel",
    "id": "ind_16_pressure_vessel",
    "icon": "MESH_UVSPHERE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndPressureVessel(Massa_OT_Base):
    bl_idname = "massa.gen_ind_16_pressure_vessel"
    bl_label = "IND Pressure Vessel"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # 1. Style Enum
    style: EnumProperty(
        name="Vessel Type",
        items=[
            ("STANDARD", "Sphere Tank", "Spherical pressure vessel"),
            ("CAPSULE", "Vertical Capsule", "Vertical cylindrical tank with hemispherical caps"),
            ("HORIZONTAL", "Horizontal Tank", "Horizontal cylindrical tank on saddle supports"),
        ],
        default="STANDARD"
    )

    # 2. Dimensions
    radius: FloatProperty(name="Radius", default=0.8, min=0.1)
    length: FloatProperty(name="Length/Height", default=2.0, min=0.5)
    leg_height: FloatProperty(name="Leg Height", default=0.5, min=0.0)

    # 3. Details
    cap_radius: FloatProperty(name="Cap Bulge", default=0.8, min=0.1)
    valve_count: IntProperty(name="Valve Count", default=2, min=0, max=8)
    valve_size: FloatProperty(name="Valve Size", default=0.15, min=0.05)
    gauge_count: IntProperty(name="Gauge Count", default=1, min=0, max=4)
    panel_inset: FloatProperty(name="Panel Inset", default=0.02, min=0.0, max=0.2)
    seam_width: FloatProperty(name="Seam Width", default=0.05, min=0.0, max=0.2)
    rim_thickness: FloatProperty(name="Rim Thick", default=0.05, min=0.01, max=0.2)
    socket_size: FloatProperty(name="Socket Base", default=0.2, min=0.1)
    reinforce_rings: IntProperty(name="Ribs", default=2, min=0, max=10)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Tank Body", "uv": "UNWRAP", "phys": "METAL_STEEL"},
            1: {"name": "Fittings", "uv": "BOX", "phys": "METAL_BRASS"},
            2: {"name": "Supports", "uv": "BOX", "phys": "METAL_IRON"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions")
        box.prop(self, "radius")
        if self.style != "STANDARD":
            box.prop(self, "length")
            box.prop(self, "cap_radius")
        box.prop(self, "leg_height")

        box = layout.box()
        box.label(text="Fittings")
        col = box.column(align=True)
        col.prop(self, "valve_count")
        col.prop(self, "valve_size")
        col.prop(self, "gauge_count")
        col.prop(self, "socket_size")

        box = layout.box()
        box.label(text="Details")
        col = box.column(align=True)
        col.prop(self, "reinforce_rings")
        col.prop(self, "seam_width")
        col.prop(self, "panel_inset")
        col.prop(self, "rim_thickness")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        rad = self.radius
        ln = self.length
        legs = self.leg_height

        # 1. Main Tank Body
        if self.style == "STANDARD":
            # Sphere
            ret = bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=rad)
            verts = ret['verts']
            z_off = rad + legs
            bmesh.ops.translate(bm, verts=verts, vec=Vector((0,0,z_off)))

            builder._update()

            # Select all faces and tag Slot 0
            builder.select_all_faces().tag_slot(0)

            # Seam Detail (Equator)
            builder.select_faces_by_height(z_off - 0.1, z_off + 0.1) \
                   .extrude(self.seam_width) \
                   .tag_slot(1)

            # Legs
            for ang in [45, 135, 225, 315]:
                rad_ang = math.radians(ang)
                lx = math.cos(rad_ang) * rad * 0.7
                ly = math.sin(rad_ang) * rad * 0.7
                lz = z_off - rad * 0.7 # Contact point roughly

                builder.create_cylinder(radius=0.1, depth=lz, center=Vector((0,0,0)))
                builder.translate(lx, ly, lz/2) # Cylinder created at origin, center Z is depth/2
                builder.tag_slot(2)

        elif self.style == "CAPSULE":
            # Vertical Cylinder
            cen_z = legs + rad + ln/2

            builder.create_cylinder(radius=rad, depth=ln, center=Vector((0,0,cen_z)))
            builder.tag_slot(0)

            # Top Cap
            builder.select_faces_by_normal(Vector((0,0,1)))

            steps = 4
            step_h = self.cap_radius / steps
            current_r = rad

            for i in range(steps):
                h_curr = (i+1) * step_h
                ratio = h_curr / self.cap_radius
                if ratio >= 1.0: ratio = 0.999
                r_next = rad * math.sqrt(1 - ratio**2)

                builder.extrude(step_h) # Active faces now sides + top

                # Filter to just Top Face for scaling
                builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)

                scale_fac = r_next / current_r if current_r > 0.001 else 0
                scale_active_face_center(builder, scale_fac, scale_fac, 1.0)
                current_r = r_next

            # Bottom Cap
            builder.select_faces_by_height(cen_z - ln/2 - 0.1, cen_z - ln/2 + 0.1) \
                   .select_faces_by_normal(Vector((0,0,-1)))

            current_r = rad
            for i in range(steps):
                h_curr = (i+1) * step_h
                ratio = h_curr / self.cap_radius
                if ratio >= 1.0: ratio = 0.999
                r_next = rad * math.sqrt(1 - ratio**2)

                builder.extrude(step_h)

                # Filter to Bottom Face
                builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1)

                scale_fac = r_next / current_r if current_r > 0.001 else 0
                scale_active_face_center(builder, scale_fac, scale_fac, 1.0)
                current_r = r_next

            # Ribs
            if self.reinforce_rings > 0:
                step_z = ln / (self.reinforce_rings + 1)
                for i in range(self.reinforce_rings):
                    z_ring = (cen_z - ln/2) + (i+1)*step_z
                    builder.create_cylinder(radius=rad + self.rim_thickness, depth=self.seam_width, center=Vector((0,0,z_ring)))
                    builder.tag_slot(2)

            # Legs
            for ang in [0, 90, 180, 270]:
                rad_ang = math.radians(ang)
                lx = math.cos(rad_ang) * rad
                ly = math.sin(rad_ang) * rad

                builder.create_cylinder(radius=0.1, depth=legs, center=Vector((0,0,0)))
                builder.translate(lx, ly, legs/2)
                builder.tag_slot(2)

        elif self.style == "HORIZONTAL":
            # Horizontal Cylinder
            z_off = rad + legs

            builder.create_cylinder(radius=rad, depth=ln, center=Vector((0,0,0)))
            builder.rotate(90, axis='X')
            builder.translate(0, 0, z_off)
            builder.tag_slot(0)

            # +Y Cap
            builder.select_faces_by_normal(Vector((0,1,0)))

            steps = 4
            step_h = self.cap_radius / steps
            current_r = rad

            for i in range(steps):
                h_curr = (i+1) * step_h
                ratio = h_curr / self.cap_radius
                if ratio >= 1.0: ratio = 0.999
                r_next = rad * math.sqrt(1 - ratio**2)

                builder.extrude(step_h)

                # Filter Top (+Y)
                builder.select_faces_by_normal(Vector((0,1,0)), tolerance=0.1)

                scale_fac = r_next / current_r if current_r > 0.001 else 0
                scale_active_face_center(builder, scale_fac, 1.0, scale_fac) # Scale XZ
                current_r = r_next

            # -Y Cap
            # Re-find face at -Y end
            # We know center is z_off. Y is roughly -ln/2.
            # Select by normal -Y and position
            builder.select_all_faces()
            candidates = []
            target_y = -ln/2
            for f in bm.faces:
                c = f.calc_center_median()
                if abs(c.y - target_y) < 0.2 and f.normal.dot(Vector((0,-1,0))) > 0.9:
                    candidates.append(f)
            builder.active_faces = candidates

            current_r = rad
            for i in range(steps):
                h_curr = (i+1) * step_h
                ratio = h_curr / self.cap_radius
                if ratio >= 1.0: ratio = 0.999
                r_next = rad * math.sqrt(1 - ratio**2)

                builder.extrude(step_h)
                builder.select_faces_by_normal(Vector((0,-1,0)), tolerance=0.1)

                scale_fac = r_next / current_r if current_r > 0.001 else 0
                scale_active_face_center(builder, scale_fac, 1.0, scale_fac)
                current_r = r_next

            # Saddles
            saddle_w = rad * 1.6
            saddle_thick = 0.3
            saddle_h = legs + rad * 0.2

            builder.create_box(saddle_w, saddle_thick, saddle_h, center=Vector((0, -ln*0.25, saddle_h/2)))
            builder.tag_slot(2)

            builder.create_box(saddle_w, saddle_thick, saddle_h, center=Vector((0, ln*0.25, saddle_h/2)))
            builder.tag_slot(2)

            # Ribs
            if self.reinforce_rings > 0:
                step_y = ln / (self.reinforce_rings + 1)
                for i in range(self.reinforce_rings):
                    y_ring = -ln/2 + (i+1)*step_y
                    builder.create_cylinder(radius=rad + self.rim_thickness, depth=self.seam_width, center=Vector((0,0,0)))
                    builder.rotate(90, axis='X')
                    builder.translate(0, y_ring, z_off)
                    builder.tag_slot(2)

        # 2. Valves & Details
        if self.style == "STANDARD": top_z = rad*2 + legs
        elif self.style == "CAPSULE": top_z = legs + rad + ln/2 + self.cap_radius
        elif self.style == "HORIZONTAL": top_z = rad + legs + rad

        # Valve Array
        if self.valve_count > 0:
            # Distribute around top center or along line
            # Circular distribution
            for i in range(self.valve_count):
                angle = (i / self.valve_count) * 360
                dist = self.radius * 0.3
                vx = math.cos(math.radians(angle)) * dist
                vy = math.sin(math.radians(angle)) * dist

                builder.create_cylinder(radius=self.valve_size, depth=0.3, center=Vector((0,0,0)))
                builder.translate(vx, vy, top_z + 0.15)
                builder.tag_slot(1)
                # Wheel
                builder.create_cylinder(radius=self.valve_size*1.5, depth=0.05, center=Vector((0,0,0)))
                builder.translate(vx, vy, top_z + 0.3)
                builder.tag_slot(1)

        # Gauges
        if self.gauge_count > 0:
            # Place on side
            center_z = legs + rad
            if self.style == "HORIZONTAL": center_z = rad + legs
            elif self.style == "CAPSULE": center_z = legs + rad + ln/2

            gx_start = rad + 0.1
            for i in range(self.gauge_count):
                # Vertical stack
                gz = center_z - (self.gauge_count-1)*0.15 + i*0.3

                builder.create_cylinder(radius=0.15, depth=0.1, center=Vector((0,0,0)))
                builder.rotate(90, axis='Y')
                builder.translate(gx_start, 0, gz)
                builder.tag_slot(1)

        # Control Panel (Using panel_inset)
        if self.panel_inset > 0:
            # Add a small box on the surface
            # Front side (Y-)
            pz = legs + rad
            if self.style == "HORIZONTAL": pz = legs + rad

            builder.create_box(0.4, 0.1, 0.4, center=Vector((0,0,0)))
            # Inset the face
            # Just place it
            builder.translate(0, -rad - 0.05 + self.panel_inset*0.1, pz) # Embed slightly
            builder.tag_slot(1)

        # 3. Socket Anchor
        min_z = float('inf')
        for f in bm.faces:
            cz = f.calc_center_median().z
            if cz < min_z: min_z = cz

        active_faces = []
        for f in bm.faces:
            cz = f.calc_center_median().z
            if abs(cz - min_z) < 0.1 and f.normal.z < -0.5:
                active_faces.append(f)

        builder.active_faces = active_faces
        builder.tag_socket(9).tag_slot(9)

        # 4. UVs
        builder.select_all_faces().tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.clean()

    def execute(self, context):
        return super().execute(context)

def scale_active_face_center(builder, scale_x, scale_y, scale_z):
    # Helper to scale active faces around their median center
    if not builder.active_faces: return

    # Calculate common center
    center = Vector((0,0,0))
    cnt = 0
    for f in builder.active_faces:
        center += f.calc_center_median()
        cnt += 1
    if cnt > 0: center /= cnt

    # Translate to origin
    builder.translate(-center.x, -center.y, -center.z)
    # Scale
    builder.scale(scale_x, scale_y, scale_z)
    # Translate back
    builder.translate(center.x, center.y, center.z)
