import bpy
import bmesh
import socket
import threading
import queue
import json
import base64
import tempfile
import os
from ..modules.debugging_system import runner, runner_console

# CONFIGURATION
HOST = '127.0.0.1'
PORT = 5555

# Thread-safe queue to pass commands from Socket -> Main Thread
execution_queue = queue.Queue()
_server_thread = None
_server_running = False

def stop_server():
    global _server_running
    print("[Bridge] Stopping Server...")
    _server_running = False
    if bpy.app.timers.is_registered(process_queue):
        bpy.app.timers.unregister(process_queue)

def analyze_mesh():
    obj = bpy.context.active_object
    if not obj: return {"error": "No Active Object"}
    if obj.type != 'MESH': return {"error": f"Object is {obj.type}, not MESH"}
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
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

def analyze_slots():
    obj = bpy.context.active_object
    if not obj: return {}
    slots = {}
    for p in obj.data.polygons:
        mid = p.material_index
        slots[mid] = slots.get(mid, 0) + 1
    return slots

def analyze_bounds():
    obj = bpy.context.active_object
    if not obj: return {"error": "No Active Object"}
    
    # Get dimensions and world location
    dims = list(obj.dimensions)
    loc = list(obj.location)
    
    # Get local bounding box (8 corners)
    bbox = [list(v) for v in obj.bound_box]
    
    return {
        "name": obj.name,
        "dimensions": dims,
        "location": loc,
        "bound_box": bbox,
        "scale": list(obj.scale)
    }

def capture_viewport(mode):
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

def socket_listener():
    """Runs in background thread. Waits for MCP commands."""
    global _server_running
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
            s.listen()
            s.settimeout(1.0) # Check for stop signal every second
            print(f"[Bridge] Listening on {PORT}...")
            
            while _server_running:
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                    
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

def process_queue():
    """Runs on Main Thread. Executes API calls safely."""
    while not execution_queue.empty():
        req, result_holder = execution_queue.get()
        data = {"status": "success"}
        
        try:
            skill = req.get('skill')
            params = req.get('params', {})

            # --- SKILL ROUTER ---
            
            if skill == 'get_server_config':
                console = bpy.context.scene.massa_console
                data["config"] = {
                    "use_direct_mode": console.mcp_use_direct_mode
                }

            elif skill == 'audit_cartridge_direct':
                path = params.get('path')
                mode = params.get('mode', 'AUDIT')
                payload = params.get('payload', {})
                data["report"] = runner.execute_audit(path, mode, payload, is_direct=True)

            elif skill == 'audit_console_direct':
                data["report"] = runner_console.execute_console_audit(is_direct=True)

            elif skill == 'console_command':
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
                data["telemetry"] = analyze_mesh()

            elif skill == 'get_slots':
                data["slots"] = analyze_slots()

            elif skill == 'get_bounds':
                data["bounds"] = analyze_bounds()

            elif skill == 'get_vision':
                data["image"] = capture_viewport(params.get('mode', 'WIRE'))

            elif skill == 'get_scene_info':
                limit = params.get('limit', 20)
                offset = params.get('offset', 0)
                obj_type = params.get('object_type')
                
                objects = []
                count = 0
                skipped = 0
                
                for obj in bpy.data.objects:
                    if obj_type and obj.type != obj_type:
                        continue
                        
                    if skipped < offset:
                        skipped += 1
                        continue
                        
                    if count >= limit:
                        break
                        
                    objects.append({
                        "name": obj.name,
                        "type": obj.type,
                        "location": list(obj.location),
                        "visible": not obj.hide_viewport
                    })
                    count += 1
                    
                data["scene_info"] = {
                    "total_objects": len(bpy.data.objects),
                    "returned": len(objects),
                    "objects": objects
                }

            elif skill == 'get_object_info':
                name = params.get('object_name')
                obj = bpy.data.objects.get(name)
                if obj:
                    # Health Checks
                    applied_scale = all(abs(s - 1.0) < 0.001 for s in obj.scale)
                    
                    data["object_info"] = {
                        "name": obj.name,
                        "type": obj.type,
                        "location": list(obj.location),
                        "rotation": list(obj.rotation_euler),
                        "scale": list(obj.scale),
                        "dimensions": list(obj.dimensions),
                        "modifiers": [m.name for m in obj.modifiers],
                        "constraints": [c.name for c in obj.constraints],
                        "parent": obj.parent.name if obj.parent else None,
                        "collections": [c.name for c in obj.users_collection],
                        "health_check": {
                            "applied_scale": applied_scale,
                            "has_uvs": bool(obj.data.uv_layers) if obj.type == 'MESH' else None
                        }
                    }
                else:
                    data = {"status": "error", "msg": f"Object '{name}' not found"}

            elif skill == 'execute_code':
                code = params.get('code')
                try:
                    # Capture stdout
                    import io
                    import contextlib
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        exec(code, {'bpy': bpy, 'bmesh': bmesh})
                    data["output"] = f.getvalue()
                except Exception as e:
                    data = {"status": "error", "msg": f"Execution Error: {str(e)}"}

            elif skill == 'create_bmesh':
                name = params.get('name', 'New_Object')
                script = params.get('script_content', '')
                
                try:
                    bm = bmesh.new()
                    # Safe context for script execution
                    local_vars = {
                        'bm': bm,
                        'bmesh': bmesh,
                        'bpy': bpy,
                        'mathutils': bpy.types.bpy_prop_collection, # weak mock, ideally import mathutils
                        'Vector': None, # Should verify if available
                        'Matrix': None,
                        'EPSILON': 0.0001
                    }
                    # Try to import mathutils if possible or assume it's there
                    import mathutils
                    local_vars['mathutils'] = mathutils
                    local_vars['Vector'] = mathutils.Vector
                    local_vars['Matrix'] = mathutils.Matrix
                    
                    exec(script, {}, local_vars)
                    
                    # Convert to Mesh
                    mesh = bpy.data.meshes.new(name)
                    bm.to_mesh(mesh)
                    bm.free()
                    
                    obj = bpy.data.objects.new(name, mesh)
                    bpy.context.collection.objects.link(obj)
                    
                    # Hard 10 Slot Mandate
                    required_slots = [
                        "Mat_Standard", "Mat_Glass", "Mat_Emission", "Mat_Dark",
                        "Mat_Metal", "Mat_Accent", "Mat_Utility", "Mat_Transparent",
                        "Mat_Scifi", "Mat_Detail" 
                    ] # Example placeholder slots if not defined elsewhere
                    
                    # Or just ensure 10 slots exist
                    for i in range(10):
                        mat_name = f"Slot_{i}"
                        mat = bpy.data.materials.get(mat_name)
                        if not mat:
                            mat = bpy.data.materials.new(mat_name)
                        obj.data.materials.append(mat)
                        
                    # Select
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    
                    data["msg"] = f"Created Object: {obj.name}"
                    
                except Exception as e:
                    data = {"status": "error", "msg": f"BMesh Script Error: {str(e)}"}

            else:
                data = {"status": "error", "msg": f"Unknown Skill: {skill}"}

        except Exception as e:
            data = {"status": "error", "msg": str(e)}
        
        result_holder.put(data)
    
    return 0.1 # Keep timer alive

