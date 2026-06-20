---
description: ITERATION & POLISH LOGIC
---

# ITERATION & POLISH LOGIC

## 1. Redo Panel Tuning

* **Tool:** `iterate_parameters(properties={...})` or `massa_generator(...)`
* **Rules:**
  * `segments`: Keep < 64 for speed.
  * `seed`: Change to vary random generation.

## 2. Visual Polish (Seams)

* **Tool:** `scan_visuals(view_mode="WIRE")`
* **Look for:** Red Lines (Seams).
* **Rule:** Seams must not "Pinch" (converge on a flat surface).
* **Fix:**
  * Try rotating/recalculating seams via Redo Props: `iterate_parameters({"edge_slot_angle_threshold": 80})`.
  * Only edit code if Redo Props fail.

## 3. Slot Audit

* **Tool:** `verify_material_logic(filename="...")`
* **Tool:** `scan_slots()` (Live Check)
* **Rule:**
  * Slot 0: Main Body
  * Slot 1: Trim/Detail
  * Slot 2: Emissive
