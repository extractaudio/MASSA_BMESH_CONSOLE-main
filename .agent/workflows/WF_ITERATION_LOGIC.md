---
description: ITERATION & POLISH LOGIC
---

# ITERATION & POLISH LOGIC

## 1. Redo Panel Tuning

* **Tool:** `iterate_parameters(properties={...})`
* **Rules:**
  * `segments`: Keep < 64 for speed.
  * `seed`: Change to vary random generation.

## 2. Visual Polish (Seams)

* **Tool:** `scan_visuals(mode="WIRE")`
* **Look for:** Red Lines (Seams).
* **Rule:** Seams must not "Pinch" (converge on a flat surface).
* **Fix:**
  * Try rotating seams via Redo Props first: `iterate_parameters({"edge_slot_1_rot": 90})`.
  * Only edit code if Redo Props fail.

## 3. Slot Audit

* **Tool:** `scan_slots()`
* **Rule:**
  * Slot 0: Main Body
  * Slot 1: Trim/Detail
  * Slot 2: Emissive
