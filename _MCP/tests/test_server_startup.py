import contextlib
import io
import types
import unittest
from unittest import mock

import blmcp


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = {
                "func": func,
                "args": args,
                "kwargs": kwargs,
            }
            return func

        return decorator


class ServerStartupTests(unittest.TestCase):
    def _parse(self, argv):
        parser = blmcp._build_arg_parser()
        return parser, parser.parse_args(argv)

    def test_default_transport_is_stdio(self):
        _parser, args = self._parse([])
        self.assertEqual(args.transport, "stdio")

    def test_loopback_http_is_allowed_by_default(self):
        parser, args = self._parse(["--transport", "http", "--host", "127.0.0.1"])
        settings = blmcp._validate_http_security(args, parser)
        self.assertTrue(settings["enable_dns_rebinding_protection"])
        self.assertIsNone(settings["allow_origins"])
        self.assertIsNotNone(settings["allow_origin_regex"])

    def test_non_loopback_http_requires_explicit_unsafe_flag(self):
        parser, args = self._parse(["--transport", "http", "--host", "0.0.0.0"])
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                blmcp._validate_http_security(args, parser)

    def test_non_loopback_http_can_be_explicitly_allowed(self):
        parser, args = self._parse(
            ["--transport", "http", "--host", "0.0.0.0", "--allow-unsafe-http"]
        )
        settings = blmcp._validate_http_security(args, parser)
        self.assertFalse(settings["enable_dns_rebinding_protection"])

    def test_wildcard_cors_requires_unsafe_flag(self):
        parser, args = self._parse(["--transport", "http", "--cors-origin", "*"])
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                blmcp._validate_http_security(args, parser)

    def test_registration_errors_are_reported_by_health_tool(self):
        fake_package = types.SimpleNamespace(__path__=["fake-tools"])
        good_module = types.SimpleNamespace(
            register=lambda mcp: mcp.tool()(lambda: {"status": "ok"})
        )

        def import_module(name):
            if name.endswith(".broken"):
                raise RuntimeError("boom")
            return good_module

        module_infos = [
            (None, "healthy", False),
            (None, "broken", False),
            (None, "ignored_toolcode", False),
            (None, "_template_ignored", False),
        ]
        fake_mcp = FakeMCP()
        with mock.patch.object(blmcp.pkgutil, "iter_modules", return_value=module_infos):
            with mock.patch.object(blmcp.importlib, "import_module", side_effect=import_module):
                blmcp._register_tools(fake_mcp, fake_package)

        self.assertIn("get_mcp_server_health", fake_mcp.tools)
        health = fake_mcp.tools["get_mcp_server_health"]["func"]()
        self.assertEqual(health["status"], "degraded")
        self.assertEqual(health["registered_tool_count"], 2)
        self.assertEqual(len(health["tool_registration_errors"]), 1)
        self.assertEqual(health["tool_registration_errors"][0]["module"], "broken")


if __name__ == "__main__":
    unittest.main()
