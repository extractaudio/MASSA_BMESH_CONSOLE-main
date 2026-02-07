import json
import os
import shutil
import random

SOURCE_FILE = 'object_logic_source.json' # Read from the safe source
TARGET_FILE = 'object_logic.json'
BACKUP_FILE = 'object_logic_backup.json'
TARGET_SCHEMA_VERSION = "1.0"

# Heuristic Rules for Categories
CATEGORY_RULES = {
    "lamp": {
        "semantic_category": ["lighting", "functional", "decorative"],
        "functional_relationships": {
            "illuminates": ["reading_chair", "bed", "workspace"],
            "power_source_proximity": 2.0,
            "typical_grouping": ["nightstand", "side_table"]
        },
        "spatial_constraints": {"height_range_m": [0.3, 1.8], "visual_balance": {"visual_weight": 0.2}},
        "blender_auto_placement": {"algorithm": "surface_snap_with_clearance", "rotation_constraint": "random_360"}
    },
    "table": {
        "semantic_category": ["furniture", "surface", "wooden"],
        "functional_relationships": {
            "supports": ["lamp", "book", "plant", "decorative_bowl"],
            "typical_grouping": ["chair", "sofa", "rug"]
        },
        "spatial_constraints": {"height_range_m": [0.4, 0.8], "distance_from_edge_m": 0.0, "visual_balance": {"visual_weight": 0.6}},
        "blender_auto_placement": {"algorithm": "box_pack_floor", "rotation_constraint": "align_to_wall_or_center"}
    },
    "chair": {
        "semantic_category": ["furniture", "seating", "comfort"],
        "functional_relationships": {
            "faces": ["table", "desk", "tv"],
            "typical_grouping": ["table", "desk"]
        },
        "spatial_constraints": {"height_range_m": [0.4, 1.0], "visual_balance": {"visual_weight": 0.4}},
        "blender_auto_placement": {"algorithm": "floor_flocking", "rotation_constraint": "face_nearest_surface"}
    },
    "sofa": {
        "semantic_category": ["furniture", "seating", "large", "comfort"],
        "functional_relationships": {
            "faces": ["tv", "fireplace", "coffee_table"],
            "typical_grouping": ["coffee_table", "armchair", "rug"]
        },
        "spatial_constraints": {"height_range_m": [0.7, 1.0], "visual_balance": {"visual_weight": 0.9}},
        "blender_auto_placement": {"algorithm": "wall_snap_or_center", "rotation_constraint": "align_to_wall_normal"}
    },
    "bed": {
        "semantic_category": ["furniture", "sleeping", "large", "comfort"],
        "functional_relationships": {
            "faces": ["wardrobe", "window"],
            "typical_grouping": ["nightstand", "lamp", "rug"]
        },
        "spatial_constraints": {"height_range_m": [0.5, 1.2], "visual_balance": {"visual_weight": 0.9}},
        "blender_auto_placement": {"algorithm": "wall_snap_headboard", "rotation_constraint": "align_to_wall_normal"}
    },
    "storage": { # dresser, wardrobe, shelf
        "semantic_category": ["furniture", "storage", "wooden"],
        "functional_relationships": {
            "stores": ["clothes", "books", "items"],
            "typical_grouping": ["bed", "desk"]
        },
        "spatial_constraints": {"height_range_m": [0.8, 2.2], "visual_balance": {"visual_weight": 0.7}},
        "blender_auto_placement": {"algorithm": "wall_snap_back", "rotation_constraint": "align_to_wall_normal"}
    },
     "appliance": { # fridge, stove, washer
        "semantic_category": ["appliance", "functional", "metal", "kitchen_utility"],
        "functional_relationships": {
            "power_source_proximity": 1.0,
            "typical_grouping": ["kitchen_cabinet", "counter"]
        },
        "spatial_constraints": {"height_range_m": [0.8, 1.8], "visual_balance": {"visual_weight": 0.8}},
        "blender_auto_placement": {"algorithm": "wall_snap_back", "rotation_constraint": "align_to_wall_normal"}
    },
    "electronics": { # tv, computer, console
        "semantic_category": ["electronics", "entertainment", "fragile"],
        "functional_relationships": {
            "power_source_proximity": 1.5,
            "requires_surface": True
        },
        "spatial_constraints": {"height_range_m": [0.3, 0.8], "visual_balance": {"visual_weight": 0.4}},
        "blender_auto_placement": {"algorithm": "surface_snap_center", "rotation_constraint": "face_user"}
    },
    "decor": { # rug, painting, plant, mirror
        "semantic_category": ["decorative", "aesthetic"],
        "functional_relationships": {
            "enhances": ["room_ambiance"],
            "typical_grouping": ["furniture_group"]
        },
         "spatial_constraints": {"visual_balance": {"visual_weight": 0.3}},
         "blender_auto_placement": {"algorithm": "surface_scatter", "rotation_constraint": "random_180"}
    },
     "kitchen_item": { # toaster, blender, utensils
        "semantic_category": ["kitchenware", "accessory", "functional"],
        "functional_relationships": {
             "stored_on": ["counter", "shelf"],
             "typical_grouping": ["kitchen_appliance"]
        },
        "spatial_constraints": {"height_range_m": [0.1, 0.4], "visual_balance": {"visual_weight": 0.1}},
        "blender_auto_placement": {"algorithm": "surface_snap_grid", "rotation_constraint": "random_360"}
    },
     "bathroom": { # toilet, sink, shower
        "semantic_category": ["bathroom", "fixture", "ceramic"],
         "functional_relationships": {
             "plumbing_required": True
         },
         "spatial_constraints": {"height_range_m": [0.4, 2.0], "visual_balance": {"visual_weight": 0.6}},
         "blender_auto_placement": {"algorithm": "wall_snap_back", "rotation_constraint": "align_to_wall_normal"}
    }
}

