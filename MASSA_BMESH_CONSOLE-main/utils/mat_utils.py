import bpy
import os
import random

LIBRARY_FILENAME = "massa_library.blend"
_CACHED_MAT_NAMES = []

# ==============================================================================
# 1. DATABASE: The Source of Truth
# ==============================================================================

UV_MAP_ITEMS = [
    ("BOX", "Box (Tri-Planar)", "Standard Cube Mapping"),
    ("FIT", "Fit (Stretch)", "Stretch to 0-1 Bounds"),
    ("TUBE_Z", "Tube Z (Vertical)", "Cylindrical Z-Axis"),
    ("TUBE_Y", "Tube Y (Length)", "Cylindrical Y-Axis"),
    ("TUBE_X", "Tube X (Width)", "Cylindrical X-Axis"),
    ("UNWRAP", "Unwrap (LSCM)", "Trust Seams & Unwrap (Post-Process)"),
    ("SKIP", "Manual / Skip", "Use Cartridge Default"),
]

# THE UNIFIED MATERIAL DATABASE
MASTER_MAT_DB = {
    # --- A. VISUAL DEBUG SLOTS (The "Solid List") ---
    "MASSA_DEBUG_0": {"name": "Slot_00_Grey",   "col": (0.5, 0.5, 0.5), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_1": {"name": "Slot_01_Red",    "col": (0.8, 0.05, 0.05), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_2": {"name": "Slot_02_Green",  "col": (0.1, 0.8, 0.1), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_3": {"name": "Slot_03_Blue",   "col": (0.1, 0.1, 0.8), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_4": {"name": "Slot_04_Yellow", "col": (0.8, 0.8, 0.1), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_5": {"name": "Slot_05_Cyan",   "col": (0.1, 0.8, 0.8), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_6": {"name": "Slot_06_Mag",    "col": (0.8, 0.1, 0.8), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_7": {"name": "Slot_07_Orange", "col": (0.8, 0.4, 0.1), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_8": {"name": "Slot_08_Purple", "col": (0.4, 0.1, 0.8), "dens": 1000, "rough": 0.5},
    "MASSA_DEBUG_9": {"name": "Slot_09_Black",  "col": (0.05, 0.05, 0.05), "dens": 1000, "rough": 0.5},

    # --- B. PHYSICAL MATERIALS ---
    "CONCRETE_RAW":   {"name": "Concrete Raw",      "col": (0.5, 0.5, 0.5),   "dens": 2400, "rough": 0.9},
    "CONCRETE_POL":   {"name": "Concrete Polished", "col": (0.6, 0.6, 0.65),  "dens": 2400, "rough": 0.2},
    "CONCRETE_BLOCK": {"name": "Concrete Block",    "col": (0.45, 0.45, 0.45),"dens": 2100, "rough": 1.0},
    "METAL_STEEL":    {"name": "Metal Steel",       "col": (0.2, 0.2, 0.25),  "dens": 7850, "rough": 0.4, "meta": 1.0},
    "METAL_ALUMINUM": {"name": "Metal Aluminum",    "col": (0.8, 0.85, 0.9),  "dens": 2700, "rough": 0.3, "meta": 1.0},
    "METAL_IRON":     {"name": "Metal Iron",        "col": (0.1, 0.1, 0.1),   "dens": 7870, "rough": 0.7, "meta": 1.0},
    "METAL_RUST":     {"name": "Metal Rust",        "col": (0.4, 0.15, 0.1),  "dens": 7800, "rough": 1.0, "meta": 0.0},
    "WOOD_OAK":       {"name": "Wood Oak",          "col": (0.6, 0.4, 0.2),   "dens": 750,  "rough": 0.6},
    "WOOD_PINE":      {"name": "Wood Pine",         "col": (0.8, 0.7, 0.5),   "dens": 500,  "rough": 0.5},
    "WOOD_PAINTED":   {"name": "Wood Painted",      "col": (0.9, 0.9, 0.9),   "dens": 600,  "rough": 0.2},
    "WOOD_ROUGH":     {"name": "Wood Rough",        "col": (0.5, 0.4, 0.3),   "dens": 650,  "rough": 0.9},
    "SYNTH_PLASTIC":  {"name": "Plastic Grey",      "col": (0.2, 0.2, 0.2),   "dens": 950,  "rough": 0.3},
    "SYNTH_RUBBER":   {"name": "Rubber Black",      "col": (0.05, 0.05, 0.05),"dens": 1100, "rough": 0.8},
    "SYNTH_GLASS":    {"name": "Glass Basic",       "col": (0.8, 0.9, 1.0),   "dens": 2500, "rough": 0.0, "trans": 1.0},
    "CERAMIC_TILE":   {"name": "Ceramic Tile",      "col": (0.9, 0.85, 0.8),  "dens": 2000, "rough": 0.1},
    "FABRIC_CANVAS":  {"name": "Fabric Canvas",     "col": (0.7, 0.65, 0.6),  "dens": 1500, "rough": 1.0},
    "GENERIC":        {"name": "Generic",           "col": (0.5, 0.5, 0.5),   "dens": 1000, "rough": 0.5},
}

PHYS_ID_MAP = {k: i + 1 for i, k in enumerate(sorted(MASTER_MAT_DB.keys()))}


def get_density(phys_key):
    return MASTER_MAT_DB.get(phys_key, MASTER_MAT_DB["GENERIC"])["dens"]


def get_visual_name_from_id(phys_id):
    """Translates Physics ID (Key) to Material Name (Value)."""
    if phys_id in MASTER_MAT_DB:
        return MASTER_MAT_DB[phys_id]["name"]
    return MASTER_MAT_DB["GENERIC"]["name"]


# ==============================================================================
# 2. CORE LOGIC
# ==============================================================================

def ensure_default_library():
    """Forces creation of all standard materials."""
    for key, data in MASTER_MAT_DB.items():
        _create_simple_mat(data)
    
    ensure_gn_viz_materials()


def _create_simple_mat(data):
    name = data["name"]
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        mat.node_tree.nodes.clear()
        out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    c = data.get("col", (0.5, 0.5, 0.5))
    if len(c) == 3:
        c = (*c, 1.0)
    
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Roughness"].default_value = data.get("rough", 0.5)
    bsdf.inputs["Metallic"].default_value = data.get("meta", 0.0)
    if "trans" in data:
        bsdf.inputs["Transmission Weight"].default_value = data["trans"]
    
    # Viewport Color
    mat.diffuse_color = c
    return mat


def load_material_by_name(name):
    """Compatible alias for smart loader."""
    return load_material_smart(name)


def load_material_smart(name_or_key):
    """
    The Ultimate Loader. Accepts Key (METAL_STEEL) or Name (Metal Steel).
    Autofills if missing.
    """
    if not name_or_key or name_or_key == "NONE":
        return None

    # 1. Try Direct Name
    mat = bpy.data.materials.get(name_or_key)
    if mat: return mat
    
    # 2. Try Key -> Name
    if name_or_key in MASTER_MAT_DB:
        return _create_simple_mat(MASTER_MAT_DB[name_or_key])
    
    # 3. Try Reverse Name -> Key (in case of mismatch)
    for k, v in MASTER_MAT_DB.items():
        if v["name"] == name_or_key:
            return _create_simple_mat(v)

    return None


def get_debug_mat_name(index):
    """Returns the name for a slot index (0-9)."""
    key = f"MASSA_DEBUG_{index}"
    if key in MASTER_MAT_DB:
        return MASTER_MAT_DB[key]["name"]
    return MASTER_MAT_DB["MASSA_DEBUG_0"]["name"]


def get_or_create_placeholder_material():
    name = "Massa_Placeholder"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (1, 0, 1, 1) 
    return mat


# ==============================================================================
# 3. UI PROVIDERS
# ==============================================================================

def get_phys_items(self, context):
    items = []
    for k in sorted(MASTER_MAT_DB.keys()):
        if not k.startswith("MASSA_DEBUG"):
            items.append((k, MASTER_MAT_DB[k]["name"], f"Data: {k}"))
    return items


def get_material_items(self, context):
    global _CACHED_MAT_NAMES
    items = [("NONE", "None / Default", "Use Slot Default")]
    
    # 1. Debugs (Top)
    for i in range(10):
        k = f"MASSA_DEBUG_{i}"
        name = MASTER_MAT_DB[k]["name"]
        items.append((name, f"Debug {i} ({name})", "High contrast debug material"))
        
    # 2. Physicals
    for k, v in sorted(MASTER_MAT_DB.items()):
        if not k.startswith("MASSA_DEBUG"):
            items.append((v["name"], v["name"], "Standard Library"))
            
    # 3. Scene Materials
    known = {i[0] for i in items}
    for m in bpy.data.materials:
        if m.name not in known:
            items.append((m.name, m.name, "Scene Material"))
            
    return items


# ==============================================================================
# 4. GN VIZ & OVERRIDES
# ==============================================================================

def ensure_gn_viz_materials():
    """Generates the Viz Materials (1-4 + Seam)."""
    colors = [
        ("Massa_Viz_Edge_1", (1.0, 0.8, 0.0)), # Yellow
        ("Massa_Viz_Edge_2", (0.0, 0.4, 1.0)), # Blue
        ("Massa_Viz_Edge_3", (1.0, 0.1, 0.1)), # Red
        ("Massa_Viz_Edge_4", (0.1, 0.9, 0.1)), # Green
        ("Massa_Viz_Edge_5", (1.0, 0.0, 1.0)), # Magenta (SEAMS)
    ]
    for name, col in colors:
        if name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=name)
            mat.diffuse_color = (*col, 1.0)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*col, 1.0)
                bsdf.inputs["Emission Color"].default_value = (*col, 1.0)
                bsdf.inputs["Emission Strength"].default_value = 2.0


def get_or_create_viz_vertex_material():
    name = "Massa_Viz_VertCol"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name="Massa_Viz_Color"
    nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# --- DEBUG SHADERS ---

def create_debug_uv_material():
    name = "Massa_Debug_UV"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location=(300,0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location=(0,0); bsdf.inputs["Roughness"].default_value=0.9
    checker = nt.nodes.new("ShaderNodeTexChecker"); checker.location=(-300,0); checker.inputs["Scale"].default_value=24.0
    checker.inputs["Color1"].default_value=(0.1,0.1,0.1,1.0); checker.inputs["Color2"].default_value=(0.8,0.8,0.8,1.0)
    uv_map = nt.nodes.new("ShaderNodeTexCoord"); uv_map.location=(-500,0)
    nt.links.new(uv_map.outputs["UV"], checker.inputs["Vector"])
    nt.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_debug_neutral_material():
    name = "Massa_Debug_Neutral"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.diffuse_color=(0.2,0.2,0.2,1.0); mat.use_nodes=True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf: bsdf.inputs["Base Color"].default_value=(0.2,0.2,0.2,1.0); bsdf.inputs["Roughness"].default_value=0.8
    return mat

def create_debug_channel_material(channel_idx):
    name = f"Massa_Debug_Chan_{channel_idx}"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emission = nt.nodes.new("ShaderNodeEmission")
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name="Massa_Surface"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(attr.outputs["Color"], sep.inputs["Color"])
    target_out = ["Red", "Green", "Blue"][channel_idx] if channel_idx < 3 else "Alpha"
    nt.links.new(sep.outputs[target_out], emission.inputs["Color"])
    nt.links.new(emission.outputs["Emission"], out.inputs["Surface"])
    return mat

def create_debug_physics_material():
    name = "Massa_Debug_Phys"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_type="GEOMETRY"; attr.attribute_name="massa_phys_id"
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation="CONSTANT"
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    step = 1.0 / len(MASTER_MAT_DB)
    for i, (k, v) in enumerate(sorted(MASTER_MAT_DB.items())):
        pos = (i + 1) * step
        if i == 0: el = ramp.color_ramp.elements[0]; el.position = 0.0
        else: el = ramp.color_ramp.elements.new(pos)
        el.color = (*v["col"], 1.0)
    math_node = nt.nodes.new("ShaderNodeMath"); math_node.operation="DIVIDE"; math_node.inputs[1].default_value=len(MASTER_MAT_DB)
    nt.links.new(attr.outputs["Fac"], math_node.inputs[0])
    nt.links.new(math_node.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_debug_part_id_material():
    name = "Massa_Debug_PartID"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_type="GEOMETRY"; attr.attribute_name="massa_part_id"
    white_noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(attr.outputs["Fac"], comb.inputs["X"])
    nt.links.new(comb.outputs["Vector"], white_noise.inputs["Vector"])
    nt.links.new(white_noise.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_debug_protect_material():
    name = "Massa_Debug_Protect"
    if name in bpy.data.materials: return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name); mat.use_nodes=True; nt=mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name="massa_protect"
    mix = nt.nodes.new("ShaderNodeMixShader")
    s_prot = nt.nodes.new("ShaderNodeEmission"); s_prot.inputs["Color"].default_value=(1,0,0,1)
    s_unprot = nt.nodes.new("ShaderNodeBsdfPrincipled"); s_unprot.inputs["Base Color"].default_value=(0.1,0.1,0.1,1)
    nt.links.new(attr.outputs["Fac"], mix.inputs["Fac"])
    nt.links.new(s_unprot.outputs["BSDF"], mix.inputs[1])
    nt.links.new(s_prot.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat