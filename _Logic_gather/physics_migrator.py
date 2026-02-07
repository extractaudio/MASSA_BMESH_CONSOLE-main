import json
import re
import os

# --- Configuration ---
INPUT_FILE = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\physics.md"
OUTPUT_FILE = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\physics_tag.json"

# --- Templates ---
# detailed defaults for different categories to enrich the data
TEMPLATES = {
    "default": {
        "category": "solid",
        "physical": {"density_kg_m3": 1000, "friction": 0.5, "thermal_cond": 0.2, "specific_heat": 1000},
        "game": {"mass": "medium", "flammability": 0.0, "impact_sound": "solid_impact"},
        "spatial": {"flow": "rigid_solid"}
    },
    "liquid": {
        "category": "liquid",
        "physical": {"density_kg_m3": 1000, "viscosity": 0.001, "thermal_cond": 0.6, "specific_heat": 4180},
        "game": {"mass": "medium", "flammability": 0.0, "impact_sound": "splash_medium"},
        "spatial": {"flow": "gravity_affected"}
    },
    "metal": {
        "category": "metal",
        "physical": {"density_kg_m3": 7800, "thermal_cond": 50, "specific_heat": 400, "conductive": True},
        "game": {"mass": "heavy", "flammability": 0.0, "impact_sound": "metal_clang", "bullet_penetration": "low"},
        "spatial": {"flow": "rigid_solid"}
    },
    "gem": {
        "category": "mineral",
        "semantic_tags": ["gemstone", "precious", "hard", "translucent"],
        "physical": {"density_kg_m3": 3500, "thermal_cond": 10, "specific_heat": 700},
        "game": {"mass": "medium", "flammability": 0.0, "impact_sound": "glass_tink", "value": "high"},
        "spatial": {"flow": "rigid_solid"}
    },
    "wood": {
        "category": "organic",
        "semantic_tags": ["wood", "flammable", "natural"],
        "physical": {"density_kg_m3": 700, "thermal_cond": 0.15, "specific_heat": 1700},
        "game": {"mass": "medium", "flammability": 0.8, "impact_sound": "wood_thud", "bullet_penetration": "medium"},
        "spatial": {"flow": "rigid_solid"}
    },
    "plastic": {
        "category": "synthetic",
        "semantic_tags": ["plastic", "insulator", "moldable"],
        "physical": {"density_kg_m3": 1200, "thermal_cond": 0.2, "specific_heat": 1500},
        "game": {"mass": "light", "flammability": 0.6, "impact_sound": "plastic_clatter"},
        "spatial": {"flow": "rigid_solid"}
    },
    "fabric": {
        "category": "textile",
        "semantic_tags": ["fabric", "soft", "flammable"],
        "physical": {"density_kg_m3": 1500, "thermal_cond": 0.04, "specific_heat": 1300},
        "game": {"mass": "light", "flammability": 0.9, "impact_sound": "cloth_rustle", "collision": "soft"},
        "spatial": {"flow": "flexible_sheet"}
    },
    "stone": {
        "category": "mineral",
        "semantic_tags": ["stone", "heavy", "rough"],
        "physical": {"density_kg_m3": 2500, "thermal_cond": 2.0, "specific_heat": 800},
        "game": {"mass": "heavy", "flammability": 0.0, "impact_sound": "stone_thud"},
        "spatial": {"flow": "rigid_solid"}
    },
    "glass": {
        "category": "mineral",
        "semantic_tags": ["glass", "transparent", "brittle"],
        "physical": {"density_kg_m3": 2500, "thermal_cond": 1.0, "specific_heat": 840},
        "game": {"mass": "medium", "flammability": 0.0, "impact_sound": "glass_shatter", "fragility": "high"},
        "spatial": {"flow": "rigid_solid"}
    },
    "food": {
        "category": "organic",
        "semantic_tags": ["food", "perishable", "soft"],
        "physical": {"density_kg_m3": 1100, "thermal_cond": 0.5, "specific_heat": 3500},
        "game": {"mass": "medium", "flammability": 0.3, "impact_sound": "organic_squish"},
        "spatial": {"flow": "deformable"}
    },
    "gas": {
        "category": "gas",
        "physical": {"density_kg_m3": 1.2, "viscosity": 0.000018, "thermal_cond": 0.024},
        "game": {"mass": "light", "flammability": 0.0},
        "spatial": {"flow": "gas_expansion"}
    }
}

