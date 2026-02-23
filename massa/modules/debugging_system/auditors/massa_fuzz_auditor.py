
import bpy
import bmesh
import random
import traceback

def audit_mesh(obj, op_class=None):
    """
    Fuzz Auditor:
    1. Instantiates the Operator Class.
    2. Identifies suitable parameters (Float, Int, Bool, Enum).
    3. Runs multiple iterations with randomized values.
    4. Checks for Crashes or Critical Topology failures.
    """
    errors = []
    
    if not op_class:
        return [] # Can't fuzz without the class
        
    print(f"[FUZZER] Starting Fuzz on {op_class.bl_idname}...")
    
    # 1. Instinctiate
    # We can't easily instantiate a bpy.types.Operator outside of context.
    # However, the runner already instantiated a MockOp if it was a headless run.
    # But here we are passed the CLASS.
    # We need to create an instance. 
    # Since our cartridges usually inherit from Massa_OT_Base which inherits from Operator,
    # AND they are designed to run in the 'main' block of the runner,
    # let's try to instantiate it as a plain Python object if possible,
    # or rely on the properties being accessible.
    
    try:
        op_instance = op_class()
    except Exception as e:
        # If standard instantiation fails (e.g. bpy restriction), 
        # we might need to rely on the fact that Blender properties are class descriptors.
        # But we need an instance to hold values.
        # If this fails, we skip fuzzing.
        errors.append(f"FUZZER_INIT_FAIL: {str(e)}")
        return errors

    # 2. Identify Parameters
    prop_defs = {}
    
    if hasattr(op_class, "bl_rna"):
        for key, prop in op_class.bl_rna.properties.items():
            if key not in {"rna_type", "bl_idname", "bl_label", "bl_description", "bl_options", "bl_undo_group", "script"}:
                prop_defs[key] = {
                    "type": prop.type,
                    "min": getattr(prop, "hard_min", -10),
                    "max": getattr(prop, "hard_max", 10),
                    "items": [i.identifier for i in prop.enum_items] if prop.type == 'ENUM' else []
                }
    elif hasattr(op_class, "__annotations__"):
        # Manual Parsing of bpy.props attributes
        for key, val in op_class.__annotations__.items():
            # Value is likely a tuple or keywords from the Property(...) call
            # We can't introspect standard Blender Property defines easily in pure python without registration?
            # Actually, `val` might be the result of FloatProperty(...) which is a function that returns a dict or specialized object.
            # In Headless, it's whatever bpy.props returns.
            # Let's try to deduce type from keywords if accessible (often kw_args).
            # If `val` has `keywords` attribute (common in many libraries), use it.
            
            p_type = 'UNKNOWN'
            p_min = -10
            p_max = 10
            p_items = []
            
            # Introspection Attempt
            keywords = getattr(val, 'keywords', {})
            if not keywords and isinstance(val, tuple):
                 # Sometimes it's (function, keywords)
                 # But in modern bpy it returns a descriptor-like thing.
                 pass

            # Duck Typing based on function name if available?
            # Or assume FLOAT if 'min'/'max' in keywords.
            
            # Let's default to parsing kw_args if valid
            if keywords:
                p_min = keywords.get('min', -10)
                p_max = keywords.get('max', 10)
                if 'items' in keywords:
                    p_type = 'ENUM'
                    p_items = [i[0] for i in keywords['items']]
                elif 'default' in keywords:
                    d = keywords['default']
                    if isinstance(d, float): p_type = 'FLOAT'
                    elif isinstance(d, int): p_type = 'INT'
                    elif isinstance(d, bool): p_type = 'BOOLEAN'
                
                # Correction if type ambiguous
                attr = getattr(val, 'function', None)
                if attr:
                    fname = getattr(attr, '__name__', '')
                    if 'Float' in fname: p_type = 'FLOAT'
                    elif 'Int' in fname: p_type = 'INT'
                    elif 'Bool' in fname: p_type = 'BOOLEAN'
                    elif 'Enum' in fname: p_type = 'ENUM'

            if p_type != 'UNKNOWN':
                prop_defs[key] = {
                    "type": p_type,
                    "min": p_min,
                    "max": p_max,
                    "items": p_items
                }

    if not prop_defs:
        # If we failed to find definitions, we can't fuzz reliably.
        # But we shouldn't fail hard if we just can't read them.
        # Just return info flag.
        return ["INFO_FUZZER_SKIPPED_NO_PARAMS"]

    # 3. Fuzz Loop
    ITERATIONS = 5
    
    for i in range(ITERATIONS):
        # Create a fresh BMesh for this iteration
        bm_fuzz = bmesh.new()
        
        # Randomize Params
        param_snapshot = {}
        for key, limits in prop_defs.items():
            
            val = None
            try:
                if limits["type"] == 'FLOAT':
                    val = random.uniform(limits["min"], limits["max"])
                    setattr(op_instance, key, val)
                    
                elif limits["type"] == 'INT':
                    val = random.randint(int(limits["min"]), int(limits["max"]))
                    setattr(op_instance, key, val)
                    
                elif limits["type"] == 'BOOLEAN':
                    val = random.choice([True, False])
                    setattr(op_instance, key, val)
                    
                elif limits["type"] == 'ENUM':
                    if limits["items"]:
                        val = random.choice(limits["items"])
                        setattr(op_instance, key, val)
                        
                if val is not None:
                    param_snapshot[key] = val
                    
            except Exception:
                continue # Skip failing props
        
        # Execute Build
        try:
            # Assume build_shape is the method
            if hasattr(op_instance, "build_shape"):
                op_instance.build_shape(bm_fuzz)
                
                # Tiny checks
                bm_fuzz.verts.ensure_lookup_table()
                if not bm_fuzz.verts:
                    errors.append(f"FUZZ_EMPTY_MESH_AT: {param_snapshot}")
                
            else:
                 errors.append("FUZZER_NO_BUILD_METHOD")
                 break
                 
        except Exception as e:
            # Capture the parameters that caused the crash
            crash_report = f"FUZZ_CRASH: {str(e)} | PARAMS: {param_snapshot}"
            errors.append(crash_report)
            
        finally:
            bm_fuzz.free()
            
    print(f"[FUZZER] Completed {ITERATIONS} iterations.")
    return errors
