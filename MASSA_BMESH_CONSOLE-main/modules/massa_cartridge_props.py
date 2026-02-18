import bpy
from .cartridges import MODULES
# We need to inspect the operator to copy properties
# We use a deferred import or string lookup to avoid circular dependencies if possible,
# but importing Massa_OT_Base is usually safe here as it is at the end of the chain.
from ..operators.massa_base import Massa_OT_Base
from .massa_properties import MassaPropertiesMixin

CARTRIDGE_PROP_CLASSES = {}

def register_cartridge_props():
    """
    Dynamically creates and registers PropertyGroup classes for each cartridge.
    These classes mirror the properties defined in the cartridge's Operator.
    """
    # 1. Identify properties to exclude (Base class properties)
    base_props = set()
    if hasattr(Massa_OT_Base, "__annotations__"):
        base_props.update(Massa_OT_Base.__annotations__.keys())

    if hasattr(MassaPropertiesMixin, "__annotations__"):
        base_props.update(MassaPropertiesMixin.__annotations__.keys())

    # Standard Blender properties to ignore
    exclude_names = {"bl_idname", "bl_label", "bl_description", "bl_options", "rna_type"}

    for mod in MODULES:
        meta = getattr(mod, "CARTRIDGE_META", {})
        cart_id = meta.get("id")
        if not cart_id:
            continue

        # Find Operator Class
        op_class = None
        for name, obj in mod.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, Massa_OT_Base) and obj != Massa_OT_Base:
                op_class = obj
                break

        if not op_class:
            continue

        # Extract unique properties
        # We sanitize the ID to make a valid class name (though ID is usually safe)
        safe_id = cart_id.replace(".", "_").replace("-", "_")
        cls_name = f"MASSA_PG_{safe_id}"

        cls_annotations = {}

        if hasattr(op_class, "__annotations__"):
            for k, v in op_class.__annotations__.items():
                if k in base_props or k in exclude_names:
                    continue
                # Copy the annotation (property definition)
                cls_annotations[k] = v

        if not cls_annotations:
            # Even if empty, we might want to register it to have a consistent handle?
            # Yes, so ui code doesn't break.
            pass

        # Define class
        # We must use type() to create the class dynamically
        # Inherit from PropertyGroup
        new_class = type(cls_name, (bpy.types.PropertyGroup,), {'__annotations__': cls_annotations})

        # Register
        try:
            bpy.utils.register_class(new_class)
            CARTRIDGE_PROP_CLASSES[cart_id] = new_class
        except ValueError:
            pass
        except Exception as e:
            print(f"MASSA ERROR: Failed to register props for {cart_id}: {e}")

def unregister_cartridge_props():
    for cls in CARTRIDGE_PROP_CLASSES.values():
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    CARTRIDGE_PROP_CLASSES.clear()

def get_cartridge_props_obj(scene, cart_id):
    """
    Helper to get the property group instance for a given cartridge ID
    from the scene.massa_console object.
    """
    console = getattr(scene, "massa_console", None)
    if not console:
        return None

    # We assume we will add PointerProperties to Massa_Console_Props
    # named "props_{cart_id}"
    prop_name = f"props_{cart_id}"
    return getattr(console, prop_name, None)
