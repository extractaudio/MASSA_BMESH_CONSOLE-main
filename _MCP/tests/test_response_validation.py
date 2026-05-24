import contextlib
import unittest
from unittest import mock

from blmcp.tools import (
    execute_blender_code,
    get_screenshot_of_area_as_image,
    get_screenshot_of_window_as_image,
)


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        del args, kwargs

        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@contextlib.contextmanager
def _synced_path(path):
    yield path


class ResponseValidationTests(unittest.TestCase):
    def test_execute_blender_code_for_cli_rejects_non_dict_result(self):
        fake_mcp = FakeMCP()
        execute_blender_code.register(fake_mcp)
        with mock.patch.object(execute_blender_code, "synced_blend_for_cli", _synced_path):
            with mock.patch.object(execute_blender_code, "run_blender_cli", return_value=[]):
                with self.assertRaises(TypeError) as caught:
                    fake_mcp.tools["execute_blender_code_for_cli"]("scene.blend", "result = []")
        self.assertIn("run_blender_cli returned list", str(caught.exception))

    def test_window_screenshot_rejects_non_dict_tool_result(self):
        fake_mcp = FakeMCP()
        get_screenshot_of_window_as_image.register(fake_mcp)
        with mock.patch.object(
            get_screenshot_of_window_as_image,
            "send_code",
            return_value={"status": "ok", "result": []},
        ):
            with self.assertRaises(TypeError) as caught:
                fake_mcp.tools["get_screenshot_of_window_as_image"]()
        self.assertIn("expected dict result", str(caught.exception))

    def test_area_screenshot_rejects_non_dict_tool_result(self):
        fake_mcp = FakeMCP()
        get_screenshot_of_area_as_image.register(fake_mcp)
        with mock.patch.object(
            get_screenshot_of_area_as_image,
            "send_code",
            return_value={"status": "ok", "result": []},
        ):
            with self.assertRaises(TypeError) as caught:
                fake_mcp.tools["get_screenshot_of_area_as_image"]("VIEW_3D")
        self.assertIn("expected dict result", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
