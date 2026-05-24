# Massa MCP — Seam tracer & selection-driven slot tools
#
# Workflow:
#   1. User enters Edit Mode on a mesh and selects edges / faces using
#      Blender's native tools (Alt+click for loops, Ctrl+click for
#      shortest path, box-select, lasso, etc.).
#   2. Agent calls get_selected_geometry to read what is highlighted,
#      with full local + world-space precision.
#   3. Agent calls one of the assignment tools to act on that selection:
#      - assign_edge_slot_to_selection         (seam tracing, edge slots 1-5)
#      - assign_face_material_slot_to_selection (face -> material slot)
#      - create_socket_at_selected_face         (Empty at face for socket mount)
#
# The selection IS the input. No index round-trip required.

__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


_EDGE_SLOT_ACTIONS = ("SEAM", "SHARP", "BOTH", "CREASE", "BEVEL", "IGNORE")


def register(mcp: FastMCP) -> None:

    # ------------------------------------------------------------------
    # READ tool — the careful one. Returns everything the agent needs to
    # confirm what the user has highlighted before acting.
    # ------------------------------------------------------------------

    @mcp.tool(annotations=ToolAnnotations(title="Get Selected Geometry", readOnlyHint=True))
    def get_selected_geometry(
        object_name: str = "",
        include_world_coords: bool = True,
        coord_precision: int = 6,
    ) -> dict[str, object]:
        """
        Return precise geometry data for every selected element on a mesh.

        Reads the live edit-mesh while in Edit Mode (the recommended path);
        falls back to the persisted selection on the mesh data when in
        Object Mode.

        For each selected vertex, edge, and face this returns:
          - index in the mesh
          - co_local  — object-space coordinates
          - co_world  — world-space coordinates (matrix_world applied)
          - topology  — edges: vertex indices; faces: vertex loop
          - geometry  — edge length, face area, face normal (local + world)
          - midpoint  — for edges
          - current_edge_slot — value of the MASSA_EDGE_SLOTS int layer
          - is_seam / is_sharp / bevel_weight / crease — current edge marks
          - material_index — for faces

        Also returns:
          - mode, in_edit_mode, select_mode  — Blender's current state
          - active_element — last-picked element ({type, index}) for
            "this exact one" intent
          - world_matrix — object's matrix_world (4x4 row list)
          - stats — selected counts + total mesh counts

        Use this BEFORE calling any of the assignment tools, so the agent
        can confirm what is highlighted. If nothing is selected, all
        arrays are empty and stats reflect zero.

        object_name           — target object; uses the active edit object
                                when empty, falling back to the active object
        include_world_coords  — set False to skip world-space transforms
                                (faster, smaller payload)
        coord_precision       — decimal places to round coordinates to
        """
        # NOTE: the entire body runs inside Blender; values are inlined.
        code = f"""
import bpy, bmesh
from mathutils import Vector

obj_name        = "{object_name}"
include_world   = {include_world_coords!r}
prec            = {int(coord_precision)}

# ---- resolve target object ----
if obj_name:
    obj = bpy.data.objects.get(obj_name)
elif bpy.context.edit_object is not None:
    obj = bpy.context.edit_object
else:
    obj = bpy.context.active_object

if obj is None:
    result = {{"status": "error", "message": "No object specified or active."}}
elif obj.type != 'MESH':
    result = {{"status": "error",
               "message": "Object '" + obj.name + "' is type " + obj.type + ", expected MESH."}}
else:
    in_edit = (bpy.context.edit_object is obj) or (obj.mode == 'EDIT')

    bm = None
    owns_bm = False
    try:
        if in_edit:
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            owns_bm = True

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        slot_layer   = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        bevel_layer  = bm.edges.layers.float.get("bevel_weight_edge")
        crease_layer = bm.edges.layers.float.get("crease_edge")

        mw    = obj.matrix_world
        mw_rs = mw.to_3x3()   # rotation/scale part for normals

        def r(v):
            return round(float(v), prec)
        def vec_l(c):
            return [r(c.x), r(c.y), r(c.z)]
        def vec_w(c):
            w = mw @ c
            return [r(w.x), r(w.y), r(w.z)]
        def nrm_w(n):
            wn = (mw_rs @ n)
            if wn.length > 0:
                wn = wn.normalized()
            return [r(wn.x), r(wn.y), r(wn.z)]

        # ---- vertices ----
        sel_verts = []
        for v in bm.verts:
            if not v.select:
                continue
            entry = {{
                "index":    v.index,
                "co_local": vec_l(v.co),
                "is_boundary":  v.is_boundary,
                "edge_count": len(v.link_edges),
            }}
            if include_world:
                entry["co_world"] = vec_w(v.co)
            sel_verts.append(entry)

        # ---- edges ----
        sel_edges = []
        for e in bm.edges:
            if not e.select:
                continue
            va, vb = e.verts
            mid = (va.co + vb.co) * 0.5
            entry = {{
                "index":             e.index,
                "vert_indices":      [va.index, vb.index],
                "v_co_local":        [vec_l(va.co), vec_l(vb.co)],
                "midpoint_local":    vec_l(mid),
                "length":            r(e.calc_length()),
                "is_seam":           bool(e.seam),
                "is_sharp":          (not bool(e.smooth)),
                "is_boundary":       e.is_boundary,
                "current_edge_slot": (e[slot_layer] if slot_layer is not None else 0),
                "face_count":        len(e.link_faces),
            }}
            if include_world:
                entry["v_co_world"]     = [vec_w(va.co), vec_w(vb.co)]
                entry["midpoint_world"] = vec_w(mid)
            if bevel_layer is not None:
                entry["bevel_weight"] = r(e[bevel_layer])
            if crease_layer is not None:
                entry["crease"] = r(e[crease_layer])
            sel_edges.append(entry)

        # ---- faces ----
        sel_faces = []
        for f in bm.faces:
            if not f.select:
                continue
            center = f.calc_center_median()
            entry = {{
                "index":          f.index,
                "vert_indices":   [v.index for v in f.verts],
                "loop_count":     len(f.verts),
                "center_local":   vec_l(center),
                "normal_local":   vec_l(f.normal),
                "area":           r(f.calc_area()),
                "material_index": f.material_index,
                "is_smooth":      bool(f.smooth),
            }}
            if include_world:
                entry["center_world"] = vec_w(center)
                entry["normal_world"] = nrm_w(f.normal)
            sel_faces.append(entry)

        # ---- active element (last clicked) ----
        active = None
        if in_edit and len(bm.select_history) > 0:
            ah = bm.select_history[-1]
            if isinstance(ah, bmesh.types.BMVert):
                active = {{"type": "VERT", "index": ah.index}}
            elif isinstance(ah, bmesh.types.BMEdge):
                active = {{"type": "EDGE", "index": ah.index}}
            elif isinstance(ah, bmesh.types.BMFace):
                active = {{"type": "FACE", "index": ah.index}}

        # ---- select mode ----
        if in_edit:
            sm_tuple = bm.select_mode
            select_mode_names = []
            if 'VERT' in sm_tuple: select_mode_names.append('VERT')
            if 'EDGE' in sm_tuple: select_mode_names.append('EDGE')
            if 'FACE' in sm_tuple: select_mode_names.append('FACE')
        else:
            select_mode_names = []

        world_matrix = None
        if include_world:
            world_matrix = [[r(x) for x in row] for row in mw]

        result = {{
            "status":          "ok",
            "object":          obj.name,
            "mode":            bpy.context.mode,
            "in_edit_mode":    in_edit,
            "select_mode":     select_mode_names,
            "active_element":  active,
            "world_matrix":    world_matrix,
            "selected": {{
                "verts": sel_verts,
                "edges": sel_edges,
                "faces": sel_faces,
            }},
            "stats": {{
                "selected_vert_count": len(sel_verts),
                "selected_edge_count": len(sel_edges),
                "selected_face_count": len(sel_faces),
                "total_verts":         len(bm.verts),
                "total_edges":         len(bm.edges),
                "total_faces":         len(bm.faces),
                "massa_edge_slot_layer_present": (slot_layer is not None),
            }},
        }}
    finally:
        if owns_bm and bm is not None:
            bm.free()
"""
        return send_code(code, strict_json=True)

    # ------------------------------------------------------------------
    # WRITE — edge slot assignment (seam tracing)
    # ------------------------------------------------------------------

    @mcp.tool(annotations=ToolAnnotations(title="Assign Edge Slot to Selection", destructiveHint=True))
    def assign_edge_slot_to_selection(
        slot: int,
        action: str = "SEAM",
        object_name: str = "",
    ) -> dict[str, object]:
        """
        Write a Massa edge-slot number to every currently selected edge,
        and optionally apply the geometric action immediately.

        The slot value is stored on the MASSA_EDGE_SLOTS bmesh int layer.
        On the next cartridge re-run, Massa's engine reads this layer and
        applies the edge_slot_N_action property defined on the operator.
        This tool can ALSO apply the action right now (live) so the user
        sees the result without rerunning.

        Workflow:
          1. Enter Edit Mode on the target mesh.
          2. Select edges (Alt+click for a loop, Ctrl+click for shortest
             path between two selected verts, etc.).
          3. Call get_selected_geometry to confirm.
          4. Call this tool.

        slot   — edge slot number (1-5); 0 clears the assignment
        action — one of:
                   SEAM   — mark UV seam (edge.seam = True)
                   SHARP  — mark sharp edge (edge.smooth = False)
                   BOTH   — apply SEAM and SHARP
                   CREASE — set full crease weight (1.0)
                   BEVEL  — set full bevel weight (1.0)
                   IGNORE — write the slot number only; do not touch
                            seam / sharp / crease / bevel attributes
        object_name — target object; uses the active edit object when empty

        Returns the list of affected edge indices.
        """
        if action not in _EDGE_SLOT_ACTIONS:
            return {
                "status": "error",
                "message": "action must be one of {}".format(list(_EDGE_SLOT_ACTIONS)),
            }
        if slot < 0 or slot > 5:
            return {"status": "error", "message": "slot must be in 0-5 (0 clears)"}

        code = f"""
import bpy, bmesh

obj_name = "{object_name}"
slot     = {int(slot)}
action   = "{action}"

if obj_name:
    obj = bpy.data.objects.get(obj_name)
else:
    obj = bpy.context.edit_object or bpy.context.active_object

if obj is None or obj.type != 'MESH':
    result = {{"status": "error", "message": "No mesh object available."}}
elif obj.mode != 'EDIT':
    result = {{"status": "error",
               "message": "Object '" + obj.name + "' must be in Edit Mode. "
                          "Enter Edit Mode and select edges first."}}
else:
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()

    slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    if slot_layer is None:
        slot_layer = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

    bevel_layer = None
    crease_layer = None
    if action == "CREASE":
        crease_layer = bm.edges.layers.float.get("crease_edge")
        if crease_layer is None:
            crease_layer = bm.edges.layers.float.new("crease_edge")
    if action == "BEVEL":
        bevel_layer = bm.edges.layers.float.get("bevel_weight_edge")
        if bevel_layer is None:
            bevel_layer = bm.edges.layers.float.new("bevel_weight_edge")

    affected = []
    for e in bm.edges:
        if not e.select:
            continue
        e[slot_layer] = slot
        if action == "SEAM" or action == "BOTH":
            e.seam = True
        if action == "SHARP" or action == "BOTH":
            e.smooth = False
        if action == "CREASE":
            e[crease_layer] = 1.0
        if action == "BEVEL":
            e[bevel_layer] = 1.0
        # IGNORE: write slot only, leave edge attrs alone
        affected.append(e.index)

    bmesh.update_edit_mesh(obj.data)

    if not affected:
        result = {{"status": "error",
                   "message": "No edges are selected. Select edges in Edit Mode first."}}
    else:
        result = {{
            "status":          "ok",
            "object":          obj.name,
            "slot":            slot,
            "action":          action,
            "edges_affected":  affected,
            "count":           len(affected),
        }}
"""
        return send_code(code, strict_json=True)

    # ------------------------------------------------------------------
    # WRITE — face -> material slot assignment
    # ------------------------------------------------------------------

    @mcp.tool(annotations=ToolAnnotations(title="Assign Material Slot to Selected Faces", destructiveHint=True))
    def assign_face_material_slot_to_selection(
        slot_index: int,
        object_name: str = "",
    ) -> dict[str, object]:
        """
        Set material_index on every selected face. This is what drives
        Massa's slot manifest (UV strategy, physics material, socket flag)
        once the cartridge runs.

        Workflow:
          1. Enter Edit Mode and select faces.
          2. Ensure the target slot exists on the object (append a
             material slot first if needed; this tool fails otherwise).
          3. Call this tool.

        slot_index  — 0-based material slot index on the mesh
        object_name — target object; uses the active edit object when empty

        Returns the list of affected face indices and the material name
        currently assigned to that slot (if any).
        """
        if slot_index < 0:
            return {"status": "error", "message": "slot_index must be >= 0"}

        code = f"""
import bpy, bmesh

obj_name   = "{object_name}"
slot_index = {int(slot_index)}

if obj_name:
    obj = bpy.data.objects.get(obj_name)
else:
    obj = bpy.context.edit_object or bpy.context.active_object

if obj is None or obj.type != 'MESH':
    result = {{"status": "error", "message": "No mesh object available."}}
elif obj.mode != 'EDIT':
    result = {{"status": "error",
               "message": "Object '" + obj.name + "' must be in Edit Mode."}}
elif slot_index >= len(obj.material_slots):
    result = {{
        "status":  "error",
        "message": "slot_index " + str(slot_index) + " is out of range; "
                   "object has " + str(len(obj.material_slots)) + " material slot(s). "
                   "Append a slot first.",
    }}
else:
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    affected = []
    for f in bm.faces:
        if f.select:
            f.material_index = slot_index
            affected.append(f.index)

    bmesh.update_edit_mesh(obj.data)

    if not affected:
        result = {{"status": "error",
                   "message": "No faces are selected. Switch to face-select mode and select faces."}}
    else:
        ms = obj.material_slots[slot_index]
        mat_name = ms.material.name if ms.material else None
        result = {{
            "status":          "ok",
            "object":          obj.name,
            "slot_index":      slot_index,
            "material_name":   mat_name,
            "faces_affected":  affected,
            "count":           len(affected),
        }}
"""
        return send_code(code, strict_json=True)

    # ------------------------------------------------------------------
    # WRITE — socket Empty creation at selected face(s)
    # ------------------------------------------------------------------

    @mcp.tool(annotations=ToolAnnotations(title="Create Socket Empty at Selected Face", destructiveHint=True))
    def create_socket_at_selected_face(
        socket_name: str = "socket",
        object_name: str = "",
        parent_to_mesh: bool = True,
        align_to_normal: bool = True,
        display_size: float = 0.2,
    ) -> dict[str, object]:
        """
        Create a Blender Empty at the centre of every selected face,
        oriented so its local +Z follows the face normal, and (by default)
        parented to the source mesh. This is the canonical Massa socket
        pattern — face-aligned empties used as mount points.

        Workflow:
          1. Enter Edit Mode and select one or more faces.
          2. Call this tool.

        socket_name      — base name; suffixed _01, _02, ... when multiple
                           faces are selected
        object_name      — target object; uses the active edit object when empty
        parent_to_mesh   — parent each Empty to the source mesh so it
                           follows the mesh through transforms
        align_to_normal  — rotate the Empty so its local +Z aligns with
                           the world-space face normal
        display_size     — Empty arrow display size in Blender units

        Returns one entry per socket with its name, source face index,
        world location, and rotation.
        """
        code = f"""
import bpy, bmesh
from mathutils import Vector, Matrix

obj_name        = "{object_name}"
socket_name     = "{socket_name}"
parent_to_mesh  = {parent_to_mesh!r}
align_to_normal = {align_to_normal!r}
display_size    = {float(display_size)!r}

if obj_name:
    obj = bpy.data.objects.get(obj_name)
else:
    obj = bpy.context.edit_object or bpy.context.active_object

if obj is None or obj.type != 'MESH':
    result = {{"status": "error", "message": "No mesh object available."}}
elif obj.mode != 'EDIT':
    result = {{"status": "error",
               "message": "Object '" + obj.name + "' must be in Edit Mode "
                          "with face(s) selected."}}
else:
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    mw    = obj.matrix_world
    mw_rs = mw.to_3x3()

    selected = [f for f in bm.faces if f.select]
    if not selected:
        result = {{"status": "error",
                   "message": "No faces are selected. Switch to face-select mode."}}
    else:
        created = []
        multi   = (len(selected) > 1)
        for i, f in enumerate(selected):
            center_world = mw @ f.calc_center_median()

            if align_to_normal:
                z = (mw_rs @ f.normal)
                if z.length == 0:
                    z = Vector((0.0, 0.0, 1.0))
                else:
                    z = z.normalized()
                up = Vector((0.0, 0.0, 1.0)) if abs(z.z) < 0.95 else Vector((1.0, 0.0, 0.0))
                x = up.cross(z).normalized()
                y = z.cross(x).normalized()
                rot_mat = Matrix((x, y, z)).transposed().to_4x4()
            else:
                rot_mat = Matrix.Identity(4)

            name = (socket_name + ("_{{:02d}}".format(i + 1) if multi else ""))
            empty = bpy.data.objects.new(name, None)
            empty.empty_display_type = 'ARROWS'
            empty.empty_display_size = display_size
            bpy.context.collection.objects.link(empty)

            world_mat = Matrix.Translation(center_world) @ rot_mat
            if parent_to_mesh:
                empty.parent = obj
                empty.matrix_world = world_mat
            else:
                empty.matrix_world = world_mat

            created.append({{
                "name":           empty.name,
                "face_index":     f.index,
                "location_world": [round(c, 6) for c in empty.matrix_world.translation],
                "rotation_euler": [round(c, 6) for c in empty.rotation_euler],
                "parent":         (obj.name if parent_to_mesh else None),
            }})

        result = {{
            "status":           "ok",
            "object":           obj.name,
            "sockets_created":  created,
            "count":            len(created),
        }}
"""
        return send_code(code, strict_json=True)
