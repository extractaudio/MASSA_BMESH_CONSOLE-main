import os
from typing import Literal
from ..config import settings
from core.server import mcp

def _read_doc(filename):
    path = os.path.join(settings.DOCS_DIR, filename)
    if not os.path.exists(path):
        # Fallback to AGENT_WORKFLOWS_DIR if not yet moved?
        path = os.path.join(settings.AGENT_WORKFLOWS_DIR, filename)
    
    if os.path.exists(path):
        with open(path, "r") as f: return f.read()
    return f"Error: Document {filename} not found."

@mcp.tool()
def consult_documentation(
    topic: Literal[
        "ORCHESTRATION", 
        "REPAIR_PROTOCOL", 
        "ITERATION_LOGIC", 
        "GENERATOR_WORKFLOW", 
        "ITERATOR_WORKFLOW", 
        "REPAIR_WORKFLOW", 
        "CONSOLE_UNDERSTANDING", 
        "AUDIT_CARTRIDGE", 
        "AUDIT_CONSOLE"
    ]
) -> str:
    """
    Retrieves specific documentation and workflows for the Massa BMesh Console.
    Use this to understand protocols, error handling, and architectural rules.
    """
    mapping = {
        "ORCHESTRATION": "WF_MCP_ORCHESTRATION.md",
        "REPAIR_PROTOCOL": "WF_DEBUG_PROTOCOLS.md",
        "ITERATION_LOGIC": "WF_ITERATION_LOGIC.md",
        "GENERATOR_WORKFLOW": "WF_UNIFIED_Cart_Generator.md",
        "ITERATOR_WORKFLOW": "WF_UNIFIED_Cart_Iterator.md",
        "REPAIR_WORKFLOW": "WF_Cart_Repair.md",
        "CONSOLE_UNDERSTANDING": "WF_Console_Understanding.md",
        "AUDIT_CARTRIDGE": "audit_cartridge.md",
        "AUDIT_CONSOLE": "audit_console.md"
    }
    return _read_doc(mapping[topic])
