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
    object_names: list[str]
    mode: str
    merge_threshold: float
    dissolve_angle_deg: float
    degenerate_iterations: int
    delete_interior: bool
    force_native: bool


class Result(NamedTuple):
    status: str
    used_hardops: bool
    mode: str
    objects: list[dict[str, object]]
    warnings: list[str]
    error: str | None = None


def main(params: Params) -> Result:
    import bpy
    import math

    def hops_clean_available():
        return hasattr(bpy.ops, "view3d") and hasattr(bpy.ops.view3d, "clean_mesh")

    def set_object_mode():
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    def resolve_meshes(names, mode):
        if names:
            meshes = []
            for name in names:
                obj = bpy.data.objects.get(name)
                if obj is None:
                    raise ValueError("Object '" + str(name) + "' was not found.")
                if obj.type != "MESH":
                    raise ValueError("Object '" + obj.name + "' is type " + obj.type + ", expected MESH.")
                meshes.append(obj)
            return meshes
        if mode == "ACTIVE" and bpy.context.active_object is not None:
            return [bpy.context.active_object]
        if mode == "VISIBLE":
            return [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.visible_get()]
        return [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]

    def select_objects(meshes, mode):
        bpy.ops.object.select_all(action="DESELECT")
        selected = meshes if mode != "ACTIVE" else meshes[:1]
        for obj in selected:
            obj.select_set(True)
        if meshes:
            bpy.context.view_layer.objects.active = meshes[0]

    def hops_property():
        try:
            from HOps.utility import addon  # type: ignore
            pref = addon.preference()
            prop = getattr(pref, "property", None)
            if prop is not None:
                return prop
        except Exception:
            pass

        for key, entry in bpy.context.preferences.addons.items():
            if "hops" not in key.lower() and "hard" not in key.lower():
                continue
            prop = getattr(getattr(entry, "preferences", None), "property", None)
            if prop is not None:
                return prop
        return None

    def snapshot_attrs(obj, names):
        if obj is None:
            return {}
        return {name: getattr(obj, name) for name in names if hasattr(obj, name)}

    def restore_attrs(obj, values):
        if obj is None:
            return
        for name, value in values.items():
            try:
                setattr(obj, name, value)
            except Exception:
                pass

    def mesh_counts(obj):
        return len(obj.data.vertices), len(obj.data.polygons)

    def stats_from(before, meshes):
        stats = []
        for obj in meshes:
            verts_after, faces_after = mesh_counts(obj)
            verts_before, faces_before = before.get(obj.name, (verts_after, faces_after))
            stats.append({
                "object": obj.name,
                "verts_before": verts_before,
                "verts_after": verts_after,
                "verts_removed": max(0, verts_before - verts_after),
                "faces_before": faces_before,
                "faces_after": faces_after,
                "faces_removed": max(0, faces_before - faces_after),
            })
        return stats

    def native_clean_object(obj):
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        if hasattr(bpy.ops.mesh, "merge_by_distance"):
            bpy.ops.mesh.merge_by_distance(distance=params.merge_threshold)
        else:
            bpy.ops.mesh.remove_doubles(threshold=params.merge_threshold)
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(params.dissolve_angle_deg))
        except Exception:
            pass
        for _idx in range(max(0, params.degenerate_iterations)):
            bpy.ops.mesh.select_all(action="SELECT")
            try:
                bpy.ops.mesh.dissolve_degenerate(threshold=params.merge_threshold)
            except Exception:
                break
        if params.delete_interior:
            try:
                bpy.ops.mesh.select_all(action="DESELECT")
                bpy.ops.mesh.select_interior_faces()
                bpy.ops.mesh.delete(type="FACE")
            except Exception:
                pass
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.data.update()

    try:
        mode = str(params.mode).upper()
        if mode not in {"ACTIVE", "SELECTED", "VISIBLE"}:
            raise ValueError("Unsupported clean mode: " + mode)
        set_object_mode()
        meshes = resolve_meshes(list(params.object_names), mode)
        if not meshes:
            raise ValueError("No mesh objects were supplied or selected.")

        before = {obj.name: mesh_counts(obj) for obj in meshes}
        warnings = []
        use_hardops = hops_clean_available() and not bool(params.force_native)

        if use_hardops:
            select_objects(meshes, mode)
            prop = hops_property()
            attr_names = (
                "meshclean_mode",
                "meshclean_dissolve_angle",
                "meshclean_remove_threshold",
                "meshclean_degenerate_iter",
                "meshclean_delete_interior",
            )
            snap = snapshot_attrs(prop, attr_names)
            try:
                if prop is not None:
                    if hasattr(prop, "meshclean_mode"):
                        prop.meshclean_mode = mode
                    if hasattr(prop, "meshclean_dissolve_angle"):
                        prop.meshclean_dissolve_angle = math.radians(params.dissolve_angle_deg)
                    if hasattr(prop, "meshclean_remove_threshold"):
                        prop.meshclean_remove_threshold = params.merge_threshold
                    if hasattr(prop, "meshclean_degenerate_iter"):
                        prop.meshclean_degenerate_iter = params.degenerate_iterations
                    if hasattr(prop, "meshclean_delete_interior"):
                        prop.meshclean_delete_interior = params.delete_interior
                try:
                    bpy.ops.view3d.clean_mesh("EXEC_DEFAULT")
                except TypeError:
                    bpy.ops.view3d.clean_mesh()
            finally:
                restore_attrs(prop, snap)
                set_object_mode()
        else:
            if not hops_clean_available():
                warnings.append("HardOps clean_mesh is not registered; used native fallback.")
            elif params.force_native:
                warnings.append("force_native=True; skipped HardOps clean_mesh.")
            for obj in meshes:
                native_clean_object(obj)
            set_object_mode()

        return Result(
            status="ok",
            used_hardops=use_hardops,
            mode=mode,
            objects=stats_from(before, meshes),
            warnings=warnings,
        )
    except Exception as exc:
        try:
            set_object_mode()
        except Exception:
            pass
        return Result(
            status="error",
            used_hardops=False,
            mode=params.mode,
            objects=[],
            warnings=[],
            error=str(exc),
        )
