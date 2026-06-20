"""
MASSA MCP bridge module.

Bundles a Blender-side socket server (see ``server.py``) so the MASSA addon
can serve the `_MCP/blmcp` client directly — no separate upstream addon needed.
The server is OFF by default and must be started explicitly (operator or UI
button) because it execs arbitrary Python received on the socket.
"""

import bpy

from . import server


class MASSA_OT_MCPBridgeStart(bpy.types.Operator):
    bl_idname = "massa.mcp_bridge_start"
    bl_label = "Start MCP Server"
    bl_description = "Start the MASSA MCP bridge socket server (localhost:9876)"

    def execute(self, context):
        try:
            started = server.start_server()
        except OSError as ex:
            self.report({'ERROR'}, "Could not start MCP bridge: {:s}".format(str(ex)))
            return {'CANCELLED'}
        if started:
            self.report({'INFO'}, "MASSA MCP bridge started")
        else:
            self.report({'INFO'}, "MASSA MCP bridge already running")
        return {'FINISHED'}


class MASSA_OT_MCPBridgeStop(bpy.types.Operator):
    bl_idname = "massa.mcp_bridge_stop"
    bl_label = "Stop MCP Server"
    bl_description = "Stop the MASSA MCP bridge socket server"

    def execute(self, context):
        server.stop_server()
        self.report({'INFO'}, "MASSA MCP bridge stopped")
        return {'FINISHED'}


_CLASSES = (
    MASSA_OT_MCPBridgeStart,
    MASSA_OT_MCPBridgeStop,
)


def register():
    for cls in _CLASSES:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass


def unregister():
    # Make sure the socket/timer are torn down with the addon.
    try:
        server.stop_server()
    except Exception:  # pragma: no cover - defensive on shutdown
        pass
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
