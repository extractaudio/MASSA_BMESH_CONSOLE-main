# MCP Security & Process Lifecycle Audit Report

> **Date:** 2026-02-28
> **Focus:** PID Tracking, Zombie Process Prevention, Local Auth Bypasses
> **Scope:** Open-source MCP server implementations on GitHub

---

## Executive Summary

This audit evaluates **10 prominent MCP repositories** for robustness in process supervision, multi-language lifecycle management, and authentication architecture. The findings reveal that **zombie process prevention is the single largest unsolved problem** in the MCP ecosystem, with multiple high-profile projects (Goose, vLLM, openai/codex, hapi) filing critical bugs around orphaned child processes. Authentication follows a dual pattern: **OAuth 2.1 for remote endpoints** and a contentious **`DANGEROUSLY_OMIT_AUTH` flag** for local development.

---

## 1. modelcontextprotocol/python-sdk

| Field | Value |
|---|---|
| **URL** | [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) |
| **Language** | Python (asyncio / anyio) |
| **Transport** | stdio, SSE, Streamable HTTP |

### Process Lifecycle Analysis

The Python SDK's `stdio_server()` in `src/mcp/server/stdio.py` uses an **`anyio` task group** as an `@asynccontextmanager`. Two coroutines (`stdin_reader`, `stdout_writer`) are spawned inside `anyio.create_task_group()`. When the context manager exits, the task group automatically **cancels all child tasks** — this is the primary cleanup mechanism.

```python
async with anyio.create_task_group() as tg:
    tg.start_soon(stdin_reader)
    tg.start_soon(stdout_writer)
    yield read_stream, write_stream
    # ← Exit here cancels both tasks
```

**PID Tracking:** The server itself does *not* track PIDs — it **is** the child process. PID tracking responsibility falls on the *client* that spawns it via `StdioServerParameters`.

**Lifespan API:** The SDK provides a `lifespan` context manager for resource init/teardown. However, there is a **known bug on Windows** where code after `yield` in the lifespan handler may not execute because the process is force-killed before cleanup runs.

**Zombie Prevention:**

- ✅ Structured concurrency via `anyio` task groups guarantees coroutine cleanup.
- ⚠️ No OS-level signal handlers (`SIGTERM`/`SIGINT`) are registered in the stdio module itself.
- ❌ No `atexit` hooks, no process group management, no idle timeout.
- ❌ If the host crashes, the server process becomes an orphan. There is no heartbeat/watchdog mechanism.

### Authentication Architecture

- The stdio transport is inherently **local-only** — no network auth needed.
- SSE/Streamable HTTP transports are **delegated to the application layer** — the SDK provides no built-in auth middleware.
- OAuth 2.1 support is specified by the MCP protocol spec but not enforced by the SDK.

---

## 2. modelcontextprotocol/typescript-sdk

| Field | Value |
|---|---|
| **URL** | [github.com/modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) |
| **Language** | TypeScript / Node.js |
| **Transport** | stdio, SSE, Streamable HTTP |

### Process Lifecycle Analysis

The `StdioClientTransport` class spawns an MCP server as a **child process** using Node.js `child_process.spawn()`. It communicates over the child's stdin/stdout.

**PID Tracking:** The PID of the spawned child is accessible via the `ChildProcess` object. The transport holds a reference for lifecycle management.

**Zombie Prevention — Known Issues:**

- **Abrupt termination bug:** `StdioClientTransport` was reported to terminate the server **abruptly**, preventing asynchronous cleanup. The proposed fix: close `stdin` first → wait for graceful exit → `SIGTERM` after timeout → `SIGKILL` if needed.
- **SSEServerTransport leak:** `SSEServerTransport` was reported to not call `res.end()` on cleanup, leaving SSE connections dangling.
- **No `disconnect()` on Client:** A feature request exists for an explicit `disconnect()` method to enable connection pooling and prevent resource/memory leaks.

**Best Practices (from MCP spec docs):**

```
Shutdown sequence:
1. Client closes input stream to child process
2. Wait for server to exit
3. SIGTERM if not exited within timeout
4. SIGKILL as last resort
```

### Authentication Architecture

- Same as Python SDK — auth is **application-layer**.
- The spec defines OAuth 2.1 with PKCE for remote endpoints.
- No built-in `OMIT_AUTH` mechanism in the SDK itself.

---

## 3. modelcontextprotocol/inspector

