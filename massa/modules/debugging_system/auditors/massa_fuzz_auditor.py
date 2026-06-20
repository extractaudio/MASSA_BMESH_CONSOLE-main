
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
    except Exception:
        # Fallback: build a stand-in when the operator can't be instantiated
        # outside Blender's operator context. Bind EVERY method from the class
        # hierarchy (not just build_shape) so helper calls inside build_shape —
        # e.g. self.create_socket_face(...) — resolve instead of raising.
        import inspect as _inspect

        class MockOperator:
            def report(self, *args, **kwargs):
                pass  # no-op stand-in for bpy.types.Operator.report

        op_instance = MockOperator()
        for attr_name in dir(op_class):
            if attr_name.startswith("__"):
                continue
            try:
                member = getattr(op_class, attr_name)
            except Exception:
                continue
            if _inspect.isfunction(member):
                try:
                    op_instance.__dict__[attr_name] = member.__get__(op_instance, MockOperator)
                except Exception:
                    pass

    # 2. Identify Parameters
    prop_defs = {}

    # Properties inherited from bpy.types.Operator (has_reports, bl_cursor_pending,
    # bl_idname, ...) are NOT cartridge parameters — fuzzing them is meaningless
    # and produces spurious crashes. Exclude the entire base-Operator surface.
    base_op_props = set()
    try:
        base_op_props = set(bpy.types.Operator.bl_rna.properties.keys())
    except Exception:
        base_op_props = {"rna_type", "bl_idname", "bl_label", "bl_description",
                         "bl_options", "bl_undo_group", "script"}

    def _sane_range(prop):
        # Prefer the UI-sensible soft range; unbounded props report hard limits
        # of +/-3.4e38 which would make random.uniform emit absurd values.
        CLAMP = 1000.0
        lo = getattr(prop, "soft_min", getattr(prop, "hard_min", -10))
        hi = getattr(prop, "soft_max", getattr(prop, "hard_max", 10))
        try:
            lo = max(float(lo), -CLAMP)
            hi = min(float(hi), CLAMP)
            if lo >= hi:
                lo, hi = -10.0, 10.0
        except (TypeError, ValueError):
            lo, hi = -10.0, 10.0
        return lo, hi

    # 2a. RNA Properties (Base class props mostly)
    if hasattr(op_class, "bl_rna"):
        for key, prop in op_class.bl_rna.properties.items():
            # Skip inherited Operator builtins and anything we can't write to.
            if key in base_op_props or getattr(prop, "is_readonly", False):
                continue
            if prop.type not in {'FLOAT', 'INT', 'BOOLEAN', 'ENUM'}:
                continue
            lo, hi = _sane_range(prop)
            prop_defs[key] = {
                "type": prop.type,
                "min": lo,
                "max": hi,
                # array_length > 1 marks a vector prop (e.g. FloatVectorProperty);
                # it must be fed a sequence, not a scalar, or build_shape unpacking fails.
                "array": getattr(prop, "array_length", 0),
                "items": [i.identifier for i in prop.enum_items] if prop.type == 'ENUM' else []
            }

    # 2b. Annotations (Python defined props - crucial for custom props in headless)
    if hasattr(op_class, "__annotations__"):
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
            p_array = 0
            if keywords:
                p_min = keywords.get('min', -10)
                p_max = keywords.get('max', 10)
                default_kw = keywords.get('default', None)

                if 'items' in keywords:
                    p_type = 'ENUM'
                    p_items = [i[0] for i in keywords['items']]
                elif isinstance(default_kw, bool):   # bool first: bool is a subclass of int
                    p_type = 'BOOLEAN'
                elif isinstance(default_kw, float):
                    p_type = 'FLOAT'
                elif isinstance(default_kw, int):
                    p_type = 'INT'

                # Vector props (FloatVectorProperty, etc.) expose a tuple/list default
                # or an explicit size= keyword and MUST be fed a sequence.
                if isinstance(default_kw, (tuple, list)):
                    p_array = len(default_kw)
                if 'size' in keywords:
                    try:
                        p_array = max(p_array, int(keywords['size']))
                    except (TypeError, ValueError):
                        pass

                # Correction if type ambiguous (derive from the Property fn name)
                attr = getattr(val, 'function', None)
                if attr:
                    fname = getattr(attr, '__name__', '')
                    if 'Float' in fname: p_type = 'FLOAT'
                    elif 'Int' in fname: p_type = 'INT'
                    elif 'Bool' in fname: p_type = 'BOOLEAN'
                    elif 'Enum' in fname: p_type = 'ENUM'

            # bl_rna (2a) is authoritative for type/range/array length. Only backfill
            # what it missed; for headless prop-less stubs bl_rna is empty so 2b adds
            # the entry. This stops a vector prop's array length being clobbered with a
            # scalar (which caused 'cannot unpack non-iterable float object' crashes).
            if key in prop_defs:
                if p_array > 1 and not prop_defs[key].get("array"):
                    prop_defs[key]["array"] = p_array
            elif p_type != 'UNKNOWN':
                prop_defs[key] = {
                    "type": p_type,
                    "min": p_min,
                    "max": p_max,
                    "array": p_array,
                    "items": p_items,
                }

            # Ensure the (mock) instance has a usable default for this key.
            if key in prop_defs and not hasattr(op_instance, key):
                info = prop_defs[key]
                arr = info.get("array", 0) or 0
                if keywords and keywords.get('default', None) is not None:
                    default_val = keywords['default']
                elif info["type"] == 'FLOAT':
                    default_val = (1.0,) * arr if arr > 1 else 1.0  # Safe non-zero default
                elif info["type"] == 'INT':
                    default_val = (1,) * arr if arr > 1 else 1
                elif info["type"] == 'BOOLEAN':
                    default_val = False
                elif info["type"] == 'ENUM' and info["items"]:
                    default_val = info["items"][0]
                else:
                    default_val = 0.0
                try:
                    setattr(op_instance, key, default_val)
                except Exception:
                    pass

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
            arr = limits.get("array", 0) or 0
            try:
                if limits["type"] == 'FLOAT':
                    if arr > 1:
                        val = tuple(random.uniform(limits["min"], limits["max"]) for _ in range(arr))
                    else:
                        val = random.uniform(limits["min"], limits["max"])
                    setattr(op_instance, key, val)

                elif limits["type"] == 'INT':
                    if arr > 1:
                        val = tuple(random.randint(int(limits["min"]), int(limits["max"])) for _ in range(arr))
                    else:
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
            tb = traceback.format_exc()
            crash_report = f"FUZZ_CRASH: {str(e)}\nTRACEBACK:\n{tb}\n | PARAMS: {param_snapshot}"
            errors.append(crash_report)
            
        finally:
            bm_fuzz.free()
            
    print(f"[FUZZER] Completed {ITERATIONS} iterations.")
    return errors
