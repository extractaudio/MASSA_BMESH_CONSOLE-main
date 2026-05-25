# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    graph_type: str
    graph_name: str
    include_imports: bool
    set_defaults: bool
    package_vendor_path: str
    repo_vendor_path: str


class Result(NamedTuple):
    status: str
    graph_type: str | None = None
    graph_name: str | None = None
    node_tree: str | None = None
    registered_ntp: bool | None = None
    operator_result: list[str] | None = None
    include_imports: bool | None = None
    set_defaults: bool | None = None
    line_count: int | None = None
    byte_size: int | None = None
    code: str | None = None
    message: str | None = None


def main(params: Params) -> Result:
    import importlib
    import sys

    PRECISION = 6

    # @include_begin: _template_ntp_common.py
    # @include_end

    graph_type = params.graph_type.upper()
    graph_name = params.graph_name
    include_imports = params.include_imports
    set_defaults = params.set_defaults
    vendor_candidates = [params.package_vendor_path, params.repo_vendor_path]

    owner, node_tree, message = _resolve_graph(graph_type, graph_name)
    if message:
        return Result(status="error", message=message)
    
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
        return Result(status="error", message="Vendored NodeToPython package was not found under the MCP vendor directory.")
    
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
            return Result(status="error", message="NodeToPython export did not produce clipboard output.")
        
        return Result(
            status="ok",
            graph_type=graph_type,
            graph_name=graph_name,
            node_tree=node_tree.name,
            registered_ntp=not registered_before,
            operator_result=sorted(list(op_result)),
            include_imports=include_imports,
            set_defaults=set_defaults,
            line_count=len(code_text.splitlines()),
            byte_size=len(code_text.encode("utf-8")),
            code=code_text,
        )
    except Exception as ex:
        return Result(status="error", message="NodeToPython snapshot failed: %s" % ex)
