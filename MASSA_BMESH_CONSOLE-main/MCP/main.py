from core.server import create_mcp_server
from skills import cartridge_forge, inspector, mechanic, knowledge, blender_ops, workflow_runner, scene_creator

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
mcp.tool()(inspector.audit_cartridge_geometry)
mcp.tool()(inspector.audit_console)

# Mechanic
mcp.tool()(mechanic.file_system_edit)

# Blender Ops
mcp.tool()(blender_ops.get_scene_info)
mcp.tool()(blender_ops.get_object_info)
mcp.tool()(blender_ops.get_viewport_screenshot)
mcp.tool()(scene_creator.create_scene)
mcp.tool()(blender_ops.execute_blender_code)
mcp.tool()(blender_ops.create_bmesh_object)
mcp.tool()(blender_ops.execute_contextual_op)
mcp.tool()(blender_ops.edit_node_graph)
mcp.tool()(blender_ops.inspect_evaluated_data)
mcp.tool()(blender_ops.manage_action_slots)
mcp.tool()(blender_ops.query_asset_browser)
mcp.tool()(blender_ops.configure_eevee_next)

# Workflow Engine
mcp.tool()(workflow_runner.start_workflow)
mcp.tool()(workflow_runner.next_step)
mcp.tool()(workflow_runner.previous_step)
mcp.tool()(workflow_runner.get_workflow_status)
mcp.tool()(workflow_runner.list_available_workflows)

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
