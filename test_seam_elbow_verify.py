import math
import bmesh
import bpy
import sys
import os

sys.path.append(os.getcwd())

# Setup mock for bpy context
from massa.modules.cartridges.cart_prim_02_pipe import MASSA_OT_PrimPipe

print("Module loaded.")
