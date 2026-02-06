---
description: Guide to understanding the MASSA Console architecture and verification
---

# 🔵 AGENT: CONSOLE_UNDERSTANDING

## 1. OBJECTIVE

Understand the "Brain-Muscle-Engine" architecture of the `MASSA_BMESH_CONSOLE-main` addon and verification protocols.

## 2. KEY COMPONENTS

* **Registry (`__init__.py`)**: The entry point. Handles Hot Reloading of all modules.
* **Brain (`massa_console.py`)**: Stores the State (Properties).
* **Muscle (`operators/massa_base.py`)**: The Base Operator. Handles "Resurrection" (Redo capability) and execution.
* **Engine (`modules/massa_engine.py`)**: The Generation Pipeline.
* **Face (`ui/`)**: The Interface (Panel and Gizmos).

## 3. SYSTEM AUDIT PROTOCOL

Before making structural changes, you must verify the Console's health.

**Command:**

```bash
python debugging_system/bridge_console.py
```

**What it Checks:**

1. **Registry**: Can the addon load in a clean environment?
2. **Operators**: Are `massa.gen_*` operators registered?
3. **Data Layers**: Does the engine produce `MASSA_EDGE_SLOTS`?
4. **Resurrection**: Is `massa_op_id` correctly assigned/restored?

## 4. ARCHITECTURAL RULES

* **Strict Separation**: UI code goes in `ui/`. Logic goes in `operators/`. Math goes in `modules/`.
* **Property Sync**: `MassaPropertiesMixin` links the Console (Scene) to the Operator.
* **Headless Safety**: Always guard against `context.space_data` being None in `massa_engine.py`.
