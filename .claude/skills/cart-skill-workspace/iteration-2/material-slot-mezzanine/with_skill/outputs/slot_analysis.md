# Slot Analysis — cart_arc_07_mezzanine.py

## Index Coverage

| Slot | Defined in get_slot_meta | Used in build_shape | Status |
|------|--------------------------|---------------------|--------|
| 0    | Yes — "Deck Surface"     | Yes — `tag_slot(0)` on deck extrusion | OK |
| 1    | Yes — "Structure"        | Yes — `tag_slot(1)` on columns, base plates, X beams, Y beams | OK |
| 2    | Yes — "Railings"         | Yes — `tag_slot(2)` on posts, top rail, mid rail | OK |
| 9    | Yes — "Socket Anchor"    | Yes — `tag_socket(9)` on column base faces | OK |

All indices used in build_shape appear in get_slot_meta. No orphaned or missing slots.

## Phys Value Validity

Valid MASTER_MAT_DB keys (from skill spec): METAL_IRON, METAL_STEEL, CONCRETE_RAW, RUBBER, GLASS_CLEAR, FABRIC_ROUGH, WOOD_OAK, PLASTIC_HARD, GENERIC, MASSA_DEBUG_1 through MASSA_DEBUG_9.

| Slot | Name           | phys value          | Valid? | Issue |
|------|----------------|---------------------|--------|-------|
| 0    | Deck Surface   | METAL_CHECKERPLATE  | NO     | Not in MASTER_MAT_DB — no CHECKERPLATE key exists |
| 1    | Structure      | METAL_STEEL         | YES    | — |
| 2    | Railings       | METAL_PAINTED       | NO     | Not in MASTER_MAT_DB — no PAINTED key exists |
| 9    | Socket Anchor  | DEBUG_9             | NO     | Must be MASSA_DEBUG_9 (prefixed form) |

## Summary

- Index coverage: PASS (all 4 slots defined and used)
- Phys validity: FAIL — 3 of 4 slots have invalid phys values
  - Slot 0: METAL_CHECKERPLATE → should be METAL_STEEL (closest valid steel-family key)
  - Slot 2: METAL_PAINTED → should be METAL_STEEL (no painted-metal key; steel is the closest structural metal)
  - Slot 9: DEBUG_9 → should be MASSA_DEBUG_9 (correct prefixed form)
