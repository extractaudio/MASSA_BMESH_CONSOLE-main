from core.server import create_mcp_server
from skills import cartridge_forge, inspector, mechanic, knowledge

mcp = create_mcp_server()

# --- REGISTER TOOLS ---

# Forge
mcp.tool()(cartridge_forge.generate_cartridge)
mcp.tool()(cartridge_forge.iterate_parameters)

# Inspector
mcp.tool()(inspector.session_launch)
mcp.tool()(inspector.scan_telemetry)
mcp.tool()(inspector.scan_slots)
mcp.tool()(inspector.scan_visuals)

# Mechanic
mcp.tool()(mechanic.file_system_edit)
mcp.tool()(mechanic.audit_cartridge)
mcp.tool()(mechanic.audit_console)

# --- REGISTER RESOURCES ---

mcp.resource("massa://protocol/orchestration")(knowledge.get_orchestration)
mcp.resource("massa://protocol/repair")(knowledge.get_repair_protocol)
mcp.resource("massa://protocol/iterate")(knowledge.get_iterate_protocol)
mcp.resource("massa://protocol/generator_workflow")(knowledge.get_generator_workflow)
mcp.resource("massa://protocol/iterator_workflow")(knowledge.get_iterator_workflow)
mcp.resource("massa://protocol/repair_workflow")(knowledge.get_repair_workflow)
mcp.resource("massa://protocol/console_understanding")(knowledge.get_console_understanding)
mcp.resource("massa://protocol/audit_cartridge")(knowledge.get_audit_cartridge_protocol)
mcp.resource("massa://protocol/audit_console")(knowledge.get_audit_console_protocol)

if __name__ == "__main__":
    mcp.run()
