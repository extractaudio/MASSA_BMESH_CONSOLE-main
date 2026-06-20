# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for setting an object's mode and (optionally) mesh select mode.

Removes the need to drop into execute_blender_code just to toggle Edit mode or
switch between vertex/edge/face selection before the selection/tagging tools.
"""

__all__ = ("Params", "Result", "main")

from typing import NamedTuple


class Params(NamedTuple):
    object_name: str
    mode: str
    select_mode: list[str]


class Result(NamedTuple):
    status: str
    object: str | None = None
    mode: str | None = None
    select_mode: list[str] | None = None
    message: str | None = None


_VALID_MODES = {
    "OBJECT", "EDIT", "SCULPT", "VERTEX_PAINT", "WEIGHT_PAINT",
    "TEXTURE_PAINT", "PARTICLE_EDIT",
}
_VALID_SELECT = {"VERT", "EDGE", "FACE"}


def main(params: Params) -> Result:
    import bpy

    obj = bpy.data.objects.get(params.object_name) if params.object_name else bpy.context.active_object
    if obj is None:
        return Result(status="error", message="Object '{:s}' was not found.".format(params.object_name))

    mode = (params.mode or "OBJECT").upper()
    if mode not in _VALID_MODES:
        return Result(status="error", object=obj.name, message="Invalid mode '{:s}'.".format(mode))

    try:
        if bpy.context.view_layer.objects.active is not obj:
            bpy.context.view_layer.objects.active = obj
        if not obj.visible_get():
            obj.hide_set(False)
        obj.select_set(True)

        if bpy.context.object and bpy.context.object.mode != mode:
            bpy.ops.object.mode_set(mode=mode)

        applied_select = None
        if mode == "EDIT" and params.select_mode:
            sel = [s.upper() for s in params.select_mode if s.upper() in _VALID_SELECT]
            if sel:
                flags = (("VERT" in sel), ("EDGE" in sel), ("FACE" in sel))
                bpy.context.tool_settings.mesh_select_mode = flags
                applied_select = sel
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return Result(status="error", object=obj.name, message=str(exc))

    return Result(status="ok", object=obj.name, mode=mode, select_mode=applied_select)
