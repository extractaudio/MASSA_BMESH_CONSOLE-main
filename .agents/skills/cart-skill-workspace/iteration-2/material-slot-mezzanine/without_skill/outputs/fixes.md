# Fixes — cart_arc_07_mezzanine.py

No fixes required.

All material slot assignments in `build_shape` exactly match the definitions in `get_slot_meta`:

- Slot 0 (Deck Surface) assigned to deck geometry
- Slot 1 (Structure) assigned to columns, base plates, and all beams
- Slot 2 (Railings) assigned to rail posts, top rail, and mid rail
- Slot 9 (Socket Anchor, sock=True) used via `tag_socket(9)` on column base faces

No undefined slot indices, no orphaned slot definitions, no missing assignments.
