# Material Slot Analysis: cart_arc_07_mezzanine.py

## get_slot_meta — defined slots

| Index | Name            | UV   | Phys                | sock  |
|-------|-----------------|------|---------------------|-------|
| 0     | Deck Surface    | BOX  | METAL_CHECKERPLATE  | —     |
| 1     | Structure       | BOX  | METAL_STEEL         | —     |
| 2     | Railings        | BOX  | METAL_PAINTED       | —     |
| 9     | Socket Anchor   | BOX  | DEBUG_9             | True  |

## build_shape — tag_slot / tag_socket call sites

| Line(s) | Geometry          | tag_slot / tag_socket | Match in get_slot_meta? |
|---------|-------------------|-----------------------|--------------------------|
| 181     | Columns           | tag_slot(1)           | YES — Structure          |
| 187     | Base plates       | tag_slot(1)           | YES — Structure          |
| 201,205 | Diagonal braces   | tag_slot(1)           | YES — Structure          |
| 212     | X beams           | tag_slot(1)           | YES — Structure          |
| 218     | Y edge girders    | tag_slot(1)           | YES — Structure          |
| 263     | Deck (pre-extrude)| tag_slot(0)           | YES — Deck Surface       |
| 266     | Deck sides (grow) | tag_slot(0)           | YES — Deck Surface       |
| 292     | Railing posts     | tag_slot(2)           | YES — Railings           |
| 304     | Top rail bar      | tag_slot(2)           | YES — Railings           |
| 311     | Mid rail bar      | tag_slot(2)           | YES — Railings           |
| 344     | Socket faces      | tag_socket(9)         | YES — Socket Anchor      |

## Slot index coverage summary

| Slot | Defined in get_slot_meta | Used in build_shape | Status  |
|------|--------------------------|---------------------|---------|
| 0    | YES                      | YES (lines 263,266) | OK      |
| 1    | YES                      | YES (lines 181,187,201,205,212,218) | OK |
| 2    | YES                      | YES (lines 292,304,311) | OK   |
| 9    | YES (sock=True)          | YES (line 344)      | OK      |

## Mismatches

**None found.**

All slot indices used in `build_shape` (0, 1, 2, 9) are declared in `get_slot_meta`.
No declared slots in `get_slot_meta` are left unused by `build_shape`.

## Notes

- `tag_socket(9)` is the correct call for slot 9 which has `"sock": True` — consistent
  with MASSA convention.
- `stair_cutout` code uses `bmesh.ops.bisect_plane` which may create new faces at
  `z_deck_base`. Those faces are gathered into `deck_faces` and tagged slot 0 before
  extrusion, so cutout remnants also get the correct material.
- `builder.grow_selection(1)` after extrusion selects newly-created side walls of the
  deck slab and tags them slot 0 — intentional and correct (deck sides = deck material).
- `structural_supports` brace geometry: after `create_grid` the code calls `tag_slot(1)`
  before `align_normal_to_vector` and extrude, then calls `tag_slot(1)` again after
  `grow_selection(1)`. Both calls correctly target slot 1 (Structure).
