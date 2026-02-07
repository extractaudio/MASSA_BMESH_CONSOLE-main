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
from ..modules import cartridges
from ..modules import advanced_analytics

# CONFIGURATION
HOST = '127.0.0.1'
PORT = 5555

# Thread-safe queue to pass commands from Socket -> Main Thread
execution_queue = queue.Queue()
_server_thread = None
_server_running = False
LAST_OP_OBJECT_NAME = None

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

def get_context_for_space(space_type):
    """Finds a window/area with the given space type for context overrides."""
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == space_type:
                for region in area.regions:
                    if region.type == 'WINDOW':
                        return {
                            "window": window,
                            "screen": screen,
                            "area": area,
                            "region": region,
                            "scene": bpy.context.scene,
                        }
    return None

def find_node_tree(object_name, tree_type):
    obj = bpy.data.objects.get(object_name)
    if not obj: return None
    
    if tree_type == 'GEOMETRY':
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                return mod.node_group
    elif tree_type == 'SHADER':
        if obj.active_material and obj.active_material.node_tree:
            return obj.active_material.node_tree
            
    return None

import struct

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
                    try:
                        # 1. Read Length Header (4 bytes)
                        raw_len = recv_all(conn, 4)
                        if not raw_len: continue
                        
                        msg_len = struct.unpack('>I', raw_len)[0]
                        
                        # 2. Read Payload
                        data = recv_all(conn, msg_len)
                        if not data: continue
                        
                        request = json.loads(data.decode('utf-8'))
                        result_holder = queue.Queue()
                        execution_queue.put((request, result_holder))
                        
                        # Block until Main Thread processes request
                        response = result_holder.get()
                        
                        # 3. Send Response (Length Prefixed)
                        resp_bytes = json.dumps(response).encode('utf-8')
                        conn.sendall(struct.pack('>I', len(resp_bytes)) + resp_bytes)
                        
                    except Exception as e:
                        err = {"status": "error", "msg": str(e)}
                        try:
                            err_bytes = json.dumps(err).encode('utf-8')
                            conn.sendall(struct.pack('>I', len(err_bytes)) + err_bytes)
                        except: pass
        except Exception as e:
            print(f"[Bridge] Critical Error: {e}")

