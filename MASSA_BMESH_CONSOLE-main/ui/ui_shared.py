import bpy


def draw_nav_bar(layout, owner):
    """
    Global Header: Command Deck (Stats + Optics) & Navigation
    Returns: col_main (The empty column to the right of the tabs)
    """
    # --- 1. THE COMMAND DECK (Unified Box) ---
    box = layout.box()

    # A. TELEMETRY (Physical Stats)
    # Only draws if generation has run and stats exist
    stats = bpy.context.scene.get("massa_temp_stats", {})
    has_stats = "global_mass" in stats

    if has_stats:
        vol = float(stats.get("global_vol", 0.0))
        mass = float(stats.get("global_mass", 0.0))

        row = box.row()
        row.alignment = "CENTER"

        # Volume Column
        col_v = row.column(align=True)
        col_v.alignment = "CENTER"
        col_v.label(text="Vol", icon="MESH_CUBE")
        if vol < 0.001:
            col_v.label(text=f"{vol * 1000000:.1f} cm³")
        else:
            col_v.label(text=f"{vol:.4f} m³")

        row.separator(factor=1.5)

        # Mass Column
        col_m = row.column(align=True)
        col_m.alignment = "CENTER"
        col_m.label(text="Mass", icon="PHYSICS")
        col_m.label(text=f"{mass:.2f} kg")

        # Separator between Stats and Controls
        box.separator()

    # B. OPTICS (Wireframe, Debug, Edge Viz)
    row = box.row(align=True)

    # Wireframe Toggle (Left)
    if owner.show_wireframe:
        row.prop(owner, "show_wireframe", text="Wire", icon="SHADING_WIRE", toggle=True)
    else:
        row.prop(owner, "show_wireframe", text="", icon="SHADING_WIRE", toggle=True)

    row.separator()

    # View Mode (Center - Expanded)
    row.prop(owner, "debug_view", text="")

    # Edge Viz (Right - Icon Only unless active)
    row.separator()
    if owner.viz_edge_mode == "OFF":
        row.prop(owner, "viz_edge_mode", text="", icon="OVERLAY")
    else:
        row.prop(owner, "viz_edge_mode", text="")

    # --- 2. NAVIGATION TABS ---
    split = layout.split(factor=0.18)
    col_nav = split.column(align=False)

    # [ARCHITECT FIX] This is the column we return, so Shape UI draws HERE, not in the top box.
    col_main = split.column()

    def _nav_btn(icon, enum_val):
        b = col_nav.box()
        b.scale_y, b.scale_x = 1.5, 0.9
        r = b.row()
        r.alignment = "CENTER"
        r.prop_enum(owner, "ui_tab", enum_val, icon=icon, text="")
        col_nav.separator(factor=0.5)

    _nav_btn("MOD_BUILD", "SHAPE")
    _nav_btn("BRUSH_DATA", "DATA")
    _nav_btn("MOD_SMOOTH", "POLISH")
    _nav_btn("GROUP_UVS", "UVS")
    _nav_btn("MATERIAL", "SLOTS")
    _nav_btn("EDGESEL", "EDGES")
    _nav_btn("PHYSICS", "COLLISION")

    # [ARCHITECT FIX] Return the main column (Right side of split)
    return col_main


