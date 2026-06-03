import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_04: Universal Portal",
    "id": "arc_04_doorway",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_ArcDoorway(Massa_OT_Base):
    bl_idname = "massa.gen_arc_04_doorway"
    bl_label = "ARC Doorway"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    door_width: FloatProperty(name="Width", default=1.0, min=0.1)
    door_height: FloatProperty(name="Height", default=2.1, min=0.1)
    frame_width: FloatProperty(name="Frame W", default=0.1, min=0.01)
    frame_depth: FloatProperty(name="Frame D", default=0.15, min=0.01)

    # Leaf
    leaf_thick: FloatProperty(name="Leaf T", default=0.05, min=0.01)
    open_angle: FloatProperty(name="Open Angle", default=0.0, min=-180, max=180)

    # Hardware
    handle_height: FloatProperty(name="Handle H", default=1.0, min=0.1)

    # UVs
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    # Styles
    door_style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Panel Door"),
            ("SCIFI", "Sci-Fi", "Blast Door / Bulkhead"),
            ("GLASS", "Glass", "Modern Storefront"),
        ],
        default="STANDARD"
    )

    def get_slot_meta(self):
        return {
            0: {"name": "Door Leaf", "uv": "SKIP", "phys": "WOOD_PAINTED"},
            1: {"name": "Frame", "uv": "SKIP", "phys": "WOOD_PAINTED"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "SYNTH_GLASS"},
            7: {"name": "Hardware", "uv": "SKIP", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"},
        }

    def build_shape(self, bm: bmesh.types.BMesh):
        # UV archetypes:
        # - Frame, stops, rails, leaf, and hardware are UV_PRIM_PLANK or BOX_DETAIL.
        # - Glass is UV_PRIM_SHEET.
        # - Sockets are tagged on existing frame faces, not helper geometry.
        dw = self.door_width
        dh = self.door_height
        fw = min(self.frame_width, max(0.01, dw * 0.45))
        fd = self.frame_depth
        lt = min(self.leaf_thick, max(0.01, fd * 0.75))
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = (bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
                      or bm.edges.layers.int.new("MASSA_EDGE_SLOTS"))
        force_seam = (bm.edges.layers.int.get("massa_force_seam")
                      or bm.edges.layers.int.new("massa_force_seam"))
        socket_layer = (bm.faces.layers.int.get("MASSA_SOCKETS")
                        or bm.faces.layers.int.new("MASSA_SOCKETS"))

        assembly_center = Vector((0.0, 0.0, dh * 0.5))
        frame_faces = []
        leaf_verts = set()

        def mark_edge(e, slot=None, seam=False, sharp=False, protect=False):
            if slot is not None:
                e[edge_slots] = slot
            if seam:
                e.seam = True
            if sharp:
                e.smooth = False
            if protect:
                e[force_seam] = 1

        def component_center(verts):
            if not verts:
                return Vector((0.0, 0.0, 0.0))
            total = Vector((0.0, 0.0, 0.0))
            for v in verts:
                total += v.co
            return total / len(verts)

        def occlusion_score(edge, center, parent_center=None):
            edge_center = (edge.verts[0].co + edge.verts[1].co) * 0.5
            score = 0.0
            if parent_center is not None:
                to_core = parent_center - edge_center
                score += max(0.0, 1.0 / max(0.001, to_core.length))

            linked_normal = Vector((0.0, 0.0, 0.0))
            for face in edge.link_faces:
                linked_normal += face.normal
            if linked_normal.length > 0.0001:
                linked_normal.normalize()
                inward = center - edge_center
                if inward.length > 0.0001:
                    score += max(0.0, linked_normal.dot(inward.normalized()))
            return score

        def dominant_axis(size):
            dims = [
                (abs(size.x), Vector((1.0, 0.0, 0.0))),
                (abs(size.y), Vector((0.0, 1.0, 0.0))),
                (abs(size.z), Vector((0.0, 0.0, 1.0))),
            ]
            return max(dims, key=lambda item: item[0])[1]

        def write_uvs(faces, projection="BOX"):
            for face in faces:
                if not face.is_valid:
                    continue
                face.normal_update()
                normal = face.normal
                loop_data = []
                for loop in face.loops:
                    co = loop.vert.co
                    if abs(normal.z) >= 0.5:
                        u, v = co.x, co.y
                    elif abs(normal.x) >= 0.5:
                        u, v = co.y, co.z
                    else:
                        u, v = co.x, co.z
                    loop_data.append((loop, u, v))

                if projection == "FIT" or self.fit_uvs:
                    u_values = [item[1] for item in loop_data]
                    v_values = [item[2] for item in loop_data]
                    min_u, max_u = min(u_values), max(u_values)
                    min_v, max_v = min(v_values), max(v_values)
                    span_u = max(max_u - min_u, 0.0001)
                    span_v = max(max_v - min_v, 0.0001)
                    for loop, u, v in loop_data:
                        loop[uv_layer].uv = ((u - min_u) / span_u, (v - min_v) / span_v)
                else:
                    for loop, u, v in loop_data:
                        loop[uv_layer].uv = (u * self.uv_scale, v * self.uv_scale)

        def mark_plank_component(faces, verts, local_axis, parent_center=None):
            bm.normal_update()
            center = component_center(verts)
            local_axis = local_axis.normalized()
            component_edges = {edge for face in faces for edge in face.edges}
            cap_faces = [
                face for face in faces
                if abs(face.normal.dot(local_axis)) > 0.85
            ]
            cap_edges = set()
            for face in cap_faces:
                for edge in face.edges:
                    cap_edges.add(edge)
                    mark_edge(edge, slot=1, seam=True, sharp=True, protect=True)

            zipper_candidates = []
            for edge in component_edges:
                if edge in cap_edges or len(edge.verts) != 2:
                    continue
                direction = edge.verts[1].co - edge.verts[0].co
                if direction.length > 0.0001 and abs(direction.normalized().dot(local_axis)) > 0.65:
                    zipper_candidates.append(edge)

            if zipper_candidates:
                zipper = max(
                    zipper_candidates,
                    key=lambda edge: occlusion_score(edge, center, parent_center),
                )
                mark_edge(zipper, slot=3, seam=True, protect=True)

            for edge in component_edges:
                if edge[edge_slots] != 0:
                    continue
                if edge.is_manifold and len(edge.link_faces) == 2:
                    try:
                        if edge.calc_face_angle(0.0) > math.radians(45.0):
                            mark_edge(edge, slot=2, sharp=True)
                    except ValueError:
                        continue

        def mark_sheet_component(faces):
            bm.normal_update()
            sheet_faces = [
                face for face in faces
                if abs(face.normal.y) > 0.85
            ] or faces
            for face in sheet_faces:
                for edge in face.edges:
                    mark_edge(edge, slot=1, seam=True, sharp=True, protect=True)

        def create_box_component(center, size, slot, archetype="PLANK", uv_projection="BOX",
                                 parent_center=None, collect_leaf=False):
            ret = bmesh.ops.create_cube(bm, size=1.0)
            verts = list(ret["verts"])
            bmesh.ops.scale(bm, vec=(size.x, size.y, size.z), verts=verts)
            bmesh.ops.translate(bm, vec=center, verts=verts)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            faces = list({face for vert in verts for face in vert.link_faces})

            for face in faces:
                face.material_index = slot
            bm.normal_update()

            if archetype == "SHEET":
                mark_sheet_component(faces)
            else:
                mark_plank_component(faces, verts, dominant_axis(size), parent_center)

            write_uvs(faces, uv_projection)
            if collect_leaf:
                leaf_verts.update(verts)
            return faces, verts

        def add_standard_panel_details(y_sign):
            panel_w = max(0.08, dw - 0.32)
            panel_h = max(0.16, dh - 0.48)
            rail = min(0.035, panel_w * 0.25, panel_h * 0.25)
            y = y_sign * (lt * 0.5 + 0.008)
            zc = dh * 0.53
            top_z = zc + panel_h * 0.5
            bottom_z = zc - panel_h * 0.5
            side_h = max(0.02, panel_h)
            pieces = [
                (Vector((0.0, y, top_z)), Vector((panel_w, 0.012, rail))),
                (Vector((0.0, y, bottom_z)), Vector((panel_w, 0.012, rail))),
                (Vector((-panel_w * 0.5, y, zc)), Vector((rail, 0.012, side_h))),
                (Vector((panel_w * 0.5, y, zc)), Vector((rail, 0.012, side_h))),
            ]
            for center, size in pieces:
                create_box_component(center, size, 0, "BOX_DETAIL", "BOX",
                                     assembly_center, collect_leaf=True)

        # 1. FRAME GENERATION
        for center, size in (
            (Vector((-dw / 2.0 - fw / 2.0, 0.0, dh / 2.0)), Vector((fw, fd, dh))),
            (Vector((dw / 2.0 + fw / 2.0, 0.0, dh / 2.0)), Vector((fw, fd, dh))),
            (Vector((0.0, 0.0, dh + fw / 2.0)), Vector((dw + 2.0 * fw, fd, fw))),
        ):
            faces, _ = create_box_component(center, size, 1, "PLANK", "BOX", assembly_center)
            frame_faces.extend(faces)

        # 2. LEAF GENERATION
        if self.door_style == "GLASS":
            frame_t = min(0.05, max(0.02, dw * 0.2), max(0.02, dh * 0.2))
            rail_specs = [
                (Vector((0.0, 0.0, frame_t / 2.0)), Vector((dw, lt, frame_t))),
                (Vector((0.0, 0.0, dh - frame_t / 2.0)), Vector((dw, lt, frame_t))),
                (Vector((-dw / 2.0 + frame_t / 2.0, 0.0, dh / 2.0)), Vector((frame_t, lt, dh))),
                (Vector((dw / 2.0 - frame_t / 2.0, 0.0, dh / 2.0)), Vector((frame_t, lt, dh))),
            ]
            for center, size in rail_specs:
                create_box_component(center, size, 0, "PLANK", "BOX",
                                     assembly_center, collect_leaf=True)

            glass_w = max(0.01, dw - 2.0 * frame_t)
            glass_h = max(0.01, dh - 2.0 * frame_t)
            create_box_component(
                Vector((0.0, 0.0, dh / 2.0)),
                Vector((glass_w, 0.02, glass_h)),
                3,
                "SHEET",
                "FIT",
                assembly_center,
                collect_leaf=True,
            )

        elif self.door_style == "SCIFI":
            create_box_component(
                Vector((0.0, 0.0, dh / 2.0)),
                Vector((dw, lt * 2.0, dh)),
                0,
                "PLANK",
                "BOX",
                assembly_center,
                collect_leaf=True,
            )
            create_box_component(
                Vector((0.0, lt + 0.01, dh / 2.0)),
                Vector((max(0.1, dw - 0.3), 0.025, max(0.1, dh - 0.3))),
                1,
                "BOX_DETAIL",
                "BOX",
                assembly_center,
                collect_leaf=True,
            )
            create_box_component(
                Vector((0.0, lt + 0.03, dh / 2.0)),
                Vector((0.2, lt * 2.2, 0.4)),
                7,
                "BOX_DETAIL",
                "BOX",
                assembly_center,
                collect_leaf=True,
            )

        else:
            stop_thick, stop_width = 0.02, 0.03
            stop_y_offset = lt / 2.0 + stop_width / 2.0
            stop_specs = [
                (Vector((-dw / 2.0 + stop_thick / 2.0, stop_y_offset, dh / 2.0)),
                 Vector((stop_thick, stop_width, dh))),
                (Vector((dw / 2.0 - stop_thick / 2.0, stop_y_offset, dh / 2.0)),
                 Vector((stop_thick, stop_width, dh))),
                (Vector((0.0, stop_y_offset, dh - stop_thick / 2.0)),
                 Vector((dw, stop_width, stop_thick))),
            ]
            for center, size in stop_specs:
                faces, _ = create_box_component(center, size, 1, "PLANK", "BOX", assembly_center)
                frame_faces.extend(faces)

            create_box_component(
                Vector((0.0, 0.0, dh / 2.0)),
                Vector((dw, lt, dh)),
                0,
                "PLANK",
                "BOX",
                assembly_center,
                collect_leaf=True,
            )
            add_standard_panel_details(1.0)
            add_standard_panel_details(-1.0)

        # 3. HARDWARE
        if self.door_style != "SCIFI":
            handle_z = self.handle_height
            handle_x = dw / 2.0 - 0.1
            handle_y = lt / 2.0 + 0.025
            create_box_component(
                Vector((handle_x, handle_y, handle_z)),
                Vector((0.12, 0.04, 0.02)),
                7,
                "BOX_DETAIL",
                "BOX",
                assembly_center,
                collect_leaf=True,
            )

        # 4. OPEN STATE
        if abs(self.open_angle) > 0.001 and leaf_verts:
            pivot = Vector((-dw / 2.0, 0.0, 0.0))
            matrix = (
                Matrix.Translation(pivot)
                @ Matrix.Rotation(math.radians(self.open_angle), 4, "Z")
                @ Matrix.Translation(-pivot)
            )
            bmesh.ops.transform(bm, matrix=matrix, verts=list(leaf_verts))
            bm.normal_update()

        # 5. SOCKETS ON EXISTING FRAME FACES
        for face in frame_faces:
            if not face.is_valid:
                continue
            face.normal_update()
            if face.normal.y < -0.85:
                face[socket_layer] = 1
                for edge in face.edges:
                    mark_edge(edge, slot=1, seam=True, sharp=True, protect=True)
            elif face.normal.y > 0.85:
                face[socket_layer] = 2
                for edge in face.edges:
                    mark_edge(edge, slot=1, seam=True, sharp=True, protect=True)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="MESH_CUBE")
        col = box.column(align=True)
        col.prop(self, "door_style")
        col.prop(self, "door_width")
        col.prop(self, "door_height")
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")

        box_leaf = layout.box()
        box_leaf.label(text="Leaf & Hardware", icon="MOD_BUILD")
        col = box_leaf.column(align=True)
        col.prop(self, "leaf_thick")
        col.prop(self, "handle_height")

        box_anim = layout.box()
        box_anim.label(text="State", icon="FILE_REFRESH")
        box_anim.prop(self, "open_angle")
