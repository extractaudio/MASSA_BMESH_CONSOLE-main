# Fixes: cart_arc_07_mezzanine.py — Material Slot Issues

## Result

**No fixes required.**

Static analysis of the cartridge found no material slot mismatches:

- Every slot index assigned via `tag_slot()` or `tag_socket()` in `build_shape`
  (indices 0, 1, 2, 9) is declared in `get_slot_meta`.
- Every slot declared in `get_slot_meta` (indices 0, 1, 2, 9) is assigned to at
  least one face in `build_shape`.
- Slot 9 is correctly marked `"sock": True` and is only used via `tag_socket(9)`.

## What was checked

1. Enumerated all `tag_slot(N)` and `tag_socket(N)` call sites in `build_shape`.
2. Cross-referenced against the dict returned by `get_slot_meta`.
3. Confirmed no stray integer (e.g. slot 3, 4, 5…8) appears anywhere in the function.
4. Confirmed that conditional branches (`angled_supports`, `structural_supports`,
   `stair_cutout`, `railing_h > 0`) all use the correct slot indices consistent
   with the unconditional geometry.

## No changes applied to the cartridge file.
