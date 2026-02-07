import bpy
from bpy.props import PointerProperty, EnumProperty, IntProperty, BoolProperty
from .massa_properties import MassaPropertiesMixin


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
        ],
        default="SHAPE",
    )

    mcp_port: IntProperty(
        name="Port",
        default=5555,
        min=1024,
        max=65535,
        description="Port for MCP Bridge Communication"
    )

    mcp_use_direct_mode: BoolProperty(
        name="Direct Execution",
        default=False,
        description="If True, MCP audits run in this Blender Instance (Modifies Active Scene)"
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
            ("PHYS", "Physics ID", "Physical Material IDs", "PHYSICS", 3),
            ("PARTS", "Part ID", "Slot Indices", "GROUP", 4),
            ("WEAR", "Wear", "Edge Wear Mask", "COLOR_RED", 5),
            ("THICK", "Thick/Flow", "Thickness or Flow Map", "COLOR_GREEN", 6),
            ("GRAV", "Gravity", "Gravity Dust/Dirt Map", "COLOR_BLUE", 7),
            ("CAVITY", "Cavity", "Ambient Occlusion / Cavity", "IMAGE_ALPHA", 8),
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


def register():
    bpy.utils.register_class(Massa_Console_Props)
    bpy.types.Scene.massa_console = PointerProperty(type=Massa_Console_Props)


def unregister():
    if hasattr(bpy.types.Scene, "massa_console"):
        del bpy.types.Scene.massa_console
    bpy.utils.unregister_class(Massa_Console_Props)
