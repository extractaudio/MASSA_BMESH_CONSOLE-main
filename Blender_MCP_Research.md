# MCP Server Research — Blender Integration Reference

> **Purpose**: Structured reference for building a robust MCP server with Blender integration.  
> **Last Updated**: 2026-02-27  
> **Source**: Research synthesis from FastMCP documentation, expert tutorials, and MCP Inspector tooling.

---

## TABLE OF CONTENTS

1. [Gold Standard Stack](#1-gold-standard-stack)
2. [Core Framework — FastMCP & UV](#2-core-framework--fastmcp--uv)
3. [Transport Protocol](#3-transport-protocol)
4. [Security Architecture](#4-security-architecture)
5. [Persistent State & Databases](#5-persistent-state--databases)
6. [Deployment Architecture](#6-deployment-architecture)
7. [Supporting Tools & Libraries](#7-supporting-tools--libraries)
8. [Key Concepts Glossary](#8-key-concepts-glossary)

---

## 1. GOLD STANDARD STACK

| Layer | Technology | Role |
|---|---|---|
| **Tool Framework** | FastMCP | Tool wrappers, JSON-RPC handling, resource/prompt definitions |
| **Async HTTP** | Starlette | Async HTTP middleware, CORS configuration |
| **Auth** | Keycloak / Stitch | Full OAuth 2.1 Bearer Token authentication |
| **JWT Decoding** | python-jose | Decode JWT tokens, extract `sub` (user ID) claim |
| **State / ORM** | SQLAlchemy + SQLite/PostgreSQL | Session and state persistence |
| **Cloud DB** | Cosmos DB | NoSQL alternative for cloud deployments |
| **Package Mgr** | uv | Fast Python project + virtual environment manager |
| **Tunneling** | ngrok | Expose local HTTP server to public URL |
| **Design Pattern** | Modular Tools | One Python function = one Blender action → returns structured JSON |

---

## 2. CORE FRAMEWORK — FastMCP & UV

**FastMCP** is the recommended Python framework for MCP servers.

- Acts as a wrapper that auto-handles the underlying **JSON-RPC protocol**
- Natively defines **tools**, **prompts**, and **resources**
- Integrates with **Starlette** for async HTTP and CORS middleware
- Has built-in support for **BearerAuthProvider** (OAuth 2.1)

**uv** is the recommended package/environment manager:

```bash
uv init          # initialize project
uv run           # run the FastMCP server
```

### What is Starlette?

Starlette is a lightweight Python ASGI library used **under the hood by FastMCP** for HTTP transport.

| Starlette Responsibility | Detail |
|---|---|
| Request/Response handling | `starlette.requests`, `starlette.responses` |
| CORS Middleware | Controls which domains, credentials, and methods can connect |
| Async Routing | Enables non-blocking HTTP request handling |

---

## 3. TRANSPORT PROTOCOL

| Transport | Use Case | Notes |
|---|---|---|
| **stdio** | Local testing, IDE integrations (Cursor, Windsurf) | Simple, no networking required |
| **HTTP** | Remote / multi-client production servers | Requires ngrok if running locally |
| **SSE** (Server-Sent Events) | Streaming responses to clients | Allows real-time push from server to client |

> [!IMPORTANT]  
> For a publicly accessible or multi-client Blender MCP server, use **HTTP or SSE** transport — not stdio.

---

## 4. SECURITY ARCHITECTURE

Three tiers of access control, ordered by complexity:

### Tier 1 — Network Isolation (Simplest)

- Deploy inside a **private network**, disable public ingress
- Best for: internal-only, single-team use

### Tier 2 — Key-Based Access

- Client sends `Authorization: Bearer <key>` or custom header (e.g. `x-functions-key`)
- Use **Azure API Management** for automated key issuance, rotation, and revocation
- Rules:
  - Never hardcode keys — use `os.getenv()` + `.env` files via `python-dotenv`
  - Store client-side keys in VS Code's local secret store
  - Rotate immediately if exposed

### Tier 3 — OAuth 2.1 (Most Robust)

```
[MCP Client] → [Authorization Server (Keycloak/Stitch/Entra)] → [FastMCP Server]
```

| FastMCP Auth Provider | When to Use | Requirement |
|---|---|---|
| `RemoteOAuthProvider` | IdP supports Dynamic Client Registration (DCR) — e.g. ScaleKit, Keycloak | None |
| `OAuthProxy` | IdP lacks DCR support — e.g. Microsoft Entra | Persistent DB (Cosmos DB) to store client IDs |
| `BearerAuthProvider` | Simple bearer token auth — e.g. Stitch | Domain + Project IDs via env vars |

**Accessing User Identity in Tools:**

```python
# FastMCP injects `ctx` into tool functions after auth
async def my_tool(ctx):
    token = ctx.access_token
    payload = jose.decode(token, ...)   # python-jose
    user_id = payload["sub"]            # Never use client ID as user ID
```

> [!WARNING]  
> Always use the `sub` claim from the JWT as the true User ID. The client application ID is NOT the user.

### Securing Outbound API Calls

```python
import os
api_key = os.getenv("EXTERNAL_API_KEY")   # Never hardcode

try:
    response = requests.get(url, headers={"Authorization": f"Bearer {api_key}"})
    response.raise_for_status()
except requests.HTTPError as e:
    return {"error": "External API failed"}   # Don't leak tracebacks
```

---

## 5. PERSISTENT STATE & DATABASES

| Option | Type | Use Case |
|---|---|---|
| **SQLAlchemy + SQLite** | ORM + local file DB | Simple state, RAG data, scene states |
| **SQLAlchemy + PostgreSQL** | ORM + relational DB | Multi-user production |
| **Cosmos DB** | NoSQL cloud | Azure deployments, storing OAuth client IDs |

**SQLAlchemy pattern:**

```python
# Map Python class → DB table
class SceneState(Base):
    __tablename__ = "scenes"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    data = Column(JSON)
```

---

## 6. DEPLOYMENT ARCHITECTURE

```
[Public Internet]
       │
[Azure API Management / ngrok tunnel]
       │
[Private Network]
       │
[Azure Container Apps → FastMCP Server]
       │
[Blender Python Addon / Socket Bridge]
```

- Containerize the FastMCP server (Docker → Azure Container Apps)
- **Disable public ingress** at the container level
- Gate all access through API Management or an identity proxy

---

## 7. SUPPORTING TOOLS & LIBRARIES

### Environment & Package Management

| Tool | Command | Purpose |
|---|---|---|
| `uv` | `uv init` / `uv run` | Fast Python env + dependency management |
| `python-dotenv` | `os.getenv()` | Load `.env` secrets at runtime |

### Networking & Tunneling

| Tool | Purpose |
|---|---|
| `ngrok` | `ngrok http 8000` — exposes localhost to public URL for HTTP transport |

### Testing & Validation Clients

| Tool | How to Use |
|---|---|
| **MCP Inspector** | Native MCP debugging tool |
| **Postman** | Create "New MCP" connection using `uv run` command |
| **Cursor / Windsurf** | IDE hosts via `mcp.json` config file (stdio) |
| **Claude Code** | CLI: `claude mcp add` — test tool calls in terminal |

### Auth & Identity Libraries

| Library | Purpose |
|---|---|
| `python-jose` | Decode JWTs, extract `sub` claim |
| **Keycloak** | Open-source, Docker-deployable OAuth 2.1 Identity Provider |
| **Stitch** | Managed consumer authentication IdP |
| **Microsoft Entra** | Enterprise IdP (requires OAuthProxy — no native DCR) |

### Frontend (OAuth Consent Screen)

| Tool | Purpose |
|---|---|
| React + Vite | Spin up a consent/login UI if acting as your own IdP |

```bash
npm create vite@latest my-auth-ui
```

---

## 8. KEY CONCEPTS GLOSSARY

| Term | Definition |
|---|---|
| **FastMCP** | Python framework that wraps JSON-RPC protocol; defines tools, prompts, resources |
| **Starlette** | Python ASGI web library used under FastMCP for async HTTP + CORS |
| **MCP** | Model Context Protocol — standard for AI ↔ tool server communication |
| **stdio transport** | Communication via standard input/output; local only |
| **HTTP/SSE transport** | Communication over network; supports remote + multi-client |
| **OAuth 2.1** | Authorization protocol; delegates identity verification to an Auth Server |
| **DCR** | Dynamic Client Registration — MCP clients self-register with the auth server |
| **JWT** | JSON Web Token — signed token containing user identity claims |
| **`sub` claim** | The "subject" field in a JWT — the true unique User ID |
| **BearerAuthProvider** | FastMCP class for simple bearer token auth |
| **RemoteOAuthProvider** | FastMCP class for IdPs with native DCR support |
| **OAuthProxy** | FastMCP class for IdPs without DCR; stores client IDs in a DB |
| **ngrok** | Tunnel tool that gives localhost a public HTTPS URL |
| **uv** | Ultra-fast Python package + virtual environment manager |
| **SQLAlchemy** | Python ORM — maps Python classes to database tables |
| **python-jose** | Python library for decoding and verifying JWTs |
| **Keycloak** | Open-source Identity Provider; deployable via Docker |
| **PRM** | Protected Resource Metadata — well-known routes FastMCP auto-creates for auth discovery |
