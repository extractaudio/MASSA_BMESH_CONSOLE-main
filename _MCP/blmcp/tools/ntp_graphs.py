# NodeToPython graph introspection tools.

__all__ = ("register",)

from pathlib import Path

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

_GRAPH_TYPES = ("MATERIAL", "GEOMETRY", "SHADER", "COMPOSITOR", "WORLD", "LIGHT", "LINESTYLE")


def _vendor_paths() -> tuple[str, str]:
    """Return repo-layout and package-layout vendor roots."""
    tool_path = Path(__file__).resolve()
    mcp_root = tool_path.parents[2]
    package_root = tool_path.parents[1]
    return (
        str(mcp_root / "vendor" / "NodeToPython"),
        str(package_root / "vendor" / "NodeToPython"),
    )


def _common_code(coord_precision: int = 6) -> str:
    prec = max(0, min(int(coord_precision), 12))
    return """
import bpy

PRECISION = __PRECISION__
VALID_GRAPH_TYPES = __GRAPH_TYPES__

def _error(message):
    return {{"status": "error", "message": message}}

def _round(value):
    try:
        return round(float(value), PRECISION)
    except Exception:
        return value

def _plain(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return _round(value)
    if hasattr(value, "name") and hasattr(value, "id_data"):
        return {{"name": value.name, "type": value.__class__.__name__}}
    if hasattr(value, "to_list"):
        return [_plain(v) for v in value.to_list()]
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes, dict)):
        try:
            return [_plain(v) for v in value]
        except Exception:
            pass
    try:
        return str(value)
    except Exception:
        return "<unreadable>"

def _tree_kind(node_tree):
    bl_idname = getattr(node_tree, "bl_idname", "")
    tree_type = getattr(node_tree, "type", "")
    if bl_idname == "GeometryNodeTree" or tree_type == "GEOMETRY":
        return "GEOMETRY"
    if bl_idname == "CompositorNodeTree" or tree_type in {"COMPOSITING", "COMPOSITOR"}:
        return "COMPOSITOR"
    if bl_idname == "ShaderNodeTree" or tree_type == "SHADER":
        return "SHADER"
    return bl_idname or tree_type or "UNKNOWN"

def _matches_group_type(node_tree, graph_type):
    return _tree_kind(node_tree) == graph_type

def _scene_compositor_tree(scene):
    if bpy.app.version >= (5, 0, 0):
        return getattr(scene, "compositing_node_group", None)
    if getattr(scene, "use_nodes", False):
        return getattr(scene, "node_tree", None)
    return None

def _resolve_graph(graph_type, graph_name):
    graph_type = str(graph_type).upper()
    if graph_type not in VALID_GRAPH_TYPES:
        return None, None, "Unsupported graph_type '%s'. Expected one of %s." % (
            graph_type, ", ".join(VALID_GRAPH_TYPES)
        )

    if graph_type == "MATERIAL":
        obj = bpy.data.materials.get(graph_name)
        tree = getattr(obj, "node_tree", None) if obj else None
        label = "material"
    elif graph_type in {"GEOMETRY", "SHADER"}:
        obj = bpy.data.node_groups.get(graph_name)
        tree = obj if obj and _matches_group_type(obj, graph_type) else None
        label = graph_type.lower() + " node group"
    elif graph_type == "COMPOSITOR":
        obj = bpy.data.node_groups.get(graph_name)
        if obj and _matches_group_type(obj, "COMPOSITOR"):
            tree = obj
            label = "compositor node group"
        else:
            obj = bpy.data.scenes.get(graph_name)
            tree = _scene_compositor_tree(obj) if obj else None
            label = "scene compositor graph"
    elif graph_type == "WORLD":
        obj = bpy.data.worlds.get(graph_name)
        tree = getattr(obj, "node_tree", None) if obj else None
        label = "world"
    elif graph_type == "LIGHT":
        obj = bpy.data.lights.get(graph_name)
        tree = getattr(obj, "node_tree", None) if obj else None
        label = "light"
    else:
        linestyles = getattr(bpy.data, "linestyles", None)
        obj = linestyles.get(graph_name) if linestyles else None
        tree = getattr(obj, "node_tree", None) if obj else None
        label = "line style"

    if obj is None:
        return None, None, "%s '%s' was not found." % (label.capitalize(), graph_name)
    if tree is None:
        return obj, None, "%s '%s' does not have a node tree." % (label.capitalize(), graph_name)
    return obj, tree, None

def _is_output_node(node):
    node_type = getattr(node, "type", "")
    bl_idname = getattr(node, "bl_idname", "")
    return (
        node_type in {"OUTPUT_MATERIAL", "OUTPUT_WORLD", "OUTPUT_LIGHT", "OUTPUT_LINESTYLE",
                      "GROUP_OUTPUT", "COMPOSITE", "VIEWER", "OUTPUT_FILE"}
        or bl_idname.startswith("ShaderNodeOutput")
        or bl_idname in {"CompositorNodeComposite", "CompositorNodeViewer", "CompositorNodeOutputFile",
                         "NodeGroupOutput"}
    )

def _has_output(node_tree):
    return any(_is_output_node(node) for node in node_tree.nodes)

def _uses_subgroups(node_tree):
    names = []
    for node in node_tree.nodes:
        sub_tree = getattr(node, "node_tree", None)
        if sub_tree is not None:
            names.append(sub_tree.name)
    return sorted(set(names))

def _graph_summary(graph_type, name, node_tree, owner_kind=None):
    subgroup_names = _uses_subgroups(node_tree)
    return {
        "type": graph_type,
        "name": name,
        "owner_kind": owner_kind or graph_type,
        "node_tree": node_tree.name,
        "node_tree_kind": _tree_kind(node_tree),
        "node_count": len(node_tree.nodes),
        "link_count": len(node_tree.links),
        "has_output": _has_output(node_tree),
        "uses_subgroups": bool(subgroup_names),
        "subgroups": subgroup_names,
    }

def _node_category(node):
    bl_idname = getattr(node, "bl_idname", "")
    node_type = getattr(node, "type", "")
    if node_type in {"GROUP", "GROUP_INPUT", "GROUP_OUTPUT"} or "Group" in bl_idname:
        return "GROUP"
    if bl_idname.startswith("GeometryNode"):
        return "GEOMETRY"
    if bl_idname.startswith("CompositorNode"):
        return "COMPOSITOR"
    if "Output" in bl_idname or node_type.startswith("OUTPUT"):
        return "OUTPUT"
    if "Tex" in bl_idname or node_type == "TEX_IMAGE":
        return "TEXTURE"
    if any(token in bl_idname for token in ("Bsdf", "Shader", "Emission", "Volume")):
        return "SHADER"
    if any(token in bl_idname for token in ("Math", "Vector", "MapRange", "ValToRGB")):
        return "MATH"
    if node_type:
        return node_type
    return "OTHER"

def _link_endpoint(link, side):
    node = getattr(link, side + "_node", None)
    sock = getattr(link, side + "_socket", None)
    return {
        "node": node.name if node else None,
        "socket": sock.name if sock else None,
        "socket_identifier": getattr(sock, "identifier", None) if sock else None,
    }
""".replace("__PRECISION__", repr(prec)).replace("__GRAPH_TYPES__", repr(list(_GRAPH_TYPES)))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="NTP List Graphs", readOnlyHint=True))
    def ntp_list_graphs(filter_by_type: str = "") -> dict[str, object]:
        """
        List material, geometry-node, shader, compositor, world, light, and line-style node graphs.
        """
        code = _common_code() + """
filter_by_type = __FILTER_BY_TYPE__.upper()
if filter_by_type and filter_by_type not in VALID_GRAPH_TYPES:
    result = _error("Unsupported filter_by_type '%s'. Expected one of %s." % (
        filter_by_type, ", ".join(VALID_GRAPH_TYPES)
    ))
else:
    graphs = []
    wanted = set(VALID_GRAPH_TYPES if not filter_by_type else [filter_by_type])

    if "MATERIAL" in wanted:
        for mat in bpy.data.materials:
            if getattr(mat, "node_tree", None) is not None:
                graphs.append(_graph_summary("MATERIAL", mat.name, mat.node_tree, "material"))

    for group in bpy.data.node_groups:
        kind = _tree_kind(group)
        if kind in {"GEOMETRY", "SHADER", "COMPOSITOR"} and kind in wanted:
            graphs.append(_graph_summary(kind, group.name, group, "node_group"))

    if "COMPOSITOR" in wanted:
        for scene in bpy.data.scenes:
            tree = _scene_compositor_tree(scene)
            if tree is not None:
                graphs.append(_graph_summary("COMPOSITOR", scene.name, tree, "scene"))

    if "WORLD" in wanted:
        for world in bpy.data.worlds:
            if getattr(world, "node_tree", None) is not None:
                graphs.append(_graph_summary("WORLD", world.name, world.node_tree, "world"))

    if "LIGHT" in wanted:
        for light in bpy.data.lights:
            if getattr(light, "node_tree", None) is not None:
                graphs.append(_graph_summary("LIGHT", light.name, light.node_tree, "light"))

    if "LINESTYLE" in wanted:
        linestyles = getattr(bpy.data, "linestyles", None)
        if linestyles:
            for line_style in linestyles:
                if getattr(line_style, "node_tree", None) is not None:
                    graphs.append(_graph_summary("LINESTYLE", line_style.name, line_style.node_tree, "linestyle"))

    graphs.sort(key=lambda g: (g["type"], g["name"]))
    result = {
        "status": "ok",
        "filter_by_type": filter_by_type or None,
        "count": len(graphs),
        "graphs": graphs,
    }
"""
        code = code.replace("__FILTER_BY_TYPE__", repr(filter_by_type))
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="NTP Snapshot Graph", readOnlyHint=True))
    def ntp_snapshot_graph(
        graph_type: str,
        graph_name: str,
        include_imports: bool = True,
        set_defaults: bool = True,
    ) -> dict[str, object]:
        """
        Export one node graph as NodeToPython Python code without changing the graph.
        """
        repo_vendor_path, package_vendor_path = _vendor_paths()
        code = _common_code() + """
import importlib
import sys

graph_type = __GRAPH_TYPE__.upper()
graph_name = __GRAPH_NAME__
include_imports = __INCLUDE_IMPORTS__
set_defaults = __SET_DEFAULTS__
vendor_candidates = [__REPO_VENDOR_PATH__, __PACKAGE_VENDOR_PATH__]

owner, node_tree, message = _resolve_graph(graph_type, graph_name)
if message:
    result = _error(message)
else:
    registered_before = bpy.types.Scene.bl_rna.properties.get("ntp_options") is not None
    package_root = None
    for candidate in vendor_candidates:
        if candidate and candidate not in sys.path:
            sys.path.insert(0, candidate)
        if candidate:
            package_init = __import__("os").path.join(candidate, "NodeToPython", "__init__.py")
            flat_init = __import__("os").path.join(candidate, "__init__.py")
            if __import__("os").path.exists(package_init) or __import__("os").path.exists(flat_init):
                package_root = candidate
                break
    if package_root is None:
        result = _error("Vendored NodeToPython package was not found under the MCP vendor directory.")
    else:
        try:
            ntp = importlib.import_module("NodeToPython")
            if not registered_before:
                ntp.register()

            scene = bpy.context.scene
            options = scene.ntp_options
            options.mode = "SCRIPT"
            options.include_imports = include_imports
            options.set_group_defaults = set_defaults
            options.set_node_sizes = True

            slot_map = {
                "MATERIAL": ("ntp_material_slots", "material", owner),
                "GEOMETRY": ("ntp_geometry_node_group_slots", "node_tree", node_tree),
                "SHADER": ("ntp_shader_node_group_slots", "node_tree", node_tree),
                "COMPOSITOR": (
                    "ntp_compositor_node_group_slots" if owner is node_tree else "ntp_scene_slots",
                    "node_tree" if owner is node_tree else "scene",
                    owner,
                ),
                "WORLD": ("ntp_world_slots", "world", owner),
                "LIGHT": ("ntp_light_slots", "light", owner),
                "LINESTYLE": ("ntp_line_style_slots", "line_style", owner),
            }
            slot_name, attr_name, slot_value = slot_map[graph_type]

            for collection_name in (
                "ntp_material_slots",
                "ntp_geometry_node_group_slots",
                "ntp_shader_node_group_slots",
                "ntp_compositor_node_group_slots",
                "ntp_scene_slots",
                "ntp_world_slots",
                "ntp_light_slots",
                "ntp_line_style_slots",
            ):
                collection = getattr(scene, collection_name, None)
                if collection is not None:
                    collection.clear()

            slot = getattr(scene, slot_name).add()
            setattr(slot, attr_name, slot_value)

            before_clipboard = bpy.context.window_manager.clipboard
            op_result = bpy.ops.ntp.export()
            code_text = bpy.context.window_manager.clipboard
            if not code_text or code_text == before_clipboard:
                result = _error("NodeToPython export did not produce clipboard output.")
            else:
                result = {
                    "status": "ok",
                    "graph_type": graph_type,
                    "graph_name": graph_name,
                    "node_tree": node_tree.name,
                    "registered_ntp": not registered_before,
                    "operator_result": sorted(list(op_result)),
                    "include_imports": include_imports,
                    "set_defaults": set_defaults,
                    "line_count": len(code_text.splitlines()),
                    "byte_size": len(code_text.encode("utf-8")),
                    "code": code_text,
                }
        except Exception as ex:
            result = _error("NodeToPython snapshot failed: %s" % ex)
"""
        code = (
            code.replace("__GRAPH_TYPE__", repr(graph_type))
            .replace("__GRAPH_NAME__", repr(graph_name))
            .replace("__INCLUDE_IMPORTS__", repr(bool(include_imports)))
            .replace("__SET_DEFAULTS__", repr(bool(set_defaults)))
            .replace("__REPO_VENDOR_PATH__", repr(repo_vendor_path))
            .replace("__PACKAGE_VENDOR_PATH__", repr(package_vendor_path))
        )
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="NTP Analyze Graph", readOnlyHint=True))
    def ntp_analyze_graph(
        graph_type: str,
        graph_name: str,
        coord_precision: int = 6,
    ) -> dict[str, object]:
        """
        Return structural stats, broken links, orphan/dead-end nodes, and group dependencies for one graph.
        """
        code = _common_code(coord_precision) + """
graph_type = __GRAPH_TYPE__.upper()
graph_name = __GRAPH_NAME__

owner, node_tree, message = _resolve_graph(graph_type, graph_name)
if message:
    result = _error(message)
else:
    nodes_by_category = {{}}
    nodes_by_type = {{}}
    orphan_nodes = []
    dead_end_nodes = []
    linked_groups = []
    output_nodes = []

    for node in node_tree.nodes:
        category = _node_category(node)
        exact_type = getattr(node, "bl_idname", "") or getattr(node, "type", "")
        nodes_by_category[category] = nodes_by_category.get(category, 0) + 1
        nodes_by_type[exact_type] = nodes_by_type.get(exact_type, 0) + 1

        has_input_link = any(sock.is_linked for sock in node.inputs)
        has_output_link = any(sock.is_linked for sock in node.outputs)
        node_info = {
            "name": node.name,
            "label": node.label,
            "type": exact_type,
            "category": category,
            "location": [_round(node.location.x), _round(node.location.y)],
        }
        if not has_input_link and not has_output_link:
            orphan_nodes.append(node_info)
        if node.outputs and not has_output_link and not _is_output_node(node):
            dead_end_nodes.append(node_info)
        if _is_output_node(node):
            output_nodes.append(node_info)
        sub_tree = getattr(node, "node_tree", None)
        if sub_tree is not None:
            linked_groups.append({
                "node": node.name,
                "node_tree": sub_tree.name,
                "node_tree_kind": _tree_kind(sub_tree),
            })

    broken_links = []
    for link in node_tree.links:
        is_valid = getattr(link, "is_valid", True)
        if not is_valid or link.from_node is None or link.to_node is None:
            broken_links.append({
                "from": _link_endpoint(link, "from"),
                "to": _link_endpoint(link, "to"),
                "is_valid": bool(is_valid),
            })

    def _dependency_chains(tree, path=None, depth=0):
        path = list(path or [tree.name])
        if depth >= 5:
            return []
        chains = []
        for node in tree.nodes:
            sub_tree = getattr(node, "node_tree", None)
            if sub_tree is None:
                continue
            next_path = path + [sub_tree.name]
            chains.append(next_path)
            if sub_tree.name not in path:
                chains.extend(_dependency_chains(sub_tree, next_path, depth + 1))
        return chains

    total_nodes = len(node_tree.nodes)
    total_links = len(node_tree.links)
    dependency_chains = _dependency_chains(node_tree)
    complexity_score = (
        total_nodes
        + (2 * total_links)
        + (5 * len(linked_groups))
        + (10 * len(broken_links))
        + (2 * len(orphan_nodes))
    )
    if complexity_score < 20:
        complexity = "low"
    elif complexity_score < 60:
        complexity = "medium"
    elif complexity_score < 140:
        complexity = "high"
    else:
        complexity = "very_high"

    result = {
        "status": "ok",
        "graph_type": graph_type,
        "graph_name": graph_name,
        "node_tree": node_tree.name,
        "total_nodes": total_nodes,
        "total_links": total_links,
        "total_input_sockets": sum(len(node.inputs) for node in node_tree.nodes),
        "total_output_sockets": sum(len(node.outputs) for node in node_tree.nodes),
        "nodes_by_category": nodes_by_category,
        "nodes_by_type": nodes_by_type,
        "has_output": bool(output_nodes),
        "output_nodes": output_nodes,
        "orphan_nodes": orphan_nodes,
        "dead_end_nodes": dead_end_nodes,
        "broken_links": broken_links,
        "linked_node_groups": linked_groups,
        "dependency_chains": dependency_chains,
        "complexity": {"score": complexity_score, "level": complexity},
    }
"""
        code = code.replace("__GRAPH_TYPE__", repr(graph_type)).replace("__GRAPH_NAME__", repr(graph_name))
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="NTP Inspect Node", readOnlyHint=True))
    def ntp_inspect_node(
        graph_type: str,
        graph_name: str,
        node_name: str,
        coord_precision: int = 6,
    ) -> dict[str, object]:
        """
        Inspect one node's sockets, links, location, and readable RNA properties.
        """
        code = _common_code(coord_precision) + """
graph_type = __GRAPH_TYPE__.upper()
graph_name = __GRAPH_NAME__
node_name = __NODE_NAME__

owner, node_tree, message = _resolve_graph(graph_type, graph_name)
if message:
    result = _error(message)
else:
    node = node_tree.nodes.get(node_name)
    if node is None:
        matches = [n for n in node_tree.nodes if n.label == node_name or getattr(n, "bl_idname", "") == node_name]
        node = matches[0] if len(matches) == 1 else None
    if node is None:
        result = _error("Node '%s' was not found in %s '%s'." % (node_name, graph_type, graph_name))
    else:
        inputs = []
        for sock in node.inputs:
            links_from = [_link_endpoint(link, "from") for link in sock.links]
            default_value = None
            if hasattr(sock, "default_value"):
                try:
                    default_value = _plain(sock.default_value)
                except Exception:
                    default_value = "<unreadable>"
            inputs.append({
                "name": sock.name,
                "identifier": getattr(sock, "identifier", None),
                "type": getattr(sock, "type", None),
                "enabled": getattr(sock, "enabled", True),
                "hide": getattr(sock, "hide", False),
                "is_linked": sock.is_linked,
                "default_value": default_value,
                "links_from": links_from,
            })

        outputs = []
        for sock in node.outputs:
            outputs.append({
                "name": sock.name,
                "identifier": getattr(sock, "identifier", None),
                "type": getattr(sock, "type", None),
                "enabled": getattr(sock, "enabled", True),
                "hide": getattr(sock, "hide", False),
                "is_linked": sock.is_linked,
                "links_to": [_link_endpoint(link, "to") for link in sock.links],
            })

        skip_props = {
            "rna_type", "name", "label", "location", "width", "height", "dimensions",
            "select", "inputs", "outputs", "internal_links", "parent", "type",
        }
        rna_properties = {}
        for prop in node.bl_rna.properties:
            identifier = prop.identifier
            if identifier in skip_props or getattr(prop, "is_hidden", False):
                continue
            if getattr(prop, "type", "") == "COLLECTION":
                continue
            try:
                value = getattr(node, identifier)
            except Exception:
                continue
            plain = _plain(value)
            if isinstance(plain, str) and plain.startswith("<") and plain.endswith(">"):
                continue
            rna_properties[identifier] = plain

        result = {
            "status": "ok",
            "graph_type": graph_type,
            "graph_name": graph_name,
            "node_tree": node_tree.name,
            "node": {
                "name": node.name,
                "label": node.label,
                "type": getattr(node, "type", None),
                "bl_idname": getattr(node, "bl_idname", None),
                "category": _node_category(node),
                "location": [_round(node.location.x), _round(node.location.y)],
                "width": _round(node.width),
                "height": _round(getattr(node, "height", 0.0)),
                "mute": getattr(node, "mute", False),
                "hide": getattr(node, "hide", False),
                "node_tree": getattr(getattr(node, "node_tree", None), "name", None),
            },
            "inputs": inputs,
            "outputs": outputs,
            "rna_properties": rna_properties,
        }
"""
        code = (
            code.replace("__GRAPH_TYPE__", repr(graph_type))
            .replace("__GRAPH_NAME__", repr(graph_name))
            .replace("__NODE_NAME__", repr(node_name))
        )
        return send_code(code, strict_json=True)