def draw_edge_slots_tab(layout, owner):
    layout.label(text="Edge Role Interpreter", icon="EDGESEL")

    # [ARCHITECT NEW] Source Control
    row = layout.row()
    row.prop(owner, "edge_auto_detect", toggle=True, icon="AUTO")

    # [ARCHITECT NEW] Auto-Detect Sharp (Convex/Concave)
    # Additive Pass - Runs after Auto-Detect
    row = layout.row(align=True)
    row.prop(owner, "edge_sharp_convex_active", toggle=True, icon="MOD_EDGESPLIT")
    if owner.edge_sharp_convex_active:
        row.prop(owner, "edge_sharp_convex_angle", text="")

    row = layout.row(align=True)
    row.prop(owner, "edge_sharp_concave_active", toggle=True, icon="MOD_BEVEL")
    if owner.edge_sharp_concave_active:
        row.prop(owner, "edge_sharp_concave_angle", text="")

    box = layout.box()
    box.label(text="Role Mappings", icon="PREFERENCES")

    row = box.row()
    row.label(text="1: Perimeter", icon="MESH_CIRCLE")
    row.prop(owner, "edge_slot_1_action", text="")

    row = box.row()
    row.label(text="2: Contour", icon="MESH_CUBE")
    row.prop(owner, "edge_slot_2_action", text="")

    row = box.row()
    row.label(text="3: Guide", icon="DRIVER")
    row.prop(owner, "edge_slot_3_action", text="")

    row = box.row()
    row.label(text="4: Detail", icon="EDITMODE_HLT")
    row.prop(owner, "edge_slot_4_action", text="")

    row = box.row()
    row.label(text="5: Fold", icon="MOD_CLOTH")
    row.prop(owner, "edge_slot_5_action", text="")

    # Legend
    if owner.viz_edge_mode == "SLOTS":
        layout.separator()
        sub = layout.box()
        sub.scale_y = 0.8
        sub.label(text="Slot Colors (Shader):", icon="INFO")
        r = sub.row(align=True)
        # [ARCHITECT UPDATE] New Color Legend
        r.label(text="1:Yel", icon="SHADING_TEXTURE")  # Yellow (Approx Icon)
        r.label(text="2:Blu", icon="COLOR_BLUE")  # Blue
        r.label(text="3:Red", icon="COLOR_RED")  # Red
        r.label(text="4:Grn", icon="COLOR_GREEN")  # Green
        r.label(text="5:Pur", icon="COLLECTION_COLOR_06")  # Purple


