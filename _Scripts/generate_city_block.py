"""
FUTURISTIC TECH-BRUTALIST CITY BLOCK GENERATOR
===============================================
Generates a dense urban scene using MASSA cartridges + custom bpy objects.
~130 procedural objects across 7 compositional layers.

Execute in Blender:
    exec(open(r'd:\\AntiGravity_google\\MASSA_BMESH_CONSOLE-main\\_Scripts\\generate_city_block.py').read())
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler

PI = math.pi
random.seed(42)

# ============================================================================
# GLOBALS & HELPERS
# ============================================================================

_spawned = []
_errors  = []

def _col(name, parent="CityBlock"):
    """Get or create a collection, nested under parent."""
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        p = bpy.data.collections.get(parent) if parent is not None else None
        if p and c.name not in [ch.name for ch in p.children]:
            p.children.link(c)
        elif not p:
            if c.name not in [ch.name for ch in bpy.context.scene.collection.children]:
                bpy.context.scene.collection.children.link(c)
    return c


def _move(obj, col_name):
    """Move an object into a named collection (under CityBlock)."""
    col = _col(col_name)
    if obj.name not in col.objects:
        col.objects.link(obj)
    for c in list(obj.users_collection):
        if c is not col:
            c.objects.unlink(obj)


def spawn(cid, loc, rot=(0,0,0), p=None, col="CityBlock"):
    """Spawn a MASSA cartridge, position it, move to collection."""
    try:
        fn = getattr(bpy.ops.massa, f"gen_{cid}", None)
        if fn is None:
            _errors.append(f"NOT FOUND: massa.gen_{cid}")
            return None
        kw = dict(p) if p else {}
        fn('EXEC_DEFAULT', **kw)
        obj = bpy.context.active_object
        if obj:
            obj.location = Vector(loc)
            obj.rotation_euler = Euler(rot)
            _move(obj, col)
            _spawned.append(obj.name)
            return obj
        else:
            _errors.append(f"NO ACTIVE OBJ after {cid}")
    except Exception as e:
        _errors.append(f"{cid}: {e}")
    return None


# ============================================================================
# PHASE 0 — SCENE SETUP
# ============================================================================
print("[CityBlock] Phase 0: Scene setup...")

if bpy.context.active_object and bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')

# Root + sub-collections
root = _col("CityBlock", parent=None)
if root.name not in [c.name for c in bpy.context.scene.collection.children]:
    bpy.context.scene.collection.children.link(root)

for sub in ("Ground", "Towers", "Street", "Utilities",
            "Cables", "Rooftop", "Walkways", "Lights"):
    _col(f"CityBlock_{sub}")

# Ground plane  — 36 × 36 m subdivided slab
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=24, y_segments=24, size=18.0)
mesh = bpy.data.meshes.new("CityGround_Mesh")
bm.to_mesh(mesh); bm.free()
gnd = bpy.data.objects.new("CityGround", mesh)
_col("CityBlock_Ground").objects.link(gnd)


# ============================================================================
# PHASE 1 — TOWER CORES  (7 structures)
# ============================================================================
print("[CityBlock] Phase 1: Towers...")

COL_T = "CityBlock_Towers"

# Tower A  NE — Brutalist Block
spawn("building_assembly_3", (7, 7, 0), col=COL_T,
      p={"category":"CONCRETE","style_concrete":"BRUTALIST_A",
         "length":10,"width":8,"height":12,"levels":3,"bay_spacing":3.0})

# Tower B  NW — Inverted Fortress  (tallest)
spawn("building_assembly_3", (-7, 7, 0), col=COL_T,
      p={"category":"CONCRETE","style_concrete":"BRUTALIST_B",
         "length":8,"width":10,"height":16,"levels":4,"bay_spacing":3.5})

# Tower C  SE — Iron-Clad Bunker
spawn("building_assembly_3", (7, -7, 0), col=COL_T,
      p={"category":"STEEL","style_steel":"IRON_CLAD",
         "length":12,"width":8,"height":10,"levels":2})

# Tower D  SW — Column-and-Slab
spawn("building_assembly_3", (-7, -7, 0), col=COL_T,
      p={"category":"CONCRETE","style_concrete":"COLUMN_SLAB",
         "length":10,"width":10,"height":14,"levels":3})

# Infill Shack  NE edge
spawn("building_assembly_1", (2, 13, 0), col=COL_T,
      p={"size":(4,5,3),"has_roof":True,"roof_type":"SHEET"})

# Infill Shack  SW edge
spawn("building_assembly_1", (-3, -13, 0), rot=(0,0,PI/6), col=COL_T,
      p={"size":(3,4,2.5),"has_roof":True,"roof_type":"SCALES"})

# Canopy / Market cover — center street
spawn("struct_canopy", (0, 0, 0), col=COL_T,
      p={"width":6,"depth":4,"height":3,"roof_style":"SLANT"})


# ============================================================================
# PHASE 2 — STREET-LEVEL FURNITURE  (~25 objects)
# ============================================================================
print("[CityBlock] Phase 2: Street furniture...")

COL_S = "CityBlock_Street"

# ---- Sidewalks ----
for x, y, rz in [(3,0,0),(-3,0,0),(0,3,PI/2),(0,-3,PI/2)]:
    spawn("urb_01_sidewalk",(x,y,0),rot=(0,0,rz),col=COL_S,
          p={"length":12,"width":2})

# ---- Barriers ----
for x, y, rz in [(2,5,0),(-2,5,0),(2,-5,0),(-2,-5,0),(4,0,PI/2),(-4,0,PI/2)]:
    spawn("urb_04_barrier",(x,y,0),rot=(0,0,rz),col=COL_S)

# ---- Utility Cabinets ----
for i,(x,y) in enumerate([(-3,4),(3,-4),(-3,-6),(3,6)]):
    spawn("urb_09_utility_cabinet",(x,y,0),col=COL_S,
          p={"style":"TELECOM" if i%2==0 else "ELECTRICAL"})

# ---- Streetlights (CYBERPUNK) ----
for x,y in [(2,8),(-2,8),(2,-8),(-2,-8)]:
    spawn("urb_03_streetlight",(x,y,0),col=COL_S,
          p={"style":"CYBERPUNK"})

# ---- Traffic Lights ----
spawn("urb_14_traffic_light",(3,2,0),col=COL_S)
spawn("urb_14_traffic_light",(-3,-2,0),rot=(0,0,PI),col=COL_S)

# ---- Bollards ----
for x,y in [(1,3),(-1,3),(1,-3),(-1,-3),(3,1),(-3,-1)]:
    spawn("urb_10_bollard",(x,y,0),col=COL_S)

# ---- Fire Hydrants ----
spawn("urb_12_fire_hydrant",(2.5,6,0),col=COL_S)
spawn("urb_12_fire_hydrant",(-2.5,-6,0),col=COL_S)

# ---- Trash / Dumpsters ----
for x,y in [(1,7),(-1,-7),(3,0)]:
    spawn("urb_07_trash_bin",(x,y,0),col=COL_S)
spawn("urb_13_dumpster",(4,10,0),col=COL_S)
spawn("urb_13_dumpster",(-4,-10,0),rot=(0,0,PI/3),col=COL_S)


# ============================================================================
# PHASE 3 — UTILITIES & INDUSTRIAL  (~30 objects)
# ============================================================================
print("[CityBlock] Phase 3: Utilities...")

COL_U = "CityBlock_Utilities"

# ---- HVAC units ----
for x,y,z,rz in [(3,8,5,0),(-3,8,6,PI),(3,-8,4,0),(-3,-8,7,PI)]:
    spawn("asm_01_hvac",(x,y,z),rot=(0,0,rz),col=COL_U)

# ---- Substations ----
spawn("asm_02_substation",(5,3,0),col=COL_U)
spawn("asm_02_substation",(-5,-3,0),rot=(0,0,PI),col=COL_U)

# ---- Ducts  (horizontal wall runs) ----
for x,y,z,rz in [(3,6,4,0),(3,9,3,0),(-3,6,5,PI),
                  (-3,-6,4,PI),(6,3,6,PI/2),(-6,-3,5,PI/2)]:
    spawn("ind_02_duct",(x,y,z),rot=(0,0,rz),col=COL_U,
          p={"length":3.0})

# ---- Pipe junctions ----
for x,y,z,st in [(3,5,4,"T_JOINT"),(-3,5,5,"ELBOW"),
                  (3,-5,3,"CROSS"),(-3,-5,4,"T_JOINT")]:
    spawn("ind_07_pipe_junction",(x,y,z),col=COL_U,p={"style":st})

# ---- Vertical pipes ----
for i in range(6):
    x = 3 if i < 3 else -3
    y = -4 + i * 2.0
    r = 0.10 + random.random()*0.08
    spawn("prim_02_pipe",(x,y,2),rot=(PI/2,0,0),col=COL_U,
          p={"length":4.0,"radius":r})

# ---- Tanks ----
spawn("ind_08_tank",(5,10,0),col=COL_U,
      p={"style":"VERTICAL","radius":1.0,"height":3.0})
spawn("ind_08_tank",(-5,-10,0),col=COL_U,
      p={"style":"HORIZONTAL","radius":0.8,"height":2.5})

# ---- Wall fans ----
for x,y,z,rz in [(3,7,8,0),(-3,-7,7,PI),(7,3,6,-PI/2),(-7,-3,5,PI/2)]:
    spawn("ind_09_fan",(x,y,z),rot=(0,0,rz),col=COL_U,p={"style":"WALL"})

# ---- Valves ----
for x,y,z in [(3,4,4),(-3,4,5),(3,-4,3)]:
    spawn("ind_14_valve",(x,y,z),col=COL_U)

# ---- Generator ----
spawn("ind_10_generator",(5,-5,0),col=COL_U)

# ---- Smoke vents ----
spawn("arc_10_smoke_vent",(7,5,8),rot=(0,0,-PI/2),col=COL_U)
spawn("arc_10_smoke_vent",(-7,-5,10),rot=(0,0,PI/2),col=COL_U)

# ---- Rooftop HVAC ----
for x,y,z in [(7,7,12),(-7,7,16),(-7,-7,14)]:
    spawn("urb_11_hvac",(x,y,z),col=COL_U,
          p={"style":"INDUSTRIAL","fan_count":2})

# ---- Greeble tech panels ----
for x,y,z,rz in [(3.1,7,3,0),(-3.1,7,4,PI),(3.1,-7,2,0),
                  (-3.1,-7,5,PI),(7,3.1,6,-PI/2),(-7,-3.1,4,PI/2)]:
    spawn("prp_03_greeble",(x,y,z),rot=(0,0,rz),col=COL_U,
          p={"size_x":2.0,"size_y":1.5,"density":8,
             "light_chance":0.4,"seed":random.randint(0,999)})


# ============================================================================
# PHASE 4 — CABLE & WIRE NETWORK  (~26 objects)
# ============================================================================
print("[CityBlock] Phase 4: Cables...")

COL_C = "CityBlock_Cables"

# ---- Major cable spans (tower-to-tower) ----
CABLE_SPANS = [
    # East-West across north face  (rotate 90° Z so Y-span → X)
    ((0,  7, 10), (0,0,PI/2), {"length":14,"count":8, "slack":0.8}),
    ((0,  7, 13), (0,0,PI/2), {"length":14,"count":5, "slack":1.2}),
    # East-West across south face
    ((0, -7,  8), (0,0,PI/2), {"length":14,"count":10,"slack":0.6}),
    ((0, -7,  6), (0,0,PI/2), {"length":14,"count":6, "slack":1.0}),
    # North-South along east wall  (default Y orientation)
    ((7,  0,  9), (0,0,0),    {"length":14,"count":7, "slack":0.7}),
    ((7,  0,  6), (0,0,0),    {"length":14,"count":4, "slack":1.5}),
    # North-South along west wall
    ((-7, 0, 11), (0,0,0),    {"length":14,"count":12,"slack":0.5}),
    # Diagonal / short spans
    ((3,  3,  5), (0,0,PI/4), {"length":8, "count":6, "slack":0.4}),
    ((-3,-3,  7), (0,0,PI/4), {"length":8, "count":8, "slack":0.6}),
    # Dense low central span
    ((0,  0,  4), (0,0,0),    {"length":6, "count":15,"slack":0.3}),
    ((2,  5,  3), (0,0,PI/3), {"length":5, "count":10,"slack":0.5}),
    ((-2,-5,  8), (0,0,-PI/3),{"length":5, "count":7, "slack":0.9}),
]
for loc, rot, kw in CABLE_SPANS:
    kw.update({"spread":0.15,"radius":0.015,
               "seed":random.randint(0,9999),"use_ties":True})
    spawn("prop_cables", loc, rot=rot, col=COL_C, p=kw)

# ---- Thick trunk cable runs ----
for loc, rot in [((0,8,5),(0,0,PI/2)),((0,-8,4),(0,0,PI/2)),
                 ((8,0,7),(0,0,0)),((-8,0,9),(0,0,0))]:
    spawn("prop_cables",loc,rot=rot,col=COL_C,
          p={"length":10,"count":20,"slack":0.8,
             "radius":0.03,"spread":0.3,"seed":random.randint(0,9999)})

# ---- Cable trays ----
for x,y,z,rz in [(3,6,3.5,0),(-3,6,4.5,PI),(3,-6,2.5,0),
                  (7,0,5,PI/2),(-7,0,6.5,PI/2),(-3,-6,3.5,PI)]:
    spawn("prim_23_cable_tray",(x,y,z),rot=(0,0,rz),col=COL_C,
          p={"length":4.0})

# ---- Pipe bundles ----
for x,y,z,rz in [(3,5,7,0),(-3,-5,6,PI),(5,3,8,PI/2),(-5,-3,9,PI/2)]:
    spawn("prim_20_bundle",(x,y,z),rot=(0,0,rz),col=COL_C,
          p={"length":3.0,"strand_count":8})


# ============================================================================
# PHASE 5 — ROOFTOP EQUIPMENT  (~12 objects)
# ============================================================================
print("[CityBlock] Phase 5: Rooftop...")

COL_R = "CityBlock_Rooftop"

# Cell Tower  on Tower B  (tallest building, z=16)
spawn("asm_10_tower",(-7,7,16),col=COL_R,
      p={"height":12,"width":1.5,"platforms":3,"taper":0.5})

# Radar Array  on Tower A  (z=12)
spawn("asm_18_radar_array",(7,7,12),col=COL_R,
      p={"dish_diameter":3,"pitch":30,"base_height":1.5})

# Quantum Servers  on Tower D  (z=14, ×2)
spawn("asm_16_quantum_server",(-6,-6,14),col=COL_R,
      p={"width":1.2,"height":2.2,"blade_count":16,"led_density":0.5})
spawn("asm_16_quantum_server",(-8,-6,14),col=COL_R,
      p={"width":1.0,"height":2.0,"blade_count":12,"led_density":0.3})

# Smokestacks
spawn("ind_12_smokestack",(7,-7,10),col=COL_R,
      p={"height":8,"style":"STEEL","has_ladder":True,"radius_base":1.0})
spawn("ind_12_smokestack",(2,13,3),col=COL_R,
      p={"height":5,"style":"BRICK","radius_base":0.6,"radius_top":0.4})

# Industrial Platform  (equipment pad)
spawn("ind_13_platform",(11,5,0),col=COL_R,
      p={"length":4,"width":3,"height":6,"style":"GRATE",
         "railing_type":"INDUSTRIAL"})

# Trusses bridging rooftops
spawn("ind_01_truss",(0,7,14),rot=(0,0,PI/2),col=COL_R,
      p={"length":10})
spawn("ind_01_truss",(7,0,10),col=COL_R,p={"length":8})

# Signage gantries
spawn("asm_08_signage",(0,14,0),col=COL_R)
spawn("asm_08_signage",(-12,0,4),rot=(0,0,PI/2),col=COL_R)

# Crane on Tower B
spawn("ind_11_crane",(-7,10,16),col=COL_R)


# ============================================================================
# PHASE 6 — WALKWAYS & VERTICAL ACCESS  (~16 objects)
# ============================================================================
print("[CityBlock] Phase 6: Walkways...")

COL_W = "CityBlock_Walkways"

# ---- Elevated walkways ----
spawn("walkway",(0,7,8),rot=(0,0,PI/2),col=COL_W,
      p={"w_length":10,"w_width":1.5,"floor_type":"SPLIT",
         "floor_pattern":"GRID","support_type":"CEILING","support_h":4,
         "has_rail":True})

spawn("walkway",(7,0,6),col=COL_W,
      p={"w_length":10,"w_width":1.2,"floor_type":"SPLIT",
         "floor_pattern":"BARS","support_type":"FLOOR","support_h":6,
         "has_rail":True})

spawn("walkway",(0,-7,7),rot=(0,0,PI/2),col=COL_W,
      p={"w_length":12,"w_width":1.5,"floor_type":"SPLIT",
         "floor_pattern":"CHEVRON","support_type":"CEILING","support_h":3,
         "has_rail":True})

# ---- Catwalks ----
spawn("ind_03_catwalk",(3,0,8),col=COL_W,p={"length":4,"width":0.8})
spawn("ind_03_catwalk",(-3,0,10),col=COL_W,p={"length":3,"width":0.8})

# ---- Ladders ----
for x,y,rz in [(3.5,7,0),(-3.5,-7,PI),(7,3.5,-PI/2),(-7,-3.5,PI/2)]:
    spawn("ind_04_ladder",(x,y,0),rot=(0,0,rz),col=COL_W,
          p={"height":8,"has_cage":True})

# ---- Fire escapes ----
spawn("asm_12_fire_escape",(12,7,0),col=COL_W)
spawn("asm_12_fire_escape",(-12,-7,0),rot=(0,0,PI),col=COL_W)

# ---- Scaffolding towers ----
spawn("cart_scaffolding",(13,0,0),col=COL_W,
      p={"width":2,"depth":1,"height":2.5,"floors":4})
spawn("cart_scaffolding",(-13,0,0),col=COL_W,
      p={"width":2,"depth":1,"height":2.0,"floors":3})

# ---- Railings ----
for x,y,rz in [(1,7,PI/2),(-1,7,PI/2),(7,1,0),(7,-1,0)]:
    spawn("urb_02_railing",(x,y,8),rot=(0,0,rz),col=COL_W)


# ============================================================================
# PHASE 7 — LIGHTING, CAMERA & ATMOSPHERE
# ============================================================================
print("[CityBlock] Phase 7: Atmosphere...")

COL_L = "CityBlock_Lights"

# ---- Sun  (low-angle golden hour) ----
sun_d = bpy.data.lights.new("CB_Sun", "SUN")
sun_d.energy = 3.0
sun_d.color = (1.0, 0.85, 0.6)
sun_o = bpy.data.objects.new("CB_Sun", sun_d)
sun_o.rotation_euler = Euler((math.radians(25), math.radians(15), math.radians(-30)))
_col(COL_L).objects.link(sun_o)

# ---- Area lights  (cold blue canyon bounce) ----
for i,(x,y,z) in enumerate([(0,5,6),(0,-5,6),(4,0,5),(-4,0,5)]):
    ad = bpy.data.lights.new(f"CB_Area_{i}", "AREA")
    ad.energy = 200; ad.color = (0.7, 0.8, 1.0); ad.size = 4
    ao = bpy.data.objects.new(f"CB_Area_{i}", ad)
    ao.location = Vector((x,y,z))
    _col(COL_L).objects.link(ao)

# ---- Point lights  (warm streetlight glow) ----
for i,(x,y) in enumerate([(2,8),(-2,8),(2,-8),(-2,-8)]):
    pd = bpy.data.lights.new(f"CB_Point_{i}", "POINT")
    pd.energy = 100; pd.color = (1.0, 0.75, 0.4); pd.shadow_soft_size = 0.5
    po = bpy.data.objects.new(f"CB_Point_{i}", pd)
    po.location = Vector((x,y,5.5))
    _col(COL_L).objects.link(po)

# ---- Spot lights  (harsh security floods) ----
for i,(x,y,z) in enumerate([(7,7,12),(-7,-7,14)]):
    sd = bpy.data.lights.new(f"CB_Spot_{i}", "SPOT")
    sd.energy = 500; sd.color = (0.95, 0.95, 1.0)
    sd.spot_size = math.radians(60); sd.spot_blend = 0.3
    so = bpy.data.objects.new(f"CB_Spot_{i}", sd)
    so.location = Vector((x,y,z))
    so.rotation_euler = Euler((math.radians(60), 0, 0))
    _col(COL_L).objects.link(so)

# ---- Camera  (street-level looking up the canyon) ----
cam_d = bpy.data.cameras.new("CB_Camera")
cam_d.lens = 28; cam_d.clip_end = 500
cam_o = bpy.data.objects.new("CB_Camera", cam_d)
cam_o.location = Vector((0, -20, 2.5))
cam_o.rotation_euler = Euler((math.radians(78), 0, 0))
_col(COL_L).objects.link(cam_o)
bpy.context.scene.camera = cam_o

# ---- World  (dark moody sky) ----
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.02, 0.025, 0.04, 1.0)
bg.inputs["Strength"].default_value = 0.3
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


# ============================================================================
# SUMMARY
# ============================================================================
print(f"[CityBlock] DONE — {len(_spawned)} objects spawned, {len(_errors)} errors")
for e in _errors:
    print(f"  ERROR: {e}")

result = {
    "status": "complete",
    "spawned_count": len(_spawned),
    "error_count": len(_errors),
    "errors": _errors[:30],
    "objects": _spawned[:40],
}
