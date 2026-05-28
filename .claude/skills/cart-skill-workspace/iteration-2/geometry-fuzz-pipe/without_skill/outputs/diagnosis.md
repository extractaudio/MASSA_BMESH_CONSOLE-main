# Diagnosis — cart_prim_02_pipe.py

## Audit Result
PASS — no errors, no CRITICAL flags, no FUZZ_CRASH.

## Source Review

### CARTRIDGE_META
- Required keys present: `name`, `id`, `icon`, `flags`.
- `id`: `"prim_02_pipe"` — correct naming convention.
- `icon`: `"MESH_CYLINDER"` — valid Blender icon.
- `flags`: `ALLOW_SOLIDIFY: False`, `USE_WELD: True`, `ALLOW_FUSE: True` — all valid flag names.

### get_slot_meta
- Three slots defined: 0 (Outer Surface), 1 (Inner Wall), 2 (Ends).
- All use `uv: "SKIP"` — appropriate since the cartridge manages its own UVs directly in `build_shape`.
- `phys` values: `METAL_STEEL` and `GENERIC` — both valid.

### build_shape
- MASSA_EDGE_SLOTS layer created correctly via `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")`.
- Geometry construction uses `bmesh.ops.create_circle` + `bridge_loops` for the annular profile — solid approach.
- STRAIGHT mode: extrude + translate, then optional bisect for segments. No degenerate edge risk.
- ELBOW mode: translate + spin — standard bmesh spin pattern, no geometry issues observed.
- Normal recalculation applied via `bmesh.ops.recalc_face_normals`.
- Face classification (outer/inner/cap) uses centroid and average vertex distance — robust for both modes.
- Material slot assignment: slots 0, 1, 2 assigned correctly to classified face groups.
- UV mapping: analytic cylindrical/toroidal UV calculation with seam-wrap correction (`> 0.5` check) — correct.
- Cap UV: flat planar projection — correct.
- Seam and edge-slot tagging: cap borders tagged seam + edge_slot 3; longitudinal seam edge identified by y~0 criterion — correct.

## Findings
No CRITICAL flags. No FUZZ_CRASH. No obvious geometry, UV, seam, or material-slot issues found in manual source review. The cartridge is well-structured and follows all MASSA conventions.
