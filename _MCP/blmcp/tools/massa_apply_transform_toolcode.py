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
    object_name: str
    location: bool
    rotation: bool
    scale: bool


class Result(NamedTuple):
    status: str
    object: str
    applied: dict[str, bool]
    error: str | None = None


def main(params: Params) -> Result:
    import bpy

    def set_object_mode():
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    try:
        set_object_mode()
        obj = bpy.data.objects.get(str(params.object_name))
        if obj is None:
            raise ValueError("Object '" + str(params.object_name) + "' was not found.")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(
            location=bool(params.location),
            rotation=bool(params.rotation),
            scale=bool(params.scale),
        )
        return Result(
            status="ok",
            object=obj.name,
            applied={
                "location": bool(params.location),
                "rotation": bool(params.rotation),
                "scale": bool(params.scale),
            },
        )
    except Exception as exc:
        return Result(
            status="error",
            object=params.object_name,
            applied={},
            error=str(exc),
        )
