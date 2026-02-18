import bpy
import sys
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, StringProperty
from ..modules.massa_properties import MassaPropertiesMixin
from ..modules import massa_engine
from ..utils import mat_utils


class Massa_OT_Base(Operator, MassaPropertiesMixin):
    """
    THE MUSCLE: Executes the generation pipeline.
    [PATCHED v4.7]: Fixed Material Injection Logic & DB Sync.
    """

    bl_idname = "massa.base_gen"
    bl_label = "Massa Base"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- UI PROPERTIES (Syncs with Console) ---
    ui_tab: EnumProperty(
        name="Tab",
        items=[
            ("SHAPE", "Shape", "Base Geometry", "MOD_BUILD", 0),
            ("DATA", "Data", "Surface Data & Wear", "BRUSH_DATA", 1),
            ("POLISH", "Polish", "Modifiers & Refinement", "MOD_SMOOTH", 2),
            ("UVS", "UVs", "Unwrapping & Seams", "GROUP_UVS", 3),
            ("SLOTS", "Slots", "Material Assignments", "MATERIAL", 4),
            ("EDGES", "Edges", "Edge Role Interpreter", "EDGESEL", 5),
            ("COLLISION", "Collision", "Collision & Physics", "PHYSICS", 6),
            ("SOCKETS", "Sockets", "Socket Generation", "EMPTY_AXIS", 7),
        ],
        default="SHAPE",
    )

    # Visualization (Synced)
    debug_view: EnumProperty(
        name="Preview",
        items=[
            ("NONE", "Final", "Show Final Result", "SHADING_RENDERED", 0),
            ("UV", "UV Check", "UV Checker Map", "UV", 1),
            ("SEAM", "Seams", "Seam Inspection (Neutral)", "EDGE_SEAM", 2),
            ("DATA_SET_1", "Set 1 (RGBW)", "Show Set 1 Channels (Wear, Thick, Grav, Cavity)", "BRUSH_DATA", 5),
            ("DATA_SET_2", "Set 2 (Alt)", "Show Set 2 Channels (Edge, Flow, Cover, Peak)", "BRUSH_DATA", 6),
            ("PHYS", "Physics ID", "Physical Material IDs", "PHYSICS", 3),
            ("PARTS", "Part ID", "Slot Indices", "GROUP", 4),
            ("PROTECT", "Protect", "Seam Protection Mask", "LOCKED", 9),
        ],
        default="NONE",
    )

    # Global UV Overrides
    auto_unwrap: BoolProperty(name="Auto Smart UV", default=False, description="Force Smart UV Project on result")
    auto_unwrap_margin: FloatProperty(
        name="Margin", default=0.02, min=0.001, max=0.5, description="Island Margin for Auto Unwrap"
    )

    viz_edge_mode: EnumProperty(
        name="Viz",
        items=[
            ("OFF", "Off", "Standard View", "X", 0),
            ("NATIVE", "Native", "Show Blender Overlays", "OVERLAY", 1),
            ("SLOTS", "Slots", "Show Colored Edge Slots (Shader)", "SHADING_WIRE", 2),
        ],
        default="NATIVE",
    )

    # Edge Actions
    edge_action_items = [
        ("IGNORE", "Ignore", "Do nothing with these edges", "X", 0),
        ("SEAM", "Seam", "Mark as UV Seam", "EDGE_SEAM", 1),
        ("SHARP", "Sharp", "Mark as Sharp", "EDGE_SHARP", 2),
        ("CREASE", "Crease", "Mark as Subsurf Crease", "EDGE_CREASE", 3),
        ("BEVEL", "Bevel", "Mark for Bevel Modifier", "EDGE_BEVEL", 4),
        ("BOTH", "Both", "Mark as both", "MOD_EDGESPLIT", 5),
    ]

    edge_slot_1_action: EnumProperty(name="S1", items=edge_action_items, default="BOTH")
    edge_slot_2_action: EnumProperty(
        name="S2", items=edge_action_items, default="SHARP"
    )
    edge_slot_3_action: EnumProperty(name="S3", items=edge_action_items, default="SEAM")
    edge_slot_4_action: EnumProperty(
        name="S4", items=edge_action_items, default="IGNORE"
    )
    edge_slot_5_action: EnumProperty(
        name="S5", items=edge_action_items, default="IGNORE"
    )

    # [ARCHITECT NEW] Internal flag for Resurrection Mode
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
        except:
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

                # [ARCHITECT FIX] Skip Generic to allow Surface Map Fallbacks (Debug Colors)
                if phys_id == "GENERIC":
                    continue

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
        all_keys = list(MassaPropertiesMixin.__annotations__.keys())
        for i in range(10):
            all_keys.extend(
                [
                    f"mat_{i}",
                    f"sep_{i}",
                    f"uv_mode_{i}",
                    f"expand_{i}",
                    f"phys_mat_{i}",
                    f"uv_scale_{i}",
                    f"sock_{i}",
                    f"off_{i}",
                    f"prot_{i}",
                    f"collision_shape_{i}",
                    f"show_coll_{i}",
                    f"phys_friction_{i}",
                    f"phys_bounce_{i}",
                    f"phys_bond_{i}",
                ]
            )
        all_keys.extend(
            [
                "ui_tab",
                "edge_slot_1_action",
                "edge_slot_2_action",
                "edge_slot_3_action",
                "edge_slot_4_action",
                "edge_slot_5_action",
                "viz_edge_mode",
                "debug_view",
                "seam_from_edges",
                "seam_use_peri",
                "seam_use_cont",
                "seam_use_guide",
                "seam_use_detail",
                "seam_use_fold",
                "phys_gen_ucx",
                "phys_bake_strain",
                "phys_kinematic_pin",
                "phys_auto_rig",
                "phys_yield_strength",
                "sock_enable",
                "sock_constraint_type",
                "sock_break_strength",
                "sock_visual_size",
            ]
        )

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
            except:
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
                    for k, v in params.items():
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
                            except:
                                pass

                    # 3. Destroy Old Object (Full Re-Birth)
                    # [ARCHITECT FIX] Ensure we only delete the target object
                    # MOVED TO EXECUTE TO SUPPORT REDO
                    self.target_delete_name = obj.name

                except Exception as e:
                    print(f"Massa Resurrection Error: {e}")

        # [LEGACY/FALLBACK] Check for Resurrection Payload from Wrapper
        elif "MASSA_TEMP_RESTORE" in context.scene:
            try:
                restore_data = context.scene["MASSA_TEMP_RESTORE"]
                for k, v in restore_data.items():
                    if k.startswith("mat_") or k.startswith("phys_mat_"):
                        continue
                    if hasattr(self, k):
                        try:
                            setattr(self, k, v)
                        except:
                            pass
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


