# Fixes Applied — cart_arc_07_mezzanine.py

File: `massa/modules/cartridges/cart_arc_07_mezzanine.py`
Method: `get_slot_meta`
Lines: 72–78

## Changes

### Slot 0 — phys fix
**Before:** `"phys": "METAL_CHECKERPLATE"`
**After:**  `"phys": "METAL_IRON"`
**Reason:** "METAL_CHECKERPLATE" is not a key in MASTER_MAT_DB. METAL_IRON is the closest valid match for a heavy industrial deck surface.

### Slot 2 — phys fix
**Before:** `"phys": "METAL_PAINTED"`
**After:**  `"phys": "METAL_STEEL"`
**Reason:** "METAL_PAINTED" is not a key in MASTER_MAT_DB. METAL_STEEL is appropriate for railing elements; no painted-metal variant exists in the DB.

### Slot 9 — phys and uv fix
**Before:** `"phys": "DEBUG_9"`, `"uv": "BOX"`
**After:**  `"phys": "GENERIC"`, `"uv": "SKIP"`
**Reason:** "DEBUG_9" is not a valid phys key (MASTER_MAT_DB has "MASSA_DEBUG_9" as a debug color slot, not a real physics material). Socket slots (sock=True) should use "SKIP" for uv since they don't require unwrapping. GENERIC is the correct fallback phys for socket anchor geometry.

## Full Before/After Diff

```diff
-            0: {"name": "Deck Surface", "uv": "BOX", "phys": "METAL_CHECKERPLATE"},
+            0: {"name": "Deck Surface", "uv": "BOX", "phys": "METAL_IRON"},
             1: {"name": "Structure", "uv": "BOX", "phys": "METAL_STEEL"},
-            2: {"name": "Railings", "uv": "BOX", "phys": "METAL_PAINTED"},
+            2: {"name": "Railings", "uv": "BOX", "phys": "METAL_STEEL"},
-            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
+            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "GENERIC"}
```

No changes to `build_shape` were required — all slot indices used (0, 1, 2, 9) were already correctly defined.
