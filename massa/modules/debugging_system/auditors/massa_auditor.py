import bmesh
import mathutils


def audit_mesh(obj, op_class=None):
    """
    Standard entry point consumed by ``auditors.run_all_auditors``.

    Wraps :class:`Massa_Auditor` (dimensions / slot layer / integrity /
    degenerate geometry) and returns its flag list. Without this wrapper the
    class was never invoked by the dynamic loader.
    """
    if getattr(obj, "type", None) != 'MESH':
        return []

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        meta_flags = {}
        # Honour an explicit open-mesh allowance if the operator advertises one
        # via CARTRIDGE_META flags (keeps open shells from reading as critical).
        flags = getattr(op_class, "CARTRIDGE_FLAGS", None) or {}
        if isinstance(flags, dict) and flags.get("ALLOW_OPEN_MESH"):
            meta_flags["ALLOW_OPEN_MESH"] = True
        report = Massa_Auditor(bm).run_full_scan(meta_flags=meta_flags)
        return report.get("flags", [])
    except Exception as e:
        return [f"CRITICAL_AUDITOR_CRASH_massa_auditor: {str(e)}"]
    finally:
        bm.free()


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

        # [ARCHITECT NEW] Degenerate Geometry Check
        zero_area = []
        thin_faces = []

        for f in self.bm.faces:
            area = f.calc_area()
            if area < 0.000001:
                zero_area.append(f)
            else:
                # Check Aspect Ratio / Thinness (Perimeter^2 / Area)
                # A square has ratio ~16. A 1x100 strip has ratio ~400.
                perimeter = sum([e.calc_length() for e in f.edges])
                if perimeter > 0:
                    ratio = (perimeter * perimeter) / area
                    # Threshold 1000 allows reasonably thin strips but catches slivers
                    if ratio > 1000.0:
                         thin_faces.append(f)

        if zero_area:
            self.report["flags"].append(f"CRITICAL_ZERO_AREA_FACES_{len(zero_area)}")
            self.report["status"] = "FAIL"

        if thin_faces:
             self.report["flags"].append(f"WARNING_THIN_FACES_{len(thin_faces)}")
             # Thin faces are bad for UVs and Bevels
             self.report["status"] = "FAIL"