class MASSA_OT_ReRun_Active(Operator):
    bl_idname = "massa.rerun_active"
    bl_label = "Update Active Object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and "massa_op_id" in context.active_object

    def execute(self, context):
        obj = context.active_object
        op_id = obj.get("massa_op_id")
        saved_matrix = obj.matrix_world.copy()

        # [ARCHITECT NEW] Capture parameters before deletion
        massa_params = None
        if "MASSA_PARAMS" in obj:
            try:
                massa_params = dict(obj["MASSA_PARAMS"].items())
            except:
                pass

        if massa_params:
            # [ARCHITECT FIX] Inject current transform so the operator property matches the visual location
            # This ensures the Redo Panel starts with the correct values instead of jumping to 0,0,0
            massa_params["obj_location"] = obj.location[:]
            massa_params["obj_rotation"] = obj.rotation_euler[:]
            context.scene["MASSA_TEMP_RESTORE"] = massa_params

        if not obj.select_get():
            obj.select_set(True)
        bpy.ops.object.delete()
        op_category, op_name = "", ""
        if "." in op_id:
            op_category, op_name = op_id.split(".")
        elif "_OT_" in op_id:
            parts = op_id.split("_OT_")
            op_category = parts[0].lower()
            op_name = parts[1]
        else:
            return {"CANCELLED"}
        try:
            op_module = getattr(bpy.ops, op_category)
            op_func = getattr(op_module, op_name)
            op_func("INVOKE_DEFAULT")
        except:
            return {"CANCELLED"}
        new_obj = context.active_object
        if new_obj:
            new_obj.matrix_world = saved_matrix
        return {"FINISHED"}
