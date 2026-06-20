import bpy
import sys
import os
import argparse
import json
import importlib
import time
import math
import base64
import io
import contextlib
import bmesh
import re

# 1. Setup Path to import your attached 'auditors' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(current_dir)) # Up 2 levels: modules/debugging_system -> modules -> root
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add parent of repo to sys.path so we can import 'massa' as a package
parent_of_repo = os.path.dirname(repo_root)
if parent_of_repo not in sys.path:
    sys.path.append(parent_of_repo)

def is_path_safe(filepath, base_dir=repo_root):
    """
    Validates that the given filepath is within the base_dir to prevent path traversal.
    """
    abs_filepath = os.path.abspath(filepath)
    abs_base_dir = os.path.abspath(base_dir)
    return os.path.commonpath([abs_filepath, abs_base_dir]) == abs_base_dir

# 2. Import your attached files
# NOTE: Ensure your attached files are in the 'auditors' folder
try:
    from . import auditors
except ImportError:
    try:
        import auditors
    except ImportError:
        pass

# =============================================================================
# SEVERITY MODEL
# -----------------------------------------------------------------------------
# Auditors emit free-form flag strings. Historically the runner marked an audit
# FAIL whenever *any* flag was present — including WARNING_/INFO_ flags such as
# INFO_FUZZER_SKIPPED_NO_PARAMS, which made nearly every headless audit report a
# false failure. We classify each flag by severity and only FAIL on CRITICAL.
# =============================================================================

# CRITICAL-looking flags that are routinely valid for this addon's cartridges
# (open shells, flat panels, thin industrial strips, box-mapped closed volumes).
# They are downgraded to WARNING so they surface in telemetry without failing
# an otherwise-healthy mesh.
SOFT_FLAG_TOKENS = (
    "NON_MANIFOLD",
    "OPEN_SHELL",
    "NO_PERIMETER",
    "FLAT_Z_AXIS",
    "NO_SEAMS_ON_COMPLEX_MESH",
    "THIN_FACES",
    "ISOLATED_SEAM",
)


def classify_flag(flag):
    """Map a single auditor flag string to 'critical' | 'warning' | 'info'."""
    f = str(flag).upper()
    if f.startswith("INFO_") or f.startswith("INFO "):
        sev = "info"
    elif f.startswith("WARNING_") or f.startswith("WARN"):
        sev = "warning"
    elif f.startswith("CRITICAL_"):
        sev = "critical"
    elif "CRASH" in f or "_ERROR" in f or "ERROR:" in f or "TRACEBACK" in f:
        # Unprefixed auditor/loader failures still count as hard failures.
        sev = "critical"
    else:
        # Unknown / legacy unprefixed strings: treat as warning, not failure.
        sev = "warning"

    if sev == "critical" and any(tok in f for tok in SOFT_FLAG_TOKENS):
        sev = "warning"
    return sev


def classify_flags(flags):
    """
    Group a flat list of flags into severity buckets (order-preserving,
    de-duplicated) and produce a summary count block.
    """
    buckets = {"critical": [], "warning": [], "info": []}
    seen = set()
    for flag in flags or []:
        flag = str(flag)
        if flag in seen:
            continue
        seen.add(flag)
        buckets[classify_flag(flag)].append(flag)

    buckets["summary"] = {
        "critical": len(buckets["critical"]),
        "warning": len(buckets["warning"]),
        "info": len(buckets["info"]),
        "total": len(seen),
    }
    return buckets


def _get_auditors_module():
    """Locate the loaded auditors package regardless of how it was imported."""
    if 'auditors' in sys.modules:
        return sys.modules['auditors']
    if 'massa.modules.debugging_system.auditors' in sys.modules:
        return sys.modules['massa.modules.debugging_system.auditors']
    if 'auditors' in globals():
        return globals()['auditors']
    return None


def _find_op_class():
    """Return the cartridge operator class loaded into globals (not the base)."""
    for name, val in globals().items():
        if name.startswith("MASSA_OT_") and isinstance(val, type) and name != "Massa_OT_Base":
            return val
    return None


def setup_massa_env():
    """
    Sets up the 'massa' package environment by aliasing the addon directory
    (which might have dashes) to a clean 'massa' package name in sys.modules.
    Absorbed from runner_console.py — used by CONSOLE_AUDIT mode.
    """
    import importlib.util

    # runner.py is in modules/debugging_system/
    # addon root is ../../  (i.e. the MASSA_BMESH_CONSOLE-main folder)
    addon_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

    init_path = os.path.join(addon_root, "__init__.py")
    if not os.path.exists(init_path):
        return False, f"__init__.py not found at {init_path}"

    try:
        spec = importlib.util.spec_from_file_location("massa", init_path)
        massa_mod = importlib.util.module_from_spec(spec)
        sys.modules["massa"] = massa_mod
        spec.loader.exec_module(massa_mod)

        if hasattr(massa_mod, "register"):
            massa_mod.register()
            return True, "Massa Registered Successfully"
        else:
            return False, "No register function in massa module"

    except Exception as e:
        import traceback
        return False, f"Setup Error: {str(e)}\n{traceback.format_exc()}"


