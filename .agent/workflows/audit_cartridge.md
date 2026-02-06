---
description: Audit a geometry cartridge using the headless Blender system
---

1. Select the cartridge you want to audit.
2. Run the bridge script from the project root. Replace `<cartridge_path>` with the relative path to your target file.

   Example: `python MASSA_BMESH_CONSOLE-main/modules/debugging_system/bridge.py MASSA_BMESH_CONSOLE-main/modules/cartridges/prim_con_beam.py`

   ```bash
   python MASSA_BMESH_CONSOLE-main/modules/debugging_system/bridge.py <cartridge_path>
   ```

## System Protocol: Geometry Auditing

You have access to a background "Fake Blender" debugging system.

### Write Code

Generate your bpy geometry script and save it to `geometry_cartridges/candidate.py`.

### Run Audit

Execute the bridge command:

```bash
python debugging_system/bridge.py geometry_cartridges/candidate.py
```

### Analyze

If status: **FAIL**: Read the `errors` list, which now includes Fuzzer output.

- **FUZZ_CRASH**: The cartridge crashed when randomized parameters were applied. Check the `PARAMS` log to see what values caused the break.
- **CRITICAL_LOOSE_VERTS**: You have vertices floating in space (not part of an edge).
- **CRITICAL_WIRE_EDGES**: You have edges that don't make a face.

### Iterate

Rewrite the script and re-run the audit until status: **PASS**.
