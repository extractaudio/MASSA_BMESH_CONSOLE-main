import os
import zipfile

from pathlib import Path

def package_addon():
    # Setup paths
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent
    source_dir = root_dir / "MASSA_BMESH_CONSOLE-main"
    addon_name = "MASSA_BMESH_CONSOLE" # Ideally read from manifest ID, but this is safe
    export_dir = root_dir / "_EXPORT"
    zip_path = export_dir / f"{addon_name}.zip"

    # Create export directory
    if export_dir.exists():
        # [USER REQUEST] Delete old package if it exists
        if zip_path.exists():
            try:
                os.remove(zip_path)
                print(f"Removed old package: {zip_path}")
            except Exception as e:
                print(f"Warning: Could not remove old package: {e}")
    else:
        export_dir.mkdir(parents=True)

    print(f"Packaging addon to: {zip_path}")

    # Files/Dirs to exclude
    EXCLUDE_DIRS = {
        '.git', 
        '.vscode', 
        '__pycache__', 
        '_EXPORT',
        'tests',
        '.github'
    }
    EXCLUDE_FILES = {
        '.gitignore', 
        '.ds_store', 
        'package_massa_addon.py',
        'Thumbs.db'
    }
    
    # Create Zip
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the directory
        for root, dirs, files in os.walk(source_dir):
            root_path = Path(root)
            
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                if file.endswith('.zip'): # Don't zip other zips recursively
                    continue
                    
                file_path = root_path / file
                
                # Calculate archive name (relative path inside zip)
                # For Blender 5.0 Extensions, manifest should be at root of zip
                arcname = file_path.relative_to(source_dir)
                
                # Filter out files inside excluded directories that might have slipped through
                # (though strict os.walk filtering above should catch them)
                if any(part in EXCLUDE_DIRS for part in arcname.parts):
                    continue

                print(f"Adding: {arcname}")
                zipf.write(file_path, arcname)

    print(f"Successfully created: {zip_path}")

if __name__ == "__main__":
    package_addon()