def handle_console_audit(is_direct=False):
    """
    Runs the CONSOLE_AUDIT health checks.
    Verifies: addon registration, operator presence, MASSA_EDGE_SLOTS layer,
    and massa_op_id custom property on generated objects.
    Absorbed from runner_console.py.
    """
    report = {"status": "PASS", "errors": [], "logs": []}

    if not is_direct:
        ok, msg = setup_massa_env()
        report["logs"].append(msg)
        if not ok:
            report["status"] = "FAIL"
            report["errors"].append(msg)
            return report

        bpy.ops.wm.read_factory_settings(use_empty=True)

    # Test: Operator Registration
    if not hasattr(bpy.ops, "massa") or not hasattr(bpy.ops.massa, "gen_prim_con_beam"):
        report["status"] = "FAIL"
        report["errors"].append("Operator massa.gen_prim_con_beam not found in bpy.ops")
        return report

    # Test: Execution
    try:
        bpy.ops.massa.gen_prim_con_beam()
        obj = bpy.context.active_object
        if not obj:
            report["status"] = "FAIL"
            report["errors"].append("Operator ran but no active object found.")
            return report

        report["logs"].append(f"Created Object: {obj.name}")

        # Test: MASSA_EDGE_SLOTS layer
        bm_test = bmesh.new()
        bm_test.from_mesh(obj.data)
        bm_test.edges.ensure_lookup_table()
        edge_slots = bm_test.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            report["status"] = "FAIL"
            report["errors"].append("MASSA_EDGE_SLOTS layer missing from generated mesh.")
        else:
            report["logs"].append("confirmed: MASSA_EDGE_SLOTS present")
        bm_test.free()

        # Test: massa_op_id custom property
        if "massa_op_id" not in obj:
            report["status"] = "FAIL"
            report["errors"].append("Object missing 'massa_op_id' custom property.")
        elif obj["massa_op_id"] != "massa.gen_prim_con_beam":
            report["status"] = "FAIL"
            report["errors"].append(f"Incorrect massa_op_id: {obj.get('massa_op_id')}")

    except Exception as e:
        import traceback
        report["status"] = "FAIL"
        report["errors"].append(f"Runtime Error: {str(e)}\n{traceback.format_exc()}")

    return report


def prepare_cartridge_env():
    # Import required modules
    try:
        # Import using full package path 'massa.x.y' to support relative imports inside them
        import massa.operators.massa_base as massa_base_mod
        import massa.modules.massa_builder as massa_builder_mod
        import massa.modules.massa_properties as massa_props_mod

        globals()['Massa_OT_Base'] = massa_base_mod.Massa_OT_Base
        globals()['MassaBuilder'] = massa_builder_mod.MassaBuilder
        globals()['MassaPropertiesMixin'] = massa_props_mod.MassaPropertiesMixin
        return True
    except ImportError as e:
        print(f"Failed to import dependencies: {e}")
        return False

def fallback_basic_checks(obj):
    """
    Minimal built-in mesh checks used when the auditors package is unavailable.
    Non-mutating: reads the active UV layer rather than verify()-ing one into
    existence (which would have masked a genuinely missing UV layer).
    """
    errors = []
    if not obj or obj.type != 'MESH':
        return ["WARNING_OBJECT_NOT_MESH"]

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        # Check A: Zero-area faces
        zero_faces = [f.index for f in bm.faces if f.calc_area() < 0.000001]
        if zero_faces:
            errors.append(f"CRITICAL_ZERO_AREA_FACES_{len(zero_faces)}")

        # Check B: UV layer presence + pinched UVs (only if UVs exist)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            if len(bm.faces) > 0:
                errors.append("CRITICAL_MISSING_UV_LAYER")
        else:
            pinched = 0
            for f in bm.faces:
                uvs = [l[uv_layer].uv for l in f.loops]
                # Shoelace formula for UV area
                area = 0.5 * abs(sum(x0 * y1 - x1 * y0
                                     for ((x0, y0), (x1, y1)) in zip(uvs, uvs[1:] + [uvs[0]])))
                if area < 0.000001 and f.calc_area() > 0.000001:
                    pinched += 1
            if pinched:
                errors.append(f"WARNING_PINCHED_UV_FACES_{pinched}")
    finally:
        bm.free()
    return errors


