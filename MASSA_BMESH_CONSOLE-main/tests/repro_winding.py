
import bpy
import bmesh
from mathutils import Vector

def repro_winding():
    bm = bmesh.new()
    
    # Coordinates from analysis (approximate)
    s = 1.0
    # Hub X TR (Top Right of X Hub)
    # X Hub is at (s, 0) approx? No, xx, xy = s*0.7, s*0.1
    # Let's use the explicit coordinates that caused issues.
    
    # From code:
    # v_tip_x = (s, 0, 0)
    # x_rig_line[-1] is X_TR projected to x=s. (So s, something, 0)
    # x_diag_v[0] is X_TR projected to diagonal x+y=s.
    
    # Assume X_TR is somewhat to the left of x=s and below diagonal.
    # e.g. (0.8, 0.2)
    x_tr = bm.verts.new(Vector((0.8, 0.2, 0.0)))
    
    # x_rig_line[-1]: Project X_TR to x=s -> (1.0, 0.2)
    x_proj_limit = bm.verts.new(Vector((1.0, 0.2, 0.0)))
    
    # v_tip_x: (s, 0, 0) -> (1.0, 0.0, 0.0)
    v_tip_x = bm.verts.new(Vector((1.0, 0.0, 0.0)))
    
    # x_diag_v[0]: Project X_TR to x+y=s along (1,1)
    # x = 0.8, y = 0.2. x+y=1.0. It is ON the diagonal?
    # xx, xy = s*0.7, s*0.1 -> 0.7, 0.1.
    # Hub radius 0.03.
    # TR corner of hub: 0.7 + r, 0.1 + r?
    # 0.7+0.03 = 0.73. 0.1+0.03=0.13. 
    # TR = (0.73, 0.13). Sum = 0.86 < 1.0.
    # So it projects to diagonal.
    
    # Projection: t = (1.0 - 0.73 - 0.13)/2 = 0.14/2 = 0.07.
    # Dest = (0.73+0.07, 0.13+0.07) = (0.80, 0.20).
    x_diag_proj = bm.verts.new(Vector((0.80, 0.20, 0.0)))
    
    # Update X_TR to match this scenario
    x_tr.co = Vector((0.73, 0.13, 0.0))
    x_proj_limit.co = Vector((1.0, 0.13, 0.0))
    
    # --- EXISTING CODE ---
    # Tri 1: X_TR, v_tip_x, X_TR_Proj_X (limit)
    # (0.73,0.13), (1.0,0.0), (1.0, 0.13)
    # Vector 1: Tip - TR = (0.27, -0.13)
    # Vector 2: Limit - TR = (0.27, 0.0)
    # Cross: 0.27*0 - (-0.13)*0.27 = +0.035. Positive Z -> CCW (Correct)
    try:
        f1 = bm.faces.new((x_tr, v_tip_x, x_proj_limit))
        f1.normal_update()
    except Exception as e:
        print(f"Face 1 Error: {e}")
        
    try:
        # NEW Winding: X_TR, v_tip_x, X_TR_Proj_Diag
        # Matches the fix applied in cart_prim_06_gusset.py
        f2 = bm.faces.new((x_tr, v_tip_x, x_diag_proj))
        f2.normal_update()
        print(f"Face 2 Normal: {f2.normal}")
        
        if f2.normal.z < -0.001:
            print("FAILURE: Face 2 is CW (Down)")
        elif f2.normal.z > 0.001:
            print("SUCCESS: Face 2 is CCW (Up)")
        else:
            print("WARNING: Face 2 Normal is Zero/Undefined")
    except Exception as e:
        print(f"Face 2 Error: {e}")
        
if __name__ == "__main__":
    repro_winding()

