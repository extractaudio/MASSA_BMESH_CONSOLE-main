import bpy
import bmesh
from mathutils import Vector
import os

def reproduce_inset():
    log_file = os.path.join(os.path.dirname(__file__), "reproduce_panel_inset_log.txt")
    
    with open(log_file, "w") as f:
        f.write("Starting reproduction...\n")
        
        try:
            bm = bmesh.new()
            
            # Simulate a single tile face
            w = 0.48
            l = 0.48
            h = 0.05
            
            v1 = bm.verts.new((-w/2, -l/2, h))
            v2 = bm.verts.new((w/2, -l/2, h))
            v3 = bm.verts.new((w/2, l/2, h))
            v4 = bm.verts.new((-w/2, l/2, h))
            
            face = bm.faces.new((v1, v2, v3, v4))
            
            f.write(f"Initial Area: {face.calc_area()}\n")
            
            inset_amount = 0.1 # Large enough to be visible
            
            # The logic from cart_prim_04_panel.py
            # res = bmesh.ops.inset_individual(bm, faces=[top_face], thickness=self.inset_amount, use_even_offset=True)
            
            try:
                res = bmesh.ops.inset_individual(
                    bm, 
                    faces=[face], 
                    thickness=inset_amount, 
                    use_even_offset=True
                )
                
                faces_inner = res["faces"]
                
                f.write(f"Inset Result Faces: {len(faces_inner)}\n")
                if faces_inner:
                    f.write(f"Inner Area: {faces_inner[0].calc_area()}\n")
                    
                    # Check edge lengths of inner face to confirm inset
                    for e in faces_inner[0].edges:
                        f.write(f"Inner Edge Len: {e.calc_length()}\n")
                else:
                    f.write("No inner faces returned!\n")
                    
            except Exception as e:
                f.write(f"Error during inset: {e}\n")
            
            bm.free()
            f.write("Finished.\n")
            
        except Exception as e:
            f.write(f"Fatal Error: {e}\n")

if __name__ == "__main__":
    reproduce_inset()
