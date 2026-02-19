import bpy
import bmesh
from mathutils import Euler, Vector, Matrix
from . import massa_polish, massa_surface, massa_sockets, seam_solvers, massa_nodes
from ..utils import mat_utils
import traceback


def _verify_layer(bm, attr_name, internal_name):
    try:
        if hasattr(bm.edges.layers, attr_name):
            return getattr(bm.edges.layers, attr_name).verify()
    except AttributeError:
        pass
    layer = bm.edges.layers.float.get(internal_name)
    if not layer:
        layer = bm.edges.layers.float.new(internal_name)
    return layer


def process_edge_slots(bm, op):
    try:
        edge_slots = bm.edges.layers.int["MASSA_EDGE_SLOTS"]
    except KeyError:
        return

    force_seam_layer = bm.edges.layers.int.get("massa_force_seam")
    if not force_seam_layer:
        force_seam_layer = bm.edges.layers.int.new("massa_force_seam")

    manifest = {
        1: getattr(op, "edge_slot_1_action", "IGNORE"),
        2: getattr(op, "edge_slot_2_action", "IGNORE"),
        3: getattr(op, "edge_slot_3_action", "IGNORE"),
        4: getattr(op, "edge_slot_4_action", "IGNORE"),
        5: getattr(op, "edge_slot_5_action", "IGNORE"),
    }

    crease_layer = None
    if any(a == "CREASE" for a in manifest.values()):
        crease_layer = _verify_layer(bm, "crease", "crease_edge")
    bevel_layer = None
    if any(a == "BEVEL" for a in manifest.values()):
        bevel_layer = _verify_layer(bm, "bevel_weight", "bevel_weight_edge")

    for edge in bm.edges:
        slot_id = edge[edge_slots]
        if slot_id not in manifest:
            continue
        action = manifest[slot_id]
        if action == "IGNORE":
            continue

        if action in {"SEAM", "BOTH"}:
            edge.seam = True
            edge[force_seam_layer] = 1
        if action in {"SHARP", "BOTH"}:
            edge.smooth = False
        if action == "CREASE" and crease_layer:
            edge[crease_layer] = 1.0
        if action == "BEVEL" and bevel_layer:
            edge[bevel_layer] = 1.0


