# MCP Server Research Prompts

---

## `Prompt 1:` The Transport & Split-Architecture Analyst

Focus: Infrastructure, Split-Brain Proxies, IPC Latency, and Transport Layers
Output File: mcp_transport_analysis.md

Plaintext
**Role & Objective:** You are an expert backend architecture analyzer. Your task is to perform a deep-dive scrape of GitHub (specifically targeting directories like awesome-mcp-servers and mcpmarket.com) for at least 15 open-source projects implementing the Model Context Protocol (MCP).

**Instructions:**

1. **Targeted Discovery:** Seek out MCP implementations, particularly those utilizing a "split-brain" or proxy architecture (e.g., a Node.js/TypeScript server communicating with a Python backend).
2. **Transport & IPC Diagnosis:** Thoroughly dissect the codebase to determine the underlying transport layer between the client, the MCP server, and the host application.
    - How are they handling the public transport (SSE, HTTP, STDIO)?
    - More importantly, how are they handling Inter-Process Communication (IPC) if the server is split? Are they using `aiohttp` REST, WebSockets, ZeroMQ, or raw sockets for high-speed local bridging?
3. **Concurrency Models:** Analyze their asynchronous handling. How do they manage high-frequency tool calls without dropping packets?
4. **Output Formatting:** Create a comprehensive markdown report (`mcp_transport_analysis.md`). Include:
    - Repository Name & URL
    - Core Language & Frameworks
    - Detailed analysis of their Transport AND internal IPC mechanisms
    - Any exposed networking challenges, latency issues, or payload size limits noted in their issues/PRs

---

## `Prompt 2:` The Host Bridge & Main-Thread Scout

Focus: Single-Threaded Host Integration, Execution Queues, and UI Safety
Output File: mcp_bridge_architectures.md

Plaintext
**Role & Objective:** You are a systems integration specialist. Your task is to scrape GitHub for MCP projects that act as a bridge into heavy, single-threaded applications (specifically look for game engines or 3D software like Blender, Maya, Unity, or Godot).

**Instructions:**

1. **Bridge Mechanism Analysis:** Investigate exactly how these projects bridge the async MCP server to the target app's blocking execution thread.
    - Find implementations of thread-safe execution queues (e.g., Python's `queue.Queue`).
    - How do they poll this queue on the main thread? (e.g., `bpy.app.timers`, `asyncio` event loops embedded in the host, or custom tick-event handlers).
2. **Context Switching & I/O:** - How do they prevent the host UI from freezing during long-running LLM tool executions?
    - How do they capture standard output (stdout/stderr) from the host app and pipe it back to the MCP server securely?
3. **Output Formatting:** Create a blueprint report (`mcp_bridge_architectures.md`). Include:
    - Repository Name, URL, and Target Host Application
    - A technical breakdown of their bridging architecture, specifically detailing their async-to-sync queuing mechanism.
    - Analysis of how they handle execution timeouts and crash prevention.

---

## `Prompt 3:` The Context Window & Dynamic Discovery Optimizer

Focus: Type-Hint Reflection, LRU Caches, and Cartridge Systems
Output File: mcp_context_management.md

Plaintext
**Role & Objective:** You are an LLM context optimization researcher. Your task is to scour GitHub for advanced MCP implementations that dynamically manage massive tool ecosystems without overflowing the LLM's context window.

**Instructions:**

1. **Dynamic Schema Generation:** Look for projects (especially in Python) that automatically generate MCP JSON Schemas at runtime.
    - Do they use decorators (e.g., `@mcp.tool`) and the `inspect` module to parse type hints and docstrings?
2. **Context Management & Eviction:** Search for implementations of module switching, "cartridge" loading, or namespaces.
    - How do they filter the `tools/list` response?
    - Do they use Least Recently Used (LRU) caches to dynamically evict older tools when loading new ones?
3. **Output Formatting:** Generate a state management report (`mcp_context_management.md`). Include:
    - Repository Name & URL
    - Code examples of their dynamic tool registration and schema parsing logic.
    - Specific caching or eviction strategies used to minimize the payload sent to the LLM.

---

## `Prompt 4:` The Process Lifecycle & Subprocess Auditor

Focus: PID Tracking, Zombie Process Prevention, and Local Auth Bypasses
Output File: mcp_security_lifecycle.md

Plaintext
**Role & Objective:** You are a DevSecOps expert. Your task is to evaluate GitHub for robust MCP servers, focusing on process supervision and multi-language lifecycle management.

**Instructions:**

1. **Lifecycle & Subprocess Management:** Find projects where a host application spawns the MCP server as a child process (e.g., via `subprocess.Popen`).
    - How do they handle PID tracking?
    - What mechanisms exist to prevent zombie processes and orphaned ports (e.g., port 3001 remaining locked) if the host application crashes unexpectedly? Do they use SIGINT/SIGTERM hooks across language boundaries?
2. **Security Layers:** - How do they secure remote execution (OAuth, API keys)?
    - Do they implement local development flags (e.g., `OMIT_AUTH`) to allow IDEs seamless local access while keeping remote endpoints locked?
3. **Output Formatting:** Compile an audit report (`mcp_security_lifecycle.md`). Include:
    - Repository Name & URL
    - Detailed analysis of its process lifecycle management, specifically how it cleans up child processes and frees ports on host termination.
    - Breakdown of its authentication architecture.
