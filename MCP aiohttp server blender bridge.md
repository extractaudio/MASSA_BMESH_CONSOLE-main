# Building the High-Speed Async MCP-Blender Bridge

This guide outlines the step-by-step process for an AI agent team (Gemini 3 + Claude Opus) to reconstruct the MCP Core Blender Bridge and Node.js Inspector Server from scratch. It is designed to be executed sequentially, with built-in tests to verify the foundation before moving to the next layer.

## Architecture Overview

You are building a split-brain system:

1. **Node.js Console (The Brain):** An MCP-compliant server running in Node.js (TypeScript) that exposes tools to the LLM via STDIO or Streamable HTTP/SSE. It manages dynamic tool discovery, OAuth, and a "cartridge" system for context window management.
2. **Blender Python Addon (The Body):** A high-speed `aiohttp` server running inside Blender that receives JSON payloads, pushes them to a thread-safe execution queue, and executes them on Blender's main thread via `bpy.app.timers`. It registers tools using a custom `FastMCP` decorator.

---

## Step 1: Project Initialization & Structure

**Objective:** Set up the basic directories, package files, and Python addon manifest for Blender 4.2+.

* **Node.js:** Initialize a standard TypeScript project (`package.json`, `tsconfig.json`). Install essential dependencies: `express`, `axios`, `@modelcontextprotocol/sdk` (if using official SDK components, though custom transport is fine), `cors`, and types.
* **Python:** Create a standard Blender Addon structure (`bl_info` or `blender_manifest.toml`). Create an `__init__.py` and a basic `mcp_receiver.py` file.

**Audit 1:** Verify Node.js compiles empty TS files and the Blender Addon can be enabled/disabled in the Blender Preferences without errors.

---

## Step 2: The FastMCP Tool Decorator (Python)

**Objective:** Implement a Python decorator to automatically generate JSON Schema definitions from type hints. This is critical for dynamic tool discovery.

* Create `fast_mcp.py`.
* Implement a `@mcp.tool(cartridge="Name")` decorator.
* The decorator must inspect the function signature (using the `inspect` module) and map Python types (`int`, `str`, `float`, `bool`) to JSON Schema types.
* It should capture the docstring as the tool description.
* Store all registered tools in a central registry dictionary within the module.

**Audit 2:** Write a dummy function `def add(a: int, b: int) -> int: """Adds numbers"""`, decorate it, and print the generated JSON Schema to ensure it matches MCP tool specification requirements.

---

## Step 3: High-Speed Async HTTP Receiver (Python)

**Objective:** Build the Blender-side server using `aiohttp` to ensure non-blocking, high-concurrency network communication.

* In `mcp_receiver.py`, implement an `aiohttp.web.Application`.
* Create a `POST /execute` endpoint.
* The server must run in a dedicated background thread (using `threading.Thread` and `asyncio.new_event_loop()`) to avoid freezing Blender's UI.
* Bind the server to `127.0.0.1:8081`.

**Audit 3:** Start the addon in Blender. Use `curl -X POST http://127.0.0.1:8081/execute -d '{"ping": "pong"}'`. The server should log the request and return a 200 OK without locking the Blender viewport.

---

## Step 4: The Thread-Safe Execution Queue (Python)

**Objective:** Bridge the async network thread to Blender's single-threaded API safely. This is the most common failure point in Blender automation.

* Create a global `queue.Queue` in Python.
* When the `aiohttp` `/execute` endpoint receives a payload (e.g., `{ "tool": "add", "args": {"a": 1, "b": 2} }`), it constructs an execution task and pushes it to the queue.
* Crucially, the HTTP request handler must then wait on a *result* queue specific to that request (implement a timeout, e.g., 60s).
* Create a function `execute_code_in_main_thread()` that polls the main queue.
* Register this function with `bpy.app.timers.register(..., first_interval=0.05)`. This function will pull tasks from the queue, execute the corresponding registered FastMCP tool, and push the result back to the specific result queue.

**Audit 4:** Send a request to `/execute` that calls a tool to create a Cube in Blender (`bpy.ops.mesh.primitive_cube_add()`). If Blender crashes or throws a "Context is incorrect" error, the execution is not happening on the main thread. Fix the queue/timer loop.

---

## Step 5: Node.js Bridge Client & Core Tools (TypeScript)

**Objective:** Build the HTTP client in Node.js that talks to Blender, and implement the static "Core" tools.

* Create `blender_bridge.ts`. Implement `sendCommandToBlender(toolName: string, args: any)` using `axios` to send `POST` requests to `localhost:8081/execute`.
* Implement a custom JSON delimiter extraction (e.g., `<<<MASSA_JSON>>>`) if you plan to capture stdout from Python execution for error handling.
* Create the core static tools in Node.js: `load_cartridge`, `list_cartridges`, `session_launch` (pinging Blender), and `run_python_script` (sending raw `{code: "..."}` payloads instead of tool names).

