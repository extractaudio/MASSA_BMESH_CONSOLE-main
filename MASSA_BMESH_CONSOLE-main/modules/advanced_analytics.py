import bpy
import bmesh
import inspect
import ast
import gpu
from gpu_extras.batch import batch_for_shader
import os
import tempfile
import base64
import blf
import bpy_extras

# --- HOLO-PROJECTOR (Visual Feedback) ---

class MCP_Overlay:
    def __init__(self):
        self.handler = None
        self.coords = []
        self.texts = [] # List of (pos, text)
        self.lines = [] # List of (start, end)
        self.shader_points = gpu.shader.from_builtin('UNIFORM_COLOR')
        self.shader_lines = gpu.shader.from_builtin('UNIFORM_COLOR')

    def set_highlights(self, coordinates):
        self.coords = coordinates
        self._refresh()

    def set_lines(self, lines):
        self.lines = lines
        self._refresh()

    def set_annotations(self, texts):
        # texts: list of tuples ( (x,y,z), "string" )
        self.texts = texts
        self._refresh()

    def clear(self):
        self.coords = []
        self.lines = []
        self.texts = []
        self._refresh()

    def _refresh(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    def draw(self):
        # Draw Points
        if self.coords:
            self.shader_points.bind()
            self.shader_points.uniform_float("color", (1, 0, 0, 1)) # Red
            gpu.state.point_size_set(8)
            batch = batch_for_shader(self.shader_points, 'POINTS', {"pos": self.coords})
            batch.draw(self.shader_points)

        # Draw Lines
        if self.lines:
            self.shader_lines.bind()
            self.shader_lines.uniform_float("color", (0, 1, 0, 1)) # Green
            gpu.state.line_width_set(2)
            flat_lines = []
            for p1, p2 in self.lines:
                flat_lines.extend([p1, p2])
            batch = batch_for_shader(self.shader_lines, 'LINES', {"pos": flat_lines})
            batch.draw(self.shader_lines)

        # Draw Text
        if self.texts:
            font_id = 0
            blf.size(font_id, 20)
            blf.color(font_id, 1, 1, 1, 1) # White

            # Need context to project 3D to 2D
            context = bpy.context
            region = context.region
            rv3d = context.region_data

            if region and rv3d:
                for pos_3d, text in self.texts:
                    # Project
                    pos_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, pos_3d)
                    if pos_2d:
                        blf.position(font_id, pos_2d.x, pos_2d.y, 0)
                        blf.draw(font_id, text)

# Global Instance
_overlay_instance = None

def get_overlay():
    global _overlay_instance
    if _overlay_instance is None:
        _overlay_instance = MCP_Overlay()
        bpy.types.SpaceView3D.draw_handler_add(_overlay_instance.draw, (), 'WINDOW', 'POST_VIEW')
    return _overlay_instance


# --- UI INTERCEPTOR (Context Awareness) ---

def parse_panel_ast(panel_idname):
    panel_cls = getattr(bpy.types, panel_idname, None)
    if not panel_cls: return {"error": f"Panel '{panel_idname}' not found"}

    try:
        source = inspect.getsource(panel_cls.draw)
    except OSError:
        return {"error": "Compiled source unavailable"}

    tree = ast.parse(source)
    ui_map = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'prop':
            # Extract property name
            prop_name = "Unknown"
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                 prop_name = node.args[1].value
            elif len(node.args) > 1 and isinstance(node.args[1], ast.Str): # Python < 3.8
                 prop_name = node.args[1].s

            # Extract label
            label = "Unknown"
            for k in node.keywords:
                if k.arg == 'text':
                    if isinstance(k.value, ast.Constant): label = k.value.value
                    elif isinstance(k.value, ast.Str): label = k.value.s

            ui_map.append({"label": label, "api_property": prop_name})

    return ui_map

def inspect_last_operator():
    last_op = None
    if len(bpy.context.window_manager.operators) > 0:
        last_op = bpy.context.window_manager.operators[-1]

    return {
        "running_operators": [op.bl_idname for op in bpy.context.window_manager.operators],
        "last_active": last_op.bl_idname if last_op else None
    }

# --- VISUAL CORTEX (Synthetic Vision) ---

