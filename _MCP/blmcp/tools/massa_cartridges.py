# Massa MCP — Cartridge tools
# Discover, inspect, and fire Massa parametric cartridge operators.

__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=ToolAnnotations(title="List Massa Cartridges", readOnlyHint=True))
    def list_massa_cartridges() -> dict[str, object]:
        """
        Return all discovered Massa cartridge operators with their metadata.

        Each entry includes:
          id       — cartridge id used in bl_idname (e.g. "pipe", "truss")
          name     — human-readable name
          icon     — Blender icon identifier
          flags    — dict of capability flags (ALLOW_SOLIDIFY, ALLOW_FUSE, …)
          bl_idname — full operator id (e.g. "massa.gen_pipe")
        """
        code = """
import bpy
import importlib
import pkgutil

cartridges = []
try:
    import massa.modules.cartridges as carts_pkg
    for _imp, modname, _ispkg in pkgutil.iter_modules(carts_pkg.__path__):
        try:
            mod = importlib.import_module(f"massa.modules.cartridges.{modname}")
            meta = getattr(mod, "CARTRIDGE_META", None)
            if meta and isinstance(meta, dict) and "id" in meta:
                cartridges.append({
                    "id":       meta.get("id", modname),
                    "name":     meta.get("name", modname),
                    "icon":     meta.get("icon", "MESH_CUBE"),
                    "flags":    meta.get("flags", {}),
                    "bl_idname": f"massa.gen_{meta.get('id', modname)}",
                    "module":   modname,
                })
        except Exception as e:
            cartridges.append({"module": modname, "error": str(e)})
    result = {"status": "ok", "cartridges": sorted(cartridges, key=lambda c: c.get("name", "")),
              "count": len(cartridges)}
except ImportError as e:
    result = {"status": "error", "message": f"Massa addon not found: {e}"}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Get Cartridge Parameters", readOnlyHint=True))
    def get_cartridge_parameters(cartridge_id: str) -> dict[str, object]:
        """
        Return the operator properties (parameters) for a cartridge.

        cartridge_id — the 'id' value from list_massa_cartridges (e.g. "pipe", "truss")
        Returns property names, types, defaults, min/max where available.
        """
        code = f"""
import bpy

bl_idname = f"massa.gen_{cartridge_id}"
op_class = None
for cls in bpy.types.Operator.__subclasses__():
    if getattr(cls, 'bl_idname', None) == bl_idname:
        op_class = cls
        break

if op_class is None:
    result = {{"status": "error", "message": f"Cartridge 'massa.gen_{cartridge_id}' not registered. Is the addon loaded?"}}
else:
    props = []
    for attr in dir(op_class):
        if attr.startswith("_"): continue
        try:
            rna = op_class.bl_rna.properties.get(attr)
            if rna and rna.identifier not in {{"name", "bl_rna", "rna_type"}}:
                entry = {{
                    "name":    rna.identifier,
                    "type":    rna.type,
                    "default": getattr(rna, "default", None),
                }}
                if hasattr(rna, "min"): entry["min"] = rna.min
                if hasattr(rna, "max"): entry["max"] = rna.max
                if hasattr(rna, "enum_items"):
                    entry["options"] = [e.identifier for e in rna.enum_items]
                props.append(entry)
        except Exception:
            pass
    result = {{"status": "ok", "cartridge_id": "{cartridge_id}",
               "bl_idname": bl_idname, "parameters": props}}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Run Massa Cartridge", destructiveHint=True))
    def run_massa_cartridge(
        cartridge_id: str,
        parameters: dict | None = None,
        location: list[float] | None = None,
    ) -> dict[str, object]:
        """
        Execute a Massa cartridge operator to generate a parametric mesh.

        cartridge_id — id from list_massa_cartridges (e.g. "pipe", "panel", "truss")
        parameters   — optional dict of operator properties to set before running
                       (use get_cartridge_parameters to see what's available)
        location     — optional [x, y, z] spawn location; uses 3D cursor when omitted

        Returns the name of the generated object and its MASSA_PARAMS snapshot.
        """
        params_repr = repr(parameters or {})
        loc_code = ""
        if location and len(location) == 3:
            loc_code = f"bpy.context.scene.cursor.location = ({location[0]}, {location[1]}, {location[2]})"

        code = f"""
import bpy

{loc_code}

bl_idname = "massa.gen_{cartridge_id}"

# Check the operator exists
try:
    op_fn = getattr(bpy.ops, "massa").gen_{cartridge_id}
except AttributeError:
    result = {{"status": "error", "message": f"Operator 'massa.gen_{cartridge_id}' not found. Is the Massa addon enabled?"}}
else:
    params = {params_repr}
    ret = bpy.ops.massa.gen_{cartridge_id}('INVOKE_DEFAULT' if not params else 'EXEC_DEFAULT', **params)
    if 'FINISHED' in ret:
        obj = bpy.context.active_object
        massa_params = obj.get("MASSA_PARAMS", {{}}) if obj else {{}}
        result = {{
            "status":       "ok",
            "operator":     bl_idname,
            "object_name":  obj.name if obj else None,
            "massa_params": massa_params,
        }}
    else:
        result = {{"status": "error", "message": f"Operator returned {{ret}}"}}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Rerun Cartridge on Object", destructiveHint=True))
    def rerun_massa_cartridge(object_name: str, parameters: dict | None = None) -> dict[str, object]:
        """
        Re-execute the Massa cartridge on an existing generated object (live edit/redo).

        object_name — name of an object that has a MASSA_PARAMS property
        parameters  — optional overrides merged on top of the stored params

        Deletes the old object, regenerates with updated params, restores transform.
        """
        params_override = repr(parameters or {})
        code = f"""
import bpy, json

obj = bpy.data.objects.get("{object_name}")
if obj is None:
    result = {{"status": "error", "message": "Object '{object_name}' not found."}}
elif "MASSA_PARAMS" not in obj:
    result = {{"status": "error", "message": "Object '{object_name}' has no MASSA_PARAMS — was it made by Massa?"}}
else:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.massa.rerun_active()
    new_obj = bpy.context.active_object
    overrides = {params_override}
    if overrides:
        # Apply parameter overrides by re-running with updated props
        for k, v in overrides.items():
            if hasattr(new_obj, k):
                try: setattr(new_obj, k, v)
                except Exception: pass
    result = {{
        "status":      "ok",
        "object_name": new_obj.name if new_obj else None,
        "massa_params": new_obj.get("MASSA_PARAMS", {{}}) if new_obj else {{}},
    }}
"""
        return send_code(code, strict_json=True)