def draw_polish_tab(layout, owner):
    layout.label(text="Structure", icon="MOD_WIREFRAME")
    b = layout.box()
    b.label(text="Topology Merge", icon="AUTOMERGE_ON")
    b.prop(owner, "pol_merge_mode", text="")
    if owner.pol_merge_mode == "BOOLEAN":
        b.label(text="Creates Intersection Seams", icon="INFO")

    layout.separator()
    b = layout.box()
    r = b.row()
    r.prop(owner, "pol_triangulate_active", text="Triangulate", icon="MOD_TRIANGULATE")
    r.prop(owner, "pol_holes_active", text="Fill Holes", icon="MESH_CIRCLE")
    if owner.pol_triangulate_active or owner.pol_holes_active:
        row = b.row(align=True)
        if owner.pol_triangulate_active:
            row.prop(owner, "pol_triangulate_method", text="")
        if owner.pol_holes_active:
            row.prop(owner, "pol_holes_sides", text="Sides")

    layout.separator()
    layout.label(text="Refinement", icon="SCULPTMODE_HLT")
    b = layout.box()
    b.prop(
        owner,
        "pol_fuse_active",
        text="SDF Fuse (Remesh)",
        icon="MOD_REMESH",
        toggle=True,
    )
    if owner.pol_fuse_active:
        r = b.row(align=True)
        r.prop(owner, "pol_fuse_radius", text="Bevel")
        r.prop(owner, "pol_fuse_segs", text="Segs")
        b.prop(owner, "pol_fuse_square", text="90° Square")

    b = layout.box()
    b.prop(owner, "pol_chamfer_active", text="Chamfer", toggle=True, icon="MOD_BEVEL")
    if owner.pol_chamfer_active:
        r = b.row(align=True)
        r.prop(owner, "pol_chamfer_width", text="W")
        r.prop(owner, "pol_chamfer_segs", text="S")
        r2 = b.row(align=True)
        r2.prop(owner, "pol_chamfer_square", text="Square")
        if hasattr(owner, "pol_chamfer_angle_min"):
            r2.prop(owner, "pol_chamfer_angle_min", text="Limit")

    if hasattr(owner, "pol_plate_active"):
        b = layout.box()
        b.prop(
            owner,
            "pol_plate_active",
            text="Plating (Inset)",
            toggle=True,
            icon="FACESEL",
        )
        if owner.pol_plate_active:
            r = b.row(align=True)
            r.prop(owner, "pol_plate_thick", text="Gap")
            r.prop(owner, "pol_plate_depth", text="Depth")

    b = layout.box()
    b.prop(
        owner, "pol_noise_active", text="Surface Noise", toggle=True, icon="RNDCURVE"
    )
    if owner.pol_noise_active:
        r = b.row(align=True)
        r.prop(owner, "pol_noise_str", text="Str")
        r.prop(owner, "pol_noise_scl", text="Scl")

    b = layout.box()
    b.prop(owner, "pol_smooth_active", text="Smooth", toggle=True, icon="MOD_SMOOTH")
    if owner.pol_smooth_active:
        r = b.row(align=True)
        r.prop(owner, "pol_smooth_iter", text="Iter")
        r.prop(owner, "pol_smooth_fac", text="Fac")

    if hasattr(owner, "pol_decay_active"):
        b = layout.box()
        b.prop(
            owner, "pol_decay_active", text="Decay (Delete)", toggle=True, icon="TRASH"
        )
        if owner.pol_decay_active:
            r = b.row(align=True)
            r.prop(owner, "pol_decay_str", text="Chance")
            r.prop(owner, "pol_decay_seed", text="Seed")

    layout.separator()
    b = layout.box()
    r = b.row()
    r.prop(
        owner, "pol_symmetrize_active", text="Mirror", toggle=True, icon="MOD_MIRROR"
    )
    r.prop(owner, "pol_taper_active", text="Taper", toggle=True, icon="MOD_LATTICE")
    if hasattr(owner, "pol_bend_active"):
        r.prop(owner, "pol_bend_active", text="Bend", toggle=True, icon="MOD_SIMPLEDEFORM")

    if owner.pol_symmetrize_active:
        b.prop(owner, "pol_symmetrize_dir", text="Direction", expand=True)
        if hasattr(owner, "pol_symmetrize_offset"):
            b.prop(owner, "pol_symmetrize_offset", text="Mirror Offset")

    if owner.pol_taper_active:
        col = b.column(align=True)
        row = col.row(align=True)
        row.prop(owner, "pol_taper_x", text="X")
        row.prop(owner, "pol_taper_y", text="Y")

        if hasattr(owner, "pol_taper_curve"):
            row = col.row(align=True)
            row.prop(owner, "pol_taper_curve", text="Curve")

            row = col.row(align=True)
            row.prop(owner, "pol_taper_mirror", text="Sym", toggle=True)
            row.prop(owner, "pol_taper_invert", text="Inv", toggle=True)

    if hasattr(owner, "pol_bend_active") and owner.pol_bend_active:
        col = b.column(align=True)
        row = col.row(align=True)
        row.prop(owner, "pol_bend_angle", text="Angle")
        row.prop(owner, "pol_bend_axis", text="Axis", expand=True)