def recv_all(conn, n):
    """Helper to ensure exactly n bytes are read."""
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def process_queue():
    """Runs on Main Thread. Executes API calls safely."""
    while not execution_queue.empty():
        req, result_holder = execution_queue.get()
        data = {"status": "success"}
        
        try:
            skill = req.get('skill')
            params = req.get('params', {})
            
            # [ARCHITECT NEW] Track Selection Context
            global LAST_OP_OBJECT_NAME

            # --- SKILL ROUTER ---

            if skill == 'execute_contextual_op':
                op_id = params.get('op_id')
                space_type = params.get('space_type', 'VIEW_3D')
                
                ctx_override = get_context_for_space(space_type)
                if ctx_override:
                    try:
                        # Parse op_id (e.g., "view3d.view_all")
                        cat, name = op_id.split(".")
                        op_func = getattr(getattr(bpy.ops, cat), name)
                        
                        # Execute with override
                        with bpy.context.temp_override(**ctx_override):
                            op_func('EXEC_DEFAULT')
                            
                        data["msg"] = f"Executed {op_id} in {space_type}"
                    except Exception as e:
                        data = {"status": "error", "msg": f"Op Error: {str(e)}"}
                else:
                    data = {"status": "error", "msg": f"Context {space_type} not found"}

            elif skill == 'edit_node_graph':
                obj_name = params.get('object_name')
                tree_type = params.get('tree_type', 'GEOMETRY') # GEOMETRY or SHADER
                operation = params.get('operation') # ADD_NODE, CONNECT, SET_VALUE
                
                node_tree = find_node_tree(obj_name, tree_type)
                
                if node_tree:
                    try:
                        if operation == 'ADD_NODE':
                            node_type = params.get('node_type')
                            node = node_tree.nodes.new(type=node_type)
                            node.location = (0, 0) # Basic placement
                            data["msg"] = f"Added {node.name}"
                            
                        elif operation == 'CONNECT':
                            from_node = node_tree.nodes.get(params.get('from_node'))
                            to_node = node_tree.nodes.get(params.get('to_node'))
                            if from_node and to_node:
                                node_tree.links.new(
                                    from_node.outputs[params.get('from_socket', 0)],
                                    to_node.inputs[params.get('to_socket', 0)]
                                )
                                data["msg"] = "Linked nodes"
                            else:
                                data = {"status": "error", "msg": "Nodes not found"}
                                
                        elif operation == 'SET_VALUE':
                            node = node_tree.nodes.get(params.get('node_name'))
                            if node:
                                socket_idx = params.get('socket_index', 0)
                                val = params.get('value')
                                # Naively set default value
                                if socket_idx < len(node.inputs):
                                    node.inputs[socket_idx].default_value = val
                                    data["msg"] = f"Set {node.name} socket {socket_idx} to {val}"
                            else:
                                data = {"status": "error", "msg": "Node not found"}
                    except Exception as e:
                         data = {"status": "error", "msg": f"Node Edit Error: {str(e)}"}
                else:
                    data = {"status": "error", "msg": f"Node Tree not found on {obj_name}"}

            elif skill == 'inspect_evaluated_data':
                obj_name = params.get('object_name')
                obj = bpy.data.objects.get(obj_name)
                
                if obj:
                    depsgraph = bpy.context.evaluated_depsgraph_get()
                    eval_obj = obj.evaluated_get(depsgraph)
                    
                    # If mesh, get mesh data
                    if eval_obj.type == 'MESH':
                        data["evaluated_info"] = {
                            "name": eval_obj.name,
                            "vertices": len(eval_obj.data.vertices),
                            "polygons": len(eval_obj.data.polygons),
                            "bound_box": [list(v) for v in eval_obj.bound_box],
                             # Check if it has instances (typical for GeomNodes)
                            "is_instancer": eval_obj.is_instancer
                        }
                    else:
                        data["evaluated_info"] = {"type": eval_obj.type}
                else:
                     data = {"status": "error", "msg": f"Object {obj_name} not found"}

            elif skill == 'manage_action_slots':
                obj_name = params.get('object_name')
                obj = bpy.data.objects.get(obj_name)
                operation = params.get('operation') # CREATE, ASSIGN
                
                if obj and obj.animation_data:
                    try:
                        # BLENDER 5.0 SLOTTED ACTIONS API ASSUMPTION
                        # This API is speculative based on 5.0 roadmap (Animation Layers / Slots)
                        if not hasattr(obj.animation_data, "action_slots"):
                             # Fallback for 4.x or if API is different
                             data = {"status": "error", "msg": "API: action_slots not found (Blender Version?)"}
                        else:
                            slots = obj.animation_data.action_slots
                            
                            if operation == 'CREATE':
                                slot_name = params.get('slot_name', 'New_Slot')
                                new_slot = slots.new(name=slot_name)
                                data["msg"] = f"Created Slot: {new_slot.name}"
                                
                            elif operation == 'ASSIGN':
                                slot_name = params.get('slot_name')
                                action_name = params.get('action_name')
                                action = bpy.data.actions.get(action_name)
                                
                                if action:
                                    # Find slot
                                    target_slot = slots.get(slot_name)
                                    if target_slot:
                                        target_slot.action = action
                                        data["msg"] = f"Assigned {action_name} to {slot_name}"
                                    else:
                                         data = {"status": "error", "msg": f"Slot {slot_name} not found"}
                                else:
                                     data = {"status": "error", "msg": f"Action {action_name} not found"}
                    except Exception as e:
                        data = {"status": "error", "msg": f"Slot Error: {str(e)}"}
                else:
                    data = {"status": "error", "msg": "Object has no animation data"}

            elif skill == 'query_asset_browser':
                # Simple implementation: Lists local assets
                # Full asset browser search via API is complex without UI context
                assets = []
                for obj in bpy.data.objects:
                    if obj.asset_data:
                        assets.append({"name": obj.name, "type": "OBJECT", "library": "LOCAL"})
                for mat in bpy.data.materials:
                     if mat.asset_data:
                        assets.append({"name": mat.name, "type": "MATERIAL", "library": "LOCAL"})
                
                # Check attached libraries (simple listing)
                for lib in bpy.data.libraries:
                    assets.append({"name": lib.name, "type": "LIBRARY", "path": lib.filepath})
                    
                data["assets"] = assets

            elif skill == 'configure_eevee_next':
                settings = params.get('settings', {})
                scene = bpy.context.scene
                
                if hasattr(scene, "eevee"):
                    eevee = scene.eevee
                    # Apply known logical mappings for 5.0 / EEVEE Next
                    if "raytracing" in settings:
                        if hasattr(eevee, "use_raytracing"): eevee.use_raytracing = settings["raytracing"]
                    if "shadows" in settings:
                        if hasattr(eevee, "use_shadows"): eevee.use_shadows = settings["shadows"]
                    if "gtao" in settings:
                        if hasattr(eevee, "use_gtao"): eevee.use_gtao = settings["gtao"]
                        
                    data["msg"] = "EEVEE Next Configured"
                else:
                    data = {"status": "error", "msg": "EEVEE settings not found"}

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
                    
                    # Track result
                    if bpy.context.active_object:
                        LAST_OP_OBJECT_NAME = bpy.context.active_object.name
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
                    
                    # Track result (even if lost, we might want to know what it WAS)
                    # But ideally we track what we just operated on
                    LAST_OP_OBJECT_NAME = obj.name
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

            elif skill == 'test_generator_ui':
                try:
                    cart_id = params.get('cartridge_id')
                    create_params = params.get('creation_params', {})
                    mod_params = params.get('modification_params')
                    
                    # 1. Find Cartridge Module
                    target_mod = None
                    for mod in cartridges.MODULES:
                        meta = getattr(mod, "CARTRIDGE_META", {})
                        if meta.get("id") == cart_id:
                            target_mod = mod
                            break
                    
                    if not target_mod:
                        raise Exception(f"Cartridge ID '{cart_id}' not found")
                        
                    # 2. Reslove Operator
                    op_idname = None
                    for name in dir(target_mod):
                        obj = getattr(target_mod, name)
                        if isinstance(obj, type) and issubclass(obj, bpy.types.Operator):
                            if hasattr(obj, "bl_idname"):
                                op_idname = obj.bl_idname
                                break
                    
                    if not op_idname:
                        raise Exception(f"No Operator found for {cart_id}")

                    # 3. Get Operator Function
                    cat, name = op_idname.split(".")
                    op_func = getattr(getattr(bpy.ops, cat), name)
                    
                    # 4. Execute Creation
                    # Convert args to correct types if needed (Assuming params are already correct types from JSON)
                    print(f"[Bridge] Creating {cart_id} with {create_params}")
                    op_func('EXEC_DEFAULT', **create_params)
                    
                    obj = bpy.context.active_object
                    created_name = obj.name if obj else "Unknown"
                    print(f"[Bridge] Created: {created_name}")
                    
                    # 5. Modification & Resurrection (Optional)
                    if mod_params and obj:
                        # [FIX] Update MASSA_PARAMS for Resurrection to see the changes
                        if "MASSA_PARAMS" in obj:
                            # We must read, modify, and write back to trigger update
                            params_dict = dict(obj["MASSA_PARAMS"])
                            for k, v in mod_params.items():
                                params_dict[k] = v
                            obj["MASSA_PARAMS"] = params_dict
                        
                        # Also try setattr for live props (if any)
                        for k, v in mod_params.items():
                            if hasattr(obj, k):
                                try: setattr(obj, k, v)
                                except: pass
                        
                        if hasattr(bpy.ops.massa, "resurrect_selected"):
                            bpy.ops.massa.resurrect_selected()
                            
                        data["msg"] = f"Created {created_name} & Resurrected with mods"
                    else:
                        data["msg"] = f"Created {created_name}"
                        
                except Exception as e:
                     data = {"status": "error", "msg": f"Generator Error: {str(e)}"}

            elif skill == 'restore_last_selection':
                target_name = params.get('name') or LAST_OP_OBJECT_NAME
                
                if target_name:
                    obj = bpy.data.objects.get(target_name)
                    if obj:
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        bpy.context.view_layer.objects.active = obj
                        data["msg"] = f"Selection Restored: {obj.name}"
                        # Update Last Op to this for continuity
                        LAST_OP_OBJECT_NAME = obj.name
                    else:
                        data = {"status": "error", "msg": f"Object '{target_name}' not found"}
                else:
                    data = {"status": "error", "msg": "No previous selection recorded and no name provided"}

            elif skill == 'get_materials':
                # [Discovery State] Return list of materials in the blend file
                mats = [m.name for m in bpy.data.materials]
                data["materials"] = mats


            elif skill == 'organize_outliner':
                method = params.get('method', 'BY_NAME')
                rules = params.get('rules') or {}
                ignore_hidden = params.get('ignore_hidden', True)
                
                moved_count = 0
                created_collections = set()
                
                try:
                    # 1. Collect Objects to Process
                    # Use scene objects to ensure they are in the current context
                    to_process = []
                    for obj in bpy.context.scene.objects:
                        if ignore_hidden and obj.hide_viewport:
                            continue
                        # Skip if object is already in a sub-collection (optional, but good for idempotency)
                        # For now, we enforce the rule: Only move if it matches criteria and isn't already there?
                        # Actually, better to just enforce the new home.
                        to_process.append(obj)
                        
                    # 2. Iterate and Move
                    for obj in to_process:
                        target_col_name = None
                        
                        if method == 'BY_TYPE':
                            # Simple Type Mapping
                            target_col_name = obj.type.capitalize() + "s" # e.g. "Meshs" (sic) -> "Meshes" logic later if needed
                            if obj.type == 'MESH': target_col_name = "Geometry"
                            elif obj.type == 'LIGHT': target_col_name = "Lights"
                            elif obj.type == 'CAMERA': target_col_name = "Cameras"
                            elif obj.type == 'EMPTY': target_col_name = "Controllers"
                            
                        elif method == 'BY_NAME':
                            # Split by underscore or just take first word
                            # e.g. "Wall_001" -> "Wall"
                            if "_" in obj.name:
                                target_col_name = obj.name.split("_")[0]
                            elif "." in obj.name:
                                target_col_name = obj.name.split(".")[0]
                            else:
                                target_col_name = "Misc"
                                
                        elif method == 'BY_PREFIX':
                            # Check rules
                            for prefix, col_name in rules.items():
                                if obj.name.startswith(prefix):
                                    target_col_name = col_name
                                    break
                        
                        if target_col_name:
                            # 3. Create Collection if missing
                            if target_col_name not in bpy.data.collections:
                                new_col = bpy.data.collections.new(target_col_name)
                                bpy.context.scene.collection.children.link(new_col)
                                created_collections.add(target_col_name)
                            
                            target_col = bpy.data.collections[target_col_name]
                            
                            # 4. Link/Unlink
                            # Check if already linked
                            if target_col_name not in [c.name for c in obj.users_collection]:
                                target_col.objects.link(obj)
                                
                                # Unlink from old collections (except the target)
                                # Be careful not to unlink from everything if it results in orphan, 
                                # but link() above saves it.
                                for old_col in obj.users_collection:
                                    if old_col.name != target_col_name:
                                        # Only unlink if it's not a master collection we want to keep?
                                        # Standard behavior: Object usually resides in ONE collection for simple hierarchy
                                        old_col.objects.unlink(obj)
                                        
                                moved_count += 1
                    
                    data["msg"] = f"Organized {moved_count} objects into {len(created_collections)} collections."
                    data["collections_created"] = list(created_collections)
                    
                except Exception as e:
                    data = {"status": "error", "msg": f"Organization Failed: {str(e)}"}



            elif skill == 'inspect_cartridge_live':
                # Direct Visual Audit: Load -> Render -> Cleanup (Optional)
                cart_id = params.get('cartridge_id')
                cleanup = params.get('cleanup', True) # Default to true to keep scene clean
                
                # 1. Reuse Test Generator UI (Direct) to create it
                # We need to construct params similar to test_generator_ui
                create_req = {
                    'cartridge_id': cart_id,
                    'creation_params': params.get('creation_params', {})
                }
                
                # Call internal handler logic (can't easily call other skill in same loop without recursion risk)
                # So we copy the core logic or call a shared function. 
                # Let's use the 'bridge' instance? No, we are inside the function.
                # Just execute the creation logic manually.
                
                try:
                    # -- CREATION BLOCK --
                    target_mod = None
                    for mod in cartridges.MODULES:
                        meta = getattr(mod, "CARTRIDGE_META", {})
                        if meta.get("id") == cart_id:
                            target_mod = mod
                            break
                    if not target_mod: raise Exception(f"Cartridge {cart_id} not found")
                    
                    op_idname = None
                    for name in dir(target_mod):
                        obj = getattr(target_mod, name)
                        if isinstance(obj, type) and issubclass(obj, bpy.types.Operator):
                            if hasattr(obj, "bl_idname"):
                                op_idname = obj.bl_idname
                                break
                    if not op_idname: raise Exception(f"No Operator for {cart_id}")
                    
                    cat, name = op_idname.split(".")
                    op_func = getattr(getattr(bpy.ops, cat), name)
                    op_func('EXEC_DEFAULT', **create_req['creation_params'])
                    obj = bpy.context.active_object
                    # -- END CREATION --
                    
                    if not obj: raise Exception("Creation failed")
                    
                    # 2. Focus & Capture
                    # Frame Selected
                    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=bpy.context.window_manager.windows[0].screen.areas[0]):
                         # Try to find a 3D view
                         for area in bpy.context.screen.areas:
                             if area.type == 'VIEW_3D':
                                 for region in area.regions:
                                     if region.type == 'WINDOW':
                                         with bpy.context.temp_override(area=area, region=region):
                                            bpy.ops.view3d.view_selected()
                                            break
                    
                    # Capture
                    data["image"] = capture_viewport("SOLID")
                    data["object_name"] = obj.name
                    
                    # 3. Cleanup
                    if cleanup:
                        bpy.ops.object.delete()
                        data["msg"] = f" inspected {obj.name} and cleaned up."
                    else:
                        data["msg"] = f" inspected {obj.name} (kept in scene)."
                        
                except Exception as e:
                    data = {"status": "error", "msg": f"Inspection Failed: {str(e)}"}

            # --- ADVANCED ANALYZER SKILLS ---

            elif skill == 'get_analytical_vision':
                mode = params.get('mode', 'SEGMENTATION')
                data["image"] = advanced_analytics.capture_analytical(mode)

            elif skill == 'parse_ui_ast':
                panel_id = params.get('panel_idname')
                data["ui_map"] = advanced_analytics.parse_panel_ast(panel_id)

            elif skill == 'inspect_last_op':
                data["op_history"] = advanced_analytics.inspect_last_operator()

            elif skill == 'audit_evaluated_deep':
                obj_name = params.get('object_name') or (bpy.context.active_object.name if bpy.context.active_object else None)
                if obj_name:
                    data["audit"] = advanced_analytics.audit_evaluated(obj_name)
                else:
                    data = {"status": "error", "msg": "No Object Specified"}

            elif skill == 'trace_deps':
                obj_name = params.get('object_name') or (bpy.context.active_object.name if bpy.context.active_object else None)
                if obj_name:
                    data["dependencies"] = advanced_analytics.trace_dependencies(obj_name)
                else:
                    data = {"status": "error", "msg": "No Object Specified"}

            elif skill == 'set_viewport_overlay':
                action = params.get('action')
                overlay = advanced_analytics.get_overlay()

                if action == 'HIGHLIGHT':
                    coords = params.get('coords', [])
                    overlay.set_highlights(coords)
                    data["msg"] = f"Highlighted {len(coords)} points"
                elif action == 'LINES':
                    lines = params.get('lines', [])
                    overlay.set_lines(lines)
                    data["msg"] = f" drew {len(lines)} lines"
                elif action == 'ANNOTATE':
                    texts = params.get('texts', [])
                    overlay.set_annotations(texts)
                    data["msg"] = f"Annotated {len(texts)} labels"
                elif action == 'CLEAR':
                    overlay.clear()
                    data["msg"] = "Overlay Cleared"
                else:
                    data = {"status": "error", "msg": f"Unknown action: {action}"}

            elif skill == 'simulate_mod_stack':
                obj_name = params.get('object_name')
                modifiers = params.get('modifiers', [])
                data["simulation"] = advanced_analytics.simulate_stack(obj_name, modifiers)

            elif skill == 'create_scene':
                # [ARCHITECT UPDATE] File-Based Workflow support
                filepath = params.get('filepath')
                if filepath and os.path.exists(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            file_data = json.load(f)
                            # Layout might be at top level or under 'layout' key
                            layout = file_data.get('layout', file_data) if isinstance(file_data, dict) else file_data
                            print(f"[Bridge] Loaded layout from {filepath}")
                    except Exception as e:
                        print(f"[Bridge] Error loading file {filepath}: {e}")
                        layout = []
                else:
                    # Legacy / Direct Payload
                    layout = params.get('layout', [])
                    
                do_audit = params.get('audit', True)
                avoid_duplicates = params.get('avoid_duplicates', True)
                
                report = {
                    "created_objects": [],
                    "errors": [],
                    "audit_results": {}
                }
                
                # 1. Capture Pre-Stats
                pre_stats = {
                    "object_count": len(bpy.data.objects),
                    "selected": len(bpy.context.selected_objects)
                }
                report["pre_stats"] = pre_stats

                # 2. Iterate Layout
                for item in layout:
                    try:
                        obj_type = item.get('type', 'PRIMITIVE')
                        item_id = item.get('id')
                        name = item.get('name', f"New_{item_id}")
                        
                        # Intelligent Check: Avoid Duplicates
                        if avoid_duplicates and name and bpy.data.objects.get(name):
                            report["errors"].append(f"Skipped {name}: Object already exists (Duplicate Protection)")
                            continue
                            
                        p_cre = item.get('parameters', {})
                        trans = item.get('transforms', {})
                        
                        obj = None
                        
                        if obj_type == 'CARTRIDGE':
                            # Reuse Generator Logic (simplified locally)
                            # Find Cartridge
                            target_mod = None
                            for mod in cartridges.MODULES:
                                meta = getattr(mod, "CARTRIDGE_META", {})
                                if meta.get("id") == item_id:
                                    target_mod = mod
                                    break
                            
                            if target_mod:
                                # Resolving Op
                                op_idname = None
                                for n in dir(target_mod):
                                    o = getattr(target_mod, n)
                                    if isinstance(o, type) and issubclass(o, bpy.types.Operator):
                                        if hasattr(o, "bl_idname"):
                                            op_idname = o.bl_idname
                                            break
                                if op_idname:
                                    cat, op_name = op_idname.split(".")
                                    op_func = getattr(getattr(bpy.ops, cat), op_name)
                                    op_func('EXEC_DEFAULT', **p_cre)
                                    obj = bpy.context.active_object
                                else:
                                    report["errors"].append(f"No Operator for {item_id}")
                            else:
                                report["errors"].append(f"Cartridge {item_id} not found")

                        elif obj_type == 'PRIMITIVE':
                            # Basic Shapes
                            if item_id == 'cube':
                                bpy.ops.mesh.primitive_cube_add(size=p_cre.get('size', 2.0))
                            elif item_id == 'plane':
                                bpy.ops.mesh.primitive_plane_add(size=p_cre.get('size', 2.0))
                            elif item_id == 'sphere':
                                bpy.ops.mesh.primitive_uv_sphere_add(radius=p_cre.get('radius', 1.0))
                            else:
                                bpy.ops.mesh.primitive_cube_add() # Fallback
                            obj = bpy.context.active_object

                        # 3. Apply Transform
                        if obj:
                            if name: obj.name = name
                            
                            if 'location' in trans:
                                obj.location = trans['location']
                            if 'rotation' in trans:
                                # Assume degrees in JSON, convert to Radians for Blender
                                import math
                                rot_deg = trans['rotation']
                                obj.rotation_euler = (math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2]))
                            if 'scale' in trans:
                                obj.scale = trans['scale']
                            
                            # Track created
                            report["created_objects"].append(obj.name)
                            
                            # 4. Per-Object Audit (if requested)
                            if do_audit and obj.type == 'MESH':
                                # Basic Bounds Check (Real World Scale Sanity)
                                dims = obj.dimensions
                                if max(dims) > 1000 or max(dims) < 0.001:
                                     report["audit_results"][obj.name] = {"warning": f"Suspicious Scale: {list(dims)}"}
                                else:
                                     # Run full mesh analysis
                                     report["audit_results"][obj.name] = analyze_mesh()

                    except Exception as e:
                        report["errors"].append(f"Failed item {item.get('id')}: {str(e)}")

                # 5. Visual Capture
                if do_audit:
                    style = params.get('visual_style', 'SOLID')
                    report["visual_capture"] = capture_viewport(style)
                    
                data["report"] = report

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