**Audit 5:** Run a Node script that calls `session_launch` (which uses the bridge to ping Blender). It should succeed and return the Blender version.

---

## Step 6: Dynamic Cartridge System & Discovery (TypeScript)

**Objective:** Implement the system that asks Blender for all its tools at startup and organizes them into an LRU-cache cartridge system to save LLM context window space.

* Create `cartridges.ts`. Define a `MAX_ACTIVE_CARTRIDGES = 3` limit. The "ConsoleCore" cartridge (from Step 5) is immune to eviction.
* Create `dynamic_loader.ts`. On Node server startup, it sends a command to Blender (via `run_python_script`) to execute a function that returns all registered tools from the FastMCP registry (Step 2).
* Parse the returned JSON schemas and dynamically register them in Node.js, mapping them to the `cartridge` tag defined in the Python decorator.
* Implement auto-loading logic: When the LLM calls a tool, check which cartridge it belongs to and load it (evicting the oldest if necessary) before forwarding the call to Blender.

**Audit 6:** Start the Node server. It should connect to Blender, pull the list of tools, and log something like "Discovered 15 tools across 3 cartridges."

---

## Step 7: The MCP Server & STDIO Transport (TypeScript)

**Objective:** Wrap the Node.js logic into a formal MCP server that IDEs (Cursor/Antigravity) can connect to.

* Create `console.ts`. Implement the standard MCP protocol handlers: `ListToolsRequest` (returns only the tools from currently *loaded* cartridges), and `CallToolRequest` (which routes through the bridge built in Step 5).
* Set up a standard STDIO transport so the Node process can communicate via stdin/stdout with the IDE client.

**Audit 7:** Configure Claude Desktop or Cursor to use your Node script as an MCP server. Open the IDE and ask it to list available tools. It should show the Core tools and the dynamically loaded tools. Ask the LLM to create a sphere in Blender using the tools.

---

## Step 8: Streamable HTTP/SSE & OAuth 2.1 (TypeScript)

**Objective:** Add a secondary transport layer for the MCP Inspector and remote clients, secured by OAuth.

* Create `http_server.ts` using Express. Bind to `0.0.0.0:3001`.
* Implement an in-memory OAuth 2.1 provider (`/authorize`, `/token`, `/register`).
* Implement Streamable HTTP routes: `POST /mcp` (tool execution), `GET /mcp` (SSE stream for server events).
* *Crucial for local dev:* Implement a `DANGEROUSLY_OMIT_AUTH` flag that bypasses OAuth if set to true.
* Ensure the Express server integrates cleanly with the `console.ts` tool dispatch logic.

**Audit 8:** Run the MCP Inspector (`npx @modelcontextprotocol/inspector`). Connect it to `http://127.0.0.1:3001/mcp` (with auth bypassed for testing). Ensure the Inspector UI loads the tools and can execute them successfully.

---

## Step 9: UI & Process Management (Python/Blender)

**Objective:** Create a UI panel in Blender to start/stop the Node server automatically.

* In `mcp_receiver.py`, add a Blender `Panel` (e.g., `VIEW3D_PT_MCP_Core`) in the N-panel.
* Add a "Start Core System" operator. This operator should use `subprocess.Popen` to launch the Node.js server (passing the `--http` flag and setting `DANGEROUSLY_OMIT_AUTH=true` as an environment variable).
* Implement PID tracking. Ensure that when Blender closes, the Node subprocess is killed gracefully to prevent zombie processes blocking port 3001.
* Add a "Start Inspector" operator that launches the MCP inspector in the background on port `6274`.

**Audit 9:** Open Blender, click "Start Core System" in the N-panel. Check your task manager to ensure the Node process spawned. Close Blender. Check the task manager to ensure the Node process died.

---

## Step 10: Final Integration Audit & Hardening

**Objective:** End-to-end verification of the asynchronous flow and safety measures.

* **Async Test:** Write a Blender Python script that takes 5 seconds to run (e.g., simulating heavy geometry calculation with `time.sleep()`). Call it via the MCP Inspector. During those 5 seconds, the Node server must remain responsive, and Blender should ideally process the queue without completely freezing the OS window (though the main thread will block on the heavy calculation, the HTTP thread remains open).
* **Context Test:** Have the agent load a new cartridge, call a tool, and observe the LRU eviction mechanism working in the Node console logs.
* **Error Handling:** Intentionally send a malformed Python script. Ensure the error is caught on the Blender side, packaged nicely in JSON, and returned to the LLM so it can correct its mistake, rather than crashing the HTTP server.

**Final Delivery:** You now have a high-speed, dynamic, and context-aware MCP bridge to Blender.