class MASSA_OT_StartMCP(bpy.types.Operator):
    """Starts the MCP Listener Button in N-Panel"""
    bl_idname = "massa.start_mcp_server"
    bl_label = "Activate MCP Link"
    bl_description = "Opens Port for Antigravity Communication"
    
    def execute(self, context):
        global _server_thread, _server_running, PORT
        
        # [ARCHITECT UDPATE] Use Port from UI
        console = context.scene.massa_console
        new_port = console.mcp_port
        PORT = new_port # Update global PORT

        if not _server_thread or not _server_thread.is_alive():
            _server_running = True
            _server_thread = threading.Thread(target=socket_listener, daemon=True)
            _server_thread.start()
            
            # Register the queue processor to run every 0.1 seconds on Main Thread
            if not bpy.app.timers.is_registered(process_queue):
                bpy.app.timers.register(process_queue)
            
            self.report({'INFO'}, f"MCP Bridge Active on {HOST}:{PORT}")
        else:
            _server_running = True
            self.report({'WARNING'}, "MCP Bridge already active")
        return {'FINISHED'}

class MASSA_OT_StopMCP(bpy.types.Operator):
    """Stops the MCP Listener"""
    bl_idname = "massa.stop_mcp_server"
    bl_label = "Stop MCP Link"
    bl_description = "Closes the MCP Bridge Connection"

    def execute(self, context):
        stop_server()
        self.report({'INFO'}, "MCP Bridge Stopped")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MASSA_OT_StartMCP)
    bpy.utils.register_class(MASSA_OT_StopMCP)

def unregister():
    stop_server()
    bpy.utils.unregister_class(MASSA_OT_StartMCP)
    bpy.utils.unregister_class(MASSA_OT_StopMCP)

def is_running():
    return _server_running

def get_address():
    return f"{HOST}:{PORT}"