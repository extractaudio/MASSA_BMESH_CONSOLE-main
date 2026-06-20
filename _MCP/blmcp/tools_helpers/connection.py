# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Socket client for communicating with the Blender add-on.

Used by MCP "tools" that send-code to the Blender add-on.
"""

__all__ = (
    "get_connection_params",
    "ping",
    "send_code",
)

import json
import os
import socket
import time

_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 9876
_TIMEOUT = 300.0
_RECV_BUFFER_SIZE = 65536

# Bounded reconnect for *transient* failures (refused/reset) only. The first
# attempt is immediate; subsequent attempts back off. Kept small so a genuinely
# down Blender still fails fast with a clear error.
_CONNECT_RETRIES = int(os.environ.get("BLENDER_MCP_CONNECT_RETRIES", "3"))
_CONNECT_BACKOFF = float(os.environ.get("BLENDER_MCP_CONNECT_BACKOFF", "0.25"))


def get_connection_params() -> tuple[str, int]:
    host = os.environ.get("BLENDER_MCP_HOST", _DEFAULT_HOST)
    port = int(os.environ.get("BLENDER_MCP_PORT", str(_DEFAULT_PORT)))
    return host, port


def _round_trip(request_obj: dict[str, object], timeout: float) -> dict[str, object]:
    """
    Send one null-delimited JSON request and read one null-delimited response.

    Retries the *connect* step a bounded number of times for transient errors
    (connection refused/reset) — e.g. Blender mid-restart or the server just
    coming up. Read timeouts are not retried (the request may have run).

    Raises ``ConnectionError`` when Blender is unreachable or returns an
    invalid response.
    """
    host, port = get_connection_params()
    request = (json.dumps(request_obj) + "\0").encode("utf-8")

    last_transient: OSError | None = None
    for attempt in range(_CONNECT_RETRIES):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
                sock.sendall(request)

                # Read response until the null byte delimiter.
                buf = bytearray()
                while True:
                    chunk = sock.recv(_RECV_BUFFER_SIZE)
                    if not chunk:
                        break
                    buf.extend(chunk)
                    if b"\0" in buf:
                        break
            break
        except (ConnectionRefusedError, ConnectionResetError) as ex:
            # Transient: the server may not have finished binding. Back off and retry.
            last_transient = ex
            if attempt < _CONNECT_RETRIES - 1:
                time.sleep(_CONNECT_BACKOFF * (attempt + 1))
                continue
            raise ConnectionError(
                "Cannot connect to Blender at {:s}:{:d} after {:d} attempts. "
                "Ensure Blender is running with the MASSA addon enabled and the "
                "MCP server started.".format(host, port, _CONNECT_RETRIES)
            ) from ex
        except socket.timeout as ex:
            raise ConnectionError(
                "Blender connection timed out at {:s}:{:d}".format(host, port)
            ) from ex
        except OSError as ex:
            # NOTE: intentionally not catching `Exception` here.
            # Callers use `ConnectionError` to trigger a fallback path;
            # a broader catch would mask real bugs as connection failures.
            raise ConnectionError(
                "Socket error communicating with Blender at {:s}:{:d}: {:s}".format(host, port, str(ex))
            ) from ex
    else:  # pragma: no cover - loop always breaks or raises
        raise ConnectionError(str(last_transient))

    if not buf:
        raise ConnectionError("Empty response from Blender")

    # Parse only up to the first null byte delimiter.
    line, _sep, _rest = buf.partition(b"\0")
    try:
        response: dict[str, object] = json.loads(line.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as ex:
        raise ConnectionError(
            "Invalid response from Blender at {:s}:{:d}: {:s}".format(host, port, str(ex))
        ) from ex
    return response


def send_code(code: str, strict_json: bool) -> dict[str, object]:
    """
    Send Python code to the Blender add-on socket server for execution.

    Returns the full response dict from the add-on containing
    ``status`` (``"ok"`` or ``"error"``), ``result`` (on success),
    ``message`` (on error), and optionally ``stdout``/``stderr``
    captured during execution.

    Raises ``ConnectionError`` when Blender is unreachable or
    returns an invalid response.
    """
    return _round_trip(
        {"type": "execute", "code": code, "strict_json": strict_json},
        timeout=_TIMEOUT,
    )


def ping(timeout: float = 5.0) -> dict[str, object]:
    """
    Lightweight liveness check for the Blender-side bridge.

    Returns the bridge's ``ping`` response (``{"pong": True, ...}``) without
    executing any user code. Raises ``ConnectionError`` if unreachable.
    """
    return _round_trip({"type": "ping"}, timeout=timeout)