| Field | Value |
|---|---|
| **URL** | [github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) |
| **Language** | TypeScript / Node.js / Express |
| **Transport** | Proxy (SSE ↔ stdio, Streamable HTTP ↔ stdio) |

### Process Lifecycle Analysis

The Inspector is a **visual debugging proxy** that sits between a client (web UI) and an MCP server. It manages transports via `Map<string, Transport>` keyed by session ID.

**PID Tracking:** When connecting to an stdio server, it spawns the server via `StdioClientTransport` and `spawn-rx`'s `findActualExecutable`. The child PID is tracked internally by the transport.

**Zombie Prevention:**

- ⚠️ Session transports are stored in maps (`webAppTransports`, `serverTransports`) but cleanup on unexpected disconnection depends on Express middleware and manual map cleanup.
- ⚠️ No explicit `SIGTERM`/`SIGINT` process signal hooks observed in the main `index.ts`.

### Authentication Architecture — **Most Comprehensive in the Ecosystem**

The Inspector implements a **multi-layered security model**:

| Layer | Mechanism |
|---|---|
| **Session Token** | `randomBytes(32).toString("hex")` — cryptographically random 256-bit token |
| **Token Comparison** | `timingSafeEqual()` — prevents timing side-channel attacks |
| **Origin Validation** | DNS rebinding protection via `ALLOWED_ORIGINS` whitelist |
| **Rate Limiting** | `express-rate-limit` — 100 requests per 15 minutes on `/sandbox` |
| **Header Forwarding** | Selective forwarding of `mcp-*`, `authorization`, custom auth headers |
| **Auth Bypass** | `DANGEROUSLY_OMIT_AUTH` env var |

```typescript
const authDisabled = !!process.env.DANGEROUSLY_OMIT_AUTH;

const authMiddleware = (req, res, next) => {
  if (authDisabled) return next(); // ← Bypass
  
  // ... timingSafeEqual token comparison ...
};
```

> [!CAUTION]
> The `DANGEROUSLY_OMIT_AUTH` flag disables **all** authentication. The Inspector's own README warns this can lead to **remote compromise via malicious websites or ads** even on a local machine, because the proxy binds to a network port accessible from the browser.

---

## 4. mark3labs/mcp-go

