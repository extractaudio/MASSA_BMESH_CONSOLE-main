---
description: Definitive guide for Material and Edge Slot IDs in Massa Cartridges.
---

# 🔵 AGENT: SLOT_STANDARDIZATION_PROTOCOL

## 1. OBJECTIVE

*The "Rosetta Stone" of the Massa Console.*

To ensure all cartridges interact seamlessly with the Console's Polish, Surface, and Physics systems, agents must adhere to strict Integer ID standards for Faces (Materials) and Edges (Features).

---

## 2. THE HARD 10 (MATERIAL SLOTS)

**Context:** `bm.faces.layers.int.get("MAT_TAG")`
**Constraint:** You must assign every face to one of these IDs.

| ID | Name | Role | Physics Tag | UV Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **0** | **BASE** | Main body, hull, primary structure. | `GENERIC` / `METAL` | BOX / UNWRAP |
| **1** | **DETAIL** | Vents, grilles, inset panels. | `MECHANICAL` | BOX |
| **2** | **TRIM** | Borders, frames, structural reinforcement. | `METAL_DARK` | STRIP / BOX |
| **3** | **GLASS** | Windows, cockpits, lenses. | `GLASS` | FIT |
| **4** | **EMISSION** | Lights, energy cores, screens. | `EMISSIVE` | FIT |
| **5** | **DARK** | Inner workings, shadows, rubber. | `RUBBER` | BOX |
| **6** | **ACCENT** | Paint stripes, decals, warnings. | `PAINT` | UNWRAP |
| **7** | **UTILITY** | Handles, latches, bolts. | `METAL_ROUGH` | BOX |
| **8** | **TRANSPARENT** | Holograms, forcefields (Alpha Blend). | `ENERGY` | FIT |
| **9** | **SOCKET** | **INVISIBLE.** Meta-data faces for snapping. | `NONE` | SKIP |

### 📝 Implementation Snippet

```python
tag_layer = bm.faces.layers.int.new("MAT_TAG")
for f in my_faces:
    f[tag_layer] = 0 # Assign to Base
```

---

## 3. THE NERVOUS SYSTEM (EDGE SLOTS)

**Context:** `bm.edges.layers.int.get("MASSA_EDGE_SLOTS")`
**Constraint:** Used by the Polish Stack (Bevel, Subd, Cloth).

| ID | Name | Visual Color | Logical Role | Polish Effect |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **PERIMETER** | 🔴 RED | Outer Boundary / Silhouette | **Seam + Sharp + Bevel.** The defining outline. |
| **2** | **CONTOUR** | 🟠 ORANGE | Major Form Break (90°) | **Sharp + Bevel.** Hard surface edges. |
| **3** | **GUIDE** | 🔵 BLUE | Topological Seam / Flow | **Seam Only.** Used for UV unwrapping cylinders/organic shapes. |
| **4** | **DETAIL** | 🟢 GREEN | Minor Surface Detail | **Bevel Only.** Small chamfers, no sharp shading. |
| **5** | **FOLD** | 🟣 PURPLE | Cloth/Soft Crease | **Crease.** Used for subdivision weighting. |

### 📝 Implementation Snippet

```python
edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
for e in bm.edges:
    if e.is_boundary:
        e[edge_slots] = 1 # PERIMETER
    elif e.calc_face_angle(0) > 1.5:
        e[edge_slots] = 2 # CONTOUR
```
