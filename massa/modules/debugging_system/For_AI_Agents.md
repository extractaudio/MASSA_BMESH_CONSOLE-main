# Instructions for AI Agents

To debug or inspect the Blender state, you can execute Python code inside the running Blender instance using the `debug_agent.py` tool.

## Tool Usage

**Script Path**: `modules/debugging_system/debug_agent.py`

**Command**:

```bash
python modules/debugging_system/debug_agent.py --code "<YOUR_PYTHON_CODE>"
```

**Example**:

```bash
python modules/debugging_system/debug_agent.py --code "import bpy; print(bpy.data.objects.keys())"
```

## detailed Inspection

For complex inspection, creating a temporary python file is recommended:

1. Create a file `temp_inspect.py` with your `bpy` logic.
2. Run: `python modules/debugging_system/debug_agent.py --file temp_inspect.py`
3. Read the output.
