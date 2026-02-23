import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Quaternion
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    FloatVectorProperty,
    EnumProperty,
)
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "Cable Bundle",
    "id": "prop_cables",
    "icon": "CURVE_PATH",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_Cables(Massa_OT_Base):
    bl_idname = "massa.gen_prop_cables"
    bl_label = "Cable Bundle"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. SPAN ---
    length: FloatProperty(name="Span (Y)", default=2.0, min=0.1, unit="LENGTH")
    drop: FloatProperty(name="Height Drop (Z)", default=0.0, unit="LENGTH")

    # --- 2. PHYSICS ---
    slack: FloatProperty(name="Slack", default=0.5, min=0.0, max=5.0)
    resolution: IntProperty(name="Resolution", default=16, min=4, max=64)

    # --- 3. BUNDLE ---
    count: IntProperty(name="Strands", default=5, min=1, max=50)
    radius: FloatProperty(name="Cable Radius", default=0.02, min=0.001, unit="LENGTH")
    spread: FloatProperty(name="Spread", default=0.1, min=0.0)

    # --- 4. TIES ---
    use_ties: BoolProperty(name="Cable Ties", default=True)
    tie_count: IntProperty(name="Tie Count", default=3, min=1)
    tie_scale: FloatProperty(name="Tie Scale", default=1.0, min=0.1)

    # --- 5. VARIATION ---
    seed: IntProperty(name="Seed", default=123)
    rand_slack: FloatProperty(name="Slack Var", default=0.1, min=0.0, max=1.0)

    # --- 6. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Cables", "uv": "TUBE_Y", "phys": "SYNTH_RUBBER"},
            1: {"name": "Ties", "uv": "BOX", "phys": "SYNTH_PLASTIC"},
            9: {"name": "Anchors", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        row = col.row(align=True)
        row.prop(self, "length")
        row.prop(self, "drop")

        col.separator()
        box = col.box()
        box.label(text="Physics", icon="PHYSICS")
        row = box.row(align=True)
        row.prop(self, "slack")
        row.prop(self, "rand_slack", text="Var")
        box.prop(self, "resolution", text="Res")

        col.separator()
        box = col.box()
        box.label(text="Bundle", icon="STRANDS")
        row = box.row(align=True)
        row.prop(self, "count")
        row.prop(self, "radius")
        box.prop(self, "spread")
        box.prop(self, "seed")

        col.separator()
        box = col.box()
        row = box.row()
        row.prop(self, "use_ties", icon="MOD_SHRINKWRAP", toggle=True)
        if self.use_ties:
            row = box.row(align=True)
            row.prop(self, "tie_count", text="Count")
            row.prop(self, "tie_scale", text="Scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        uv_layer = bm.loops.layers.uv.verify()
        rng = random.Random(self.seed)

        # Defines
        p1 = Vector((0, -self.length / 2, 0))
        p2 = Vector((0, self.length / 2, self.drop))

        # Tie Locations (0.0 to 1.0 factors)
        tie_factors = []
        if self.use_ties:
            for _ in range(self.tie_count):
                tie_factors.append(rng.uniform(0.15, 0.85))
            tie_factors.sort()

        # --- GENERATE STRANDS ---
        for i in range(self.count):
            # 1. Randomize Params
            offset_vec = Vector(
                (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
            ).normalized() * (self.spread * rng.uniform(0.5, 1.0))

            # Start/End offsets (tapered bundle effect?)
            # Let's offset the whole curve mostly, but pinch at ties

            this_slack = self.slack * rng.uniform(
                1.0 - self.rand_slack, 1.0 + self.rand_slack
            )

            # 2. Generate Path Points
            path_points = []
            res = self.resolution

            prev_pt = None

            for step in range(res + 1):
                t = step / res

                # Base Catenary
                base_pt = self.calc_catenary(p1, p2, this_slack, t)

                # Apply Pinch
                pinch = self.calc_pinch(t, tie_factors)

                # Final Point
                final_pt = base_pt + (offset_vec * pinch)
                path_points.append(final_pt)

            # 3. Build Mesh Tube (Sweep)
            self.create_tube_from_points(bm, path_points, self.radius, 0, uv_layer)

        # --- GENERATE TIES ---
        if self.use_ties:
            for t in tie_factors:
                # Calculate center of bundle at t
                # We approximate by taking the "main" catenary
                center_pt = self.calc_catenary(p1, p2, self.slack, t)
                next_pt = self.calc_catenary(p1, p2, self.slack, t + 0.01)
                tangent = (next_pt - center_pt).normalized()

                # Create Tie Geometry (Ring)
                # Radius needs to encompass the spread
                tie_rad = self.radius + self.spread * 0.8 * self.tie_scale

                # Build Matrix
                rot_quat = tangent.to_track_quat("Z", "Y")
                mat = Matrix.Translation(center_pt) @ rot_quat.to_matrix().to_4x4()

                # Create Cylinder/Torus
                res = bmesh.ops.create_cone(
                    bm,
                    cap_ends=True,
                    radius1=tie_rad,
                    radius2=tie_rad,
                    depth=self.radius * 4.0,  # Thick band
                    segments=12,
                    matrix=mat,
                )

                for v in res["verts"]:
                    for f in v.link_faces:
                        f.material_index = 1  # Tie Material
                        f.smooth = True

        # 4. Sockets
        self.create_socket(bm, p1, Vector((0, -1, 0)), 9)
        self.create_socket(bm, p2, Vector((0, 1, 0)), 9)

    # --- MATH HELPERS ---

    def calc_catenary(self, p1, p2, slack, t):
        """Standard parabola approximation for catenary"""
        linear = p1.lerp(p2, t)
        dist = (p2 - p1).length
        # Sag vector (Global Z down)
        drop = Vector((0, 0, -1)) * (dist * slack)
        # Parabola: 1 at 0.5, 0 at ends
        sag = 1.0 - math.pow((t - 0.5) * 2, 2)
        return linear + (drop * sag)

    def calc_pinch(self, t, ties):
        """Squeeze factor near ties"""
        if not ties:
            return 1.0
        min_dist = min([abs(t - tie_t) for tie_t in ties])
        pinch_w = 0.1
        if min_dist < pinch_w:
            # Smoothstep-ish interpolation
            fac = min_dist / pinch_w
            return fac * fac * (3 - 2 * fac)  # Smooth pinch
        return 1.0

    def create_tube_from_points(self, bm, points, radius, slot_idx, uv_layer):
        """Sweeps a circle along a list of points"""
        if len(points) < 2:
            return

        segments = 6  # Low poly cables
        prev_verts = []

        # Helper to get rotation frame
        def get_rot(i):
            if i >= len(points) - 1:
                tangent = (points[i] - points[i - 1]).normalized()
            else:
                tangent = (points[i + 1] - points[i]).normalized()
            return tangent.to_track_quat("Z", "Y")

        # 1. Create First Ring
        start_mat = Matrix.Translation(points[0]) @ get_rot(0).to_matrix().to_4x4()

        angle_step = (math.pi * 2) / segments
        for i in range(segments):
            a = i * angle_step
            # Local circle on XY plane
            local = Vector((math.cos(a) * radius, math.sin(a) * radius, 0))
            world = start_mat @ local
            prev_verts.append(bm.verts.new(world))

        # Face Loop
        for i in range(1, len(points)):
            current_mat = (
                Matrix.Translation(points[i]) @ get_rot(i).to_matrix().to_4x4()
            )
            current_verts = []

            # Create new ring
            for s in range(segments):
                a = s * angle_step
                local = Vector((math.cos(a) * radius, math.sin(a) * radius, 0))
                world = current_mat @ local
                current_verts.append(bm.verts.new(world))

            # Bridge
            for s in range(segments):
                v1 = prev_verts[s]
                v2 = prev_verts[(s + 1) % segments]
                v3 = current_verts[(s + 1) % segments]
                v4 = current_verts[s]

                f = bm.faces.new((v1, v2, v3, v4))
                f.material_index = slot_idx
                f.smooth = True

                # UVs: U = Angle, V = Length along curve
                # Simple approximation
                u_min = s / segments
                u_max = (s + 1) / segments
                v_min = (i - 1) / len(points) * self.uv_scale
                v_max = i / len(points) * self.uv_scale

                for loop in f.loops:
                    v = loop.vert
                    if v == v1:
                        loop[uv_layer].uv = (u_min, v_min)
                    elif v == v2:
                        loop[uv_layer].uv = (u_max, v_min)
                    elif v == v3:
                        loop[uv_layer].uv = (u_max, v_max)
                    elif v == v4:
                        loop[uv_layer].uv = (u_min, v_max)

            prev_verts = current_verts

        # Cap Ends? Cables usually open or plugged. Let's leave open for speed.

    def create_socket(self, bm, loc, normal, slot):
        # Visual Helper
        r = self.radius * 2
        t1 = Vector((0, 0, 1)) if abs(normal.z) < 0.9 else Vector((1, 0, 0))
        t2 = normal.cross(t1).normalized() * r
        t1 = normal.cross(t2).normalized() * r
        verts = [
            bm.verts.new(loc + t1),
            bm.verts.new(loc - t1 + t2),
            bm.verts.new(loc - t1 - t2),
        ]
        f = bm.faces.new(verts)
        f.material_index = slot
