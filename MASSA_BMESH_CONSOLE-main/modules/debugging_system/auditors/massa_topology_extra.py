
import bmesh

def audit_mesh(obj, op_class=None):
    """
    Extra Topology Checks:
    1. Loose Vertices (Vertices not linked to any edges)
    2. Wire Edges (Edges with 0 faces)
    """
    errors = []
    
    if obj.type != 'MESH':
        return []

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    # 1. Loose Vertices
    loose_verts = [v for v in bm.verts if not v.link_edges]
    if loose_verts:
        errors.append(f"CRITICAL_LOOSE_VERTS_{len(loose_verts)}")
        
    # 2. Wire Edges
    wire_edges = [e for e in bm.edges if not e.link_faces]
    if wire_edges:
        errors.append(f"CRITICAL_WIRE_EDGES_{len(wire_edges)}")
        
    bm.free()
    return errors