def draw_data_tab(layout, owner, slot_names):
    # --- 0. VISIBILITY CONTROL ---
    layout.label(text="Data Layer Visibility", icon="RESTRICT_VIEW_OFF")
    box = layout.box()

    # Global Set Toggles
    row = box.row(align=True)
    row.prop(owner, "show_data_set_1", text="Set 1 (RGBW)", toggle=True)
    row.prop(owner, "show_data_set_2", text="Set 2 (Alt)", toggle=True)

    box.separator()

    # Individual Toggles (Grid)
    # Row 1: Set 1
    if owner.show_data_set_1:
        col = box.column(align=True)
        col.label(text="Set 1 Channels:", icon="BRUSH_DATA")
        row = col.row(align=True)
        row.prop(owner, "wear_show", text="Wear", icon="COLOR_RED", toggle=True)
        row.prop(owner, "thick_show", text="Thick", icon="COLOR_GREEN", toggle=True)
        row.prop(owner, "grav_show", text="Grav", icon="COLOR_BLUE", toggle=True)
        row.prop(owner, "cavity_show", text="Cavity", icon="IMAGE_ALPHA", toggle=True)
        box.separator()

    # Row 2: Set 2
    if owner.show_data_set_2:
        col = box.column(align=True)
        col.label(text="Set 2 Channels:", icon="BRUSH_DATA")
        row = col.row(align=True)
        row.prop(owner, "wear2_show", text="Edge", icon="COLOR_RED", toggle=True)
        row.prop(owner, "flow2_show", text="Flow", icon="COLOR_GREEN", toggle=True)
        row.prop(owner, "cover_show", text="Cover", icon="COLOR_BLUE", toggle=True)
        row.prop(owner, "peak_show", text="Peak", icon="IMAGE_ALPHA", toggle=True)

    layout.separator()

    # --- 1. SET 1 CONTROLS ---
    layout.label(text="Set 1: Surface Data", icon="BRUSH_DATA")

    # Wear (R)
    box = layout.box()
    row = box.row()
    row.prop(owner, "wear_active", icon="COLOR_RED", toggle=True)
    if owner.wear_active:
        col = box.column(align=True)
        col.prop(owner, "wear_amount", text="Amount")
        col.prop(owner, "wear_scale", text="Scale")
        col.prop(owner, "wear_rough", text="Roughness")

    # Thick/Flow (G)
    box = layout.box()
    row = box.row()
    row.prop(owner, "thick_active", icon="COLOR_GREEN", toggle=True)
    if owner.thick_active:
        box.prop(owner, "data_green_mode", expand=True)
        col = box.column(align=True)
        if owner.data_green_mode == "THICKNESS":
            col.prop(owner, "thick_amount")
            col.prop(owner, "thick_dist")
            col.prop(owner, "thick_contrast")
        else:
            col.prop(owner, "flow_rain")
            col.prop(owner, "flow_steps")
            col.prop(owner, "flow_streak")

    # Gravity (B)
    box = layout.box()
    row = box.row()
    row.prop(owner, "grav_active", icon="COLOR_BLUE", toggle=True)
    if owner.grav_active:
        col = box.column(align=True)
        col.prop(owner, "grav_amount")
        col.prop(owner, "grav_bias")

    # Cavity (A)
    box = layout.box()
    row = box.row()
    row.prop(owner, "cavity_active", icon="IMAGE_ALPHA", toggle=True)
    if owner.cavity_active:
        col = box.column(align=True)
        col.prop(owner, "cavity_dist")
        col.prop(owner, "cavity_samples")
        col.prop(owner, "cavity_contrast")

    layout.separator()

    # --- 2. SET 2 CONTROLS ---
    layout.label(text="Set 2: Advanced Data", icon="BRUSH_DATA")

    # Edge Wear (R)
    box = layout.box()
    row = box.row()
    row.prop(owner, "wear2_active", icon="COLOR_RED", toggle=True)
    if owner.wear2_active:
        col = box.column(align=True)
        col.prop(owner, "wear2_amount")
        col.prop(owner, "wear2_contrast")

    # Flow (G)
    box = layout.box()
    row = box.row()
    row.prop(owner, "flow2_active", icon="COLOR_GREEN", toggle=True)
    if owner.flow2_active:
        col = box.column(align=True)
        col.prop(owner, "flow2_rain")
        col.prop(owner, "flow2_wind_dir")

    # Cover (B)
    box = layout.box()
    row = box.row()
    row.prop(owner, "cover_active", icon="COLOR_BLUE", toggle=True)
    if owner.cover_active:
        col = box.column(align=True)
        col.prop(owner, "cover_amount")
        col.prop(owner, "cover_contrast")

    # Peak (A)
    box = layout.box()
    row = box.row()
    row.prop(owner, "peak_active", icon="IMAGE_ALPHA", toggle=True)
    if owner.peak_active:
        col = box.column(align=True)
        col.prop(owner, "peak_dist")
        col.prop(owner, "peak_contrast")

    layout.separator()
    layout.label(text="Identity", icon="TAG")
    row = layout.row(align=True)
    row.prop(owner, "phys_active", toggle=True)
    row.prop(owner, "part_active", toggle=True)


