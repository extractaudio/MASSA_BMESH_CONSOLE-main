"""
Live integration test for the MASSA fluency tools.

Requires a running Blender with the MASSA addon and its MCP bridge started
(3D View > Massa panel > 'Start' next to MCP Server, or
``bpy.ops.massa.mcp_bridge_start()``). The whole module is SKIPPED when the
bridge is unreachable, so it is safe to run in CI / offline.

Run with the bridge up:
    uv run python -m unittest tests.test_massa_integration -v
"""

import unittest

import blmcp
import blmcp.tools as tools_pkg
from blmcp.tools_helpers import connection


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = {"func": func, "args": args, "kwargs": kwargs}
            return func

        return decorator


def _bridge_reachable():
    try:
        connection.ping(timeout=2.0)
        return True
    except ConnectionError:
        return False


@unittest.skipUnless(_bridge_reachable(), "Blender MCP bridge not reachable on localhost:9876")
class MassaIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mcp = FakeMCP()
        blmcp._register_tools(cls.mcp, tools_pkg)
        cls.spawned = None

    @classmethod
    def tearDownClass(cls):
        # Best-effort cleanup of whatever we spawned.
        if cls.spawned:
            try:
                from blmcp.tools_helpers.connection import send_code
                send_code(
                    "import bpy\n"
                    "o = bpy.data.objects.get({!r})\n".format(cls.spawned)
                    + "result = {'ok': True}\n"
                    "if o: bpy.data.objects.remove(o, do_unlink=True)\n",
                    strict_json=False,
                )
            except Exception:
                pass

    def _call(self, name, **kwargs):
        return self.mcp.tools[name]["func"](**kwargs)

    @staticmethod
    def _inner(resp):
        """Unwrap the bridge envelope to the toolcode result dict."""
        assert resp.get("status") == "ok", resp
        return resp["result"]

    def test_ping(self):
        out = self._call("blender_ping")
        self.assertTrue(out["reachable"], out)

    def test_full_cartridge_loop(self):
        # 1. Discover cartridges
        carts = self._inner(self._call("massa_list_cartridges"))
        self.assertEqual(carts["status"], "ok", carts)
        self.assertTrue(carts["cartridges"], "no cartridges discovered")
        cart_id = carts["cartridges"][0]["id"]

        # 2. Discover its parameters
        prm = self._inner(self._call("massa_get_cartridge_parameters", cartridge_id=cart_id))
        self.assertEqual(prm["status"], "ok", prm)
        self.assertIsInstance(prm["parameters"], list)

        # 3. Spawn it
        spawn = self._inner(self._call("massa_spawn_cartridge", cartridge_id=cart_id))
        self.assertEqual(spawn["status"], "ok", spawn)
        obj_name = spawn["object_name"]
        self.assertTrue(obj_name)
        type(self).spawned = obj_name

        # 4. Slot meta resolves (socket slot may be None for some cartridges)
        meta = self._inner(self._call("massa_get_slot_meta", object_name=obj_name))
        self.assertEqual(meta["status"], "ok", meta)
        self.assertIsInstance(meta["slots"], dict)

        # 5. Mode + programmatic selection
        mode = self._inner(self._call("massa_set_mode", object_name=obj_name, mode="EDIT", select_mode=["FACE"]))
        self.assertEqual(mode["status"], "ok", mode)
        sel = self._inner(self._call("massa_select_geometry", object_name=obj_name, select_by="ALL", domain="FACE"))
        self.assertEqual(sel["status"], "ok", sel)
        self.assertGreater(sel["selected_count"], 0)

        # 6. Material slots manageable
        slots = self._inner(self._call("massa_manage_material_slots", object_name=obj_name, action="LIST"))
        self.assertEqual(slots["status"], "ok", slots)

        # 7. Live re-run (regenerates in place)
        self._call("massa_set_mode", object_name=obj_name, mode="OBJECT")
        rerun = self._inner(self._call("massa_rerun_cartridge", object_name=obj_name))
        self.assertEqual(rerun["status"], "ok", rerun)
        type(self).spawned = rerun["object_name"]


if __name__ == "__main__":
    unittest.main()
