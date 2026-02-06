import bpy
import bmesh
import socket
import threading
import queue
import json
import base64
import tempfile
import os

# CONFIGURATION
HOST = '127.0.0.1'
PORT = 5555

# Thread-safe queue to pass commands from Socket -> Main Thread
execution_queue = queue.Queue()

class MASSA_OT_StartMCP(bpy.types.Operator):
    """Starts the MCP Listener Button in N-Panel"""
    bl_idname = "massa.start_mcp_server"
    bl_label = "Activate MCP Link"
    bl_description = "Opens Port 5555 for Antigravity Communication"
    
    _server_thread = None

    def execute(self, context):
        if not self._server_thread or not self._server_thread.is_alive():
            self._server_thread = threading.Thread(target=self.socket_listener, daemon=True)
            self._server_thread.start()
            
            # Register the queue processor to run every 0.1 seconds on Main Thread
            bpy.app.timers.register(self.process_queue)
            
            self.report({'INFO'}, f"MCP Bridge Active on {HOST}:{PORT}")
        else:
            self.report({'WARNING'}, "MCP Bridge already active")
        return {'FINISHED'}

    def socket_listener(self):
        """Runs in background thread. Waits for MCP commands."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((HOST, PORT))
                s.listen()
                print(f"[Bridge] Listening on {PORT}...")
                
                while True:
                    conn, addr = s.accept()
                    with conn:
                        # Receive (Buffer for large scripts)
                        data = b""
                        while True:
                            chunk = conn.recv(4096)
                            if not chunk: break
                            data += chunk
                            if len(chunk) < 4096: break
                        
                        if data:
                            try:
                                request = json.loads(data.decode('utf-8'))
                                result_holder = queue.Queue()
                                execution_queue.put((request, result_holder))
                                
                                # Block until Main Thread processes request
                                response = result_holder.get()
                                conn.sendall(json.dumps(response).encode('utf-8'))
                            except Exception as e:
                                err = {"status": "error", "msg": str(e)}
                                conn.sendall(json.dumps(err).encode('utf-8'))
            except Exception as e:
                print(f"[Bridge] Critical Error: {e}")

    def process_queue(self):
        """Runs on Main Thread. Executes API calls safely."""
        while not execution_queue.empty():
            req, result_holder = execution_queue.get()
            data = {"status": "success"}
            
            try:
                skill = req.get('skill')
                params = req.get('params', {})

                # --- SKILL ROUTER ---
                
                if skill == 'console_command':
                    if hasattr(bpy.ops.massa, "console_parse"):
                        bpy.ops.massa.console_parse(text=params['command'])
                        data["msg"] = f"Executed: {params['command']}"
                    else:
                        data = {"status": "error", "msg": "Massa Console Operator not found"}

                elif skill == 'set_redo_prop':
                    obj = bpy.context.active_object
                    if obj:
                        for k, v in params.items():
                            if hasattr(obj, k):
                                try: setattr(obj, k, v)
                                except: pass
                        
                        # Trigger Resurrect
                        if hasattr(bpy.ops.massa, "resurrect_selected"):
                            bpy.ops.massa.resurrect_selected()
                        data["msg"] = "Properties updated & Mesh Resurrected"
                    else:
                        data = {"status": "error", "msg": "No Active Object"}

                elif skill == 'get_telemetry':
                    data["telemetry"] = self.analyze_mesh()

                elif skill == 'get_slots':
                    data["slots"] = self.analyze_slots()

                elif skill == 'get_vision':
                    data["image"] = self.capture_viewport(params.get('mode', 'WIRE'))

                else:
                    data = {"status": "error", "msg": f"Unknown Skill: {skill}"}

            except Exception as e:
                data = {"status": "error", "msg": str(e)}
            
            result_holder.put(data)
        
        return 0.1 # Keep timer alive

    def analyze_mesh(self):
        obj = bpy.context.active_object
        if not obj or obj.type != 'MESH': return {"error": "No Mesh"}
        
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        
        ghosts = [f.index for f in bm.faces if f.calc_area() < 0.00001]
        
        stats = {
            "verts": len(bm.verts),
            "faces": len(bm.faces),
            "is_manifold": all(e.is_manifold for e in bm.edges),
            "ghost_faces_count": len(ghosts),
            "ghost_indices": ghosts
        }
        bm.free()
        return stats

    def analyze_slots(self):
        obj = bpy.context.active_object
        if not obj: return {}
        slots = {}
        for p in obj.data.polygons:
            mid = p.material_index
            slots[mid] = slots.get(mid, 0) + 1
        return slots

    def capture_viewport(self, mode):
        path = os.path.join(tempfile.gettempdir(), "mcp_vision.png")
        # Simple viewport capture logic
        try:
            bpy.ops.render.opengl(write_still=True)
            img = bpy.data.images['Render Result']
            img.save_render(filepath=path)
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except:
            return ""