# MCP Bridge Architectures — Single-Threaded Host Integration Blueprint

> **Focus:** How MCP servers bridge async AI agents into the blocking main threads of 3D applications.
> **Date:** 2026-02-28 | **Scope:** Blender, Maya, Unity, Godot

---

## Executive Summary

Every 3D application listed below enforces a **single-threaded execution model** for its scene graph and UI. MCP servers, by contrast, are inherently async (stdio, SSE, or WebSocket transports). Bridging the two requires a universal pattern:

```
┌──────────────┐   transport   ┌──────────────┐   thread-safe   ┌──────────────────┐
│  AI Client   │ ────────────► │  MCP Server   │ ──────queue───► │  Host App Main   │
│ (Claude, etc)│ ◄──────────── │  (async)      │ ◄──result────── │  Thread           │
└──────────────┘               └──────────────┘                  └──────────────────┘
```

The queue mechanism varies per host, but the principle is identical:

1. **Receive** — MCP server receives tool call on its async transport.
2. **Enqueue** — Command is placed into a thread-safe queue.
3. **Poll & Execute** — Host app's main thread polls the queue at idle (timer/tick/deferred) and executes.
4. **Return** — Result is marshalled back to the MCP transport.

---

## 1. Blender — `ahujasid/blender-mcp`

| Field | Value |
|---|---|
| **Repository** | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) |
| **Stars** | ~4.5k |
| **Language** | Python |
| **Target Host** | Blender 3.0+ |
| **Transport** | TCP Socket (JSON-over-TCP, port 9876) |

### Bridge Architecture

```
┌──────────────────┐  stdio   ┌───────────────────┐  TCP socket  ┌─────────────────────────┐
│  AI Client       │ ───────► │  MCP Server        │ ──────────► │  Blender Addon (addon.py)│
│  (Claude Desktop)│          │  (server.py)       │             │   ┌──────────────────┐   │
│                  │          │  Python + FastMCP   │             │   │ BlenderMCPServer │   │
└──────────────────┘          └───────────────────┘             │   └──────────────────┘   │
                                                                 └─────────────────────────┘
```

**Two-process architecture:**

- **Process A** — MCP Server (`server.py`): A standalone Python process launched by the MCP client (Claude Desktop, Cursor). Talks stdio to the AI client and TCP to the Blender addon.
- **Process B** — Blender Addon (`addon.py`): Runs inside Blender's Python interpreter. Opens a TCP socket server on a **daemon background thread**.

### Async-to-Sync Queuing Mechanism

This is the critical bridging pattern. The addon uses **`bpy.app.timers.register()`** to safely marshal execution from a background socket thread onto Blender's main thread:

```python
# In _handle_client() — runs on a BACKGROUND daemon thread
def execute_wrapper():
    try:
        response = self.execute_command(command)
        response_json = json.dumps(response)
        client.sendall(response_json.encode('utf-8'))
    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        client.sendall(json.dumps(error_response).encode('utf-8'))
    return None  # Unregister timer after single execution

# KEY LINE — schedules execute_wrapper on the MAIN thread
bpy.app.timers.register(execute_wrapper, first_interval=0.0)
```

**How it works:**

1. The background `_server_loop()` thread accepts TCP connections.
2. Each client gets a dedicated `_handle_client()` daemon thread.
3. When a JSON command arrives, it wraps the execution in a closure (`execute_wrapper`).
4. `bpy.app.timers.register(fn, first_interval=0.0)` schedules this closure to run on Blender's main thread at the **next available idle tick**.
5. Returning `None` from the timer function automatically **unregisters** it (one-shot execution).

### UI Freeze Prevention

- Commands execute **synchronously** on the main thread once dequeued — there is no chunking or yielding.
- The main thread blocks only for the duration of `execute_command()`.
- For long-running operations (e.g., large mesh generation), the Blender UI **will freeze** momentarily. This is a known limitation of this architecture.
- The socket threads remain alive and accept new connections even while a command is executing on main.

### Stdout/Stderr Capture

- The addon imports `from contextlib import redirect_stdout, suppress` but primarily uses `print()` statements that go to Blender's System Console.
- Errors are caught via `traceback.print_exc()` and the error message is serialized back as a JSON `{"status": "error", "message": str(e)}` over the TCP socket.
- There is **no structured stdout capture mechanism** — output goes to Blender's console and errors return to the MCP client by JSON response.