def run_pipeline(op, context):
    # print("MASSA DEBUG: run_pipeline STARTED")
    # [ARCHITECT FIX] Ensure DB is ready
    mat_utils.ensure_default_library()
    
    meta = op._get_cartridge_meta()
    flags = meta.get("flags", {})
    bm = bmesh.new()

    # [ARCHITECT NEW] Phase 3: Socket Layer
    # This allows Cartridges to tag faces for socket generation using pure math.
    bm.faces.layers.int.get("MASSA_SOCKETS") or bm.faces.layers.int.new("MASSA_SOCKETS")

    try:
        op.build_shape(bm)

        # [ARCHITECT FIX] Ensure layer exists before detection
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
            
        if getattr(op, "edge_auto_detect", True):
            massa_surface.auto_detect_edge_slots(bm)

        process_edge_slots(bm, op)

        # [ARCHITECT NEW] Additive Sharp Detection (Runs after slots)
        massa_surface.auto_detect_sharp_edges(bm, op)

        if abs(op.global_scale - 1.0) > 0.001:
            bmesh.ops.scale(bm, vec=(op.global_scale,) * 3, verts=bm.verts)
        if not flags.get("LOCK_PIVOT", False):
            massa_polish.apply_transform_alignment(bm, op.pivot_mode)

        manifest, active_sockets = massa_surface.gather_manifest(op)
        massa_polish.apply_protection_mask(bm, manifest)
        massa_polish.apply_slot_inflation(bm, op)
        massa_polish.apply_hard_merge(bm, mode=op.pol_merge_mode)

        if not op.draft_mode:
            _run_polish_stack(bm, op, flags, manifest)

        massa_polish.apply_safety_decimate(bm)
        if flags.get("FIX_DEGENERATE", True):
            bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if flags.get("REMOVE_LOOSE", True):
            try:
                loose_verts = [v for v in bm.verts if not v.link_edges]
                if loose_verts:
                    bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")
            except:
                pass

        stats = massa_surface.write_identity_layers(bm, manifest, op)

        vol, mass = massa_surface.calculate_physical_stats(bm, manifest)
        stats["global_vol"] = vol
        stats["global_mass"] = mass

        context.scene["massa_temp_stats"] = {str(k): v for k, v in stats.items()}
        socket_data = massa_sockets.calculate_transforms(bm, active_sockets)

        viz_mode = getattr(op, "viz_edge_mode", "NATIVE")
        if not op.draft_mode or viz_mode == "SLOTS":
            # Tag ID 5 for Seams here
            cvx, cnv = massa_surface.tag_structure_edges(bm, op)
            
            if getattr(op, "seam_active", False):
                e_mask = (
                    getattr(op, "seam_use_peri", True),
                    getattr(op, "seam_use_cont", True),
                    getattr(op, "seam_use_guide", False),
                    getattr(op, "seam_use_detail", False),
                    getattr(op, "seam_use_fold", False),
                )
                seam_solvers.apply_base_drivers(
                    bm,
                    use_angle=op.seam_from_angle,
                    angle_limit=op.seam_angle_limit,
                    use_slots=op.seam_from_slots,
                    bias=op.seam_bias,
                    use_edges=getattr(op, "seam_from_edges", False),
                    edge_mask=e_mask,
                )
                if op.seam_solver_mode != "NONE":
                    seam_solvers.solve_seams(
                        bm,
                        mode=op.seam_solver_mode,
                        orient=getattr(op, "seam_orient", "BACK"),
                        cluster_tol=getattr(op, "seam_cluster_tol", 15.0),
                        straightness=getattr(op, "seam_straightness", 2.0),
                        strict_slots=op.seam_from_slots,
                    )
                if op.seam_cleanup_flat:
                    if op.seam_solver_mode not in {
                        "SMART_TUBE",
                        "ORGANIC",
                        "BOX_STRIP",
                    }:
                        seam_solvers.cleanup_flat_seams(
                            bm,
                            threshold=op.seam_cleanup_thresh,
                            keep_slots=op.seam_from_slots,
                        )
            
            massa_surface.generate_surface_maps(bm, op, cvx, cnv)

        if op.ui_use_rot:
            bmesh.ops.transform(
                bm,
                matrix=Euler(op.rotation, "XYZ").to_matrix().to_4x4(),
                verts=bm.verts,
            )
        _generate_output(op, context, bm, socket_data, manifest)

    except Exception as e:
        op.report({"ERROR"}, f"Pipeline Error: {e}")
        traceback.print_exc()
        if bm:
            bm.free()
        return {"CANCELLED"}
    return {"FINISHED"}


def _capture_operator_params(op):
    """
    Serializes all custom properties of the operator into a dictionary.
    Excludes standard Blender properties and internal methods.
    """
    params = {}

    # Iterate over all RNA properties defined in the operator
    for prop in op.bl_rna.properties:
        if prop.is_readonly:
            continue
        if prop.identifier in {"bl_idname", "bl_label", "bl_description", "bl_options", "rna_type"}:
            continue

        try:
            val = getattr(op, prop.identifier)
            # Convert mathutils types to lists/tuples for JSON compatibility
            if hasattr(val, "to_tuple"):
                val = val.to_tuple()
            elif hasattr(val, "to_list"):
                val = val.to_list()

            params[prop.identifier] = val
        except:
            pass

    return params


