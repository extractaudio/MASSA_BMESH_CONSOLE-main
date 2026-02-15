---
description: Definitive guide for Material and Edge Slot IDs in Massa Cartridges.
---

# 🔵 AGENT: SLOT_STANDARDIZATION_PROTOCOL

## 1. OBJECTIVE

*Topology foundation of the Massa Console.*

To ensure all cartridges generate slots for all faces ('slots' redo panel tab) and edges ('Edges' redo panel tab). The faces generate their own 'Visual' material and 'Physics' ID. The Edges generate an edge slot that is defined by: Perimeter (endcaps/important edge loops), Contour (90 degree forum break), Seams (manually placed Guide to ensuring a proper uv unwrap), Detail (Edges whos neibors have very minor surface detail), and Fold (Used for subdivision weighting cloth.) Attempt to create professional grade UV map by visually auditing the veiwport. Agents must adhere to strict Integer ID standards for Faces (Materials) and Edges (Features).

ensure that these slots are NOT creating new mesh edges, faces, or vert. The slots and edges purpose it to MARK the proper placement of faces (slots) and edges (edge slots).

---

## 2. SLOTS (FACE MATERIAL IDs)

**Context:** `bm.faces.layers.int` (Material Index)
**Constraint:** You must assign `face.material_index` to one of these IDs.

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
# No custom layer needed. Use native BMesh attribute.
for f in my_faces:
    f.material_index = 0 # Assign to Base
```

---

## 3. EDGE SLOTS

**Context:** `bm.edges.layers.int.get("MASSA_EDGE_SLOTS")`
**Constraint:** Used by the Polish Stack (Bevel, Subd, Cloth).

| ID | Name | Visual Color | Logical Role | Polish Effect |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **PERIMETER** | 🔵 BLUE | Outer Boundary / Silhouette | **Seam + Sharp + Bevel.** The defining outline. |
| **2** | **CONTOUR** | 🟢 GREEN | Major Form Break (90°) | **Sharp + Bevel.** Hard surface edges. |
| **3** | **GUIDE** | 🔴 RED  | Topological Seam / Flow | **Seam Only.** Used for UV unwrapping cylinders/organic shapes. |
| **4** | **DETAIL** | 🟠 ORANGE | Minor Surface Detail | **Bevel Only.** Small chamfers, no sharp shading. |
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