def run_checks(obj):
    """
    Flat-list audit used by skill handlers (e.g. get_object_info). Runs the full
    auditor suite when available, otherwise the built-in fallback checks.
    Returns a de-duplicated ``list[str]`` of flags (legacy contract preserved).
    """
    if not obj or getattr(obj, "type", None) != 'MESH':
        return ["WARNING_OBJECT_NOT_MESH"]

    auditors_mod = _get_auditors_module()
    if not (auditors_mod and hasattr(auditors_mod, 'run_all_auditors')):
        return fallback_basic_checks(obj)

    # Register the operator class so bl_rna-dependent auditors (UI, fuzz) work.
    op_class = _find_op_class()
    if op_class:
        try:
            bpy.utils.register_class(op_class)
        except Exception:
            pass

    try:
        flags = list(auditors_mod.run_all_auditors(obj, op_class))
    except Exception as e:
        flags = [f"CRITICAL_AUDITOR_LOADER_FAILED: {str(e)}"] + fallback_basic_checks(obj)

    # De-duplicate while preserving order.
    seen, deduped = set(), []
    for f in flags:
        f = str(f)
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    return deduped


def gather_mesh_telemetry(obj):
    """
    Collect structured, JSON-serializable telemetry about an object so callers
    can parse Blender data without re-deriving it. Safe on non-mesh objects.
    """
    tel = {"name": getattr(obj, "name", None), "type": getattr(obj, "type", None)}
    if not obj or obj.type != 'MESH':
        return tel

    me = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        tri_faces = quad_faces = ngon_faces = 0
        tri_total = 0
        for f in bm.faces:
            n = len(f.verts)
            tri_total += max(n - 2, 0)
            if n == 3:
                tri_faces += 1
            elif n == 4:
                quad_faces += 1
            elif n > 4:
                ngon_faces += 1

        open_edges = sum(1 for e in bm.edges if len(e.link_faces) < 2)
        non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
        wire_edges = sum(1 for e in bm.edges if not e.link_faces)
        loose_verts = sum(1 for v in bm.verts if not v.link_edges)

        tel["geometry"] = {
            "verts": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "tris_equiv": tri_total,
            "tri_faces": tri_faces,
            "quad_faces": quad_faces,
            "ngon_faces": ngon_faces,
            "open_edges": open_edges,
            "non_manifold_edges": non_manifold,
            "wire_edges": wire_edges,
            "loose_verts": loose_verts,
            "is_watertight": (open_edges == 0 and non_manifold == 0 and len(bm.faces) > 0),
        }

        # Local-space bounds + world-space dimensions (accounts for scale).
        if bm.verts:
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            zs = [v.co.z for v in bm.verts]
            tel["bounds_local"] = {
                "min": [round(min(xs), 5), round(min(ys), 5), round(min(zs), 5)],
                "max": [round(max(xs), 5), round(max(ys), 5), round(max(zs), 5)],
            }
        tel["dimensions"] = [round(d, 5) for d in obj.dimensions]

        # MASSA edge-slot telemetry.
        slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if slot_layer is None:
            tel["edge_slots"] = {"layer_present": False}
        else:
            hist = {}
            for e in bm.edges:
                val = e[slot_layer]
                if val:
                    hist[val] = hist.get(val, 0) + 1
            tel["edge_slots"] = {
                "layer_present": True,
                "tagged_edges": sum(hist.values()),
                "histogram": {str(k): v for k, v in sorted(hist.items())},
            }

        # UV telemetry.
        uv_names = list(bm.loops.layers.uv.keys())
        uv_block = {"layers": uv_names, "layer_count": len(uv_names)}
        active_uv = bm.loops.layers.uv.active
        if active_uv is not None:
            us, vs = [], []
            collapsed = 0
            for f in bm.faces:
                if f.calc_area() <= 0.0001:
                    continue
                loops = f.loops
                uv_area = 0.0
                ring = [l[active_uv].uv for l in loops]
                for i, uv in enumerate(ring):
                    nxt = ring[(i + 1) % len(ring)]
                    uv_area += (uv.x * nxt.y) - (uv.y * nxt.x)
                    us.append(uv.x)
                    vs.append(uv.y)
                if abs(uv_area * 0.5) < 0.000001:
                    collapsed += 1
            if us:
                uv_block["bounds"] = {
                    "min": [round(min(us), 5), round(min(vs), 5)],
                    "max": [round(max(us), 5), round(max(vs), 5)],
                }
            uv_block["collapsed_faces"] = collapsed
        tel["uv"] = uv_block
    finally:
        bm.free()

    tel["materials"] = [m.name if m else None for m in obj.data.materials]
    tel["modifiers"] = [{"name": m.name, "type": m.type} for m in obj.modifiers]
    tel["transform"] = {
        "location": [round(v, 5) for v in obj.location],
        "rotation_euler": [round(v, 5) for v in obj.rotation_euler],
        "scale": [round(v, 5) for v in obj.scale],
    }
    # Resurrection metadata (only the safe, serializable keys).
    tel["massa_op_id"] = obj.get("massa_op_id")
    tel["has_massa_params"] = "MASSA_PARAMS" in obj
    tel["custom_prop_keys"] = [k for k in obj.keys()]
    return tel

