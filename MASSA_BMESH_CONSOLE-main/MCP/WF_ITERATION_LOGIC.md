---
description: ITERATION & POLISH LOGIC
---

# ITERATION & POLISH LOGIC

This workflow details the process of refining a cartridge's parameters and visual characteristics after it has passed the initial geometry audit.

## 1. Redo Panel Tuning (Parameter Stress Testing)

*   **Goal:** Ensure the script produces the intended variations when parameters change and make sure the geometry cartridge (ui: shape tab) parameters are within a visually desireable range.
*   **Tool:** `inspector.stress_test_ui_parameters()`
*   **Usage:**
    1.  Define a set of new parameters as a JSON string.
    2.  Call the tool: `inspector.stress_test_ui_parameters(filename="MyPart.py", parameter_json='{"segments": 12, "radius": 0.75}')`
    3.  Review the output audit report for geometry errors. If it fails, the script is not robust enough and needs a code-level fix (See Orchestration: STATE 3).

## 2. Visual Polish & Seam Placement

*   **Goal:** Verify topology flow and ensure UV seams are placed logically on sharp edges, not flat surfaces.
*   **Primary Tools:**
    1.  `inspector.inspect_viewport(filename="MyPart.py", view_mode="WIREFRAME")`
        *   Provides a general overview of the topology. Look for pinching or strange flows.
    2.  `inspector.visualize_edge_slots(filename="MyPart.py", slot_name="seam")`
        *   **This is the most critical tool.** It generates an image highlighting *only* the edges marked as 'seam'. Red lines on flat surfaces are an immediate failure.

*   **Fixing Bad Seams:**
    1.  **Parameter-First Approach:** Try to fix seams by changing script parameters that control edge selection logic (e.g., angle thresholds). Use `stress_test_ui_parameters` to test changes.
    2.  **Code-Level Fix:** If parameters are not exposed or sufficient, read the script (`cartridge_forge.read_cartridge_script`), modify the BMesh edge selection logic for the `slots['seam']` array, and write it back (`cartridge_forge.write_cartridge_script`).

## 3. Slot & Material Audit

*   **Goal:** Verify that all intended geometry slots (bevels, materials, subdivisions) are correctly assigned.
*   **Tools:**
    1.  `inspector.visualize_edge_slots(filename, slot_name="...")`
        *   Use this for any edge-based slot: `bevel`, `crease`, etc.
    2.  `inspector.verify_material_logic(filename)`
        *   Performs a static code analysis to ensure the `MAT_TAG` integer layer is being retrieved and used, which is required for material assignment.
    3.  `inspector.inspect_viewport(filename, view_mode="MATERIAL")`
        *   A final visual check to see if materials are applied as expected in the final render.