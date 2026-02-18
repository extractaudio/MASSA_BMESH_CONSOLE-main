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

    edge_auto_detect: BoolProperty(
        name="Auto-Detect Boundaries",
        default=True,
        description="If True, auto-assigns edge slots based on material boundaries. If False, relies on Cartridge assignments.",
    )

    edge_angle: FloatProperty(
        name="Sharp Angle", default=30.0, description="Visual Shading Threshold"
    )

    # [ARCHITECT NEW] Auto-Detect Sharp Edge (Convex/Concave)
    edge_sharp_convex_active: BoolProperty(
        name="Sharp (Convex)",
        default=False,
        description="Mark exposed ridges as Sharp",
    )
    edge_sharp_convex_angle: FloatProperty(
        name="Angle (Cvx)",
        default=0.52359, # 30 degrees
        min=0.0,
        max=3.14159,
        subtype="ANGLE",
        description="Angle threshold for Convex edges",
    )

    edge_sharp_concave_active: BoolProperty(
        name="Sharp (Concave)",
        default=False,
        description="Mark enclosed valleys as Sharp",
    )
    edge_sharp_concave_angle: FloatProperty(
        name="Angle (Cnv)",
        default=0.52359, # 30 degrees
        min=0.0,
        max=3.14159,
        subtype="ANGLE",
        description="Angle threshold for Concave edges",
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
        name="Guide (3)", default=True, description="Cut Flow Lines"
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
            ("COLLISION", "Collision", ""),
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
    pol_symmetrize_offset: FloatProperty(name="Offset", default=0.0)

    pol_bend_active: BoolProperty(name="Bend", default=False)
    pol_bend_angle: FloatProperty(
        name="Angle", default=0.0, min=-3.14159, max=3.14159, subtype="ANGLE"
    )
    pol_bend_axis: EnumProperty(
        name="Axis",
        items=[("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")],
        default="X",
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
    pol_chamfer_width: FloatProperty(
        name="Width", default=0.005, min=0.0, max=1.0, soft_max=0.1, step=0.001
    )
    pol_chamfer_segs: IntProperty(name="Segs", default=1, min=1, max=10)
    pol_chamfer_square: BoolProperty(name="Square Profile", default=False)
    pol_chamfer_angle_min: FloatProperty(
        name="Min Angle", default=0.05, min=0.0, max=3.14, subtype="ANGLE"
    )

    pol_taper_active: BoolProperty(name="Taper", default=False)
    pol_taper_x: FloatProperty(name="X", min=-2.0, max=2.0)
    pol_taper_y: FloatProperty(name="Y", min=-2.0, max=2.0)
    pol_taper_curve: FloatProperty(
        name="Curve", default=1.0, min=0.1, max=10.0, soft_max=5.0
    )
    pol_taper_mirror: BoolProperty(name="Mirror", default=False)
    pol_taper_invert: BoolProperty(name="Invert", default=False)

    pol_noise_active: BoolProperty(name="Noise", default=False)
    pol_noise_str: FloatProperty(name="Str", min=0.0, max=10.0, soft_max=2.0)
    pol_noise_scl: FloatProperty(name="Scl")

    pol_smooth_active: BoolProperty(name="Smooth", default=False)
    pol_smooth_iter: IntProperty(name="Iter", min=1, max=100, soft_max=20)
    pol_smooth_fac: FloatProperty(name="Fac", min=0.0, max=1.0)

    pol_plate_active: BoolProperty(name="Plating", default=False)
    pol_plate_thick: FloatProperty(
        name="Gap", default=0.01, min=0.0, max=0.5, soft_max=0.1
    )
    pol_plate_depth: FloatProperty(name="Depth", default=-0.005)

    pol_decay_active: BoolProperty(name="Decay", default=False)
    pol_decay_str: FloatProperty(name="Strength", default=0.1, min=0.0, max=1.0)
    pol_decay_seed: IntProperty(name="Seed", default=0)

    # --- DATA LAYER ---
    # Global Visibility
    show_data_set_1: BoolProperty(name="Show Set 1 (RGBW)", default=True)
    show_data_set_2: BoolProperty(name="Show Set 2 (O/B/P/B)", default=True)

    # --- SET 1 (Legacy) ---
    wear_active: BoolProperty(name="Wear (R)", default=False)
    wear_show: BoolProperty(name="Show", default=True)
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
    thick_show: BoolProperty(name="Show", default=True)
    thick_amount: FloatProperty(name="Amt", default=1.0)
    thick_dist: FloatProperty(name="Depth", default=0.2)
    thick_contrast: FloatProperty(name="Contr", default=1.0)

    flow_rain: FloatProperty(name="Rain", default=0.5)
    flow_steps: IntProperty(name="Steps", default=1)
    flow_streak: FloatProperty(name="Streak", default=0.9)

    grav_active: BoolProperty(name="Gravity (B)", default=False)
    grav_show: BoolProperty(name="Show", default=True)
    grav_amount: FloatProperty(name="Amt", default=0.5)
    grav_scale: FloatProperty(name="Streak", default=1.5)
    grav_bias: FloatProperty(name="Bias", default=0.5)

    cavity_active: BoolProperty(name="Cavity (A)", default=False)
    cavity_show: BoolProperty(name="Show", default=True)
    cavity_dist: FloatProperty(name="Dist", default=0.1)
    cavity_samples: IntProperty(name="Samples", default=16)
    cavity_contrast: FloatProperty(name="Contr", default=1.0)

    # --- SET 2 (New) ---
    wear2_active: BoolProperty(name="Edge Wear (R)", default=False)
    wear2_show: BoolProperty(name="Show", default=True)
    wear2_amount: FloatProperty(name="Amt", default=1.0)
    wear2_contrast: FloatProperty(name="Contr", default=2.0)

    flow2_active: BoolProperty(name="Flow (G)", default=False)
    flow2_show: BoolProperty(name="Show", default=True)
    flow2_rain: FloatProperty(name="Rain", default=0.8)
    flow2_wind_dir: FloatVectorProperty(name="Wind Dir", default=(1.0, 0.0, 0.0), size=3, subtype='DIRECTION')

    cover_active: BoolProperty(name="Covered (B)", default=False)
    cover_show: BoolProperty(name="Show", default=True)
    cover_amount: FloatProperty(name="Amt", default=1.0)
    cover_contrast: FloatProperty(name="Contr", default=1.0)

    peak_active: BoolProperty(name="Peaks (A)", default=False)
    peak_show: BoolProperty(name="Show", default=True)
    peak_dist: FloatProperty(name="Dist", default=0.1)

    peak_contrast: FloatProperty(name="Contr", default=1.0)

    # --- PHYSICS PIPELINE (Brain) ---
    phys_gen_ucx: BoolProperty(
        name="Generate UCX",
        default=False,
        description="Generate UE5 UCX Colliders",
    )
    phys_bake_strain: BoolProperty(
        name="Bake Strain",
        default=False,
        description="Bake Chaos Strain to Vertex Colors",
    )
    phys_kinematic_pin: BoolProperty(
        name="Kinematic Pin",
        default=False,
        description="Generate Kinematic Vertex Weights",
    )
    phys_auto_rig: BoolProperty(
        name="Auto-Rig",
        default=False,
        description="Spawn Constraints for Detached Slots",
    )
    phys_yield_strength: FloatProperty(
        name="Yield Strength",
        default=1.0,
        min=0.0,
        max=10.0,
        description="Strain falloff and constraint breaking limits",
    )

    phys_active: BoolProperty(name="Write Physics IDs", default=True)
    part_active: BoolProperty(name="Write Part IDs", default=True)

    debug_view: EnumProperty(
        name="View",
        items=[
            ("NONE", "Final", ""),
            ("UV", "UV Check", ""),
            ("DATA_SET_1", "Set 1 (RGBW)", "Show Set 1 Channels (Wear, Thick, Grav, Cavity)"),
            ("DATA_SET_2", "Set 2 (Alt)", "Show Set 2 Channels (Edge, Flow, Cover, Peak)"),
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

        # [ARCHITECT NEW] Collision Properties
        __annotations__[f"collision_shape_{i}"] = EnumProperty(
            name=f"Shape {i}",
            items=[
                ("BOX", "Box", "Axis Aligned Box"),
                ("HULL", "Convex Hull", "Convex Hull"),
                ("SPHERE", "Sphere", "Bounding Sphere"),
                ("CAPSULE", "Capsule", "Vertical Capsule"),
                ("MESH", "Mesh", "Original Geometry (Slow)"),
            ],
            default="MESH",
        )
        __annotations__[f"show_coll_{i}"] = BoolProperty(
            name=f"Show Collision {i}", default=False
        )
        __annotations__[f"phys_friction_{i}"] = FloatProperty(
            name=f"Friction {i}", default=0.5, min=0.0, max=1.0
        )
        __annotations__[f"phys_bounce_{i}"] = FloatProperty(
            name=f"Restitution {i}", default=0.0, min=0.0, max=1.0
        )
        __annotations__[f"phys_bond_{i}"] = FloatProperty(
            name=f"Bond Strength {i}", default=1.0, min=0.0
        )
