import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from ..modules import cartridges

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from ..modules import cartridges

# This file previously contained MCP-Bridge specific operators.
# They have been removed as part of the MCP cleanup.
# This file is kept as a placeholder to avoid breaking imports in __init__.py 
# if it is imported as a whole module, although __init__.py was already cleaned.
# However, to be safe, we leave it empty or with a comment.

