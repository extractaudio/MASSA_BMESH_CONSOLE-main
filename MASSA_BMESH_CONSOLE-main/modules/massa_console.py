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
    """

    # --- 1. UI STATE OVERRIDES ---
    ui_tab: EnumProperty(
        name="Tab",
        items=[
            ("SHAPE", "Shape", "Base Geometry", "MOD_BUILD", 0),
            ("DATA", "Data", "Surface Data & Wear", "BRUSH_DATA", 1),
            ("POLISH", "Polish", "Modifiers & Refinement", "MOD_SMOOTH", 2),
            ("UVS", "UVs", "Unwrapping & Seams", "GROUP_UVS", 3),
            ("SLOTS", "Slots", "Material Assignments", "MATERIAL", 4),
            ("EDGES", "Edges", "Edge Role Interpreter", "EDGESEL", 5),
            ("COLLISION", "Collision", "Physics & Collision", "PHYSICS", 6),
        ],
        default="SHAPE",
    )



    # --- 2. GLOBAL VISUALIZATION (Redefined with ICONS) ---
    # The "Preview" Menu
    debug_view: EnumProperty(
        name="Preview",
        description="Global Overlay Mode",
        items=[
            ("NONE", "Final", "Show Final Result", "SHADING_RENDERED", 0),
            ("UV", "UV Check", "UV Checker Map", "UV", 1),
            ("SEAM", "Seams", "Seam Inspection (Neutral)", "EDGE_SEAM", 2),
            ("DATA_SET_1", "Set 1 (RGBW)", "Show Set 1 Channels (Wear, Thick, Grav, Cavity)", "BRUSH_DATA", 5),
            ("DATA_SET_2", "Set 2 (Alt)", "Show Set 2 Channels (Edge, Flow, Cover, Peak)", "BRUSH_DATA", 6),
            ("PHYS", "Physics ID", "Physical Material IDs", "PHYSICS", 3),
            ("PARTS", "Part ID", "Slot Indices", "GROUP", 4),
            ("PROTECT", "Protect", "Seam Protection Mask", "LOCKED", 9),
        ],
        default="NONE",
    )

    # --- 3. EDGE SLOT DEFINITIONS ---
    edge_action_items = [
        ("IGNORE", "Ignore", "Do nothing with these edges", "X", 0),
        ("SEAM", "Seam", "Mark as UV Seam", "EDGE_SEAM", 1),
        ("SHARP", "Sharp", "Mark as Sharp", "EDGE_SHARP", 2),
        ("CREASE", "Crease", "Mark as Subsurf Crease", "EDGE_CREASE", 3),
        ("BEVEL", "Bevel", "Mark for Bevel Modifier", "EDGE_BEVEL", 4),
        ("BOTH", "Seam+Sharp", "Mark as both", "MOD_EDGESPLIT", 5),
    ]

    edge_slot_1_action: EnumProperty(
        name="Slot 1 (Perimeter)", items=edge_action_items, default="BOTH"
    )
    edge_slot_2_action: EnumProperty(
        name="Slot 2 (Contour)", items=edge_action_items, default="SHARP"
    )
    edge_slot_3_action: EnumProperty(
        name="Slot 3 (Guide)", items=edge_action_items, default="SEAM"
    )
    edge_slot_4_action: EnumProperty(
        name="Slot 4 (Detail)", items=edge_action_items, default="IGNORE"
    )
    edge_slot_5_action: EnumProperty(
        name="Slot 5 (Fold)", items=edge_action_items, default="IGNORE"
    )

    # --- VISUALIZATION ---
    viz_edge_mode: EnumProperty(
        name="Edge Viz",
        items=[
            ("OFF", "Off", "Standard View", "X", 0),
            ("NATIVE", "Native", "Show Blender Overlays", "OVERLAY", 1),
            ("SLOTS", "Slots", "Show Colored Edge Slots (Shader)", "SHADING_WIRE", 2),
        ],
        default="NATIVE",
    )

    # --- 4. POINT & SHOOT MODE ---
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