def draw_uvs_tab(layout, owner, slot_names, stats):
    """
    Revised UV Tab Layout: Compact, Contextual, Organized.
    """
    # --- 1. SOLVERS (The Algorithm) - MOVED TO TOP ---
    box = layout.box()
    # Header row with Icon and Dropdown
    row = box.row(align=True)
    row.label(text="Auto-Solver", icon="MOD_UVPROJECT")
    row.prop(owner, "seam_solver_mode", text="")

    # Contextual Parameters
    if owner.seam_solver_mode != "NONE":
        col = box.column(align=True)
        col.separator(factor=0.5)

        if owner.seam_solver_mode in {"HARD_SURFACE", "AUTO"}:
            col.prop(owner, "seam_cluster_tol")
        elif owner.seam_solver_mode in {"ORGANIC", "SMART_TUBE", "BOX_STRIP"}:
            col.prop(owner, "seam_orient")
            if owner.seam_solver_mode == "ORGANIC":
                col.prop(owner, "seam_straightness")

    layout.separator()

    # --- 1.5 GLOBAL OVERRIDES (Auto) ---
    box = layout.box()
    row = box.row(align=True)
    row.label(text="Global Overrides", icon="PREFERENCES")
    row.prop(owner, "auto_unwrap", text="Auto Smart UV", toggle=True)
    if owner.auto_unwrap:
        box.prop(owner, "auto_unwrap_margin", text="Margin")

    layout.separator()

    layout.label(text="Seam Intelligence", icon="GROUP_UVS")

    # --- 2. DRIVERS (The Main Control Deck) ---
    box = layout.box()

    # Header: Main Switch
    row = box.row(align=True)
    row.label(text="Drivers", icon="DRIVER")
    row.prop(owner, "seam_active", text="Active", toggle=True)

    if owner.seam_active:
        col = box.column(align=True)
        col.separator(factor=0.5)

        # Source Selection (Horizontal Bar)
        row = col.row(align=True)
        row.prop(owner, "seam_from_slots", text="Slots", toggle=True)
        row.prop(owner, "seam_from_angle", text="Angle", toggle=True)
        row.prop(owner, "seam_from_edges", text="Edges", toggle=True)

        # Contextual Sub-Panels (Only show if source is on)
        if owner.seam_from_angle or owner.seam_from_edges:
            col.separator(factor=0.5)

            # Angle Settings
            if owner.seam_from_angle:
                sub = col.box()
                r = sub.row(align=True)
                r.prop(owner, "seam_angle_limit", text="Angle")
                r.prop(owner, "seam_bias", text="")  # Enum is descriptive enough

            # Edge Role Settings (The 4-Way Grid)
            if owner.seam_from_edges:
                sub = col.box()
                r = sub.row(align=True)
                r.alignment = "CENTER"
                r.label(text="Edge Role Mask (1-4)", icon="EDGESEL")

                # Use grid flow for the 4 checkboxes
                grid = sub.grid_flow(
                    row_major=True, columns=2, even_columns=True, align=True
                )
                grid.prop(owner, "seam_use_peri", text="Perimeter")
                grid.prop(owner, "seam_use_cont", text="Contour")
                grid.prop(owner, "seam_use_guide", text="Guide")
                grid.prop(owner, "seam_use_detail", text="Detail")
                grid.prop(owner, "seam_use_fold", text="Fold")

    layout.separator()

    # --- 3. ENFORCER (The Cleanup) ---
    box = layout.box()
    # Integrated Header Toggle
    row = box.row(align=True)
    row.label(text="Enforcer", icon="MOD_MASK")
    row.prop(owner, "seam_cleanup_flat", text="Remove Flat Seams", toggle=True)

    if owner.seam_cleanup_flat:
        box.prop(owner, "seam_cleanup_thresh", text="Threshold")

    layout.separator()

    # --- 4. SLOT PROJECTION (The Per-Material Override) ---
    layout.label(text="Slot Projection", icon="UV")

    for i in range(10):
        if not getattr(owner, f"expand_{i}", False):
            continue

        box = layout.box()
        s_name = slot_names.get(i, f"Slot {i}")

        # Header Row
        row = box.row(align=True)
        row.label(text=f"{i}: {s_name}", icon="MATERIAL")

        # Efficiency Stats (Optional Visual Feedack)
        if stats and str(i) in stats:
            try:
                eff_f = float(stats[str(i)])
                # Green check if good ratio, Warning if distorted
                icon_e = "CHECKMARK" if eff_f < 1.1 else "ERROR"
                row.label(text=f"{eff_f:.2f}", icon=icon_e)
            except:
                pass

        # Internal Controls
        col = box.column(align=True)
        col.prop(owner, f"uv_mode_{i}", text="Mode")

        # Only show scale if not Skip/Unwrap/Fit (Fit has no scale)
        if getattr(owner, f"uv_mode_{i}") not in {"SKIP", "UNWRAP", "FIT"}:
            col.prop(owner, f"uv_scale_{i}", text="Scale")

        col.prop(owner, f"off_{i}", text="Inflate", icon="MOD_THICKNESS")


