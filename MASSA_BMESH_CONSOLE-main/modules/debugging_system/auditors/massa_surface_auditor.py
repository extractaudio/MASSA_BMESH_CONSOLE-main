import bmesh
import mathutils

# Safe Import for BVH (Prevents crashes on some Blender installs)
try:
    from mathutils.bvhtree import BVHTree
    HAS_BVH = True
except ImportError:
    HAS_BVH = False

class Massa_Surface_Auditor:
    def __init__(self, bm: bmesh.types.BMesh):
        self.bm = bm
        self.report = {
            "status": "PASS",
            "flags": [],
            "metrics": {"overlap_count": 0, "spike_count": 0}
        }

    def run_scan(self, meta_flags=None):
        if meta_flags is None: meta_flags = {}
        
        try:
            self.bm.faces.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()
            self.bm.verts.ensure_lookup_table()
            
            # 1. Structural Checks
            self._check_uv_existence()
            self._check_normals()
            self._check_degenerate_faces()
            
            # 2. Optical Checks (Expensive, only run if structure is sound)
            if self.report["status"] == "PASS":
                self._check_self_intersections()
                self._check_uv_integrity()
                self._check_collapsed_uvs()
                
        except Exception as e:
            self.report["status"] = "FAIL"
            self.report["flags"].append(f"SURFACE_AUDIT_ERROR: {str(e)}")
            
        return self.report

    def _check_uv_existence(self):
        try:
            uv_layer = self.bm.loops.layers.uv.verify()
        except:
            self.report["flags"].append("CRITICAL_MISSING_UV_LAYER")
            self.report["status"] = "FAIL"
            return

        has_data = False
        # Sample first 50 faces to save performance
        sample = self.bm.faces[:50] if len(self.bm.faces) > 50 else self.bm.faces
        for face in sample:
            for loop in face.loops:
                if loop[uv_layer].uv.length > 0.0001:
                    has_data = True
                    break
            if has_data: break
            
        if not has_data and len(self.bm.faces) > 0:
            self.report["flags"].append("CRITICAL_ZERO_UV_DATA")
            self.report["status"] = "FAIL"

    def _check_normals(self):
        if not self.bm.verts: return
        center = mathutils.Vector((0,0,0))
        for v in self.bm.verts: center += v.co
        center /= len(self.bm.verts)
        
        flipped = 0
        for f in self.bm.faces:
            if (f.calc_center_median() - center).dot(f.normal) < -0.0001: 
                flipped += 1
                
        if len(self.bm.faces) > 0 and (flipped / len(self.bm.faces)) > 0.5:
            self.report["flags"].append("CRITICAL_INVERTED_NORMALS")
            self.report["status"] = "FAIL"

    def _check_degenerate_faces(self):
        zero = [f for f in self.bm.faces if f.calc_area() < 0.000001]
        if zero:
            self.report["flags"].append(f"CRITICAL_ZERO_AREA_FACES_{len(zero)}")
            self.report["status"] = "FAIL"

    def _check_self_intersections(self):
        if not HAS_BVH or len(self.bm.faces) < 4: return
        try:
            tree = BVHTree.FromBMesh(self.bm, epsilon=0.0001)
            overlaps = tree.overlap(tree)
            real = 0
            for i1, i2 in overlaps:
                if i1 == i2: continue
                # Check for shared vertices (neighbors)
                if not set(v.index for v in self.bm.faces[i1].verts).isdisjoint(
                       set(v.index for v in self.bm.faces[i2].verts)):
                    continue
                real += 1
            
            if real > 0:
                self.report["metrics"]["overlap_count"] = real // 2
                self.report["flags"].append("CRITICAL_SELF_INTERSECTION")
                self.report["status"] = "FAIL"
        except: pass

    def _check_uv_integrity(self):
        uv_layer = self.bm.loops.layers.uv.verify()
        spikes = 0
        for f in self.bm.faces:
            for l in f.loops:
                uv_len = (l[uv_layer].uv - l.link_loop_next[uv_layer].uv).length
                geo_len = l.edge.calc_length()
                # Spike Rule: UV is huge (>0.8) but Geo is tiny (<0.1)
                if uv_len > 0.8 and geo_len < 0.1:
                    spikes += 1
        
        if spikes > 0:
            self.report["metrics"]["spike_count"] = spikes
            self.report["flags"].append(f"CRITICAL_UV_SPIKES_{spikes}")
            self.report["status"] = "FAIL"

    def _check_collapsed_uvs(self):
        """
        Detects faces that have Area in 3D but Zero Area in UV (Lazy Planar Projection on Sides).
        """
        uv_layer = self.bm.loops.layers.uv.verify()
        collapsed = 0
        
        for f in self.bm.faces:
            # 1. Check Geometric Area ensures we ignore degenerates (handled separately)
            if f.calc_area() > 0.0001:
                # 2. Calculate UV Area
                # Polygon area formula for UVs
                uv_area = 0.0
                for i, loop in enumerate(f.loops):
                    v1 = loop[uv_layer].uv
                    v2 = f.loops[(i + 1) % len(f.loops)][uv_layer].uv
                    uv_area += (v1.x * v2.y) - (v1.y * v2.x)
                uv_area = abs(uv_area * 0.5)
                
                # 3. Flag if UV is collapsed
                if uv_area < 0.000001:
                    collapsed += 1
                    
        if collapsed > 0:
             self.report["flags"].append(f"CRITICAL_COLLAPSED_UVS_{collapsed}")
             self.report["status"] = "FAIL"