def _run_polish_stack(bm, op, flags, manifest):
    if op.pol_fuse_active and flags.get("ALLOW_FUSE", True):
        massa_polish.apply_concave_bevel(
            bm,
            op.pol_fuse_radius * op.global_scale,
            op.pol_fuse_segs,
            op.pol_fuse_square,
        )
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if op.pol_solidify_active and flags.get("ALLOW_SOLIDIFY", True):
        massa_polish.apply_solidify(bm, op.pol_solidify_thick * op.global_scale)
    if op.pol_bridge_active:
        massa_polish.apply_bridge_loops(bm)
    if op.pol_holes_active:
        massa_polish.apply_fill_holes(bm, op.pol_holes_sides)
    if op.pol_symmetrize_active:
        massa_polish.apply_symmetrize(
            bm, op.pol_symmetrize_dir, op.pol_symmetrize_offset
        )
    if op.pol_taper_active:
        massa_polish.apply_taper(
            bm,
            op.pol_taper_x,
            op.pol_taper_y,
            op.pol_taper_curve,
            op.pol_taper_mirror,
            op.pol_taper_invert,
        )
    if hasattr(op, "pol_bend_active") and op.pol_bend_active:
        massa_polish.apply_bend(bm, op.pol_bend_angle, op.pol_bend_axis)
    if hasattr(op, "pol_plate_active") and op.pol_plate_active:
        massa_polish.apply_plating(
            bm,
            manifest,
            op.pol_plate_thick * op.global_scale,
            op.pol_plate_depth * op.global_scale,
        )
    if op.pol_noise_active:
        massa_polish.apply_noise(
            bm, op.pol_noise_str * op.global_scale, op.pol_noise_scl, 0, op.global_scale
        )
    if op.pol_smooth_active:
        massa_polish.apply_smooth(bm, op.pol_smooth_iter, op.pol_smooth_fac)
    if hasattr(op, "pol_decay_active") and op.pol_decay_active:
        massa_polish.apply_decay(bm, manifest, op.pol_decay_str, op.pol_decay_seed)
    if op.pol_triangulate_active:
        massa_polish.apply_triangulate(bm, op.pol_triangulate_method)
    if op.pol_chamfer_active and flags.get("ALLOW_CHAMFER", True):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        massa_polish.apply_chamfer(
            bm,
            op.pol_chamfer_width * op.global_scale,
            op.pol_chamfer_segs,
            op.pol_chamfer_square,
            getattr(op, "pol_chamfer_angle_min", 0.05),
        )


