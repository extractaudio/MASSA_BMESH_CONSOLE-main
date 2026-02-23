import bpy
import sys
import os

sys.path.append(os.getcwd())

# Mock environment
from massa.operators.massa_base import Massa_OT_Base
from massa.modules.cartridges.cart_ind_11_crane import MASSA_OT_IndCrane

# Register
try:
    bpy.utils.register_class(MASSA_OT_IndCrane)
except:
    pass

print(f"Class: {MASSA_OT_IndCrane}")
print(f"Has bl_rna: {hasattr(MASSA_OT_IndCrane, 'bl_rna')}")

if hasattr(MASSA_OT_IndCrane, 'bl_rna'):
    print("RNA Props:")
    for k in MASSA_OT_IndCrane.bl_rna.properties.keys():
        print(f"  - {k}")

print("Annotations:")
for k, v in MASSA_OT_IndCrane.__annotations__.items():
    print(f"  - {k}: {v}")
    if hasattr(v, 'keywords'):
        print(f"    Keywords: {v.keywords}")
