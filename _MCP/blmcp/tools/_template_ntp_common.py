import bpy

VALID_GRAPH_TYPES = ("MATERIAL", "GEOMETRY", "SHADER", "COMPOSITOR", "WORLD", "LIGHT", "LINESTYLE")

def _error(message):
    return {"status": "error", "message": message}

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
        return {"name": value.name, "type": value.__class__.__name__}
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