def _generate_output(op, context, bm, socket_data, manifest):
    has_bevel = False
    if bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.get(
        "bevel_weight"
    ):
        has_bevel = True

    viz_mode = getattr(op, "viz_edge_mode", "NATIVE")
    debug_mode = getattr(op, "debug_view", "NONE")

    STRICT_DEBUG_MODES = {
        "UV",
        "WEAR",
        "THICK",
        "GRAV",
        "CAVITY",
        "PHYS",
        "PARTS",
        "PROTECT",
        "SEAM",
    }
    is_debug_override = debug_mode in STRICT_DEBUG_MODES

    # [ARCHITECT FIX] Removed destructive data clearing for SLOTS mode.
    # The user wants edge attributes (seams/sharps) to persist on export even when visualizing slots.
    # if viz_mode == "SLOTS":
    #    try:
    #        edge_slots = bm.edges.layers.int["MASSA_EDGE_SLOTS"]
    #        crease_layer = _verify_layer(bm, "crease", "crease_edge")
    #        bevel_layer = _verify_layer(bm, "bevel_weight", "bevel_weight_edge")
    #        for e in bm.edges:
    #            e.seam = False
    #            e.smooth = True
    #            e[crease_layer] = 0.0
    #            e[bevel_layer] = 0.0
    #    except KeyError:
    #        pass

    mesh = bpy.data.meshes.new("Massa_Obj")
    obj = bpy.data.objects.new(op.bl_label, mesh)

    # [ARCHITECT FIX] MATERIAL ASSIGNMENT (Moved up to support Slot Selection)
    # Must be done BEFORE bm.to_mesh() to preserve face material indices (0-9).
    # If slots are missing on the target mesh, to_mesh() clamps indices to 0.
    # [ARCHITECT FIX] Now returns a slot map for remapped indices
    slot_map = massa_surface.assign_materials(obj, op, bm=bm)

    # [ARCHITECT NEW] Phase 3 Protocol: Data Layers (Chaos / Soft Body)
    massa_surface.bake_strain_map(bm, op)
    massa_surface.bake_kinematic_anchors(obj, bm, op)

    # [ARCHITECT NEW] Phase 4: Socket Collection (BMesh Based)
    collected_sockets = []
    if getattr(op, "sock_enable", False):
        try:
            sock_layer = bm.faces.layers.int.get("MASSA_SOCKETS")
            if sock_layer:
                socket_faces = {}
                for f in bm.faces:
                    sid = f[sock_layer]
                    if sid > 0:
                        socket_faces.setdefault(sid, []).append(f)

                for sid, faces in socket_faces.items():
                    center = Vector((0,0,0))
                    normal = Vector((0,0,0))
                    for f in faces:
                        center += f.calc_center_median()
                        normal += f.normal
                    if len(faces) > 0:
                        center /= len(faces)
                        normal = normal.normalized()
                    collected_sockets.append((sid, center, normal))
        except Exception as e:
            print(f"Socket Collection Error: {e}")

    bm.to_mesh(mesh)
    bm.free()

    if mesh.uv_layers:
        mesh.uv_layers[0].name = "UVMap"

    context.collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    context.view_layer.objects.active = obj
    obj.select_set(True)

    # [ARCHITECT FIX] Robust ID Storage
    op_id = op.bl_idname
    try:
        meta_id = op._get_cartridge_meta().get("id", "")
        if meta_id:
            op_id = f"massa.gen_{meta_id}"
    except:
        pass

    # Fallback: Fix internal class name leakage (MASSA_OT_gen_ -> massa.gen_)
    if op_id.startswith("MASSA_OT_gen_"):
        suffix = op_id.split("MASSA_OT_gen_")[-1]
        op_id = f"massa.gen_{suffix}"
        
    obj["massa_op_id"] = op_id

    # [ARCHITECT NEW] Save Parameters for Resurrection
    try:
        obj["MASSA_PARAMS"] = _capture_operator_params(op)
    except Exception as e:
        print(f"Massa Save Error: {e}")

    for p in mesh.polygons:
        p.use_smooth = True

    if has_bevel and viz_mode != "SLOTS":
        mod = obj.modifiers.new("Massa_Bevel", "BEVEL")
        mod.limit_method = "WEIGHT"
        mod.width = 0.01 * getattr(op, "global_scale", 1.0)
        mod.segments = 2
        mod.profile = 0.7

    force_auto_unwrap = getattr(op, "auto_unwrap", False)

    needs_unwrap = False
    for i in range(10):
        if manifest[i]["uv"] == "UNWRAP":
            needs_unwrap = True
            break

    if force_auto_unwrap:
        needs_unwrap = True

    allow_unwrap = (viz_mode != "SLOTS") or (debug_mode == "UV")

    allow_unwrap = (viz_mode != "SLOTS") or (debug_mode == "UV")
    
    # [ARCHITECT FIX] Force Unwrap if user explicitly requests Auto-Unwrap
    if force_auto_unwrap:
        allow_unwrap = True

    # 1. Standard Per-Slot Unwrap (LSCM / Conformal)
    # We allow this to run naturally so we respect 'UNWRAP' vs 'BOX' vs 'SKIP'
    if needs_unwrap and allow_unwrap:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        for i in range(10):
            # [ARCHITECT FIX] Treat SKIP as UNWRAP if Auto-Unwrap is ON
            should_unwrap = (manifest[i]["uv"] == "UNWRAP")
            if force_auto_unwrap and manifest[i]["uv"] == "SKIP":
                should_unwrap = True

            # [ARCHITECT FIX] Allow Manual KEEP (Preserve UVs but allow packing)
            if manifest[i]["uv"] == "KEEP":
                should_unwrap = False

            if should_unwrap:
                if is_debug_override:
                    bpy.ops.mesh.select_all(action="SELECT")
                else:
                    # [ARCHITECT FIX] Use Remapped Slot Index
                    # If this slot (i) was not used, it won't be in the map.
                    if i in slot_map:
                        obj.active_material_index = slot_map[i]
                        bpy.ops.object.material_slot_select()
                    else:
                        continue # Skip unwrapping if no geometry uses this slot

                # [ARCHITECT LOGIC] Decide Strategy
                # If Auto-Unwrap is ON and NO Seams are active, use Smart Project.
                # If Seams are active, trust them (LSCM).
                use_smart = (force_auto_unwrap and not getattr(op, "seam_active", False))

                if use_smart:
                    try:
                        bpy.ops.uv.smart_project(
                            angle_limit=66.0,
                            island_margin=0.0,
                            area_weight=0.0,
                            correct_aspect=True,
                            scale_to_bounds=False,
                        )
                    except:
                        pass
                else:
                    try:
                        bpy.ops.uv.unwrap(
                            method="ANGLE_BASED", margin=0.001, correct_aspect=True
                        )
                    except Exception as e:
                        # [ARCHITECT HYBRID] Fallback to Smart Project if LSCM fails
                        # This prevents "Unwrap failed to solve" errors on closed meshes
                        print(f"Massa UV Fallback (Slot {i}): {e}")
                        try:
                            bpy.ops.uv.smart_project(
                                angle_limit=66.0,
                                island_margin=0.0,
                                area_weight=0.0,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                        except:
                            pass
                bpy.ops.mesh.select_all(action="DESELECT")
                if is_debug_override:
                    break
        bpy.ops.object.mode_set(mode="OBJECT")

    # 2. [ARCHITECT NEW] Global Packing Enforcement
    # If Auto-Unwrap is on, we take WHATEVER UVs exist (Analytic or Unwrapped)
    # and pack them strictly into 0-1 bounds.
    if getattr(op, "auto_unwrap", False) and allow_unwrap:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.uv.pack_islands(
                margin=getattr(op, "auto_unwrap_margin", 0.02),
                rotate=True,
                scale=True, # Force fit to 0-1
            )
        except Exception as e:
            print(f"Auto Pack Error: {e}")
        bpy.ops.object.mode_set(mode="OBJECT")

    massa_sockets.spawn_socket_objects(
        obj, socket_data, manifest, op.global_scale, op.ui_use_rot, op.rotation
    )

    if debug_mode == "SEAM":
        obj.show_wire = True
        obj.show_all_edges = True
    else:
        # [ARCHITECT FIX] Respect user wireframe preference even in SLOTS mode
        obj.show_wire = op.show_wireframe
        obj.show_all_edges = op.show_wireframe

    if op.pol_fuse_active:
        massa_polish.apply_sdf_fuse(obj, op)
    should_apply = any(getattr(op, f"sep_{i}", False) for i in range(10))
    if should_apply and op.pol_fuse_active:
        if not obj.select_get():
            obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier="Massa_Fuse")
        except:
            pass

    # [ARCHITECT VIZ OVERLAY]
    # Moved to END of stack to prevent baking tubes into Fuse or Mesh
    if viz_mode == "SLOTS":
        try:
            # Ensure Viz Materials exist
            mat_utils.ensure_gn_viz_materials()

            # 1. Get the GN Tree
            viz_tree = massa_nodes.get_or_create_viz_overlay_tree()

            # 2. Add Modifier (Always Last)
            mod_viz = obj.modifiers.new("Massa_Edge_Viz", "NODES")
            mod_viz.node_group = viz_tree

            # 3. Assign the 'Neutral/Clay' material to the GN 'Material' input
            viz_mat = mat_utils.get_or_create_viz_vertex_material()
            if viz_mat:
                if "Material" in mod_viz.keys():
                    mod_viz["Material"] = viz_mat

        except Exception as e:
            print(f"Massa Viz Error: {e}")

    massa_polish.handle_separation(obj, op, manifest, context, slot_map=slot_map)

    context.view_layer.objects.active = obj
    if is_debug_override:
        obj.select_set(False)
    else:
        if not obj.select_get():
            obj.select_set(True)

    if context.space_data and context.space_data.type == "VIEW_3D":
        overlay = context.space_data.overlay
        if viz_mode == "NATIVE":
            overlay.show_edge_seams = True
            overlay.show_edge_sharp = True
            overlay.show_edge_crease = True
            try:
                overlay.show_edge_bevel_weight = True
            except:
                pass
            overlay.show_overlays = True

        if is_debug_override:
            context.space_data.shading.type = "MATERIAL"

    # [ARCHITECT NEW] Phase 4 Protocol: Physics Volumes & Socket Forge
    try:
        if getattr(op, "phys_gen_ucx", False):
            phys_gen_ucx(obj, op, manifest, slot_map)
        if getattr(op, "phys_auto_rig", False):
            phys_auto_rig(obj, op, manifest)

        # [ARCHITECT NEW] Phase 4: Socket Forge (Physical)
        if collected_sockets:
            vis_size = getattr(op, "sock_visual_size", 0.1)
            con_type = getattr(op, "sock_constraint_type", 'NONE')
            break_force = getattr(op, "sock_break_strength", 250.0)

            # Map Enum to Blender Types
            TYPE_MAP = {
                'FIXED': 'FIXED',
                'HINGE': 'HINGE',
                'SLIDER': 'SLIDER',
                'SPRING': 'GENERIC_SPRING'
            }

            for sid, center, normal in collected_sockets:
                s_name = f"SOCKET_{obj.name}_{sid:02d}"
                sock = bpy.data.objects.new(s_name, None)
                sock.empty_display_type = 'ARROWS'
                sock.empty_display_size = vis_size

                # Link
                if context.collection:
                    context.collection.objects.link(sock)
                else:
                    context.scene.collection.objects.link(sock)

                # Parent First (Establishes Local Space)
                sock.parent = obj

                # Align Z to Normal
                z_vec = normal
                up_vec = Vector((0,0,1))
                if abs(z_vec.dot(up_vec)) > 0.95:
                    up_vec = Vector((0,1,0))
                x_vec = up_vec.cross(z_vec).normalized()
                y_vec = z_vec.cross(x_vec).normalized()

                rot_mat = Matrix((x_vec, y_vec, z_vec)).transposed()

                # Set Transforms (Local Space)
                sock.location = center
                sock.rotation_euler = rot_mat.to_euler()

                # Apply Constraints
                if con_type != 'NONE' and con_type in TYPE_MAP:
                    b_type = TYPE_MAP[con_type]

                    # Ensure selection for Operator
                    bpy.ops.object.select_all(action='DESELECT')
                    sock.select_set(True)
                    context.view_layer.objects.active = sock

                    try:
                        # Add Rigid Body Constraint (Empty becomes a Constraint Object)
                        bpy.ops.rigidbody.constraint_add(type=b_type)
                        rbc = sock.rigid_body_constraint
                        # Object 1 is Main Object (Parent)
                        rbc.object1 = obj
                        # Object 2 is left blank (Connecting Piece)
                        rbc.use_breaking = True
                        rbc.breaking_threshold = break_force
                    except Exception as ce:
                        print(f"Socket Constraint Error ({s_name}): {ce}")

            # Restore Selection to Main Object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

    except Exception as e:
        print(f"Phase 4 Physics/Socket Error: {e}")
        traceback.print_exc()


