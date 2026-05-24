import bpy
import sys
import re
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, StringProperty
from ..modules.massa_properties import MassaPropertiesMixin
from ..modules import massa_engine
from ..utils import mat_utils


MASSA_PARAMS_VERSION = 1
_SLOT_PROP_PATTERN = re.compile(r"^[a-z_]+_\d$")
_PARAM_RENAMES = {
    # version: {"old_key": "new_key"}
}


def _migrate_params(params, version):
    migrated = dict(params)
    for source_version in range(int(version or 0), MASSA_PARAMS_VERSION):
        for old_key, new_key in _PARAM_RENAMES.get(source_version, {}).items():
            if old_key in migrated and new_key not in migrated:
                migrated[new_key] = migrated.pop(old_key)
    migrated["MASSA_PARAMS_VERSION"] = MASSA_PARAMS_VERSION
    return migrated


class Massa_OT_Base(Operator, MassaPropertiesMixin):
    """
    THE MUSCLE: Executes the generation pipeline.
    [PATCHED v4.7]: Fixed Material Injection Logic & DB Sync.
    """

    bl_idname = "massa.base_gen"
    bl_label = "Massa Base"
    bl_options = {"REGISTER", "UNDO", "PRESET"}
    MASSA_PARAMS_VERSION = MASSA_PARAMS_VERSION

    # --- OPERATOR-ONLY PROPERTIES ---
    # (All shared properties inherited from MassaPropertiesMixin)

    # Internal flag for Resurrection Mode
    rerun_mode: BoolProperty(default=False, options={"HIDDEN", "SKIP_SAVE"})

    # [ARCHITECT NEW] Resurrection Transform Persistence
    # These persist in the Redo Panel to ensure the object stays put during tweaking.
    obj_location: FloatVectorProperty(name="Location", subtype="TRANSLATION")
    obj_rotation: FloatVectorProperty(name="Rotation", subtype="EULER")

    # [ARCHITECT NEW] Persistence for Deletion Target (Fixes Doubling on Redo)
    target_delete_name: StringProperty(options={'HIDDEN'})

    def _get_cartridge_meta(self):
        try:
            mod = sys.modules[self.__module__]
            if hasattr(mod, "CARTRIDGE_META"):
                return mod.CARTRIDGE_META
        except Exception:
            pass
        return {}

    def _inject_cartridge_defaults(self):
        """
        ENGINEERING FIX:
        Reads 'get_slot_meta' from the active cartridge and force-applies
        Physics IDs to Visual Material slots IF they are currently 'NONE'.
        [ARCHITECT FIX]: Translates Physics KEY (e.g. 'METAL_STEEL') to
        Visual Material NAME (e.g. 'Metal Steel') via mat_utils.DB.
        """
        if not hasattr(self, "get_slot_meta"):
            return

        meta_slots = self.get_slot_meta()

        for i, data in meta_slots.items():
            # Check current property value
            prop_name = f"mat_{i}"
            if not hasattr(self, prop_name):
                continue

            current_val = getattr(self, prop_name, "NONE")

            # Only override if the user/system hasn't set a specific material yet
            if current_val == "NONE":
                # 1. Get Physics ID Key (e.g. 'METAL_STEEL')
                phys_id = data.get("phys", "GENERIC")

                # 2. Look up the Human-Readable Name from DB
                vis_name = mat_utils.get_visual_name_from_id(phys_id)

                # 3. Apply if valid
                if vis_name != "NONE":
                    try:
                        setattr(self, prop_name, vis_name)
                    except Exception:
                        pass

    def _sync(self, context, from_console=False):
        if not hasattr(context.scene, "massa_console"):
            return
        console = context.scene.massa_console
        annotations = MassaPropertiesMixin.__annotations__
        shared_keys = [k for k in annotations if not _SLOT_PROP_PATTERN.match(k)]
        slot_keys = [k for k in annotations if _SLOT_PROP_PATTERN.match(k)]
        all_keys = shared_keys + slot_keys
        # Note: All shared properties (ui_tab, debug_view, edge_slot_*_action,
        # viz_edge_mode, auto_unwrap*, seam_*, phys_*, sock_*) are already
        # captured via MassaPropertiesMixin.__annotations__ above.

        for key in all_keys:
            if not hasattr(console, key):
                continue
            try:
                if from_console:
                    val = getattr(console, key, None)
                    if val is not None:
                        setattr(self, key, val)
                else:
                    val = getattr(self, key, None)
                    if val is not None:
                        setattr(console, key, val)
            except Exception:
                pass

    def invoke(self, context, event):
        # 1. Sync from Console (Persistent Settings)
        self._sync(context, from_console=True)

        # [ARCHITECT NEW] Resurrection Mode Logic
        # If activated via UI, we pull params directly from the object
        # instead of relying on a wrapper operator.
        if self.rerun_mode:
            obj = context.active_object
            if obj and "MASSA_PARAMS" in obj:
                try:
                    # 1. Capture Transform (Loc/Rot only, as requested)
                    # We store these in properties so they persist across Redo steps
                    self.obj_location = obj.location
                    self.obj_rotation = obj.rotation_euler

                    # 2. Restore Parameters
                    # [ARCHITECT FIX] Use safe dict conversion for IDProperty
                    params = dict(obj["MASSA_PARAMS"].items())
                    version = params.get("MASSA_PARAMS_VERSION", 0)
                    params = _migrate_params(params, version)
                    ignored_keys = []
                    for k, v in params.items():
                        if k == "MASSA_PARAMS_VERSION":
                            continue
                        # Skip materials to allow Console override
                        if k.startswith("mat_") or k.startswith("phys_mat_"):
                            continue

                        # [ARCHITECT FIX] Skip UV/Seam properties to allow Console override
                        # This ensures global UV settings (N-Panel) take precedence over stored object params.
                        if k.startswith("uv_mode_") or k.startswith("uv_scale_"):
                            continue
                        if k in {"auto_unwrap", "auto_unwrap_margin"}:
                            continue
                        if k.startswith("seam_"):
                            continue

                        # [ARCHITECT FIX] Skip transform properties to prevent overwriting with stale data
                        if k in {"obj_location", "obj_rotation"}:
                            continue
                        if hasattr(self, k):
                            try:
                                setattr(self, k, v)
                            except Exception:
                                pass
                        else:
                            ignored_keys.append(k)

                    # 3. Destroy Old Object (Full Re-Birth)
                    # [ARCHITECT FIX] Ensure we only delete the target object
                    # MOVED TO EXECUTE TO SUPPORT REDO
                    self.target_delete_name = obj.name
                    if ignored_keys:
                        self.report(
                            {"WARNING"},
                            "Ignored stale MASSA_PARAMS keys: "
                            + ", ".join(sorted(ignored_keys)[:6]),
                        )

                except Exception as e:
                    print(f"Massa Resurrection Error: {e}")

        # [LEGACY/FALLBACK] Check for Resurrection Payload from Wrapper
        elif "MASSA_TEMP_RESTORE" in context.scene:
            try:
                restore_data = context.scene["MASSA_TEMP_RESTORE"]
                version = restore_data.get("MASSA_PARAMS_VERSION", 0)
                restore_data = _migrate_params(restore_data, version)
                ignored_keys = []
                for k, v in restore_data.items():
                    if k == "MASSA_PARAMS_VERSION":
                        continue
                    if k.startswith("mat_") or k.startswith("phys_mat_"):
                        continue
                    if hasattr(self, k):
                        try:
                            setattr(self, k, v)
                        except Exception:
                            pass
                    else:
                        ignored_keys.append(k)
                if ignored_keys:
                    self.report(
                        {"WARNING"},
                        "Ignored stale MASSA restore keys: "
                        + ", ".join(sorted(ignored_keys)[:6]),
                    )
                del context.scene["MASSA_TEMP_RESTORE"]
            except Exception as e:
                print(f"Massa Resurrection Error: {e}")

        # [ARCHITECT NEW] 3D Cursor Placement (Standard "Add Mesh" Behavior)
        else:
            # If not resurrecting, spawn at the 3D Cursor
            if context.scene and context.scene.cursor:
                self.obj_location = context.scene.cursor.location

        # [ARCHITECT FIX] Ensure Library Exists BEFORE Injection
        mat_utils.ensure_default_library()

        # 2. Inject Cartridge-Specific Defaults
        self._inject_cartridge_defaults()

        return self.execute(context)

    def execute(self, context):
        # [ARCHITECT FIX] Handle Deletion here to support Redo
        if self.target_delete_name:
            # We look up by name because the pointer might be stale or lost in undo
            old_obj = context.scene.objects.get(self.target_delete_name)
            if old_obj:
                try:
                    # [ARCHITECT FIX] Recursive Deletion for Detached Parts
                    # If we detached rail guards, they are children of old_obj.
                    # We must delete them too, or they will duplicate.
                    objects_to_delete = [old_obj] + [c for c in old_obj.children]
                    
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in objects_to_delete:
                        o.select_set(True)
                        
                    bpy.ops.object.delete()
                except Exception as e:
                    print(f"Massa Deletion Error: {e}")

        # [ARCHITECT FIX] Ensure Library Exists BEFORE Injection (Headless safety)
        mat_utils.ensure_default_library()

        # Ensure we inject defaults if running headless
        self._inject_cartridge_defaults()

        # Run Pipeline
        # [ARCHITECT NEW] PHASE 2 PROTOCOL (CLEANUP)
        # Garbage collection for existing active object's children (UCX/Joints)
        # This prevents infinite duplication during Redo Panel updates.
        try:
            clean_obj = context.active_object
            if clean_obj:
                # Loop safely over a copy of children
                for child in list(clean_obj.children):
                    if child.name.startswith("UCX_") or child.name.startswith("MASSA_JOINT_") or child.name.startswith("SOCKET_"):
                        bpy.data.objects.remove(child, do_unlink=True)
        except Exception as e:
            print(f"Massa Child Cleanup Error: {e}")

        result = massa_engine.run_pipeline(self, context)

        # [ARCHITECT NEW] Apply Resurrection Transform
        # We do this AFTER generation so the new object exists.
        # Uses properties so it works during Redo adjustments.
        obj = context.active_object
        if obj:
            # Only apply if not zero (or if in rerun mode, but simpler to just apply)
            # Since default is 0,0,0, applying it for new objects places them at origin,
            # which matches previous behavior.
            obj.location = self.obj_location
            obj.rotation_euler = self.obj_rotation
            # Note: Scale is intentionally NOT restored.

        # Sync back to Console
        self._sync(context, from_console=False)

        return result

    def draw(self, context):
        from ..ui import ui_shared

        layout = self.layout
        stats = context.scene.get("massa_temp_stats", {})

        col = ui_shared.draw_nav_bar(layout, self)

        slots = {}
        if hasattr(self, "get_slot_meta"):
            slots = {k: v.get("name", "Slot") for k, v in self.get_slot_meta().items()}

        if self.ui_tab == "SHAPE":
            if hasattr(self, "draw_shape_ui"):
                self.draw_shape_ui(col)
            layout.separator()
            layout.label(text="Transform", icon="OBJECT_ORIGIN")
            row = col.row(align=True)
            row.prop(self, "pivot_mode", text="")
            row.prop(self, "ui_use_rot", text="Rotate", toggle=True)
            if self.ui_use_rot:
                col.prop(self, "rotation", text="")
        elif self.ui_tab == "EDGES":
            ui_shared.draw_edge_slots_tab(col, self)
        elif self.ui_tab == "POLISH":
            ui_shared.draw_polish_tab(col, self)
        elif self.ui_tab == "DATA":
            ui_shared.draw_data_tab(col, self, slot_names=slots)
        elif self.ui_tab == "UVS":
            ui_shared.draw_uvs_tab(col, self, slot_names=slots, stats=stats)
        elif self.ui_tab == "SLOTS":
            ui_shared.draw_slots_tab(col, self, slots, stats)
        elif self.ui_tab == "COLLISION":
            ui_shared.draw_collision_tab(col, self, slots)
        elif self.ui_tab == "SOCKETS":
            ui_shared.draw_sockets_ui(col, self, slots)


# [REMOVED] MASSA_OT_ReRun_Active — replaced by dynamic dispatch from the UI.
# The N-panel button and the gizmo now call the cartridge operator directly with
# `rerun_mode=True`, and the existing `if self.rerun_mode:` branch in
# Massa_OT_Base.invoke() handles param restore from obj["MASSA_PARAMS"], transform
# capture, and scheduling deletion of the old object via `target_delete_name`.
# This eliminates the nested-operator + timer chain that was silently failing.
