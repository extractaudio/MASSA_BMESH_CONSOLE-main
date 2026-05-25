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
    filter_by_type: str


class Result(NamedTuple):
    status: str
    filter_by_type: str | None = None
    count: int | None = None
    graphs: list[dict[str, object]] | None = None
    message: str | None = None


def main(params: Params) -> Result:
    PRECISION = 6

    # @include_begin: _template_ntp_common.py
    # @include_end

    filter_by_type = params.filter_by_type.upper() if params.filter_by_type else ""
    if filter_by_type and filter_by_type not in VALID_GRAPH_TYPES:
        return Result(status="error", message="Unsupported filter_by_type '%s'. Expected one of %s." % (
            filter_by_type, ", ".join(VALID_GRAPH_TYPES)
        ))

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
    return Result(
        status="ok",
        filter_by_type=filter_by_type or None,
        count=len(graphs),
        graphs=graphs,
    )
