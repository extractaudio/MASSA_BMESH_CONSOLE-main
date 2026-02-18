import bpy

class MASSA_OT_ShootDispatcher(bpy.types.Operator):
    bl_idname = "massa.shoot_dispatcher"
    bl_label = "Shoot Generation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        console = context.scene.massa_console

        # 1. Get Parameters
        cart_id = console.massa_staged_cartridge

        # [ARCHITECT NEW] Check for Active Target Empty
        # If "Massa_Target" exists, it overrides the console coordinate
        target_obj = context.scene.objects.get("Massa_Target")
        if target_obj:
            console.massa_target_coord = target_obj.location[:]

        # Fix: bpy_prop_array doesn't have .copy(), use slicing to get a tuple/list copy
        target_loc = console.massa_target_coord[:]

        # 2. Save Cursor
        # Scene.cursor.location is a FloatVectorProperty, so slicing is safer here too
        cursor_loc = context.scene.cursor.location[:]

        # 3. Move Cursor to Target
        context.scene.cursor.location = target_loc

        # 4. Call Operator
        # We construct the operator name dynamically: massa.gen_{cart_id}
        op_id = f"gen_{cart_id}"

        try:
            if hasattr(bpy.ops.massa, op_id):
                # [ARCHITECT NEW] Parameter Injection Logic
                # Instead of INVOKE_DEFAULT (which uses defaults), we pull
                # from our persistent Console storage.

                kwargs = {}

                # A. Inject Cartridge-Specific Properties
                safe_id = cart_id.replace(".", "_").replace("-", "_")
                prop_name = f"props_{safe_id}"
                pg = getattr(console, prop_name, None)

                if pg:
                     pg_cls = type(pg)
                     if hasattr(pg_cls, "__annotations__"):
                         for k in pg_cls.__annotations__.keys():
                             val = getattr(pg, k)
                             # Convert to python types if needed
                             if hasattr(val, "to_tuple"):
                                 val = val.to_tuple()
                             elif hasattr(val, "to_list"):
                                 val = val.to_list()
                             kwargs[k] = val

                # B. Inject Global Parameters (MassaPropertiesMixin)
                from ..modules.massa_properties import MassaPropertiesMixin
                for k in MassaPropertiesMixin.__annotations__.keys():
                     val = getattr(console, k)
                     if hasattr(val, "to_tuple"):
                         val = val.to_tuple()
                     elif hasattr(val, "to_list"):
                         val = val.to_list()
                     kwargs[k] = val

                # C. Inject Slot Properties (0-9)
                slot_props = [
                    "mat_", "phys_mat_", "uv_mode_", "uv_scale_", "sep_",
                    "sock_", "off_", "prot_", "expand_",
                    "collision_shape_", "show_coll_", "phys_friction_", "phys_bounce_", "phys_bond_"
                ]
                for i in range(10):
                    for p in slot_props:
                        key = f"{p}{i}"
                        if hasattr(console, key):
                             val = getattr(console, key)
                             if hasattr(val, "to_tuple"): val = val.to_tuple()
                             kwargs[key] = val

                # Call with EXEC_DEFAULT + kwargs to inject parameters
                getattr(bpy.ops.massa, op_id)('EXEC_DEFAULT', **kwargs)
            else:
                self.report({'ERROR'}, f"Operator massa.{op_id} not found")
                # Restore cursor
                context.scene.cursor.location = cursor_loc
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to shoot {cart_id}: {e}")
            # Restore cursor
            context.scene.cursor.location = cursor_loc
            return {'CANCELLED'}

        # 5. Restore Cursor
        context.scene.cursor.location = cursor_loc

        # 6. Stay in Point Shoot Mode
        # console.massa_op_mode = 'ACTIVE'

        return {'FINISHED'}


class MASSA_OT_SpawnTarget(bpy.types.Operator):
    bl_idname = "massa.spawn_target"
    bl_label = "Spawn Target"
    bl_description = "Create or Select the Massa Target Empty"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        console = scene.massa_console

        # Check if exists
        target_name = "Massa_Target"
        obj = scene.objects.get(target_name)

        if not obj:
            # Create
            # empty_add uses 3D cursor by default if location not specified, or we specify
            saved_cursor = scene.cursor.location[:]
            scene.cursor.location = console.massa_target_coord

            bpy.ops.object.empty_add(type='PLAIN_AXES', location=console.massa_target_coord)
            obj = context.active_object
            obj.name = target_name
            obj.empty_display_size = 0.5
            obj.show_name = True

            scene.cursor.location = saved_cursor
        else:
            # Ensure visible
            obj.hide_viewport = False

        # Select
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {'FINISHED'}
