"""
MASSA MCP bridge — Blender-side socket server.

Wire-compatible with the upstream Blender Lab MCP add-on so the existing
`_MCP/blmcp` client (and all its tools) work unchanged:

  request  : JSON {"type": "execute", "code": str, "strict_json": bool} + "\\0"
             JSON {"type": "ping"} + "\\0"
  response : JSON {"status": "ok"|"error", "result": ..., "message"?: str,
                   "stdout"?: str, "stderr"?: str} + "\\0"

Code is exec'd in a fresh namespace; the convention is that the code assigns a
JSON-serialisable value to ``result`` and may assign a callable
``check_is_finished`` for deferred (long-running) jobs. ``check_is_finished()``
is polled until it returns a non-None value, which becomes the final result.

`bpy` may only be touched from Blender's main thread, so the socket accept loop
runs on a worker thread that *enqueues* jobs; a ``bpy.app.timers`` callback
drains the queue on the main thread and signals each job's completion event.
"""

import contextlib
import io
import json
import os
import queue
import socket
import threading
import traceback

import bpy

_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 9876
_RECV_BUFFER_SIZE = 65536
_TICK_INTERVAL = 0.05  # seconds between main-thread queue drains
_JOB_TIMEOUT = 300.0   # matches the client socket timeout

# Module-level singleton so register/unregister and operators share one server.
_SERVER = None


def get_connection_params():
    host = os.environ.get("BLENDER_MCP_HOST", _DEFAULT_HOST)
    port = int(os.environ.get("BLENDER_MCP_PORT", str(_DEFAULT_PORT)))
    return host, port


class _Job:
    """A single execute request awaiting main-thread processing."""

    __slots__ = ("code", "strict_json", "event", "response", "_check", "_stdout", "_stderr")

    def __init__(self, code, strict_json):
        self.code = code
        self.strict_json = strict_json
        self.event = threading.Event()
        self.response = None
        self._check = None      # deferred check_is_finished callable (if any)
        self._stdout = ""
        self._stderr = ""


def _serialise_response(result, strict_json, stdout, stderr):
    """Build the response dict, honouring strict vs. repr-fallback JSON."""
    payload = {"status": "ok", "result": result}
    if stdout:
        payload["stdout"] = stdout
    if stderr:
        payload["stderr"] = stderr
    try:
        if strict_json:
            json.dumps(payload)
        else:
            payload = json.loads(json.dumps(payload, default=repr))
    except (TypeError, ValueError) as ex:
        return {
            "status": "error",
            "message": "Result is not JSON-serialisable: {:s}".format(str(ex)),
            "stdout": stdout,
            "stderr": stderr,
        }
    return payload


class BridgeServer:
    """Threaded socket server marshalling code execution onto the main thread."""

    def __init__(self):
        host, port = get_connection_params()
        self.host = host
        self.port = port
        self._sock = None
        self._accept_thread = None
        self._jobs = queue.Queue()
        self._running = False

    # --- lifecycle ---------------------------------------------------------

    @property
    def is_running(self):
        return self._running

    def start(self):
        if self._running:
            return False
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(8)
        srv.settimeout(0.5)  # so the accept loop can observe shutdown
        self._sock = srv
        self._running = True
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()
        if not bpy.app.timers.is_registered(self._drain_main_thread):
            bpy.app.timers.register(self._drain_main_thread, persistent=True)
        print("MASSA MCP bridge: listening on {:s}:{:d}".format(self.host, self.port))
        return True

    def stop(self):
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if bpy.app.timers.is_registered(self._drain_main_thread):
            try:
                bpy.app.timers.unregister(self._drain_main_thread)
            except ValueError:
                pass
        print("MASSA MCP bridge: stopped")

    # --- worker thread: accept + per-connection handling -------------------

    def _accept_loop(self):
        while self._running:
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_conn, args=(conn,), daemon=True).start()

    def _handle_conn(self, conn):
        with conn:
            conn.settimeout(_JOB_TIMEOUT)
            try:
                request = self._recv_request(conn)
            except (OSError, ValueError):
                return
            response = self._dispatch(request)
            try:
                conn.sendall((json.dumps(response) + "\0").encode("utf-8"))
            except OSError:
                pass

    @staticmethod
    def _recv_request(conn):
        buf = bytearray()
        while True:
            chunk = conn.recv(_RECV_BUFFER_SIZE)
            if not chunk:
                break
            buf.extend(chunk)
            if b"\0" in buf:
                break
        if not buf:
            raise ValueError("empty request")
        line, _sep, _rest = buf.partition(b"\0")
        return json.loads(line.decode("utf-8"))

    def _dispatch(self, request):
        req_type = request.get("type", "execute")
        if req_type == "ping":
            return {
                "status": "ok",
                "result": {
                    "pong": True,
                    "blender_version": bpy.app.version_string,
                    "massa_loaded": "massa_console" in dir(bpy.types.Scene),
                },
            }
        if req_type != "execute":
            return {"status": "error", "message": "Unknown request type: {!r}".format(req_type)}

        job = _Job(request.get("code", ""), bool(request.get("strict_json", False)))
        self._jobs.put(job)
        if not job.event.wait(timeout=_JOB_TIMEOUT):
            return {"status": "error", "message": "Execution timed out on the Blender main thread"}
        return job.response

    # --- main thread: drain queue, exec, poll deferred jobs ----------------

    def _drain_main_thread(self):
        if not self._running:
            return None  # unregister the timer
        try:
            job = self._jobs.get_nowait()
        except queue.Empty:
            return _TICK_INTERVAL
        try:
            self._run_job(job)
        except Exception:  # pragma: no cover - safety net
            job.response = {"status": "error", "message": traceback.format_exc()}
            job.event.set()
        return _TICK_INTERVAL

    def _run_job(self, job):
        namespace = {"__builtins__": __builtins__}
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                exec(job.code, namespace)  # pylint: disable=exec-used
        except Exception:
            job.response = {
                "status": "error",
                "message": traceback.format_exc(),
                "stdout": out.getvalue(),
                "stderr": err.getvalue(),
            }
            job.event.set()
            return

        check = namespace.get("check_is_finished")
        if callable(check):
            job._check = check
            job._stdout = out.getvalue()
            job._stderr = err.getvalue()
            self._poll_deferred(job)
            return

        result = namespace.get("result")
        job.response = _serialise_response(result, job.strict_json, out.getvalue(), err.getvalue())
        job.event.set()

    def _poll_deferred(self, job):
        """Poll a deferred job's check_is_finished() on a recurring timer."""
        def _tick():
            if not self._running:
                job.response = {"status": "error", "message": "Server stopped before job finished"}
                job.event.set()
                return None
            out = io.StringIO()
            err = io.StringIO()
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    value = job._check()
            except Exception:
                job.response = {"status": "error", "message": traceback.format_exc()}
                job.event.set()
                return None
            job._stdout += out.getvalue()
            job._stderr += err.getvalue()
            if value is None:
                return _TICK_INTERVAL  # still running
            job.response = _serialise_response(value, job.strict_json, job._stdout, job._stderr)
            job.event.set()
            return None

        bpy.app.timers.register(_tick, first_interval=_TICK_INTERVAL)


def start_server():
    global _SERVER
    if _SERVER is None:
        _SERVER = BridgeServer()
    return _SERVER.start()


def stop_server():
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()


def is_running():
    return _SERVER is not None and _SERVER.is_running
