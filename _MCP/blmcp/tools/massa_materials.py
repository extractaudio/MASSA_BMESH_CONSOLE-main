# Massa MCP — Material tools
# Assign, list, and inspect Massa material presets from MASTER_MAT_DB.

__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=ToolAnnotations(title="List Massa Material Presets", readOnlyHint=True))
    def list_massa_material_presets() -> dict[str, object]:
        """
        Return all available Massa material preset names from MASTER_MAT_DB.

        Use these names with assign_massa_material.
        """
        code = """
import bpy
try:
    from massa.modules.materials import MASTER_MAT_DB
    result = {"presets": sorted(MASTER_MAT_DB.keys()), "count": len(MASTER_MAT_DB)}
except ImportError:
    # Fallback: scan scene materials for massa_ prefix
    names = [m.name for m in bpy.data.materials if m.name.startswith("MAT_")]
    result = {"presets": sorted(names), "count": len(names),
              "note": "MASTER_MAT_DB not found — showing MAT_ materials in scene"}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Assign Massa Material", destructiveHint=True))
    def assign_massa_material(
        preset: str,
        object_name: str = "",
        slot_index: int = 0,
    ) -> dict[str, object]:
        """
        Assign a Massa material preset to a mesh object.

        preset      — name from list_massa_material_presets (e.g. "METAL_STEEL", "RUBBER", "CONCRETE")
        object_name — target object; uses the active object when empty
        slot_index  — material slot index (0-based); new slots are appended as needed
        """
        code = f"""
import bpy
try:
    from massa.modules.materials import MASTER_MAT_DB
    mat = MASTER_MAT_DB.get("{preset}")
except ImportError:
    mat = bpy.data.materials.get("{preset}")

if mat is None:
    result = {{"status": "error", "message": "Unknown preset '{preset}'. Use list_massa_material_presets to see options."}}
else:
    obj_name = "{object_name}"
    obj = bpy.data.objects.get(obj_name) if obj_name else bpy.context.active_object
    if obj is None:
        result = {{"status": "error", "message": "No object found. Pass object_name or select one in Blender."}}
    elif obj.type != 'MESH':
        result = {{"status": "error", "message": f"Object '{{obj.name}}' is type {{obj.type}}, must be MESH."}}
    else:
        while len(obj.data.materials) <= {slot_index}:
            obj.data.materials.append(None)
        obj.data.materials[{slot_index}] = mat
        result = {{"status": "ok", "object": obj.name, "slot": {slot_index}, "material": mat.name}}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Get Object Materials", readOnlyHint=True))
    def get_object_materials(object_name: str = "") -> dict[str, object]:
        """
        Return the material slot list for an object.

        object_name — target object; uses the active object when empty.
        Shows slot index, material name, and whether it is a Massa preset.
        """
        code = f"""
import bpy
try:
    from massa.modules.materials import MASTER_MAT_DB
    massa_names = set(MASTER_MAT_DB.keys())
except ImportError:
    massa_names = set()

obj_name = "{object_name}"
obj = bpy.data.objects.get(obj_name) if obj_name else bpy.context.active_object
if obj is None:
    result = {{"status": "error", "message": "No object found."}}
else:
    slots = []
    for i, slot in enumerate(obj.material_slots):
        mat = slot.material
        slots.append({{
            "index":    i,
            "name":     mat.name if mat else None,
            "is_massa": (mat.name in massa_names) if mat else False,
        }})
    result = {{"status": "ok", "object": obj.name, "slots": slots}}
"""
        return send_code(code, strict_json=True)
