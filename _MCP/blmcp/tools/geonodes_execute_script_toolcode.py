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
    vendor_parent: str
    script: str
    target_object: str


class Result(NamedTuple):
    status: str
    message: str | None = None
    created_node_groups: list[str] | None = None
    created_materials: list[str] | None = None
    attached_to_object: str | None = None
    stdout: str | None = None
    traceback: str | None = None


def main(params: Params) -> Result:
    import contextlib
    import io
    import sys
    import traceback
    import bpy

    vendor_parent = params.vendor_parent
    user_script = params.script
    target_object_name = params.target_object

    if vendor_parent not in sys.path:
        sys.path.insert(0, vendor_parent)

    before_groups = set(bpy.data.node_groups.keys())
    before_materials = set(bpy.data.materials.keys())
    stdout = io.StringIO()
    trace = None

    try:
        with contextlib.redirect_stdout(stdout):
            exec(compile(user_script, "<geonodes_execute_script>", "exec"), {"__name__": "__main__"})
    except Exception:
        trace = traceback.format_exc()

    created_node_groups = sorted(name for name in bpy.data.node_groups.keys() if name not in before_groups)
    created_materials = sorted(name for name in bpy.data.materials.keys() if name not in before_materials)

    attached_to = None
    if not trace and created_node_groups:
        node_group = bpy.data.node_groups.get(created_node_groups[0])
        if node_group:
            target_obj = None
            if target_object_name:
                target_obj = bpy.data.objects.get(target_object_name)
            
            if not target_obj:
                mesh = bpy.data.meshes.new(name="GeoNodes_Mesh")
                target_obj = bpy.data.objects.new("GeoNodes_Object", mesh)
                bpy.context.scene.collection.objects.link(target_obj)
                
                # Add default geometry
                import bmesh
                bm = bmesh.new()
                bmesh.ops.create_cube(bm, size=1.0)
                bm.to_mesh(mesh)
                bm.free()
            
            mod = target_obj.modifiers.new(name=node_group.name, type='NODES')
            mod.node_group = node_group
            attached_to = target_obj.name

    return Result(
        status="error" if trace else "ok",
        message="geonodes script failed; see traceback." if trace else "geonodes script executed.",
        created_node_groups=created_node_groups,
        created_materials=created_materials,
        attached_to_object=attached_to,
        stdout=stdout.getvalue(),
        traceback=trace,
    )
