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
    node_name: str
    coord_precision: int


class Result(NamedTuple):
    status: str
    graph_type: str | None = None
    graph_name: str | None = None
    node_tree: str | None = None
    node: dict[str, object] | None = None
    inputs: list[dict[str, object]] | None = None
    outputs: list[dict[str, object]] | None = None
    rna_properties: dict[str, object] | None = None
    message: str | None = None


def main(params: Params) -> Result:
    PRECISION = params.coord_precision

    # @include_begin: _template_ntp_common.py
    # @include_end

    graph_type = params.graph_type.upper()
    graph_name = params.graph_name
    node_name = params.node_name

    owner, node_tree, message = _resolve_graph(graph_type, graph_name)
    if message:
        return Result(status="error", message=message)

    node = node_tree.nodes.get(node_name)
    if node is None:
        matches = [n for n in node_tree.nodes if n.label == node_name or getattr(n, "bl_idname", "") == node_name]
        node = matches[0] if len(matches) == 1 else None
    if node is None:
        return Result(status="error", message="Node '%s' was not found in %s '%s'." % (node_name, graph_type, graph_name))
    
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

    return Result(
        status="ok",
        graph_type=graph_type,
        graph_name=graph_name,
        node_tree=node_tree.name,
        node={
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
        inputs=inputs,
        outputs=outputs,
        rna_properties=rna_properties,
    )
