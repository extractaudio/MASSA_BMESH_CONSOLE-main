import os
from datetime import datetime

def snapshot_mcp_to_markdown(source_dir, output_file, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []
        
    exclude_paths = [os.path.abspath(os.path.join(source_dir, d)) for d in exclude_dirs]
    
    print(f"Creating Markdown snapshot of {source_dir} -> {output_file}")
    if exclude_paths:
        print("Excluding directories:")
        for ep in exclude_paths:
            print(f"  - {ep}")
            
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# MCP Codebase Snapshot\n\n")
        
        count = 0
        for root, dirs, files in os.walk(source_dir):
            # Filter out excluded paths and common ignore directories
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in exclude_paths 
                       and d not in ['.git', '__pycache__', '.venv', 'node_modules']]
            
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.abspath(file_path) in exclude_paths:
                    continue
                    
                rel_path = os.path.relpath(file_path, os.path.dirname(source_dir))
                
                # Determine language for markdown code block
                ext = os.path.splitext(file)[1].lower()
                lang = ext[1:] if ext else "text"
                if lang == "py": lang = "python"
                elif lang == "js": lang = "javascript"
                elif lang == "ts": lang = "typescript"
                elif lang == "md": lang = "markdown"
                
                try:
                    # Only read files that can be decoded as UTF-8 (filters out most binaries)
                    with open(file_path, 'r', encoding='utf-8') as src:
                        content = src.read()
                        
                    f.write(f"## File: `{rel_path}`\n\n")
                    f.write(f"```{lang}\n")
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                    f.write("```\n\n")
                    
                    count += 1
                    
                    if count % 100 == 0:
                        print(f"Processed {count} files...")
                        
                except UnicodeDecodeError:
                    # Skip binary files like images, compiled data, etc.
                    pass
                    
    print(f"Snapshot complete. {count} text files merged and saved to {output_file}")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    mcp_dir = os.path.join(base_dir, "_MCP")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = os.path.join(base_dir, "_EXPORT")
    if not os.path.exists(export_dir):
        export_dir = base_dir
        
    output_md = os.path.join(export_dir, f"MCP_snapshot_{timestamp}.md")
    
    # Exclude vendor directory, data/api, data/manual, and lock files
    excludes = [
        os.path.join("blmcp", "vendor"),
        os.path.join("blmcp", "data", "api"),
        os.path.join("blmcp", "data", "manual"),
        os.path.join("massa_blender_mcp.egg-info"),
        "uv.lock" # skip lock file to save space
    ]
    
    if not os.path.exists(mcp_dir):
        print(f"Error: Could not find {mcp_dir}")
        exit(1)
        
    snapshot_mcp_to_markdown(mcp_dir, output_md, excludes)