def find_generated_object(exclude=None):
    if exclude is None: exclude = []
    # Try active
    obj = bpy.context.active_object
    if obj and obj not in exclude and obj.type == 'MESH':
        return obj
    # Try list
    for o in bpy.data.objects:
        if o.type == 'MESH' and o not in exclude:
            return o
    return None

def setup_visual_diff(obj_a, obj_b):
    # Red for A
    mat_a = bpy.data.materials.new(name="Red_Wire")
    mat_a.use_nodes = False
    mat_a.diffuse_color = (1.0, 0.0, 0.0, 1.0) # Red
    # Wireframe display in viewport
    obj_a.show_wire = True
    obj_a.show_all_edges = True
    obj_a.color = (1.0, 0.0, 0.0, 1.0)
    
    # Green for B
    mat_b = bpy.data.materials.new(name="Green_Wire")
    mat_b.use_nodes = False
    mat_b.diffuse_color = (0.0, 1.0, 0.0, 1.0) # Green
    obj_b.show_wire = True
    obj_b.show_all_edges = True
    obj_b.color = (0.0, 1.0, 0.0, 1.0)

    # Offset B slightly to prevent Z-fighting if identical
    obj_b.location.x += 0.01

def setup_camera(angle="ISO_CAM"):
    # Simple camera setup
    cam_data = bpy.data.cameras.new("Cam")
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    if angle == "ISO_CAM":
        cam_obj.location = (10, -10, 10)
        cam_obj.rotation_euler = (0.95, 0, 0.78)

def render_viewport(name):
    tmp_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"{name}.png")
    bpy.context.scene.render.filepath = tmp_path

    if bpy.app.background:
        # Use Workbench for software render
        bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
        # Configure Workbench for clarity
        bpy.context.scene.display.shading.light = 'FLAT'
        bpy.context.scene.display.shading.color_type = 'MATERIAL' # Use Material colors (for Heatmaps/UVs)
        # Ensure we show wireframes if set on objects
        # Workbench X-Ray might be needed for UV overlap checking?
        # Actually wireframe attribute on object works in Workbench.

        bpy.ops.render.render(write_still=True)
    else:
        # Use OpenGL render (viewport render)
        bpy.ops.render.opengl(write_still=True)
    return tmp_path

def image_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return None

# --- SKILL HANDLERS ---

def skill_get_scene_info(params):
    limit = params.get("limit", 20)
    offset = params.get("offset", 0)
    obj_type = params.get("object_type")
    
    all_objs = bpy.data.objects
    if obj_type:
        all_objs = [o for o in all_objs if o.type == obj_type]
        
    total_count = len(all_objs)
    subset = all_objs[offset : offset + limit]
    
    obj_list = []
    for o in subset:
        obj_list.append({
            "name": o.name,
            "type": o.type,
            "location": [round(v, 3) for v in o.location],
            "collection": [c.name for c in o.users_collection]
        })
        
    return {
        "status": "SUCCESS",
        "total_objects": total_count,
        "returned": len(obj_list),
        "objects": obj_list
    }

def skill_get_object_info(params):
    name = params.get("object_name")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "FAIL", "msg": f"Object '{name}' not found"}
        
    # Gather Info
    info = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(v, 4) for v in obj.location],
        "rotation_euler": [round(v, 4) for v in obj.rotation_euler],
        "scale": [round(v, 4) for v in obj.scale],
        "dimensions": [round(v, 4) for v in obj.dimensions],
        "parent": obj.parent.name if obj.parent else None,
        "collections": [c.name for c in obj.users_collection],
        "modifiers": [m.name for m in obj.modifiers],
        "constraints": [c.name for c in obj.constraints],
        "vertex_count": len(obj.data.vertices) if obj.type == 'MESH' else 0,
        "poly_count": len(obj.data.polygons) if obj.type == 'MESH' else 0
    }
    
    # Run Health Check (severity-aware: only CRITICAL flags fail the object)
    health = "PASS"
    issues = []
    if obj.type == 'MESH':
        issues = run_checks(obj)
        classified = classify_flags(issues)
        if classified["critical"]:
            health = "FAIL"
        elif classified["warning"]:
            health = "WARN"
        info["audit_summary"] = classified["summary"]

    info["health"] = health
    info["audit_issues"] = issues

    return {"status": "SUCCESS", "info": info}