### Timeout & Crash Prevention

- **Socket timeout:** 1.0s timeout on the server socket `accept()` to allow clean shutdown checks.
- **Client timeout:** `None` (no timeout) — the client handler blocks indefinitely waiting for data.
- **No explicit execution timeout** — if `execute_command()` hangs on the main thread, Blender hangs.
- **Daemon threads:** All threads are `daemon=True`, so they die when Blender exits.
- **Graceful shutdown:** `stop()` method closes socket and joins threads with a 1.0s timeout.

## 1b. Blender — `CommonSenseMachines/blender-mcp`

| Field | Value |
|---|---|
| **Repository** | [CommonSenseMachines/blender-mcp](https://github.com/CommonSenseMachines/blender-mcp) |
| **Stars** | ~1k |
| **Language** | Python |
| **Target Host** | Blender 3.0+ |
| **Transport** | TCP Socket (JSON-over-TCP) |

### Bridge Architecture & Differences

This is an ecosystem-specific integration built on the core `ahujasid/blender-mcp` architecture. It uses the exact same `bpy.app.timers.register()` one-shot closure pattern for thread-marshaling but integrates a specific set of tools for the [CSM.ai](https://csm.ai) pipeline.

### Ecosystem Integration

- **Vision & GenAI Tools:** Integrates text-to-3D, text-to-animation, and direct interaction with the CSM.ai API.
- **Asset Control:** Automatically handles original vs. generated assets (hiding/backing up meshes) directly within the main-thread executor block.
- **UI Panel:** Exposes API key configuration and private asset toggles directly in Blender's 3D Viewport sidebar (`VIEW_3D > UI > BlenderMCP`).

---

## 1c. Blender — `ChrisWilliamson11/blender-assistant-mcp`

| Field | Value |
|---|---|
| **Repository** | [ChrisWilliamson11/blender-assistant-mcp](https://github.com/ChrisWilliamson11/blender-assistant-mcp) |
| **Stars** | ~100 |
| **Language** | Python |
| **Target Host** | Blender 3.0+ |
| **Transport** | HTTP/SSE (Server-Sent Events) |

### Bridge Architecture & Advanced Threading

Unlike the raw TCP socket approach, this repository uses a robust HTTP/SSE transport layer. It also introduces a more advanced threading model designed for "fuzzy automation" and LLM integration.

### Execution Pipeline

The execution architecture explicitly implements a Timeout Watchdog pattern using `threading.Event()`:

1. **Background HTTP Thread:** Receives the requested execution payload via an HTTP `/execute` endpoint.
2. **Event Tracking:** Creates a `threading.Event()` to track the completion state.
3. **Queue onto Main Thread:** `bpy.app.timers.register` schedules the task on Blender's main thread.
4. **Main Thread Execution:** Blender runs the task, captures stdout/results, sets the event flag, and caches the response.
5. **Background Wait:** The HTTP thread waits on the event flag with a configurable timeout. If it times out or completes, it formats the MCP response and returns it over the SSE stream.

### Key Advantages

- **Timeout Resilience:** The explicit `threading.Event().wait(timeout)` prevents the MCP server thread from hanging indefinitely if the Blender main thread gets stuck.
- **RAG & Vision Integration:** Designed to query Blender's API documentation via RAG, injecting contextual info into the prompt cycle before executing commands.

---

## 2. Maya — `PatrickPalmer/MayaMCP`

| Field | Value |
|---|---|
| **Repository** | [PatrickPalmer/MayaMCP](https://github.com/PatrickPalmer/MayaMCP) |
| **Stars** | ~260 |
| **Language** | Python |
| **Target Host** | Autodesk Maya (any version with command port) |
| **Transport** | Maya Command Port (MEL-wrapped Python over TCP) |

### Bridge Architecture

```
┌──────────────────┐  stdio   ┌───────────────────┐  cmd port   ┌──────────────────────┐
│  AI Client       │ ───────► │  MCP Server        │ ──────────► │  Maya Command Port   │
│  (Claude Desktop)│          │  (maya_mcp_server)  │             │  (MEL → Python exec) │
└──────────────────┘          └───────────────────┘             └──────────────────────┘
```

**Single-process MCP server + Maya's built-in command port:**

- No addon/plugin is installed inside Maya.
- The MCP server sends raw Python code to Maya's **command port** (TCP, typically port 7001).
- Maya's command port runs on Maya's **main thread** during idle ticks — providing inherent thread safety.

### Async-to-Sync Queuing Mechanism

Maya's command port is itself the queue. When the port receives data, Maya processes it on the main thread at the next idle moment. This is Maya's native async-to-sync bridge:

```
maya.utils.executeInMainThreadWithResult(callable)
maya.utils.executeDeferred(callable)
```

**MayaMCP's dual-connection pattern:**

1. **Connection 1** — Send Python code wrapped in a MEL `python()` call. The code executes and stores results in `_mcp_maya_results`.
2. **Connection 2** — Read back the value of `_mcp_maya_results`.

This is necessary because Maya's command port running MEL cannot return multi-line Python results in a single connection.

### Namespace Isolation

All injected Python functions/variables are scoped with the `mcp_maya` prefix:

- Functions wrap in `_mcp_maya_scope()` to avoid polluting Maya's global Python interpreter.
- Results stored in `_mcp_maya_results` variable.

### Dynamic Tool Registration

- Tools are not hardcoded — Python files are added to a tools directory.
- The MCP server dynamically inspects function signatures at startup using Python introspection.
- Tool files are pure Maya Python — no MCP decorators required.

### UI Freeze Prevention

- Maya's command port executes on the main thread during idle. If a tool runs long, **Maya's UI freezes**.
- `executeInMainThreadWithResult()` is a blocking call — the calling thread waits for the result.
- For heavy operations, the recommendation is to batch updates rather than making frequent small calls.

### Timeout & Crash Prevention

- **No explicit timeout mechanism** in the MCP server layer.
- Maya can crash if too many rapid `executeInMainThreadWithResult()` calls are queued.
- The dual-connection pattern minimizes namespace pollution risks.

---

## 3. Unity — `igordias2/UnityMCP`

| Field | Value |
|---|---|
| **Repository** | [igordias2/UnityMCP](https://github.com/igordias2/UnityMCP) |
| **Stars** | ~400 |
| **Language** | C# (plugin) + TypeScript (MCP server) |
| **Target Host** | Unity Editor |
| **Transport** | WebSocket (port 8080, JSON messages) |

### Bridge Architecture

```
┌──────────────────┐  stdio   ┌───────────────────┐  WebSocket   ┌─────────────────────────────┐
│  AI Client       │ ───────► │  MCP Server        │ ──────────► │  Unity Editor Plugin (C#)   │
│  (Cursor, Claude)│          │  (TypeScript/Node)  │  port 8080 │   ┌────────────────────┐    │
└──────────────────┘          └───────────────────┘             │   │ Main Thread        │    │
                                                                 │   │ Dispatcher (Update) │    │
                                                                 │   └────────────────────┘    │
                                                                 └─────────────────────────────┘
```

### Async-to-Sync Queuing Mechanism

Unity's API is **strictly main-thread-only**. The plugin uses the standard Unity dispatcher pattern:

```csharp
// Thread-safe queue for main-thread execution
private ConcurrentQueue<Action> _mainThreadQueue = new ConcurrentQueue<Action>();

// Called every frame on the main thread
void Update()
{
    while (_mainThreadQueue.TryDequeue(out Action action))
    {
        action.Invoke();
    }
}

// Called from WebSocket receive handler (background thread)
public void EnqueueOnMainThread(Action action)
{
    _mainThreadQueue.Enqueue(action);
}
```

**How it works:**

1. WebSocket receives a JSON command on a **background thread**.
2. The command is parsed and an `Action` delegate wrapping the execution is **enqueued** into a `ConcurrentQueue<Action>`.
3. Unity's `Update()` (called every frame on the main thread) **drains** the queue and invokes each action.
4. Results are serialized back to JSON and sent over WebSocket.

### C# Code Execution Engine

- The plugin can compile and execute **arbitrary C# code** at runtime.
- Full access to `UnityEngine` and `UnityEditor` APIs.
- Compilation errors are caught and returned as structured error messages.

### UI Freeze Prevention

- Quick commands execute within a single `Update()` frame — negligible UI impact.
- Long-running commands block the main thread during execution. The `Update()` loop resumes once the action completes.
- **No coroutine-based yielding** for long operations in the current architecture.

### Stdout/Stderr Capture

- Comprehensive **logging system** captures Unity's `Debug.Log`, `Debug.LogWarning`, and `Debug.LogError`.
- Logs are buffered and filterable by type, content, and timestamp.
- A `get_logs` tool exposes the log buffer to the MCP client.
- Editor state tracking serializes the full scene hierarchy.

### Timeout & Crash Prevention

- **Command timeout protection** — configurable timeout for execute operations.
- **Automatic reconnection** — WebSocket client handles dropped connections.
- **Connection state monitoring** — debug window shows real-time status.
- **Error boundary** — runtime exceptions in executed code are caught and don't crash the editor.

---

## 4. Unity — `CoderGamester/mcp-unity`

| Field | Value |
|---|---|
| **Repository** | [CoderGamester/mcp-unity](https://github.com/CoderGamester/mcp-unity) |
| **Stars** | ~2.5k |
| **Language** | C# (Unity package) + TypeScript (MCP server) |
| **Target Host** | Unity Editor |
| **Transport** | WebSocket (port 8090, configurable) |

### Bridge Architecture

Same fundamental pattern as UnityMCP, but more mature and configurable:

- **Unity Package** — installable via Unity Package Manager (UPM).
- **Node.js MCP Server** — compiled TypeScript, auto-built by the Unity package.
- **WebSocket bridge** — default port 8090, configurable via the Server Window.

### Enhanced Features Over UnityMCP

| Feature | Detail |
|---|---|
| **Configurable timeout** | Default 10s, adjustable in Server Window. Env var: `UNITY_REQUEST_TIMEOUT` |
| **Remote connections** | Can bind to `0.0.0.0` for cross-machine MCP bridge access |
| **Port configuration** | Env var: `UNITY_PORT` |
| **Logging** | `LOGGING=true` / `LOGGING_FILE=true` for debug capture |
| **WSL2 support** | Three documented solutions for Windows ↔ WSL2 networking |

### Async-to-Sync Mechanism

Same `ConcurrentQueue<Action>` + `Update()` dispatcher pattern as UnityMCP. The WebSocket server in Node.js forwards tool calls to the Unity Editor plugin's WebSocket client, which enqueues onto the main thread.

---

## 5. Godot — `bradypp/godot-mcp`

| Field | Value |
|---|---|
| **Repository** | [bradypp/godot-mcp](https://github.com/bradypp/godot-mcp) |
| **Stars** | ~800 |
| **Language** | TypeScript (MCP server) + GDScript (operations) |
| **Target Host** | Godot 4.x |
| **Transport** | Godot CLI subprocess (no persistent connection) |

### Bridge Architecture

```
┌──────────────────┐  stdio   ┌───────────────────┐  subprocess   ┌─────────────────────────┐
│  AI Client       │ ───────► │  MCP Server        │ ──────────►  │  Godot CLI (headless)    │
│  (Cline, Cursor) │          │  (TypeScript/Node)  │ ◄stdout───── │  godot_operations.gd     │
└──────────────────┘          └───────────────────┘              └─────────────────────────┘
```

**Fundamentally different from the other bridges — no persistent connection to a running host.**

### Async-to-Sync Queuing Mechanism

There is **no queue** in the traditional sense. Instead:

1. **Simple operations** (launch editor, get project info) — direct Godot CLI commands via `child_process.spawn()`.
2. **Complex operations** (create scenes, add nodes) — the MCP server invokes `godot --headless --script godot_operations.gd` as a subprocess with JSON parameters.
3. Godot runs the GDScript, performs file I/O on `.tscn`/`.tres` files, prints JSON results to **stdout**, and **exits**.

```
GodotExecutor.ts  →  spawn('godot', ['--headless', '--script', 'godot_operations.gd', ...])
                  ←  stdout (JSON result)
                  ←  stderr (error output)
```

### Why No Queue Is Needed

Godot's MCP bridge doesn't connect to a running editor session. It operates on **project files** on disk. There's no need to marshal commands to a main thread because:

- Godot runs headless as a subprocess for each operation.
- File-based scene manipulation doesn't require the editor's main loop.
- The `ProcessManager.ts` handles subprocess lifecycle.

### Stdout/Stderr Capture

- **stdout** — captured by the MCP server's `child_process` handler, parsed as JSON.
- **stderr** — captured separately for error reporting.
- Debug output from `godot --headless` is captured and forwarded to the MCP client.

### Timeout & Crash Prevention

- **Process timeout** — subprocess execution has configurable timeouts via `ProcessManager.ts`.
- **No persistent process** — each operation spawns a fresh Godot instance, so crashes don't affect the MCP server.
- **Read-only mode** — a security feature that filters which tools are available, preventing destructive operations.
- **Input validation** — `ParameterNormalizer.ts` sanitizes all inputs before passing to Godot.

---

## 6. Godot — `Coding-Solo/godot-mcp`

| Field | Value |
|---|---|
| **Repository** | [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) |
| **Stars** | ~1.6k |
| **Language** | TypeScript + GDScript |
| **Target Host** | Godot 4.x |
| **Transport** | Godot CLI subprocess |

### Bridge Architecture

Same subprocess-based approach as `bradypp/godot-mcp`. Uses a bundled `godot_operations.gd` script invoked headlessly.

### Key Differences

- Slightly simpler codebase, focused on: launching editor, running projects, capturing debug output.
- Same bundled GDScript architecture: single `godot_operations.gd` accepting JSON params.
- No temporary files — all operations go through the bundled script.

---

## Comparative Analysis

### Queuing Mechanisms Matrix

| Host | Project | Queue Type | Poll Mechanism | Thread Safety |
|------|---------|-----------|----------------|---------------|
| **Blender** | `ahujasid/blender-mcp` | `bpy.app.timers.register()` (one-shot) | Blender idle tick | Timer runs on main thread, closure captures command |
| **Blender** | `CommonSenseMachines/...` | `bpy.app.timers.register()` (one-shot) | Blender idle tick | Same pattern, integrated with CSM.ai tools |
| **Blender** | `ChrisWilliamson11/...` | `bpy.app.timers` + `threading.Event()` | Blender idle tick | Adds timeout limits via `Event.wait(timeout)` |
| **Maya** | `PatrickPalmer/MayaMCP` | Maya command port (built-in) | Maya idle processing | Native — command port is already main-thread |
| **Unity** | `igordias2/UnityMCP` | `ConcurrentQueue<Action>` | `Update()` frame loop | `ConcurrentQueue` is lock-free thread-safe |
| **Unity** | `CoderGamester/mcp-unity` | `ConcurrentQueue<Action>` | `Update()` frame loop | Same pattern, more configurable |
| **Godot** | `bradypp/godot-mcp` | None (subprocess) | N/A (no running host) | Process isolation |
| **Godot** | `Coding-Solo/godot-mcp` | None (subprocess) | N/A (no running host) | Process isolation |

### Transport Layer Comparison

| Host | Transport: AI↔MCP | Transport: MCP↔Host | Encoding |
|------|------------------|---------------------|----------|
| **Blender** | stdio | TCP Socket (`ahujasid`, `CSM`) | JSON over raw TCP |
| **Blender** | HTTP/SSE | HTTP/SSE (`ChrisWilliamson11`) | JSON over HTTP/SSE |
| **Maya** | stdio | Maya Command Port (TCP) | MEL-wrapped Python strings |
| **Unity** | stdio | WebSocket (port 8080/8090) | JSON messages |
| **Godot** | stdio | subprocess stdin/stdout | JSON via CLI args + stdout |

### UI Freeze Risk Assessment

| Host | Risk Level | Mitigation | Long-Op Behavior |
|------|-----------|-----------|-----------------|
| **Blender** | 🟡 Medium | `Event.wait` timeout (`ChrisWilliamson11`) | UI freezes until command completes |
| **Maya** | 🟡 Medium | Batch updates recommended | UI freezes during `executeInMainThreadWithResult` |
| **Unity** | 🟢 Low | Command timeout (configurable) | Timeout kills execution after N seconds |
| **Godot** | 🟢 None | Subprocess isolation | Editor is not connected; no freeze possible |

### Crash Prevention Comparison

| Feature | Blender MCP | MayaMCP | UnityMCP | mcp-unity | Godot MCPs |
|---------|------------|---------|----------|-----------|------------|
| Execution timeout | ❌ (yes for `ChrisWilliamson11`) | ❌ | ✅ | ✅ (10s default) | ✅ (subprocess) |
| Graceful shutdown | ✅ | ✅ | ✅ | ✅ | ✅ (process dies) |
| Error serialization | ✅ JSON | ✅ scoped | ✅ structured | ✅ structured | ✅ JSON stdout |
| Namespace isolation | ❌ | ✅ `_mcp_maya_*` | ✅ (separate plugin) | ✅ (UPM package) | ✅ (process isolation) |
| Reconnection | ❌ manual | ❌ per-session | ✅ auto | ✅ auto | N/A |
| Read-only mode | ❌ | ❌ | ❌ | ❌ | ✅ (`bradypp`) |

---

## Key Architectural Insights for MASSA Integration

### Pattern Recommendation: Blender + `bpy.app.timers`

For the MASSA BMesh Console, the `ahujasid/blender-mcp` pattern is the most directly applicable:

```python
# MASSA-compatible bridging pattern
import queue
import threading
import bpy

# Thread-safe command queue
command_queue = queue.Queue()
result_queue = queue.Queue()

def main_thread_executor():
    """Polled by bpy.app.timers on Blender's main thread."""
    try:
        while not command_queue.empty():
            cmd_id, func, args = command_queue.get_nowait()
            try:
                result = func(*args)
                result_queue.put((cmd_id, {"status": "ok", "result": result}))
            except Exception as e:
                result_queue.put((cmd_id, {"status": "error", "message": str(e)}))
    except queue.Empty:
        pass
    return 0.01  # Poll every 10ms (return None to unregister)

# Register the executor
bpy.app.timers.register(main_thread_executor)
```

### Critical Differences from ahujasid's Approach

| ahujasid Pattern | Recommended MASSA Pattern |
|---|---|
| One-shot timers per command (`return None`) | Persistent polling timer (`return 0.01`) |
| Direct socket send in timer closure | Separate result queue — decouples I/O from execution |
| No execution timeout | Add `threading.Timer` watchdog for stuck commands |
| No queue — just closures | Explicit `queue.Queue` for ordering guarantees |

### Recommended Timeout Watchdog

```python
def execute_with_timeout(func, args, timeout=30.0):
    """Wrap command execution with a timeout watchdog."""
    result = {"status": "timeout", "message": f"Execution exceeded {timeout}s"}
    event = threading.Event()

    def wrapper():
        nonlocal result
        try:
            result = {"status": "ok", "result": func(*args)}
        except Exception as e:
            result = {"status": "error", "message": str(e)}
        finally:
            event.set()

    # Schedule on main thread
    bpy.app.timers.register(wrapper, first_interval=0.0)

    # Wait with timeout on the calling (background) thread
    if not event.wait(timeout=timeout):
        # Timeout — result stays as timeout message
        pass

    return result
```

---

## Repository Index

| # | Repository | Host | URL | Architecture |
|---|-----------|------|-----|-------------|
| 1 | `ahujasid/blender-mcp` | Blender | [Link](https://github.com/ahujasid/blender-mcp) | TCP Socket + `bpy.app.timers` |
| 2 | `CommonSenseMachines/blender-mcp` | Blender | [Link](https://github.com/CommonSenseMachines/blender-mcp) | TCP Socket + CSM API Integration |
| 3 | `ChrisWilliamson11/blender-assistant-mcp` | Blender | [Link](https://github.com/ChrisWilliamson11/blender-assistant-mcp) | HTTP/SSE + Timeout Watchdog |
| 4 | `PatrickPalmer/MayaMCP` | Maya | [Link](https://github.com/PatrickPalmer/MayaMCP) | Command Port (MEL→Python) |
| 5 | `igordias2/UnityMCP` | Unity | [Link](https://github.com/igordias2/UnityMCP) | WebSocket + `ConcurrentQueue` Dispatcher |
| 6 | `CoderGamester/mcp-unity` | Unity | [Link](https://github.com/CoderGamester/mcp-unity) | WebSocket + `ConcurrentQueue` + Timeout |
| 7 | `bradypp/godot-mcp` | Godot | [Link](https://github.com/bradypp/godot-mcp) | Subprocess + Bundled GDScript |
| 8 | `Coding-Solo/godot-mcp` | Godot | [Link](https://github.com/Coding-Solo/godot-mcp) | Subprocess + Bundled GDScript |
