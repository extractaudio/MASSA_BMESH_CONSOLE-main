
import os
import glob
from typing import Dict, List, Optional
from core.server import mcp
from core.workflow import WorkflowEngine
from config import settings

# Global Engine Instance
# We use a single global instance to maintain state across tool calls.
# In a multi-user environment, this would need to be session-keyed.
_ENGINE = WorkflowEngine()

@mcp.tool()
def list_available_workflows() -> str:
    """
    Lists all available workflows in the .agent/workflows directory.
    """
    if not os.path.exists(settings.AGENT_WORKFLOWS_DIR):
        return "Workflow directory not found."
        
    files = glob.glob(os.path.join(settings.AGENT_WORKFLOWS_DIR, "*.md"))
    filenames = [os.path.basename(f) for f in files]
    
    return f"Available Workflows:\n" + "\n".join(filenames)

@mcp.tool()
def start_workflow(workflow_name: str) -> str:
    """
    Starts an interactive workflow session.
    
    Args:
        workflow_name: The name of the workflow file (e.g., 'WF_Cart_Repair.md'). 
                       Fuzzy matching is attempted if exact name not found.
    
    Returns:
        The content of the first step of the workflow.
    """
    target_path = os.path.join(settings.AGENT_WORKFLOWS_DIR, workflow_name)
    
    # Try exact match
    if not os.path.exists(target_path):
        # Try appending .md
        if os.path.exists(target_path + ".md"):
            target_path += ".md"
        else:
            # Try fuzzy search
            files = glob.glob(os.path.join(settings.AGENT_WORKFLOWS_DIR, "*.md"))
            matches = [f for f in files if workflow_name.lower() in os.path.basename(f).lower()]
            
            if len(matches) == 1:
                target_path = matches[0]
            elif len(matches) > 1:
                return f"Ambiguous name '{workflow_name}'. Logic matched: {[os.path.basename(f) for f in matches]}"
            else:
                return f"Workflow '{workflow_name}' not found in {settings.AGENT_WORKFLOWS_DIR}"

    final_name = os.path.basename(target_path)
    return _ENGINE.load_workflow(final_name, target_path)

@mcp.tool()
def next_step() -> str:
    """
    Advances the current workflow to the next step.
    """
    return _ENGINE.next_step()

@mcp.tool()
def previous_step() -> str:
    """
    Returns to the previous step in the current workflow.
    """
    return _ENGINE.previous_step()

@mcp.tool()
def get_workflow_status() -> str:
    """
    Returns the current status of the active workflow (Step X/Y).
    """
    return _ENGINE.get_status()
