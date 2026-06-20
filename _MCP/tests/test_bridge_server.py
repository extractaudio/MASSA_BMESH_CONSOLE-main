"""
Unit tests for the bundled Blender-side MCP bridge (massa/modules/mcp_bridge/
server.py). A fake ``bpy`` is injected so the job-processing logic (exec,
stdout/stderr capture, strict/non-strict serialisation, deferred
check_is_finished) can be tested without Blender or real sockets.
"""

import importlib.util
import os
import sys
import types
import unittest


_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SERVER_PATH = os.path.join(_REPO, "massa", "modules", "mcp_bridge", "server.py")


def _load_server_with_fake_bpy():
    class _Timers:
        def __init__(self):
            self.registered = []

        def register(self, fn, **_kw):
            self.registered.append(fn)

        def is_registered(self, fn):
            return fn in self.registered

        def unregister(self, fn):
            if fn in self.registered:
                self.registered.remove(fn)

    fake_bpy = types.ModuleType("bpy")
    fake_bpy.app = types.SimpleNamespace(version_string="5.1.0", timers=_Timers())
    fake_bpy.types = types.SimpleNamespace(Scene=type("Scene", (), {}))
    sys.modules["bpy"] = fake_bpy

    spec = importlib.util.spec_from_file_location("massa_mcp_bridge_server", _SERVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, fake_bpy


class BridgeServerTests(unittest.TestCase):
    def setUp(self):
        self.server_mod, self.fake_bpy = _load_server_with_fake_bpy()
        self.srv = self.server_mod.BridgeServer()

    def test_ping_dispatch(self):
        resp = self.srv._dispatch({"type": "ping"})
        self.assertEqual(resp["status"], "ok")
        self.assertTrue(resp["result"]["pong"])
        self.assertEqual(resp["result"]["blender_version"], "5.1.0")

    def test_unknown_type(self):
        resp = self.srv._dispatch({"type": "nope"})
        self.assertEqual(resp["status"], "error")

    def test_execute_sets_result(self):
        job = self.server_mod._Job("result = {'value': 21 * 2}", strict_json=True)
        self.srv._run_job(job)
        self.assertTrue(job.event.is_set())
        self.assertEqual(job.response["status"], "ok")
        self.assertEqual(job.response["result"], {"value": 42})

    def test_execute_captures_stdout(self):
        job = self.server_mod._Job("print('hello'); result = {'ok': True}", strict_json=True)
        self.srv._run_job(job)
        self.assertEqual(job.response["status"], "ok")
        self.assertIn("hello", job.response["stdout"])

    def test_execute_error_is_reported(self):
        job = self.server_mod._Job("raise ValueError('boom')", strict_json=True)
        self.srv._run_job(job)
        self.assertEqual(job.response["status"], "error")
        self.assertIn("boom", job.response["message"])

    def test_strict_json_rejects_unserialisable(self):
        job = self.server_mod._Job("result = {'bad': object()}", strict_json=True)
        self.srv._run_job(job)
        self.assertEqual(job.response["status"], "error")

    def test_non_strict_falls_back_to_repr(self):
        job = self.server_mod._Job("result = {'obj': object()}", strict_json=False)
        self.srv._run_job(job)
        self.assertEqual(job.response["status"], "ok")
        self.assertIsInstance(job.response["result"]["obj"], str)

    def test_deferred_completion(self):
        # Mirrors the calling-convention footer: a callable check_is_finished is
        # polled until it returns a non-None value.
        code = (
            "_state = {'n': 0}\n"
            "def check_is_finished():\n"
            "    _state['n'] += 1\n"
            "    return None if _state['n'] < 2 else {'done': True}\n"
        )
        self.srv._running = True
        job = self.server_mod._Job(code, strict_json=True)
        self.srv._run_job(job)
        # Not finished after the initial exec; a poll tick was registered.
        self.assertFalse(job.event.is_set())
        ticks = self.fake_bpy.app.timers.registered
        self.assertTrue(ticks)
        tick = ticks[-1]
        self.assertEqual(tick(), self.server_mod._TICK_INTERVAL)  # still running
        self.assertIsNone(tick())                                 # second call -> done
        self.assertTrue(job.event.is_set())
        self.assertEqual(job.response["result"], {"done": True})


if __name__ == "__main__":
    unittest.main()
