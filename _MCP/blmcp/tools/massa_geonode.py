# Massa MCP — Geometry Nodes tools
# Create, configure, and query Geometry Nodes modifiers on objects.

__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations=ToolAnnotations(title="List GeoNode Groups", readOnlyHint=True))
    def list_geonode_groups() -> dict[str, object]:
        """
        Return all Geometry Nodes node groups currently loaded in the .blend file.

        Each entry shows the group name and its input socket names + types.
        Use these names with apply_geonode_modifier.
        """
        code = """
import bpy
groups = []
for ng in bpy.data.node_groups:
    if ng.type != 'GEOMETRY':
        continue
    inputs = []
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            inputs.append({"name": item.name, "type": item.bl_socket_idname})
    groups.append({"name": ng.name, "inputs": inputs})
result = {"status": "ok", "groups": sorted(groups, key=lambda g: g["name"]), "count": len(groups)}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Apply GeoNode Modifier", destructiveHint=True))
    def apply_geonode_modifier(
        node_group: str,
        object_name: str = "",
        inputs: dict | None = None,
        modifier_name: str = "",
    ) -> dict[str, object]:
        """
        Add a Geometry Nodes modifier using the named node group to an object.

        node_group    — name of the node group (from list_geonode_groups)
        object_name   — target object; uses the active object when empty
        inputs        — dict of {input_name: value} to set on the modifier
        modifier_name — custom modifier name; defaults to the node group name

        Returns the modifier name and a summary of applied input values.
        """
        inputs_repr = repr(inputs or {})
        mod_name = modifier_name or node_group

        code = f"""
import bpy

obj_name = "{object_name}"
obj = bpy.data.objects.get(obj_name) if obj_name else bpy.context.active_object
if obj is None:
    result = {{"status": "error", "message": "No object found."}}
else:
    ng = bpy.data.node_groups.get("{node_group}")
    if ng is None:
        result = {{"status": "error", "message": "Node group '{node_group}' not found. Use list_geonode_groups."}}
    else:
        mod = obj.modifiers.new(name="{mod_name}", type='NODES')
        mod.node_group = ng

        applied = {{}}
        inputs_dict = {inputs_repr}
        for k, v in inputs_dict.items():
            # Try identifier first, then name match
            if k in mod:
                mod[k] = v
                applied[k] = v
            else:
                # Scan interface for matching name
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == k:
                        try:
                            mod[item.identifier] = v
                            applied[item.name] = v
                        except Exception as e:
                            applied[f"ERROR_{{k}}"] = str(e)
                        break

        result = {{
            "status":        "ok",
            "object":        obj.name,
            "modifier":      mod.name,
            "node_group":    ng.name,
            "applied_inputs": applied,
        }}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Set GeoNode Input", destructiveHint=True))
    def set_geonode_input(
        object_name: str,
        modifier_name: str,
        input_name: str,
        value: float | int | bool | str | list,
    ) -> dict[str, object]:
        """
        Update a single input on an existing Geometry Nodes modifier.

        object_name   — name of the target object
        modifier_name — name of the modifier to update
        input_name    — the socket name or identifier to change
        value         — new value (scalar, bool, or [x,y,z] for vectors)
        """
        value_repr = repr(value)
        code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if obj is None:
    result = {{"status": "error", "message": "Object '{object_name}' not found."}}
else:
    mod = obj.modifiers.get("{modifier_name}")
    if mod is None or mod.type != 'NODES':
        result = {{"status": "error", "message": "GeoNode modifier '{modifier_name}' not found on '{object_name}'."}}
    else:
        new_val = {value_repr}
        identifier = "{input_name}"
        # If the raw identifier isn't present, scan by name
        if identifier not in mod:
            ng = mod.node_group
            if ng:
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == identifier:
                        identifier = item.identifier
                        break
        try:
            mod[identifier] = new_val
            result = {{"status": "ok", "object": obj.name, "modifier": mod.name,
                       "input": "{input_name}", "value": new_val}}
        except Exception as e:
            result = {{"status": "error", "message": str(e)}}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Get GeoNode Modifier State", readOnlyHint=True))
    def get_geonode_modifier_state(
        object_name: str = "",
        modifier_name: str = "",
    ) -> dict[str, object]:
        """
        Return current input values for all GeoNode modifiers on an object.

        object_name   — target object; uses the active object when empty
        modifier_name — filter to a specific modifier; returns all GN mods when empty
        """
        code = f"""
import bpy

obj_name = "{object_name}"
mod_filter = "{modifier_name}"
obj = bpy.data.objects.get(obj_name) if obj_name else bpy.context.active_object
if obj is None:
    result = {{"status": "error", "message": "No object found."}}
else:
    modifiers = []
    for mod in obj.modifiers:
        if mod.type != 'NODES': continue
        if mod_filter and mod.name != mod_filter: continue
        inputs = []
        ng = mod.node_group
        if ng:
            for item in ng.interface.items_tree:
                if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                    val = mod.get(item.identifier, None)
                    if hasattr(val, '__iter__') and not isinstance(val, str):
                        val = list(val)
                    inputs.append({{"name": item.name, "identifier": item.identifier, "value": val}})
        modifiers.append({{"name": mod.name, "node_group": ng.name if ng else None, "inputs": inputs}})
    result = {{"status": "ok", "object": obj.name, "modifiers": modifiers}}
"""
        return send_code(code, strict_json=True)
