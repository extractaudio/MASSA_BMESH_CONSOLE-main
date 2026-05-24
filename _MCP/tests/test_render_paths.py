import os
import sys
import tempfile
import types
import unittest

from blmcp.tools import render_viewport_to_path_toolcode


class _RenderData:
    def __init__(self):
        self.filepath = "original.blend-render-path"


class _FakeBpy:
    def __init__(self, fail=False):
        self.app = types.SimpleNamespace(background=True)
        self.path = types.SimpleNamespace(abspath=lambda path: os.path.abspath(path))
        self.context = types.SimpleNamespace(
            scene=types.SimpleNamespace(render=_RenderData())
        )
        self.ops = types.SimpleNamespace(
            render=types.SimpleNamespace(render=self._render)
        )
        self.fail = fail
        self.rendered_path = None

    def _render(self, *args, **kwargs):
        del args, kwargs
        self.rendered_path = self.context.scene.render.filepath
        if self.fail:
            raise RuntimeError("render failed")


class RenderPathTests(unittest.TestCase):
    def setUp(self):
        self._old_bpy = sys.modules.get("bpy")

    def tearDown(self):
        if self._old_bpy is None:
            sys.modules.pop("bpy", None)
        else:
            sys.modules["bpy"] = self._old_bpy

    def test_viewport_render_uses_exact_output_path_and_creates_parent(self):
        fake_bpy = _FakeBpy()
        sys.modules["bpy"] = fake_bpy
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "nested", "viewport.png")
            result = render_viewport_to_path_toolcode.main(
                render_viewport_to_path_toolcode.Params(output_path=output_path)
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.filepath, os.path.abspath(output_path))
        self.assertEqual(fake_bpy.rendered_path, os.path.abspath(output_path))
        self.assertEqual(fake_bpy.context.scene.render.filepath, "original.blend-render-path")

    def test_viewport_render_restores_filepath_on_error(self):
        fake_bpy = _FakeBpy(fail=True)
        sys.modules["bpy"] = fake_bpy
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "nested", "viewport.png")
            result = render_viewport_to_path_toolcode.main(
                render_viewport_to_path_toolcode.Params(output_path=output_path)
            )

        self.assertEqual(result.status, "error")
        self.assertEqual(result.message, "render failed")
        self.assertEqual(fake_bpy.context.scene.render.filepath, "original.blend-render-path")


if __name__ == "__main__":
    unittest.main()
