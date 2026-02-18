import bpy


def get_or_create_sdf_fuse_tree():
    """
    Constructs a Geometry Node tree for SDF Fusing.
    """
    tree_name = "Massa_SDF_Fuse"
    if tree_name in bpy.data.node_groups:
        return bpy.data.node_groups[tree_name]

    nt = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

    nt.interface.new_socket(
        name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
    )
    sock_res = nt.interface.new_socket(
        name="Resolution", in_out="INPUT", socket_type="NodeSocketInt"
    )
    sock_res.default_value = 128
    sock_res.min_value = 32
    sock_res.max_value = 512
    nt.interface.new_socket(
        name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
    )

    node_in = nt.nodes.new("NodeGroupInput")
    node_in.location = (-400, 0)
    node_out = nt.nodes.new("NodeGroupOutput")
    node_out.location = (400, 0)

    try:
        n_sdf = nt.nodes.new("GeometryNodeMeshToVolume")
        n_sdf.location = (-200, 0)
        if "Resolution Mode" in n_sdf.inputs:
            n_sdf.inputs["Resolution Mode"].default_value = "VOXEL_AMOUNT"
    except:
        nt.links.new(node_in.outputs["Geometry"], node_out.inputs["Geometry"])
        return nt

    n_mesh = nt.nodes.new("GeometryNodeVolumeToMesh")
    n_mesh.location = (0, 0)
    if "Adaptivity" in n_mesh.inputs:
        n_mesh.inputs["Adaptivity"].default_value = 0.1
    if "Threshold" in n_mesh.inputs:
        n_mesh.inputs["Threshold"].default_value = 0.1

    n_smooth = nt.nodes.new("GeometryNodeSetShadeSmooth")
    n_smooth.location = (200, 0)

    nt.links.new(node_in.outputs["Geometry"], n_sdf.inputs["Mesh"])
    nt.links.new(node_in.outputs["Resolution"], n_sdf.inputs["Voxel Amount"])
    nt.links.new(n_sdf.outputs["Volume"], n_mesh.inputs["Volume"])
    nt.links.new(n_mesh.outputs["Mesh"], n_smooth.inputs["Geometry"])
    nt.links.new(n_smooth.outputs["Geometry"], node_out.inputs["Geometry"])

    return nt


def get_or_create_viz_overlay_tree():
    """
    [ARCHITECT STABLE] Robust GN tree for Seam Viz.
    Separates geometry by ID (1-5) and assigns hardcoded debug materials.
    Includes ID 5 (Seams).
    """
    tree_name = "Massa_Viz_Overlay"
    if tree_name in bpy.data.node_groups:
        return bpy.data.node_groups[tree_name]

    nt = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")

    # --- INTERFACE ---
    nt.interface.new_socket(
        name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
    )
    # Expose Material Socket
    nt.interface.new_socket(
        name="Material", in_out="INPUT", socket_type="NodeSocketMaterial"
    )
    nt.interface.new_socket(
        name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
    )

    # --- NODES ---
    n_in = nt.nodes.new("NodeGroupInput")
    n_in.location = (-1200, 0)
    n_out = nt.nodes.new("NodeGroupOutput")
    n_out.location = (1200, 0)
    n_join = nt.nodes.new("GeometryNodeJoinGeometry")
    n_join.location = (1000, 0)

    # 1. Pass Original Geometry
    nt.links.new(n_in.outputs["Geometry"], n_join.inputs["Geometry"])

    try:
        # 2. Read Attribute "Massa_Viz_ID" (Int)
        n_read = nt.nodes.new("GeometryNodeInputNamedAttribute")
        n_read.data_type = "INT"
        n_read.inputs["Name"].default_value = "Massa_Viz_ID"
        n_read.location = (-1000, 300)

        # 3. Materials Map (ID -> Blender Material Name)
        mats = {
            1: "Massa_Viz_Edge_1",  # Yellow
            2: "Massa_Viz_Edge_2",  # Blue
            3: "Massa_Viz_Edge_3",  # Red
            4: "Massa_Viz_Edge_4",  # Green
            5: "Massa_Viz_Edge_5",  # Magenta (SEAMS)
        }

        y = 400

        for id_val, mat_name in mats.items():
            # Separate
            n_sep = nt.nodes.new("GeometryNodeSeparateGeometry")
            n_sep.domain = "EDGE"
            n_sep.location = (-600, y)

            n_eq = nt.nodes.new("FunctionNodeCompare")
            n_eq.data_type = "INT"
            n_eq.operation = "EQUAL"
            n_eq.inputs["B"].default_value = id_val
            n_eq.location = (-800, y)

            # Meshing
            n_m2c = nt.nodes.new("GeometryNodeMeshToCurve")
            n_m2c.location = (-400, y)

            n_c2m = nt.nodes.new("GeometryNodeCurveToMesh")
            n_c2m.location = (-200, y)

            n_circle = nt.nodes.new("GeometryNodeCurvePrimitiveCircle")
            # Thicker for Seams (ID 5)
            rad = 0.005 if id_val == 5 else 0.0035
            n_circle.inputs["Radius"].default_value = rad
            n_circle.inputs["Resolution"].default_value = 4
            n_circle.location = (-400, y - 150)

            # Set Material
            n_setmat = nt.nodes.new("GeometryNodeSetMaterial")
            n_setmat.location = (0, y)
            ma = bpy.data.materials.get(mat_name)
            if ma:
                n_setmat.inputs["Material"].default_value = ma
            
            # Linking
            nt.links.new(n_in.outputs["Geometry"], n_sep.inputs["Geometry"])
            nt.links.new(n_read.outputs["Attribute"], n_eq.inputs["A"])
            nt.links.new(n_eq.outputs["Result"], n_sep.inputs["Selection"])

            nt.links.new(n_sep.outputs["Selection"], n_m2c.inputs["Mesh"])
            nt.links.new(n_m2c.outputs["Curve"], n_c2m.inputs["Curve"])
            nt.links.new(n_circle.outputs["Curve"], n_c2m.inputs["Profile Curve"])

            nt.links.new(n_c2m.outputs["Mesh"], n_setmat.inputs["Geometry"])
            nt.links.new(n_setmat.outputs["Geometry"], n_join.inputs["Geometry"])
            
            y -= 300
        
        # [ARCHITECT FIX] Viewport Only Logic
        # Switch: True=Viewport(All), False=Render(Original Only)
        n_is_viewport = nt.nodes.new("GeometryNodeIsViewport")
        n_is_viewport.location = (1000, 200)

        n_switch = nt.nodes.new("GeometryNodeSwitch")
        n_switch.input_type = "GEOMETRY"
        n_switch.location = (1200, 0)
        
        # Switch Logic: Use indices for robustness
        # Input 0: Switch (Boolean), Input 1: False (Geometry), Input 2: True (Geometry)
        nt.links.new(n_is_viewport.outputs[0], n_switch.inputs[0])
        nt.links.new(n_in.outputs[0], n_switch.inputs[1])   # Render: Show Original (False)
        nt.links.new(n_join.outputs[0], n_switch.inputs[2]) # Viewport: Show All (True)

        nt.links.new(n_switch.outputs[0], n_out.inputs[0])

    except Exception as e:
        print(f"MASSA VIZ ERROR: {e}")
        try:
            if not n_out.inputs["Geometry"].is_linked:
                nt.links.new(n_in.outputs["Geometry"], n_out.inputs["Geometry"])
        except:
            pass

    return nt