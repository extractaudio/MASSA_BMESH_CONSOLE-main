# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for re-running (live-editing) an existing Massa cartridge object.

Replicates the addon's resurrection path WITHOUT relying on the UI invoke()
context: it restores the object's stored ``MASSA_PARAMS``, merges caller
overrides, and fires the cartridge operator in EXEC mode with
``target_delete_name`` set so ``Massa_OT_Base.execute()`` deletes the old object
and regenerates in place. (The old ``massa.rerun_active`` operator was removed;
resurrection is now param-restore + re-run.)
"""

__all__ = ("Params", "Result", "main")

from typing import NamedTuple, Any


class Params(NamedTuple):
    object_name: str
    console_params: dict[str, Any]
    cartridge_params: dict[str, Any]


class Result(NamedTuple):
    status: str
    object_name: str | None = None
    bl_idname: str | None = None
    applied_overrides: list[str] | None = None
    error: str | None = None


def main(params: Params) -> Result:
    import bpy

    obj = bpy.data.objects.get(params.object_name) if params.object_name else bpy.context.active_object
    if obj is None:
        return Result(status="error", error="Object '{:s}' was not found.".format(params.object_name))
    if "MASSA_PARAMS" not in obj or "massa_op_id" not in obj:
        return Result(
            status="error",
            object_name=obj.name,
            error="Object '{:s}' is not a Massa cartridge (missing MASSA_PARAMS/massa_op_id).".format(obj.name),
        )

    bl_idname = obj["massa_op_id"]            # e.g. "massa.gen_prim_02_pipe"
    op_name = bl_idname.split(".", 1)[-1]     # "gen_prim_02_pipe"
    op = getattr(bpy.ops.massa, op_name, None)
    if op is None:
        return Result(status="error", object_name=obj.name, error="Operator {:s} not found.".format(bl_idname))

    # Determine which kwargs the operator actually accepts. Properties live on
    # the ops RNA type; exclude rna_type and bl_* builtins (passing e.g.
    # bl_translation_context as a kwarg raises "unrecognized keyword").
    valid = set()
    try:
        rna = op.get_rna_type()
        for prop in rna.properties:
            ident = prop.identifier
            if prop.is_readonly or ident == "rna_type" or ident.startswith("bl_"):
                continue
            valid.add(ident)
    except Exception:  # pylint: disable=broad-exception-caught
        valid = set()

    # Base parameters from the stored payload.
    kwargs: dict[str, Any] = {}
    try:
        restored = dict(obj["MASSA_PARAMS"].items())
    except Exception:  # pylint: disable=broad-exception-caught
        restored = {}
    for key, value in restored.items():
        if key == "MASSA_PARAMS_VERSION" or key == "rna_type" or key.startswith("bl_"):
            continue
        if valid and key not in valid:
            continue
        kwargs[key] = list(value) if hasattr(value, "__len__") and not isinstance(value, str) else value

    # Caller overrides (console then cartridge params; cartridge wins).
    applied: list[str] = []
    for source in (params.console_params, params.cartridge_params):
        for key, value in source.items():
            if valid and key not in valid:
                continue
            kwargs[key] = value
            applied.append(key)

    # Preserve transform and tell execute() to delete the old object.
    kwargs["target_delete_name"] = obj.name
    kwargs["obj_location"] = list(obj.location)
    kwargs["obj_rotation"] = list(obj.rotation_euler)

    try:
        if bpy.context.view_layer.objects.active is not obj:
            bpy.context.view_layer.objects.active = obj
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        op(**kwargs)
        new_obj = bpy.context.active_object
        new_name = new_obj.name if new_obj else None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return Result(status="error", object_name=obj.name, bl_idname=bl_idname, error=str(exc))

    return Result(
        status="ok",
        object_name=new_name,
        bl_idname=bl_idname,
        applied_overrides=sorted(set(applied)),
    )
