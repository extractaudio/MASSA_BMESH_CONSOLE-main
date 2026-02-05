import bmesh
import mathutils

class Massa_Auditor:
    def __init__(self, bm: bmesh.types.BMesh):
        self.bm = bm
        self.report = {"status": "PASS", "flags": [], "dimensions": {}, "slots": {}}

    def run_full_scan(self, meta_flags=None):
        if meta_flags is None: meta_flags = {}
        try:
            self._check_dimensions()
            self._check_slots()
            self._check_integrity(meta_flags)
        except Exception as e:
            self.report["status"] = "FAIL"
            self.report["flags"].append(f"AUDITOR_INTERNAL_ERROR: {str(e)}")
        return self.report

    def _check_dimensions(self):
        self.bm.verts.ensure_lookup_table()
        if not self.bm.verts:
            self.report["flags"].append("CRITICAL_EMPTY_MESH")
            self.report["status"] = "FAIL"
            return
        z_coords = [v.co.z for v in self.bm.verts]
        if (max(z_coords) - min(z_coords)) < 0.001:
             self.report["flags"].append("CRITICAL_FLAT_Z_AXIS")

    def _check_slots(self):
        layer = self.bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not layer:
            self.report["flags"].append("CRITICAL_MISSING_SLOT_LAYER")
            self.report["status"] = "FAIL"
            return
        if not any(e[layer] == 1 for e in self.bm.edges):
            self.report["flags"].append("CRITICAL_NO_PERIMETER_DEFINED")
            self.report["status"] = "FAIL"

    def _check_integrity(self, meta):
        loose = [v for v in self.bm.verts if not v.link_edges]
        if loose:
            self.report["flags"].append(f"CRITICAL_LOOSE_VERTS_{len(loose)}")
            self.report["status"] = "FAIL"
        
        non_manifold = [e for e in self.bm.edges if not e.is_manifold]
        if non_manifold:
            if meta.get("ALLOW_OPEN_MESH", False):
                self.report["flags"].append(f"INFO_OPEN_SHELL_{len(non_manifold)}")
            else:
                self.report["flags"].append(f"CRITICAL_NON_MANIFOLD_{len(non_manifold)}")
                self.report["status"] = "FAIL"