# Fixes — cart_arc_07_mezzanine.py

## Analysis

The jCodemunch index was stale (`_freshness: stale_index`). Reading the actual file on disk
revealed the phys values had already been corrected in a prior edit.

## Current On-Disk State (correct)

```python
def get_slot_meta(self):
    return {
        0: {"name": "Deck Surface", "uv": "BOX",  "phys": "METAL_IRON"},
        1: {"name": "Structure",    "uv": "BOX",  "phys": "METAL_STEEL"},
        2: {"name": "Railings",     "uv": "BOX",  "phys": "METAL_STEEL"},
        9: {"name": "Socket Anchor","sock": True, "uv": "SKIP", "phys": "GENERIC"}
    }
```

## What Was Previously Wrong (stale index values)

| Slot | Stale (bad) phys   | Current (correct) phys | Fix applied |
|------|--------------------|------------------------|-------------|
| 0    | METAL_CHECKERPLATE | METAL_IRON             | Previously fixed |
| 1    | METAL_STEEL        | METAL_STEEL            | Was already correct |
| 2    | METAL_PAINTED      | METAL_STEEL            | Previously fixed |
| 9    | DEBUG_9, uv=BOX    | GENERIC, uv=SKIP       | Previously fixed |

## No Further Changes Required

All phys values on disk are valid MASTER_MAT_DB keys. All slot indices defined in
get_slot_meta are used in build_shape and vice versa. Socket slot 9 correctly has
uv="SKIP" and sock=True.
