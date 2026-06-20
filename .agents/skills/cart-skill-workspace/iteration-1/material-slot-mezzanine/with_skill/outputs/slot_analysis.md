# Slot Analysis — cart_arc_07_mezzanine.py

## get_slot_meta (BEFORE FIX)

| Slot | Name | uv | phys | sock | In MASTER_MAT_DB? |
|------|------|----|------|------|-------------------|
| 0 | Deck Surface | BOX | METAL_CHECKERPLATE | — | **NO — INVALID** |
| 1 | Structure | BOX | METAL_STEEL | — | YES |
| 2 | Railings | BOX | METAL_PAINTED | — | **NO — INVALID** |
| 9 | Socket Anchor | BOX | DEBUG_9 | True | **NO — INVALID** |

## build_shape Face Assignments

| tag_slot call | Context | Slot Defined? |
|---------------|---------|--------------|
| tag_slot(1) | Columns (create_box for each ix/iy) | YES |
| tag_slot(1) | Base plates (STEEL_BEAM style) | YES |
| tag_slot(1) | X-direction beams | YES |
| tag_slot(1) | Y-direction beams | YES |
| tag_slot(0) | Deck extruded faces | YES |
| tag_slot(2) | Railing posts | YES |
| tag_slot(2) | Top rail | YES |
| tag_slot(2) | Mid rail | YES |
| tag_socket(9) | Column base faces at Z~0 | YES (sock=True) |

## Mismatch Summary

| Problem | Slot | Detail |
|---------|------|--------|
| Invalid phys key | 0 | "METAL_CHECKERPLATE" not in MASTER_MAT_DB |
| Invalid phys key | 2 | "METAL_PAINTED" not in MASTER_MAT_DB |
| Invalid phys key | 9 | "DEBUG_9" not in MASTER_MAT_DB |
| Inappropriate uv | 9 | Socket slots should use "SKIP" not "BOX" |

## Unused / Missing Slots

- All slots used in build_shape (0, 1, 2, 9) are defined in get_slot_meta — no missing slots.
- No extra slots in get_slot_meta that build_shape never uses.
