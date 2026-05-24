# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
MCP server for Blender.

Provides tools for LLM's, connecting to Blender via a bridge-server.
All tools send code to the add-on to run.
"""

__all__ = (
    "main",
)

import argparse
import ipaddress
import importlib
import os
import pkgutil
import traceback
from types import ModuleType

import yaml
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

# NOTE(@ideasman42): this was written to support LLAMA-C++'s Web UI,
# which is one of the nicer ways to run this locally.
# It is not full HTTP support because there looks to be many options for this protocol.
# This could be disabled if it no longer serves its purpose - as most agents wont use STDIO.
_USE_HTTP_SUPPORT = True

_TRANSPORTS = ("stdio", *(("http",) if _USE_HTTP_SUPPORT else ()))
_LOCALHOST_ORIGIN_REGEX = r"https?://(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?"


def _is_loopback_host(host: str) -> bool:
    clean_host = host.strip().lower().strip("[]")
    if clean_host == "localhost":
        return True
    try:
        return ipaddress.ip_address(clean_host).is_loopback
    except ValueError:
        return False


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MCP server for Blender.")
    parser.add_argument(
        "--transport", "-t",
        choices=_TRANSPORTS,
        default="stdio",
        help="Transport protocol (default: stdio).",
    )
    if _USE_HTTP_SUPPORT:
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host to bind to for HTTP transports (default: 127.0.0.1).",
        )
        parser.add_argument(
            "--port", "-p",
            type=int,
            default=8000,
            help="Port to bind to for HTTP transports (default: 8000).",
        )
        parser.add_argument(
            "--allow-unsafe-http",
            action="store_true",
            help=(
                "Allow HTTP on non-loopback hosts and unsafe CORS settings. "
                "This exposes Blender Python execution to the network."
            ),
        )
        parser.add_argument(
            "--cors-origin",
            action="append",
            default=[],
            help=(
                "Exact CORS origin to allow for HTTP transport. May be repeated. "
                "Use '*' only with --allow-unsafe-http."
            ),
        )
    return parser


def _validate_http_security(args: argparse.Namespace, parser: argparse.ArgumentParser) -> dict[str, object]:
    if args.transport != "http":
        return {
            "allow_origins": None,
            "allow_origin_regex": None,
            "enable_dns_rebinding_protection": True,
        }

    if not _is_loopback_host(args.host) and not args.allow_unsafe_http:
        parser.error(
            "HTTP transport may only bind to loopback hosts by default. "
            "Use --allow-unsafe-http to bind to a non-loopback host."
        )

    cors_origins = list(args.cors_origin or [])
    if "*" in cors_origins and not args.allow_unsafe_http:
        parser.error("Wildcard CORS requires --allow-unsafe-http.")

    if "*" in cors_origins:
        allow_origins: list[str] | None = ["*"]
        allow_origin_regex: str | None = None
    elif cors_origins:
        allow_origins = cors_origins
        allow_origin_regex = None
    else:
        allow_origins = None
        allow_origin_regex = _LOCALHOST_ORIGIN_REGEX

    return {
        "allow_origins": allow_origins,
        "allow_origin_regex": allow_origin_regex,
        "enable_dns_rebinding_protection": not args.allow_unsafe_http,
    }


def _registered_tool_count(mcp: FastMCP, fallback: int) -> int:
    tools = getattr(mcp, "tools", None)
    if isinstance(tools, dict):
        return len(tools)

    tool_manager = getattr(mcp, "_tool_manager", None)
    manager_tools = getattr(tool_manager, "_tools", None)
    if isinstance(manager_tools, dict):
        return len(manager_tools)

    return fallback


def _register_health_tool(
    mcp: FastMCP,
    registration_errors: list[dict[str, str]],
    successful_modules: list[str],
) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Get MCP Server Health",
            readOnlyHint=True,
        )
    )
    def get_mcp_server_health() -> dict[str, object]:
        """Return MCP startup health and skipped tool-registration errors."""
        fallback_count = len(successful_modules) + 1
        return {
            "status": "ok" if not registration_errors else "degraded",
            "registered_tool_count": _registered_tool_count(mcp, fallback_count),
            "registered_tool_modules": list(successful_modules),
            "tool_registration_errors": list(registration_errors),
        }


def _register_tools(mcp: FastMCP, tools_pkg: ModuleType) -> None:
    registration_errors: list[dict[str, str]] = []
    successful_modules: list[str] = []

    for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname.endswith("_toolcode") or modname.startswith("_template_"):
            continue
        try:
            mod = importlib.import_module("blmcp.tools.{:s}".format(modname))
            if hasattr(mod, "register"):
                mod.register(mcp)
            successful_modules.append(modname)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            registration_errors.append({
                "module": modname,
                "error_type": type(ex).__name__,
                "message": str(ex),
                "traceback": traceback.format_exc(),
            })

    _register_health_tool(mcp, registration_errors, successful_modules)


def _configure_http_transport(mcp: FastMCP, args: argparse.Namespace, security: dict[str, object]) -> str:
    # pylint: disable-next=import-error,no-name-in-module
    from mcp.server.fastmcp.server import TransportSecuritySettings  # type: ignore[attr-defined]
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.streamable_http_path = "/"
    mcp.settings.stateless_http = True
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=bool(security["enable_dns_rebinding_protection"]),
    )

    _orig = mcp.streamable_http_app

    def _app_with_cors() -> Starlette:
        app = _orig()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=security["allow_origins"] or [],
            allow_origin_regex=security["allow_origin_regex"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return app

    mcp.streamable_http_app = _app_with_cors  # type: ignore[method-assign]
    return "streamable-http"


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()
    http_security = _validate_http_security(args, parser)

    # Load prompts.
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    with open(os.path.join(data_dir, "prompts.yml"), encoding="utf-8") as fh:
        prompts = yaml.safe_load(fh)

    mcp = FastMCP("blender-mcp", instructions=str(prompts["initial_instructions"]))

    # Auto-discover and register all tools (they are never un-registered).
    import blmcp.tools as tools_pkg

    _register_tools(mcp, tools_pkg)

    transport = args.transport
    if _USE_HTTP_SUPPORT and transport == "http":
        transport = _configure_http_transport(mcp, args, http_security)

    mcp.run(transport=transport)
    return 0