# --- Keyword Matchers ---
# Heuristics to assign templates based on material name
KEYWORD_MAP = [
    (r"(?i)water|milk|honey|oil|beer|wine|blood|seawater|juice|fuel|gasoline|diesel|fluid|ink|dye|bleach|ammonia|soap|shampoo|liquid", "liquid"),
    (r"(?i)gold|silver|copper|iron|aluminum|steel|brass|bronze|chrome|platinum|titanium|zinc|nickel|cobalt|pewter|solder|lead|tin|tungsten|mercury|gallium|metal", "metal"),
    (r"(?i)diamond|ruby|sapphire|emerald|opal|amethyst|quartz|jade|obsidian|turquoise|topaz|amber|malachite|garnet|peridot|spinel|zircon|tanzanite|moonstone|lapis|crystal", "gem"),
    (r"(?i)wood|bamboo|cork|plywood|bark|mahogany|oak|pine|walnut|ebony|balsa|birch", "wood"),
    (r"(?i)plastic|pvc|acrylic|nylon|teflon|poly|abs|vinyl|silicone|resin|epoxy|styrofoam|rubber|bakelite|formica|kevlar", "plastic"),
    (r"(?i)cotton|silk|wool|velvet|denim|leather|suede|satin|linen|polyester|fur|hair|canvas|chiffon|organza|tulle|spandex|lycra|cloth|fabric|felt", "fabric"),
    (r"(?i)stone|rock|concrete|brick|asphalt|marble|granite|slate|travertine|terracotta|ceramic|porcelain|plaster|sand|soil|clay|mud|peat|gravel", "stone"),
    (r"(?i)glass|mirror", "glass"),
    (r"(?i)apple|banana|orange|strawberry|chocolate|butter|cheese|bread|meat|egg|bone|enamel", "food"),
    (r"(?i)air|oxygen|nitrogen|steam|smoke|helium|hydrogen", "gas")
]

def resolve_template(name):
    for pattern, template_key in KEYWORD_MAP:
        if re.search(pattern, name):
            # Special logic: Mercury is a liquid metal
            if "mercury" in name.lower() or "gallium" in name.lower():
                # We can merge templates or just prefer one. Let's return a hybrid key we handle later, 
                # or just 'liquid' with metal tags. For simplicity, let's stick to the first match logic.
                if template_key == "metal": # If it matched metal first
                     if "mercury" in name.lower() or "gallium" in name.lower():
                         return TEMPLATES["liquid"] # Override for liquid metals to behave like liquids physically
            return TEMPLATES[template_key]
    return TEMPLATES["default"]

def parse_val_range(val_str):
    """Parses '0.2 - 0.5' or '0.5' into a float or list of floats."""
    val_str = val_str.replace("~", "").strip()
    # Remove text comments like '(Ref)'
    val_str = re.sub(r'\(.*?\)', '', val_str).strip()
    
    if "-" in val_str:
        try:
            parts = [float(x.strip()) for x in val_str.split("-") if x.strip()]
            if len(parts) == 2:
                return parts
            return parts[0] if parts else 0.0
        except ValueError:
            return 0.0
    else:
        try:
            # Handle cases like '> 0.95'
            val_str = val_str.replace(">", "").strip()
            return float(val_str)
        except ValueError:
            return 0.0

def parse_color(color_str):
    """Parses hex or approx RGB from string."""
    # Try to find hex
    hex_match = re.search(r'#[0-9a-fA-F]{6}', color_str)
    if hex_match:
        return hex_match.group(0)
    
    # Try to find RGB values
    rgb_match = re.search(r'RGB:?\s*(\d+),\s*(\d+),\s*(\d+)', color_str)
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        # Convert to hex
        return "#{:02x}{:02x}{:02x}".format(r, g, b).upper()
        
    return None # Fallback or keep generic

def normalize_rgb(hex_color):
    if not hex_color: return [0.8, 0.8, 0.8]
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)]

