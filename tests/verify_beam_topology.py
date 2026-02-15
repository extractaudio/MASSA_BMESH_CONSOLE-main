import bpy
import bmesh
from mathutils import Vector

def test_beam_topology():
    # 1. Create BMesh
    bm = bmesh.new()
    
    # 2. Replicate 'BOX' profile logic
    w, h = 0.2, 0.4
    hw = w / 2.0
    # pts = [(-0.1, 0), (0, 0), (0.1, 0), (0.1, 0.4), (-0.1, 0.4)]
    pts = [(-hw, 0), (0, 0), (hw, 0), (hw, h), (-hw, h)]
    
    # Create base verts
    base_verts = [bm.verts.new((p[0], 0.0, p[1])) for p in pts]
    bm.verts.ensure_lookup_table()
    
    # Create face
    start_cap = bm.faces.new(base_verts)
    
    # Extrude
    res_ext = bmesh.ops.extrude_face_region(bm, geom=[start_cap])
    verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts_ext, vec=(0.0, 3.0, 0.0))
    
    # Check edges
    bm.edges.ensure_lookup_table()
    seam_edges = []
    
    print("\n--- CHECKING EDGES ---")
    count_center = 0
    for e in bm.edges:
        v1 = e.verts[0]
        v2 = e.verts[1]
        
        is_center_x = (abs(v1.co.x) < 0.0001) and (abs(v2.co.x) < 0.0001)
        is_center_z = (abs(v1.co.z) < 0.0001) and (abs(v2.co.z) < 0.0001)
        
        if is_center_x and is_center_z:
            count_center += 1
            print(f"Center Edge: {v1.co} -> {v2.co}")
            seam_edges.append(e)

    print(f"Total Center Edges Found: {count_center}")
    
    # Check if we have vertices at (0,0,0) and (0,3,0)
    verts_at_zero = [v for v in bm.verts if abs(v.co.x) < 0.001 and abs(v.co.z) < 0.001]
    print(f"Vertices at X=0, Z=0: {len(verts_at_zero)}")
    for v in verts_at_zero:
        print(f"  v: {v.co}")

    bm.free()

if __name__ == "__main__":
    test_beam_topology()