# Mapping specific keywords to general categories. 
# ORDER MATTERS: Specific compound words should come before general words.
KEYWORD_MAPPINGS_LIST = [
    ("stand mixer", "kitchen_item"),
    ("coffee maker", "kitchen_item"),
    ("rice cooker", "kitchen_item"),
    ("slow cooker", "kitchen_item"),
    ("air fryer", "kitchen_item"),
    ("deep fryer", "kitchen_item"),
    ("pressure cooker", "kitchen_item"),
    ("food processor", "kitchen_item"),
    ("waffle maker", "kitchen_item"),
    ("ice cream maker", "kitchen_item"),
    ("bread maker", "kitchen_item"),
    ("espresso machine", "kitchen_item"),
    ("soda stream", "kitchen_item"),
    ("can opener", "kitchen_item"),
    ("knife block", "kitchen_item"),
    ("paper towel", "kitchen_item"),
    ("fruit bowl", "kitchen_item"),
    ("bread box", "kitchen_item"),
    ("dish rack", "kitchen_item"),
    ("spice rack", "kitchen_item"),
    ("napkin holder", "kitchen_item"),
    ("cutting board", "kitchen_item"),
    ("mixing bowl", "kitchen_item"),
    ("baking sheet", "kitchen_item"),
    ("muffin tin", "kitchen_item"),
    ("cake pan", "kitchen_item"),
    ("pie dish", "kitchen_item"),
    ("casserole dish", "kitchen_item"),
    ("frying pan", "kitchen_item"),
    ("rolling pin", "kitchen_item"),
    ("salad spinner", "kitchen_item"),
    
    # Lighting
    ("lamp", "lamp"),
    ("light", "lamp"),
    ("sconce", "lamp"),
    ("chandelier", "lamp"),
    
    # Furniture - Seating
    ("armchair", "chair"),
    ("chair", "chair"),
    ("stool", "chair"),
    ("bench", "chair"),
    ("sofa", "sofa"),
    ("couch", "sofa"),
    ("loveseat", "sofa"),
    
    # Furniture - Sleeping
    ("bed", "bed"),
    ("crib", "bed"),
    ("cot", "bed"),
    
    # Furniture - Storage
    ("bookshelf", "storage"),
    ("shelf", "storage"),
    ("dresser", "storage"),
    ("wardrobe", "storage"),
    ("cabinet", "storage"),
    ("chest", "storage"),
    ("bookcase", "storage"),
    ("credenza", "storage"),
    ("sideboard", "storage"),
    ("buffet", "storage"),
    ("pantry", "storage"),
    
    # Furniture - Surfaces (Check these after specific items like 'stand mixer')
    ("nightstand", "table"),
    ("coffee table", "table"),
    ("end table", "table"),
    ("dining table", "table"),
    ("side table", "table"),
    ("console table", "table"),
    ("desk", "table"),
    ("table", "table"),
    ("stand", "table"), # tv stand, plant stand, but NOT stand mixer (handled above)
    
    # Appliances
    ("fridge", "appliance"),
    ("refrigerator", "appliance"),
    ("stove", "appliance"),
    ("oven", "appliance"),
    ("microwave", "appliance"),
    ("washing machine", "appliance"),
    ("washer", "appliance"),
    ("dryer", "appliance"),
    ("dishwasher", "appliance"),
    ("freezer", "appliance"),
    ("range", "appliance"),
    
    # Electronics
    ("tv", "electronics"),
    ("television", "electronics"),
    ("computer", "electronics"),
    ("pc", "electronics"),
    ("laptop", "electronics"),
    ("monitor", "electronics"),
    ("console", "electronics"),
    ("speaker", "electronics"),
    ("tablet", "electronics"),
    ("printer", "electronics"),
    ("router", "electronics"),
    
    # Decor
    ("rug", "decor"),
    ("carpet", "decor"),
    ("painting", "decor"),
    ("poster", "decor"),
    ("picture", "decor"),
    ("art", "decor"),
    ("mirror", "decor"),
    ("plant", "decor"),
    ("vase", "decor"),
    ("clock", "decor"),
    ("curtains", "decor"),
    ("drapes", "decor"),
    ("blinds", "decor"),
    ("cushion", "decor"),
    ("pillow", "decor"),
    ("sculpture", "decor"),
    ("figurine", "decor"),
    ("candle", "decor"),
    ("basket", "decor"),
    ("trash can", "decor"),
    ("bin", "decor"),
    
    # Bathroom
    ("toilet", "bathroom"),
    ("sink", "bathroom"),
    ("shower", "bathroom"),
    ("bathtub", "bathroom"),
    ("bath", "bathroom"),
    ("vanity", "bathroom"),
    ("towel", "bathroom"),
]


