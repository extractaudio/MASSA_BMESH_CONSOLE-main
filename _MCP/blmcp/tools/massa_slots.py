# Massa MCP — Slot & Edge-Slot tools
# Tag material slots, edge slots, and inspect slot manifests on Massa objects.

__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=ToolAnnotations(title="Get Slot Manifest", readOnlyHint=True))
    def get_slot_manifest(object_name: str = "") -> dict[str, object]:
        """
        Return the material slot manifest for a Massa-generated object.

        Shows each slot's index, name, UV mapping strategy, physics material,
        whether it is a socket slot, and the material currently assigned.

        object_name — target object; uses the active object when empty.
        """
        code = f"""
import bpy, importlib, pkgutil

obj_name = "{object_name}"
obj = bpy.data.objects.get(obj_name) if obj_name else bpy.context.active_object
if obj is None:
    result = {{"status": "error", "message": "No object found."}}
else:
    op_id = obj.get("massa_op_id", "")
    slot_meta = {{}}
    if op_id:
        try:
            import massa.modules.cartridges as carts_pkg
            for _imp, modname, _ispkg in pkgutil.iter_modules(carts_pkg.__path__):
                mod = importlib.import_module(f"massa.modules.cartridges.{{modname}}")
                meta = getattr(mod, "CARTRIDGE_META", {{}})
                if meta.get("id", "") == op_id.replace("massa.gen_", ""):
                    op_cls = getattr(mod, None, None)
                    for cls in bpy.types.Operator.__subclasses__():
                        if getattr(cls, "bl_idname", "") == op_id:
                            try:
                                instance = cls.__new__(cls)
                                slot_meta = instance.get_slot_meta()
                            except Exception:
                                pass
                            break
                    break
        except Exception:
            pass

    slots = []
    for i, ms in enumerate(obj.material_slots):
        entry = {{
            "index": i,
            "material": ms.material.name if ms.material else None,
        }}
        if i in slot_meta:
            sm = slot_meta[i]
            entry.update({{
                "slot_name": sm.get("name", ""),
                "uv":        sm.get("uv", ""),
                "phys":      sm.get("phys", ""),
                "is_socket": sm.get("sock", False),
            }})
        slots.append(entry)
    result = {{
        "status":   "ok",
        "object":   obj.name,
        "op_id":    op_id,
        "slots":    slots,
    }}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Tag Faces to Slot", destructiveHint=True))
    def tag_faces_to_slot(
        object_name: str,
        slot_index: int,
        face_indices: list[int] | None = None,
        select_by_normal: list[float] | None = None,
        normal_threshold: float = 0.5,
    ) -> dict[str, object]:
        """
        Assign faces on a Massa mesh to a material slot.

        object_name        — target mesh object
        slot_index         — material slot index (0-based)
        face_indices       — explicit list of face indices to tag; overrides normal selection
        select_by_normal   — [nx, ny, nz] unit vector; selects faces whose normal aligns within threshold
        normal_threshold   — dot-product threshold for normal-based selection (default 0.5)
        """
        faces_repr  = repr(face_indices)
        normal_repr = repr(select_by_normal)
        code = f"""
import bpy, bmesh
from mathutils import Vector

obj = bpy.data.objects.get("{object_name}")
if obj is None or obj.type != 'MESH':
    result = {{"status": "error", "message": "Mesh object '{object_name}' not found."}}
else:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    face_ids   = {faces_repr}
    normal_vec = {normal_repr}
    threshold  = {normal_threshold}

    tagged = 0
    if face_ids is not None:
        for fi in face_ids:
            if 0 <= fi < len(bm.faces):
                bm.faces[fi].material_index = {slot_index}
                tagged += 1
    elif normal_vec is not None:
        ref = Vector(normal_vec).normalized()
        for f in bm.faces:
            if f.normal.dot(ref) >= threshold:
                f.material_index = {slot_index}
                tagged += 1
    else:
        # Tag all selected faces
        for f in bm.faces:
            if f.select:
                f.material_index = {slot_index}
                tagged += 1

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    result = {{"status": "ok", "object": obj.name, "slot_index": {slot_index}, "faces_tagged": tagged}}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Set Edge Slot Action", destructiveHint=True))
    def set_edge_slot_action(
        object_name: str = "",
        slot: int = 1,
        action: str = "SHARP",
    ) -> dict[str, object]:
        """
        Set the action for an edge slot on a Massa operator instance.

        The change is stored on the operator property and takes effect on
        the next rerun (use rerun_massa_cartridge to regenerate).

        object_name — target Massa object; uses the active object when empty
        slot        — edge slot number 1–5
        action      — one of: SEAM, SHARP, BOTH, CREASE, BEVEL, IGNORE
        """
        valid_actions = {"SEAM", "SHARP", "BOTH", "CREASE", "BEVEL", "IGNORE"}
        code = f"""
import bpy

valid = {repr(valid_actions)}
action = "{action}"
if action not in valid:
    result = {{"status": "error", "message": f"Invalid action '{{action}}'. Choose from: {{sorted(valid)}}"}}
else:
    obj_name = "{object_name}"
    obj = bpy.data.objects.get(obj_name) if obj_name else bpy.context.active_object
    if obj is None:
        result = {{"status": "error", "message": "No object found."}}
    else:
        prop_name = f"edge_slot_{slot}_action"
        params = obj.get("MASSA_PARAMS", {{}})
        if not params:
            result = {{"status": "error", "message": "Object has no MASSA_PARAMS — not a Massa object."}}
        else:
            params[prop_name] = action
            obj["MASSA_PARAMS"] = params
            result = {{"status": "ok", "object": obj.name, "slot": {slot}, "action": action,
                       "note": "Call rerun_massa_cartridge to regenerate with the new edge slot action."}}
"""
        return send_code(code, strict_json=True)
