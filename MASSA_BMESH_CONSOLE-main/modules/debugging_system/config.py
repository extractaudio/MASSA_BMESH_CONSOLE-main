import os
import sys

# ==========================================================
# [IMPORTANT] SET YOUR BLENDER EXE PATH HERE
# Windows: r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
# MacOS:   "/Applications/Blender.app/Contents/MacOS/Blender"
# Linux:   "/usr/bin/blender"
# ==========================================================
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

if not os.path.exists(BLENDER_PATH):
    print(f"CRITICAL ERROR: Blender not found at {BLENDER_PATH}")
    sys.exit(1)