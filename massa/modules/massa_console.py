import bpy
from bpy.props import PointerProperty, EnumProperty, IntProperty, BoolProperty, FloatVectorProperty
from .massa_properties import MassaPropertiesMixin

def get_cartridge_items(self, context):
    try:
        from .cartridges import MODULES
    except ImportError:
        return []

    items = []
    for i, mod in enumerate(MODULES):
        meta = mod.CARTRIDGE_META
        # Identifier, Name, Description, Icon, ID
        items.append((meta["id"], meta["name"], meta.get("description", ""), meta.get("icon", "MESH_CUBE"), i))
    return items

class Massa_Console_Props(bpy.types.PropertyGroup, MassaPropertiesMixin):
    """
    THE BRAIN: Persistent Storage.
    Lives on bpy.types.Scene. Survives restarts.
    All shared properties inherited from MassaPropertiesMixin.
    """

    # --- CONSOLE-ONLY: POINT & SHOOT MODE ---
    massa_op_mode: EnumProperty(
        name="Operation Mode",
        items=[
            ("ACTIVE", "Active (Redo)", "Standard generation on active object"),
            ("POINT_SHOOT", "Point & Generate", "Targeted generation at 3D cursor/point"),
        ],
        default="ACTIVE",
    )

    massa_target_coord: FloatVectorProperty(
        name="Target Coordinate",
        size=3,
        subtype="TRANSLATION",
        default=(0.0, 0.0, 0.0),
    )

    massa_staged_cartridge: EnumProperty(
        name="Staged Cartridge",
        items=get_cartridge_items,
        description="Cartridge to generate in Point & Shoot mode",
    )


def register():
    # Dynamic Property Generation
    from .massa_cartridge_props import register_cartridge_props, CARTRIDGE_PROP_CLASSES
    register_cartridge_props()

    # Inject PointerProperties into Console Props
    # This allows persistent storage of per-cartridge parameters
    for cart_id, cls in CARTRIDGE_PROP_CLASSES.items():
        safe_id = cart_id.replace(".", "_").replace("-", "_")
        prop_name = f"props_{safe_id}"
        Massa_Console_Props.__annotations__[prop_name] = PointerProperty(type=cls)

    bpy.utils.register_class(Massa_Console_Props)
    bpy.types.Scene.massa_console = PointerProperty(type=Massa_Console_Props)


def unregister():
    if hasattr(bpy.types.Scene, "massa_console"):
        del bpy.types.Scene.massa_console
    bpy.utils.unregister_class(Massa_Console_Props)

    from .massa_cartridge_props import unregister_cartridge_props
    unregister_cartridge_props()
