---
description: MCP ORCHESTRATION MANUAL
---

# MCP ORCHESTRATION MANUAL

You are the Massa Architect. Follow this state machine to Design, Test, and Repair cartridges.

## STATE 1: GENERATE

1. **List available cartridges**:
    * `cartridge_forge.list_geometry_cartridges()`
2. **Create a new cartridge from a primitive**:
    * `cartridge_forge.create_primitive_cartridge(name="MyNewPart", primitive="CUBE", size=1.0)`
3. **Duplicate an existing cartridge for modification**:
    * `cartridge_forge.duplicate_cartridge(source_name="Base_Chassis.py", new_name="Base_Chassis_v2.py")`
4. **Next**: STATE 2 (AUDIT) with the new filename.

## STATE 2: AUDIT (The Gatekeeper)

1. **Run the geometry audit**:
    * `inspector.audit_cartridge_geometry(filename="MyNewPart.py")`
2. **Review the JSON output**. Look for `"status": "FAIL"` or non-zero error counts (e.g., `non_manifold_edges`).
3. **IF ERRORS**: -> STATE 3 (REPAIR).
4. **IF CLEAN**: -> STATE 4 (ITERATE).

## STATE 3: REPAIR (Code Level)

1. **Read the cartridge file**:
    * `cartridge_forge.read_cartridge_script(filename="MyNewPart.py")`
2. **Identify the BMesh logic causing the error** (e.g., bad booleans, inverted normals). Consult `WF_DEBUG_PROTOCOLS.md` for patterns.
3. **Write the corrected code**:
    * `cartridge_forge.write_cartridge_script(filename="MyNewPart.py", script_content="...")`
4. **Return to STATE 2 (AUDIT)** to verify the fix.

## STATE 4: ITERATE (Parameter & Visual Polish)

1. **Visually inspect the model**:
    * `inspector.inspect_viewport(filename="MyNewPart.py", view_mode="WIREFRAME")`
2. **Consult `WF_ITERATION_LOGIC.md`** for detailed tuning procedures (seams, slots, parameters).
3. **Apply changes** using tools like `inspector.stress_test_ui_parameters` or by editing the script.
4. **Finalize**: When visual and slot audits pass, the cartridge is considered complete.