def skill_transform_object(params):
    """
    Handles Move, Rotate, Scale
    """
    name = params.get("name")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "FAIL", "msg": f"Object '{name}' not found"}
        
    mode = params.get("mode", "ABSOLUTE")
    loc = params.get("location")
    rot = params.get("rotation") # Degrees
    scl = params.get("scale")
    
    # Location
    if loc:
        if mode == "RELATIVE":
            obj.location.x += loc[0]
            obj.location.y += loc[1]
            obj.location.z += loc[2]
        else:
            obj.location = loc
            
    # Rotation
    if rot:
        # Convert degrees to radians
        rot_rad = [math.radians(a) for a in rot]
        if mode == "RELATIVE":
            obj.rotation_euler.x += rot_rad[0]
            obj.rotation_euler.y += rot_rad[1]
            obj.rotation_euler.z += rot_rad[2]
        else:
            obj.rotation_euler = rot_rad
            
    # Scale
    if scl:
        if mode == "RELATIVE":
            obj.scale.x *= scl[0]
            obj.scale.y *= scl[1]
            obj.scale.z *= scl[2]
        else:
            obj.scale = scl
            
    # Update dependency graph
    bpy.context.view_layer.update()
    
    return {
        "status": "SUCCESS",
        "new_transforms": {
            "location": [round(v, 3) for v in obj.location],
            "rotation_deg": [round(math.degrees(v), 3) for v in obj.rotation_euler],
            "scale": [round(v, 3) for v in obj.scale]
        }
    }

def skill_get_vision(params):
    mode = params.get("mode", "SOLID")
    # Set view mode if possible (requires view3d context, tricky in background)
    # We'll just render whatever assume setup is okay.
    
    path = render_viewport("vision_dump")
    b64 = image_to_base64(path)
    
    return {
        "status": "SUCCESS",
        "image": b64, # Base64 data
        "path": path
    }

def skill_execute_code(params):
    code = params.get("code", "")
    try:
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        
        exec(code, globals())
        
        sys.stdout = old_stdout
        return {"status": "SUCCESS", "output": new_stdout.getvalue()}
    except Exception as e:
        import traceback
        import sys
        if 'old_stdout' in locals():
            sys.stdout = old_stdout
        return {"status": "FAIL", "msg": str(e), "errors": traceback.format_exc()}

def handle_skill_execution(payload):
    skill = payload.get("skill")
    params = payload.get("params", {})
    
    if skill == "get_scene_info":
        return skill_get_scene_info(params)
    elif skill == "get_object_info":
        return skill_get_object_info(params)
    elif skill == "transform_object":
        return skill_transform_object(params)
    elif skill == "get_vision":
        return skill_get_vision(params)
    elif skill == "execute_code":
        return skill_execute_code(params)
    else:
        return {"status": "FAIL", "msg": f"Unknown skill: {skill}"}


