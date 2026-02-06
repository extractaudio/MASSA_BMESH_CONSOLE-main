import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from ..modules import cartridges

class MASSA_OT_ConsoleParse(Operator):
    """
    Parses MCP commands and triggers internal operators.
    Used by mcp_bridge.py to execute agent commands.
    """
    bl_idname = "massa.console_parse"
    bl_label = "Massa Console Parse"
    bl_options = {'INTERNAL'}

    text: StringProperty(name="Command Text")

    def execute(self, context):
        cmd = self.text.strip()
        print(f"[MASSA CONSOLE] Parsing: {cmd}")

        if not cmd:
            return {'FINISHED'}

        parts = cmd.split()
        action = parts[0]
        args = parts[1:]

        if action == "create_cartridge":
            self.handle_create_cartridge(context, args)
        else:
            self.report({'WARNING'}, f"Unknown console command: {action}")

        return {'FINISHED'}

    def handle_create_cartridge(self, context, args):
        # Parse args: -shape box -slots 2
        params = {}
        for i in range(len(args)):
            if args[i].startswith("-") and i + 1 < len(args):
                key = args[i][1:]
                val = args[i+1]
                params[key] = val

        shape_id = params.get("shape")
        if not shape_id:
            self.report({'ERROR'}, "Missing -shape argument")
            return

        # Find cartridge
        target_mod = None
        for mod in cartridges.MODULES:
            meta = getattr(mod, "CARTRIDGE_META", {})
            if meta.get("id") == shape_id:
                target_mod = mod
                break

        if not target_mod:
            self.report({'ERROR'}, f"Cartridge ID '{shape_id}' not found")
            return

        # Find Operator Class
        op_idname = None
        # Look for the operator class in the module
        for name in dir(target_mod):
            obj = getattr(target_mod, name)
            # We check if it looks like a blender operator class
            if isinstance(obj, type) and issubclass(obj, bpy.types.Operator):
                if hasattr(obj, "bl_idname"):
                    op_idname = obj.bl_idname
                    break

        if not op_idname:
            self.report({'ERROR'}, f"Could not resolve Operator ID for {shape_id}")
            return

        print(f"[MASSA CONSOLE] Launching {op_idname} with {params}")

        # Prepare kwargs
        op_kwargs = {k: v for k, v in params.items() if k != "shape"}

        # Convert types (simple heuristic)
        clean_kwargs = {}
        for k, v in op_kwargs.items():
            if v.isdigit():
                clean_kwargs[k] = int(v)
            else:
                try:
                    clean_kwargs[k] = float(v)
                except ValueError:
                    clean_kwargs[k] = v

        # Call Operator
        try:
            op_func = self.get_op_func(op_idname)
            if op_func:
                # Use EXEC_DEFAULT to run immediately
                # Attempt to pass kwargs. If they fail (unrecognized), we might need to retry without them
                try:
                    op_func('EXEC_DEFAULT', **clean_kwargs)
                    self.report({'INFO'}, f"Created {shape_id}")
                except TypeError as e:
                    # Fallback: run without args if kwargs were invalid
                    print(f"[MASSA CONSOLE] Argument Mismatch: {e}. Running default.")
                    op_func('EXEC_DEFAULT')
                    self.report({'WARNING'}, f"Created {shape_id} (ignoring invalid args)")
            else:
                 self.report({'ERROR'}, f"Operator {op_idname} not found in bpy.ops")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to execute {op_idname}: {e}")

    def get_op_func(self, bl_idname):
        try:
            category, name = bl_idname.split(".")
            op_module = getattr(bpy.ops, category)
            return getattr(op_module, name)
        except:
            return None


class MASSA_OT_ResurrectSelected(Operator):
    """
    Bridge alias for Resurrect Wrapper.
    """
    bl_idname = "massa.resurrect_selected"
    bl_label = "Resurrect Selected (MCP)"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return hasattr(bpy.ops.massa, "resurrect_wrapper")

    def execute(self, context):
        try:
            bpy.ops.massa.resurrect_wrapper()
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Resurrection failed: {e}")
            return {'CANCELLED'}