def draw_slots_tab(layout, owner, slot_names, stats):
    """
    [ARCHITECT RESTORED] The missing Slots Tab logic.
    """
    layout.label(text="Material Slots", icon="MATERIAL")
    for i in range(10):
        box = layout.box()
        row = box.row()
        is_expanded = getattr(owner, f"expand_{i}", False)
        icon = "TRIA_DOWN" if is_expanded else "TRIA_RIGHT"
        row.prop(owner, f"expand_{i}", icon=icon, text="", emboss=False)
        row.label(text=f"{i}: {slot_names.get(i, f'Slot {i}')}")

        sub = row.row(align=True)
        sub.prop(owner, f"sep_{i}", text="", icon="UNLINKED", toggle=True)
        sub.prop(owner, f"sock_{i}", text="", icon="EMPTY_AXIS", toggle=True)
        sub.prop(owner, f"prot_{i}", text="", icon="LOCKED", toggle=True)

        if is_expanded:
            col = box.column(align=True)
            col.prop(owner, f"mat_{i}", text="Visual")
            col.prop(owner, f"phys_mat_{i}", text="Physics")


def draw_collision_tab(layout, owner, slot_names):
    """
    [ARCHITECT NEW] Collision & Physics Tab
    """
    layout.label(text="Collision & Physics", icon="PHYSICS")

    # --- P1: GLOBAL PHYSICS SETTINGS ---
    # Box 1: Data Maps (Chaos & Cloth)
    box = layout.box()
    box.label(text="Data Maps (Chaos & Cloth)", icon="BRUSH_DATA")
    row = box.row(align=True)
    row.prop(owner, "phys_bake_strain", text="Strain (VCol)")
    row.prop(owner, "phys_kinematic_pin", text="Pin (Weight)")
    box.prop(owner, "phys_yield_strength")

    # Box 2: Engine Proxies (Collision)
    box = layout.box()
    box.label(text="Engine Proxies (Collision)", icon="MOD_PHYSICS")
    box.prop(owner, "phys_gen_ucx", text="Generate UCX", toggle=True, icon="MESH_CUBE")

    # Box 3: Mechanics (Rigid Body Links)
    box = layout.box()
    box.label(text="Mechanics (Rigid Body Links)", icon="CONSTRAINT")
    box.prop(owner, "phys_auto_rig", text="Auto-Rig Constraints", toggle=True, icon="CONSTRAINT_BONE")

    layout.separator()
    layout.label(text="Per-Slot Collision", icon="MATERIAL")

    for i in range(10):
        box = layout.box()
        row = box.row()

        is_expanded = getattr(owner, f"expand_{i}", False)
        icon = "TRIA_DOWN" if is_expanded else "TRIA_RIGHT"
        row.prop(owner, f"expand_{i}", icon=icon, text="", emboss=False)

        s_name = slot_names.get(i, f"Slot {i}")
        row.label(text=f"{i}: {s_name}", icon="MATERIAL")

        # Wireframe Toggle on Header
        sub = row.row(align=True)
        if getattr(owner, f"show_coll_{i}", False):
            sub.prop(
                owner, f"show_coll_{i}", text="", icon="SHADING_WIRE", toggle=True
            )
        else:
            sub.prop(owner, f"show_coll_{i}", text="", icon="X", toggle=True)

        if is_expanded:
            col = box.column(align=True)

            # Shape
            col.prop(owner, f"collision_shape_{i}", text="Shape")
            col.separator()

            # Physics Props
            col.prop(owner, f"phys_friction_{i}", text="Friction")
            col.prop(owner, f"phys_bounce_{i}", text="Restitution")
            col.prop(owner, f"phys_bond_{i}", text="Attachment Strength")
