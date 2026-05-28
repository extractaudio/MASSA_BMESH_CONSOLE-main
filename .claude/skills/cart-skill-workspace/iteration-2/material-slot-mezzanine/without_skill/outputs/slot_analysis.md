# Material Slot Analysis — cart_arc_07_mezzanine.py

## Defined in `get_slot_meta` (lines 60–66)

| Slot | Name            | UV    | Phys               | Notes       |
|------|-----------------|-------|--------------------|-------------|
| 0    | Deck Surface    | BOX   | METAL_CHECKERPLATE |             |
| 1    | Structure       | BOX   | METAL_STEEL        |             |
| 2    | Railings        | BOX   | METAL_PAINTED      |             |
| 9    | Socket Anchor   | BOX   | DEBUG_9            | sock=True   |

## Used in `build_shape` via `tag_slot()` / `tag_socket()` (lines 97–336)

| Call             | Location (geometry)                        | Slot |
|------------------|--------------------------------------------|------|
| `tag_slot(1)`    | Columns (concrete and steel styles)        | 1    |
| `tag_slot(1)`    | Base plates (STEEL_BEAM style)             | 1    |
| `tag_slot(1)`    | X-direction beams (at each Y grid line)    | 1    |
| `tag_slot(1)`    | Y-direction beams (joists)                 | 1    |
| `tag_slot(0)`    | Deck faces after extrude (deck thickness)  | 0    |
| `tag_slot(2)`    | Railing posts                              | 2    |
| `tag_slot(2)`    | Top rail                                   | 2    |
| `tag_slot(2)`    | Mid rail                                   | 2    |
| `tag_socket(9)`  | Column base socket (faces at Z~0)          | 9    |

## Comparison

| Slot | Defined? | Used in build_shape? | Match? |
|------|----------|----------------------|--------|
| 0    | YES      | YES (deck extrude)   | OK     |
| 1    | YES      | YES (structure)      | OK     |
| 2    | YES      | YES (railings)       | OK     |
| 9    | YES      | YES (socket anchor)  | OK     |

## Verdict

No mismatches. All slots used in `build_shape` are covered by `get_slot_meta`, and all defined slots are actively assigned in the geometry. No orphaned definitions or undefined slot references.