def determine_category(name):
    name_lower = name.lower()
    
    # Iterate through ordered list
    for keyword, category in KEYWORD_MAPPINGS_LIST:
        if keyword in name_lower:
            return category
    
    # Fallback heuristics
    if "rack" in name_lower or "holder" in name_lower:
        return "kitchen_item"
    if "maker" in name_lower or "mixer" in name_lower or "blender" in name_lower: 
        return "kitchen_item"
    if "cooker" in name_lower or "fryer" in name_lower or "processor" in name_lower:
        return "kitchen_item"
    
    return "decor" # Default to decor if unknown

# ... (previous code) ...

def resolve_placement(name, category_key, old_placement):
    name_lower = name.lower()
    
    # strong overrides based on name
    if "floor" in name_lower: return "floor"
    if "wall" in name_lower: return "wall"
    if "ceiling" in name_lower: return "ceiling"
    if "rug" in name_lower or "carpet" in name_lower: return "floor"
    if "curtain" in name_lower or "blind" in name_lower: return "wall"
    
    # Category overrides
    if category_key == "kitchen_item": return "surface"
    if category_key == "table": return "floor"
    if category_key == "chair": return "floor"
    if category_key == "sofa": return "floor"
    if category_key == "bed": return "floor"
    if category_key == "storage": 
        # Shelves/Cabinets can be wall, but mostly floor furniture
        if "shelf" in name_lower and "book" not in name_lower: return "wall" # Wall shelf
        return "floor"
    
    if category_key == "appliance":
        if "microwave" in name_lower: return "surface"
        return "floor" # Fridge, Stove
        
    if category_key == "electronics":
        if "tv" in name_lower and "stand" in name_lower: return "surface" # Stand TV
        return "surface" # Default for laptops, consoles
        
    if category_key == "lamp":
        if "table" in name_lower: return "surface"
        return "surface" # Default
        
    if category_key == "bathroom":
        if "toilet" in name_lower or "shower" in name_lower or "bath" in name_lower: return "floor"
        if "sink" in name_lower: return "surface" # Sink implies counter? Or floor standing?
        return "floor"

    # Default logic
    if old_placement and old_placement.lower() not in ["floor", "unknown"]:
         return old_placement.lower()
         
    return "surface" if category_key == "decor" else "floor"