| Field | Value |
|---|---|
| **URL** | [github.com/mark3labs/mcp-go](https://github.com/mark3labs/mcp-go) |
| **Language** | Go |
| **Transport** | stdio, SSE, Streamable HTTP |

### Process Lifecycle Analysis

`mcp-go` is the **most mature MCP server framework in Go**. It provides explicit `Shutdown(ctx)` method and built-in signal handling.

**Graceful Shutdown Pattern:**

```go
// From mcp-go examples:
func setupGracefulShutdown(s *MCPServer) {
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    go func() {
        <-sigCh
        ctx, cancel := context.WithTimeout(context.Background(), 28*time.Second)
        defer cancel()
        s.Shutdown(ctx)
    }()
}
```

**Task Lifecycle Management:**

- `taskEntry` structs track: task state, session ID, tool name, creation time, result, error, **cancel function**, and a `done` channel.
- `cancelTask()` calls `cancelFunc()` on the context, decrements `activeTasks`, sends status notification, and fires task hooks.
- `scheduleTaskCleanup()` implements TTL-based cleanup with a 5-minute tombstone window for expired tasks.

**Zombie Prevention:**

- ✅ OS signal handling (`SIGINT`, `SIGTERM`) with graceful shutdown timeout.
- ✅ Context-based cancellation propagates through entire call chain.
- ✅ `sync.Mutex` protects shared task state.
- ✅ `WaitGroup`-style coordination via `done` channels.
- ⚠️ No parent-process heartbeat — if the host dies without signaling, the server persists.

### Authentication Architecture

- The framework itself is **auth-agnostic** — designed for embedding.
- HTTP transport supports middleware chains where developers inject their own auth.
- No built-in OAuth or `OMIT_AUTH` — left to the application layer.

---

## 5. supercorp-ai/supergateway

| Field | Value |
|---|---|
| **URL** | [github.com/supercorp-ai/supergateway](https://github.com/supercorp-ai/supergateway) |
| **Language** | TypeScript / Node.js |
| **Transport** | stdio↔SSE, stdio↔WS, SSE↔stdio, stdio↔StreamableHTTP |

### Process Lifecycle Analysis

Supergateway is a **transport bridge** — it spawns a stdio MCP server and re-exposes it over network transports (SSE, WebSocket, Streamable HTTP).

**Subprocess Spawning:** Uses the `--stdio` argument to specify the child command (e.g., `npx -y @modelcontextprotocol/server-filesystem /`). The child is spawned and its stdin/stdout are piped through the gateway.

**Session Management (Stateful Mode):**

- `--stateful` flag enables per-session stdio process instances.
- `--sessionTimeout` (ms) allows configuring an idle session TTL that auto-terminates sessions.
- When a session expires, the associated stdio subprocess should be terminated.

**Zombie Prevention:**

- ⚠️ The specifics of child process cleanup on gateway crash are not extensively documented.
- ✅ Health endpoints (`--healthEndpoint /healthz`) allow external monitoring to detect and restart hung gateways.
- ⚠️ If the gateway process dies unexpectedly, the stdio child may become an orphan.

### Authentication Architecture

| Mechanism | Implementation |
|---|---|
| **OAuth 2.0 Bearer** | `--oauth2Bearer "token"` adds `Authorization: Bearer <token>` to all outbound requests |
| **Custom Headers** | `--header "x-api-key: ..."` allows arbitrary auth headers |
| **CORS Control** | `--cors` with origin whitelist or regex matching |
| **No built-in OMIT_AUTH** | Auth is pass-through; gateway does not enforce auth on its own endpoints |

---

## 6. block/goose (formerly square/goose)

| Field | Value |
|---|---|
| **URL** | [github.com/block/goose](https://github.com/block/goose) |
| **Language** | Rust / TypeScript |
| **Transport** | stdio |

### Process Lifecycle Analysis — **Critical Bug Case Study**

Goose is an AI agent that spawns MCP servers as child processes. It has been the source of **two major zombie process bugs**:

**Bug #2205: "MCP server processes persist and accumulate across Goose sessions"**

- MCP server child processes were **not cleaned up** after sessions ended or the application closed.
- Zombie/idle MCP processes accumulated over time, consuming system resources.
- Root cause: Missing cleanup hooks on session teardown.

**Bug #6843: VS Code Extension — JSON-RPC client/subprocess disposal**

- JSON-RPC clients and their underlying subprocesses were not properly disposed.
- Recommendation: Keep the client alive for recoverable errors, only dispose on terminal failures.

**Lessons Learned:**

- ❌ Relying on the OS to clean up child processes on host exit is insufficient.
- ❌ Session-scoped process management requires explicit lifecycle tracking.
- ✅ Fix involved adding explicit process termination to session teardown logic.

### Authentication Architecture

- Local-only stdio transport — no network auth.
- Extension-based auth for remote integrations.

---

## 7. openai/codex

| Field | Value |
|---|---|
| **URL** | [github.com/openai/codex](https://github.com/openai/codex) |
| **Language** | TypeScript |
| **Transport** | stdio |

### Process Lifecycle Analysis — **Proposed Idle Cleanup Architecture**

**Issue #12335: "Automatic lifecycle cleanup for completed/idle sub-agents"**

Multi-agent sessions create many long-lived MCP subprocesses, causing **memory accumulation**. The proposed architecture:

```
┌─────────────────────────────────────────────┐
│  Proposed MCP Subprocess Lifecycle Manager  │
├─────────────────────────────────────────────┤
│  1. Auto-close completed sub-agents         │
│  2. Tear down associated MCP clients        │
│  3. Configurable idle timeout policies      │
│  4. Graceful shutdown on unused detection   │
└─────────────────────────────────────────────┘
```

**Key Design Points:**

- Configurable idle timeout (e.g., "kill after 5 min of no tool calls").
- Resource tracking per sub-agent (CPU, memory, open connections).
- Batch cleanup on session end.

### Authentication Architecture

- Uses OpenAI API keys for upstream communication.
- No `OMIT_AUTH` — API keys are always required.

---

## 8. vllm-project/vllm (MCP Integration)

| Field | Value |
|---|---|
| **URL** | [github.com/vllm-project/vllm](https://github.com/vllm-project/vllm) |
| **Language** | Python |
| **Transport** | stdio (embedded) |

### Process Lifecycle Analysis — **GPU Resource Leak**

**Issue #25850: "vLLM subprocesses continue after parent exits via MCP"**

- vLLM workers (GPU-bound processes) continued running after the MCP-integrated parent process exited.
- **GPU memory was not released**, blocking other workloads.
- Root cause: No graceful shutdown API for MCP-spawned subprocesses.

**Impact:**

- Leaked GPU memory can only be recovered by manual `kill -9` of orphan processes.
- In containerized environments, this can cause the entire node to become unusable.

**Requested Fix:** Official graceful shutdown API that sends `SIGTERM` → waits → `SIGKILL` to all worker subprocesses.

---

## 9. hapi (MCP/Gemini Integration)

| Field | Value |
|---|---|
| **URL** | Reported on GitHub (issue #99) |
| **Language** | Python |
| **Transport** | stdio |

### Process Lifecycle Analysis — **Memory Leak via Orphaned Processes**

**Issue #99: "Memory leak: orphaned MCP/Gemini child processes not cleaned up after session ends"**

Root cause analysis identified **five failure modes**:

| # | Failure Mode | Description |
|---|---|---|
| 1 | Untracked child PIDs | MCP processes spawned without recording PID references |
| 2 | Incomplete disconnect logic | Session end does not iterate and kill child processes |
| 3 | Async cleanup in sync exit | Cleanup coroutines scheduled in `atexit` (sync) never run |
| 4 | Unregistered signal handlers | No `SIGTERM`/`SIGINT` handlers on parent process |
| 5 | No `SIGKILL` escalation | `SIGTERM` sent but not followed by `SIGKILL` on timeout |

**Recommended Fix Pattern:**

```python
import signal, atexit, os

child_pids = []

def cleanup():
    for pid in child_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    # Wait 5s, then SIGKILL survivors
    import time; time.sleep(5)
    for pid in child_pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda s, f: (cleanup(), exit(0)))
signal.signal(signal.SIGINT, lambda s, f: (cleanup(), exit(0)))
```

---

## 10. FastMCP (modelcontextprotocol/python-sdk integrated)

| Field | Value |
|---|---|
| **URL** | [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) (FastMCP is now part of the official SDK) |
| **Language** | Python |
| **Transport** | stdio, SSE, Streamable HTTP |

### Process Lifecycle Analysis

FastMCP provides a high-level decorator-based API over the MCP Python SDK.

**Server Lifecycle Phases:**

1. **Initialization** — Resource setup, tool registration
2. **Operation** — Request handling
3. **Shutdown** — Graceful teardown

**Known Issue:** FastMCP SSE transport **fails to shut down properly** after processing at least one request when receiving a termination signal. The event loop or SSE connection keeps the process alive, preventing graceful exit.

**Zombie Prevention:**

- ⚠️ Inherits the Python SDK's limitations (no OS signal handlers in stdio module).
- ⚠️ SSE transport has the additional shutdown bug.
- ❌ No process group management.

### Authentication Architecture

- Auth is **application-layer**, not built into FastMCP itself.
- Developers use ASGI middleware (e.g., Starlette) for OAuth/API key auth.

---

## Cross-Cutting Analysis

### Zombie Process Prevention — Ecosystem Maturity Matrix

| Repository | Signal Handlers | Process Groups | Parent Heartbeat | Idle Timeout | atexit | Overall Grade |
|---|---|---|---|---|---|---|
| python-sdk | ❌ | ❌ | ❌ | ❌ | ❌ | **D** |
| typescript-sdk | ⚠️ (buggy) | ❌ | ❌ | ❌ | N/A | **D+** |
| inspector | ❌ | ❌ | ❌ | ❌ | N/A | **D** |
| mcp-go | ✅ | ❌ | ❌ | ❌ | N/A | **B** |
| supergateway | ❌ | ❌ | ❌ | ✅ (session) | N/A | **C** |
| goose | ❌ (was bug) | ❌ | ❌ | ❌ | ❌ | **D** (improving) |
| openai/codex | ❌ (proposed) | ❌ | ❌ | ❌ (proposed) | ❌ | **D** (proposed) |
| vllm | ❌ | ❌ | ❌ | ❌ | ❌ | **F** |
| hapi | ❌ (was bug) | ❌ | ❌ | ❌ | ❌ | **F** (fixing) |
| FastMCP | ❌ | ❌ | ❌ | ❌ | ❌ | **D** |

### Authentication Architecture — Ecosystem Overview

| Repository | OAuth 2.1 | API Keys | OMIT_AUTH | Origin Validation | Rate Limiting |
|---|---|---|---|---|---|
| python-sdk | Spec only | App-layer | ❌ | ❌ | ❌ |
| typescript-sdk | Spec only | App-layer | ❌ | ❌ | ❌ |
| inspector | ❌ | ✅ (session token) | ✅ (`DANGEROUSLY_OMIT_AUTH`) | ✅ | ✅ |
| mcp-go | App-layer | App-layer | ❌ | ❌ | ❌ |
| supergateway | ✅ (bearer pass-through) | ✅ (header pass-through) | ❌ | ✅ (CORS) | ❌ |
| mcp-remote | ✅ (Okta integration) | ❌ | ❌ | ❌ | ❌ |

---

## Recommendations

### For MCP Server Developers

> [!IMPORTANT]
> **Mandatory: Implement a 3-stage shutdown sequence.**
>
> 1. Close stdin → signal session end
> 2. `SIGTERM` after 5-second grace period
> 3. `SIGKILL` after an additional 5 seconds

### Recommended Defensive Patterns

```python
# Python: Robust MCP subprocess manager
import subprocess, signal, atexit, os, threading

class MCPProcessManager:
    def __init__(self):
        self._children: dict[int, subprocess.Popen] = {}
        self._lock = threading.Lock()
        atexit.register(self._cleanup_all)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def spawn(self, cmd: list[str]) -> subprocess.Popen:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # ← Process group isolation
        )
        with self._lock:
            self._children[proc.pid] = proc
        return proc
    
    def _signal_handler(self, signum, frame):
        self._cleanup_all()
        os._exit(128 + signum)
    
    def _cleanup_all(self):
        with self._lock:
            for pid, proc in list(self._children.items()):
                try:
                    proc.terminate()  # SIGTERM
                except ProcessLookupError:
                    pass
            
            # Grace period
            import time; time.sleep(3)
            
            for pid, proc in list(self._children.items()):
                try:
                    proc.kill()  # SIGKILL
                except ProcessLookupError:
                    pass
            
            self._children.clear()
```

```go
// Go: Recommended pattern (as seen in mcp-go)
func setupGracefulShutdown(server *MCPServer) {
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    go func() {
        sig := <-sigCh
        log.Printf("Received %s, shutting down...", sig)
        ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
        defer cancel()
        if err := server.Shutdown(ctx); err != nil {
            log.Printf("Shutdown error: %v", err)
        }
    }()
}
```

### For IDE/Host Application Developers

1. **Track all child PIDs** in a registry structure.
2. **Implement a parent-process heartbeat**: child MCP servers should periodically check if their parent is alive (e.g., poll `os.getppid()` on Unix, check if stdin is readable).
3. **Use process groups**: Spawn MCP servers with `start_new_session=True` (Python) or `CREATE_NEW_PROCESS_GROUP` (Windows) for batch cleanup.
4. **Implement idle timeout**: Kill MCP servers that haven't received a tool call in N minutes.
5. **Clean up on startup**: Detect and offer to kill orphaned MCP processes from previous sessions.

### For Authentication

> [!WARNING]
> **Never use `DANGEROUSLY_OMIT_AUTH` in any environment reachable from a web browser.** Even on localhost, a malicious webpage can make requests to `http://localhost:6277` and execute arbitrary MCP tool calls if auth is disabled.

1. Always use **OAuth 2.1 with PKCE** for remote endpoints.
2. For local development, use **auto-generated session tokens** (as the Inspector does) rather than disabling auth.
3. Implement **origin validation** to prevent DNS rebinding attacks.
4. Use **`timingSafeEqual`** for all token comparisons to prevent timing side-channels.
5. Apply **rate limiting** to tool-execution endpoints.

---

## Appendix: Key GitHub Issues Referenced

| Project | Issue | Topic |
|---|---|---|
| block/goose | #2205 | Zombie MCP server processes persist across sessions |
| block/goose | #6843 | VS Code extension subprocess disposal |
| openai/codex | #12335 | Auto lifecycle cleanup for idle sub-agents |
| vllm-project/vllm | #25850 | GPU worker subprocesses persist after MCP parent exit |
| hapi | #99 | Memory leak from orphaned MCP/Gemini child processes |
| modelcontextprotocol/typescript-sdk | (multiple) | StdioClientTransport abrupt termination, SSEServerTransport leak, missing `disconnect()` |
| modelcontextprotocol/python-sdk | (multiple) | Windows lifespan cleanup failure, multiprocessing hangs stdio |