def phys_gen_ucx(obj, op, manifest, slot_map):
    """
    PHASE 4: UCX COLLISION FORGE
    Generates optimized collision meshes for ALL used Slots.
    Supports: BOX, SPHERE, CAPSULE, HULL, MESH.
    """
    # [ARCHITECT UPDATED] Target all active slots in the map
    target_slots = set(slot_map.keys()) if slot_map else set()

    # Fallback if map is missing (though it shouldn't be)
    if not target_slots:
        target_slots = {0, 1, 2}  # Legacy Fallback

    # Identify all participating geometry (Main + Detached Children)
    all_objs = [obj] + [c for c in obj.children if c.type == "MESH"]

    # Pre-fetch slot names from cartridge metadata
    slot_names = {}
    try:
        if hasattr(op, "get_slot_meta"):
            meta = op.get_slot_meta()
            for i, data in meta.items():
                slot_names[i] = data.get("name", f"Slot_{i}")
    except:
        pass

    for i in target_slots:
        # Resolve Material Index
        mat_idx = i
        if slot_map:
            mat_idx = slot_map.get(i)

        if mat_idx is None:
            continue

        # 1. Determine Shape & Name
        shape_type = getattr(op, f"collision_shape_{i}", "BOX")

        slot_label = slot_names.get(i, f"{i:02d}")
        # Sanitize label
        slot_label = slot_label.replace(" ", "_").replace(".", "_")

        ucx_name = f"UCX_{obj.name}_{slot_label}"

        # 2. Collect Geometry
        # We need full geometry for MESH, just verts for others (mostly)

        collected_verts = []
        collected_faces = []  # List of lists of indices into collected_verts

        vert_offset = 0

        has_geom = False

        for part in all_objs:
            try:
                me = part.data
                if not me.vertices:
                    continue

                # We need BMesh to filter faces by material index easily
                bm_temp = bmesh.new()
                bm_temp.from_mesh(me)

                # Transform to Main Object Local Space if needed
                if part != obj:
                    bmesh.ops.transform(
                        bm_temp, matrix=part.matrix_local, verts=bm_temp.verts
                    )

                # Filter faces
                part_faces = [f for f in bm_temp.faces if f.material_index == mat_idx]

                if not part_faces:
                    bm_temp.free()
                    continue

                has_geom = True

                # Extract Geometry
                # We need to map local verts to global collected_verts
                # Optimization: Only extract used verts

                used_verts = set()
                for f in part_faces:
                    for v in f.verts:
                        used_verts.add(v)

                # Create a mapping from bm_vert to new index
                v_map = {}
                sorted_verts = list(used_verts)  # Stable order

                for v in sorted_verts:
                    collected_verts.append(v.co.copy())
                    v_map[v] = vert_offset
                    vert_offset += 1

                for f in part_faces:
                    face_indices = [v_map[v] for v in f.verts]
                    collected_faces.append(face_indices)

                bm_temp.free()
            except Exception as e:
                print(f"Geometry Collection Error ({part.name}): {e}")
                pass

        if not has_geom:
            continue

        # 3. Generate Shape
        try:
            bm_final = bmesh.new()

            if shape_type == "MESH":
                # Reconstruct Mesh
                # Add vertices
                bm_verts = [bm_final.verts.new(co) for co in collected_verts]
                bm_final.verts.ensure_lookup_table()

                # Add faces
                for f_idx in collected_faces:
                    try:
                        verts = [bm_verts[idx] for idx in f_idx]
                        bm_final.faces.new(verts)
                    except ValueError:
                        # Duplicate faces or invalid geometry might occur
                        pass

                bmesh.ops.recalc_face_normals(bm_final, faces=bm_final.faces)

            elif shape_type == "HULL":
                # Add vertices only
                for co in collected_verts:
                    bm_final.verts.new(co)

                bmesh.ops.convex_hull(bm_final, input=bm_final.verts[:])
                # Clean up loose geometry if any (convex_hull output might leave original verts?)
                # Actually convex_hull returns geom.
                # Usually best to just use the result.
                # But typically it modifies bm_final in place.

            elif shape_type == "BOX":
                # Bounding Box
                min_v = Vector((float("inf"), float("inf"), float("inf")))
                max_v = Vector((float("-inf"), float("-inf"), float("-inf")))

                for co in collected_verts:
                    min_v.x = min(min_v.x, co.x)
                    min_v.y = min(min_v.y, co.y)
                    min_v.z = min(min_v.z, co.z)
                    max_v.x = max(max_v.x, co.x)
                    max_v.y = max(max_v.y, co.y)
                    max_v.z = max(max_v.z, co.z)

                center = (min_v + max_v) / 2
                size = max_v - min_v

                # Create Cube
                bmesh.ops.create_cube(bm_final, size=1.0)  # Unit cube
                # Scale and Translate
                bmesh.ops.scale(bm_final, vec=size, verts=bm_final.verts)
                bmesh.ops.translate(bm_final, vec=center, verts=bm_final.verts)

            elif shape_type == "SPHERE":
                # Bounding Sphere
                min_v = Vector((float("inf"), float("inf"), float("inf")))
                max_v = Vector((float("-inf"), float("-inf"), float("-inf")))

                for co in collected_verts:
                    min_v.x = min(min_v.x, co.x)
                    min_v.y = min(min_v.y, co.y)
                    min_v.z = min(min_v.z, co.z)
                    max_v.x = max(max_v.x, co.x)
                    max_v.y = max(max_v.y, co.y)
                    max_v.z = max(max_v.z, co.z)

                center = (min_v + max_v) / 2
                # Simple radius: max distance from center
                radius = 0.0
                for co in collected_verts:
                    dist = (co - center).length
                    if dist > radius:
                        radius = dist

                bmesh.ops.create_uvsphere(
                    bm_final, u_segments=16, v_segments=8, radius=radius
                )
                bmesh.ops.translate(bm_final, vec=center, verts=bm_final.verts)

            elif shape_type == "CAPSULE":
                # Bounding Capsule (Approximation using Cylinder/Capsule logic)
                # Since BMesh doesn't have create_capsule, we use a Cylinder.
                # Or we can just do a bounding box Z-aligned Cylinder.

                min_v = Vector((float("inf"), float("inf"), float("inf")))
                max_v = Vector((float("-inf"), float("-inf"), float("-inf")))

                for co in collected_verts:
                    min_v.x = min(min_v.x, co.x)
                    min_v.y = min(min_v.y, co.y)
                    min_v.z = min(min_v.z, co.z)
                    max_v.x = max(max_v.x, co.x)
                    max_v.y = max(max_v.y, co.y)
                    max_v.z = max(max_v.z, co.z)

                center = (min_v + max_v) / 2
                size = max_v - min_v
                radius = max(size.x, size.y) / 2.0
                height = size.z

                # Cylinder
                bmesh.ops.create_cone(
                    bm_final,
                    cap_ends=True,
                    cap_tris=False,
                    segments=16,
                    radius1=radius,
                    radius2=radius,
                    depth=height,
                )
                bmesh.ops.translate(bm_final, vec=center, verts=bm_final.verts)

            # 4. Finalize
            mesh_ucx = bpy.data.meshes.new(f"Mesh_{ucx_name}")
            bm_final.to_mesh(mesh_ucx)
            bm_final.free()

            ucx_obj = bpy.data.objects.new(ucx_name, mesh_ucx)

            # Link
            if obj.users_collection:
                obj.users_collection[0].objects.link(ucx_obj)
            else:
                bpy.context.collection.objects.link(ucx_obj)

            ucx_obj.parent = obj
            # [ARCHITECT FIX] Set display type to WIRE for cleanliness
            ucx_obj.display_type = "WIRE"
            ucx_obj.hide_render = True

        except Exception as e:
            print(f"UCX Shape Error (Slot {i}): {e}")
            import traceback

            traceback.print_exc()


