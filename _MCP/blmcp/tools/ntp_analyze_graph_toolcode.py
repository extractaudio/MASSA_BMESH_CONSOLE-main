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
    coord_precision: int


class Result(NamedTuple):
    status: str
    graph_type: str | None = None
    graph_name: str | None = None
    node_tree: str | None = None
    total_nodes: int | None = None
    total_links: int | None = None
    total_input_sockets: int | None = None
    total_output_sockets: int | None = None
    nodes_by_category: dict[str, int] | None = None
    nodes_by_type: dict[str, int] | None = None
    has_output: bool | None = None
    output_nodes: list[dict[str, object]] | None = None
    orphan_nodes: list[dict[str, object]] | None = None
    dead_end_nodes: list[dict[str, object]] | None = None
    broken_links: list[dict[str, object]] | None = None
    linked_node_groups: list[dict[str, object]] | None = None
    dependency_chains: list[list[str]] | None = None
    complexity: dict[str, object] | None = None
    message: str | None = None


def main(params: Params) -> Result:
    PRECISION = params.coord_precision

    # @include_begin: _template_ntp_common.py
    # @include_end

    graph_type = params.graph_type.upper()
    graph_name = params.graph_name

    owner, node_tree, message = _resolve_graph(graph_type, graph_name)
    if message:
        return Result(status="error", message=message)
    
    nodes_by_category = {}
    nodes_by_type = {}
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

    return Result(
        status="ok",
        graph_type=graph_type,
        graph_name=graph_name,
        node_tree=node_tree.name,
        total_nodes=total_nodes,
        total_links=total_links,
        total_input_sockets=sum(len(node.inputs) for node in node_tree.nodes),
        total_output_sockets=sum(len(node.outputs) for node in node_tree.nodes),
        nodes_by_category=nodes_by_category,
        nodes_by_type=nodes_by_type,
        has_output=bool(output_nodes),
        output_nodes=output_nodes,
        orphan_nodes=orphan_nodes,
        dead_end_nodes=dead_end_nodes,
        broken_links=broken_links,
        linked_node_groups=linked_groups,
        dependency_chains=dependency_chains,
        complexity={"score": complexity_score, "level": complexity},
    )
