"""
Registers every real tool module against a fake MCP and asserts they all load
without error — this exercises the actual imports and ``*_toolcode.py`` loading
(template includes, calling-convention wrapping) for all tools, including the
MASSA fluency tools, without needing a live Blender.
"""

import unittest

import blmcp
import blmcp.tools as tools_pkg


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = {"func": func, "args": args, "kwargs": kwargs}
            return func

        return decorator


# Tools added by this overhaul; must all be present and error-free.
_NEW_TOOLS = (
    "blender_ping",
    "massa_get_cartridge_parameters",
    "massa_get_slot_meta",
    "massa_set_mode",
    "massa_select_geometry",
    "massa_rerun_cartridge",
    "massa_manage_material_slots",
)


class ToolRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.mcp = FakeMCP()
        blmcp._register_tools(self.mcp, tools_pkg)
        self.health = self.mcp.tools["get_mcp_server_health"]["func"]()

    def test_no_registration_errors(self):
        self.assertEqual(
            self.health["status"], "ok",
            msg="Tool registration errors: {!r}".format(self.health["tool_registration_errors"]),
        )

    def test_new_tools_are_registered(self):
        for name in _NEW_TOOLS:
            self.assertIn(name, self.mcp.tools, "Missing tool: {:s}".format(name))


if __name__ == "__main__":
    unittest.main()
