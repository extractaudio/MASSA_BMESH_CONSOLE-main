# MASSA BMESH CONSOLE - SETUP

## Prerequisites

1. **Blender 4.0+** (Recommended: Blender 4.5.0 or later)
    * Ensure Blender is installed and you know the path to the executable.

## Configuration

1. **Verify Blender Path**
    * Open `modules/debugging_system/config.py`.
    * Update the `BLENDER_PATH` variable to point to your local Blender executable.
    * Example: `BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"`

## Dependency Installation

The project currently has no external Python dependencies beyond the standard library (and `bpy` which is provided by Blender).

## Running the Debugger

You can use the `modules/debugging_system/debug_agent.py` script to run arbitrary Python code within the Blender context:

```bash
python modules/debugging_system/debug_agent.py --code "import bpy; print(bpy.app.version_string)"
```

Or run a specific python file:

```bash
python modules/debugging_system/debug_agent.py --file path/to/your_script.py
```
