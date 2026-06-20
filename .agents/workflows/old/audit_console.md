---
description: Audit the Massa Console internals using the Headless architecture
---

1. Ensure your Blender path is configured in `modules/debugging_system/config.py`.

2. Run the Console Bridge script from the project root:

   ```bash
   python MASSA_BMESH_CONSOLE-main/modules/debugging_system/bridge_console.py
   ```

## Agent Protocol

To perform this audit via the MCP interface:

* **Tool:** `audit_console()`

## System Protocol: Console Auditing

This workflow tests the integrity of the Massa Console itself, not just an individual cartridge.

### What it Tests

* **Addon Registration**: Verifies `__init__.py` and module loading.
* **Operator Registry**: Checks if `massa.gen_*` operators are registered.
* **Execution Pipeline**: Runs a standard cartridge (e.g., Beam) to verify geometry generation.
* **Data Integrity**: Checks for mandatory layers like `MASSA_EDGE_SLOTS`.
* **Resurrection Identifiers**: Verifies `massa_op_id` metadata for Redo Panel support.

### Analyze Results

If status: **FAIL**:

* **Import Errors**: The console failed to load. Check `__init__.py` or module dependencies.
* **Operator Missing**: Registration failed. Check `massa_console.register()`.
* **Layer Missing**: The geometry pipeline dropped the `MASSA_EDGE_SLOTS` layer. Check `massa_engine.py`.