def upgrade_object(old_obj, index):
    name = old_obj.get("name", "Unknown Object")
    category_key = determine_category(name)
    rules = CATEGORY_RULES.get(category_key, CATEGORY_RULES["decor"])
    
    # Generate ID
    obj_id = f"obj_{index+1:03d}"
    
    # Merge Semantic Categories
    semantic_category = rules["semantic_category"].copy()
    # Add specific name partials as tags
    words = name.lower().split()
    for w in words:
        if len(w) > 3 and w not in semantic_category:
            semantic_category.append(w)

    # Transform Placement Rules
    legacy_placement = old_obj.get("placement")
    new_placement = old_obj.get("placement_rules", {}).get("placement_type")
    
    # Extract candidate 
    if legacy_placement:
        raw_placement = legacy_placement
    elif new_placement:
        raw_placement = new_placement
    else:
        raw_placement = "floor"
        
    # INTELLIGENT RESOLUTION (Fixes corruption)
    placement_type_str = resolve_placement(name, category_key, raw_placement)
    
    allowed_surfaces = old_obj.get("parent_whitelist")
    if not allowed_surfaces:
         allowed_surfaces = old_obj.get("placement_rules", {}).get("allowed_surfaces")
    
    # Reconstruct allowed surfaces if missing and needed
    if not allowed_surfaces and placement_type_str == "surface":
        if category_key == "kitchen_item": allowed_surfaces = ["Kitchen Counter", "Table"]
        elif category_key == "electronics": allowed_surfaces = ["Desk", "TV Stand"]
        elif category_key == "lamp": allowed_surfaces = ["End Table", "Nightstand"]
        else: allowed_surfaces = ["Table", "Shelf"] # Default

    
    placement_rules = {
        "placement_type": placement_type_str,
        "allowed_surfaces": allowed_surfaces if allowed_surfaces else ["Floor"] if placement_type_str == "floor" else ["Wall"] if placement_type_str == "wall" else [],
        "minimum_surface_area_m2": 0.1 if placement_type_str == "surface" else 0.5,
        "clearance_3d": {
            "above": rules["spatial_constraints"].get("height_range_m", [0, 1])[1] * 0.5, # Estimation
            "sides": old_obj.get("clearance", 0.1), # accessing legacy clearance
            "front": old_obj.get("clearance", 0.1)
        }
    }

    # Functional Relationships
    func_rels = rules["functional_relationships"].copy()
    
    # Spatial Constraints
    spatial = rules["spatial_constraints"].copy()
    
    # Blender Auto Placement
    blender_rules = rules["blender_auto_placement"].copy()
    blender_rules["scale_range"] = [0.9, 1.1] # Standard variance

    new_obj = {
        "id": obj_id,
        "name": name,
        "semantic_category": semantic_category,
        "placement_rules": placement_rules,
        "functional_relationships": func_rels,
        "spatial_constraints": spatial,
        "blender_auto_placement": blender_rules
    }
    
    return new_obj

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: {SOURCE_FILE} not found.")
        return

    # Backup TARGET if it exists
    if os.path.exists(TARGET_FILE):
        shutil.copy(TARGET_FILE, BACKUP_FILE)
        print(f"Backed up {TARGET_FILE} to {BACKUP_FILE}")

    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in source file.")
        return

    # Handle if old_data is a list (current format) or dict
    if isinstance(old_data, dict) and "objects" in old_data:
        old_objects = old_data["objects"]
    elif isinstance(old_data, list):
        old_objects = old_data
    else:
        print("Error: Unknown JSON structure.")
        return

    new_objects = []
    print(f"Processing {len(old_objects)} objects from {SOURCE_FILE}...")

    for i, obj in enumerate(old_objects):
        new_obj = upgrade_object(obj, i)
        new_objects.append(new_obj)

    final_json = {
        "schema_version": TARGET_SCHEMA_VERSION,
        "knowledge_type": "placement_logic",
        "objects": new_objects
    }

    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=2)

    print(f"Successfully upgraded {len(new_objects)} objects to new schema in {TARGET_FILE}")

if __name__ == "__main__":
    main()
