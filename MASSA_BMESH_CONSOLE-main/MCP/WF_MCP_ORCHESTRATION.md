---
description: MCP ORCHESTRATION MANUAL
---

# MCP ORCHESTRATION MANUAL

You are the Massa Architect. Follow this state machine to Design, Test, and Repair cartridges.

## STATE 1: GENERATE

1. Construct command: `create_cartridge -shape box -slots 2`
2. Execute: `generate_cartridge(command_str)`
3. **Next:** STATE 2 (AUDIT)

## STATE 2: AUDIT (The Gatekeeper)

1. Call `scan_telemetry()`.
2. **IF ERRORS (Ghost faces / Non-Manifold):** -> STATE 3 (REPAIR).
3. **IF CLEAN:** -> STATE 4 (ITERATE).

## STATE 3: REPAIR (Code Level)

1. Read cartridge file using `file_system_edit('READ')`.
2. Consult `WF_DEBUG_PROTOCOLS.md`.
3. Rewrite logic using `file_system_edit('WRITE')`.
4. Trigger `iterate_parameters({})` to refresh.
5. Return to STATE 2 (AUDIT).

## STATE 4: ITERATE (Parameter Level)

1. Call `scan_visuals(view_mode="WIRE")`.
2. Consult `WF_ITERATION_LOGIC.md`.
3. Call `iterate_parameters({...})` to tune shape/seams.
4. Call `scan_slots()` to verify Material IDs.
5. **Finalize:** Report success.
