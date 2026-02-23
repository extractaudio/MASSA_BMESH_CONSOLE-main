import bmesh
import math

def audit_mesh(obj):
    """
    Entry point for the Edge Slot Auditor.
    Analyzes the mesh for proper Seam placement (Slot 1/3) to ensure UV unwraps work.
    """
    if obj.type != 'MESH': return []

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    auditor = Massa_Edge_Auditor(bm)
    flags = auditor.run_scan()

    bm.free()
    return flags

class Massa_Edge_Auditor:
    def __init__(self, bm: bmesh.types.BMesh):
        self.bm = bm
        self.report = {"status": "PASS", "flags": []}

    def run_scan(self):
        try:
            self.bm.verts.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()
            self.bm.faces.ensure_lookup_table()

            # 1. Check Layer Existence
            layer = self._check_edge_slots_layer()

            if layer:
                # 2. Analyze Seams
                self._analyze_seam_placement(layer)

        except Exception as e:
            self.report["status"] = "FAIL"
            self.report["flags"].append(f"EDGE_AUDIT_ERROR: {str(e)}")

        return self.report["flags"]

    def _check_edge_slots_layer(self):
        layer = self.bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not layer:
            # If the mesh is trivial (e.g. a single plane), missing layer is fine.
            # But generally cartridges should initialize it.
            if len(self.bm.faces) > 0:
                self.report["flags"].append("WARNING_MISSING_EDGE_SLOTS_LAYER")
            return None
        return layer

    def _analyze_seam_placement(self, layer):
        # Count Seams (Slot 1=Perimeter, 3=Guide)
        # Note: Slot 1 is often used for Bevels/Perimeter. Slot 3 is explicitly "Guide/Seam".
        # But commonly both are treated as seams by the unwrap logic (Workflow_builder.md says "Use Edge Slots 1, 3, 5 as UV Seams").

        seam_edges = [e for e in self.bm.edges if e[layer] in [1, 3, 5]]
        seam_count = len(seam_edges)

        # Analyze Mesh Complexity
        if not self.bm.verts: return

        bbox_min = [min([v.co[i] for v in self.bm.verts]) for i in range(3)]
        bbox_max = [max([v.co[i] for v in self.bm.verts]) for i in range(3)]
        dims = [bbox_max[i] - bbox_min[i] for i in range(3)]

        is_3d = all(d > 0.01 for d in dims) # It has thickness in all 3 dims
        face_count = len(self.bm.faces)

        # Rule 1: Complex 3D Manifolds MUST have seams
        # If it's a closed volume (or close to it) with > 12 faces (2 cubes worth), it needs seams.
        if is_3d and face_count > 12:
            if seam_count == 0:
                self.report["flags"].append("CRITICAL_NO_SEAMS_ON_COMPLEX_MESH")
                self.report["status"] = "FAIL"
                return

        # Rule 2: Isolated Seams
        # Seams that don't connect to other seams or boundaries are often mistakes (except for zipper cuts on cylinders).
        # A zipper cut on a cylinder: Connects Top Rim (Boundary) to Bottom Rim (Boundary).
        # So it should connect to something.

        if seam_count > 0:
            isolated_seams = 0
            for e in seam_edges:
                # Check endpoints
                is_connected = False
                for v in e.verts:
                    # Check if vertex is on a boundary (open mesh)
                    if v.is_boundary:
                        is_connected = True
                        break

                    # Check if vertex connects to another seam edge
                    for linked_e in v.link_edges:
                        if linked_e is not e and linked_e[layer] in [1, 3, 5]:
                            is_connected = True
                            break
                    if is_connected: break

                if not is_connected:
                    isolated_seams += 1

            if isolated_seams > 0:
                # This is just a warning, as sometimes a floating cut is valid (e.g. stress relief),
                # but usually implies a seam that stops in the middle of a face loop.
                self.report["flags"].append(f"WARNING_ISOLATED_SEAM_EDGES_{isolated_seams}")

        # Rule 3: Cylinder Check (Heuristic)
        # If we have a loop of > 4 faces that share edges but no seams cut them, it's a cylinder/tube.
        # This is expensive to detect perfectly, but we can check for "high valence" of face connectivity without seams.
        # Skip for now to keep performance high.