def execute_audit(cartridge_path, mode="AUDIT", payload=None, is_direct=False):
    """
    Executes the audit logic.
    is_direct: If True, skips scene clearing and uses current context.
    """
    if payload is None: payload = {}

    if not is_direct:
        # Clean Scene
        bpy.ops.wm.read_factory_settings(use_empty=True)

    # --- MODE CHECK ---
    
    if mode == "SKILL_EXEC":
        return handle_skill_execution(payload)

    if mode == "CONSOLE_AUDIT":
        return handle_console_audit(is_direct=is_direct)

    if mode == "VISUAL_DIFF":
        # 1. Run First Cartridge (Target A)
        if not is_path_safe(cartridge_path):
            return {"status": "FAIL", "message": f"Access Denied: Cartridge A path '{cartridge_path}' is outside authorized directory"}

        try:
            with open(cartridge_path) as f:
                exec(f.read(), globals())
        except Exception as e:
            return {"status": "FAIL", "message": f"Cartridge A Crash: {e}"}

        obj_a = find_generated_object()
        if not obj_a:
            return {"status": "FAIL", "message": "Cartridge A produced no object"}
        obj_a.name = "Version_A_Red"
        
        # 2. Run Second Cartridge (Target B)
        file_b = payload.get("filename_b")
        if file_b:
            if not os.path.isabs(file_b):
                 # Assume same dir as cartridge A if relative
                 file_b = os.path.join(os.path.dirname(cartridge_path), file_b)
            
            if not is_path_safe(file_b):
                return {"status": "FAIL", "message": f"Access Denied: Cartridge B path '{file_b}' is outside authorized directory"}

            if os.path.exists(file_b):
                try:
                    with open(file_b) as f:
                        exec(f.read(), globals())
                except Exception as e:
                    return {"status": "FAIL", "message": f"Cartridge B Crash: {e}"}
                
                obj_b = find_generated_object(exclude=[obj_a])
                if not obj_b:
                    return {"status": "FAIL", "message": "Cartridge B produced no object"}
                obj_b.name = "Version_B_Green"
                
                # 3. Setup Red/Green
                setup_visual_diff(obj_a, obj_b)
                
                # 4. Render
                output_path = render_viewport(f"diff_{obj_a.name}_vs_{obj_b.name}")
                return {"status": "SUCCESS", "image_path": output_path}
            else:
                 return {"status": "FAIL", "message": f"File B not found: {file_b}"}
        else:
             return {"status": "FAIL", "message": "filename_b missing in payload"}

    # Default AUDIT execution
    exec_time_ms = 0.0
    try:
        start_time = time.perf_counter()
        print(f"Runner: Checking cartridge {cartridge_path}")
        if os.path.exists(cartridge_path) and cartridge_path != "global_skill_placeholder.py":
            if not is_path_safe(cartridge_path):
                return {"status": "FAIL", "errors": [f"Access Denied: Cartridge path '{cartridge_path}' is outside authorized directory"]}

            print("Runner: File exists, executing...")
            prepare_cartridge_env()
            with open(cartridge_path) as f:
                code = f.read()

                # Replace relative imports using regex to handle variations
                # Use flexible whitespace matching
                code = re.sub(r'from\s+\.+\s*operators\.massa_base\s+import\s+Massa_OT_Base', '# [MOCKED] Massa_OT_Base', code)
                # Allow optional 'modules.' prefix for MassaBuilder
                code = re.sub(r'from\s+\.+\s*(?:modules\.)?massa_builder\s+import\s+MassaBuilder', '# [MOCKED] MassaBuilder', code)
                # Mock MassaPropertiesMixin
                code = re.sub(r'from\s+\.+\s*(?:modules\.)?massa_properties\s+import\s+MassaPropertiesMixin', '# [MOCKED] MassaPropertiesMixin', code)

                # Check for remaining relative imports
                if "from ." in code:
                    print("Runner WARNING: Relative imports found in code!")
                    for line in code.split('\n'):
                        if "from ." in line and not line.strip().startswith("#"):
                            print(f"  > {line}")

                exec(code, globals())

                # [AUTO-EXECUTE] If we just loaded an Operator, run it to generate the mesh
                op_class = None
                print("Runner: Scanning globals for MASSA_OT_...")
                for name, val in globals().items():
                    if name.startswith("MASSA_OT_"):
                         print(f"Runner: Found Global {name}")
                         if isinstance(val, type):
                             # Avoid picking up the Base class itself if imported
                             if name != "Massa_OT_Base":
                                 op_class = val
                                 break

                if op_class:
                    try:
                        # Ensure bpy is real
                        if hasattr(bpy, "utils") and hasattr(bpy, "ops"):
                            try:
                                bpy.utils.register_class(op_class)
                            except ValueError:
                                pass # Already registered

                            # Call Operator
                            idname = op_class.bl_idname
                            print(f"Runner: Found Operator {idname}")
                            if "." in idname:
                                cat, name = idname.split(".")
                                if hasattr(bpy.ops, cat):
                                    func = getattr(getattr(bpy.ops, cat), name)
                                    func() # Run!
                                    print(f"Runner: Executed {idname}")
                                else:
                                    print(f"Runner: Could not find category {cat} in bpy.ops")
                            else:
                                print(f"Runner: Invalid idname {idname}")
                    except Exception as e:
                        print(f"Runner Execution Error: {e}")
                        import traceback
                        traceback.print_exc()

        else:
             # If cartridge doesn't exist (and we aren't in SKILL_EXEC), it's okay if we just want to audit existing?
             # But usually audit runs the cartridge.
             # If placeholder, we skip exec.
             pass
             
        end_time = time.perf_counter()
        exec_time_ms = (end_time - start_time) * 1000
    except Exception as e:
        return {"status": "FAIL", "errors": [f"Syntax/Runtime Error: {str(e)}"]}

    # Find Mesh
    obj = find_generated_object()
    if not obj:
        # If we didn't run a cartridge, and there's no object, fail.
        # But if we are in a mode that expects one, we should error.
        if mode in ["AUDIT", "PERFORMANCE", "UV_HEATMAP", "CSG_DEBUG", "UV_INSPECT", "RENDER"]:
             return {"status": "FAIL", "errors": ["No Mesh Created by Cartridge or Found in Scene"]}

    if mode == "UV_HEATMAP":
        try:
             setup_uv_heatmap(obj)
             output_path = render_viewport(f"heatmap_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             return {"status": "FAIL", "message": f"Heatmap Error: {str(e)}"}

    if mode == "UV_INSPECT":
        try:
             # Generate a 2D mesh representation of the UV layout
             print(f"DEBUG: UV_INSPECT on {obj} Name:{obj.name} Type:{obj.type} Data:{obj.data}")
             setup_uv_layout_view(obj)
             output_path = render_viewport(f"uv_layout_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             import traceback
             traceback.print_exc()
             return {"status": "FAIL", "message": f"UV Inspect Error: {str(e)}"}

    if mode == "PERFORMANCE":
        poly_count = len(obj.data.polygons)
        vert_count = len(obj.data.vertices)

        crashes_blender = poly_count > 100000

        result = {
            "status": "SUCCESS",
            "mode": "PERFORMANCE",
            "object": obj.name,
            "execution_time_ms": round(exec_time_ms, 3),
            "poly_count": poly_count,
            "vert_count": vert_count,
            "budget_status": "FAIL" if crashes_blender else "PASS",
            "telemetry": gather_mesh_telemetry(obj),
        }
        return result

    if mode == "CSG_DEBUG":
        # Visualize Cutters
        cutters_found = 0
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.object:
                mod.object.hide_viewport = False
                mod.object.hide_render = False
                mod.object.display_type = 'WIRE'
                mod.object.show_wire = True
                cutters_found += 1
                
        if cutters_found == 0:
            return {"status": "FAIL", "message": "No Boolean Modifiers found to debug"}

        setup_camera(payload.get("camera_angle", "ISO_CAM"))
        output_path = render_viewport(f"csg_debug_{obj.name}")
        return {"status": "SUCCESS", "image_path": output_path, "cutters_visualized": cutters_found}

    if mode == "RENDER":
        setup_camera(payload.get("camera_angle", "ISO_CAM"))
        try:
             # Basic View Settings for clear render
             if obj:
                 obj.show_wire = (payload.get("shading") == "WIREFRAME")
                 if obj.show_wire:
                     obj.display_type = 'WIRE'
                 else:
                     obj.display_type = 'SOLID'
                     
             output_path = render_viewport(f"render_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             return {"status": "FAIL", "message": f"Render Error: {str(e)}"}

    # Default AUDIT execution
    # -------------------------------------------------------------------------
    # Run the full auditor suite (severity-aware) and attach rich telemetry so
    # the caller can both judge PASS/FAIL and inspect the underlying mesh data.
    # -------------------------------------------------------------------------
    op_class = _find_op_class()
    auditors_mod = _get_auditors_module()

    by_auditor = {}
    ran = []
    skipped = []
    if auditors_mod and hasattr(auditors_mod, 'run_all_auditors'):
        if op_class:
            try:
                bpy.utils.register_class(op_class)
            except Exception:
                pass
        try:
            detail = auditors_mod.run_all_auditors(obj, op_class, detailed=True)
            flags = detail.get("flags", [])
            by_auditor = detail.get("by_auditor", {})
            ran = detail.get("ran", [])
            skipped = detail.get("skipped", [])
        except TypeError:
            # Older auditors package without the detailed= kwarg.
            flags = list(auditors_mod.run_all_auditors(obj, op_class))
        except Exception as e:
            flags = [f"CRITICAL_AUDITOR_LOADER_FAILED: {str(e)}"]
    else:
        flags = fallback_basic_checks(obj)

    classified = classify_flags(flags)
    status = "FAIL" if classified["critical"] else "PASS"

    result = {
        "status": status,
        "mode": "AUDIT",
        "object": obj.name,
        "operator": getattr(op_class, "bl_idname", None),
        "summary": classified["summary"],
        "issues": {
            "critical": classified["critical"],
            "warning": classified["warning"],
            "info": classified["info"],
        },
        "auditors": {"ran": ran, "skipped": skipped, "by_auditor": by_auditor},
        "telemetry": gather_mesh_telemetry(obj),
        "execution_time_ms": round(exec_time_ms, 3),
        # Backward-compatible flat list of every flag found.
        "errors": classified["critical"] + classified["warning"] + classified["info"],
    }

    return result

def setup_uv_heatmap(obj):
    import bmesh
    
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    
    uv_layer = bm.loops.layers.uv.verify()
    
    # Create Vertex Color Layer for Heatmap
    vcol_layer = bm.loops.layers.color.new("Heatmap")
    
    blue = (0.0, 0.0, 1.0, 1.0)
    green = (0.0, 1.0, 0.0, 1.0)
    yellow = (1.0, 1.0, 0.0, 1.0)
    red = (1.0, 0.0, 0.0, 1.0)
    
    for f in bm.faces:
        # Calculate 3D Area
        area_3d = f.calc_area()
        
        # Calculate UV Area
        uvs = [l[uv_layer].uv for l in f.loops]
        # Shoelace formula
        area_uv = 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in zip(uvs, uvs[1:] + [uvs[0]])))
        
        if area_3d < 0.000001:
            ratio = 1.0
        else:
            if area_uv < 0.000001:
                ratio = 999.0 # Infinite stretch
            else:
                ratio = area_3d / area_uv
        
        # Simple heuristic for "Badness"
        if ratio > 5.0 or ratio < 0.2:
            col = red
        elif ratio > 2.0 or ratio < 0.5:
            col = yellow
        elif ratio > 1.2 or ratio < 0.8:
            col = green
        else:
            col = blue
            
        for l in f.loops:
            l[vcol_layer] = col

    bm.to_mesh(mesh)
    bm.free()
    
    # Setup Material to show Vertex Colors
    mat = bpy.data.materials.new(name="Heatmap_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Shader
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfDiffuse') # Simple diffuse
    
    # Vertex Color
    vcol = nodes.new('ShaderNodeVertexColor')
    vcol.layer_name = "Heatmap"
    
    links.new(vcol.outputs['Color'], bsdf.inputs['Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat
        
    # Ensure Render uses it
    obj.active_material = mat
    # Viewport
    obj.show_wire = True
    
    setup_camera()

def setup_uv_layout_view(obj):
    """
    Creates a new mesh where XY coordinates = UV coordinates of the original object.
    Used for visual inspection of packing and overlaps.
    """
    import bmesh

    bm_orig = bmesh.new()
    bm_orig.from_mesh(obj.data)
    bm_orig.faces.ensure_lookup_table()

    uv_layer = bm_orig.loops.layers.uv.verify()

    # Create new BMesh for UVs
    bm_uv = bmesh.new()

    # Iterate faces and recreate them in UV space (2D)
    for f in bm_orig.faces:
        uv_verts = []
        for l in f.loops:
            uv = l[uv_layer].uv
            # Create vert at (u, v, 0)
            # Note: We duplicate verts per face loop to simulate split UVs correctly
            # (UV islands are split in UV space even if connected in 3D)
            v = bm_uv.verts.new((uv.x, uv.y, 0))
            uv_verts.append(v)

        try:
            bm_uv.faces.new(uv_verts)
        except ValueError:
            pass # Degenerate face in UV space

    bm_orig.free()

    # Convert to Mesh Object
    mesh_uv = bpy.data.meshes.new("UV_Layout_Mesh")
    bm_uv.to_mesh(mesh_uv)
    bm_uv.free()

    uv_obj = bpy.data.objects.new("UV_Layout_Obj", mesh_uv)
    bpy.context.collection.objects.link(uv_obj)

    # Hide original
    obj.hide_render = True
    obj.hide_viewport = True

    # Material: Wireframe + Semi-transparent fill
    mat = bpy.data.materials.new(name="UV_Layout_Mat")
    mat.use_nodes = True
    # Wireframe display
    uv_obj.show_wire = True
    uv_obj.show_all_edges = True
    uv_obj.data.materials.append(mat)

    # Setup Orthographic Camera
    setup_camera()
    cam = bpy.context.scene.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 1.2 # Slightly larger than 1.0 to show margins
    cam.location = (0.5, 0.5, 10) # Center of 0-1 space
    cam.rotation_euler = (0, 0, 0) # Look down Z (default camera points down -Z in Blender if rot is 0,0,0? No, default is -Z)
    # Actually standard camera looks down -Z.
    # We want to look at XY plane.
    # Default camera:
    # Location (0,0,10)
    # Rotation (0,0,0) -> Points Down -Z.
    # Top of image is +Y, Right is +X.
    # This matches UV space orientation.

    # Add border for 0-1 bounds
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.5, 0.5, -0.1))
    plane = bpy.context.active_object
    plane.display_type = 'WIRE'
    plane.show_wire = True

def print_json(data):
    # default=str guarantees serialization never raises on stray Blender objects
    # (which would otherwise leave the launcher with "no data").
    print("---AUDIT_START---")
    try:
        print(json.dumps(data, default=str))
    except Exception as e:
        print(json.dumps({"status": "SYSTEM_FAILURE",
                          "message": f"Result serialization failed: {str(e)}"}))
    print("---AUDIT_END---")

def main():
    # Parse Args
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--cartridge", required=True)
    parser.add_argument(
        "--mode",
        default="AUDIT",
        choices=["AUDIT", "VISUAL_DIFF", "UV_HEATMAP", "UV_INSPECT",
                 "PERFORMANCE", "CSG_DEBUG", "RENDER", "SKILL_EXEC", "CONSOLE_AUDIT"]
    )
    parser.add_argument("--payload", default=None)
    
    args, _ = parser.parse_known_args(argv)

    payload = {}
    if args.payload:
        try: payload = json.loads(args.payload)
        except: pass

    # Execute
    result = execute_audit(args.cartridge, args.mode, payload, is_direct=False)

    # Print Result
    print_json(result)

if __name__ == "__main__":
    main()