def main():
    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    material_classes = []
    
    # Skip header lines (usually first 4 lines in standard markdown tables)
    # Finding the separator line |---|---|
    start_index = 0
    for i, line in enumerate(lines):
        if "|---" in line:
            start_index = i + 1
            break
            
    count = 0
    for i in range(start_index, len(lines)):
        line = lines[i].strip()
        if not line or not line.startswith("|"): continue
        
        # Parse table columns
        # | Material | IOR | Albedo | Roughness | Type |
        cols = [c.strip() for c in line.split('|')]
        # cols[0] is empty (before first |), cols[1] is Material, etc.
        if len(cols) < 6: continue
        
        raw_name = cols[1]
        raw_ior = cols[2]
        raw_albedo = cols[3]
        raw_roughness = cols[4]
        raw_type = cols[5]
        
        # Resolution
        template = resolve_template(raw_name)
        
        # ID generation
        count += 1
        class_id = f"phys_{count:03d}"
        
        # Parsed Data
        ior_val = parse_val_range(raw_ior)
        if isinstance(ior_val, list): ior_val = sum(ior_val)/len(ior_val) # avg for single field
        
        roughness_val = parse_val_range(raw_roughness)
        # Ensure roughness is a range format [min, max] if strictly required, or float. 
        # The schema uses range [0.0, 0.1]. 
        if isinstance(roughness_val, float):
            roughness_range = [max(0.0, roughness_val - 0.05), min(1.0, roughness_val + 0.05)]
        else:
            roughness_range = roughness_val

        hex_color = parse_color(raw_albedo)
        if not hex_color:
            # Generate dummy hex based on category? or simple grey
            hex_color = "#CCCCCC"
            
        rgb_color = normalize_rgb(hex_color)

        # Structuring
        entry = {
            "class_id": class_id,
            "material_name": raw_name,
            "category": template["category"],
            "semantic_tags": template.get("semantic_tags", []) + [raw_type.lower().replace(" ", "_")],
            "optical_properties": {
                "index_of_refraction": ior_val,
                "transmission": 1.0 if "transmission" in raw_albedo.lower() or template["category"] in ["liquid", "gas", "gem"] else 0.0,
                "roughness_range": roughness_range,
                "subsurface_scattering": {
                    "radius_mm": [10, 10, 10], 
                    "scale": 0.1, 
                    "color": rgb_color # SSS matches base for now
                },
                "absorption_coefficient": 0.1,
                "scattering_coefficient": 0.1
            },
            "physical_properties": {
                "density_kg_m3": template["physical"]["density_kg_m3"],
                "viscosity_pas": template["physical"].get("viscosity", 1000000), # solid default
                "specific_heat_j_kgk": template["physical"]["specific_heat"],
                "thermal_conductivity_w_mk": template["physical"]["thermal_cond"],
                "melting_point_k": 300, # Dummy default
                "boiling_point_k": 500, # Dummy default
                "speed_of_sound_m_s": 3000 # Solid default
            },
            "game_attributes": {
                "mass_category": template["game"]["mass"],
                "buoyancy_factor": 1000.0 / template["physical"]["density_kg_m3"], # approx vs water
                "friction_coefficient": {"static": 0.5, "dynamic": 0.3, "rolling": 0.1},
                "collision_response": template["game"].get("collision", "rigid"),
                "damage_resistance": 0.5,
                "flammability": template["game"]["flammability"],
                "electrical_conductivity": 1.0 if template["physical"].get("conductive") else 0.0,
                "audio_properties": {
                    "footstep_sound": template["game"].get("impact_sound", "generic_step"),
                    "impact_sound": template["game"].get("impact_sound", "generic_impact"),
                    "continuous_sound": "none"
                },
                "interaction_flags": ["solid"]
            },
            "visual_properties": {
                "albedo_hex": hex_color,
                "albedo_rgb": rgb_color,
                "specular": 0.5,
                "metallic": 1.0 if template["category"] == "metal" else 0.0,
                "emissive": 0.0,
                "translucency": 0.0,
                "opacity": 1.0
            },
            "blender_shader": {
                "principled_bsdf_v2": {
                    "base_color": rgb_color + [1.0],
                    "metallic": 1.0 if template["category"] == "metal" else 0.0,
                    "roughness": roughness_range[0],
                    "ior": ior_val
                },
                 "node_group": "standard_surface",
                 "render_settings": {"sample_count": 128}
            },
             "real_world_context": {
                "typical_uses": ["construction", "crafting"],
                "rarity": "common",
                "cost_per_m3": 100.0
            },
            "spatial_reasoning": {
                "flow_characteristics": template["spatial"]["flow"]
            }
        }
        
        # Specific override for Water/Liquids to match the high quality manual ones if possible?
        # For now, this script REPLACES the manual file. 
        # A better approach (future) would be to merge. 
        # But per user instruction: "Generate the full... in one go".
        
        material_classes.append(entry)

    final_json = {
        "schema_version": "2.0",
        "knowledge_type": "physical_properties",
        "material_classes": material_classes
    }
    
    print(f"Generated {len(material_classes)} materials.")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=2)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
