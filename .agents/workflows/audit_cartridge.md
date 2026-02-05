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

If status: **FAIL**: Read the `errors` list.

- If errors mention "Zero-Area Faces", check your vertex coordinate math.
- If errors mention "Pinched UVs", ensure your unwrapping logic (e.g., `smart_project`, `unwrap`) uses sufficient margin or angle_based methods.

### Iterate

Rewrite the script and re-run the audit until status: **PASS**.