def capture_analytical(mode):
    # Modes: SEGMENTATION, DEPTH_NORMALIZED, HEATMAP_DENSITY
    scene = bpy.context.scene

    # Find a 3D View
    area = None
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            area = a
            break

    if not area: return {"error": "No 3D View found"}
    space = area.spaces.active

    # Store State
    old_type = space.shading.type
    old_color_type = space.shading.color_type
    old_light = space.shading.light
    original_colors = {} # For Heatmap restoration
    temp_mat = None # For Depth

    try:
        if mode == 'SEGMENTATION':
            space.shading.type = 'SOLID'
            space.shading.color_type = 'RANDOM'
            space.shading.show_xray_wireframe = False
            space.overlay.show_overlays = False # Hide grid, etc.

        elif mode == 'DEPTH_NORMALIZED':
            space.shading.type = 'SOLID'
            space.shading.color_type = 'MATERIAL'
            space.shading.light = 'FLAT'
            space.overlay.show_overlays = False

            # Create Temp Depth Material
            temp_mat = bpy.data.materials.new(name="MCP_Depth_Analysis")
            temp_mat.use_nodes = True
            tree = temp_mat.node_tree
            nodes = tree.nodes
            links = tree.links
            nodes.clear()

            # Nodes: Camera Data -> View Z Depth -> Map Range -> Emission
            node_cam = nodes.new('ShaderNodeCameraData')
            node_map = nodes.new('ShaderNodeMapRange')
            # Normalize depth: 0.1 to 50.0m
            node_map.inputs[1].default_value = 0.1 # From Min
            node_map.inputs[2].default_value = 50.0 # From Max
            node_map.inputs[3].default_value = 0.0 # To Min (Black - Close)
            node_map.inputs[4].default_value = 1.0 # To Max (White - Far)

            node_emit = nodes.new('ShaderNodeEmission')
            node_out = nodes.new('ShaderNodeOutputMaterial')

            links.new(node_cam.outputs['View Z Depth'], node_map.inputs[0])
            links.new(node_map.outputs[0], node_emit.inputs['Color'])
            links.new(node_emit.outputs[0], node_out.inputs['Surface'])

            # Apply Override
            bpy.context.view_layer.material_override = temp_mat

        elif mode == 'HEATMAP_DENSITY':
            space.shading.type = 'SOLID'
            space.shading.color_type = 'OBJECT' # We will color objects
            space.overlay.show_overlays = False

            # Colorize objects
            max_verts = 0
            mesh_objs = [o for o in scene.objects if o.type == 'MESH']
            for o in mesh_objs:
                if len(o.data.vertices) > max_verts: max_verts = len(o.data.vertices)

            if max_verts > 0:
                for o in mesh_objs:
                    # Store original color (RGBA)
                    original_colors[o.name] = tuple(o.color)

                    count = len(o.data.vertices)
                    ratio = count / max_verts
                    # Heatmap: Blue (0) -> Red (1)
                    o.color = (ratio, 0, 1.0 - ratio, 1.0)

    except Exception as e:
        # Cleanup early if setup fails
        if temp_mat: bpy.data.materials.remove(temp_mat)
        bpy.context.view_layer.material_override = None
        for name, col in original_colors.items():
            o = bpy.data.objects.get(name)
            if o: o.color = col
        return {"error": str(e)}

    # Capture
    import tempfile
    import base64
    path = os.path.join(tempfile.gettempdir(), f"mcp_ana_{mode}.png")

    # We use 'Render Result' image
    data = ""
    try:
        with bpy.context.temp_override(window=bpy.context.window, area=area):
             bpy.ops.render.opengl(write_still=True, view_context=True)

        img = bpy.data.images.get('Render Result')
        if img:
            img.save_render(filepath=path)
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        data = f"Capture Error: {e}"

    # --- CLEANUP & RESTORE ---
    space.shading.type = old_type
    space.shading.color_type = old_color_type
    space.shading.light = old_light
    space.overlay.show_overlays = True

    if mode == 'DEPTH_NORMALIZED':
        bpy.context.view_layer.material_override = None
        if temp_mat: bpy.data.materials.remove(temp_mat)

    if mode == 'HEATMAP_DENSITY':
        for name, col in original_colors.items():
            o = bpy.data.objects.get(name)
            if o: o.color = col

    return data

# --- DEEP ANALYST (Data Forensics) ---

def audit_evaluated(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if not obj: return {"error": "Object not found"}

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)

    if eval_obj.type != 'MESH': return {"error": "Not a mesh"}

    mesh = eval_obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    stats = {
        "verts": len(bm.verts),
        "faces": len(bm.faces),
        "edges": len(bm.edges),
        "non_manifold": sum(1 for e in bm.edges if not e.is_manifold),
        "poles_5plus": sum(1 for v in bm.verts if len(v.link_edges) > 5),
    }

    try:
        stats["volume"] = mesh.calc_volume() # 5.0 API check
    except:
        pass

    bm.free()

    return stats

def trace_dependencies(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if not obj: return {}

    deps = {"parents": [], "constraints": [], "drivers": []}

    if obj.parent: deps["parents"].append(obj.parent.name)

    for c in obj.constraints:
        if hasattr(c, "target") and c.target:
            deps["constraints"].append({"name": c.name, "target": c.target.name})

    if obj.animation_data and obj.animation_data.drivers:
        for d in obj.animation_data.drivers:
            for v in d.driver.variables:
                for t in v.targets:
                    if t.id:
                        deps["drivers"].append({"path": d.data_path, "target": t.id.name})

    return deps

# --- GHOST SIMULATION ---

def simulate_stack(obj_name, modifier_setup):
    # modifier_setup: list of dicts {"type": "REMESH", "props": {"voxel_size": 0.1}}
    obj = bpy.data.objects.get(obj_name)
    if not obj: return {"error": "Object not found"}

    # Duplicate
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    bpy.context.collection.objects.link(new_obj)

    stats = {}
    try:
        # Apply Modifiers
        for mod_def in modifier_setup:
            mod = new_obj.modifiers.new(name="GhostMod", type=mod_def['type'])
            for k, v in mod_def.get('props', {}).items():
                if hasattr(mod, k):
                    setattr(mod, k, v)

        # Evaluate
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = new_obj.evaluated_get(depsgraph)

        # Measure
        stats = {
            "verts": len(eval_obj.data.vertices),
            "polys": len(eval_obj.data.polygons)
        }

    except Exception as e:
        stats = {"error": str(e)}

    finally:
        # Cleanup
        mesh_data = new_obj.data
        bpy.data.objects.remove(new_obj, do_unlink=True)
        # Fix Memory Leak: Remove the mesh data block
        if mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)

    return stats
