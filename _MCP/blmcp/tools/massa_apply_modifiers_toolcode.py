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
    modifier_names: object
    keep_last_bevel_weighted_normal: bool
    preserve_shape_keys: bool


class Result(NamedTuple):
    status: str
    object: str
    applied: list[str]
    skipped: list[dict[str, str]]
    kept: list[str]
    warnings: list[str]
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
        if obj.type != "MESH":
            raise ValueError("Object '" + obj.name + "' is type " + obj.type + ", expected MESH.")

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        requested = params.modifier_names
        if isinstance(requested, str):
            if requested != "ALL":
                requested_names = {requested}
            else:
                requested_names = {modifier.name for modifier in obj.modifiers}
        else:
            requested_names = {str(name) for name in requested}

        applied = []
        skipped = []
        kept = []
        warnings = []
        existing_names = {modifier.name for modifier in obj.modifiers}
        for name in sorted(requested_names - existing_names):
            skipped.append({"name": name, "reason": "modifier not found"})

        keep_names = set()
        if bool(params.keep_last_bevel_weighted_normal):
            for wanted_type in ("BEVEL", "WEIGHTED_NORMAL"):
                matches = [modifier.name for modifier in obj.modifiers if modifier.type == wanted_type]
                if matches:
                    keep_names.add(matches[-1])

        has_shape_keys = bool(getattr(obj.data, "shape_keys", None))
        if bool(params.preserve_shape_keys) and has_shape_keys:
            warnings.append(
                "preserve_shape_keys=True requested, but Blender modifier_apply is not deterministic with shape keys; requested modifiers were skipped."
            )
            for modifier in obj.modifiers:
                if modifier.name in requested_names:
                    skipped.append({"name": modifier.name, "reason": "shape key preservation requested"})
        else:
            if has_shape_keys:
                warnings.append("Object has shape keys; Blender may reject applying some modifiers.")
            for modifier_name in [modifier.name for modifier in obj.modifiers]:
                if modifier_name not in requested_names:
                    continue
                if modifier_name in keep_names:
                    kept.append(modifier_name)
                    continue
                try:
                    bpy.ops.object.modifier_apply(modifier=modifier_name)
                    applied.append(modifier_name)
                except Exception as exc:
                    skipped.append({"name": modifier_name, "reason": str(exc)})

        return Result(
            status="ok",
            object=obj.name,
            applied=applied,
            skipped=skipped,
            kept=kept,
            warnings=warnings,
        )
    except Exception as exc:
        return Result(
            status="error",
            object=params.object_name,
            applied=[],
            skipped=[],
            kept=[],
            warnings=[],
            error=str(exc),
        )
