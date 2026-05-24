@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "MCP_DIR=%ROOT_DIR%_MCP"

if /I "%~1"=="--help" goto :help
if /I "%~1"=="-h" goto :help
if /I "%~1"=="/?" goto :help

echo.
echo MASSA BMESH CONSOLE installer
echo =============================
echo.

if not exist "%MCP_DIR%\pyproject.toml" (
    echo ERROR: Could not find "%MCP_DIR%\pyproject.toml".
    echo Run this script from the repository root, or keep it in the root folder.
    exit /b 1
)

call :find_python
if errorlevel 1 exit /b 1

echo Checking Python version...
"%PYTHON_CMD%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.10 or newer is required.
    "%PYTHON_CMD%" --version
    exit /b 1
)
"%PYTHON_CMD%" --version

where uv >nul 2>nul
if errorlevel 1 (
    echo.
    echo uv was not found. Installing uv with pip...
    "%PYTHON_CMD%" -m pip install --upgrade uv
    if errorlevel 1 (
        echo ERROR: Failed to install uv.
        exit /b 1
    )
) else (
    echo uv found.
)

echo.
echo Installing MCP server dependencies from "%MCP_DIR%\pyproject.toml"...
uv sync --project "%MCP_DIR%"
if errorlevel 1 (
    echo ERROR: uv sync failed.
    exit /b 1
)

echo.
echo Verifying MCP entry point...
uv run --project "%MCP_DIR%" massa-blender-mcp --help >nul
if errorlevel 1 (
    echo ERROR: massa-blender-mcp did not run successfully.
    exit /b 1
)

echo.
echo Install complete.
echo.
echo Notes:
echo - Blender is still an external prerequisite and provides bpy itself.
echo - Set BLENDER_PATH in massa\modules\debugging_system\config.py before running headless cartridge audits.
echo - Vendored libraries under _MCP\vendor do not need a separate install step.
exit /b 0

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

echo ERROR: Python was not found. Install Python 3.10 or newer, then rerun this script.
exit /b 1

:help
echo Installs the Python dependencies needed by this repository.
echo.
echo Usage:
echo   install.bat
echo.
echo What it does:
echo   1. Requires Python 3.10 or newer.
echo   2. Installs uv with pip if uv is missing.
echo   3. Runs uv sync --project _MCP to install MCP dependencies.
echo   4. Verifies the massa-blender-mcp command is available.
echo.
echo Blender itself is not installed by this script.
exit /b 0
