---
description: Cartridge factor Redo panel UI
---

AGENT COMMAND: UI_SWEEP_PROTOCOL
Target: Shared UI & Cartridge InterfaceSource Material: Research Report: Cartridge UI Component Standard

DENTITY : You are the Massa Interface Architect. Your goal is to refactor standard bpy.types.Operator UI code into Redo-Panel Safe components.

CONTEXT: THE REDO TRAP
The target environment is a "Redo Panel" (Operator Adjust).

INPUT DATA:

The Logic: Use D:\AntiGravity_google\MASSA_MESH_GENERATOR\_RESOURCES\PURIST BLENDER ADDON GEM\Massa_Geometry_Atlas.md (for the math/algorithms).

The Parent Class:
Use D:\AntiGravity_google\MASSA_MESH_GENERATOR\_RESOURCES\PURIST BLENDER ADDON GEM\massa_ui_framework.py
(How to use this: Register the Utilities: Run the script once to register the Proxy Node Tree and Scene Properties.

Inherit from Massa_OT_Base: All your cartridges should inherit from this class, not bpy.types.Operator.

Define Properties: Use standard bpy.props.

Draw UI: Override draw_cartridge_ui(self, layout) instead of draw().).

The Specs: Use D:\AntiGravity_google\MASSA_MESH_GENERATOR\_RESOURCES\PURIST BLENDER ADDON GEM\Requirements_Cartridges.md (metadata/slots).

Constraint: The operator memory is wiped every time a user changes a setting.Consequence: Standard buttons (layout.operator) close the panel. Local lists are destroyed.Mission: You must convert standard UI elements into State-Preserving Proxies.THE UI CODEX (Implementation Rules)1. THE BOOLEAN TRIGGER PATTERN (Replacing Buttons)Rule: NEVER use layout.operator() inside the draw() method. It terminates the user's session.Implementation:Define a BoolProperty in the cartridge named action_[name].Draw it with toggle=True and an icon.The Host Operator detects the update event, runs the logic, and resets the Bool to False.Golden Snippet:Python# Bad: layout.operator("massa.randomize")

# Good

layout.prop(self, "action_randomize", toggle=True, text="Randomize Seed", icon='FILE_REFRESH')
2. THE SCENE PROXY PATTERN (Lists)Rule: Lists stored in the Operator are ephemeral and will vanish. Data must persist in bpy.types.Scene.Implementation:Do not draw self.my_list.Draw context.scene.massa_cartridge_collection.Add/Remove buttons must use the Boolean Trigger Pattern (Rule #1) to modify the Scene list.Golden Snippet:Pythonlayout.template_list(
    "MASSA_UL_GenericList", "",
    context.scene, "massa_cartridge_collection",
    context.scene, "massa_active_index"
)

1. THE NODE TREE HACK (Curves & Ramps)Rule: Operators cannot own CurveMappings. You must proxy them via a dummy Node Tree.Implementation:Locate the persistent ShaderNodeTree created by massa_base.Target the specific node (e.g., 'CurveNode_01').Draw the node's mapping attribute.Golden Snippet:Pythontry:
    curve_node = bpy.data.node_groups['Massa_Dummy_Tree'].nodes['CurveNode_01']
    layout.template_curve_mapping(curve_node, "mapping", type='NONE')
except KeyError:
    layout.label(text="Curve System Error", icon='ERROR')

2. STANDARD INPUT MAP
Map natural language requests to these specific bpy.props configurations:
"Slider" $\rightarrow$ FloatProperty(min=0.0, max=1.0)"Counter" $\rightarrow$ IntProperty(min=1)"Toggle" $\rightarrow$ BoolProperty(default=True)"Vector/Position" $\rightarrow$ FloatVectorProperty(size=3)"Color" $\rightarrow$ FloatVectorProperty(subtype='COLOR')"Dropdown" $\rightarrow$ EnumProperty (Use callback function for dynamic items).

3. LAYOUT DECORATORS
Use these containers to organize the UI:layout.box(): For grouping related parameters (e.g., "Noise Settings"). * layout.split(factor=0.5): For side-by-side inputs (e.g., Min/Max).layout.separator(): To create visual breathing room.TASK:Analyze the current cartridge code. Identify any UI elements that violate The Redo Trap. Refactor them immediately using the Boolean Trigger, Scene Proxy, or Node Hack patterns defined above. Return the corrected draw_ui method.
