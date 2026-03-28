# MASSA Slot and Material Protocol

> **The 'Hard 10' Material System for Faces**

Golden Cartridges utilize a fixed 10-slot system (Indices 0-9) to handle material assignment dynamically via `get_slot_meta()`.

## 1. Slot Definition (`get_slot_meta`)
Defines the 10 Material Slots. It must return a dictionary where keys are Slot Indices (int 0-9) and values are parameter dicts.

**Keys in the dict:**
- `name`: Human-readable label (e.g., "Base Hull").
- `phys`: Physics/Visual Material tag (e.g., "DEBUG_1", "METAL_STEEL").
- `uv`: UV Strategy (e.g., "BOX", "UNWRAP", "SKIP").
- `sock` (Optional): If `True`, marks this slot as a Socket Anchor.

**Implementation Example:**
```python
def get_slot_meta(self):
    return {
        0: {"name": "Base Hull",     "uv": "BOX",    "phys": "DEBUG_1"},
        1: {"name": "Detail Vent",   "uv": "BOX",    "phys": "DEBUG_2"},
        2: {"name": "Trim/Frame",    "uv": "STRIP",  "phys": "DEBUG_3"},
        3: {"name": "Glass/Screen",  "uv": "FIT",    "phys": "DEBUG_4"},
        # ... define up to 9
        9: {"name": "Socket Anchor", "uv": "SKIP",   "sock": True, "phys": "DEBUG_9"},
    }
```

## 2. Standard Slot ID Meanings
| ID | Role | Default Material | Description |
| :--- | :--- | :--- | :--- |
| **0** | **BASE** | `DEBUG_1` | Main body, hull. |
| **1** | **DETAIL** | `DEBUG_2` | Vents, grilles, insets. |
| **2** | **TRIM** | `DEBUG_3` | Frames, borders. |
| **3** | **GLASS** | `DEBUG_4` | Windows, screens. |
| **4** | **EMISSION** | `DEBUG_5` | Lights, energy. |
| **5** | **DARK** | `DEBUG_6` | Inner shadows, tires. |
| **6** | **ACCENT** | `DEBUG_7` | Decals, stripes. |
| **7** | **UTILITY** | `DEBUG_8` | Bolts, handles. |
| **8** | **TRANSPARENT** | `DEBUG_9` | Forcefields. |
| **9** | **SOCKET** | `DEBUG_9` | **Anchor/Invisible**. Used for snapping points. |

## 3. Assignment Mandate (`build_shape`)
**Usage**: `f.material_index = ID`

Every face generated in `build_shape` must have a valid `material_index` (0-9).

## 4. UV Strategy

The UV unwrap style is defined in `get_slot_meta()` under the `"uv"` key:
- `"BOX"`: Tri-planar projection. Best for hard surface (Slots 0, 1, 2, 5, 7). Fallback for simple/flat parts.
- `"UNWRAP"`: LSCM Unwrap. **REQUIRES SEAMS** (Edge Slot 1 or 3). Best for organic/curved geometry.
- `"FIT"`: Stretches UVs to fill 0-1. Best for screens/glass (Slot 3, 4, 8).
- `"STRIP"`: Unwraps long quads evenly. Best for frames, trim, piping.
- `"SKIP"`: No auto-UVs generated. Signals that the script handles UVs manually mathematically inside `build_shape`. Strongly recommended for hero elements.

## 5. UV Mandate: Manual & Precise
Golden Cartridges **should preferably calculate UVs mathematically** within `build_shape` using the `"SKIP"` strategy. However, relying on the Engine's fallback strategies (`"BOX"`, `"UNWRAP"`, `"FIT"`, `"STRIP"`) is permissible and valid even in Golden Cartridges for non-hero elements or when procedural mathematical unwrapping is unnecessarily complex compared to the engine's auto-unwrap mechanisms.

When using `"SKIP"`, adhere to the following:

1. **Verify Layer**: `uv_layer = bm.loops.layers.uv.verify()`
2. **Calculate**: Iterate over faces/loops. Calculate `u` and `v` based on vertex coordinates, arc length, or polar coordinates.
3. **Handle Wrapping**: For cylindrical objects, detect the 0.0 -> 1.0 seam crossing and shift UVs to prevent "smearing".

**Standard Pattern:**
```python
for f in bm.faces:
    if f.material_index == 0: # Main Surface
        for l in f.loops:
            u, v = calculate_uv(l.vert.co)
            l[uv_layer].uv = (u * scale_u, v * scale_v)
```