def phys_auto_rig(obj, op, manifest):
    """
    PHASE 4: AUTO-RIGGER
    Detects detached parts and auto-rigs them with Hinge Constraints.
    """
    # [ARCHITECT UPDATED] Strict Child Validation
    children = []
    for c in obj.children:
        if c.type == "MESH" and c.data and len(c.data.vertices) > 0:
            # Ensure it's not a helper/empty
            children.append(c)

    if not children:
        return

    yield_strength = getattr(op, "phys_yield_strength", 10.0)
    break_force = yield_strength * 1000.0
    
    for child in children:
        try:
            # We assume any child mesh is a detached part from our system.
            # Calculate Boundary Center
            me = child.data
            bm_child = bmesh.new()
            bm_child.from_mesh(me)
            
            boundary_edges = [e for e in bm_child.edges if e.is_boundary]
            
            center = Vector((0,0,0))
            if boundary_edges:
                b_verts = set()
                for e in boundary_edges:
                    b_verts.add(e.verts[0])
                    b_verts.add(e.verts[1])
                
                if b_verts:
                    center = sum((v.co for v in b_verts), Vector()) / len(b_verts)
            else:
                # Fallback to BBox Center
                center = sum((Vector(v) for v in child.bound_box), Vector()) / 8.0
            
            bm_child.free()
            
            # Convert Center to Parent Local Space logic
            # Child.matrix_local is transform relative to Parent.
            # Center is in Child Local Space.
            # Pivot (in Parent Space) = Child.matrix_local @ Center
            pivot_local = child.matrix_local @ center
            
            # Create Joint Empty
            joint_name = f"MASSA_JOINT_{child.name}"
            empty = bpy.data.objects.new(joint_name, None)
            
            if obj.users_collection:
                obj.users_collection[0].objects.link(empty)
            else:
                bpy.context.collection.objects.link(empty)

            # Align Empty Matrix
            # [ARCHITECT FIX] Set location in local space AFTER parenting.
            # pivot_local is already in Parent's local space.
            empty.parent = obj
            empty.location = pivot_local
            
            # Create Rigid Body Constraint
            # We add it to the scene collection but need to enable RB
            bpy.ops.object.select_all(action="DESELECT")
            empty.select_set(True)
            bpy.context.view_layer.objects.active = empty

            # Add Rigid Body Constraint via Operator (Safest)
            # This ensures physics world is respected/created
            try:
                bpy.ops.rigidbody.constraint_add(type='HINGE')
                rbc = empty.rigid_body_constraint
                rbc.object1 = obj
                rbc.object2 = child
                rbc.use_breaking = True
                rbc.breaking_threshold = break_force
            except:
                # Fallback if ops fail (e.g. no RB world)
                pass
                
        except Exception as e:
            print(f"Auto-Rig Error ({child.name}): {e}")
