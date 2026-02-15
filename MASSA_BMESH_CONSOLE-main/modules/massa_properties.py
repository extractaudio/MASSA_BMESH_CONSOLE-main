import bpy
from bpy.props import (
    FloatProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty,
)
from ..utils.mat_utils import get_material_items, get_phys_items, UV_MAP_ITEMS


class MassaPropertiesMixin:
    """
    The DNA of Massa.
    Inherited by Massa_OT_Base (Muscle) and Massa_Console_Props (Brain).
    """

    # --- GLOBAL ---
    global_scale: FloatProperty(name="Global Scale", default=1.0, min=0.01)
    draft_mode: BoolProperty(name="Draft Mode", default=False)

    # --- TRANSFORM ---
    pivot_mode: EnumProperty(
        name="Pivot Alignment",
        items=[
            ("ORIGIN", "Cartridge Default", "Use script pivot"),
            ("Z_MIN", "Bottom (Z-Min)", "Sit on Grid"),
            ("CENTER", "Center Mass", "Geometric Center"),
            ("Z_MAX", "Top (Z-Max)", "Hang from Top"),
        ],
        default="ORIGIN",
    )
    ui_use_rot: BoolProperty(name="Rotate", default=False)
    rotation: FloatVectorProperty(name="Rotation", size=3)

    use_weld: BoolProperty(name="Weld", default=True)

    # --- LOGIC (SHADING) ---
    edge_mode: EnumProperty(
        name="Edge Logic",
        items=[
            ("ANGLE", "Angle", ""),
            ("SLOTS", "Slots", ""),
            ("HYBRID", "Hybrid", ""),
        ],
        default="HYBRID",
    )
    edge_angle: FloatProperty(
        name="Sharp Angle", default=30.0, description="Visual Shading Threshold"
    )

    # --- SEAM LOGIC (UVs) ---
    seam_active: BoolProperty(name="Write Seams", default=False)

    # 1. DRIVERS
    seam_from_angle: BoolProperty(name="Seam from Angle", default=True)
    seam_angle_limit: FloatProperty(
        name="Seam Angle",
        default=60.0,
        min=1.0,
        max=180.0,
        description="Angle to force a UV cut (Independent of shading)",
    )
    seam_from_slots: BoolProperty(name="Seam from Slots", default=True)
    
    # [ARCHITECT NEW] Auto-Unwrap Global Overrides
    auto_unwrap: BoolProperty(
        name="Auto Smart UV",
        default=False,
        description="Force Smart UV Project on result",
    )
    auto_unwrap_margin: FloatProperty(
        name="Margin",
        default=0.02,
        min=0.001,
        max=0.5,
        description="Island Margin for Auto Unwrap",
    )

    # [ARCHITECT NEW] Edge Role Drivers
    seam_from_edges: BoolProperty(
        name="Seam from Edges",
        default=True,
        description="Use Cartridge Edge Roles to drive seams",
    )

    # [ARCHITECT NEW] The "Bias" / Selector for Edge Roles
    seam_use_peri: BoolProperty(
        name="Perimeter (1)", default=True, description="Cut Outer Boundaries"
    )
    seam_use_cont: BoolProperty(
        name="Contour (2)", default=True, description="Cut Major Form Changes"
    )
    seam_use_guide: BoolProperty(
        name="Guide (3)", default=False, description="Cut Flow Lines"
    )
    seam_use_detail: BoolProperty(
        name="Detail (4)", default=False, description="Cut Panel Lines"
    )
    seam_use_fold: BoolProperty(
        name="Fold (5)", default=False, description="Cut Fold Lines"
    )

    # 2. CLEANUP
    seam_cleanup_flat: BoolProperty(name="Remove Flat Seams", default=False)
    seam_cleanup_thresh: FloatProperty(
        name="Flat Tol",
        default=5.0,
        min=0.1,
        max=45.0,
        description="Degrees deviation to consider 'flat' (The Enforcer)",
    )

    # 3. BIAS
    seam_bias: EnumProperty(
        name="Seam Bias",
        items=[
            ("BALANCED", "Balanced", "Cut all sharp angles"),
            ("CONVEX", "Expose (Convex)", "Prioritize ridges (Baking)"),
            ("CONCAVE", "Hide (Concave)", "Prioritize valleys (Environment)"),
        ],
        default="BALANCED",
    )

    # 4. SOLVER SETTINGS
    seam_solver_mode: EnumProperty(
        name="Auto-Seam",
        items=[
            ("NONE", "None", "Use Angle/Drivers only"),
            ("HARD_SURFACE", "Hard Surface", "Planar Graph Clustering"),
            ("STRIP", "Strip", "Quad Strip Following"),
            ("SMART_TUBE", "Smart Tube", "1-Cut Unroll (Zipper)"),
            ("ORGANIC", "Organic", "Cylinder Detective"),
            ("BOX_STRIP", "Box Strip", "Legacy Wall Unrolling"),
        ],
        default="HARD_SURFACE",
    )

    seam_cluster_tol: FloatProperty(
        name="Planar Tolerance",
        default=15.0,
        min=0.1,
        max=90.0,
        description="Hard Surface: Max angle deviation from chart seed",
    )

    seam_orient: EnumProperty(
        name="Zipper Align",
        items=[
            ("BACK", "Back (-Y)", "Hide seam on negative Y"),
            ("FRONT", "Front (+Y)", "Force seam to front"),
            ("LEFT", "Left (-X)", "Force seam to negative X"),
            ("RIGHT", "Right (+X)", "Force seam to positive X"),
            ("BOTTOM", "Bottom (-Z)", "Force seam to bottom"),
        ],
        default="BACK",
    )

    seam_straightness: FloatProperty(
        name="Straightness",
        default=2.0,
        min=0.0,
        max=10.0,
        description="Organic: Penalty for twisting seams",
    )

    ui_tab: EnumProperty(
        name="Tab",
        items=[
            ("SHAPE", "Shape", ""),
            ("DATA", "Data", ""),
            ("POLISH", "Polish", ""),
            ("UVS", "UVs", ""),
            ("SLOTS", "Slots", ""),
            ("EDGES", "Edges", ""),
        ],
        default="SHAPE",
    )

    # --- POLISH: STRUCTURE ---
    pol_solidify_active: BoolProperty(name="Solidify", default=False)
    pol_solidify_thick: FloatProperty(name="Thickness", default=0.05)
    pol_bridge_active: BoolProperty(name="Bridge Loops", default=False)
    pol_triangulate_active: BoolProperty(name="Triangulate", default=False)
    pol_triangulate_method: EnumProperty(
        items=[("BEAUTY", "Beauty", ""), ("FIXED", "Fixed", "")], default="BEAUTY"
    )
    pol_holes_active: BoolProperty(name="Fill Holes", default=False)
    pol_holes_sides: IntProperty(name="Sides", default=4, min=3)
    pol_symmetrize_active: BoolProperty(name="Symmetrize", default=False)
    pol_symmetrize_dir: EnumProperty(
        items=[
            ("POS_X", "-X to +X", ""),
            ("POS_Y", "-Y to +Y", ""),
            ("POS_Z", "-Z to +Z", ""),
            ("NEG_X", "+X to -X", ""),
            ("NEG_Y", "+Y to -Y", ""),
            ("NEG_Z", "+Z to -Z", ""),
        ],
        default="POS_X",
    )

    # --- POLISH: REFINEMENT ---
    pol_merge_mode: EnumProperty(
        name="Merge Mode",
        items=[
            ("NONE", "None", "Do not merge parts"),
            ("WELD", "Weld (Fast)", "Merge vertices by distance"),
            ("BOOLEAN", "Boolean (Hard)", "Union intersection (Creates Edges)"),
        ],
        default="WELD",
    )

    pol_fuse_active: BoolProperty(name="SDF Fuse", default=False)
    pol_fuse_radius: FloatProperty(name="Fuse Bevel", default=0.02)
    pol_fuse_segs: IntProperty(name="Fuse Segs", default=1)
    pol_fuse_square: BoolProperty(name="Square Profile", default=False)

    pol_chamfer_active: BoolProperty(name="Chamfer", default=False)
    pol_chamfer_width: FloatProperty(name="Width", default=0.005, min=0.0, step=0.001)
    pol_chamfer_segs: IntProperty(name="Segs", default=1)
    pol_chamfer_square: BoolProperty(name="Square Profile", default=False)

    pol_taper_active: BoolProperty(name="Taper", default=False)
    pol_taper_x: FloatProperty(name="X")
    pol_taper_y: FloatProperty(name="Y")

    pol_noise_active: BoolProperty(name="Noise", default=False)
    pol_noise_str: FloatProperty(name="Str")
    pol_noise_scl: FloatProperty(name="Scl")

    pol_smooth_active: BoolProperty(name="Smooth", default=False)
    pol_smooth_iter: IntProperty(name="Iter")
    pol_smooth_fac: FloatProperty(name="Fac")

    pol_plate_active: BoolProperty(name="Plating", default=False)
    pol_plate_thick: FloatProperty(name="Gap", default=0.01)
    pol_plate_depth: FloatProperty(name="Depth", default=-0.005)

    pol_decay_active: BoolProperty(name="Decay", default=False)
    pol_decay_str: FloatProperty(name="Strength", default=0.1, min=0.0, max=1.0)
    pol_decay_seed: IntProperty(name="Seed", default=0)

    # --- DATA LAYER ---
    # [ARCHITECT UPDATE] Defaults set to False
    wear_active: BoolProperty(name="Wear (R)", default=False)
    wear_amount: FloatProperty(name="Amt", default=0.5)
    wear_scale: FloatProperty(name="Scl", default=2.0)
    wear_rough: FloatProperty(name="Var", default=0.5)

    data_green_mode: EnumProperty(
        name="Green Mode",
        items=[("THICKNESS", "Thickness", ""), ("FLOW", "Flow", "")],
        default="THICKNESS",
    )

    # [ARCHITECT UPDATE] Defaults set to False
    thick_active: BoolProperty(name="Enable Thickness", default=False)
    thick_amount: FloatProperty(name="Amt", default=1.0)
    thick_dist: FloatProperty(name="Depth", default=0.2)
    thick_contrast: FloatProperty(name="Contr", default=1.0)

    flow_rain: FloatProperty(name="Rain", default=0.5)
    flow_steps: IntProperty(name="Steps", default=1)
    flow_streak: FloatProperty(name="Streak", default=0.9)

    grav_active: BoolProperty(name="Gravity (B)", default=False)
    grav_amount: FloatProperty(name="Amt", default=0.5)
    grav_scale: FloatProperty(name="Streak", default=1.5)
    grav_bias: FloatProperty(name="Bias", default=0.5)

    cavity_active: BoolProperty(name="Cavity (A)", default=False)
    cavity_dist: FloatProperty(name="Dist", default=0.1)
    cavity_samples: IntProperty(name="Samples", default=16)
    cavity_contrast: FloatProperty(name="Contr", default=1.0)

    phys_active: BoolProperty(name="Write Physics IDs", default=True)
    part_active: BoolProperty(name="Write Part IDs", default=True)

    debug_view: EnumProperty(
        name="View",
        items=[
            ("NONE", "Final", ""),
            ("UV", "UV Check", ""),
            ("WEAR", "Wear (R)", ""),
            ("THICK", "Thick (G)", ""),
            ("GRAV", "Gravity (B)", ""),
            ("CAVITY", "Cavity (A)", ""),
            ("PHYS", "Physics", ""),
            ("PARTS", "Part IDs", "Show slot indices"),
            ("PROTECT", "Protection", "Show noise masks"),
            ("SEAM", "Seams", ""),
        ],
        default="NONE",
    )

    show_wireframe: BoolProperty(name="Wireframe", default=False)

    ui_expand_prims: BoolProperty(default=True)
    ui_expand_prim_con: BoolProperty(default=True)
    ui_expand_builds: BoolProperty(default=True)
    ui_expand_arch: BoolProperty(default=True)

    # --- SLOT GENERATOR (0-9) ---
    if not "__annotations__" in locals():
        __annotations__ = {}

    for i in range(10):
        __annotations__[f"expand_{i}"] = BoolProperty(default=(i == 0))
        __annotations__[f"mat_{i}"] = EnumProperty(
            name=f"Mat {i}", items=get_material_items
        )
        __annotations__[f"phys_mat_{i}"] = EnumProperty(
            name=f"Phys {i}", items=get_phys_items
        )
        __annotations__[f"uv_mode_{i}"] = EnumProperty(
            name=f"UV {i}", items=UV_MAP_ITEMS, default="SKIP"
        )
        __annotations__[f"uv_scale_{i}"] = FloatProperty(
            name=f"Scl {i}", default=1.0, min=0.1
        )
        __annotations__[f"sep_{i}"] = BoolProperty(name=f"Detach {i}", default=False)
        __annotations__[f"sock_{i}"] = BoolProperty(name="Socket", default=False)
        __annotations__[f"off_{i}"] = FloatProperty(name="Offset", default=0.0)
        __annotations__[f"prot_{i}"] = BoolProperty(name="Protect", default=False)
