# A2A Protocol Deep Research

> This document is a comprehensive export of the A2A Protocol documentation from https://a2a-protocol.org/latest/.

# Page: /

## Home

Agent2Agent (A2A) Protocol

## What is A2A Protocol?

<p>Welcome to the official documentation for the Agent2Agent (A2A) Protocol, an open standard designed to enable seamless communication and collaboration between AI agents.</p> <p>Originally developed by Google and now donated to the Linux Foundation, A2A provides the definitive common language for agent interoperability in a world where agents are built using diverse frameworks and by different vendors.</p> <p>Build with  ADK (or any framework), equip with  MCP (or any tool), and communicate with  A2A, to remote agents, local agents, and humans.</p>

## Get started with A2A

<ul> <li> <p> Video Intro in &lt;8 min</p> <p></p> </li> <li> <p> Course DeepLearning.AI - Intro to A2A</p> <p></p> </li> <li> <p> Read the Introduction</p> <p>Understand the core ideas behind A2A.</p> <p> What is A2A?</p> <p> Key Concepts</p> </li> <li> <p> Dive into the Specification</p> <p>Explore the detailed technical definition of the A2A protocol.</p> <p> Protocol Specification</p> </li> <li> <p> Follow the Tutorials</p> <p>Build your first A2A-compliant agent with our step-by-step Python quickstart.</p> <p> Python Tutorial</p> <p> Walkthrough with AI Agent Frameworks</p> </li> <li> <p> Explore Code Samples</p> <p>See A2A in action with sample clients, servers, and agent framework integrations.</p> <p> GitHub Samples</p> </li> <li> <p> Download the Official SDKs</p> <p> Python</p> <p> JavaScript</p> <p> Java</p> <p> C#/.NET</p> <p> Golang</p> </li> </ul>

## Why use the A2A Protocol

<pre><code>graph LR
    User(🧑‍💻 User) &lt;--&gt; ClientAgent(🤖 Client Agent)
    ClientAgent --&gt; A2A1(**↔️ A2A**) --&gt; RemoteAgent1(🤖 Remote Agent 1)
    ClientAgent --&gt; A2A2(**↔️ A2A**) --&gt; RemoteAgent2(🤖 Remote Agent 2)

    style User fill:#fdebd0,stroke:#e67e22,stroke-width:2px
    style ClientAgent fill:#d6eaf8,stroke:#3498db,stroke-width:2px
    style RemoteAgent1 fill:#d6eaf8,stroke:#3498db,stroke-width:2px
    style RemoteAgent2 fill:#d6eaf8,stroke:#3498db,stroke-width:2px
    style A2A1 fill:#ebedef,stroke:#909497,stroke-width:2px
    style A2A2 fill:#ebedef,stroke:#909497,stroke-width:2px</code></pre> <ul> <li> <p> Interoperability</p> <p>Connect agents built on different platforms (LangGraph, CrewAI, Semantic Kernel, custom solutions) to create powerful, composite AI systems.</p> </li> <li> <p> Complex Workflows</p> <p>Enable agents to delegate sub-tasks, exchange information, and coordinate actions to solve complex problems that a single agent cannot.</p> </li> <li> <p> Secure &amp; Opaque</p> <p>Agents interact without needing to share internal memory, tools, or proprietary logic, ensuring security and preserving intellectual property.</p> </li> </ul>

## How does A2A work with MCP?

<p>A2A and Model Context Protocol (MCP) are complementary standards for building robust agentic applications:</p> <ul> <li>Model Context Protocol (MCP): Provides agent-to-tool communication. It's a complementary standard that standardizes how an agent connects to its tools, APIs, and resources to get information.</li> <li>IBM ACP: Incorporated into the A2A Protocol</li> <li>Cisco agntcy: A framework that provides components to the Internet of Agents with discovery, group communication, identity and observability and leverages A2A and MCP for agent communication and tool calling.</li> <li>A2A: Provides agent-to-agent communication. As a universal, decentralized standard, A2A acts as the public internet that allows ai agents—including those using MCP, or built with frameworks like agntcy—to interoperate, collaborate, and share their findings.</li> </ul>

---

# Page: /community/

## A2A Community Hub

<p>Welcome to the official community hub for the Agent2Agent (A2A) protocol! A2A is an open, standardized protocol that enables seamless interoperability and collaboration between AI agents across all frameworks and vendors.</p>

## Recent News &amp; Blog Posts

<p>Stay up-to-date with the latest announcements, tutorials, and insights from the A2A team and our community.</p> <ul> <li>Announcing Agent Payments Protocol (AP2) - September 16</li> <li>A2A Extensions Empowering Custom Agent Functionality - September 9</li> <li>A2A protocol: Demystifying Tasks vs Messages - August 18</li> <li>End-to-end evaluation of multi-agent systems on Vertex AI - August 7</li> <li>Agent2Agent (A2A) protocol is getting an upgrade - July 26</li> </ul>

## Use Case Highlights

<p>A2A unlocks powerful new ways for AI agents to collaborate and solve complex problems. Here are a few examples of what's possible:</p> <ul> <li>Multi-Agent Workflows: Chain specialized agents together to automate complex processes, like candidate sourcing for hiring or streamlining supply chain logistics.</li> <li>Agent Marketplaces: Create platforms where agents can discover and utilize the capabilities of other agents from different providers.</li> <li>Cross-Platform Integration: Connect agents built on different frameworks—like LangGraph, BeeAI, and more—to work together seamlessly.</li> <li>Evaluating Multi-Agent Systems: Use frameworks like Vertex AI to assess the performance and success of collaborative agent trajectories.</li> </ul>

## Featured Contributions

<p>A2A is an open-source protocol, and we thrive on community contributions. A huge thank you to everyone who has helped build and improve A2A! Here are some recent highlights:</p> <ul> <li>Python Quickstart Tutorial (PR#202)</li> <li>LlamaIndex sample implementation (PR#179)</li> <li>Autogen sample server (PR#232)</li> <li>AG2 + MCP example (PR#230)</li> <li>PydanticAI example (PR#127)</li> </ul>

## The Word on the Street

<p>The launch of A2A has sparked lively discussions and positive reactions across various social and video platforms.</p> <ul> <li>Microsoft's Semantic Kernel: Asha Sharma, Head of AI Platform Product at Microsoft, announced on LinkedIn that "Semantic Kernel now speaks A2A," enabling instant, secure interoperability.</li> <li>Matt Pocock's Diagramming: Well-known developer educator Matt Pocock shared diagrams on X explaining the A2A protocol, which were liked and reposted hundreds of times.</li> <li>Craig McLuckie's "Hot Take": Craig McLuckie shared his thoughts on LinkedIn, highlighting A2A's focus on interactions between agentic systems as a sensible approach.</li> <li>Zachary Huang's Deep Dive: In his YouTube video, Zachary explains how A2A complements MCP, with A2A handling communication between agents and MCP connecting agents to tools.</li> </ul>

## A2A Integrations

<p>These agentic frameworks have built-in A2A integration, making it easy to get started:</p> <ul> <li>Agent Development Kit (ADK)</li> <li>Agno</li> <li>AG2</li> <li>BeeAI Framework</li> <li>CrewAI</li> <li>Hector</li> <li>LangGraph</li> <li>LiteLLM</li> <li>Microsoft Agent Framework</li> <li>Pydantic AI</li> <li>Slide (Tyler)</li> <li>Strands Agents</li> </ul>

## The Future is Interoperable

<p>The excitement surrounding Google's A2A protocol clearly indicates a strong belief in its potential to revolutionize multi-agent AI systems. By providing a standardized way for AI agents to communicate and collaborate, A2A is poised to unlock new levels of automation and innovation. As enterprises increasingly adopt AI agents, A2A represents a crucial step towards realizing the full power of interconnected AI ecosystems.</p> <p>Join the growing community building the future of AI interoperability with A2A!</p>

---

# Page: /definitions/

## A2A Definition/Schema

ProtobufJSON <p>Protobuf The normative A2A protocol definition in Protocol Buffers (proto3 syntax). This is the source of truth for the A2A protocol specification.</p> <p>Download</p> <p>You can download the proto file directly: <code>a2a.proto</code></p> <p>Definition</p> <pre><code>// Older protoc compilers don't understand edition yet.
syntax = "proto3";
package lf.a2a.v1;

import "google/api/annotations.proto";
import "google/api/client.proto";
import "google/api/field_behavior.proto";
import "google/protobuf/empty.proto";
import "google/protobuf/struct.proto";
import "google/protobuf/timestamp.proto";

option csharp_namespace = "Lf.A2a.V1";
option go_package = "google.golang.org/lf/a2a/v1";
option java_multiple_files = true;
option java_outer_classname = "A2A";
option java_package = "com.google.lf.a2a.v1";

// Provides operations for interacting with agents using the A2A protocol.
service A2AService {
  // Sends a message to an agent.
  rpc SendMessage(SendMessageRequest) returns (SendMessageResponse) {
    option (google.api.http) = {
      post: "/message:send"
      body: "*"
      additional_bindings: {
        post: "/{tenant}/message:send"
        body: "*"
      }
    };
  }
  // Sends a streaming message to an agent, allowing for real-time interaction and status updates.
  // Streaming version of `SendMessage`
  rpc SendStreamingMessage(SendMessageRequest) returns (stream StreamResponse) {
    option (google.api.http) = {
      post: "/message:stream"
      body: "*"
      additional_bindings: {
        post: "/{tenant}/message:stream"
        body: "*"
      }
    };
  }

  // Gets the latest state of a task.
  rpc GetTask(GetTaskRequest) returns (Task) {
    option (google.api.http) = {
      get: "/tasks/{id=*}"
      additional_bindings: {
        get: "/{tenant}/tasks/{id=*}"
      }
    };
    option (google.api.method_signature) = "id";
  }
  // Lists tasks that match the specified filter.
  rpc ListTasks(ListTasksRequest) returns (ListTasksResponse) {
    option (google.api.http) = {
      get: "/tasks"
      additional_bindings: {
        get: "/{tenant}/tasks"
      }
    };
  }
  // Cancels a task in progress.
  rpc CancelTask(CancelTaskRequest) returns (Task) {
    option (google.api.http) = {
      post: "/tasks/{id=*}:cancel"
      body: "*"
      additional_bindings: {
        post: "/{tenant}/tasks/{id=*}:cancel"
        body: "*"
      }
    };
  }
  // Subscribes to task updates for tasks not in a terminal state.
  // Returns `UnsupportedOperationError` if the task is already in a terminal state (completed, failed, canceled, rejected).
  rpc SubscribeToTask(SubscribeToTaskRequest) returns (stream StreamResponse) {
    option (google.api.http) = {
      get: "/tasks/{id=*}:subscribe"
      additional_bindings: {
        get: "/{tenant}/tasks/{id=*}:subscribe"
      }
    };
  }

  // (-- api-linter: client-libraries::4232::required-fields=disabled
  //     api-linter: core::0133::method-signature=disabled
  //     aip.dev/not-precedent: method_signature preserved for backwards compatibility --)
  // Creates a push notification config for a task.
  rpc CreateTaskPushNotificationConfig(CreateTaskPushNotificationConfigRequest) returns (TaskPushNotificationConfig) {
    option (google.api.http) = {
      post: "/tasks/{task_id=*}/pushNotificationConfigs"
      body: "config"
      additional_bindings: {
        post: "/{tenant}/tasks/{task_id=*}/pushNotificationConfigs"
        body: "config"
      }
    };
    option (google.api.method_signature) = "task_id,config";
  }
  // Gets a push notification config for a task.
  rpc GetTaskPushNotificationConfig(GetTaskPushNotificationConfigRequest) returns (TaskPushNotificationConfig) {
    option (google.api.http) = {
      get: "/tasks/{task_id=*}/pushNotificationConfigs/{id=*}"
      additional_bindings: {
        get: "/{tenant}/tasks/{task_id=*}/pushNotificationConfigs/{id=*}"
      }
    };
    option (google.api.method_signature) = "task_id,id";
  }
  // Get a list of push notifications configured for a task.
  rpc ListTaskPushNotificationConfigs(ListTaskPushNotificationConfigsRequest) returns (ListTaskPushNotificationConfigsResponse) {
    option (google.api.http) = {
      get: "/tasks/{task_id=*}/pushNotificationConfigs"
      additional_bindings: {
        get: "/{tenant}/tasks/{task_id=*}/pushNotificationConfigs"
      }
    };
    option (google.api.method_signature) = "task_id";
  }
  // Gets the extended agent card for the authenticated agent.
  rpc GetExtendedAgentCard(GetExtendedAgentCardRequest) returns (AgentCard) {
    option (google.api.http) = {
      get: "/extendedAgentCard"
      additional_bindings: {
        get: "/{tenant}/extendedAgentCard"
      }
    };
  }
  // Deletes a push notification config for a task.
  rpc DeleteTaskPushNotificationConfig(DeleteTaskPushNotificationConfigRequest) returns (google.protobuf.Empty) {
    option (google.api.http) = {
      delete: "/tasks/{task_id=*}/pushNotificationConfigs/{id=*}"
      additional_bindings: {
        delete: "/{tenant}/tasks/{task_id=*}/pushNotificationConfigs/{id=*}"
      }
    };
    option (google.api.method_signature) = "task_id,id";
  }
}

// Configuration of a send message request.
message SendMessageConfiguration {
  // A list of media types the client is prepared to accept for response parts.
  // Agents SHOULD use this to tailor their output.
  repeated string accepted_output_modes = 1;
  // Configuration for the agent to send push notifications for task updates.
  PushNotificationConfig push_notification_config = 2;
  // The maximum number of most recent messages from the task's history to retrieve in
  // the response. An unset value means the client does not impose any limit. A
  // value of zero is a request to not include any messages. The server MUST NOT
  // return more messages than the provided value, but MAY apply a lower limit.
  optional int32 history_length = 3;
  // If `true`, the operation MUST wait until the task reaches a terminal state
  // (`COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`) or an interrupted state
  // (`INPUT_REQUIRED`, `AUTH_REQUIRED`) before returning. Default is `false`.
  bool blocking = 4;
}

// `Task` is the core unit of action for A2A. It has a current status
// and when results are created for the task they are stored in the
// artifact. If there are multiple turns for a task, these are stored in
// history.
message Task {
  // Unique identifier (e.g. UUID) for the task, generated by the server for a
  // new task.
  string id = 1 [(google.api.field_behavior) = REQUIRED];
  // Unique identifier (e.g. UUID) for the contextual collection of interactions
  // (tasks and messages). Created by the A2A server.
  string context_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The current status of a `Task`, including `state` and a `message`.
  TaskStatus status = 3 [(google.api.field_behavior) = REQUIRED];
  // A set of output artifacts for a `Task`.
  repeated Artifact artifacts = 4;
  // protolint:disable REPEATED_FIELD_NAMES_PLURALIZED
  // The history of interactions from a `Task`.
  repeated Message history = 5;
  // protolint:enable REPEATED_FIELD_NAMES_PLURALIZED
  // A key/value object to store custom metadata about a task.
  google.protobuf.Struct metadata = 6;
}

// Defines the possible lifecycle states of a `Task`.
enum TaskState {
  // The task is in an unknown or indeterminate state.
  TASK_STATE_UNSPECIFIED = 0;
  // Indicates that a task has been successfully submitted and acknowledged.
  TASK_STATE_SUBMITTED = 1;
  // Indicates that a task is actively being processed by the agent.
  TASK_STATE_WORKING = 2;
  // Indicates that a task has finished successfully. This is a terminal state.
  TASK_STATE_COMPLETED = 3;
  // Indicates that a task has finished with an error. This is a terminal state.
  TASK_STATE_FAILED = 4;
  // Indicates that a task was canceled before completion. This is a terminal state.
  TASK_STATE_CANCELED = 5;
  // Indicates that the agent requires additional user input to proceed. This is an interrupted state.
  TASK_STATE_INPUT_REQUIRED = 6;
  // Indicates that the agent has decided to not perform the task.
  // This may be done during initial task creation or later once an agent
  // has determined it can't or won't proceed. This is a terminal state.
  TASK_STATE_REJECTED = 7;
  // Indicates that authentication is required to proceed. This is an interrupted state.
  TASK_STATE_AUTH_REQUIRED = 8;
}

// A container for the status of a task
message TaskStatus {
  // The current state of this task.
  TaskState state = 1 [(google.api.field_behavior) = REQUIRED];
  // A message associated with the status.
  Message message = 2;
  // ISO 8601 Timestamp when the status was recorded.
  // Example: "2023-10-27T10:00:00Z"
  google.protobuf.Timestamp timestamp = 3;
}

// `Part` represents a container for a section of communication content.
// Parts can be purely textual, some sort of file (image, video, etc) or
// a structured data blob (i.e. JSON).
message Part {
  oneof content {
    // The string content of the `text` part.
    string text = 1;
    // The `raw` byte content of a file. In JSON serialization, this is encoded as a base64 string.
    bytes raw = 2;
    // A `url` pointing to the file's content.
    string url = 3;
    // Arbitrary structured `data` as a JSON value (object, array, string, number, boolean, or null).
    google.protobuf.Value data = 4;
  }
  // Optional. metadata associated with this part.
  google.protobuf.Struct metadata = 5;
  // An optional `filename` for the file (e.g., "document.pdf").
  string filename = 6;
  // The `media_type` (MIME type) of the part content (e.g., "text/plain", "application/json", "image/png").
  // This field is available for all part types.
  string media_type = 7;
}

// Defines the sender of a message in A2A protocol communication.
enum Role {
  // The role is unspecified.
  ROLE_UNSPECIFIED = 0;
  // The message is from the client to the server.
  ROLE_USER = 1;
  // The message is from the server to the client.
  ROLE_AGENT = 2;
}

// `Message` is one unit of communication between client and server. It can be
// associated with a context and/or a task. For server messages, `context_id` must
// be provided, and `task_id` only if a task was created. For client messages, both
// fields are optional, with the caveat that if both are provided, they have to
// match (the `context_id` has to be the one that is set on the task). If only
// `task_id` is provided, the server will infer `context_id` from it.
message Message {
  // The unique identifier (e.g. UUID) of the message. This is created by the message creator.
  string message_id = 1 [(google.api.field_behavior) = REQUIRED];
  // Optional. The context id of the message. If set, the message will be associated with the given context.
  string context_id = 2;
  // Optional. The task id of the message. If set, the message will be associated with the given task.
  string task_id = 3;
  // Identifies the sender of the message.
  Role role = 4 [(google.api.field_behavior) = REQUIRED];
  // Parts is the container of the message content.
  repeated Part parts = 5 [(google.api.field_behavior) = REQUIRED];
  // Optional. Any metadata to provide along with the message.
  google.protobuf.Struct metadata = 6;
  // The URIs of extensions that are present or contributed to this Message.
  repeated string extensions = 7;
  // A list of task IDs that this message references for additional context.
  repeated string reference_task_ids = 8;
}

// Artifacts represent task outputs.
message Artifact {
  // Unique identifier (e.g. UUID) for the artifact. It must be unique within a task.
  string artifact_id = 1 [(google.api.field_behavior) = REQUIRED];
  // A human readable name for the artifact.
  string name = 2;
  // Optional. A human readable description of the artifact.
  string description = 3;
  // The content of the artifact. Must contain at least one part.
  repeated Part parts = 4 [(google.api.field_behavior) = REQUIRED];
  // Optional. Metadata included with the artifact.
  google.protobuf.Struct metadata = 5;
  // The URIs of extensions that are present or contributed to this Artifact.
  repeated string extensions = 6;
}

// An event sent by the agent to notify the client of a change in a task's status.
message TaskStatusUpdateEvent {
  // The ID of the task that has changed.
  string task_id = 1 [(google.api.field_behavior) = REQUIRED];
  // The ID of the context that the task belongs to.
  string context_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The new status of the task.
  TaskStatus status = 3 [(google.api.field_behavior) = REQUIRED];
  // Optional. Metadata associated with the task update.
  google.protobuf.Struct metadata = 4;
}

// A task delta where an artifact has been generated.
message TaskArtifactUpdateEvent {
  // The ID of the task for this artifact.
  string task_id = 1 [(google.api.field_behavior) = REQUIRED];
  // The ID of the context that this task belongs to.
  string context_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The artifact that was generated or updated.
  Artifact artifact = 3 [(google.api.field_behavior) = REQUIRED];
  // If true, the content of this artifact should be appended to a previously
  // sent artifact with the same ID.
  bool append = 4;
  // If true, this is the final chunk of the artifact.
  bool last_chunk = 5;
  // Optional. Metadata associated with the artifact update.
  google.protobuf.Struct metadata = 6;
}

// Configuration for setting up push notifications for task updates.
message PushNotificationConfig {
  // A unique identifier (e.g. UUID) for this push notification configuration.
  string id = 1;
  // The URL where the notification should be sent.
  string url = 2 [(google.api.field_behavior) = REQUIRED];
  // A token unique for this task or session.
  string token = 3;
  // Authentication information required to send the notification.
  AuthenticationInfo authentication = 4;
}

// Defines authentication details, used for push notifications.
message AuthenticationInfo {
  // HTTP Authentication Scheme from the [IANA registry](https://www.iana.org/assignments/http-authschemes/).
  // Examples: `Bearer`, `Basic`, `Digest`.
  // Scheme names are case-insensitive per [RFC 9110 Section 11.1](https://www.rfc-editor.org/rfc/rfc9110#section-11.1).
  string scheme = 1 [(google.api.field_behavior) = REQUIRED];
  // Push Notification credentials. Format depends on the scheme (e.g., token for Bearer).
  string credentials = 2;
}

// Declares a combination of a target URL, transport and protocol version for interacting with the agent.
// This allows agents to expose the same functionality over multiple protocol binding mechanisms.
message AgentInterface {
  // The URL where this interface is available. Must be a valid absolute HTTPS URL in production.
  // Example: "https://api.example.com/a2a/v1", "https://grpc.example.com/a2a"
  string url = 1 [(google.api.field_behavior) = REQUIRED];
  // The protocol binding supported at this URL. This is an open form string, to be
  // easily extended for other protocol bindings. The core ones officially
  // supported are `JSONRPC`, `GRPC` and `HTTP+JSON`.
  string protocol_binding = 2 [(google.api.field_behavior) = REQUIRED];
  // Tenant ID to be used in the request when calling the agent.
  string tenant = 3;
  // The version of the A2A protocol this interface exposes.
  // Use the latest supported minor version per major version.
  // Examples: "0.3", "1.0"
  string protocol_version = 4 [(google.api.field_behavior) = REQUIRED];
}

// A self-describing manifest for an agent. It provides essential
// metadata including the agent's identity, capabilities, skills, supported
// communication methods, and security requirements.
// Next ID: 20
message AgentCard {
  // A human readable name for the agent.
  // Example: "Recipe Agent"
  string name = 1 [(google.api.field_behavior) = REQUIRED];
  // A human-readable description of the agent, assisting users and other agents
  // in understanding its purpose.
  // Example: "Agent that helps users with recipes and cooking."
  string description = 2 [(google.api.field_behavior) = REQUIRED];
  // Ordered list of supported interfaces. The first entry is preferred.
  repeated AgentInterface supported_interfaces = 3 [(google.api.field_behavior) = REQUIRED];
  // The service provider of the agent.
  AgentProvider provider = 4;
  // The version of the agent.
  // Example: "1.0.0"
  string version = 5 [(google.api.field_behavior) = REQUIRED];
  // A URL providing additional documentation about the agent.
  optional string documentation_url = 6;
  // A2A Capability set supported by the agent.
  AgentCapabilities capabilities = 7 [(google.api.field_behavior) = REQUIRED];
  // The security scheme details used for authenticating with this agent.
  map&lt;string, SecurityScheme&gt; security_schemes = 8;
  // Security requirements for contacting the agent.
  repeated SecurityRequirement security_requirements = 9;
  // protolint:enable REPEATED_FIELD_NAMES_PLURALIZED
  // The set of interaction modes that the agent supports across all skills.
  // This can be overridden per skill. Defined as media types.
  repeated string default_input_modes = 10 [(google.api.field_behavior) = REQUIRED];
  // The media types supported as outputs from this agent.
  repeated string default_output_modes = 11 [(google.api.field_behavior) = REQUIRED];
  // Skills represent the abilities of an agent.
  // It is largely a descriptive concept but represents a more focused set of behaviors that the
  // agent is likely to succeed at.
  repeated AgentSkill skills = 12 [(google.api.field_behavior) = REQUIRED];
  // JSON Web Signatures computed for this `AgentCard`.
  repeated AgentCardSignature signatures = 13;
  // Optional. A URL to an icon for the agent.
  optional string icon_url = 14;
}

// Represents the service provider of an agent.
message AgentProvider {
  // A URL for the agent provider's website or relevant documentation.
  // Example: "https://ai.google.dev"
  string url = 1 [(google.api.field_behavior) = REQUIRED];
  // The name of the agent provider's organization.
  // Example: "Google"
  string organization = 2 [(google.api.field_behavior) = REQUIRED];
}

// Defines optional capabilities supported by an agent.
message AgentCapabilities {
  // Indicates if the agent supports streaming responses.
  optional bool streaming = 1;
  // Indicates if the agent supports sending push notifications for asynchronous task updates.
  optional bool push_notifications = 2;
  // A list of protocol extensions supported by the agent.
  repeated AgentExtension extensions = 3;
  // Indicates if the agent supports providing an extended agent card when authenticated.
  optional bool extended_agent_card = 4;
}

// A declaration of a protocol extension supported by an Agent.
message AgentExtension {
  // The unique URI identifying the extension.
  string uri = 1;
  // A human-readable description of how this agent uses the extension.
  string description = 2;
  // If true, the client must understand and comply with the extension's requirements.
  bool required = 3;
  // Optional. Extension-specific configuration parameters.
  google.protobuf.Struct params = 4;
}

// Represents a distinct capability or function that an agent can perform.
message AgentSkill {
  // A unique identifier for the agent's skill.
  string id = 1 [(google.api.field_behavior) = REQUIRED];
  // A human-readable name for the skill.
  string name = 2 [(google.api.field_behavior) = REQUIRED];
  // A detailed description of the skill.
  string description = 3 [(google.api.field_behavior) = REQUIRED];
  // A set of keywords describing the skill's capabilities.
  repeated string tags = 4 [(google.api.field_behavior) = REQUIRED];
  // Example prompts or scenarios that this skill can handle.
  repeated string examples = 5;
  // The set of supported input media types for this skill, overriding the agent's defaults.
  repeated string input_modes = 6;
  // The set of supported output media types for this skill, overriding the agent's defaults.
  repeated string output_modes = 7;
  // Security schemes necessary for this skill.
  repeated SecurityRequirement security_requirements = 8;
}

// AgentCardSignature represents a JWS signature of an AgentCard.
// This follows the JSON format of an RFC 7515 JSON Web Signature (JWS).
message AgentCardSignature {
  // (-- api-linter: core::0140::reserved-words=disabled
  //     aip.dev/not-precedent: Backwards compatibility --)
  // Required. The protected JWS header for the signature. This is always a
  // base64url-encoded JSON object.
  string protected = 1 [(google.api.field_behavior) = REQUIRED];
  // Required. The computed signature, base64url-encoded.
  string signature = 2 [(google.api.field_behavior) = REQUIRED];
  // The unprotected JWS header values.
  google.protobuf.Struct header = 3;
}

// A container associating a push notification configuration with a specific task.
message TaskPushNotificationConfig {
  // Optional. Tenant ID.
  string tenant = 1;
  // The ID of the task this configuration is associated with.
  string task_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The push notification configuration details.
  PushNotificationConfig push_notification_config = 3 [(google.api.field_behavior) = REQUIRED];
}

// protolint:disable REPEATED_FIELD_NAMES_PLURALIZED
// A list of strings.
message StringList {
  // The individual string values.
  repeated string list = 1;
}
// protolint:enable REPEATED_FIELD_NAMES_PLURALIZED

// Defines the security requirements for an agent.
message SecurityRequirement {
  // A map of security schemes to the required scopes.
  map&lt;string, StringList&gt; schemes = 1;
}

// Defines a security scheme that can be used to secure an agent's endpoints.
// This is a discriminated union type based on the OpenAPI 3.2 Security Scheme Object.
// See: https://spec.openapis.org/oas/v3.2.0.html#security-scheme-object
message SecurityScheme {
  oneof scheme {
    // API key-based authentication.
    APIKeySecurityScheme api_key_security_scheme = 1;
    // HTTP authentication (Basic, Bearer, etc.).
    HTTPAuthSecurityScheme http_auth_security_scheme = 2;
    // OAuth 2.0 authentication.
    OAuth2SecurityScheme oauth2_security_scheme = 3;
    // OpenID Connect authentication.
    OpenIdConnectSecurityScheme open_id_connect_security_scheme = 4;
    // Mutual TLS authentication.
    MutualTlsSecurityScheme mtls_security_scheme = 5;
  }
}

// Defines a security scheme using an API key.
message APIKeySecurityScheme {
  // An optional description for the security scheme.
  string description = 1;
  // The location of the API key. Valid values are "query", "header", or "cookie".
  string location = 2 [(google.api.field_behavior) = REQUIRED];
  // The name of the header, query, or cookie parameter to be used.
  string name = 3 [(google.api.field_behavior) = REQUIRED];
}

// Defines a security scheme using HTTP authentication.
message HTTPAuthSecurityScheme {
  // An optional description for the security scheme.
  string description = 1;
  // The name of the HTTP Authentication scheme to be used in the Authorization header,
  // as defined in RFC7235 (e.g., "Bearer").
  // This value should be registered in the IANA Authentication Scheme registry.
  string scheme = 2 [(google.api.field_behavior) = REQUIRED];
  // A hint to the client to identify how the bearer token is formatted (e.g., "JWT").
  // Primarily for documentation purposes.
  string bearer_format = 3;
}

// Defines a security scheme using OAuth 2.0.
message OAuth2SecurityScheme {
  // An optional description for the security scheme.
  string description = 1;
  // An object containing configuration information for the supported OAuth 2.0 flows.
  OAuthFlows flows = 2 [(google.api.field_behavior) = REQUIRED];
  // URL to the OAuth2 authorization server metadata [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414).
  // TLS is required.
  string oauth2_metadata_url = 3;
}

// Defines a security scheme using OpenID Connect.
message OpenIdConnectSecurityScheme {
  // An optional description for the security scheme.
  string description = 1;
  // The [OpenID Connect Discovery URL](https://openid.net/specs/openid-connect-discovery-1_0.html) for the OIDC provider's metadata.
  string open_id_connect_url = 2 [(google.api.field_behavior) = REQUIRED];
}

// Defines a security scheme using mTLS authentication.
message MutualTlsSecurityScheme {
  // An optional description for the security scheme.
  string description = 1;
}

// Defines the configuration for the supported OAuth 2.0 flows.
message OAuthFlows {
  oneof flow {
    // Configuration for the OAuth Authorization Code flow.
    AuthorizationCodeOAuthFlow authorization_code = 1;
    // Configuration for the OAuth Client Credentials flow.
    ClientCredentialsOAuthFlow client_credentials = 2;
    // Deprecated: Use Authorization Code + PKCE instead.
    ImplicitOAuthFlow implicit = 3 [deprecated = true];
    // Deprecated: Use Authorization Code + PKCE or Device Code.
    PasswordOAuthFlow password = 4 [deprecated = true];
    // Configuration for the OAuth Device Code flow.
    DeviceCodeOAuthFlow device_code = 5;
  }
}

// Defines configuration details for the OAuth 2.0 Authorization Code flow.
message AuthorizationCodeOAuthFlow {
  // The authorization URL to be used for this flow.
  string authorization_url = 1 [(google.api.field_behavior) = REQUIRED];
  // The token URL to be used for this flow.
  string token_url = 2 [(google.api.field_behavior) = REQUIRED];
  // The URL to be used for obtaining refresh tokens.
  string refresh_url = 3;
  // The available scopes for the OAuth2 security scheme.
  map&lt;string, string&gt; scopes = 4 [(google.api.field_behavior) = REQUIRED];
  // Indicates if PKCE (RFC 7636) is required for this flow.
  // PKCE should always be used for public clients and is recommended for all clients.
  bool pkce_required = 5;
}

// Defines configuration details for the OAuth 2.0 Client Credentials flow.
message ClientCredentialsOAuthFlow {
  // The token URL to be used for this flow.
  string token_url = 1 [(google.api.field_behavior) = REQUIRED];
  // The URL to be used for obtaining refresh tokens.
  string refresh_url = 2;
  // The available scopes for the OAuth2 security scheme.
  map&lt;string, string&gt; scopes = 3 [(google.api.field_behavior) = REQUIRED];
}

// Deprecated: Use Authorization Code + PKCE instead.
message ImplicitOAuthFlow {
  // The authorization URL to be used for this flow. This MUST be in the
  // form of a URL. The OAuth2 standard requires the use of TLS
  string authorization_url = 1;
  // The URL to be used for obtaining refresh tokens. This MUST be in the
  // form of a URL. The OAuth2 standard requires the use of TLS.
  string refresh_url = 2;
  // The available scopes for the OAuth2 security scheme. A map between the
  // scope name and a short description for it. The map MAY be empty.
  map&lt;string, string&gt; scopes = 3;
}

// Deprecated: Use Authorization Code + PKCE or Device Code.
message PasswordOAuthFlow {
  // The token URL to be used for this flow. This MUST be in the form of a URL.
  // The OAuth2 standard requires the use of TLS.
  string token_url = 1;
  // The URL to be used for obtaining refresh tokens. This MUST be in the
  // form of a URL. The OAuth2 standard requires the use of TLS.
  string refresh_url = 2;
  // The available scopes for the OAuth2 security scheme. A map between the
  // scope name and a short description for it. The map MAY be empty.
  map&lt;string, string&gt; scopes = 3;
}

// Defines configuration details for the OAuth 2.0 Device Code flow (RFC 8628).
// This flow is designed for input-constrained devices such as IoT devices,
// and CLI tools where the user authenticates on a separate device.
message DeviceCodeOAuthFlow {
  // The device authorization endpoint URL.
  string device_authorization_url = 1 [(google.api.field_behavior) = REQUIRED];
  // The token URL to be used for this flow.
  string token_url = 2 [(google.api.field_behavior) = REQUIRED];
  // The URL to be used for obtaining refresh tokens.
  string refresh_url = 3;
  // The available scopes for the OAuth2 security scheme.
  map&lt;string, string&gt; scopes = 4 [(google.api.field_behavior) = REQUIRED];
}

// Represents a request for the `SendMessage` method.
message SendMessageRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The message to send to the agent.
  Message message = 2 [(google.api.field_behavior) = REQUIRED];
  // Configuration for the send request.
  SendMessageConfiguration configuration = 3;
  // A flexible key-value map for passing additional context or parameters.
  google.protobuf.Struct metadata = 4;
}

// Represents a request for the `GetTask` method.
message GetTaskRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The resource ID of the task to retrieve.
  string id = 2 [(google.api.field_behavior) = REQUIRED];
  // The maximum number of most recent messages from the task's history to retrieve. An
  // unset value means the client does not impose any limit. A value of zero is
  // a request to not include any messages. The server MUST NOT return more
  // messages than the provided value, but MAY apply a lower limit.
  optional int32 history_length = 3;
}

// Parameters for listing tasks with optional filtering criteria.
message ListTasksRequest {
  // Tenant ID, provided as a path parameter.
  string tenant = 1;
  // Filter tasks by context ID to get tasks from a specific conversation or session.
  string context_id = 2;
  // Filter tasks by their current status state.
  TaskState status = 3;
  // The maximum number of tasks to return. The service may return fewer than this value.
  // If unspecified, at most 50 tasks will be returned.
  // The minimum value is 1.
  // The maximum value is 100.
  optional int32 page_size = 4;
  // A page token, received from a previous `ListTasks` call.
  // `ListTasksResponse.next_page_token`.
  // Provide this to retrieve the subsequent page.
  string page_token = 5;
  // The maximum number of messages to include in each task's history.
  optional int32 history_length = 6;
  // Filter tasks which have a status updated after the provided timestamp in ISO 8601 format (e.g., "2023-10-27T10:00:00Z").
  // Only tasks with a status timestamp time greater than or equal to this value will be returned.
  google.protobuf.Timestamp status_timestamp_after = 7;
  // Whether to include artifacts in the returned tasks.
  // Defaults to false to reduce payload size.
  optional bool include_artifacts = 8;
}

// Result object for `ListTasks` method containing an array of tasks and pagination information.
message ListTasksResponse {
  // Array of tasks matching the specified criteria.
  repeated Task tasks = 1 [(google.api.field_behavior) = REQUIRED];
  // A token to retrieve the next page of results, or empty if there are no more results in the list.
  string next_page_token = 2 [(google.api.field_behavior) = REQUIRED];
  // The page size used for this response.
  int32 page_size = 3 [(google.api.field_behavior) = REQUIRED];
  // Total number of tasks available (before pagination).
  int32 total_size = 4 [(google.api.field_behavior) = REQUIRED];
}

// Represents a request for the `CancelTask` method.
message CancelTaskRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The resource ID of the task to cancel.
  string id = 2 [(google.api.field_behavior) = REQUIRED];
  // A flexible key-value map for passing additional context or parameters.
  google.protobuf.Struct metadata = 3;
}

// Represents a request for the `GetTaskPushNotificationConfig` method.
message GetTaskPushNotificationConfigRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The parent task resource ID.
  string task_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The resource ID of the configuration to retrieve.
  string id = 3 [(google.api.field_behavior) = REQUIRED];
}

// Represents a request for the `DeleteTaskPushNotificationConfig` method.
message DeleteTaskPushNotificationConfigRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The parent task resource ID.
  string task_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The resource ID of the configuration to delete.
  string id = 3 [(google.api.field_behavior) = REQUIRED];
}

// Represents a request for the `CreateTaskPushNotificationConfig` method.
message CreateTaskPushNotificationConfigRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The parent task resource ID.
  string task_id = 2 [(google.api.field_behavior) = REQUIRED];
  // The configuration to create.
  PushNotificationConfig config = 3 [(google.api.field_behavior) = REQUIRED];
}

// Represents a request for the `SubscribeToTask` method.
message SubscribeToTaskRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
  // The resource ID of the task to subscribe to.
  string id = 2 [(google.api.field_behavior) = REQUIRED];
}

// Represents a request for the `ListTaskPushNotificationConfigs` method.
message ListTaskPushNotificationConfigsRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 4;
  // The parent task resource ID.
  string task_id = 1 [(google.api.field_behavior) = REQUIRED];

  // The maximum number of configurations to return.
  int32 page_size = 2;

  // A page token received from a previous `ListTaskPushNotificationConfigsRequest` call.
  string page_token = 3;
}

// Represents a request for the `GetExtendedAgentCard` method.
message GetExtendedAgentCardRequest {
  // Optional. Tenant ID, provided as a path parameter.
  string tenant = 1;
}

// Represents the response for the `SendMessage` method.
message SendMessageResponse {
  // The payload of the response.
  oneof payload {
    // The task created or updated by the message.
    Task task = 1;
    // A message from the agent.
    Message message = 2;
  }
}

// A wrapper object used in streaming operations to encapsulate different types of response data.
message StreamResponse {
  // The payload of the stream response.
  oneof payload {
    // A Task object containing the current state of the task.
    Task task = 1;
    // A Message object containing a message from the agent.
    Message message = 2;
    // An event indicating a task status update.
    TaskStatusUpdateEvent status_update = 3;
    // An event indicating a task artifact update.
    TaskArtifactUpdateEvent artifact_update = 4;
  }
}

// Represents a successful response for the `ListTaskPushNotificationConfigs`
// method.
message ListTaskPushNotificationConfigsResponse {
  // The list of push notification configurations.
  repeated TaskPushNotificationConfig configs = 1;
  // A token to retrieve the next page of results, or empty if there are no more results in the list.
  string next_page_token = 2;
}
</code></pre> <p>JSON The A2A protocol JSON Schema definition (JSON Schema 2020-12 compliant). This schema is automatically generated from the protocol buffer definitions and bundled into a single file with all message definitions.</p> <p>Download</p> <p>You can download the schema file directly: <code>a2a.json</code></p> <p>Definition</p> <pre><code>{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "A2A Protocol Schemas",
  "description": "Non-normative JSON Schema bundle extracted from proto definitions.",
  "version": "v1",
  "definitions": {
    "Struct": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "title": "Struct",
      "type": "object"
    },
    "Timestamp": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "format": "date-time",
      "title": "Timestamp",
      "type": "string"
    },
    "Value": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "title": "Value"
    },
    "API Key Security Scheme": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines a security scheme using an API key.",
      "properties": {
        "description": {
          "default": "",
          "description": "An optional description for the security scheme.",
          "type": "string"
        },
        "location": {
          "default": "",
          "description": "The location of the API key. Valid values are \"query\", \"header\", or \"cookie\".",
          "type": "string"
        },
        "name": {
          "default": "",
          "description": "The name of the header, query, or cookie parameter to be used.",
          "type": "string"
        }
      },
      "title": "API Key Security Scheme",
      "type": "object"
    },
    "Agent Capabilities": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines optional capabilities supported by an agent.",
      "patternProperties": {
        "^(extended_agent_card)$": {
          "description": "Indicates if the agent supports providing an extended agent card when authenticated.",
          "type": "boolean"
        },
        "^(push_notifications)$": {
          "description": "Indicates if the agent supports sending push notifications for asynchronous task updates.",
          "type": "boolean"
        }
      },
      "properties": {
        "extendedAgentCard": {
          "description": "Indicates if the agent supports providing an extended agent card when authenticated.",
          "type": "boolean"
        },
        "extensions": {
          "description": "A list of protocol extensions supported by the agent.",
          "items": {
            "$ref": "lf.a2a.v1.AgentExtension.jsonschema.json"
          },
          "type": "array"
        },
        "pushNotifications": {
          "description": "Indicates if the agent supports sending push notifications for asynchronous task updates.",
          "type": "boolean"
        },
        "streaming": {
          "description": "Indicates if the agent supports streaming responses.",
          "type": "boolean"
        }
      },
      "title": "Agent Capabilities",
      "type": "object"
    },
    "Agent Card": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A self-describing manifest for an agent. It provides essential\n metadata including the agent's identity, capabilities, skills, supported\n communication methods, and security requirements.\n Next ID: 20",
      "patternProperties": {
        "^(default_input_modes)$": {
          "description": "The set of interaction modes that the agent supports across all skills.\n This can be overridden per skill. Defined as media types.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "^(default_output_modes)$": {
          "description": "The media types supported as outputs from this agent.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "^(documentation_url)$": {
          "description": "A URL providing additional documentation about the agent.",
          "type": "string"
        },
        "^(icon_url)$": {
          "description": "Optional. A URL to an icon for the agent.",
          "type": "string"
        },
        "^(security_requirements)$": {
          "description": "Security requirements for contacting the agent.",
          "items": {
            "$ref": "lf.a2a.v1.SecurityRequirement.jsonschema.json"
          },
          "type": "array"
        },
        "^(security_schemes)$": {
          "additionalProperties": {
            "$ref": "lf.a2a.v1.SecurityScheme.jsonschema.json"
          },
          "description": "The security scheme details used for authenticating with this agent.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        },
        "^(supported_interfaces)$": {
          "description": "Ordered list of supported interfaces. The first entry is preferred.",
          "items": {
            "$ref": "lf.a2a.v1.AgentInterface.jsonschema.json"
          },
          "type": "array"
        }
      },
      "properties": {
        "capabilities": {
          "$ref": "lf.a2a.v1.AgentCapabilities.jsonschema.json",
          "description": "A2A Capability set supported by the agent."
        },
        "defaultInputModes": {
          "description": "The set of interaction modes that the agent supports across all skills.\n This can be overridden per skill. Defined as media types.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "defaultOutputModes": {
          "description": "The media types supported as outputs from this agent.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "description": {
          "default": "",
          "description": "A human-readable description of the agent, assisting users and other agents\n in understanding its purpose.\n Example: \"Agent that helps users with recipes and cooking.\"",
          "type": "string"
        },
        "documentationUrl": {
          "description": "A URL providing additional documentation about the agent.",
          "type": "string"
        },
        "iconUrl": {
          "description": "Optional. A URL to an icon for the agent.",
          "type": "string"
        },
        "name": {
          "default": "",
          "description": "A human readable name for the agent.\n Example: \"Recipe Agent\"",
          "type": "string"
        },
        "provider": {
          "$ref": "lf.a2a.v1.AgentProvider.jsonschema.json",
          "description": "The service provider of the agent."
        },
        "securityRequirements": {
          "description": "Security requirements for contacting the agent.",
          "items": {
            "$ref": "lf.a2a.v1.SecurityRequirement.jsonschema.json"
          },
          "type": "array"
        },
        "securitySchemes": {
          "additionalProperties": {
            "$ref": "lf.a2a.v1.SecurityScheme.jsonschema.json"
          },
          "description": "The security scheme details used for authenticating with this agent.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        },
        "signatures": {
          "description": "JSON Web Signatures computed for this `AgentCard`.",
          "items": {
            "$ref": "lf.a2a.v1.AgentCardSignature.jsonschema.json"
          },
          "type": "array"
        },
        "skills": {
          "description": "Skills represent the abilities of an agent.\n It is largely a descriptive concept but represents a more focused set of behaviors that the\n agent is likely to succeed at.",
          "items": {
            "$ref": "lf.a2a.v1.AgentSkill.jsonschema.json"
          },
          "type": "array"
        },
        "supportedInterfaces": {
          "description": "Ordered list of supported interfaces. The first entry is preferred.",
          "items": {
            "$ref": "lf.a2a.v1.AgentInterface.jsonschema.json"
          },
          "type": "array"
        },
        "version": {
          "default": "",
          "description": "The version of the agent.\n Example: \"1.0.0\"",
          "type": "string"
        }
      },
      "title": "Agent Card",
      "type": "object"
    },
    "Agent Card Signature": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "AgentCardSignature represents a JWS signature of an AgentCard.\n This follows the JSON format of an RFC 7515 JSON Web Signature (JWS).",
      "properties": {
        "header": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "The unprotected JWS header values."
        },
        "protected": {
          "default": "",
          "description": "(-- api-linter: core::0140::reserved-words=disabled\n     aip.dev/not-precedent: Backwards compatibility --)\n Required. The protected JWS header for the signature. This is always a\n base64url-encoded JSON object.",
          "type": "string"
        },
        "signature": {
          "default": "",
          "description": "Required. The computed signature, base64url-encoded.",
          "type": "string"
        }
      },
      "title": "Agent Card Signature",
      "type": "object"
    },
    "Agent Extension": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A declaration of a protocol extension supported by an Agent.",
      "properties": {
        "description": {
          "default": "",
          "description": "A human-readable description of how this agent uses the extension.",
          "type": "string"
        },
        "params": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "Optional. Extension-specific configuration parameters."
        },
        "required": {
          "default": false,
          "description": "If true, the client must understand and comply with the extension's requirements.",
          "type": "boolean"
        },
        "uri": {
          "default": "",
          "description": "The unique URI identifying the extension.",
          "type": "string"
        }
      },
      "title": "Agent Extension",
      "type": "object"
    },
    "Agent Interface": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Declares a combination of a target URL, transport and protocol version for interacting with the agent.\n This allows agents to expose the same functionality over multiple protocol binding mechanisms.",
      "patternProperties": {
        "^(protocol_binding)$": {
          "default": "",
          "description": "The protocol binding supported at this URL. This is an open form string, to be\n easily extended for other protocol bindings. The core ones officially\n supported are `JSONRPC`, `GRPC` and `HTTP+JSON`.",
          "type": "string"
        },
        "^(protocol_version)$": {
          "default": "",
          "description": "The version of the A2A protocol this interface exposes.\n Use the latest supported minor version per major version.\n Examples: \"0.3\", \"1.0\"",
          "type": "string"
        }
      },
      "properties": {
        "protocolBinding": {
          "default": "",
          "description": "The protocol binding supported at this URL. This is an open form string, to be\n easily extended for other protocol bindings. The core ones officially\n supported are `JSONRPC`, `GRPC` and `HTTP+JSON`.",
          "type": "string"
        },
        "protocolVersion": {
          "default": "",
          "description": "The version of the A2A protocol this interface exposes.\n Use the latest supported minor version per major version.\n Examples: \"0.3\", \"1.0\"",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Tenant ID to be used in the request when calling the agent.",
          "type": "string"
        },
        "url": {
          "default": "",
          "description": "The URL where this interface is available. Must be a valid absolute HTTPS URL in production.\n Example: \"https://api.example.com/a2a/v1\", \"https://grpc.example.com/a2a\"",
          "type": "string"
        }
      },
      "title": "Agent Interface",
      "type": "object"
    },
    "Agent Provider": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents the service provider of an agent.",
      "properties": {
        "organization": {
          "default": "",
          "description": "The name of the agent provider's organization.\n Example: \"Google\"",
          "type": "string"
        },
        "url": {
          "default": "",
          "description": "A URL for the agent provider's website or relevant documentation.\n Example: \"https://ai.google.dev\"",
          "type": "string"
        }
      },
      "title": "Agent Provider",
      "type": "object"
    },
    "Agent Skill": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a distinct capability or function that an agent can perform.",
      "patternProperties": {
        "^(input_modes)$": {
          "description": "The set of supported input media types for this skill, overriding the agent's defaults.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "^(output_modes)$": {
          "description": "The set of supported output media types for this skill, overriding the agent's defaults.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "^(security_requirements)$": {
          "description": "Security schemes necessary for this skill.",
          "items": {
            "$ref": "lf.a2a.v1.SecurityRequirement.jsonschema.json"
          },
          "type": "array"
        }
      },
      "properties": {
        "description": {
          "default": "",
          "description": "A detailed description of the skill.",
          "type": "string"
        },
        "examples": {
          "description": "Example prompts or scenarios that this skill can handle.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "id": {
          "default": "",
          "description": "A unique identifier for the agent's skill.",
          "type": "string"
        },
        "inputModes": {
          "description": "The set of supported input media types for this skill, overriding the agent's defaults.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "name": {
          "default": "",
          "description": "A human-readable name for the skill.",
          "type": "string"
        },
        "outputModes": {
          "description": "The set of supported output media types for this skill, overriding the agent's defaults.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "securityRequirements": {
          "description": "Security schemes necessary for this skill.",
          "items": {
            "$ref": "lf.a2a.v1.SecurityRequirement.jsonschema.json"
          },
          "type": "array"
        },
        "tags": {
          "description": "A set of keywords describing the skill's capabilities.",
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "title": "Agent Skill",
      "type": "object"
    },
    "Artifact": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Artifacts represent task outputs.",
      "patternProperties": {
        "^(artifact_id)$": {
          "default": "",
          "description": "Unique identifier (e.g. UUID) for the artifact. It must be unique within a task.",
          "type": "string"
        }
      },
      "properties": {
        "artifactId": {
          "default": "",
          "description": "Unique identifier (e.g. UUID) for the artifact. It must be unique within a task.",
          "type": "string"
        },
        "description": {
          "default": "",
          "description": "Optional. A human readable description of the artifact.",
          "type": "string"
        },
        "extensions": {
          "description": "The URIs of extensions that are present or contributed to this Artifact.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "Optional. Metadata included with the artifact."
        },
        "name": {
          "default": "",
          "description": "A human readable name for the artifact.",
          "type": "string"
        },
        "parts": {
          "description": "The content of the artifact. Must contain at least one part.",
          "items": {
            "$ref": "lf.a2a.v1.Part.jsonschema.json"
          },
          "type": "array"
        }
      },
      "title": "Artifact",
      "type": "object"
    },
    "Authentication Info": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines authentication details, used for push notifications.",
      "properties": {
        "credentials": {
          "default": "",
          "description": "Push Notification credentials. Format depends on the scheme (e.g., token for Bearer).",
          "type": "string"
        },
        "scheme": {
          "default": "",
          "description": "HTTP Authentication Scheme from the [IANA registry](https://www.iana.org/assignments/http-authschemes/).\n Examples: `Bearer`, `Basic`, `Digest`.\n Scheme names are case-insensitive per [RFC 9110 Section 11.1](https://www.rfc-editor.org/rfc/rfc9110#section-11.1).",
          "type": "string"
        }
      },
      "title": "Authentication Info",
      "type": "object"
    },
    "Authorization CodeO Auth Flow": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines configuration details for the OAuth 2.0 Authorization Code flow.",
      "patternProperties": {
        "^(authorization_url)$": {
          "default": "",
          "description": "The authorization URL to be used for this flow.",
          "type": "string"
        },
        "^(pkce_required)$": {
          "default": false,
          "description": "Indicates if PKCE (RFC 7636) is required for this flow.\n PKCE should always be used for public clients and is recommended for all clients.",
          "type": "boolean"
        },
        "^(refresh_url)$": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens.",
          "type": "string"
        },
        "^(token_url)$": {
          "default": "",
          "description": "The token URL to be used for this flow.",
          "type": "string"
        }
      },
      "properties": {
        "authorizationUrl": {
          "default": "",
          "description": "The authorization URL to be used for this flow.",
          "type": "string"
        },
        "pkceRequired": {
          "default": false,
          "description": "Indicates if PKCE (RFC 7636) is required for this flow.\n PKCE should always be used for public clients and is recommended for all clients.",
          "type": "boolean"
        },
        "refreshUrl": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens.",
          "type": "string"
        },
        "scopes": {
          "additionalProperties": {
            "type": "string"
          },
          "description": "The available scopes for the OAuth2 security scheme.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        },
        "tokenUrl": {
          "default": "",
          "description": "The token URL to be used for this flow.",
          "type": "string"
        }
      },
      "title": "Authorization CodeO Auth Flow",
      "type": "object"
    },
    "Cancel Task Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `CancelTask` method.",
      "properties": {
        "id": {
          "default": "",
          "description": "The resource ID of the task to cancel.",
          "type": "string"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "A flexible key-value map for passing additional context or parameters."
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Cancel Task Request",
      "type": "object"
    },
    "Client CredentialsO Auth Flow": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines configuration details for the OAuth 2.0 Client Credentials flow.",
      "patternProperties": {
        "^(refresh_url)$": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens.",
          "type": "string"
        },
        "^(token_url)$": {
          "default": "",
          "description": "The token URL to be used for this flow.",
          "type": "string"
        }
      },
      "properties": {
        "refreshUrl": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens.",
          "type": "string"
        },
        "scopes": {
          "additionalProperties": {
            "type": "string"
          },
          "description": "The available scopes for the OAuth2 security scheme.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        },
        "tokenUrl": {
          "default": "",
          "description": "The token URL to be used for this flow.",
          "type": "string"
        }
      },
      "title": "Client CredentialsO Auth Flow",
      "type": "object"
    },
    "Create Task Push Notification Config Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `CreateTaskPushNotificationConfig` method.",
      "patternProperties": {
        "^(task_id)$": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        }
      },
      "properties": {
        "config": {
          "$ref": "lf.a2a.v1.PushNotificationConfig.jsonschema.json",
          "description": "The configuration to create."
        },
        "taskId": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Create Task Push Notification Config Request",
      "type": "object"
    },
    "Delete Task Push Notification Config Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `DeleteTaskPushNotificationConfig` method.",
      "patternProperties": {
        "^(task_id)$": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        }
      },
      "properties": {
        "id": {
          "default": "",
          "description": "The resource ID of the configuration to delete.",
          "type": "string"
        },
        "taskId": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Delete Task Push Notification Config Request",
      "type": "object"
    },
    "Device CodeO Auth Flow": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines configuration details for the OAuth 2.0 Device Code flow (RFC 8628).\n This flow is designed for input-constrained devices such as IoT devices,\n and CLI tools where the user authenticates on a separate device.",
      "patternProperties": {
        "^(device_authorization_url)$": {
          "default": "",
          "description": "The device authorization endpoint URL.",
          "type": "string"
        },
        "^(refresh_url)$": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens.",
          "type": "string"
        },
        "^(token_url)$": {
          "default": "",
          "description": "The token URL to be used for this flow.",
          "type": "string"
        }
      },
      "properties": {
        "deviceAuthorizationUrl": {
          "default": "",
          "description": "The device authorization endpoint URL.",
          "type": "string"
        },
        "refreshUrl": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens.",
          "type": "string"
        },
        "scopes": {
          "additionalProperties": {
            "type": "string"
          },
          "description": "The available scopes for the OAuth2 security scheme.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        },
        "tokenUrl": {
          "default": "",
          "description": "The token URL to be used for this flow.",
          "type": "string"
        }
      },
      "title": "Device CodeO Auth Flow",
      "type": "object"
    },
    "Get Extended Agent Card Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `GetExtendedAgentCard` method.",
      "properties": {
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Get Extended Agent Card Request",
      "type": "object"
    },
    "Get Task Push Notification Config Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `GetTaskPushNotificationConfig` method.",
      "patternProperties": {
        "^(task_id)$": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        }
      },
      "properties": {
        "id": {
          "default": "",
          "description": "The resource ID of the configuration to retrieve.",
          "type": "string"
        },
        "taskId": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Get Task Push Notification Config Request",
      "type": "object"
    },
    "Get Task Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `GetTask` method.",
      "patternProperties": {
        "^(history_length)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of most recent messages from the task's history to retrieve. An\n unset value means the client does not impose any limit. A value of zero is\n a request to not include any messages. The server MUST NOT return more\n messages than the provided value, but MAY apply a lower limit."
        }
      },
      "properties": {
        "historyLength": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of most recent messages from the task's history to retrieve. An\n unset value means the client does not impose any limit. A value of zero is\n a request to not include any messages. The server MUST NOT return more\n messages than the provided value, but MAY apply a lower limit."
        },
        "id": {
          "default": "",
          "description": "The resource ID of the task to retrieve.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Get Task Request",
      "type": "object"
    },
    "HTTP Auth Security Scheme": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines a security scheme using HTTP authentication.",
      "patternProperties": {
        "^(bearer_format)$": {
          "default": "",
          "description": "A hint to the client to identify how the bearer token is formatted (e.g., \"JWT\").\n Primarily for documentation purposes.",
          "type": "string"
        }
      },
      "properties": {
        "bearerFormat": {
          "default": "",
          "description": "A hint to the client to identify how the bearer token is formatted (e.g., \"JWT\").\n Primarily for documentation purposes.",
          "type": "string"
        },
        "description": {
          "default": "",
          "description": "An optional description for the security scheme.",
          "type": "string"
        },
        "scheme": {
          "default": "",
          "description": "The name of the HTTP Authentication scheme to be used in the Authorization header,\n as defined in RFC7235 (e.g., \"Bearer\").\n This value should be registered in the IANA Authentication Scheme registry.",
          "type": "string"
        }
      },
      "title": "HTTP Auth Security Scheme",
      "type": "object"
    },
    "ImplicitO Auth Flow": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Deprecated: Use Authorization Code + PKCE instead.",
      "patternProperties": {
        "^(authorization_url)$": {
          "default": "",
          "description": "The authorization URL to be used for this flow. This MUST be in the\n form of a URL. The OAuth2 standard requires the use of TLS",
          "type": "string"
        },
        "^(refresh_url)$": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens. This MUST be in the\n form of a URL. The OAuth2 standard requires the use of TLS.",
          "type": "string"
        }
      },
      "properties": {
        "authorizationUrl": {
          "default": "",
          "description": "The authorization URL to be used for this flow. This MUST be in the\n form of a URL. The OAuth2 standard requires the use of TLS",
          "type": "string"
        },
        "refreshUrl": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens. This MUST be in the\n form of a URL. The OAuth2 standard requires the use of TLS.",
          "type": "string"
        },
        "scopes": {
          "additionalProperties": {
            "type": "string"
          },
          "description": "The available scopes for the OAuth2 security scheme. A map between the\n scope name and a short description for it. The map MAY be empty.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        }
      },
      "title": "ImplicitO Auth Flow",
      "type": "object"
    },
    "List Task Push Notification Configs Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `ListTaskPushNotificationConfigs` method.",
      "patternProperties": {
        "^(page_size)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "default": 0,
          "description": "The maximum number of configurations to return."
        },
        "^(page_token)$": {
          "default": "",
          "description": "A page token received from a previous `ListTaskPushNotificationConfigsRequest` call.",
          "type": "string"
        },
        "^(task_id)$": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        }
      },
      "properties": {
        "pageSize": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "default": 0,
          "description": "The maximum number of configurations to return."
        },
        "pageToken": {
          "default": "",
          "description": "A page token received from a previous `ListTaskPushNotificationConfigsRequest` call.",
          "type": "string"
        },
        "taskId": {
          "default": "",
          "description": "The parent task resource ID.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "List Task Push Notification Configs Request",
      "type": "object"
    },
    "List Task Push Notification Configs Response": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a successful response for the `ListTaskPushNotificationConfigs`\n method.",
      "patternProperties": {
        "^(next_page_token)$": {
          "default": "",
          "description": "A token to retrieve the next page of results, or empty if there are no more results in the list.",
          "type": "string"
        }
      },
      "properties": {
        "configs": {
          "description": "The list of push notification configurations.",
          "items": {
            "$ref": "lf.a2a.v1.TaskPushNotificationConfig.jsonschema.json"
          },
          "type": "array"
        },
        "nextPageToken": {
          "default": "",
          "description": "A token to retrieve the next page of results, or empty if there are no more results in the list.",
          "type": "string"
        }
      },
      "title": "List Task Push Notification Configs Response",
      "type": "object"
    },
    "List Tasks Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Parameters for listing tasks with optional filtering criteria.",
      "patternProperties": {
        "^(context_id)$": {
          "default": "",
          "description": "Filter tasks by context ID to get tasks from a specific conversation or session.",
          "type": "string"
        },
        "^(history_length)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of messages to include in each task's history."
        },
        "^(include_artifacts)$": {
          "description": "Whether to include artifacts in the returned tasks.\n Defaults to false to reduce payload size.",
          "type": "boolean"
        },
        "^(page_size)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of tasks to return. The service may return fewer than this value.\n If unspecified, at most 50 tasks will be returned.\n The minimum value is 1.\n The maximum value is 100."
        },
        "^(page_token)$": {
          "default": "",
          "description": "A page token, received from a previous `ListTasks` call.\n `ListTasksResponse.next_page_token`.\n Provide this to retrieve the subsequent page.",
          "type": "string"
        },
        "^(status_timestamp_after)$": {
          "$ref": "google.protobuf.Timestamp.jsonschema.json",
          "description": "Filter tasks which have a status updated after the provided timestamp in ISO 8601 format (e.g., \"2023-10-27T10:00:00Z\").\n Only tasks with a status timestamp time greater than or equal to this value will be returned."
        }
      },
      "properties": {
        "contextId": {
          "default": "",
          "description": "Filter tasks by context ID to get tasks from a specific conversation or session.",
          "type": "string"
        },
        "historyLength": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of messages to include in each task's history."
        },
        "includeArtifacts": {
          "description": "Whether to include artifacts in the returned tasks.\n Defaults to false to reduce payload size.",
          "type": "boolean"
        },
        "pageSize": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of tasks to return. The service may return fewer than this value.\n If unspecified, at most 50 tasks will be returned.\n The minimum value is 1.\n The maximum value is 100."
        },
        "pageToken": {
          "default": "",
          "description": "A page token, received from a previous `ListTasks` call.\n `ListTasksResponse.next_page_token`.\n Provide this to retrieve the subsequent page.",
          "type": "string"
        },
        "status": {
          "anyOf": [
            {
              "pattern": "^TASK_STATE_UNSPECIFIED$",
              "type": "string"
            },
            {
              "enum": [
                "TASK_STATE_SUBMITTED",
                "TASK_STATE_WORKING",
                "TASK_STATE_COMPLETED",
                "TASK_STATE_FAILED",
                "TASK_STATE_CANCELED",
                "TASK_STATE_INPUT_REQUIRED",
                "TASK_STATE_REJECTED",
                "TASK_STATE_AUTH_REQUIRED"
              ],
              "type": "string"
            },
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            }
          ],
          "default": 0,
          "description": "Filter tasks by their current status state.",
          "title": "Task State"
        },
        "statusTimestampAfter": {
          "$ref": "google.protobuf.Timestamp.jsonschema.json",
          "description": "Filter tasks which have a status updated after the provided timestamp in ISO 8601 format (e.g., \"2023-10-27T10:00:00Z\").\n Only tasks with a status timestamp time greater than or equal to this value will be returned."
        },
        "tenant": {
          "default": "",
          "description": "Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "List Tasks Request",
      "type": "object"
    },
    "List Tasks Response": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Result object for `ListTasks` method containing an array of tasks and pagination information.",
      "patternProperties": {
        "^(next_page_token)$": {
          "default": "",
          "description": "A token to retrieve the next page of results, or empty if there are no more results in the list.",
          "type": "string"
        },
        "^(page_size)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "default": 0,
          "description": "The page size used for this response."
        },
        "^(total_size)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "default": 0,
          "description": "Total number of tasks available (before pagination)."
        }
      },
      "properties": {
        "nextPageToken": {
          "default": "",
          "description": "A token to retrieve the next page of results, or empty if there are no more results in the list.",
          "type": "string"
        },
        "pageSize": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "default": 0,
          "description": "The page size used for this response."
        },
        "tasks": {
          "description": "Array of tasks matching the specified criteria.",
          "items": {
            "$ref": "lf.a2a.v1.Task.jsonschema.json"
          },
          "type": "array"
        },
        "totalSize": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "default": 0,
          "description": "Total number of tasks available (before pagination)."
        }
      },
      "title": "List Tasks Response",
      "type": "object"
    },
    "Message": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "`Message` is one unit of communication between client and server. It can be\n associated with a context and/or a task. For server messages, `context_id` must\n be provided, and `task_id` only if a task was created. For client messages, both\n fields are optional, with the caveat that if both are provided, they have to\n match (the `context_id` has to be the one that is set on the task). If only\n `task_id` is provided, the server will infer `context_id` from it.",
      "patternProperties": {
        "^(context_id)$": {
          "default": "",
          "description": "Optional. The context id of the message. If set, the message will be associated with the given context.",
          "type": "string"
        },
        "^(message_id)$": {
          "default": "",
          "description": "The unique identifier (e.g. UUID) of the message. This is created by the message creator.",
          "type": "string"
        },
        "^(reference_task_ids)$": {
          "description": "A list of task IDs that this message references for additional context.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "^(task_id)$": {
          "default": "",
          "description": "Optional. The task id of the message. If set, the message will be associated with the given task.",
          "type": "string"
        }
      },
      "properties": {
        "contextId": {
          "default": "",
          "description": "Optional. The context id of the message. If set, the message will be associated with the given context.",
          "type": "string"
        },
        "extensions": {
          "description": "The URIs of extensions that are present or contributed to this Message.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "messageId": {
          "default": "",
          "description": "The unique identifier (e.g. UUID) of the message. This is created by the message creator.",
          "type": "string"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "Optional. Any metadata to provide along with the message."
        },
        "parts": {
          "description": "Parts is the container of the message content.",
          "items": {
            "$ref": "lf.a2a.v1.Part.jsonschema.json"
          },
          "type": "array"
        },
        "referenceTaskIds": {
          "description": "A list of task IDs that this message references for additional context.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "role": {
          "anyOf": [
            {
              "pattern": "^ROLE_UNSPECIFIED$",
              "type": "string"
            },
            {
              "enum": [
                "ROLE_USER",
                "ROLE_AGENT"
              ],
              "type": "string"
            },
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            }
          ],
          "default": 0,
          "description": "Identifies the sender of the message.",
          "title": "Role"
        },
        "taskId": {
          "default": "",
          "description": "Optional. The task id of the message. If set, the message will be associated with the given task.",
          "type": "string"
        }
      },
      "title": "Message",
      "type": "object"
    },
    "Mutual Tls Security Scheme": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines a security scheme using mTLS authentication.",
      "properties": {
        "description": {
          "default": "",
          "description": "An optional description for the security scheme.",
          "type": "string"
        }
      },
      "title": "Mutual Tls Security Scheme",
      "type": "object"
    },
    "O Auth2 Security Scheme": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines a security scheme using OAuth 2.0.",
      "patternProperties": {
        "^(oauth2_metadata_url)$": {
          "default": "",
          "description": "URL to the OAuth2 authorization server metadata [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414).\n TLS is required.",
          "type": "string"
        }
      },
      "properties": {
        "description": {
          "default": "",
          "description": "An optional description for the security scheme.",
          "type": "string"
        },
        "flows": {
          "$ref": "lf.a2a.v1.OAuthFlows.jsonschema.json",
          "description": "An object containing configuration information for the supported OAuth 2.0 flows."
        },
        "oauth2MetadataUrl": {
          "default": "",
          "description": "URL to the OAuth2 authorization server metadata [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414).\n TLS is required.",
          "type": "string"
        }
      },
      "title": "O Auth2 Security Scheme",
      "type": "object"
    },
    "O Auth Flows": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines the configuration for the supported OAuth 2.0 flows.",
      "patternProperties": {
        "^(authorization_code)$": {
          "$ref": "lf.a2a.v1.AuthorizationCodeOAuthFlow.jsonschema.json",
          "description": "Configuration for the OAuth Authorization Code flow."
        },
        "^(client_credentials)$": {
          "$ref": "lf.a2a.v1.ClientCredentialsOAuthFlow.jsonschema.json",
          "description": "Configuration for the OAuth Client Credentials flow."
        },
        "^(device_code)$": {
          "$ref": "lf.a2a.v1.DeviceCodeOAuthFlow.jsonschema.json",
          "description": "Configuration for the OAuth Device Code flow."
        }
      },
      "properties": {
        "authorizationCode": {
          "$ref": "lf.a2a.v1.AuthorizationCodeOAuthFlow.jsonschema.json",
          "description": "Configuration for the OAuth Authorization Code flow."
        },
        "clientCredentials": {
          "$ref": "lf.a2a.v1.ClientCredentialsOAuthFlow.jsonschema.json",
          "description": "Configuration for the OAuth Client Credentials flow."
        },
        "deviceCode": {
          "$ref": "lf.a2a.v1.DeviceCodeOAuthFlow.jsonschema.json",
          "description": "Configuration for the OAuth Device Code flow."
        },
        "implicit": {
          "$ref": "lf.a2a.v1.ImplicitOAuthFlow.jsonschema.json",
          "description": "Deprecated: Use Authorization Code + PKCE instead."
        },
        "password": {
          "$ref": "lf.a2a.v1.PasswordOAuthFlow.jsonschema.json",
          "description": "Deprecated: Use Authorization Code + PKCE or Device Code."
        }
      },
      "title": "O Auth Flows",
      "type": "object"
    },
    "Open Id Connect Security Scheme": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines a security scheme using OpenID Connect.",
      "patternProperties": {
        "^(open_id_connect_url)$": {
          "default": "",
          "description": "The [OpenID Connect Discovery URL](https://openid.net/specs/openid-connect-discovery-1_0.html) for the OIDC provider's metadata.",
          "type": "string"
        }
      },
      "properties": {
        "description": {
          "default": "",
          "description": "An optional description for the security scheme.",
          "type": "string"
        },
        "openIdConnectUrl": {
          "default": "",
          "description": "The [OpenID Connect Discovery URL](https://openid.net/specs/openid-connect-discovery-1_0.html) for the OIDC provider's metadata.",
          "type": "string"
        }
      },
      "title": "Open Id Connect Security Scheme",
      "type": "object"
    },
    "Part": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "`Part` represents a container for a section of communication content.\n Parts can be purely textual, some sort of file (image, video, etc) or\n a structured data blob (i.e. JSON).",
      "patternProperties": {
        "^(media_type)$": {
          "default": "",
          "description": "The `media_type` (MIME type) of the part content (e.g., \"text/plain\", \"application/json\", \"image/png\").\n This field is available for all part types.",
          "type": "string"
        }
      },
      "properties": {
        "data": {
          "$ref": "google.protobuf.Value.jsonschema.json",
          "description": "Arbitrary structured `data` as a JSON value (object, array, string, number, boolean, or null)."
        },
        "filename": {
          "default": "",
          "description": "An optional `filename` for the file (e.g., \"document.pdf\").",
          "type": "string"
        },
        "mediaType": {
          "default": "",
          "description": "The `media_type` (MIME type) of the part content (e.g., \"text/plain\", \"application/json\", \"image/png\").\n This field is available for all part types.",
          "type": "string"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "Optional. metadata associated with this part."
        },
        "raw": {
          "description": "The `raw` byte content of a file. In JSON serialization, this is encoded as a base64 string.",
          "pattern": "^[A-Za-z0-9+/]*={0,2}$",
          "type": "string"
        },
        "text": {
          "description": "The string content of the `text` part.",
          "type": "string"
        },
        "url": {
          "description": "A `url` pointing to the file's content.",
          "type": "string"
        }
      },
      "title": "Part",
      "type": "object"
    },
    "PasswordO Auth Flow": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Deprecated: Use Authorization Code + PKCE or Device Code.",
      "patternProperties": {
        "^(refresh_url)$": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens. This MUST be in the\n form of a URL. The OAuth2 standard requires the use of TLS.",
          "type": "string"
        },
        "^(token_url)$": {
          "default": "",
          "description": "The token URL to be used for this flow. This MUST be in the form of a URL.\n The OAuth2 standard requires the use of TLS.",
          "type": "string"
        }
      },
      "properties": {
        "refreshUrl": {
          "default": "",
          "description": "The URL to be used for obtaining refresh tokens. This MUST be in the\n form of a URL. The OAuth2 standard requires the use of TLS.",
          "type": "string"
        },
        "scopes": {
          "additionalProperties": {
            "type": "string"
          },
          "description": "The available scopes for the OAuth2 security scheme. A map between the\n scope name and a short description for it. The map MAY be empty.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        },
        "tokenUrl": {
          "default": "",
          "description": "The token URL to be used for this flow. This MUST be in the form of a URL.\n The OAuth2 standard requires the use of TLS.",
          "type": "string"
        }
      },
      "title": "PasswordO Auth Flow",
      "type": "object"
    },
    "Push Notification Config": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Configuration for setting up push notifications for task updates.",
      "properties": {
        "authentication": {
          "$ref": "lf.a2a.v1.AuthenticationInfo.jsonschema.json",
          "description": "Authentication information required to send the notification."
        },
        "id": {
          "default": "",
          "description": "A unique identifier (e.g. UUID) for this push notification configuration.",
          "type": "string"
        },
        "token": {
          "default": "",
          "description": "A token unique for this task or session.",
          "type": "string"
        },
        "url": {
          "default": "",
          "description": "The URL where the notification should be sent.",
          "type": "string"
        }
      },
      "title": "Push Notification Config",
      "type": "object"
    },
    "Security Requirement": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines the security requirements for an agent.",
      "properties": {
        "schemes": {
          "additionalProperties": {
            "$ref": "lf.a2a.v1.StringList.jsonschema.json"
          },
          "description": "A map of security schemes to the required scopes.",
          "propertyNames": {
            "type": "string"
          },
          "type": "object"
        }
      },
      "title": "Security Requirement",
      "type": "object"
    },
    "Security Scheme": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Defines a security scheme that can be used to secure an agent's endpoints.\n This is a discriminated union type based on the OpenAPI 3.2 Security Scheme Object.\n See: https://spec.openapis.org/oas/v3.2.0.html#security-scheme-object",
      "patternProperties": {
        "^(api_key_security_scheme)$": {
          "$ref": "lf.a2a.v1.APIKeySecurityScheme.jsonschema.json",
          "description": "API key-based authentication."
        },
        "^(http_auth_security_scheme)$": {
          "$ref": "lf.a2a.v1.HTTPAuthSecurityScheme.jsonschema.json",
          "description": "HTTP authentication (Basic, Bearer, etc.)."
        },
        "^(mtls_security_scheme)$": {
          "$ref": "lf.a2a.v1.MutualTlsSecurityScheme.jsonschema.json",
          "description": "Mutual TLS authentication."
        },
        "^(oauth2_security_scheme)$": {
          "$ref": "lf.a2a.v1.OAuth2SecurityScheme.jsonschema.json",
          "description": "OAuth 2.0 authentication."
        },
        "^(open_id_connect_security_scheme)$": {
          "$ref": "lf.a2a.v1.OpenIdConnectSecurityScheme.jsonschema.json",
          "description": "OpenID Connect authentication."
        }
      },
      "properties": {
        "apiKeySecurityScheme": {
          "$ref": "lf.a2a.v1.APIKeySecurityScheme.jsonschema.json",
          "description": "API key-based authentication."
        },
        "httpAuthSecurityScheme": {
          "$ref": "lf.a2a.v1.HTTPAuthSecurityScheme.jsonschema.json",
          "description": "HTTP authentication (Basic, Bearer, etc.)."
        },
        "mtlsSecurityScheme": {
          "$ref": "lf.a2a.v1.MutualTlsSecurityScheme.jsonschema.json",
          "description": "Mutual TLS authentication."
        },
        "oauth2SecurityScheme": {
          "$ref": "lf.a2a.v1.OAuth2SecurityScheme.jsonschema.json",
          "description": "OAuth 2.0 authentication."
        },
        "openIdConnectSecurityScheme": {
          "$ref": "lf.a2a.v1.OpenIdConnectSecurityScheme.jsonschema.json",
          "description": "OpenID Connect authentication."
        }
      },
      "title": "Security Scheme",
      "type": "object"
    },
    "Send Message Configuration": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Configuration of a send message request.",
      "patternProperties": {
        "^(accepted_output_modes)$": {
          "description": "A list of media types the client is prepared to accept for response parts.\n Agents SHOULD use this to tailor their output.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "^(history_length)$": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of most recent messages from the task's history to retrieve in\n the response. An unset value means the client does not impose any limit. A\n value of zero is a request to not include any messages. The server MUST NOT\n return more messages than the provided value, but MAY apply a lower limit."
        },
        "^(push_notification_config)$": {
          "$ref": "lf.a2a.v1.PushNotificationConfig.jsonschema.json",
          "description": "Configuration for the agent to send push notifications for task updates."
        }
      },
      "properties": {
        "acceptedOutputModes": {
          "description": "A list of media types the client is prepared to accept for response parts.\n Agents SHOULD use this to tailor their output.",
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "blocking": {
          "default": false,
          "description": "If `true`, the operation MUST wait until the task reaches a terminal state\n (`COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`) or an interrupted state\n (`INPUT_REQUIRED`, `AUTH_REQUIRED`) before returning. Default is `false`.",
          "type": "boolean"
        },
        "historyLength": {
          "anyOf": [
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            },
            {
              "pattern": "^-?[0-9]+$",
              "type": "string"
            }
          ],
          "description": "The maximum number of most recent messages from the task's history to retrieve in\n the response. An unset value means the client does not impose any limit. A\n value of zero is a request to not include any messages. The server MUST NOT\n return more messages than the provided value, but MAY apply a lower limit."
        },
        "pushNotificationConfig": {
          "$ref": "lf.a2a.v1.PushNotificationConfig.jsonschema.json",
          "description": "Configuration for the agent to send push notifications for task updates."
        }
      },
      "title": "Send Message Configuration",
      "type": "object"
    },
    "Send Message Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `SendMessage` method.",
      "properties": {
        "configuration": {
          "$ref": "lf.a2a.v1.SendMessageConfiguration.jsonschema.json",
          "description": "Configuration for the send request."
        },
        "message": {
          "$ref": "lf.a2a.v1.Message.jsonschema.json",
          "description": "The message to send to the agent."
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "A flexible key-value map for passing additional context or parameters."
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Send Message Request",
      "type": "object"
    },
    "Send Message Response": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents the response for the `SendMessage` method.",
      "properties": {
        "message": {
          "$ref": "lf.a2a.v1.Message.jsonschema.json",
          "description": "A message from the agent."
        },
        "task": {
          "$ref": "lf.a2a.v1.Task.jsonschema.json",
          "description": "The task created or updated by the message."
        }
      },
      "title": "Send Message Response",
      "type": "object"
    },
    "Stream Response": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A wrapper object used in streaming operations to encapsulate different types of response data.",
      "patternProperties": {
        "^(artifact_update)$": {
          "$ref": "lf.a2a.v1.TaskArtifactUpdateEvent.jsonschema.json",
          "description": "An event indicating a task artifact update."
        },
        "^(status_update)$": {
          "$ref": "lf.a2a.v1.TaskStatusUpdateEvent.jsonschema.json",
          "description": "An event indicating a task status update."
        }
      },
      "properties": {
        "artifactUpdate": {
          "$ref": "lf.a2a.v1.TaskArtifactUpdateEvent.jsonschema.json",
          "description": "An event indicating a task artifact update."
        },
        "message": {
          "$ref": "lf.a2a.v1.Message.jsonschema.json",
          "description": "A Message object containing a message from the agent."
        },
        "statusUpdate": {
          "$ref": "lf.a2a.v1.TaskStatusUpdateEvent.jsonschema.json",
          "description": "An event indicating a task status update."
        },
        "task": {
          "$ref": "lf.a2a.v1.Task.jsonschema.json",
          "description": "A Task object containing the current state of the task."
        }
      },
      "title": "Stream Response",
      "type": "object"
    },
    "String List": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A list of strings.",
      "properties": {
        "list": {
          "description": "The individual string values.",
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "title": "String List",
      "type": "object"
    },
    "Subscribe To Task Request": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "Represents a request for the `SubscribeToTask` method.",
      "properties": {
        "id": {
          "default": "",
          "description": "The resource ID of the task to subscribe to.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID, provided as a path parameter.",
          "type": "string"
        }
      },
      "title": "Subscribe To Task Request",
      "type": "object"
    },
    "Task": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "`Task` is the core unit of action for A2A. It has a current status\n and when results are created for the task they are stored in the\n artifact. If there are multiple turns for a task, these are stored in\n history.",
      "patternProperties": {
        "^(context_id)$": {
          "default": "",
          "description": "Unique identifier (e.g. UUID) for the contextual collection of interactions\n (tasks and messages). Created by the A2A server.",
          "type": "string"
        }
      },
      "properties": {
        "artifacts": {
          "description": "A set of output artifacts for a `Task`.",
          "items": {
            "$ref": "lf.a2a.v1.Artifact.jsonschema.json"
          },
          "type": "array"
        },
        "contextId": {
          "default": "",
          "description": "Unique identifier (e.g. UUID) for the contextual collection of interactions\n (tasks and messages). Created by the A2A server.",
          "type": "string"
        },
        "history": {
          "description": "The history of interactions from a `Task`.",
          "items": {
            "$ref": "lf.a2a.v1.Message.jsonschema.json"
          },
          "type": "array"
        },
        "id": {
          "default": "",
          "description": "Unique identifier (e.g. UUID) for the task, generated by the server for a\n new task.",
          "type": "string"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "A key/value object to store custom metadata about a task."
        },
        "status": {
          "$ref": "lf.a2a.v1.TaskStatus.jsonschema.json",
          "description": "The current status of a `Task`, including `state` and a `message`."
        }
      },
      "title": "Task",
      "type": "object"
    },
    "Task Artifact Update Event": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A task delta where an artifact has been generated.",
      "patternProperties": {
        "^(context_id)$": {
          "default": "",
          "description": "The ID of the context that this task belongs to.",
          "type": "string"
        },
        "^(last_chunk)$": {
          "default": false,
          "description": "If true, this is the final chunk of the artifact.",
          "type": "boolean"
        },
        "^(task_id)$": {
          "default": "",
          "description": "The ID of the task for this artifact.",
          "type": "string"
        }
      },
      "properties": {
        "append": {
          "default": false,
          "description": "If true, the content of this artifact should be appended to a previously\n sent artifact with the same ID.",
          "type": "boolean"
        },
        "artifact": {
          "$ref": "lf.a2a.v1.Artifact.jsonschema.json",
          "description": "The artifact that was generated or updated."
        },
        "contextId": {
          "default": "",
          "description": "The ID of the context that this task belongs to.",
          "type": "string"
        },
        "lastChunk": {
          "default": false,
          "description": "If true, this is the final chunk of the artifact.",
          "type": "boolean"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "Optional. Metadata associated with the artifact update."
        },
        "taskId": {
          "default": "",
          "description": "The ID of the task for this artifact.",
          "type": "string"
        }
      },
      "title": "Task Artifact Update Event",
      "type": "object"
    },
    "Task Push Notification Config": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A container associating a push notification configuration with a specific task.",
      "patternProperties": {
        "^(push_notification_config)$": {
          "$ref": "lf.a2a.v1.PushNotificationConfig.jsonschema.json",
          "description": "The push notification configuration details."
        },
        "^(task_id)$": {
          "default": "",
          "description": "The ID of the task this configuration is associated with.",
          "type": "string"
        }
      },
      "properties": {
        "pushNotificationConfig": {
          "$ref": "lf.a2a.v1.PushNotificationConfig.jsonschema.json",
          "description": "The push notification configuration details."
        },
        "taskId": {
          "default": "",
          "description": "The ID of the task this configuration is associated with.",
          "type": "string"
        },
        "tenant": {
          "default": "",
          "description": "Optional. Tenant ID.",
          "type": "string"
        }
      },
      "title": "Task Push Notification Config",
      "type": "object"
    },
    "Task Status": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "A container for the status of a task",
      "properties": {
        "message": {
          "$ref": "lf.a2a.v1.Message.jsonschema.json",
          "description": "A message associated with the status."
        },
        "state": {
          "anyOf": [
            {
              "pattern": "^TASK_STATE_UNSPECIFIED$",
              "type": "string"
            },
            {
              "enum": [
                "TASK_STATE_SUBMITTED",
                "TASK_STATE_WORKING",
                "TASK_STATE_COMPLETED",
                "TASK_STATE_FAILED",
                "TASK_STATE_CANCELED",
                "TASK_STATE_INPUT_REQUIRED",
                "TASK_STATE_REJECTED",
                "TASK_STATE_AUTH_REQUIRED"
              ],
              "type": "string"
            },
            {
              "maximum": 2147483647,
              "minimum": -2147483648,
              "type": "integer"
            }
          ],
          "default": 0,
          "description": "The current state of this task.",
          "title": "Task State"
        },
        "timestamp": {
          "$ref": "google.protobuf.Timestamp.jsonschema.json",
          "description": "ISO 8601 Timestamp when the status was recorded.\n Example: \"2023-10-27T10:00:00Z\""
        }
      },
      "title": "Task Status",
      "type": "object"
    },
    "Task Status Update Event": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "additionalProperties": false,
      "description": "An event sent by the agent to notify the client of a change in a task's status.",
      "patternProperties": {
        "^(context_id)$": {
          "default": "",
          "description": "The ID of the context that the task belongs to.",
          "type": "string"
        },
        "^(task_id)$": {
          "default": "",
          "description": "The ID of the task that has changed.",
          "type": "string"
        }
      },
      "properties": {
        "contextId": {
          "default": "",
          "description": "The ID of the context that the task belongs to.",
          "type": "string"
        },
        "metadata": {
          "$ref": "google.protobuf.Struct.jsonschema.json",
          "description": "Optional. Metadata associated with the task update."
        },
        "status": {
          "$ref": "lf.a2a.v1.TaskStatus.jsonschema.json",
          "description": "The new status of the task."
        },
        "taskId": {
          "default": "",
          "description": "The ID of the task that has changed.",
          "type": "string"
        }
      },
      "title": "Task Status Update Event",
      "type": "object"
    }
  }
}
</code></pre>

---

# Page: /partners/

## Partners

<p>Below is a list of partners (and a link to their A2A announcement or blog post, if available) who are part of the A2A community and are helping build, codify, and adopt A2A as the standard protocol for AI agents to communicate and collaborate effectively with each other and with users.</p> <ul> <li>A2A Net</li> <li>Accelirate Inc</li> <li>Accenture</li> <li>Activeloop</li> <li>Adobe</li> <li>AG2AI</li> <li>AI21 Labs</li> <li>AI71</li> <li>Aisera</li> <li>AliCloud</li> <li>Almawave.it</li> <li>AmikoNet</li> <li>ArcBlock</li> <li>Arize</li> <li>Articul8</li> <li>ask-ai.com</li> <li>Atlassian</li> <li>Auth0</li> <li>Autodesk</li> <li>AWS</li> <li>Beekeeper</li> <li>BCG</li> <li>Block Inc</li> <li>Bloomberg LP</li> <li>BLUEISH Inc</li> <li>BMC Software Inc</li> <li>Boomi</li> <li>Box</li> <li>Bridge2Things Automation Process GmbH</li> <li>Cafe 24</li> <li>C3 AI</li> <li>Capgemini</li> <li>Chronosphere</li> <li>Cisco</li> <li>Codimite PTE LTD</li> <li>Cognigy</li> <li>Cognizant</li> <li>Cohere</li> <li>Collibra</li> <li>Confluent</li> <li>Contextual</li> <li>Cotality (fka Corelogic)</li> <li>Crubyt</li> <li>Cyderes</li> <li>Datadog</li> <li>DataRobot</li> <li>DataStax</li> <li>Decagon.ai</li> <li>Deloitte</li> <li>Devnagri</li> <li>Deutsche Telekom</li> <li>Dexter Tech Labs</li> <li>Distyl.ai</li> <li>Elastic</li> <li>Ema.co</li> <li>EPAM</li> <li>Eviden (Atos Group)</li> <li>fractal.ai</li> <li>GenAI Nebula9.ai Solutions Pvt Ltd</li> <li>Glean</li> <li>Global Logic</li> <li>Gravitee</li> <li>GrowthLoop</li> <li>Guru</li> <li>Harness</li> <li>HCLTech</li> <li>Headwaters</li> <li>Hellotars</li> <li>Hexaware</li> <li>HUMAN</li> <li>IBM Research</li> <li>Incorta</li> <li>Infinitus</li> <li>InfoSys</li> <li>Intuit</li> <li>Iron Mountain</li> <li>JetBrains</li> <li>JFrog</li> <li>Kakao</li> <li>King's College London</li> <li>KPMG</li> <li>Kyndryl</li> <li>LabelBox</li> <li>LangChain</li> <li>LG CNS</li> <li>Livex.ai</li> <li>LlamaIndex</li> <li>LTIMindTtree</li> <li>Lumeris</li> <li>Lyzr.ai</li> <li>Magyar Telekom</li> <li>MasOrange</li> <li>Microsoft</li> <li>MindsDB</li> <li>McKinsey</li> <li>MongoDB</li> <li>Monite</li> <li>Neo4j</li> <li>New Relic</li> <li>Nisum</li> <li>Noorle Inc</li> <li>NTT DATA</li> <li>Optimizely Inc</li> <li>Oracle / NetSuite</li> <li>Palo Alto Networks</li> <li>PancakeAI</li> <li>ParkourSC</li> <li>Pendo</li> <li>PerfAI.ai</li> <li>Personal AI</li> <li>Poppulo</li> <li>Productive Edge</li> <li>Proofs</li> <li>Publicis Sapient</li> <li>PWC</li> <li>Quantiphi</li> <li>Radix</li> <li>RagaAI Inc</li> <li>Red Hat</li> <li>Reltio Inc</li> <li>S&amp;P</li> <li>Sage</li> <li>Salesforce</li> <li>SAP</li> <li>Sayone Technologies</li> <li>ServiceNow</li> <li>Siemens AG</li> <li>SoftBank Corp</li> <li>Solace</li> <li>Solo.io</li> <li>Stacklok, Inc</li> <li>Supertab</li> <li>Suzega</li> <li>TCS</li> <li>Tech Mahindra</li> <li>Telefonica</li> <li>Test Innovation Technology</li> <li>the artinet project</li> <li>Think41</li> <li>Thoughtworks</li> <li>Tredence</li> <li>Two Tall Totems Ltd. DBA TTT Studios</li> <li>Typeface</li> <li>UKG</li> <li>UiPath</li> <li>Upwork, Inc.</li> <li>Ushur, Inc.</li> <li>Valle AI</li> <li>Valtech</li> <li>Vervelo</li> <li>VoltAgent</li> <li>Weights &amp; Biases</li> <li>Wipro</li> <li>Workday</li> <li>Writer</li> <li>Zenity</li> <li>Zeotap</li> <li>Zocket Technologies , Inc.</li> <li>Zoom</li> <li>zyprova</li> </ul>

---

# Page: /roadmap/

## A2A protocol roadmap

<p>Last updated: Jul 16, 2025</p>

## Near-term initiatives

<ul> <li>Release <code>0.3</code> version of the protocol which we intend to keep supported and without breaking changes for a significant amount of time with backward compatibility of the SDKs starting at version <code>0.3</code>. As part of this release there are a few known breaking changes including:<ul> <li>Update the <code>/.well-known/agent.json</code> path for hosting Agent Cards to <code>/.well-known/agent-card.json</code> based on feedback from IANA.</li> <li>Refactor class fields to be more Pythonic and adopt <code>snake_case</code>. PR 199</li> </ul> </li> <li>Solidify the support for A2A extensions with SDK support (starting with the Python SDK) and publishing sample extensions.</li> <li>Introduce support for signed Agent Cards Discussion 199 to allow verifying the integrity of Agent Card content.</li> <li>Enhance the client side support in SDK (starting with Python) to expose ready-to-use A2A clients, streamlined auth handling and improved handling of tasks.</li> </ul> <p>To review recent protocol changes see Release Notes.</p>

## Governance

<p>The protocol has been donated to the Linux Foundation. The TSC is working on implementing a governance structure that prioritizes community-led development with standardized processes for contributing to the specification, SDKs and tooling. As part of the effort there will be dedicated working groups created for specific areas of the protocol.</p>

## Agent Registry

<p>Agent Registry enables the discovery of agents and is a critical component of a multi-agent system. There is an active and ongoing discussion in the community around the latest Discussion 741.</p>

## Validation

<p>As the A2A ecosystem matures, it becomes critical for the A2A community to have tools to validate their agents. The community has launched two efforts to help with validation which the group will continue to enhance in the coming months. Learn more about A2A Inspector and the A2A Protocol Technology Compatibility Kit (TCK).</p>

## SDKs

<p>A2A Project currently hosts SDKs in five languages (Python, Go, JS, Java, .NET).</p>

## Community best practices

<p>As companies and individuals deploy A2A systems at an increasing pace, we are looking to accelerate the learning of the community by collecting and sharing the best practices and success stories that A2A enabled.</p>

---

# Page: /specification/

## Agent2Agent (A2A) Protocol Specification (Release Candidate v1.0)

Latest Released Version <code>0.3.0</code> <p>Previous Versions</p> <ul> <li><code>0.2.6</code></li> <li><code>0.2.5</code></li> <li><code>0.2.4</code></li> <li><code>0.2.0</code></li> <li><code>0.1.0</code></li> </ul> <p>See Release Notes for changes made between versions.</p>

## 1. Introduction

<p>The Agent2Agent (A2A) Protocol is an open standard designed to facilitate communication and interoperability between independent, potentially opaque AI agent systems. In an ecosystem where agents might be built using different frameworks, languages, or by different vendors, A2A provides a common language and interaction model.</p> <p>This document provides the detailed technical specification for the A2A protocol. Its primary goal is to enable agents to:</p> <ul> <li>Discover each other's capabilities.</li> <li>Negotiate interaction modalities (text, files, structured data).</li> <li>Manage collaborative tasks.</li> <li>Securely exchange information to achieve user goals without needing access to each other's internal state, memory, or tools.</li> </ul>

## 1.1. Key Goals of A2A

<ul> <li>Interoperability: Bridge the communication gap between disparate agentic systems.</li> <li>Collaboration: Enable agents to delegate tasks, exchange context, and work together on complex user requests.</li> <li>Discovery: Allow agents to dynamically find and understand the capabilities of other agents.</li> <li>Flexibility: Support various interaction modes including synchronous request/response, streaming for real-time updates, and asynchronous push notifications for long-running tasks.</li> <li>Security: Facilitate secure communication patterns suitable for enterprise environments, relying on standard web security practices.</li> <li>Asynchronicity: Natively support long-running tasks and interactions that may involve human-in-the-loop scenarios.</li> </ul>

## 1.2. Guiding Principles

<ul> <li>Simple: Reuse existing, well-understood standards (HTTP, JSON-RPC 2.0, Server-Sent Events).</li> <li>Enterprise Ready: Address authentication, authorization, security, privacy, tracing, and monitoring by aligning with established enterprise practices.</li> <li>Async First: Designed for (potentially very) long-running tasks and human-in-the-loop interactions.</li> <li>Modality Agnostic: Support exchange of diverse content types including text, audio/video (via file references), structured data/forms, and potentially embedded UI components (e.g., iframes referenced in parts).</li> <li>Opaque Execution: Agents collaborate based on declared capabilities and exchanged information, without needing to share their internal thoughts, plans, or tool implementations.</li> </ul> <p>For a broader understanding of A2A's purpose and benefits, see What is A2A?.</p>

## 1.3. Specification Structure

<p>This specification is organized into three distinct layers that work together to provide a complete protocol definition:</p> <pre><code>graph TB
    subgraph L1 ["A2A Data Model"]
        direction LR
        A[Task] ~~~ B[Message] ~~~ C[AgentCard] ~~~ D[Part] ~~~ E[Artifact] ~~~ F[Extension]
    end

    subgraph L2 ["A2A Operations"]
        direction LR
        G[Send Message] ~~~ H[Stream Message] ~~~ I[Get Task] ~~~ J[List Tasks] ~~~ K[Cancel Task] ~~~ L[Get Agent Card]
    end

    subgraph L3 ["Protocol Bindings"]
        direction LR
        M[JSON-RPC Methods] ~~~ N[gRPC RPCs] ~~~ O[HTTP/REST Endpoints] ~~~ P[Custom Bindings]
    end

    %% Dependencies between layers
    L1 --&gt; L2
    L2 --&gt; L3


    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style C fill:#e1f5fe
    style D fill:#e1f5fe
    style E fill:#e1f5fe
    style F fill:#e1f5fe

    style G fill:#f3e5f5
    style H fill:#f3e5f5
    style I fill:#f3e5f5
    style J fill:#f3e5f5
    style K fill:#f3e5f5
    style L fill:#f3e5f5

    style M fill:#e8f5e8
    style N fill:#e8f5e8
    style O fill:#e8f5e8

    style L1 fill:#f0f8ff,stroke:#333,stroke-width:2px
    style L2 fill:#faf0ff,stroke:#333,stroke-width:2px
    style L3 fill:#f0fff0,stroke:#333,stroke-width:2px</code></pre> <p>Layer 1: Canonical Data Model defines the core data structures and message formats that all A2A implementations must understand. These are protocol agnostic definitions expressed as Protocol Buffer messages.</p> <p>Layer 2: Abstract Operations describes the fundamental capabilities and behaviors that A2A agents must support, independent of how they are exposed over specific protocols.</p> <p>Layer 3: Protocol Bindings provides concrete mappings of the abstract operations and data structures to specific protocol bindings (JSON-RPC, gRPC, HTTP/REST), including method names, endpoint patterns, and protocol-specific behaviors.</p> <p>This layered approach ensures that:</p> <ul> <li>Core semantics remain consistent across all protocol bindings</li> <li>New protocol bindings can be added without changing the fundamental data model</li> <li>Developers can reason about A2A operations independently of binding concerns</li> <li>Interoperability is maintained through shared understanding of the canonical data model</li> </ul>

## 1.4 Normative Content

<p>In addition to the protocol requirements defined in this document, the file <code>spec/a2a.proto</code> is the single authoritative normative definition of all protocol data objects and request/response messages. A generated JSON artifact (<code>spec/a2a.json</code>, produced at build time and not committed) MAY be published for convenience to tooling and the website, but it is a non-normative build artifact. SDK language bindings, schemas, and any other derived forms MUST be regenerated from the proto (directly or via code generation) rather than edited manually.</p> <p>Change Control and Deprecation Lifecycle:</p> <ul> <li>Introduction: When a proto message or field is renamed, the new name is added while existing published names remain available, but marked deprecated, until the next major release.</li> <li>Documentation: Migration guidance MUST be provided via an ancillary document when introducing major breaking changes.</li> <li>Anchors: Legacy documentation anchors MUST be preserved (as hidden HTML anchors) to avoid breaking inbound links.</li> <li>SDK/Schema Aliases: SDKs and JSON Schemas SHOULD provide deprecated alias types/definitions to maintain backward compatibility.</li> <li>Removal: A deprecated name SHOULD NOT be removed earlier than the next major version after introduction of its replacement.</li> </ul> <p>Automated Generation:</p> <p>The documentation build generates <code>specification/json/a2a.json</code> on-the-fly (the file is not tracked in source control). Future improvements may publish an OpenAPI v3 + JSON Schema bundle for enhanced tooling.</p> <p>Rationale:</p> <p>Centering the proto file as the normative source ensures protocol neutrality, reduces specification drift, and provides a deterministic evolution path for the ecosystem.</p>

## 2.1. Requirements Language

<p>The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.</p>

## 2.2. Core Concepts

<p>A2A revolves around several key concepts. For detailed explanations, please refer to the Key Concepts guide.</p> <ul> <li>A2A Client: An application or agent that initiates requests to an A2A Server on behalf of a user or another system.</li> <li>A2A Server (Remote Agent): An agent or agentic system that exposes an A2A-compliant endpoint, processing tasks and providing responses.</li> <li>Agent Card: A JSON metadata document published by an A2A Server, describing its identity, capabilities, skills, service endpoint, and authentication requirements.</li> <li>Message: A communication turn between a client and a remote agent, having a <code>role</code> ("user" or "agent") and containing one or more <code>Parts</code>.</li> <li>Task: The fundamental unit of work managed by A2A, identified by a unique ID. Tasks are stateful and progress through a defined lifecycle.</li> <li>Part: The smallest unit of content within a Message or Artifact. Parts can contain text, file references, or structured data.</li> <li>Artifact: An output (e.g., a document, image, structured data) generated by the agent as a result of a task, composed of <code>Parts</code>.</li> <li>Streaming: Real-time, incremental updates for tasks (status changes, artifact chunks) delivered via protocol-specific streaming mechanisms.</li> <li>Push Notifications: Asynchronous task updates delivered via server-initiated HTTP POST requests to a client-provided webhook URL, for long-running or disconnected scenarios.</li> <li>Context: An optional, server-generated identifier to logically group related tasks and messages.</li> <li>Extension: A mechanism for agents to provide additional functionality or data beyond the core A2A specification.</li> </ul>

## 3. A2A Protocol Operations

<p>This section describes the core operations of the A2A protocol in a binding-independent manner. These operations define the fundamental capabilities that all A2A implementations must support, regardless of the underlying binding mechanism.</p>

## 3.1. Core Operations

<p>The following operations define the fundamental capabilities that all A2A implementations must support, independent of the specific protocol binding used. For a quick reference mapping of these operations to protocol-specific method names and endpoints, see Section 5.3 (Method Mapping Reference). For detailed protocol-specific implementation details, see:</p> <ul> <li>Section 9: JSON-RPC Protocol Binding</li> <li>Section 10: gRPC Protocol Binding</li> <li>Section 11: HTTP+JSON/REST Protocol Binding</li> </ul>

## 3.1.1. Send Message

<p>The primary operation for initiating agent interactions. Clients send a message to an agent and receive either a task that tracks the processing or a direct response message.</p> <p>Inputs:</p> <ul> <li><code>SendMessageRequest</code>: Request object containing the message, configuration, and metadata</li> </ul> <p>Outputs:</p> <ul> <li><code>Task</code>: A task object representing the processing of the message, OR</li> <li><code>Message</code>: A direct response message (for simple interactions that don't require task tracking)</li> </ul> <p>Errors:</p> <ul> <li><code>ContentTypeNotSupportedError</code>: A Media Type provided in the request's message parts is not supported by the agent.</li> <li><code>UnsupportedOperationError</code>: Messages sent to Tasks that are in a terminal state (e.g., completed, canceled, rejected) cannot accept further messages.</li> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> </ul> <p>Behavior:</p> <p>The agent MAY create a new <code>Task</code> to process the provided message asynchronously or MAY return a direct <code>Message</code> response for simple interactions. The operation MUST return immediately with either task information or response message. Task processing MAY continue asynchronously after the response when a <code>Task</code> is returned.</p>

## 3.1.2. Send Streaming Message

<p>Similar to Send Message but with real-time streaming of updates during processing.</p> <p>Inputs:</p> <ul> <li><code>SendMessageRequest</code>: Request object containing the message, configuration, and metadata</li> </ul> <p>Outputs:</p> <ul> <li><code>Stream Response</code> object containing:<ul> <li>Initial response: <code>Task</code> object OR <code>Message</code> object</li> <li>Subsequent events following a <code>Task</code> MAY include stream of <code>TaskStatusUpdateEvent</code> and <code>TaskArtifactUpdateEvent</code> objects</li> </ul> </li> <li>Final completion indicator</li> </ul> <p>Errors:</p> <ul> <li><code>UnsupportedOperationError</code>: Streaming is not supported by the agent (see Capability Validation).</li> <li><code>UnsupportedOperationError</code>: Messages sent to Tasks that are in a terminal state (e.g., completed, canceled, rejected) cannot accept further messages.</li> <li><code>ContentTypeNotSupportedError</code>: A Media Type provided in the request's message parts is not supported by the agent.</li> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> </ul> <p>Behavior:</p> <p>The operation MUST establish a streaming connection for real-time updates. The stream MUST follow one of these patterns:</p> <ol> <li> <p>Message-only stream: If the agent returns a <code>Message</code>, the stream MUST contain exactly one <code>Message</code> object and then close immediately. No task tracking or updates are provided.</p> </li> <li> <p>Task lifecycle stream: If the agent returns a <code>Task</code>, the stream MUST begin with the Task object, followed by zero or more <code>TaskStatusUpdateEvent</code> or <code>TaskArtifactUpdateEvent</code> objects. The stream MUST close when the task reaches a terminal state (e.g. completed, failed, canceled, rejected).</p> </li> </ol> <p>The agent MAY return a <code>Task</code> for complex processing with status/artifact updates or MAY return a <code>Message</code> for direct streaming responses without task overhead. The implementation MUST provide immediate feedback on progress and intermediate results.</p>

## 3.1.3. Get Task

<p>Retrieves the current state (including status, artifacts, and optionally history) of a previously initiated task. This is typically used for polling the status of a task initiated with message/send, or for fetching the final state of a task after being notified via a push notification or after a stream has ended.</p> <p>Inputs:</p> <p>Represents a request for the <code>GetTask</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>id</code> <code>string</code> Yes The resource ID of the task to retrieve. <code>historyLength</code> <code>integer</code> No The maximum number of most recent messages from the task's history to retrieve. An unset value means the client does not impose any limit. A value of zero is a request to not include any messages. The server MUST NOT return more messages than the provided value, but MAY apply a lower limit. <p>See History Length Semantics for details about <code>historyLength</code>.</p> <p>Outputs:</p> <ul> <li><code>Task</code>: Current state and artifacts of the requested task</li> </ul> <p>Errors:</p> <ul> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> </ul>

## 3.1.4. List Tasks

<p>Retrieves a list of tasks with optional filtering and pagination capabilities. This method allows clients to discover and manage multiple tasks across different contexts or with specific status criteria.</p> <p>Inputs:</p> <p>Parameters for listing tasks with optional filtering criteria.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Tenant ID, provided as a path parameter. <code>contextId</code> <code>string</code> No Filter tasks by context ID to get tasks from a specific conversation or session. <code>status</code> <code>TaskState</code> No Filter tasks by their current status state. <code>pageSize</code> <code>integer</code> No The maximum number of tasks to return. The service may return fewer than this value. If unspecified, at most 50 tasks will be returned. The minimum value is 1. The maximum value is 100. <code>pageToken</code> <code>string</code> No A page token, received from a previous <code>ListTasks</code> call. <code>ListTasksResponse.next_page_token</code>. Provide this to retrieve the subsequent page. <code>historyLength</code> <code>integer</code> No The maximum number of messages to include in each task's history. <code>statusTimestampAfter</code> <code>timestamp</code> No Filter tasks which have a status updated after the provided timestamp in ISO 8601 format (e.g., "2023-10-27T10:00:00Z"). Only tasks with a status timestamp time greater than or equal to this value will be returned. <code>includeArtifacts</code> <code>boolean</code> No Whether to include artifacts in the returned tasks. Defaults to false to reduce payload size. <p>When <code>includeArtifacts</code> is false (the default), the artifacts field MUST be omitted entirely from each Task object in the response. The field should not be present as an empty array or null value. When <code>includeArtifacts</code> is true, the artifacts field should be included with its actual content (which may be an empty array if the task has no artifacts).</p> <p>Outputs:</p> <p>Result object for <code>ListTasks</code> method containing an array of tasks and pagination information.</p> Field Type Required Description <code>tasks</code> array of <code>Task</code> Yes Array of tasks matching the specified criteria. <code>nextPageToken</code> <code>string</code> Yes A token to retrieve the next page of results, or empty if there are no more results in the list. <code>pageSize</code> <code>integer</code> Yes The page size used for this response. <code>totalSize</code> <code>integer</code> Yes Total number of tasks available (before pagination). <p>Note on <code>nextPageToken</code>: The <code>nextPageToken</code> field MUST always be present in the response. When there are no more results to retrieve (i.e., this is the final page), the field MUST be set to an empty string (""). Clients should check for an empty string to determine if more pages are available.</p> <p>Errors:</p> <p>None specific to this operation beyond standard protocol errors.</p> <p>Behavior:</p> <p>The operation MUST return only tasks visible to the authenticated client and MUST use cursor-based pagination for performance and consistency. Tasks MUST be sorted by last update time in descending order. Implementations MUST implement appropriate authorization scoping to ensure clients can only access authorized tasks. See Section 13.1 Data Access and Authorization Scoping for detailed security requirements.</p> <p>Pagination Strategy:</p> <p>This method uses cursor-based pagination (via <code>pageToken</code>/<code>nextPageToken</code>) rather than offset-based pagination for better performance and consistency, especially with large datasets. Cursor-based pagination avoids the "deep pagination problem" where skipping large numbers of records becomes inefficient for databases. This approach is consistent with the gRPC specification, which also uses cursor-based pagination (page_token/next_page_token).</p> <p>Ordering:</p> <p>Implementations MUST return tasks sorted by their status timestamp time in descending order (most recently updated tasks first). This ensures consistent pagination and allows clients to efficiently monitor recent task activity.</p>

## 3.1.5. Cancel Task

<p>Requests the cancellation of an ongoing task. The server will attempt to cancel the task, but success is not guaranteed (e.g., the task might have already completed or failed, or cancellation might not be supported at its current stage).</p> <p>Inputs:</p> <p>Represents a request for the <code>CancelTask</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>id</code> <code>string</code> Yes The resource ID of the task to cancel. <code>metadata</code> <code>object</code> No A flexible key-value map for passing additional context or parameters. <p>Outputs:</p> <ul> <li>Updated <code>Task</code> with cancellation status</li> </ul> <p>Errors:</p> <ul> <li><code>TaskNotCancelableError</code>: The task is not in a cancelable state (e.g., already completed, failed, or canceled).</li> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> </ul> <p>Behavior:</p> <p>The operation attempts to cancel the specified task and returns its updated state.</p>

## 3.1.6. Subscribe to Task

<p>Establishes a streaming connection to receive updates for an existing task.</p> <p>Inputs:</p> <p>Represents a request for the <code>SubscribeToTask</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>id</code> <code>string</code> Yes The resource ID of the task to subscribe to. <p>Outputs:</p> <ul> <li><code>Stream Response</code> object containing:<ul> <li>Initial response: <code>Task</code> object with current state</li> <li>Stream of <code>TaskStatusUpdateEvent</code> and <code>TaskArtifactUpdateEvent</code> objects</li> </ul> </li> </ul> <p>Errors:</p> <ul> <li><code>UnsupportedOperationError</code>: Streaming is not supported by the agent (see Capability Validation).</li> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> <li><code>UnsupportedOperationError</code>: The operation is attempted on a task that is in a terminal state (<code>completed</code>, <code>failed</code>, <code>canceled</code>, or <code>rejected</code>).</li> </ul> <p>Behavior:</p> <p>The operation enables real-time monitoring of task progress and can be used with any task that is not in a terminal state. The stream MUST terminate when the task reaches a terminal state (<code>completed</code>, <code>failed</code>, <code>canceled</code>, or <code>rejected</code>).</p> <p>The operation MUST return a <code>Task</code> object as the first event in the stream, representing the current state of the task at the time of subscription. This prevents a potential loss of information between a call to <code>GetTask</code> and calling <code>SubscribeToTask</code>.</p>

## 3.1.7. Create Push Notification Config

<p>Creates a push notification configuration for a task to receive asynchronous updates via webhook.</p> <p>Inputs:</p> <p>Represents a request for the <code>CreateTaskPushNotificationConfig</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>config</code> <code>PushNotificationConfig</code> Yes The configuration to create. <p>Outputs:</p> <ul> <li><code>PushNotificationConfig</code>: Created configuration with assigned ID</li> </ul> <p>Errors:</p> <ul> <li><code>PushNotificationNotSupportedError</code>: Push notifications are not supported by the agent (see Capability Validation).</li> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> </ul> <p>Behavior:</p> <p>The operation MUST establish a webhook endpoint for task update notifications. When task updates occur, the agent will send HTTP POST requests to the configured webhook URL with <code>StreamResponse</code> payloads (see Push Notification Payload for details). This operation is only available if the agent supports push notifications capability. The configuration MUST persist until task completion or explicit deletion.</p> <p></p>

## 3.1.8. Get Push Notification Config

<p>Retrieves an existing push notification configuration for a task.</p> <p>Inputs:</p> <p>Represents a request for the <code>GetTaskPushNotificationConfig</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>id</code> <code>string</code> Yes The resource ID of the configuration to retrieve. <p>Outputs:</p> <ul> <li><code>PushNotificationConfig</code>: The requested configuration</li> </ul> <p>Errors:</p> <ul> <li><code>PushNotificationNotSupportedError</code>: Push notifications are not supported by the agent (see Capability Validation).</li> <li><code>TaskNotFoundError</code>: The push notification configuration does not exist.</li> </ul> <p>Behavior:</p> <p>The operation MUST return configuration details including webhook URL and notification settings. The operation MUST fail if the configuration does not exist or the client lacks access.</p>

## 3.1.9. List Push Notification Configs

<p>Retrieves all push notification configurations for a task.</p> <p>Inputs:</p> <p>Represents a request for the <code>ListTaskPushNotificationConfigs</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>pageSize</code> <code>integer</code> No The maximum number of configurations to return. <code>pageToken</code> <code>string</code> No A page token received from a previous <code>ListTaskPushNotificationConfigsRequest</code> call. <p>Outputs:</p> <p>Represents a successful response for the <code>ListTaskPushNotificationConfigs</code> method.</p> Field Type Required Description <code>configs</code> array of <code>TaskPushNotificationConfig</code> No The list of push notification configurations. <code>nextPageToken</code> <code>string</code> No A token to retrieve the next page of results, or empty if there are no more results in the list. <p>Errors:</p> <ul> <li><code>PushNotificationNotSupportedError</code>: Push notifications are not supported by the agent (see Capability Validation).</li> <li><code>TaskNotFoundError</code>: The task ID does not exist or is not accessible.</li> </ul> <p>Behavior:</p> <p>The operation MUST return all active push notification configurations for the specified task and MAY support pagination for tasks with many configurations.</p>

## 3.1.10. Delete Push Notification Config

<p>Removes a push notification configuration for a task.</p> <p>Inputs:</p> <p>Represents a request for the <code>DeleteTaskPushNotificationConfig</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>id</code> <code>string</code> Yes The resource ID of the configuration to delete. <p>Outputs:</p> <ul> <li>Confirmation of deletion (implementation-specific)</li> </ul> <p>Errors:</p> <ul> <li><code>PushNotificationNotSupportedError</code>: Push notifications are not supported by the agent (see Capability Validation).</li> <li><code>TaskNotFoundError</code>: The task ID does not exist.</li> </ul> <p>Behavior:</p> <p>The operation MUST permanently remove the specified push notification configuration. No further notifications will be sent to the configured webhook after deletion. This operation MUST be idempotent - multiple deletions of the same config have the same effect.</p>

## 3.1.11. Get Extended Agent Card

<p>Retrieves a potentially more detailed version of the Agent Card after the client has authenticated. This endpoint is available only if <code>AgentCard.capabilities.extendedAgentCard</code> is <code>true</code>.</p> <p>Inputs:</p> <p>Represents a request for the <code>GetExtendedAgentCard</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <p>Outputs:</p> <ul> <li><code>AgentCard</code>: A complete Agent Card object, which may contain additional details or skills not present in the public card</li> </ul> <p>Errors:</p> <ul> <li><code>UnsupportedOperationError</code>: The agent does not support authenticated extended cards (see Capability Validation).</li> <li><code>ExtendedAgentCardNotConfiguredError</code>: The agent declares support but does not have an extended agent card configured.</li> </ul> <p>Behavior:</p> <ul> <li>Authentication: The client MUST authenticate the request using one of the schemes declared in the public <code>AgentCard.securitySchemes</code> and <code>AgentCard.security</code> fields.</li> <li>Extended Information: The operation MAY return different details based on client authentication level, including additional skills, capabilities, or configuration not available in the public Agent Card.</li> <li>Card Replacement: Clients retrieving this extended card SHOULD replace their cached public Agent Card with the content received from this endpoint for the duration of their authenticated session or until the card's version changes.</li> <li>Availability: This operation is only available if the public Agent Card declares <code>capabilities.extendedAgentCard: true</code>.</li> </ul> <p>For detailed security guidance on extended agent cards, see Section 13.3 Extended Agent Card Access Control.</p>

## 3.2. Operation Parameter Objects

<p>This section defines common parameter objects used across multiple operations.</p>

## 3.2.1. SendMessageRequest

<p>Represents a request for the <code>SendMessage</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>message</code> <code>Message</code> Yes The message to send to the agent. <code>configuration</code> <code>SendMessageConfiguration</code> No Configuration for the send request. <code>metadata</code> <code>object</code> No A flexible key-value map for passing additional context or parameters.

## 3.2.2. SendMessageConfiguration

<p>Configuration of a send message request.</p> Field Type Required Description <code>acceptedOutputModes</code> array of <code>string</code> No A list of media types the client is prepared to accept for response parts. Agents SHOULD use this to tailor their output. <code>pushNotificationConfig</code> <code>PushNotificationConfig</code> No Configuration for the agent to send push notifications for task updates. <code>historyLength</code> <code>integer</code> No The maximum number of most recent messages from the task's history to retrieve in the response. An unset value means the client does not impose any limit. A value of zero is a request to not include any messages. The server MUST NOT return more messages than the provided value, but MAY apply a lower limit. <code>blocking</code> <code>boolean</code> No If <code>true</code>, the operation MUST wait until the task reaches a terminal state (<code>COMPLETED</code>, <code>FAILED</code>, <code>CANCELED</code>, <code>REJECTED</code>) or an interrupted state (<code>INPUT_REQUIRED</code>, <code>AUTH_REQUIRED</code>) before returning. Default is <code>false</code>. <p>Blocking vs Non-Blocking Execution:</p> <p>The <code>blocking</code> field in <code>SendMessageConfiguration</code> controls whether the operation waits for task completion:</p> <ul> <li> <p>Blocking (<code>blocking: true</code>): The operation MUST wait until the task reaches a terminal state (<code>COMPLETED</code>, <code>FAILED</code>, <code>CANCELED</code>, <code>REJECTED</code>) or an interrupted state (<code>INPUT_REQUIRED</code>, <code>AUTH_REQUIRED</code>) before returning. The response MUST include the latest task state with all artifacts and status information.</p> </li> <li> <p>Non-Blocking (<code>blocking: false</code>): The operation MUST return immediately after creating the task, even if processing is still in progress. The returned task will have an in-progress state (e.g., <code>working</code>, <code>input_required</code>). It is the caller's responsibility to poll for updates using Get Task, subscribe via Subscribe to Task, or receive updates via push notifications.</p> </li> </ul> <p>The <code>blocking</code> field has no effect:</p> <ul> <li>when the operation returns a direct <code>Message</code> response instead of a task.</li> <li>for streaming operations, which always return updates in real-time.</li> <li>on configured push notification configurations, which operates independently of blocking mode.</li> </ul>

## 3.2.3. Stream Response

<p>A wrapper object used in streaming operations to encapsulate different types of response data.</p> Field Type Required Description <code>task</code> <code>Task</code> Optional (OneOf) A Task object containing the current state of the task. <code>message</code> <code>Message</code> Optional (OneOf) A Message object containing a message from the agent. <code>statusUpdate</code> <code>TaskStatusUpdateEvent</code> Optional (OneOf) An event indicating a task status update. <code>artifactUpdate</code> <code>TaskArtifactUpdateEvent</code> Optional (OneOf) An event indicating a task artifact update. <p>Note: A <code>StreamResponse</code> MUST contain exactly one of the following: <code>task</code>, <code>message</code>, <code>statusUpdate</code>, <code>artifactUpdate</code></p> <p>This wrapper allows streaming endpoints to return different types of updates through a single response stream while maintaining type safety.</p>

## 3.2.4. History Length Semantics

<p>The <code>historyLength</code> parameter appears in multiple operations and controls how much task history is returned in responses. This parameter follows consistent semantics across all operations:</p> <ul> <li>Unset/undefined: No limit imposed; server returns its default amount of history (implementation-defined, may be all history)</li> <li>0: No history should be returned; the <code>history</code> field SHOULD be omitted</li> <li>&gt; 0: Return at most this many recent messages from the task's history</li> </ul>

## 3.2.5. Metadata

<p>A flexible key-value map for passing additional context or parameters with operations. Metadata keys and are strings and values can be any valid value that can be represented in JSON. <code>Extensions</code> can be used to strongly type metadata values for specific use cases.</p>

## 3.2.6 Service Parameters

<p>A key-value map for passing horizontally applicable context or parameters with case-insensitive string keys and case-sensitive string values. The transmission mechanism for these service parameter key-value pairs is defined by the specific protocol binding (e.g., HTTP headers for HTTP-based bindings, gRPC metadata for gRPC bindings). Custom protocol bindings MUST specify how service parameters are transmitted in their binding specification.</p> <p>Standard A2A Service Parameters:</p> Name Description Example Value <code>A2A-Extensions</code> Comma-separated list of extension URIs that the client wants to use for the request <code>https://example.com/extensions/geolocation/v1,https://standards.org/extensions/citations/v1</code> <code>A2A-Version</code> The A2A protocol version that the client is using. If the version is not supported, the agent returns <code>VersionNotSupportedError</code> <code>0.3</code> <p>As service parameter names MAY need to co-exist with other parameters defined by the underlying transport protocol or infrastructure, all service parameters defined by this specification will be prefixed with <code>a2a-</code>.</p>

## 3.3.1. Idempotency

<ul> <li>Get operations (Get Task, List Tasks, Get Extended Agent Card) are naturally idempotent</li> <li>Send Message operations MAY be idempotent. Agents may utilize the messageId to detect duplicate messages.</li> <li>Cancel Task operations are idempotent - multiple cancellation requests have the same effect. A duplicate cancellation request MAY return <code>TaskNotFoundError</code> if the task has already been canceled and purged.</li> </ul>

## 3.3.2. Error Handling

<p>All operations may return errors in the following categories. Servers MUST return appropriate errors and SHOULD provide actionable information to help clients resolve issues.</p> <p>Error Categories and Server Requirements:</p> <ul> <li> <p>Authentication Errors: Invalid or missing credentials</p> <ul> <li>Servers MUST reject requests with invalid or missing authentication credentials</li> <li>Servers SHOULD include authentication challenge information in the error response</li> <li>Servers SHOULD specify which authentication scheme is required</li> <li>Example error codes: HTTP <code>401 Unauthorized</code>, gRPC <code>UNAUTHENTICATED</code>, JSON-RPC custom error</li> <li>Example scenarios: Missing bearer token, expired API key, invalid OAuth token</li> </ul> </li> <li> <p>Authorization Errors: Insufficient permissions for requested operation</p> <ul> <li>Servers MUST return an authorization error when the authenticated client lacks required permissions</li> <li>Servers SHOULD indicate what permission or scope is missing (without leaking sensitive information about resources the client cannot access)</li> <li>Servers MUST NOT reveal the existence of resources the client is not authorized to access</li> <li>Example error codes: HTTP <code>403 Forbidden</code>, gRPC <code>PERMISSION_DENIED</code>, JSON-RPC custom error</li> <li>Example scenarios: Attempting to access a task created by another user, insufficient OAuth scopes</li> </ul> </li> <li> <p>Validation Errors: Invalid input parameters or message format</p> <ul> <li>Servers MUST validate all input parameters before processing</li> <li>Servers SHOULD specify which parameter(s) failed validation and why</li> <li>Servers SHOULD provide guidance on valid parameter values or formats</li> <li>Example error codes: HTTP <code>400 Bad Request</code>, gRPC <code>INVALID_ARGUMENT</code>, JSON-RPC <code>-32602 Invalid params</code></li> <li>Example scenarios: Invalid task ID format, missing required message parts, unsupported content type</li> </ul> </li> <li> <p>Resource Errors: Requested task not found or not accessible</p> <ul> <li>Servers MUST return a not found error when a requested resource does not exist or is not accessible to the authenticated client</li> <li>Servers SHOULD NOT distinguish between "does not exist" and "not authorized" to prevent information leakage</li> <li>Example error codes: HTTP <code>404 Not Found</code>, gRPC <code>NOT_FOUND</code>, JSON-RPC custom error (see A2A-specific errors)</li> <li>Example scenarios: Task ID does not exist, task has been deleted, configuration not found</li> </ul> </li> <li> <p>System Errors: Internal agent failures or temporary unavailability</p> <ul> <li>Servers SHOULD return appropriate error codes for temporary failures vs. permanent errors</li> <li>Servers MAY include retry guidance (e.g., Retry-After header in HTTP)</li> <li>Servers SHOULD log system errors for diagnostic purposes</li> <li>Example error codes: HTTP <code>500 Internal Server Error</code> or <code>503 Service Unavailable</code>, gRPC <code>INTERNAL</code> or <code>UNAVAILABLE</code>, JSON-RPC <code>-32603 Internal error</code></li> <li>Example scenarios: Database connection failure, downstream service timeout, rate limit exceeded</li> </ul> </li> </ul> <p>Error Payload Structure:</p> <p>All error responses in the A2A protocol, regardless of binding, MUST convey the following information:</p> <ol> <li>Error Code: A machine-readable identifier for the error type (e.g., string code, numeric code, or protocol-specific status)</li> <li>Error Message: A human-readable description of the error</li> <li>Error Details (optional): Additional structured information about the error, such as:<ul> <li>Affected fields or parameters</li> <li>Contextual information (e.g., task ID, timestamp)</li> <li>Suggestions for resolution</li> </ul> </li> </ol> <p>Protocol bindings MUST map these elements to their native error representations while preserving semantic meaning. See binding-specific sections for concrete error format examples: JSON-RPC Error Handling, gRPC Error Handling, and HTTP/REST Error Handling.</p> <p>A2A-Specific Errors:</p> Error Name Description <code>TaskNotFoundError</code> The specified task ID does not correspond to an existing or accessible task. It might be invalid, expired, or already completed and purged. <code>TaskNotCancelableError</code> An attempt was made to cancel a task that is not in a cancelable state (e.g., it has already reached a terminal state like <code>completed</code>, <code>failed</code>, or <code>canceled</code>). <code>PushNotificationNotSupportedError</code> Client attempted to use push notification features but the server agent does not support them (i.e., <code>AgentCard.capabilities.pushNotifications</code> is <code>false</code>). <code>UnsupportedOperationError</code> The requested operation or a specific aspect of it is not supported by this server agent implementation. <code>ContentTypeNotSupportedError</code> A Media Type provided in the request's message parts or implied for an artifact is not supported by the agent or the specific skill being invoked. <code>InvalidAgentResponseError</code> An agent returned a response that does not conform to the specification for the current method. <code>ExtendedAgentCardNotConfiguredError</code> The agent does not have an extended agent card configured when one is required for the requested operation. <code>ExtensionSupportRequiredError</code> Server requested use of an extension marked as <code>required: true</code> in the Agent Card but the client did not declare support for it in the request. <code>VersionNotSupportedError</code> The A2A protocol version specified in the request (via <code>A2A-Version</code> service parameter) is not supported by the agent.

## 3.3.3. Asynchronous Processing

<p>A2A operations are designed for asynchronous task execution. Operations return immediately with either <code>Task</code> objects or <code>Message</code> objects, and when a Task is returned, processing continues in the background. Clients retrieve task updates through polling, streaming, or push notifications (see Section 3.5). Agents MAY accept additional messages for tasks in non-terminal states to enable multi-turn interactions (see Section 3.4).</p>

## 3.3.4. Capability Validation

<p>Agents declare optional capabilities in their <code>AgentCard</code>. When clients attempt to use operations or features that require capabilities not declared as supported in the Agent Card, the agent MUST return an appropriate error response:</p> <ul> <li>Push Notifications: If <code>AgentCard.capabilities.pushNotifications</code> is <code>false</code> or not present, operations related to push notification configuration (Create, Get, List, Delete) MUST return <code>PushNotificationNotSupportedError</code>.</li> <li>Streaming: If <code>AgentCard.capabilities.streaming</code> is <code>false</code> or not present, attempts to use <code>SendStreamingMessage</code> or <code>SubscribeToTask</code> operations MUST return <code>UnsupportedOperationError</code>.</li> <li>Extended Agent Card: If <code>AgentCard.capabilities.extendedAgentCard</code> is <code>false</code> or not present, attempts to call the Get Extended Agent Card operation MUST return <code>UnsupportedOperationError</code>. If the agent declares support but has not configured an extended card, it MUST return <code>ExtendedAgentCardNotConfiguredError</code>.</li> <li>Extensions: When a server requests use of an extension marked as <code>required: true</code> in the Agent Card but the client does not declare support for it, the agent MUST return <code>ExtensionSupportRequiredError</code>.</li> </ul> <p>Clients SHOULD validate capability support by examining the Agent Card before attempting operations that require optional capabilities.</p>

## 3.4. Multi-Turn Interactions

<p>The A2A protocol supports multi-turn conversations through context identifiers and task references, enabling agents to maintain conversational continuity across multiple interactions.</p>

## 3.4.1. Context Identifier Semantics

<p>A <code>contextId</code> is an identifier that logically groups multiple related <code>Task</code> and <code>Message</code> objects, providing continuity across a series of interactions.</p> <p>Generation and Assignment:</p> <ul> <li>Agents MUST generate a new <code>contextId</code> when processing a <code>Message</code> that does not include a <code>contextId</code> field</li> <li>The generated <code>contextId</code> MUST be included in the response (either <code>Task</code> or <code>Message</code>)</li> <li>Agents MUST accept and preserve client-provided <code>contextId</code> values if validations pass (i.e., it doesn't conflict with provided <code>taskId</code>)</li> <li><code>contextId</code> values SHOULD be treated as opaque identifiers by clients</li> </ul> <p>Grouping and Scope:</p> <ul> <li>A <code>contextId</code> logically groups multiple <code>Task</code> objects and <code>Message</code> objects that are part of the same conversational context</li> <li>All tasks and messages with the same <code>contextId</code> SHOULD be treated as part of the same conversational session</li> <li>Agents MAY use the <code>contextId</code> to maintain internal state, conversational history, or LLM context across multiple interactions</li> <li>Agents MAY implement context expiration or cleanup policies and SHOULD document any such policies</li> </ul>

## 3.4.2. Task Identifier Semantics

<p>A <code>taskId</code> is a unique identifier for a <code>Task</code> object, representing a stateful unit of work with a defined lifecycle.</p> <p>Generation and Assignment:</p> <ul> <li>Task IDs are server-generated when a new task is created in response to a <code>Message</code></li> <li>Agents MUST generate a unique <code>taskId</code> for each new task they create</li> <li>The generated <code>taskId</code> MUST be included in the <code>Task</code> object returned to the client</li> <li>When a client includes a <code>taskId</code> in a <code>Message</code>, it MUST reference an existing task</li> <li>Agents MUST return a <code>TaskNotFoundError</code> if the provided <code>taskId</code> does not correspond to an existing task</li> <li>Client-provided <code>taskId</code> values for creating new tasks is NOT supported</li> </ul>

## 3.4.3. Multi-Turn Conversation Patterns

<p>The A2A protocol supports several patterns for multi-turn interactions:</p> <p>Context Continuity:</p> <ul> <li><code>Task</code> objects maintain conversation context through the <code>contextId</code> field</li> <li>Clients MAY include the <code>contextId</code> in subsequent messages to indicate continuation of a previous interaction</li> <li>Clients MAY use <code>taskId</code> (with or without <code>contextId</code>) to continue or refine a specific task</li> <li>Clients MAY use <code>contextId</code> without <code>taskId</code> to start a new task within an existing conversation context</li> <li>Agents MUST infer <code>contextId</code> from the task if only <code>taskId</code> is provided</li> <li>Agents MUST reject messages containing mismatching <code>contextId</code> and <code>taskId</code> (i.e., the provided <code>contextId</code> is different from that of the referenced <code>Task</code>).</li> </ul> <p>Input Required State:</p> <ul> <li>Agents can request additional input mid-processing by transitioning a task to the <code>input-required</code> state</li> <li>The client continues the interaction by sending a new message with the same <code>taskId</code> and <code>contextId</code></li> </ul> <p>Follow-up Messages:</p> <ul> <li>Clients can send additional messages with <code>taskId</code> references to continue or refine existing tasks</li> <li>Clients SHOULD use the <code>referenceTaskIds</code> field in <code>Message</code> to explicitly reference related tasks</li> <li>Agents SHOULD use referenced tasks to understand the context and intent of follow-up requests</li> </ul> <p>Context Inheritance:</p> <ul> <li>New tasks created within the same <code>contextId</code> can inherit context from previous interactions</li> <li>Agents SHOULD leverage the shared <code>contextId</code> to provide contextually relevant responses</li> </ul>

## 3.5. Task Update Delivery Mechanisms

<p>The A2A protocol provides three complementary mechanisms for clients to receive updates about task progress and completion.</p>

## 3.5.1. Overview of Update Mechanisms

<p>Polling (Get Task):</p> <ul> <li>Client periodically calls Get Task (Section 3.1.3) to check task status</li> <li>Simple to implement, works with all protocol bindings</li> <li>Higher latency, potential for unnecessary requests</li> <li>Best for: Simple integrations, infrequent updates, clients behind restrictive firewalls</li> </ul> <p>Streaming:</p> <ul> <li>Real-time delivery of events as they occur</li> <li>Operations: Stream Message (Section 3.1.2) and Subscribe to Task (Section 3.1.6)</li> <li>Low latency, efficient for frequent updates</li> <li>Requires persistent connection support</li> <li>Best for: Interactive applications, real-time dashboards, live progress monitoring</li> <li>Requires <code>AgentCard.capabilities.streaming</code> to be <code>true</code></li> </ul> <p>Push Notifications (WebHooks):</p> <ul> <li>Agent sends HTTP POST requests to client-registered endpoints when task state changes</li> <li>Client does not maintain persistent connection</li> <li>Asynchronous delivery, client must be reachable via HTTP</li> <li>Best for: Server-to-server integrations, long-running tasks, event-driven architectures</li> <li>Operations: Create (Section 3.1.7), Get (Section 3.1.8), List (Section 3.1.9), Delete (Section 3.1.10)</li> <li>Event types: TaskStatusUpdateEvent (Section 4.2.1), TaskArtifactUpdateEvent (Section 4.2.2), WebHook payloads (Section 4.3)</li> <li>Requires <code>AgentCard.capabilities.pushNotifications</code> to be <code>true</code></li> <li>Regardless of the protocol binding being used by the agent, WebHook calls use plain HTTP and the JSON payloads as defined in the HTTP protocol binding</li> </ul>

## 3.5.2. Streaming Event Delivery

<p>Event Ordering:</p> <p>All implementations MUST deliver events in the order they were generated. Events MUST NOT be reordered during transmission, regardless of protocol binding.</p> <p>Multiple Streams Per Task:</p> <p>An agent MAY serve multiple concurrent streams to one or more clients for the same task. This allows multiple clients (or the same client with multiple connections) to independently subscribe to and receive updates about a task's progress.</p> <p>When multiple streams are active for a task:</p> <ul> <li>Events MUST be broadcast to all active streams for that task</li> <li>Each stream MUST receive the same events in the same order</li> <li>Closing one stream MUST NOT affect other active streams for the same task</li> <li>The task lifecycle is independent of any individual stream's lifecycle</li> </ul> <p>This capability enables scenarios such as:</p> <ul> <li>Multiple team members monitoring the same long-running task</li> <li>A client reconnecting to a task after a network interruption by opening a new stream</li> <li>Different applications or dashboards displaying real-time updates for the same task</li> </ul>

## 3.5.3. Push Notification Delivery

<p>Push notifications are delivered via HTTP POST to client-registered webhook endpoints. The delivery semantics and reliability guarantees are defined in Section 4.3.</p>

## 3.6 Versioning

<p>The specific version of the A2A protocol in use is identified using the <code>Major.Minor</code> elements (e.g. <code>1.0</code>) of the corresponding A2A specification version. Patch version numbers used by the specification, do not affect protocol compatibility. Patch version numbers SHOULD NOT be used in requests, responses and Agent Cards, and MUST not be considered when clients and servers negotiate protocol versions.</p>

## 3.6.1 Client Responsibilities

<p>Clients MUST send the <code>A2A-Version</code> header with each request to maintain compatibility after an agent upgrades to a new version of the protocol (except for 0.3 Clients - 0.3 will be assumed for empty header). Sending the <code>A2A-Version</code> header also provides visibility to agents about version usage in the ecosystem, which can help inform the risks of inplace version upgrades.</p> <p>Example of HTTP GET Request with Version Header:</p> <pre><code>GET /tasks/task-123 HTTP/1.1
Host: agent.example.com
A2A-Version: 1.0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
</code></pre> <p>Clients MAY provide the <code>A2A-Version</code> as a request parameter instead of a header.</p> <p>Example of HTTP GET Request with Version request parameter:</p> <pre><code>GET /tasks/task-123?A2A-Version=1.0 HTTP/1.1
Host: agent.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
</code></pre>

## 3.6.2 Server Responsibilities

<p>Agents MUST process requests using the semantics of the requested <code>A2A-Version</code> (matching <code>Major.Minor</code>). If the version is not supported by the interface, agents MUST return a <code>VersionNotSupportedError</code>.</p> <p>Agents MUST interpret empty value as 0.3 version.</p> <p>Agents CAN expose multiple interfaces for the same transport with different versions under the same or different URLs.</p>

## 3.6.3 Tooling support

<p>Tooling libraries and SDKs that implement the A2A protocol MUST provide mechanisms to help clients manage protocol versioning, such as negotiation of the transport and protocol version used. Client Agents that require the latest features of the protocol should be configured to request specific versions and avoid automatic fallback to older versions, to prevent silently losing functionality.</p>

## 3.7 Messages and Artifacts

<p>Messages and Artifacts serve distinct purposes within the A2A protocol. The core interaction model defined by A2A is for clients to send messages to initiate a task that produces one or more artifacts.</p> <p>Messages play several key roles:</p> <ul> <li>Task Initiation: Clients send Messages to agents to initiate new tasks.</li> <li>Clarification Messages: Agents may send Messages back to the client to request clarification prior to initiating a task.</li> <li>Status Messages: Agents attach Messages to status update events to inform clients about task progress, request additional input, or provide informational updates.</li> <li>Task Interaction: Clients send Messages to provide additional input or instructions for ongoing tasks.</li> </ul> <p>Messages SHOULD NOT be used to deliver task outputs. Results SHOULD BE returned using Artifacts associated with a Task. This separation allows for a clear distinction between communication (Messages) and data output (Artifacts).</p> <p>The Task History field contains Messages exchanged during task execution. However, not all Messages are guaranteed to be persisted in the Task history; for example, transient informational messages may not be stored. Messages exchanged prior to task creation may not be stored in Task history. The agent is responsible to determine which Messages are persisted in the Task History.</p> <p>Clients using streaming to retrieve task updates MAY not receive all status update messages if the client is disconnected and then reconnects. Messages MUST NOT be considered a reliable delivery mechanism for critical information.</p> <p>Agents MAY choose to persist all Messages that contain important information in the Task history to ensure clients can retrieve it later. However, clients MUST NOT rely on this behavior unless negotiated out-of-band.</p>

## 4. Protocol Data Model

<p>The A2A protocol defines a canonical data model using Protocol Buffers. All protocol bindings MUST provide functionally equivalent representations of these data structures.</p>

## 4.1.1. Task

<p><code>Task</code> is the core unit of action for A2A. It has a current status and when results are created for the task they are stored in the artifact. If there are multiple turns for a task, these are stored in history.</p> Field Type Required Description <code>id</code> <code>string</code> Yes Unique identifier (e.g. UUID) for the task, generated by the server for a new task. <code>contextId</code> <code>string</code> Yes Unique identifier (e.g. UUID) for the contextual collection of interactions (tasks and messages). Created by the A2A server. <code>status</code> <code>TaskStatus</code> Yes The current status of a <code>Task</code>, including <code>state</code> and a <code>message</code>. <code>artifacts</code> array of <code>Artifact</code> No A set of output artifacts for a <code>Task</code>. <code>history</code> array of <code>Message</code> No The history of interactions from a <code>Task</code>. <code>metadata</code> <code>object</code> No A key/value object to store custom metadata about a task. <p></p>

## 4.1.2. TaskStatus

<p>A container for the status of a task</p> Field Type Required Description <code>state</code> <code>TaskState</code> Yes The current state of this task. <code>message</code> <code>Message</code> No A message associated with the status. <code>timestamp</code> <code>timestamp</code> No ISO 8601 Timestamp when the status was recorded. Example: "2023-10-27T10:00:00Z" <p></p>

## 4.1.3. TaskState

<p>Defines the possible lifecycle states of a <code>Task</code>.</p> Value Description <code>TASK_STATE_UNSPECIFIED</code> The task is in an unknown or indeterminate state. <code>TASK_STATE_SUBMITTED</code> Indicates that a task has been successfully submitted and acknowledged. <code>TASK_STATE_WORKING</code> Indicates that a task is actively being processed by the agent. <code>TASK_STATE_COMPLETED</code> Indicates that a task has finished successfully. This is a terminal state. <code>TASK_STATE_FAILED</code> Indicates that a task has finished with an error. This is a terminal state. <code>TASK_STATE_CANCELED</code> Indicates that a task was canceled before completion. This is a terminal state. <code>TASK_STATE_INPUT_REQUIRED</code> Indicates that the agent requires additional user input to proceed. This is an interrupted state. <code>TASK_STATE_REJECTED</code> Indicates that the agent has decided to not perform the task. This may be done during initial task creation or later once an agent has determined it can't or won't proceed. This is a terminal state. <code>TASK_STATE_AUTH_REQUIRED</code> Indicates that authentication is required to proceed. This is an interrupted state. <p></p>

## 4.1.4. Message

<p><code>Message</code> is one unit of communication between client and server. It can be associated with a context and/or a task. For server messages, <code>context_id</code> must be provided, and <code>task_id</code> only if a task was created. For client messages, both fields are optional, with the caveat that if both are provided, they have to match (the <code>context_id</code> has to be the one that is set on the task). If only <code>task_id</code> is provided, the server will infer <code>context_id</code> from it.</p> Field Type Required Description <code>messageId</code> <code>string</code> Yes The unique identifier (e.g. UUID) of the message. This is created by the message creator. <code>contextId</code> <code>string</code> No Optional. The context id of the message. If set, the message will be associated with the given context. <code>taskId</code> <code>string</code> No Optional. The task id of the message. If set, the message will be associated with the given task. <code>role</code> <code>Role</code> Yes Identifies the sender of the message. <code>parts</code> array of <code>Part</code> Yes Parts is the container of the message content. <code>metadata</code> <code>object</code> No Optional. Any metadata to provide along with the message. <code>extensions</code> array of <code>string</code> No The URIs of extensions that are present or contributed to this Message. <code>referenceTaskIds</code> array of <code>string</code> No A list of task IDs that this message references for additional context. <p></p>

## 4.1.5. Role

<p>Defines the sender of a message in A2A protocol communication.</p> Value Description <code>ROLE_UNSPECIFIED</code> The role is unspecified. <code>ROLE_USER</code> The message is from the client to the server. <code>ROLE_AGENT</code> The message is from the server to the client. <p></p>

## 4.1.6. Part

<p><code>Part</code> represents a container for a section of communication content. Parts can be purely textual, some sort of file (image, video, etc) or a structured data blob (i.e. JSON).</p> Field Type Required Description <code>text</code> <code>string</code> Optional (OneOf) The string content of the <code>text</code> part. <code>raw</code> <code>bytes</code> Optional (OneOf) The <code>raw</code> byte content of a file. In JSON serialization, this is encoded as a base64 string. <code>url</code> <code>string</code> Optional (OneOf) A <code>url</code> pointing to the file's content. <code>data</code> <code>any</code> Optional (OneOf) Arbitrary structured <code>data</code> as a JSON value (object, array, string, number, boolean, or null). <code>metadata</code> <code>object</code> No Optional. metadata associated with this part. <code>filename</code> <code>string</code> No An optional <code>filename</code> for the file (e.g., "document.pdf"). <code>mediaType</code> <code>string</code> No The <code>media_type</code> (MIME type) of the part content (e.g., "text/plain", "application/json", "image/png"). This field is available for all part types. <p>Note: A <code>Part</code> MUST contain exactly one of the following: <code>text</code>, <code>raw</code>, <code>url</code>, <code>data</code></p> <p></p>

## 4.1.7. Artifact

<p>Artifacts represent task outputs.</p> Field Type Required Description <code>artifactId</code> <code>string</code> Yes Unique identifier (e.g. UUID) for the artifact. It must be unique within a task. <code>name</code> <code>string</code> No A human readable name for the artifact. <code>description</code> <code>string</code> No Optional. A human readable description of the artifact. <code>parts</code> array of <code>Part</code> Yes The content of the artifact. Must contain at least one part. <code>metadata</code> <code>object</code> No Optional. Metadata included with the artifact. <code>extensions</code> array of <code>string</code> No The URIs of extensions that are present or contributed to this Artifact.

## 4.2.1. TaskStatusUpdateEvent

<p>An event sent by the agent to notify the client of a change in a task's status.</p> Field Type Required Description <code>taskId</code> <code>string</code> Yes The ID of the task that has changed. <code>contextId</code> <code>string</code> Yes The ID of the context that the task belongs to. <code>status</code> <code>TaskStatus</code> Yes The new status of the task. <code>metadata</code> <code>object</code> No Optional. Metadata associated with the task update. <p></p>

## 4.2.2. TaskArtifactUpdateEvent

<p>A task delta where an artifact has been generated.</p> Field Type Required Description <code>taskId</code> <code>string</code> Yes The ID of the task for this artifact. <code>contextId</code> <code>string</code> Yes The ID of the context that this task belongs to. <code>artifact</code> <code>Artifact</code> Yes The artifact that was generated or updated. <code>append</code> <code>boolean</code> No If true, the content of this artifact should be appended to a previously sent artifact with the same ID. <code>lastChunk</code> <code>boolean</code> No If true, this is the final chunk of the artifact. <code>metadata</code> <code>object</code> No Optional. Metadata associated with the artifact update.

## 4.3.1. PushNotificationConfig

<p>Configuration for setting up push notifications for task updates.</p> Field Type Required Description <code>id</code> <code>string</code> No A unique identifier (e.g. UUID) for this push notification configuration. <code>url</code> <code>string</code> Yes The URL where the notification should be sent. <code>token</code> <code>string</code> No A token unique for this task or session. <code>authentication</code> <code>AuthenticationInfo</code> No Authentication information required to send the notification. <p></p>

## 4.3.2. AuthenticationInfo

<p>Defines authentication details, used for push notifications.</p> Field Type Required Description <code>scheme</code> <code>string</code> Yes HTTP Authentication Scheme from the IANA registry. Examples: <code>Bearer</code>, <code>Basic</code>, <code>Digest</code>. Scheme names are case-insensitive per RFC 9110 Section 11.1. <code>credentials</code> <code>string</code> No Push Notification credentials. Format depends on the scheme (e.g., token for Bearer).

## 4.3.3. Push Notification Payload

<p>When a task update occurs, the agent sends an HTTP POST request to the configured webhook URL. The payload uses the same <code>StreamResponse</code> format as streaming operations, allowing push notifications to deliver the same event types as real-time streams.</p> <p>Request Format:</p> <pre><code>POST {webhook_url}
Authorization: {authentication_scheme} {credentials}
Content-Type: application/json

{
  /* StreamResponse object - one of: */
  "task": { /* Task object */ },
  "message": { /* Message object */ },
  "statusUpdate": { /* TaskStatusUpdateEvent object */ },
  "artifactUpdate": { /* TaskArtifactUpdateEvent object */ }
}
</code></pre> <p>Payload Structure:</p> <p>The webhook payload is a <code>StreamResponse</code> object containing exactly one of the following:</p> <ul> <li>task: A <code>Task</code> object with the current task state</li> <li>message: A <code>Message</code> object containing a message response</li> <li>statusUpdate: A <code>TaskStatusUpdateEvent</code> indicating a status change</li> <li>artifactUpdate: A <code>TaskArtifactUpdateEvent</code> indicating artifact updates</li> </ul> <p>Authentication:</p> <p>The agent MUST include authentication credentials in the request headers as specified in the <code>PushNotificationConfig.authentication</code> field. The format follows standard HTTP authentication patterns (Bearer tokens, Basic auth, etc.).</p> <p>Client Responsibilities:</p> <ul> <li>Clients MUST respond with HTTP 2xx status codes to acknowledge successful receipt</li> <li>Clients SHOULD process notifications idempotently, as duplicate deliveries may occur</li> <li>Clients MUST validate the task ID matches an expected task</li> <li>Clients SHOULD implement appropriate security measures to verify the notification source</li> </ul> <p>Server Guarantees:</p> <ul> <li>Agents MUST attempt delivery at least once for each configured webhook</li> <li>Agents MAY implement retry logic with exponential backoff for failed deliveries</li> <li>Agents SHOULD include a reasonable timeout for webhook requests (recommended: 10-30 seconds)</li> <li>Agents MAY stop attempting delivery after a configured number of consecutive failures</li> </ul> <p>For detailed security guidance on push notifications, see Section 13.2 Push Notification Security.</p>

## 4.4.1. AgentCard

<p>A self-describing manifest for an agent. It provides essential metadata including the agent's identity, capabilities, skills, supported communication methods, and security requirements.</p> Field Type Required Description <code>name</code> <code>string</code> Yes A human readable name for the agent. Example: "Recipe Agent" <code>description</code> <code>string</code> Yes A human-readable description of the agent, assisting users and other agents in understanding its purpose. Example: "Agent that helps users with recipes and cooking." <code>supportedInterfaces</code> array of <code>AgentInterface</code> Yes Ordered list of supported interfaces. The first entry is preferred. <code>provider</code> <code>AgentProvider</code> No The service provider of the agent. <code>version</code> <code>string</code> Yes The version of the agent. Example: "1.0.0" <code>documentationUrl</code> <code>string</code> No A URL providing additional documentation about the agent. <code>capabilities</code> <code>AgentCapabilities</code> Yes A2A Capability set supported by the agent. <code>securitySchemes</code> map of string to <code>SecurityScheme</code> No The security scheme details used for authenticating with this agent. <code>securityRequirements</code> array of <code>SecurityRequirement</code> No Security requirements for contacting the agent. <code>defaultInputModes</code> array of <code>string</code> Yes The set of interaction modes that the agent supports across all skills. This can be overridden per skill. Defined as media types. <code>defaultOutputModes</code> array of <code>string</code> Yes The media types supported as outputs from this agent. <code>skills</code> array of <code>AgentSkill</code> Yes Skills represent the abilities of an agent. It is largely a descriptive concept but represents a more focused set of behaviors that the agent is likely to succeed at. <code>signatures</code> array of <code>AgentCardSignature</code> No JSON Web Signatures computed for this <code>AgentCard</code>. <code>iconUrl</code> <code>string</code> No Optional. A URL to an icon for the agent. <p></p>

## 4.4.2. AgentProvider

<p>Represents the service provider of an agent.</p> Field Type Required Description <code>url</code> <code>string</code> Yes A URL for the agent provider's website or relevant documentation. Example: "https://ai.google.dev" <code>organization</code> <code>string</code> Yes The name of the agent provider's organization. Example: "Google" <p></p>

## 4.4.3. AgentCapabilities

<p>Defines optional capabilities supported by an agent.</p> Field Type Required Description <code>streaming</code> <code>boolean</code> No Indicates if the agent supports streaming responses. <code>pushNotifications</code> <code>boolean</code> No Indicates if the agent supports sending push notifications for asynchronous task updates. <code>extensions</code> array of <code>AgentExtension</code> No A list of protocol extensions supported by the agent. <code>extendedAgentCard</code> <code>boolean</code> No Indicates if the agent supports providing an extended agent card when authenticated. <p></p>

## 4.4.4. AgentExtension

<p>A declaration of a protocol extension supported by an Agent.</p> Field Type Required Description <code>uri</code> <code>string</code> No The unique URI identifying the extension. <code>description</code> <code>string</code> No A human-readable description of how this agent uses the extension. <code>required</code> <code>boolean</code> No If true, the client must understand and comply with the extension's requirements. <code>params</code> <code>object</code> No Optional. Extension-specific configuration parameters. <p></p>

## 4.4.5. AgentSkill

<p>Represents a distinct capability or function that an agent can perform.</p> Field Type Required Description <code>id</code> <code>string</code> Yes A unique identifier for the agent's skill. <code>name</code> <code>string</code> Yes A human-readable name for the skill. <code>description</code> <code>string</code> Yes A detailed description of the skill. <code>tags</code> array of <code>string</code> Yes A set of keywords describing the skill's capabilities. <code>examples</code> array of <code>string</code> No Example prompts or scenarios that this skill can handle. <code>inputModes</code> array of <code>string</code> No The set of supported input media types for this skill, overriding the agent's defaults. <code>outputModes</code> array of <code>string</code> No The set of supported output media types for this skill, overriding the agent's defaults. <code>securityRequirements</code> array of <code>SecurityRequirement</code> No Security schemes necessary for this skill. <p></p>

## 4.4.6. AgentInterface

<p>Declares a combination of a target URL, transport and protocol version for interacting with the agent. This allows agents to expose the same functionality over multiple protocol binding mechanisms.</p> Field Type Required Description <code>url</code> <code>string</code> Yes The URL where this interface is available. Must be a valid absolute HTTPS URL in production. Example: "https://api.example.com/a2a/v1", "https://grpc.example.com/a2a" <code>protocolBinding</code> <code>string</code> Yes The protocol binding supported at this URL. This is an open form string, to be easily extended for other protocol bindings. The core ones officially supported are <code>JSONRPC</code>, <code>GRPC</code> and <code>HTTP+JSON</code>. <code>tenant</code> <code>string</code> No Tenant ID to be used in the request when calling the agent. <code>protocolVersion</code> <code>string</code> Yes The version of the A2A protocol this interface exposes. Use the latest supported minor version per major version. Examples: "0.3", "1.0" <p></p>

## 4.4.7. AgentCardSignature

<p>AgentCardSignature represents a JWS signature of an AgentCard. This follows the JSON format of an RFC 7515 JSON Web Signature (JWS).</p> Field Type Required Description <code>protected</code> <code>string</code> Yes Required. The protected JWS header for the signature. This is always a base64url-encoded JSON object. <code>signature</code> <code>string</code> Yes Required. The computed signature, base64url-encoded. <code>header</code> <code>object</code> No The unprotected JWS header values.

## 4.5.1. SecurityScheme

<p>Defines a security scheme that can be used to secure an agent's endpoints. This is a discriminated union type based on the OpenAPI 3.2 Security Scheme Object. See: https://spec.openapis.org/oas/v3.2.0.html#security-scheme-object</p> Field Type Required Description <code>apiKeySecurityScheme</code> <code>APIKeySecurityScheme</code> Optional (OneOf) API key-based authentication. <code>httpAuthSecurityScheme</code> <code>HTTPAuthSecurityScheme</code> Optional (OneOf) HTTP authentication (Basic, Bearer, etc.). <code>oauth2SecurityScheme</code> <code>OAuth2SecurityScheme</code> Optional (OneOf) OAuth 2.0 authentication. <code>openIdConnectSecurityScheme</code> <code>OpenIdConnectSecurityScheme</code> Optional (OneOf) OpenID Connect authentication. <code>mtlsSecurityScheme</code> <code>MutualTlsSecurityScheme</code> Optional (OneOf) Mutual TLS authentication. <p>Note: A <code>SecurityScheme</code> MUST contain exactly one of the following: <code>apiKeySecurityScheme</code>, <code>httpAuthSecurityScheme</code>, <code>oauth2SecurityScheme</code>, <code>openIdConnectSecurityScheme</code>, <code>mtlsSecurityScheme</code></p> <p></p>

## 4.5.2. APIKeySecurityScheme

<p>Defines a security scheme using an API key.</p> Field Type Required Description <code>description</code> <code>string</code> No An optional description for the security scheme. <code>location</code> <code>string</code> Yes The location of the API key. Valid values are "query", "header", or "cookie". <code>name</code> <code>string</code> Yes The name of the header, query, or cookie parameter to be used. <p></p>

## 4.5.3. HTTPAuthSecurityScheme

<p>Defines a security scheme using HTTP authentication.</p> Field Type Required Description <code>description</code> <code>string</code> No An optional description for the security scheme. <code>scheme</code> <code>string</code> Yes The name of the HTTP Authentication scheme to be used in the Authorization header, as defined in RFC7235 (e.g., "Bearer"). This value should be registered in the IANA Authentication Scheme registry. <code>bearerFormat</code> <code>string</code> No A hint to the client to identify how the bearer token is formatted (e.g., "JWT"). Primarily for documentation purposes. <p></p>

## 4.5.4. OAuth2SecurityScheme

<p>Defines a security scheme using OAuth 2.0.</p> Field Type Required Description <code>description</code> <code>string</code> No An optional description for the security scheme. <code>flows</code> <code>OAuthFlows</code> Yes An object containing configuration information for the supported OAuth 2.0 flows. <code>oauth2MetadataUrl</code> <code>string</code> No URL to the OAuth2 authorization server metadata RFC 8414. TLS is required. <p></p>

## 4.5.5. OpenIdConnectSecurityScheme

<p>Defines a security scheme using OpenID Connect.</p> Field Type Required Description <code>description</code> <code>string</code> No An optional description for the security scheme. <code>openIdConnectUrl</code> <code>string</code> Yes The OpenID Connect Discovery URL for the OIDC provider's metadata. <p></p>

## 4.5.6. MutualTlsSecurityScheme

<p>Defines a security scheme using mTLS authentication.</p> Field Type Required Description <code>description</code> <code>string</code> No An optional description for the security scheme. <p></p>

## 4.5.7. OAuthFlows

<p>Defines the configuration for the supported OAuth 2.0 flows.</p> Field Type Required Description <code>authorizationCode</code> <code>AuthorizationCodeOAuthFlow</code> Optional (OneOf) Configuration for the OAuth Authorization Code flow. <code>clientCredentials</code> <code>ClientCredentialsOAuthFlow</code> Optional (OneOf) Configuration for the OAuth Client Credentials flow. <code>implicit</code> <code>ImplicitOAuthFlow</code> Optional (OneOf) Deprecated: Use Authorization Code + PKCE instead. <code>password</code> <code>PasswordOAuthFlow</code> Optional (OneOf) Deprecated: Use Authorization Code + PKCE or Device Code. <code>deviceCode</code> <code>DeviceCodeOAuthFlow</code> Optional (OneOf) Configuration for the OAuth Device Code flow. <p>Note: A <code>OAuthFlows</code> MUST contain exactly one of the following: <code>authorizationCode</code>, <code>clientCredentials</code>, <code>implicit</code>, <code>password</code>, <code>deviceCode</code></p> <p></p>

## 4.5.8. AuthorizationCodeOAuthFlow

<p>Defines configuration details for the OAuth 2.0 Authorization Code flow.</p> Field Type Required Description <code>authorizationUrl</code> <code>string</code> Yes The authorization URL to be used for this flow. <code>tokenUrl</code> <code>string</code> Yes The token URL to be used for this flow. <code>refreshUrl</code> <code>string</code> No The URL to be used for obtaining refresh tokens. <code>scopes</code> map of string to <code>string</code> Yes The available scopes for the OAuth2 security scheme. <code>pkceRequired</code> <code>boolean</code> No Indicates if PKCE (RFC 7636) is required for this flow. PKCE should always be used for public clients and is recommended for all clients. <p></p>

## 4.5.9. ClientCredentialsOAuthFlow

<p>Defines configuration details for the OAuth 2.0 Client Credentials flow.</p> Field Type Required Description <code>tokenUrl</code> <code>string</code> Yes The token URL to be used for this flow. <code>refreshUrl</code> <code>string</code> No The URL to be used for obtaining refresh tokens. <code>scopes</code> map of string to <code>string</code> Yes The available scopes for the OAuth2 security scheme. <p></p>

## 4.5.10. DeviceCodeOAuthFlow

<p>Defines configuration details for the OAuth 2.0 Device Code flow (RFC 8628). This flow is designed for input-constrained devices such as IoT devices, and CLI tools where the user authenticates on a separate device.</p> Field Type Required Description <code>deviceAuthorizationUrl</code> <code>string</code> Yes The device authorization endpoint URL. <code>tokenUrl</code> <code>string</code> Yes The token URL to be used for this flow. <code>refreshUrl</code> <code>string</code> No The URL to be used for obtaining refresh tokens. <code>scopes</code> map of string to <code>string</code> Yes The available scopes for the OAuth2 security scheme.

## 4.6. Extensions

<p>The A2A protocol supports extensions to provide additional functionality or data beyond the core specification while maintaining backward compatibility and interoperability. Extensions allow agents to declare additional capabilities such as protocol enhancements or vendor-specific features, maintain compatibility with clients that don't support specific extensions, enable innovation through experimental or domain-specific features without modifying the core protocol, and facilitate standardization by providing a pathway for community-developed features to become part of the core specification.</p>

## 4.6.1. Extension Declaration

<p>Agents declare their supported extensions in the <code>AgentCard</code> using the <code>extensions</code> field, which contains an array of <code>AgentExtension</code> objects.</p> <p>Example: Agent declaring extension support in AgentCard:</p> <pre><code>{
  "name": "Research Assistant Agent",
  "description": "AI agent for academic research and fact-checking",
  "supportedInterfaces": [
    {
      "url": "https://research-agent.example.com/a2a/v1",
      "protocolBinding": "HTTP+JSON",
      "protocolVersion": "0.3",
    }
  ],
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "extensions": [
      {
        "uri": "https://standards.org/extensions/citations/v1",
        "description": "Provides citation formatting and source verification",
        "required": false
      },
      {
        "uri": "https://example.com/extensions/geolocation/v1",
        "description": "Location-based search capabilities",
        "required": false
      }
    ]
  },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"],
  "skills": [
    {
      "id": "academic-research",
      "name": "Academic Research Assistant",
      "description": "Provides research assistance with citations and source verification",
      "tags": ["research", "citations", "academic"],
      "examples": ["Find peer-reviewed articles on climate change"],
      "inputModes": ["text/plain"],
      "outputModes": ["text/plain"]
    }
  ]
}
</code></pre> <p>Clients indicate their desire to opt into the use of specific extensions through binding-specific mechanisms such as HTTP headers, gRPC metadata, or JSON-RPC request parameters that identify the extension identifiers they wish to utilize during the interaction.</p> <p>Example: HTTP client opting into extensions using headers:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/json
Authorization: Bearer token
A2A-Extensions: https://example.com/extensions/geolocation/v1,https://standards.org/extensions/citations/v1

{
  "message": {
    "role": "ROLE_USER",
    "parts": [{"text": "Find restaurants near me"}],
    "extensions": ["https://example.com/extensions/geolocation/v1"],
    "metadata": {
      "https://example.com/extensions/geolocation/v1": {
        "latitude": 37.7749,
        "longitude": -122.4194
      }
    }
  }
}
</code></pre>

## 4.6.2. Extensions Points

<p>Extensions can be integrated into the A2A protocol at several well-defined extension points:</p> <p>Message Extensions:</p> <p>Messages can be extended to allow clients to provide additional strongly typed context or parameters relevant to the message being sent, or TaskStatus Messages to include extra information about the task's progress.</p> <p>Example: A location extension using the extensions and metadata arrays:</p> <pre><code>{
  "role": "ROLE_USER",
  "parts": [
    {"text": "Find restaurants near me"}
  ],
  "extensions": ["https://example.com/extensions/geolocation/v1"],
  "metadata": {
    "https://example.com/extensions/geolocation/v1": {
      "latitude": 37.7749,
      "longitude": -122.4194,
      "accuracy": 10.0,
      "timestamp": "2025-10-21T14:30:00Z"
    }
  }
}
</code></pre> <p>Artifact Extensions:</p> <p>Artifacts can include extension data to provide strongly typed context or metadata about the generated content.</p> <p>Example: An artifact with citation extension for research sources:</p> <pre><code>{
  "artifactId": "research-summary-001",
  "name": "Climate Change Summary",
  "parts": [
    {
      "text": "Global temperatures have risen by 1.1°C since pre-industrial times, with significant impacts on weather patterns and sea levels."
    }
  ],
  "extensions": ["https://standards.org/extensions/citations/v1"],
  "metadata": {
    "https://standards.org/extensions/citations/v1": {
      "sources": [
        {
          "title": "Global Temperature Anomalies - 2023 Report",
          "authors": ["Smith, J.", "Johnson, M."],
          "url": "https://climate.gov/reports/2023-temperature",
          "accessDate": "2025-10-21",
          "relevantText": "Global temperatures have risen by 1.1°C"
        }
      ]
    }
  }
}
</code></pre>

## 4.6.3. Extension Versioning and Compatibility

<p>Extensions SHOULD include version information in their URI identifier. This allows clients and agents to negotiate compatible versions of extensions during interactions. A new URI MUST be created for breaking changes to an extension.</p> <p>If a client requests a versions of an extension that the agent does not support, the agent SHOULD ignore the extension for that interaction and proceed without it, unless the extension is marked as <code>required</code> in the AgentCard, in which case the agent MUST return an error indicating unsupported extension. It MUST NOT fall back to a previous version of the extension automatically.</p>

## 5.1. Functional Equivalence Requirements

<p>When an agent supports multiple protocols, all supported protocols MUST:</p> <ul> <li>Identical Functionality: Provide the same set of operations and capabilities</li> <li>Consistent Behavior: Return semantically equivalent results for the same requests</li> <li>Same Error Handling: Map errors consistently using appropriate protocol-specific codes</li> <li>Equivalent Authentication: Support the same authentication schemes declared in the AgentCard</li> </ul>

## 5.2. Protocol Selection and Negotiation

<ul> <li>Agent Declaration: Agents MUST declare all supported protocols in their AgentCard</li> <li>Client Choice: Clients MAY choose any protocol declared by the agent</li> <li>Fallback Behavior: Clients SHOULD implement fallback logic for alternative protocols</li> </ul>

## 5.3. Method Mapping Reference

Functionality JSON-RPC Method gRPC Method REST Endpoint Send message <code>SendMessage</code> <code>SendMessage</code> <code>POST /message:send</code> Stream message <code>SendStreamingMessage</code> <code>SendStreamingMessage</code> <code>POST /message:stream</code> Get task <code>GetTask</code> <code>GetTask</code> <code>GET /tasks/{id}</code> List tasks <code>ListTasks</code> <code>ListTasks</code> <code>GET /tasks</code> Cancel task <code>CancelTask</code> <code>CancelTask</code> <code>POST /tasks/{id}:cancel</code> Subscribe to task <code>SubscribeToTask</code> <code>SubscribeToTask</code> <code>POST /tasks/{id}:subscribe</code> Create push notification config <code>CreateTaskPushNotificationConfig</code> <code>CreateTaskPushNotificationConfig</code> <code>POST /tasks/{id}/pushNotificationConfigs</code> Get push notification config <code>GetTaskPushNotificationConfig</code> <code>GetTaskPushNotificationConfig</code> <code>GET /tasks/{id}/pushNotificationConfigs/{configId}</code> List push notification configs <code>ListTaskPushNotificationConfigs</code> <code>ListTaskPushNotificationConfigs</code> <code>GET /tasks/{id}/pushNotificationConfigs</code> Delete push notification config <code>DeleteTaskPushNotificationConfig</code> <code>DeleteTaskPushNotificationConfig</code> <code>DELETE /tasks/{id}/pushNotificationConfigs/{configId}</code> Get extended Agent Card <code>GetExtendedAgentCard</code> <code>GetExtendedAgentCard</code> <code>GET /extendedAgentCard</code>

## 5.4. Error Code Mappings

<p>All A2A-specific errors defined in Section 3.3.2 MUST be mapped to binding-specific error representations. The following table provides the canonical mappings for each standard protocol binding:</p> A2A Error Type JSON-RPC Code gRPC Status HTTP Status HTTP Type URI <code>TaskNotFoundError</code> <code>-32001</code> <code>NOT_FOUND</code> <code>404 Not Found</code> <code>https://a2a-protocol.org/errors/task-not-found</code> <code>TaskNotCancelableError</code> <code>-32002</code> <code>FAILED_PRECONDITION</code> <code>409 Conflict</code> <code>https://a2a-protocol.org/errors/task-not-cancelable</code> <code>PushNotificationNotSupportedError</code> <code>-32003</code> <code>UNIMPLEMENTED</code> <code>400 Bad Request</code> <code>https://a2a-protocol.org/errors/push-notification-not-supported</code> <code>UnsupportedOperationError</code> <code>-32004</code> <code>UNIMPLEMENTED</code> <code>400 Bad Request</code> <code>https://a2a-protocol.org/errors/unsupported-operation</code> <code>ContentTypeNotSupportedError</code> <code>-32005</code> <code>INVALID_ARGUMENT</code> <code>415 Unsupported Media Type</code> <code>https://a2a-protocol.org/errors/content-type-not-supported</code> <code>InvalidAgentResponseError</code> <code>-32006</code> <code>INTERNAL</code> <code>502 Bad Gateway</code> <code>https://a2a-protocol.org/errors/invalid-agent-response</code> <code>ExtendedAgentCardNotConfiguredError</code> <code>-32007</code> <code>FAILED_PRECONDITION</code> <code>400 Bad Request</code> <code>https://a2a-protocol.org/errors/extended-agent-card-not-configured</code> <code>ExtensionSupportRequiredError</code> <code>-32008</code> <code>FAILED_PRECONDITION</code> <code>400 Bad Request</code> <code>https://a2a-protocol.org/errors/extension-support-required</code> <code>VersionNotSupportedError</code> <code>-32009</code> <code>UNIMPLEMENTED</code> <code>400 Bad Request</code> <code>https://a2a-protocol.org/errors/version-not-supported</code> <p>Custom Binding Requirements:</p> <p>Custom protocol bindings MUST define equivalent error code mappings that preserve the semantic meaning of each A2A error type. The binding specification SHOULD provide a similar mapping table showing how each A2A error type is represented in the custom binding's native error format.</p> <p>For binding-specific error structures and examples, see:</p> <ul> <li>JSON-RPC Error Handling</li> <li>gRPC Error Handling</li> <li>HTTP/REST Error Handling</li> </ul>

## 5.5. JSON Field Naming Convention

<p>All JSON serializations of the A2A protocol data model MUST use camelCase naming for field names, not the snake_case convention used in Protocol Buffer definitions.</p> <p>Naming Convention:</p> <ul> <li>Protocol Buffer field: <code>protocol_version</code> → JSON field: <code>protocolVersion</code></li> <li>Protocol Buffer field: <code>context_id</code> → JSON field: <code>contextId</code></li> <li>Protocol Buffer field: <code>default_input_modes</code> → JSON field: <code>defaultInputModes</code></li> <li>Protocol Buffer field: <code>push_notification_config</code> → JSON field: <code>pushNotificationConfig</code></li> </ul> <p>Enum Values:</p> <ul> <li>Enum values MUST be represented according to the ProtoJSON specification, which serializes enums as their string names as defined in the Protocol Buffer definition (typically SCREAMING_SNAKE_CASE).</li> </ul> <p>Examples:</p> <ul> <li>Protocol Buffer enum: <code>TASK_STATE_INPUT_REQUIRED</code> → JSON value: <code>"TASK_STATE_INPUT_REQUIRED"</code></li> <li>Protocol Buffer enum: <code>ROLE_USER</code> → JSON value: <code>"ROLE_USER"</code></li> </ul> <p>Note: This follows the ProtoJSON specification as adopted in ADR-001.</p>

## 5.6. Data Type Conventions

<p>This section documents conventions for common data types used throughout the A2A protocol, particularly as they apply to protocol bindings.</p>

## 5.6.1. Timestamps

<p>The A2A protocol uses <code>google.protobuf.Timestamp</code> for all timestamp fields in the Protocol Buffer definitions. When serialized to JSON (in JSON-RPC, HTTP/REST, or other JSON-based bindings), these timestamps MUST be represented as ISO 8601 formatted strings in UTC timezone.</p> <p>Format Requirements:</p> <ul> <li>Format: ISO 8601 combined date and time representation</li> <li>Timezone: UTC (denoted by 'Z' suffix)</li> <li>Precision: Millisecond precision SHOULD be used where available</li> <li>Pattern: <code>YYYY-MM-DDTHH:mm:ss.sssZ</code></li> </ul> <p>Examples:</p> <pre><code>{
  "timestamp": "2025-10-28T10:30:00.000Z",
  "createdAt": "2025-10-28T14:25:33.142Z",
  "lastModified": "2025-10-31T17:45:22.891Z"
}
</code></pre> <p>Implementation Notes:</p> <ul> <li>Protocol Buffer's <code>google.protobuf.Timestamp</code> represents time as seconds since Unix epoch (January 1, 1970, 00:00:00 UTC) plus nanoseconds</li> <li>JSON serialization automatically converts this to ISO 8601 format when using standard Protocol Buffer JSON encoding</li> <li>Clients and servers MUST parse and generate ISO 8601 timestamps correctly</li> <li>When millisecond precision is not available, the fractional seconds portion MAY be omitted or zero-filled</li> <li>Timestamps MUST NOT include timezone offsets other than 'Z' (all times are UTC)</li> </ul>

## 5.7. Field Presence and Optionality

<p>The Protocol Buffer definition in <code>specification/a2a.proto</code> uses <code>google.api.field_behavior</code> annotations to indicate whether fields are <code>REQUIRED</code>. These annotations serve as both documentation and validation hints for implementations.</p> <p>Required Fields:</p> <p>Fields marked with <code>[(google.api.field_behavior) = REQUIRED]</code> indicate that the field MUST be present and set in valid messages. Implementations SHOULD validate these requirements and reject messages with missing required fields. Arrays marked as required MUST contain at least one element.</p> <p>Optional Field Presence:</p> <p>The Protocol Buffer <code>optional</code> keyword is used to distinguish between a field being explicitly set versus omitted. This distinction is critical for two scenarios:</p> <ol> <li> <p>Explicit Default Values: Some fields in the specification define default values that differ from Protocol Buffer's implicit defaults. Implementations should apply the default value when the field is not explicitly provided.</p> </li> <li> <p>Agent Card Canonicalization: When creating cryptographic signatures of Agent Cards, it is required to produce a canonical JSON representation. The <code>optional</code> keyword enables implementations to distinguish between fields that were explicitly set (and should be included in the canonical form) versus fields that were omitted (and should be excluded from canonicalization). This ensures Agent Cards can be reconstructed to accurately match their signature.</p> </li> </ol> <p>Unrecognized Fields:</p> <p>Implementations SHOULD ignore unrecognized fields in messages, allowing for forward compatibility as the protocol evolves.</p>

## 6. Common Workflows &amp; Examples

<p>This section provides illustrative examples of common A2A interactions across different bindings.</p>

## 6.1. Basic Task Execution

<p>Scenario: Client asks a question and receives a completed task response.</p> <p>Request:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "role": "ROLE_USER",
    "parts": [{"text": "What is the weather today?"}],
    "messageId": "msg-uuid"
  }
}
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "task": {
    "id": "task-uuid",
    "contextId": "context-uuid",
    "status": {"state": "TASK_STATE_COMPLETED"},
    "artifacts": [{
      "artifactId": "artifact-uuid",
      "name": "Weather Report",
      "parts": [{"text": "Today will be sunny with a high of 75°F"}]
    }]
  }
}
</code></pre>

## 6.2. Streaming Task Execution

<p>Scenario: Client requests a long-running task with real-time updates.</p> <p>Request:</p> <pre><code>POST /message:stream HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "role": "ROLE_USER",
    "parts": [{"text": "Write a detailed report on climate change"}],
    "messageId": "msg-uuid"
  }
}
</code></pre> <p>SSE Response Stream:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"task": {"id": "task-uuid", "status": {"state": "TASK_STATE_WORKING"}}}

data: {"artifactUpdate": {"taskId": "task-uuid", "artifact": {"parts": [{"text": "# Climate Change Report\n\n"}]}}}

data: {"statusUpdate": {"taskId": "task-uuid", "status": {"state": "TASK_STATE_COMPLETED"}}}
</code></pre>

## 6.3. Multi-Turn Interaction

<p>Scenario: Agent requires additional input to complete a task.</p> <p>Initial Request:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "role": "ROLE_USER",
    "parts": [{"text": "Book me a flight"}],
    "messageId": "msg-1"
  }
}
</code></pre> <p>Response (Input Required):</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "task": {
    "id": "task-uuid",
    "status": {
      "state": "TASK_STATE_INPUT_REQUIRED",
      "message": {
        "role": "ROLE_AGENT",
        "parts": [{"text": "I need more details. Where would you like to fly from and to?"}]
      }
    }
  }
}
</code></pre> <p>Follow-up Request:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "taskId": "task-uuid",
    "role": "ROLE_USER",
    "parts": [{"text": "From San Francisco to New York"}],
    "messageId": "msg-2"
  }
}
</code></pre>

## 6.4. Version Negotiation Error

<p>Scenario: Client requests an unsupported protocol version.</p> <p>Request:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token
A2A-Version: 0.5

{
  "message": {
    "role": "ROLE_USER",
    "parts": [{"text": "Hello"}],
    "messageId": "msg-uuid"
  }
}
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
  "type": "https://a2a-protocol.org/errors/version-not-supported",
  "title": "Protocol Version Not Supported",
  "status": 400,
  "detail": "The requested A2A protocol version 0.5 is not supported by this agent",
  "supportedVersions": ["0.3"]
}
</code></pre>

## 6.5. Task Listing and Management

<p>Scenario: Client wants to see all tasks from a specific context or all tasks with a particular status.</p>

## Request: All tasks from a specific context

<p>Request:</p> <pre><code>POST /tasks/list HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
  "pageSize": 10,
  "historyLength": 3
}
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "tasks": [
    {
      "id": "3f36680c-7f37-4a5f-945e-d78981fafd36",
      "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
      "status": {
        "state": "TASK_STATE_COMPLETED",
        "timestamp": "2024-03-15T10:15:00Z"
      }
    }
  ],
  "totalSize": 5,
  "pageSize": 10,
  "nextPageToken": ""
}
</code></pre>

## Request: All working tasks across all contexts

<p>Request:</p> <pre><code>POST /tasks/list HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "status": "TASK_STATE_WORKING",
  "pageSize": 20
}
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "tasks": [
    {
      "id": "789abc-def0-1234-5678-9abcdef01234",
      "contextId": "another-context-id",
      "status": {
        "state": "TASK_STATE_WORKING",
        "message": {
          "role": "ROLE_AGENT",
          "parts": [
            {
              "text": "Processing your document analysis..."
            }
          ],
          "messageId": "msg-status-update"
        },
        "timestamp": "2024-03-15T10:20:00Z"
      }
    }
  ],
  "totalSize": 1,
  "pageSize": 20,
  "nextPageToken": ""
}
</code></pre>

## Pagination Example

<p>Request:</p> <pre><code>POST /tasks/list HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
  "pageSize": 10,
  "pageToken": "base64-encoded-cursor-token"
}
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "tasks": [
    /* ... additional tasks */
  ],
  "totalSize": 15,
  "pageSize": 10,
  "nextPageToken": "base64-encoded-next-cursor-token"
}
</code></pre>

## Validation Error Example

<p>Request:</p> <pre><code>POST /tasks/list HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "pageSize": 150,
  "historyLength": -5,
  "status": "running"
}
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
  "status": 400,
  "detail": "Invalid parameters",
  "errors": [
    {
      "field": "pageSize",
      "message": "Must be between 1 and 100 inclusive, got 150"
    },
    {
      "field": "historyLength",
      "message": "Must be non-negative integer, got -5"
    },
    {
      "field": "status",
      "message": "Invalid status value 'running'. Must be one of: pending, working, completed, failed, canceled"
    }
  ]
}
</code></pre>

## 6.6. Push Notification Setup and Usage

<p>Scenario: Client requests a long-running report generation and wants to be notified via webhook when it's done.</p> <p>Initial Request with Push Notification Config:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "role": "ROLE_USER",
    "parts": [
      {
        "text": "Generate the Q1 sales report. This usually takes a while. Notify me when it's ready."
      }
    ],
    "messageId": "6dbc13b5-bd57-4c2b-b503-24e381b6c8d6"
  },
  "configuration": {
    "pushNotificationConfig": {
      "url": "https://client.example.com/webhook/a2a-notifications",
      "token": "secure-client-token-for-task-aaa",
      "authentication": {
        "schemes": ["Bearer"]
      }
    }
  }
}
</code></pre> <p>Response (Task Submitted):</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "task": {
    "id": "43667960-d455-4453-b0cf-1bae4955270d",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "submitted",
      "timestamp": "2024-03-15T11:00:00Z"
    }
  }
}
</code></pre> <p>Later: Server POSTs Notification to Webhook:</p> <pre><code>POST /webhook/a2a-notifications HTTP/1.1
Host: client.example.com
Authorization: Bearer server-generated-jwt
Content-Type: application/a2a+json
X-A2A-Notification-Token: secure-client-token-for-task-aaa

{
  "statusUpdate": {
    "taskId": "43667960-d455-4453-b0cf-1bae4955270d",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "TASK_STATE_COMPLETED",
      "timestamp": "2024-03-15T18:30:00Z"
    }
  }
}
</code></pre>

## 6.7. File Exchange (Upload and Download)

<p>Scenario: Client sends an image for analysis, and the agent returns a modified image.</p> <p>Request with File Upload:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "role": "ROLE_USER",
    "parts": [
      {
        "text": "Analyze this image and highlight any faces."
      },
      {
        "raw": "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
        "filename": "input_image.png",
        "mediaType": "image/png",
      }
    ],
    "messageId": "6dbc13b5-bd57-4c2b-b503-24e381b6c8d6"
  }
}
</code></pre> <p>Response with File Reference:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "task": {
    "id": "43667960-d455-4453-b0cf-1bae4955270d",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "TASK_STATE_COMPLETED",
      "timestamp": "2024-03-15T12:05:00Z"
    },
    "artifacts": [
      {
        "artifactId": "9b6934dd-37e3-4eb1-8766-962efaab63a1",
        "name": "processed_image_with_faces.png",
        "parts": [
          {
            "url": "https://storage.example.com/processed/task-bbb/output.png?token=xyz",
            "filename": "output.png",
            "mediaType": "image/png"
          }
        ]
      }
    ]
  }
}
</code></pre>

## 6.8. Structured Data Exchange

<p>Scenario: Client asks for a list of open support tickets in a specific JSON format.</p> <p>Request:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/a2a+json
Authorization: Bearer token

{
  "message": {
    "role": "ROLE_USER",
    "parts": [
      {
        "text": "Show me a list of my open IT tickets",
        "metadata": {
          "mediaType": "application/json",
          "schema": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "ticketNumber": { "type": "string" },
                "description": { "type": "string" }
              }
            }
          }
        }
      }
    ],
    "messageId": "85b26db5-ffbb-4278-a5da-a7b09dea1b47"
  }
}
</code></pre> <p>Response with Structured Data:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "task": {
    "id": "d8c6243f-5f7a-4f6f-821d-957ce51e856c",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "TASK_STATE_COMPLETED",
      "timestamp": "2025-04-17T17:47:09.680794Z"
    },
    "artifacts": [
      {
        "artifactId": "c5e0382f-b57f-4da7-87d8-b85171fad17c",
        "parts": [
          {
            "text": "[{\"ticketNumber\":\"REQ12312\",\"description\":\"request for VPN access\"},{\"ticketNumber\":\"REQ23422\",\"description\":\"Add to DL - team-gcp-onboarding\"}]"
          }
        ]
      }
    ]
  }
}
</code></pre>

## 6.9. Fetching Authenticated Extended Agent Card

<p>Scenario: A client discovers a public Agent Card indicating support for an authenticated extended card and wants to retrieve the full details.</p> <p>Step 1: Client fetches the public Agent Card:</p> <pre><code>GET /.well-known/agent-card.json HTTP/1.1
Host: example.com
</code></pre> <p>Response includes:</p> <pre><code>{
  "capabilities": {
    "extendedAgentCard": true
  },
  "securitySchemes": {
    "google": {
      "openIdConnectSecurityScheme": {
        "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration"
      }
    }
  }
}
</code></pre>

## Step 3: Client fetches authenticated extended Agent Card

<pre><code>GET /extendedAgentCard HTTP/1.1
Host: agent.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
</code></pre> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/a2a+json

{
  "name": "Extended Agent with Additional Skills",
  "skills": [
    /* Extended skills available to authenticated users */
  ]
}
</code></pre>

## 7. Authentication and Authorization

<p>A2A treats agents as standard enterprise applications, relying on established web security practices. Identity information is handled at the protocol layer, not within A2A semantics.</p> <p>For a comprehensive guide on enterprise security aspects, see Enterprise-Ready Features.</p>

## 7.1. Protocol Security

<p>Production deployments MUST use encrypted communication (HTTPS for HTTP-based bindings, TLS for gRPC). Implementations SHOULD use modern TLS configurations (TLS 1.3+ recommended) with strong cipher suites.</p>

## 7.2. Server Identity Verification

<p>A2A Clients SHOULD verify the A2A Server's identity by validating its TLS certificate against trusted certificate authorities (CAs) during the TLS handshake.</p>

## 7.3. Client Authentication Process

<ol> <li>Discovery of Requirements: The client discovers the server's required authentication schemes via the <code>securitySchemes</code> field in the AgentCard.</li> <li>Credential Acquisition (Out-of-Band): The client obtains the necessary credentials through an out-of-band process specific to the required authentication scheme.</li> <li>Credential Transmission: The client includes these credentials in protocol-appropriate headers or metadata for every A2A request.</li> </ol>

## 7.4. Server Authentication Responsibilities

<p>The A2A Server:</p> <ul> <li>MUST authenticate every incoming request based on the provided credentials and its declared authentication requirements.</li> <li>SHOULD use appropriate binding-specific error codes for authentication challenges or rejections.</li> <li>SHOULD provide relevant authentication challenge information with error responses.</li> </ul>

## 7.5. In-Task Authentication (Secondary Credentials)

<p>If an agent requires additional credentials during task execution:</p> <ol> <li>It SHOULD transition the A2A task to the <code>TASK_STATE_AUTH_REQUIRED</code> state.</li> <li>The accompanying <code>TaskStatus.update</code> SHOULD provide details about the required secondary authentication.</li> <li>The A2A Client obtains these credentials out-of-band and provides them in a subsequent message request.</li> </ol>

## 7.6. Authorization

<p>Once authenticated, the A2A Server authorizes requests based on the authenticated identity and its own policies. Authorization logic is implementation-specific and MAY consider:</p> <ul> <li>Specific skills requested</li> <li>Actions attempted within tasks</li> <li>Data access policies</li> <li>OAuth scopes (if applicable)</li> </ul>

## 8.1. Purpose

<p>A2A Servers MUST make an Agent Card available. The Agent Card describes the server's identity, capabilities, skills, and interaction requirements. Clients use this information for discovering suitable agents and configuring interactions.</p> <p>For more on discovery strategies, see the Agent Discovery guide.</p>

## 8.2. Discovery Mechanisms

<p>Clients can find Agent Cards through:</p> <ul> <li>Well-Known URI: Accessing <code>https://{server_domain}/.well-known/agent-card.json</code></li> <li>Registries/Catalogs: Querying curated catalogs of agents</li> <li>Direct Configuration: Pre-configured Agent Card URLs or content</li> </ul>

## 8.3. Protocol Declaration Requirements

<p>The AgentCard MUST properly declare supported protocols:</p>

## 8.3.1. Supported Interfaces Declaration

<ul> <li>The <code>supportedInterfaces</code> field SHOULD declare all supported protocol combinations in preference order</li> <li>The first entry in <code>supportedInterfaces</code> represents the preferred interface</li> <li>Each interface MUST accurately declare its transport protocol and URL</li> <li>URLs MAY be reused if multiple transports are available at the same endpoint</li> </ul>

## 8.3.2. Client Protocol Selection

<p>Clients MUST follow these rules:</p> <ol> <li>Parse <code>supportedInterfaces</code> if present, and select the first supported transport</li> <li>Prefer earlier entries in the ordered list when multiple options are supported</li> <li>Use the correct URL for the selected transport</li> </ol>

## 8.4. Agent Card Signing

<p>Agent Cards MAY be digitally signed using JSON Web Signature (JWS) as defined in RFC 7515 to ensure authenticity and integrity. Signatures allow clients to verify that an Agent Card has not been tampered with and originates from the claimed provider.</p>

## 8.4.1. Canonicalization Requirements

<p>Before signing, the Agent Card content MUST be canonicalized using the JSON Canonicalization Scheme (JCS) as defined in RFC 8785. This ensures consistent signature generation and verification across different JSON implementations.</p> <p>Canonicalization Rules:</p> <ol> <li> <p>Field Presence and Default Value Handling: Before canonicalization, the JSON representation MUST respect Protocol Buffer field presence semantics as defined in Section 5.7. This ensures that the canonical form accurately reflects which fields were explicitly provided versus which were omitted, enabling signature verification when Agent Cards are reconstructed:</p> <ul> <li>Optional fields not explicitly set: Fields marked with the <code>optional</code> keyword that were not explicitly set MUST be omitted from the JSON object</li> <li>Optional fields explicitly set to defaults: Fields marked with <code>optional</code> that were explicitly set to a value (even if that value matches a default) MUST be included in the JSON object</li> <li>Required fields: Fields marked with <code>REQUIRED</code> MUST always be present, even if the field value matches the default.</li> <li>Default values: Fields with default values MUST be omitted unless the field is marked as <code>REQUIRED</code> or has the <code>optional</code> keyword.</li> </ul> </li> <li> <p>RFC 8785 Compliance: The Agent Card JSON MUST be canonicalized according to RFC 8785, which specifies:</p> <ul> <li>Predictable ordering of object properties (lexicographic by key)</li> <li>Consistent representation of numbers, strings, and other primitive values</li> <li>Removal of insignificant whitespace</li> </ul> </li> <li> <p>Signature Field Exclusion: The <code>signatures</code> field itself MUST be excluded from the content being signed to avoid circular dependencies.</p> </li> </ol> <p>Example of Default Value Removal:</p> <p>Original Agent Card fragment:</p> <pre><code>{
  "name": "Example Agent",
  "description": "",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "extensions": []
  },
  "skills": []
}
</code></pre> <p>Applying the canonicalization rules:</p> <ul> <li><code>name</code>: "Example Agent" - REQUIRED field → include</li> <li><code>description</code>: "" - REQUIRED field → include</li> <li><code>capabilities</code>: object - REQUIRED field → include (after processing children)<ul> <li><code>streaming</code>: false - optional field, present in JSON (explicitly set) → include</li> <li><code>pushNotifications</code>: false - optional field, present in JSON (explicitly set) → include</li> <li><code>extensions</code>: [] - repeated field (not REQUIRED) with empty array → omit</li> </ul> </li> <li><code>skills</code>: [] - REQUIRED field → include</li> </ul> <p>After applying RFC 8785:</p> <pre><code>{"capabilities":{"pushNotifications":false,"streaming":false},"description":"","name":"Example Agent","skills":[]}
</code></pre>

## 8.4.2. Signature Format

<p>Signatures use the JSON Web Signature (JWS) format as defined in RFC 7515. The <code>AgentCardSignature</code> object represents JWS components using three fields:</p> <ul> <li><code>protected</code> (required, string): Base64url-encoded JSON object containing the JWS Protected Header</li> <li><code>signature</code> (required, string): Base64url-encoded signature value</li> <li><code>header</code> (optional, object): JWS Unprotected Header as a JSON object (not base64url-encoded)</li> </ul> <p>JWS Protected Header Parameters:</p> <p>The protected header MUST include:</p> <ul> <li><code>alg</code>: Algorithm used for signing (e.g., "ES256", "RS256")</li> <li><code>typ</code>: SHOULD be set to "JOSE" for JWS</li> <li><code>kid</code>: Key ID for identifying the signing key</li> </ul> <p>The protected header MAY include:</p> <ul> <li><code>jku</code>: URL to JSON Web Key Set (JWKS) containing the public key</li> </ul> <p>Signature Generation Process:</p> <ol> <li> <p>Prepare the payload:</p> <ul> <li>Remove properties with default values from the Agent Card</li> <li>Exclude the <code>signatures</code> field</li> <li>Canonicalize the resulting JSON using RFC 8785 to produce the canonical payload</li> </ul> </li> <li> <p>Create the protected header:</p> <ul> <li>Construct a JSON object with the required header parameters (<code>alg</code>, <code>typ</code>, <code>kid</code>) and any optional parameters (<code>jku</code>)</li> <li>Serialize the header to JSON</li> <li>Base64url-encode the serialized header to produce the <code>protected</code> field value</li> </ul> </li> <li> <p>Compute the signature:</p> <ul> <li>Construct the JWS Signing Input: <code>ASCII(BASE64URL(UTF8(JWS Protected Header)) || '.' || BASE64URL(JWS Payload))</code></li> <li>Sign the JWS Signing Input using the algorithm specified in the <code>alg</code> header parameter and the private key</li> <li>Base64url-encode the resulting signature bytes to produce the <code>signature</code> field value</li> </ul> </li> <li> <p>Assemble the AgentCardSignature:</p> <ul> <li>Set <code>protected</code> to the base64url-encoded protected header from step 2</li> <li>Set <code>signature</code> to the base64url-encoded signature value from step 3</li> <li>Optionally set <code>header</code> to a JSON object containing any unprotected header parameters.</li> </ul> </li> </ol> <p>Example:</p> <p>Given a canonical Agent Card payload and signing key, the signature generation produces:</p> <pre><code>{
  "protected": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpPU0UiLCJraWQiOiJrZXktMSIsImprdSI6Imh0dHBzOi8vZXhhbXBsZS5jb20vYWdlbnQvandrcy5qc29uIn0",
  "signature": "QFdkNLNszlGj3z3u0YQGt_T9LixY3qtdQpZmsTdDHDe3fXV9y9-B3m2-XgCpzuhiLt8E0tV6HXoZKHv4GtHgKQ"
}
</code></pre> <p>Where the <code>protected</code> value decodes to:</p> <pre><code>{"alg":"ES256","typ":"JOSE","kid":"key-1","jku":"https://example.com/agent/jwks.json"}
</code></pre>

## 8.4.3. Signature Verification

<p>Clients verifying Agent Card signatures MUST:</p> <ol> <li>Extract the signature from the <code>signatures</code> array</li> <li>Retrieve the public key using the <code>kid</code> and <code>jku</code> (or from a trusted key store)</li> <li>Remove properties with default values from the received Agent Card</li> <li>Exclude the <code>signatures</code> field</li> <li>Canonicalize the resulting JSON using RFC 8785</li> <li>Verify the signature against the canonicalized payload</li> </ol> <p>Security Considerations:</p> <ul> <li>Clients SHOULD verify at least one signature before trusting an Agent Card</li> <li>Public keys SHOULD be retrieved over secure channels (HTTPS)</li> <li>Clients MAY maintain a trusted key store for known agent providers</li> <li>Expired or revoked keys MUST NOT be used for verification</li> <li>Multiple signatures MAY be present to support key rotation</li> </ul>

## 8.5. Sample Agent Card

<pre><code>{
  "name": "GeoSpatial Route Planner Agent",
  "description": "Provides advanced route planning, traffic analysis, and custom map generation services. This agent can calculate optimal routes, estimate travel times considering real-time traffic, and create personalized maps with points of interest.",
  "supportedInterfaces": [
    {"url": "https://georoute-agent.example.com/a2a/v1", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"},
    {"url": "https://georoute-agent.example.com/a2a/grpc", "protocolBinding": "GRPC", "protocolVersion": "1.0"},
    {"url": "https://georoute-agent.example.com/a2a/json", "protocolBinding": "HTTP+JSON", "protocolVersion": "1.0"}
  ],
  "provider": {
    "organization": "Example Geo Services Inc.",
    "url": "https://www.examplegeoservices.com"
  },
  "iconUrl": "https://georoute-agent.example.com/icon.png",
  "version": "1.2.0",
  "documentationUrl": "https://docs.examplegeoservices.com/georoute-agent/api",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true,
    "stateTransitionHistory": false,
    "extendedAgentCard": true
  },
  "securitySchemes": {
    "google": {
      "openIdConnectSecurityScheme": {
        "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration"
      }
    }
  },
  "security": [{ "google": ["openid", "profile", "email"] }],
  "defaultInputModes": ["application/json", "text/plain"],
  "defaultOutputModes": ["application/json", "image/png"],
  "skills": [
    {
      "id": "route-optimizer-traffic",
      "name": "Traffic-Aware Route Optimizer",
      "description": "Calculates the optimal driving route between two or more locations, taking into account real-time traffic conditions, road closures, and user preferences (e.g., avoid tolls, prefer highways).",
      "tags": ["maps", "routing", "navigation", "directions", "traffic"],
      "examples": [
        "Plan a route from '1600 Amphitheatre Parkway, Mountain View, CA' to 'San Francisco International Airport' avoiding tolls.",
        "{\"origin\": {\"lat\": 37.422, \"lng\": -122.084}, \"destination\": {\"lat\": 37.7749, \"lng\": -122.4194}, \"preferences\": [\"avoid_ferries\"]}"
      ],
      "inputModes": ["application/json", "text/plain"],
      "outputModes": [
        "application/json",
        "application/vnd.geo+json",
        "text/html"
      ]
    },
    {
      "id": "custom-map-generator",
      "name": "Personalized Map Generator",
      "description": "Creates custom map images or interactive map views based on user-defined points of interest, routes, and style preferences. Can overlay data layers.",
      "tags": ["maps", "customization", "visualization", "cartography"],
      "examples": [
        "Generate a map of my upcoming road trip with all planned stops highlighted.",
        "Show me a map visualizing all coffee shops within a 1-mile radius of my current location."
      ],
      "inputModes": ["application/json"],
      "outputModes": [
        "image/png",
        "image/jpeg",
        "application/json",
        "text/html"
      ]
    }
  ],
  "signatures": [
    {
      "protected": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpPU0UiLCJraWQiOiJrZXktMSIsImprdSI6Imh0dHBzOi8vZXhhbXBsZS5jb20vYWdlbnQvandrcy5qc29uIn0",
      "signature": "QFdkNLNszlGj3z3u0YQGt_T9LixY3qtdQpZmsTdDHDe3fXV9y9-B3m2-XgCpzuhiLt8E0tV6HXoZKHv4GtHgKQ"
    }
  ]
}
</code></pre>

## 9. JSON-RPC Protocol Binding

<p>The JSON-RPC protocol binding provides a simple, HTTP-based interface using JSON-RPC 2.0 for method calls and Server-Sent Events for streaming.</p>

## 9.1. Protocol Requirements

<ul> <li>Protocol: JSON-RPC 2.0 over HTTP(S)</li> <li>Content-Type: <code>application/json</code> for requests and responses</li> <li>Method Naming: PascalCase method names matching gRPC conventions (e.g., <code>SendMessage</code>, <code>GetTask</code>)</li> <li>Streaming: Server-Sent Events (<code>text/event-stream</code>)</li> </ul>

## 9.2. Service Parameter Transmission

<p>A2A service parameters defined in Section 3.2.6 MUST be transmitted using standard HTTP request headers, as JSON-RPC 2.0 operates over HTTP(S).</p> <p>Service Parameter Requirements:</p> <ul> <li>Service parameter names MUST be transmitted as HTTP header fields</li> <li>Service parameter keys are case-insensitive per HTTP specification (RFC 7230)</li> <li>Multiple values for the same service parameter (e.g., <code>A2A-Extensions</code>) SHOULD be comma-separated in a single header field</li> </ul> <p>Example Request with A2A Service Parameters:</p> <pre><code>POST /rpc HTTP/1.1
Host: agent.example.com
Content-Type: application/json
Authorization: Bearer token
A2A-Version: 0.3
A2A-Extensions: https://example.com/extensions/geolocation/v1,https://standards.org/extensions/citations/v1

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "SendMessage",
  "params": { /* SendMessageRequest */ }
}
</code></pre>

## 9.3. Base Request Structure

<p>All JSON-RPC requests MUST follow the standard JSON-RPC 2.0 format:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "category/action",
  "params": { /* method-specific parameters */ }
}
</code></pre>

## 9.4.1. <code>SendMessage</code>

<p>Sends a message to initiate or continue a task.</p> <p>Request:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "SendMessage",
  "params": { /* SendMessageRequest object */ }
}
</code></pre> <p>Referenced Objects: <code>SendMessageRequest</code>, <code>Message</code></p> <p>Response:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    /* SendMessageResponse object, contains one of:
     * "task": { Task object }
     * "message": { Message object }
    */
  }
</code></pre> <p>Referenced Objects: <code>Task</code>, <code>Message</code></p>

## 9.4.2. <code>SendStreamingMessage</code>

<p>Sends a message and subscribes to real-time updates via Server-Sent Events.</p> <p>Request: Same as <code>SendMessage</code></p> <p>Response: HTTP 200 with <code>Content-Type: text/event-stream</code></p> <pre><code>data: {"jsonrpc": "2.0", "id": 1, "result": { /* StreamResponse object */ }}

data: {"jsonrpc": "2.0", "id": 1, "result": { /* StreamResponse object */ }}
</code></pre> <p>Referenced Objects: <code>StreamResponse</code></p>

## 9.4.3. <code>GetTask</code>

<p>Retrieves the current state of a task.</p> <p>Request:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "GetTask",
  "params": {
    "id": "task-uuid",
    "historyLength": 10
  }
}
</code></pre>

## 9.4.4. <code>ListTasks</code>

<p>Lists tasks with optional filtering and pagination.</p> <p>Request:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "ListTasks",
  "params": {
    "contextId": "context-uuid",
    "status": "TASK_STATE_WORKING",
    "pageSize": 50,
    "pageToken": "cursor-token"
  }
}
</code></pre>

## 9.4.5. <code>CancelTask</code>

<p>Cancels an ongoing task.</p> <p>Request:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "CancelTask",
  "params": {
    "id": "task-uuid"
  }
}
</code></pre>

## 9.4.6. <code>SubscribeToTask</code>

<p>Subscribes to a task stream for receiving updates on a task that is not in a terminal state.</p> <p>Request:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "SubscribeToTask",
  "params": {
    "id": "task-uuid"
  }
}
</code></pre> <p>Response: SSE stream (same format as <code>SendStreamingMessage</code>)</p> <p>Error: Returns <code>UnsupportedOperationError</code> if the task is in a terminal state (<code>completed</code>, <code>failed</code>, <code>canceled</code>, or <code>rejected</code>).</p>

## 9.4.7. Push Notification Configuration Methods

<ul> <li><code>CreateTaskPushNotificationConfig</code> - Create push notification configuration</li> <li><code>GetTaskPushNotificationConfig</code> - Get push notification configuration</li> <li><code>ListTaskPushNotificationConfigs</code> - List push notification configurations</li> <li><code>DeleteTaskPushNotificationConfig</code> - Delete push notification configuration</li> </ul>

## 9.4.8. <code>GetExtendedAgentCard</code>

<p>Retrieves an extended Agent Card.</p> <p>Request:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "GetExtendedAgentCard"
}
</code></pre>

## 9.5. Error Handling

<p>JSON-RPC error responses use the standard JSON-RPC 2.0 error object structure, which maps to the generic A2A error model defined in Section 3.3.2 as follows:</p> <ul> <li>Error Code: Mapped to <code>error.code</code> (numeric JSON-RPC error code)</li> <li>Error Message: Mapped to <code>error.message</code> (human-readable string)</li> <li>Error Details: Mapped to <code>error.data</code> (optional structured object)</li> </ul> <p>Standard JSON-RPC Error Codes:</p> JSON-RPC Error Code Error Name Standard Message Description <code>-32700</code> <code>JSONParseError</code> "Invalid JSON payload" The server received invalid JSON <code>-32600</code> <code>InvalidRequestError</code> "Request payload validation error" The JSON sent is not a valid Request object <code>-32601</code> <code>MethodNotFoundError</code> "Method not found" The requested method does not exist or is not available <code>-32602</code> <code>InvalidParamsError</code> "Invalid parameters" The method parameters are invalid <code>-32603</code> <code>InternalError</code> "Internal error" An internal error occurred on the server <p>A2A-Specific Error Codes:</p> <p>A2A-specific errors use codes in the range <code>-32001</code> to <code>-32099</code>. For the complete mapping of A2A error types to JSON-RPC error codes, see Section 5.4 (Error Code Mappings).</p> <p>Error Response Structure:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {
      "method": "invalid/method"
    }
  }
}
</code></pre> <p>Example A2A-Specific Error Response:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32001,
    "message": "Task not found",
    "data": {
      "taskId": "nonexistent-task-id",
      "timestamp": "2025-11-09T10:30:00.000Z"
    }
  }
}
</code></pre> <p>The <code>data</code> field MAY include additional context-specific information to help clients diagnose and resolve the error.</p>

## 10. gRPC Protocol Binding

<p>The gRPC Protocol Binding provides a high-performance, strongly-typed interface using Protocol Buffers over HTTP/2. The gRPC Protocol Binding leverages the API guidelines to simplify gRPC to HTTP mapping.</p>

## 10.1. Protocol Requirements

<ul> <li>Protocol: gRPC over HTTP/2 with TLS</li> <li>Definition: Use the normative Protocol Buffers definition in <code>specification/a2a.proto</code></li> <li>Serialization: Protocol Buffers version 3</li> <li>Service: Implement the <code>A2AService</code> gRPC service</li> </ul>

## 10.2. Service Parameter Transmission

<p>A2A service parameters defined in Section 3.2.6 MUST be transmitted using gRPC metadata (headers).</p> <p>Service Parameter Requirements:</p> <ul> <li>Service parameter names MUST be transmitted as gRPC metadata keys</li> <li>Metadata keys are case-insensitive and automatically converted to lowercase by gRPC</li> <li>Multiple values for the same service parameter (e.g., <code>A2A-Extensions</code>) SHOULD be comma-separated in a single metadata entry</li> </ul> <p>Example gRPC Request with A2A Service Parameters:</p> <pre><code>// Go example using gRPC metadata
md := metadata.Pairs(
    "authorization", "Bearer token",
    "a2a-version", "0.3",
    "a2a-extensions", "https://example.com/extensions/geolocation/v1,https://standards.org/extensions/citations/v1",
)
ctx := metadata.NewOutgoingContext(context.Background(), md)

// Make the RPC call with the context containing metadata
response, err := client.SendMessage(ctx, request)
</code></pre> <p>Metadata Handling:</p> <ul> <li>Implementations MUST extract A2A service parameters from gRPC metadata for processing</li> <li>Servers SHOULD validate required service parameters (e.g., <code>A2A-Version</code>) from metadata</li> <li>Service parameter keys in metadata are normalized to lowercase per gRPC conventions</li> </ul>

## 10.3. Service Definition

Method Request Response Description <code>SendMessage</code> <code>SendMessageRequest</code> <code>SendMessageResponse</code> Sends a message to an agent. <code>SendStreamingMessage</code> <code>SendMessageRequest</code> stream <code>StreamResponse</code> Sends a streaming message to an agent, allowing for real-time interaction and status updates. Streaming version of <code>SendMessage</code> <code>GetTask</code> <code>GetTaskRequest</code> <code>Task</code> Gets the latest state of a task. <code>ListTasks</code> <code>ListTasksRequest</code> <code>ListTasksResponse</code> Lists tasks that match the specified filter. <code>CancelTask</code> <code>CancelTaskRequest</code> <code>Task</code> Cancels a task in progress. <code>SubscribeToTask</code> <code>SubscribeToTaskRequest</code> stream <code>StreamResponse</code> Subscribes to task updates for tasks not in a terminal state. Returns <code>UnsupportedOperationError</code> if the task is already in a terminal state (completed, failed, canceled, rejected). <code>CreateTaskPushNotificationConfig</code> <code>CreateTaskPushNotificationConfigRequest</code> <code>TaskPushNotificationConfig</code> Creates a push notification config for a task. <code>GetTaskPushNotificationConfig</code> <code>GetTaskPushNotificationConfigRequest</code> <code>TaskPushNotificationConfig</code> Gets a push notification config for a task. <code>ListTaskPushNotificationConfigs</code> <code>ListTaskPushNotificationConfigsRequest</code> <code>ListTaskPushNotificationConfigsResponse</code> Get a list of push notifications configured for a task. <code>GetExtendedAgentCard</code> <code>GetExtendedAgentCardRequest</code> <code>AgentCard</code> Gets the extended agent card for the authenticated agent. <code>DeleteTaskPushNotificationConfig</code> <code>DeleteTaskPushNotificationConfigRequest</code> <code>empty</code> Deletes a push notification config for a task.

## 10.4.1. SendMessage

<p>Sends a message to an agent.</p> <p>Request:</p> <p>Represents a request for the <code>SendMessage</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>message</code> <code>Message</code> Yes The message to send to the agent. <code>configuration</code> <code>SendMessageConfiguration</code> No Configuration for the send request. <code>metadata</code> <code>object</code> No A flexible key-value map for passing additional context or parameters. <p>Response:</p> <p>Represents the response for the <code>SendMessage</code> method.</p> Field Type Required Description <code>task</code> <code>Task</code> Optional (OneOf) The task created or updated by the message. <code>message</code> <code>Message</code> Optional (OneOf) A message from the agent. <p>Note: A <code>SendMessageResponse</code> MUST contain exactly one of the following: <code>task</code>, <code>message</code></p>

## 10.4.2. SendStreamingMessage

<p>Sends a message with streaming updates.</p> <p>Request:</p> <p>Represents a request for the <code>SendMessage</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>message</code> <code>Message</code> Yes The message to send to the agent. <code>configuration</code> <code>SendMessageConfiguration</code> No Configuration for the send request. <code>metadata</code> <code>object</code> No A flexible key-value map for passing additional context or parameters. <p>Response: Server streaming <code>StreamResponse</code> objects.</p>

## 10.4.3. GetTask

<p>Retrieves task status.</p> <p>Request:</p> <p>Represents a request for the <code>GetTask</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>id</code> <code>string</code> Yes The resource ID of the task to retrieve. <code>historyLength</code> <code>integer</code> No The maximum number of most recent messages from the task's history to retrieve. An unset value means the client does not impose any limit. A value of zero is a request to not include any messages. The server MUST NOT return more messages than the provided value, but MAY apply a lower limit. <p>Response: See <code>Task</code> object definition.</p>

## 10.4.4. ListTasks

<p>Lists tasks with filtering.</p> <p>Request:</p> <p>Parameters for listing tasks with optional filtering criteria.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Tenant ID, provided as a path parameter. <code>contextId</code> <code>string</code> No Filter tasks by context ID to get tasks from a specific conversation or session. <code>status</code> <code>TaskState</code> No Filter tasks by their current status state. <code>pageSize</code> <code>integer</code> No The maximum number of tasks to return. The service may return fewer than this value. If unspecified, at most 50 tasks will be returned. The minimum value is 1. The maximum value is 100. <code>pageToken</code> <code>string</code> No A page token, received from a previous <code>ListTasks</code> call. <code>ListTasksResponse.next_page_token</code>. Provide this to retrieve the subsequent page. <code>historyLength</code> <code>integer</code> No The maximum number of messages to include in each task's history. <code>statusTimestampAfter</code> <code>timestamp</code> No Filter tasks which have a status updated after the provided timestamp in ISO 8601 format (e.g., "2023-10-27T10:00:00Z"). Only tasks with a status timestamp time greater than or equal to this value will be returned. <code>includeArtifacts</code> <code>boolean</code> No Whether to include artifacts in the returned tasks. Defaults to false to reduce payload size. <p>Response:</p> <p>Result object for <code>ListTasks</code> method containing an array of tasks and pagination information.</p> Field Type Required Description <code>tasks</code> array of <code>Task</code> Yes Array of tasks matching the specified criteria. <code>nextPageToken</code> <code>string</code> Yes A token to retrieve the next page of results, or empty if there are no more results in the list. <code>pageSize</code> <code>integer</code> Yes The page size used for this response. <code>totalSize</code> <code>integer</code> Yes Total number of tasks available (before pagination).

## 10.4.5. CancelTask

<p>Cancels a running task.</p> <p>Request:</p> <p>Represents a request for the <code>CancelTask</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>id</code> <code>string</code> Yes The resource ID of the task to cancel. <code>metadata</code> <code>object</code> No A flexible key-value map for passing additional context or parameters. <p>Response: See <code>Task</code> object definition.</p>

## 10.4.6. SubscribeToTask

<p>Subscribe to task updates via streaming. Returns <code>UnsupportedOperationError</code> if the task is in a terminal state.</p> <p>Request:</p> <p>Represents a request for the <code>SubscribeToTask</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>id</code> <code>string</code> Yes The resource ID of the task to subscribe to. <p>Response: Server streaming <code>StreamResponse</code> objects.</p>

## 10.4.7. CreateTaskPushNotificationConfig

<p>Creates a push notification configuration for a task.</p> <p>Request:</p> <p>Represents a request for the <code>CreateTaskPushNotificationConfig</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>config</code> <code>PushNotificationConfig</code> Yes The configuration to create. <p>Response: See <code>PushNotificationConfig</code> object definition.</p>

## 10.4.8. GetTaskPushNotificationConfig

<p>Retrieves an existing push notification configuration for a task.</p> <p>Request:</p> <p>Represents a request for the <code>GetTaskPushNotificationConfig</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>id</code> <code>string</code> Yes The resource ID of the configuration to retrieve. <p>Response: See <code>PushNotificationConfig</code> object definition.</p>

## 10.4.9. ListTaskPushNotificationConfigs

<p>Lists all push notification configurations for a task.</p> <p>Request:</p> <p>Represents a request for the <code>ListTaskPushNotificationConfigs</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>pageSize</code> <code>integer</code> No The maximum number of configurations to return. <code>pageToken</code> <code>string</code> No A page token received from a previous <code>ListTaskPushNotificationConfigsRequest</code> call. <p>Response:</p> <p>Represents a successful response for the <code>ListTaskPushNotificationConfigs</code> method.</p> Field Type Required Description <code>configs</code> array of <code>TaskPushNotificationConfig</code> No The list of push notification configurations. <code>nextPageToken</code> <code>string</code> No A token to retrieve the next page of results, or empty if there are no more results in the list.

## 10.4.10. DeleteTaskPushNotificationConfig

<p>Removes a push notification configuration for a task.</p> <p>Request:</p> <p>Represents a request for the <code>DeleteTaskPushNotificationConfig</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <code>taskId</code> <code>string</code> Yes The parent task resource ID. <code>id</code> <code>string</code> Yes The resource ID of the configuration to delete. <p>Response: <code>google.protobuf.Empty</code></p>

## 10.4.11. GetExtendedAgentCard

<p>Retrieves the agent's extended capability card after authentication.</p> <p>Request:</p> <p>Represents a request for the <code>GetExtendedAgentCard</code> method.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID, provided as a path parameter. <p>Response: See <code>AgentCard</code> object definition.</p>

## 10.5.1. TaskPushNotificationConfig

<p>Resource wrapper for push notification configurations. This is a gRPC-specific type used in resource-oriented operations to provide the full resource name along with the configuration data.</p> <p>A container associating a push notification configuration with a specific task.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID. <code>taskId</code> <code>string</code> Yes The ID of the task this configuration is associated with. <code>pushNotificationConfig</code> <code>PushNotificationConfig</code> Yes The push notification configuration details. <p>Fields:</p> <p>A container associating a push notification configuration with a specific task.</p> Field Type Required Description <code>tenant</code> <code>string</code> No Optional. Tenant ID. <code>taskId</code> <code>string</code> Yes The ID of the task this configuration is associated with. <code>pushNotificationConfig</code> <code>PushNotificationConfig</code> Yes The push notification configuration details.

## 10.6. Error Handling

<p>gRPC error responses use the standard gRPC status structure with google.rpc.Status, which maps to the generic A2A error model defined in Section 3.3.2 as follows:</p> <ul> <li>Error Code: Mapped to <code>status.code</code> (gRPC status code enum)</li> <li>Error Message: Mapped to <code>status.message</code> (human-readable string)</li> <li>Error Details: Mapped to <code>status.details</code> (repeated google.protobuf.Any messages)</li> </ul> <p>A2A Error Representation:</p> <p>For A2A-specific errors, implementations MUST include a <code>google.rpc.ErrorInfo</code> message in the <code>status.details</code> array with:</p> <ul> <li><code>reason</code>: The A2A error type in UPPER_SNAKE_CASE without the "Error" suffix (e.g., <code>TASK_NOT_FOUND</code>)</li> <li><code>domain</code>: Set to <code>"a2a-protocol.org"</code></li> <li><code>metadata</code>: Optional map of additional error context</li> </ul> <p>For the complete mapping of A2A error types to gRPC status codes, see Section 5.4 (Error Code Mappings).</p> <p>Error Response Example:</p> <pre><code>// Standard gRPC invalid argument error
status {
  code: INVALID_ARGUMENT
  message: "Invalid request parameters"
  details: [
    {
      type: "type.googleapis.com/google.rpc.BadRequest"
      field_violations: [
        {
          field: "message.parts"
          description: "At least one part is required"
        }
      ]
    }
  ]
}
</code></pre> <p>Example A2A-Specific Error Response:</p> <pre><code>// A2A-specific task not found error
status {
  code: NOT_FOUND
  message: "Task with ID 'task-123' not found"
  details: [
    {
      type: "type.googleapis.com/google.rpc.ErrorInfo"
      reason: "TASK_NOT_FOUND"
      domain: "a2a-protocol.org"
      metadata: {
        task_id: "task-123"
        timestamp: "2025-11-09T10:30:00Z"
      }
    }
  ]
}
</code></pre>

## 10.7. Streaming

<p>gRPC streaming uses server streaming RPCs for real-time updates. The <code>StreamResponse</code> message provides a union of possible streaming events:</p> <p>A wrapper object used in streaming operations to encapsulate different types of response data.</p> Field Type Required Description <code>task</code> <code>Task</code> Optional (OneOf) A Task object containing the current state of the task. <code>message</code> <code>Message</code> Optional (OneOf) A Message object containing a message from the agent. <code>statusUpdate</code> <code>TaskStatusUpdateEvent</code> Optional (OneOf) An event indicating a task status update. <code>artifactUpdate</code> <code>TaskArtifactUpdateEvent</code> Optional (OneOf) An event indicating a task artifact update. <p>Note: A <code>StreamResponse</code> MUST contain exactly one of the following: <code>task</code>, <code>message</code>, <code>statusUpdate</code>, <code>artifactUpdate</code></p>

## 11. HTTP+JSON/REST Protocol Binding

<p>The HTTP+JSON protocol binding provides a RESTful interface using standard HTTP methods and JSON payloads.</p>

## 11.1. Protocol Requirements

<ul> <li>Protocol: HTTP(S) with JSON payloads</li> <li>Content-Type: <code>application/json</code> for requests and responses</li> <li>Methods: Standard HTTP verbs (GET, POST, PUT, DELETE)</li> <li>URL Patterns: RESTful resource-based URLs</li> <li>Streaming: Server-Sent Events for real-time updates</li> </ul>

## 11.2. Service Parameter Transmission

<p>A2A service parameters defined in Section 3.2.6 MUST be transmitted using standard HTTP request headers.</p> <p>Service Parameter Requirements:</p> <ul> <li>Service parameter names MUST be transmitted as HTTP header fields</li> <li>Service parameter keys are case-insensitive per HTTP specification (RFC 9110)</li> <li>Multiple values for the same service parameter (e.g., <code>A2A-Extensions</code>) SHOULD be comma-separated in a single header field</li> </ul> <p>Example Request with A2A Service Parameters:</p> <pre><code>POST /message:send HTTP/1.1
Host: agent.example.com
Content-Type: application/json
Authorization: Bearer token
A2A-Version: 0.3
A2A-Extensions: https://example.com/extensions/geolocation/v1,https://standards.org/extensions/citations/v1

{
  "message": {
    "role": "ROLE_USER",
    "parts": [{"text": "Find restaurants near me"}]
  }
}
</code></pre>

## 11.3.1. Message Operations

<ul> <li><code>POST /message:send</code> - Send message</li> <li><code>POST /message:stream</code> - Send message with streaming (SSE response)</li> </ul>

## 11.3.2. Task Operations

<ul> <li><code>GET /tasks/{id}</code> - Get task status</li> <li><code>GET /tasks</code> - List tasks (with query parameters)</li> <li><code>POST /tasks/{id}:cancel</code> - Cancel task</li> <li><code>POST /tasks/{id}:subscribe</code> - Subscribe to task updates (SSE response, returns error for terminal tasks)</li> </ul>

## 11.3.3. Push Notification Configuration

<ul> <li><code>POST /tasks/{id}/pushNotificationConfigs</code> - Create configuration</li> <li><code>GET /tasks/{id}/pushNotificationConfigs/{configId}</code> - Get configuration</li> <li><code>GET /tasks/{id}/pushNotificationConfigs</code> - List configurations</li> <li><code>DELETE /tasks/{id}/pushNotificationConfigs/{configId}</code> - Delete configuration</li> </ul>

## 11.3.4. Agent Card

<ul> <li><code>GET /extendedAgentCard</code> - Get authenticated extended Agent Card</li> </ul>

## 11.4. Request/Response Format

<p>All requests and responses use JSON objects structurally equivalent to the Protocol Buffer definitions.</p> <p>Example Send Message:</p> <pre><code>POST /message:send
Content-Type: application/json

{
  "message": {
    "messageId": "uuid",
    "role": "ROLE_USER",
    "parts": [{"text": "Hello"}]
  },
  "configuration": {
    "acceptedOutputModes": ["text/plain"]
  }
}
</code></pre> <p>Referenced Objects: <code>SendMessageRequest</code>, <code>Message</code></p> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/json

{
  "task": {
    "id": "task-uuid",
    "contextId": "context-uuid",
    "status": {
      "state": "TASK_STATE_COMPLETED"
    }
  }
}
</code></pre> <p>Referenced Objects: <code>Task</code></p>

## 11.5. Query Parameter Naming for Request Parameters

<p>HTTP methods that do not support request bodies (GET, DELETE) MUST transmit operation request parameters as path parameters or query parameters. This section defines how to map Protocol Buffer field names to query parameter names.</p> <p>Naming Convention:</p> <p>Query parameter names MUST use <code>camelCase</code> to match the JSON serialization of Protocol Buffer field names. This ensures consistency with request bodies used in POST operations.</p> <p>Example Mappings:</p> Protocol Buffer Field Query Parameter Name Example Usage <code>context_id</code> <code>contextId</code> <code>?contextId=uuid</code> <code>page_size</code> <code>pageSize</code> <code>?pageSize=50</code> <code>page_token</code> <code>pageToken</code> <code>?pageToken=cursor</code> <code>task_id</code> <code>taskId</code> <code>?taskId=uuid</code> <p>Usage Examples:</p> <p>List tasks with filtering:</p> <pre><code>GET /tasks?contextId=uuid&amp;status=working&amp;pageSize=50&amp;pageToken=cursor
</code></pre> <p>Get task with history:</p> <pre><code>GET /tasks/{id}?historyLength=10
</code></pre> <p>Field Type Handling:</p> <ul> <li>Strings: Passed directly as query parameter values</li> <li>Booleans: Represented as lowercase strings (<code>true</code>, <code>false</code>)</li> <li>Numbers: Represented as decimal strings</li> <li>Enums: Represented using their string values (e.g., <code>status=working</code>)</li> <li>Repeated Fields: Multiple values MAY be passed by repeating the parameter name (e.g., <code>?tag=value1&amp;tag=value2</code>) or as comma-separated values (e.g., <code>?tag=value1,value2</code>)</li> <li>Nested Objects: Not supported in query parameters; operations requiring nested objects MUST use POST with a request body</li> <li>Datetimes/Timestamps: Represented as ISO 8601 strings (e.g., <code>2025-11-09T10:30:00Z</code>)</li> </ul> <p>URL Encoding:</p> <p>All query parameter values MUST be properly URL-encoded per RFC 3986.</p>

## 11.6. Error Handling

<p>HTTP error responses use RFC 9457 Problem Details format with <code>Content-Type: application/problem+json</code>, which maps to the generic A2A error model defined in Section 3.3.2 as follows:</p> <ul> <li>Error Code: Mapped to <code>status</code> (HTTP status code) and <code>type</code> (URI identifier)</li> <li>Error Message: Mapped to <code>detail</code> (human-readable string)</li> <li>Error Details: Mapped to extension fields in the problem details object</li> </ul> <p>A2A Error Representation:</p> <p>For A2A-specific errors, the <code>type</code> field MUST use the URI from the mapping table in Section 5.4 (Error Code Mappings). Additional error context MAY be included as extension fields in the problem details object.</p> <p>Error Response Example:</p> <pre><code>HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://a2a-protocol.org/errors/task-not-found",
  "title": "Task Not Found",
  "status": 404,
  "detail": "The specified task ID does not exist or is not accessible",
  "taskId": "task-123",
  "timestamp": "2025-11-09T10:30:00.000Z"
}
</code></pre> <p>Extension fields like <code>taskId</code> and <code>timestamp</code> provide additional context to help diagnose the error.</p>

## 11.7. Streaming

<p>REST streaming uses Server-Sent Events with the <code>data</code> field containing JSON serializations of the protocol data objects:</p> <pre><code>POST /message:stream
Content-Type: application/json

{ /* SendMessageRequest object */ }
</code></pre> <p>Referenced Objects: <code>SendMessageRequest</code></p> <p>Response:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: text/event-stream

data: { /* StreamResponse object */ }

data: { /* StreamResponse object */ }
</code></pre> <p>Referenced Objects: <code>StreamResponse</code> Streaming responses are simple, linearly ordered sequences: first a <code>Task</code> (or single <code>Message</code>), then zero or more status or artifact update events until the task reaches a terminal or interrupted state, at which point the stream closes. Implementations SHOULD avoid re-ordering events and MAY optionally resend a final <code>Task</code> snapshot before closing.</p>

## 12. Custom Binding Guidelines

<p>While the A2A protocol provides three standard bindings (JSON-RPC, gRPC, and HTTP+JSON/REST), implementers MAY create custom protocol bindings to support additional transport mechanisms or communication patterns. Custom bindings MUST comply with all requirements defined in Section 5 (Protocol Binding Requirements and Interoperability). This section provides additional guidelines specific to developing custom bindings.</p>

## 12.1. Binding Requirements

<p>Custom protocol bindings MUST:</p> <ol> <li>Implement All Core Operations: Support all operations defined in Section 3 (A2A Protocol Operations)</li> <li>Preserve Data Model: Use data structures functionally equivalent to those defined in Section 4 (Protocol Data Model)</li> <li>Maintain Semantics: Ensure operations behave consistently with the abstract operation definitions</li> <li>Document Completely: Provide comprehensive documentation of the binding specification</li> </ol>

## 12.2. Data Type Mappings

<p>Custom bindings MUST provide clear mappings for:</p> <ul> <li>Protocol Buffer Types: Define how each Protocol Buffer message type is represented</li> <li>Timestamps: Follow the conventions in Section 5.6.1 (Timestamps)</li> <li>Binary Data: Specify encoding for binary content (e.g., base64 for text-based protocols)</li> <li>Enumerations: Define representation of enum values (e.g., strings, integers)</li> </ul>

## 12.3. Service Parameter Transmission

<p>As specified in Section 3.2.6 (Service Parameters), custom protocol bindings MUST document how service parameters are transmitted. The binding specification MUST address:</p> <ol> <li>Transmission Mechanism: The protocol-specific method for transmitting service parameter key-value pairs</li> <li>Value Constraints: Any limitations on service parameter values (e.g., character encoding, size limits)</li> <li>Reserved Names: Any service parameter names reserved by the binding itself</li> <li>Fallback Strategy: What happens when the protocol lacks native header support (e.g., passing service parameters in metadata)</li> </ol> <p>Example Documentation Requirements:</p> <ul> <li>For native header support: "Service parameters are transmitted using HTTP request headers. Service parameter keys are case-insensitive and must conform to RFC 7230. Service parameter values must be UTF-8 strings."</li> <li>For protocols without headers: "Service parameters are serialized as a JSON object and transmitted in the request metadata field <code>a2a-service-parameters</code>."</li> </ul>

## 12.4. Error Mapping

<p>Custom bindings MUST:</p> <ol> <li>Map Standard Errors: Provide mappings for all A2A-specific error types defined in Section 3.2.2 (Error Handling)</li> <li>Preserve Error Information: Ensure error details are accessible to clients</li> <li>Use Appropriate Codes: Map to protocol-native error codes where applicable</li> <li>Document Error Format: Specify the structure of error responses</li> </ol>

## 12.5. Streaming Support

<p>If the binding supports streaming operations:</p> <ol> <li>Define Stream Mechanism: Document how streaming is implemented (e.g., WebSockets, long-polling, chunked encoding)</li> <li>Event Ordering: Specify ordering guarantees for streaming events</li> <li>Reconnection: Define behavior for connection interruption and resumption</li> <li>Stream Termination: Specify how stream completion is signaled</li> </ol> <p>If streaming is not supported, the binding MUST clearly document this limitation in the Agent Card.</p>

## 12.6. Authentication and Authorization

<p>Custom bindings MUST:</p> <ol> <li>Support Standard Schemes: Implement authentication schemes declared in the Agent Card</li> <li>Document Integration: Specify how credentials are transmitted in the protocol</li> <li>Handle Challenges: Define how authentication challenges are communicated</li> <li>Maintain Security: Follow security best practices for the transport protocol</li> </ol>

## 12.7. Agent Card Declaration

<p>Custom bindings MUST be declared in the Agent Card:</p> <ol> <li>Transport Identifier: Use a clear, descriptive transport name</li> <li>Endpoint URL: Provide the full URL where the binding is available</li> <li>Documentation Link: Include a URL to the complete binding specification</li> </ol> <p>Example:</p> <pre><code>{
  "supportedInterfaces": [
    {
      "url": "wss://agent.example.com/a2a/websocket",
      "protocolBinding": "WEBSOCKET"
    }
  ]
}
</code></pre>

## 12.8. Interoperability Testing

<p>Custom binding implementers SHOULD:</p> <ol> <li>Test Against Reference: Verify behavior matches standard bindings</li> <li>Document Differences: Clearly note any deviations from standard binding behavior</li> <li>Provide Examples: Include sample requests and responses</li> <li>Test Edge Cases: Verify handling of error conditions, large payloads, and long-running tasks</li> </ol>

## 13. Security Considerations

<p>This section consolidates security guidance and best practices for implementing and operating A2A agents. For additional enterprise security considerations, see Enterprise-Ready Features.</p>

## 13.1. Data Access and Authorization Scoping

<p>Implementations MUST ensure appropriate scope limitation based on the authenticated caller's authorization boundaries. This applies to all operations that access or list tasks and other resources.</p> <p>Authorization Principles:</p> <ul> <li>Servers MUST implement authorization checks on every A2A Protocol Operations request</li> <li>Implementations MUST scope results to the caller's authorized access boundaries as defined by the agent's authorization model</li> <li>Even when <code>contextId</code> or other filter parameters are not specified in requests, implementations MUST scope results to the caller's authorized access boundaries</li> <li>Authorization models are agent-defined and MAY be based on:<ul> <li>User identity (user-based authorization)</li> <li>Organizational roles or groups (role-based authorization)</li> <li>Project or workspace membership (project-based authorization)</li> <li>Organizational or tenant boundaries (multi-tenant authorization)</li> <li>Custom authorization logic specific to the agent's domain</li> </ul> </li> </ul> <p>Operations Requiring Scope Limitation:</p> <ul> <li><code>List Tasks</code>: MUST only return tasks visible to the authenticated client according to the agent's authorization model</li> <li><code>Get Task</code>: MUST verify the authenticated client has access to the requested task according to the agent's authorization model</li> <li>Task-related operations (Cancel, Subscribe, Push Notification Config): MUST verify the client has appropriate access rights according to the agent's authorization model</li> </ul> <p>Implementation Requirements:</p> <ul> <li>Authorization boundaries are defined by each agent's authorization model, not prescribed by the protocol</li> <li>Authorization checks MUST occur before any database queries or operations that could leak information about the existence of resources outside the caller's authorization scope</li> <li>Agents SHOULD document their authorization model and access control policies</li> </ul> <p>See also: Section 3.1.4 List Tasks (Security Note) for operation-specific requirements.</p>

## 13.2. Push Notification Security

<p>When implementing push notifications, both agents (as webhook callers) and clients (as webhook receivers) have security responsibilities.</p> <p>Agent (Webhook Caller) Requirements:</p> <ul> <li>Agents MUST include authentication credentials in webhook requests as specified in <code>PushNotificationConfig.authentication</code></li> <li>Agents SHOULD implement reasonable timeout values for webhook requests (recommended: 10-30 seconds)</li> <li>Agents SHOULD implement retry logic with exponential backoff for failed deliveries</li> <li>Agents MAY stop attempting delivery after a configured number of consecutive failures</li> <li>Agents SHOULD validate webhook URLs to prevent SSRF (Server-Side Request Forgery) attacks:<ul> <li>Reject private IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)</li> <li>Reject localhost and link-local addresses</li> <li>Implement URL allowlists where appropriate</li> </ul> </li> </ul> <p>Client (Webhook Receiver) Requirements:</p> <ul> <li>Clients MUST validate webhook authenticity using the provided authentication credentials</li> <li>Clients SHOULD verify the task ID in the payload matches an expected task they created</li> <li>Clients MUST respond with HTTP 2xx status codes to acknowledge successful receipt</li> <li>Clients SHOULD process notifications idempotently, as duplicate deliveries may occur</li> <li>Clients SHOULD implement rate limiting to prevent webhook flooding</li> <li>Clients SHOULD use HTTPS endpoints for webhook URLs to ensure confidentiality</li> </ul> <p>Configuration Security:</p> <ul> <li>Webhook URLs SHOULD use HTTPS to protect payload confidentiality in transit</li> <li>Authentication tokens in <code>PushNotificationConfig</code> SHOULD be treated as secrets and rotated periodically</li> <li>Agents SHOULD securely store push notification configurations and credentials</li> <li>Clients SHOULD use unique, single-purpose tokens for each push notification configuration</li> </ul> <p>See also: Section 4.3 Push Notification Objects and Section 4.3.3 Push Notification Payload.</p>

## 13.3. Extended Agent Card Access Control

<p>The extended Agent Card feature allows agents to provide additional capabilities or information to authenticated clients beyond what is available in the public Agent Card.</p> <p>Access Control Requirements:</p> <ul> <li>The <code>Get Extended Agent Card</code> operation MUST require authentication</li> <li>Agents MUST authenticate requests using one of the schemes declared in the public <code>AgentCard.securitySchemes</code> and <code>AgentCard.security</code> fields</li> <li>Agents MAY return different extended card content based on the authenticated client's identity or authorization level</li> <li>Agents SHOULD implement appropriate caching headers to control client-side caching of extended cards</li> </ul> <p>Capability-Based Access:</p> <ul> <li>Extended cards MAY include additional skills not present in the public card</li> <li>Extended cards MAY expose more detailed capability information (e.g., rate limits, quotas)</li> <li>Extended cards MAY include organization-specific or user-specific configuration</li> <li>Agents SHOULD document which capabilities are available at different authentication levels</li> </ul> <p>Security Considerations:</p> <ul> <li>Extended cards SHOULD NOT include sensitive information that could be exploited if leaked (e.g., internal service URLs, unmasked credentials)</li> <li>Agents MUST validate that clients have appropriate permissions before returning privileged information in extended cards</li> <li>Clients retrieving extended cards SHOULD replace their cached public Agent Card with the extended version for the duration of their authenticated session</li> <li>Agents SHOULD version extended cards appropriately and honor client cache invalidation</li> </ul> <p>Availability Declaration:</p> <ul> <li>Agents declare extended card support via <code>AgentCard.capabilities.extendedAgentCard</code></li> <li>When <code>capabilities.extendedAgentCard</code> is <code>false</code> or not present, the operation MUST return <code>UnsupportedOperationError</code></li> <li>When support is declared but no extended card is configured, the operation MUST return <code>ExtendedAgentCardNotConfiguredError</code></li> </ul> <p>See also: Section 3.1.11 Get Extended Agent Card and Section 3.3.4 Capability Validation.</p>

## 13.4. General Security Best Practices

<p>Transport Security:</p> <ul> <li>Production deployments MUST use encrypted communication (HTTPS for HTTP-based bindings, TLS for gRPC)</li> <li>Implementations SHOULD use modern TLS configurations (TLS 1.3+ recommended) with strong cipher suites</li> <li>Agents SHOULD enforce HSTS (HTTP Strict Transport Security) headers when using HTTP-based bindings</li> <li>Implementations SHOULD disable support for deprecated SSL/TLS versions (SSLv3, TLS 1.0, TLS 1.1)</li> </ul> <p>Input Validation:</p> <ul> <li>Agents MUST validate all input parameters before processing</li> <li>Agents SHOULD implement appropriate limits on message sizes, file sizes, and request complexity</li> <li>Agents SHOULD sanitize or validate file content types and reject unexpected media types</li> </ul> <p>Credential Management:</p> <ul> <li>API keys, tokens, and other credentials MUST be treated as secrets</li> <li>Credentials SHOULD be rotated periodically</li> <li>Credentials SHOULD be transmitted only over encrypted connections</li> <li>Agents SHOULD implement credential revocation mechanisms</li> <li>Agents SHOULD log authentication failures and implement rate limiting to prevent brute-force attacks</li> </ul> <p>Audit and Monitoring:</p> <ul> <li>Agents SHOULD log security-relevant events (authentication failures, authorization denials, suspicious requests)</li> <li>Agents SHOULD implement monitoring for unusual patterns (rapid task creation, excessive cancellations)</li> <li>Agents SHOULD provide audit trails for sensitive operations</li> <li>Logs MUST NOT include sensitive information (credentials, personal data) unless required and properly protected</li> </ul> <p>Rate Limiting and Abuse Prevention:</p> <ul> <li>Agents SHOULD implement rate limiting on all operations</li> <li>Agents SHOULD return appropriate error responses when rate limits are exceeded</li> <li>Agents MAY implement different rate limits for different operations or user tiers</li> </ul> <p>Data Privacy:</p> <ul> <li>Agents MUST comply with applicable data protection regulations</li> <li>Agents SHOULD provide mechanisms for users to request deletion of their data</li> <li>Agents SHOULD implement appropriate data retention policies</li> <li>Agents SHOULD minimize logging of sensitive or personal information</li> </ul> <p>Custom Binding Security:</p> <ul> <li>Custom protocol bindings MUST address security considerations in their specification</li> <li>Custom bindings SHOULD follow the same security principles as standard bindings</li> <li>Custom bindings MUST document authentication integration and credential transmission</li> </ul> <p>See also: Section 12.6 Authentication and Authorization (Custom Bindings).</p>

## 14. IANA Considerations

<p>This section provides registration templates for the A2A protocol's media type, HTTP headers, and well-known URI, intended for submission to the Internet Assigned Numbers Authority (IANA).</p>

## 14.1.1. application/a2a+json

<p>Type name: <code>application</code></p> <p>Subtype name: <code>a2a+json</code></p> <p>Required parameters: None</p> <p>Optional parameters:</p> <ul> <li>None</li> </ul> <p>Encoding considerations: Binary (UTF-8 encoding MUST be used for JSON text)</p> <p>Security considerations: This media type shares security considerations common to all JSON-based formats as described in RFC 8259, Section 12. Additionally:</p> <ul> <li>Content MUST be validated against the A2A protocol schema before processing</li> <li>Implementations MUST sanitize user-provided content to prevent injection attacks</li> <li>File references within A2A messages MUST be validated to prevent server-side request forgery (SSRF)</li> <li>Authentication and authorization MUST be enforced as specified in Section 7 of the A2A specification</li> <li>Sensitive information in task history and artifacts MUST be protected according to applicable data protection regulations</li> </ul> <p>Interoperability considerations: The A2A protocol supports multiple protocol bindings. This media type is intended for the HTTP+JSON/REST binding.</p> <p>Published specification: Agent2Agent (A2A) Protocol Specification, available at: https://a2a-protocol.org/latest/specification</p> <p>Applications that use this media type: AI agent platforms, agentic workflow systems, multi-agent collaboration tools, and enterprise automation systems that implement the A2A protocol for agent-to-agent communication.</p> <p>Fragment identifier considerations: None</p> <p>Additional information:</p> <ul> <li>Deprecated alias names for this type: None</li> <li>Magic number(s): None</li> <li>File extension(s): .a2a.json</li> <li>Macintosh file type code(s): TEXT</li> </ul> <p>Person &amp; email address to contact for further information: A2A Protocol Working Group, a2a-protocol@example.org</p> <p>Intended usage: COMMON</p> <p>Restrictions on usage: None</p> <p>Author: A2A Protocol Working Group</p> <p>Change controller: A2A Protocol Working Group</p> <p>Provisional registration: No</p>

## 14.2. HTTP Header Field Registrations

<p>Note: The following HTTP headers represent the HTTP-based protocol binding implementation of the abstract A2A service parameters defined in Section 3.2.6. These registrations are specific to HTTP/HTTPS transports.</p>

## 14.2.1. A2A-Version Header

<p>Header field name: A2A-Version</p> <p>Applicable protocol: HTTP</p> <p>Status: Standard</p> <p>Author/Change controller: A2A Protocol Working Group</p> <p>Specification document: Section 3.2.5 of the A2A Protocol Specification</p> <p>Related information: The A2A-Version header field indicates the A2A protocol version that the client is using. The value MUST be in the format <code>Major.Minor</code> (e.g., "0.3"). If the version is not supported by the agent, the agent returns a <code>VersionNotSupportedError</code>.</p> <p>Example:</p> <pre><code>A2A-Version: 0.3
</code></pre>

## 14.2.2. A2A-Extensions Header

<p>Header field name: A2A-Extensions</p> <p>Applicable protocol: HTTP</p> <p>Status: Standard</p> <p>Author/Change controller: A2A Protocol Working Group</p> <p>Specification document: Section 3.2.5 of the A2A Protocol Specification</p> <p>Related information: The A2A-Extensions header field contains a comma-separated list of extension URIs that the client wants to use for the request. Extensions allow agents to provide additional functionality beyond the core A2A specification while maintaining backward compatibility.</p> <p>Example:</p> <pre><code>A2A-Extensions: https://example.com/extensions/geolocation/v1,https://standards.org/extensions/citations/v1
</code></pre>

## 14.3. Well-Known URI Registration

<p>URI suffix: agent-card.json</p> <p>Change controller: A2A Protocol Working Group</p> <p>Specification document: Section 8.2 of the A2A Protocol Specification</p> <p>Related information: The <code>.well-known/agent-card.json</code> URI provides a standardized location for discovering an A2A agent's capabilities, supported protocols, authentication requirements, and available skills. The resource at this URI MUST return an AgentCard object as defined in Section 4.4.1 of the A2A specification.</p> <p>Status: Permanent</p> <p>Security considerations:</p> <ul> <li>The Agent Card MAY contain public information about an agent's capabilities and SHOULD NOT include sensitive credentials or internal implementation details</li> <li>Implementations SHOULD support HTTPS to ensure authenticity and integrity of the Agent Card</li> <li>Agent Cards MAY be signed using JSON Web Signatures (JWS) as specified in the AgentCardSignature object (Section 4.4.7)</li> <li>Clients SHOULD verify signatures when present to ensure the Agent Card has not been tampered with</li> <li>Extended Agent Cards retrieved via authenticated endpoints (Section 3.1.11) MAY contain additional information and MUST enforce appropriate access controls</li> </ul> <p>Example:</p> <pre><code>https://agent.example.com/.well-known/agent-card.json
</code></pre>

## Appendix A. Migration &amp; Legacy Compatibility

<p>This appendix catalogs renamed protocol messages and objects, their legacy identifiers, and the planned deprecation/removal schedule. All legacy names and anchors MUST remain resolvable until the stated earliest removal version.</p> Legacy Name Current Name Earliest Removal Version Notes <code>MessageSendParams</code> <code>SendMessageRequest</code> &gt;= 0.5.0 Request payload rename for clarity (request vs params) <code>SendMessageSuccessResponse</code> <code>SendMessageResponse</code> &gt;= 0.5.0 Unified success response naming <code>SendStreamingMessageSuccessResponse</code> <code>StreamResponse</code> &gt;= 0.5.0 Shorter, binding-agnostic streaming response <code>SetTaskPushNotificationConfigRequest</code> <code>CreateTaskPushNotificationConfigRequest</code> &gt;= 0.5.0 Explicit creation intent <code>ListTaskPushNotificationConfigSuccessResponse</code> <code>ListTaskPushNotificationConfigsResponse</code> &gt;= 0.5.0 Consistent response suffix removal <code>GetAuthenticatedExtendedCardRequest</code> <code>GetExtendedAgentCardRequest</code> &gt;= 0.5.0 Removed "Authenticated" from naming <p>Planned Lifecycle (example timeline; adjust per release strategy):</p> <ol> <li>0.3.x: New names introduced; legacy names documented; aliases added.</li> <li>0.4.x: Legacy names marked "deprecated" in SDKs and schemas; warning notes added.</li> <li>≥0.5.0: Legacy names eligible for removal after review; migration appendix updated.</li> </ol>

## A.1 Legacy Documentation Anchors

<p>Hidden anchor spans preserve old inbound links:</p> <p> </p> <p> </p> <p>Each legacy span SHOULD be placed adjacent to the current object's heading (to be inserted during detailed object section edits). If an exact numeric-prefixed anchor existed (e.g., <code>#414-message</code>), add an additional span matching that historical form if known.</p>

## A.2 Migration Guidance

<p>Client Implementations SHOULD:</p> <ul> <li>Prefer new names immediately for all new integrations.</li> <li>Implement dual-handling where schemas/types permit (e.g., union type or backward-compatible decoder).</li> <li>Log a warning when receiving legacy-named objects after the first deprecation announcement release.</li> </ul> <p>Server Implementations MAY:</p> <ul> <li>Accept both legacy and current request message forms during the overlap period.</li> <li>Emit only current form in responses (recommended) while providing explicit upgrade notes.</li> </ul>

## A.2.1 Breaking Change: Kind Discriminator Removed

<p>Version 1.0 introduces a breaking change in how polymorphic objects are represented in the protocol. This affects <code>Part</code> types and streaming event types.</p> <p>Legacy Pattern (v0.3.x): Objects used an inline <code>kind</code> field as a discriminator to identify the object type:</p> <p>Example 1 - TextPart:</p> <pre><code>{
  "kind": "text",
  "text": "Hello, world!"
}
</code></pre> <p>Example 2 - FilePart:</p> <pre><code>{
  "kind": "file",
  "file": {
    "name": "diagram.png",
    "mimeType": "image/png",
    "fileWithBytes": "iVBORw0KGgo..."
  }
}
</code></pre> <p>Current Pattern (v1.0): Objects now use the JSON member name itself to identify the type. The member name acts as the discriminator, and the value structure depends on the specific type:</p> <p>Example 1 - TextPart:</p> <pre><code>{
  "text": "Hello, world!"
}
</code></pre> <p>Example 2 - FilePart:</p> <pre><code>{
  "raw": "iVBORw0KGgo...",
  "filename": "diagram.png",
  "mediaType": "image/png"
}
</code></pre> <p>Affected Types:</p> <ol> <li>Part Union Types:</li> <li>TextPart:<ul> <li>Legacy: <code>{ "kind": "text", "text": "..." }</code></li> <li>Current: <code>{ "text": "..." }</code> (member presence acts as discriminator)</li> </ul> </li> <li>FilePart:<ul> <li>Legacy: <code>{ "kind": "file", "file": { "name": "...", "mimeType": "...", "fileWithBytes": "..." } }</code></li> <li>Current: <code>{ "raw": "...", "filename": "...", "mediaType": "..." }</code> (or <code>url</code> instead of <code>raw</code>)</li> </ul> </li> <li> <p>DataPart:</p> <ul> <li>Legacy: <code>{ "kind": "data", "data": {...} }</code></li> <li>Current: <code>{ "data": {...}, "mediaType": "application/json" }</code></li> </ul> </li> <li> <p>Streaming Event Types:</p> </li> <li>TaskStatusUpdateEvent:<ul> <li>Legacy: <code>{ "kind": "status-update", "taskId": "...", "status": {...} }</code></li> <li>Current: <code>{ "statusUpdate": { "taskId": "...", "status": {...} } }</code></li> </ul> </li> <li>TaskArtifactUpdateEvent:<ul> <li>Legacy: <code>{ "kind": "artifact-update", "taskId": "...", "artifact": {...} }</code></li> <li>Current: <code>{ "artifactUpdate": { "taskId": "...", "artifact": {...} } }</code></li> </ul> </li> </ol> <p>Migration Strategy:</p> <p>For Clients upgrading from pre-0.3.x:</p> <ol> <li>Update parsers to expect wrapper objects with member names as discriminators</li> <li>When constructing requests, use the new wrapper format</li> <li>Implement version detection based on the agent's <code>protocolVersions</code> in the <code>AgentCard</code></li> <li>Consider maintaining backward compatibility by detecting and handling both formats during a transition period</li> </ol> <p>For Servers upgrading from pre-0.3.x:</p> <ol> <li>Update serialization logic to emit wrapper objects</li> <li>Breaking: The <code>kind</code> field is no longer part of the protocol and should not be emitted</li> <li>Update deserialization to expect wrapper objects with member names</li> <li>Ensure the <code>AgentCard</code> declares the correct <code>protocolVersions</code> (e.g., ["1.0"] or later)</li> </ol> <p>Rationale:</p> <p>This change aligns with modern API design practices and Protocol Buffers' <code>oneof</code> semantics, where the field name itself serves as the type discriminator. This approach:</p> <ul> <li>Reduces redundancy (no need for both a field name and a <code>kind</code> value)</li> <li>Aligns JSON-RPC and gRPC representations more closely</li> <li>Simplifies code generation from schema definitions</li> <li>Eliminates the need for representing inheritance structures in schema languages</li> <li>Improves type safety in strongly-typed languages</li> </ul>

## A.2.2 Breaking Change: Extended Agent Card Field Relocated

<p>Version 1.0 relocates the extended agent card capability from a top-level field to the capabilities object for architectural consistency.</p> <p>Legacy Structure (pre-1.0):</p> <pre><code>{
  "supportsExtendedAgentCard": true,
  "capabilities": {
    "streaming": true
  }
}
</code></pre> <p>Current Structure (1.0+):</p> <pre><code>{
  "capabilities": {
    "streaming": true,
    "extendedAgentCard": true
  }
}
</code></pre> <p>Proto Changes:</p> <ul> <li>Removed: <code>AgentCard.supports_extended_agent_card</code> (field 13)</li> <li>Added: <code>AgentCapabilities.extended_agent_card</code> (field 5)</li> </ul> <p>Migration Steps:</p> <p>For Agent Implementations:</p> <ol> <li>Remove <code>supportsExtendedAgentCard</code> from top-level AgentCard</li> <li>Add <code>extendedAgentCard</code> to <code>capabilities</code> object</li> <li>Update validation: <code>agentCard.capabilities?.extendedAgentCard</code></li> </ol> <p>For Client Implementations:</p> <ol> <li>Update capability checks: <code>agentCard.capabilities?.extendedAgentCard</code></li> <li>Temporary fallback (transition period):</li> </ol> <pre><code>const supported = agentCard.capabilities?.extendedAgentCard ||
                  agentCard.supportsExtendedAgentCard;
</code></pre> <ol> <li>Remove fallback after agent ecosystem migrates</li> </ol> <p>For SDK Developers:</p> <ol> <li>Regenerate code from updated proto</li> <li>Update type definitions</li> <li>Document breaking change in release notes</li> </ol> <p>Rationale:</p> <p>All optional features enabling specific operations (<code>streaming</code>, <code>pushNotifications</code>, <code>stateTransitionHistory</code>) reside in <code>AgentCapabilities</code>. Moving <code>extendedAgentCard</code> achieves:</p> <ul> <li>Architectural consistency</li> <li>Improved discoverability</li> <li>Semantic correctness (it is a capability)</li> </ul>

## A.3 Future Automation

<p>Once the proto→schema generation pipeline lands, this appendix will be partially auto-generated (legacy mapping table sourced from a maintained manifest). Until then, edits MUST be manual and reviewed in PRs affecting <code>a2a.proto</code>.</p>

## Appendix B. Relationship to MCP (Model Context Protocol)

<p>A2A and MCP are complementary protocols designed for different aspects of agentic systems:</p> <ul> <li>Model Context Protocol (MCP): Focuses on standardizing how AI models and agents connect to and interact with tools, APIs, data sources, and other external resources. It defines structured ways to describe tool capabilities (like function calling in LLMs), pass inputs, and receive structured outputs. Think of MCP as the "how-to" for an agent to use a specific capability or access a resource.</li> <li>Agent2Agent Protocol (A2A): Focuses on standardizing how independent, often opaque, AI agents communicate and collaborate with each other as peers. A2A provides an application-level protocol for agents to discover each other, negotiate interaction modalities, manage shared tasks, and exchange conversational context or complex results. It's about how agents partner or delegate work.</li> </ul> <p>How they work together: An A2A Client agent might request an A2A Server agent to perform a complex task. The Server agent, in turn, might use MCP to interact with several underlying tools, APIs, or data sources to gather information or perform actions necessary to fulfill the A2A task.</p> <p>For a more detailed comparison, see the A2A and MCP guide.</p>

---

# Page: /whats-new-v1/

## What's New in A2A Protocol v1.0

<p>This document provides a comprehensive overview of changes from A2A Protocol v0.3.0 to v1.0. The v1.0 release represents a significant maturation of the protocol with enhanced clarity, stronger specifications, and important structural improvements.</p>

## Overview of Major Themes

<p>The v1.0 release focuses on four major themes:</p>

## 1. Protocol Maturity and Standardization

<ul> <li>Leverage formal specification standards (RFC 9457, RFC 8785, RFC 7515) where possible</li> <li>Stricter adherence to industry-standard patterns for REST, gRPC, and JSON-RPC bindings</li> <li>Enhanced versioning strategy with explicit backward compatibility rules</li> <li>Comprehensive error taxonomy with protocol-specific mappings</li> </ul>

## 2. Enhanced Type Safety and Clarity

<ul> <li>Removal of discriminator <code>kind</code> fields in favor of JSON member-based polymorphism</li> <li>Breaking: Enum values changed from <code>kebab-case</code> to <code>SCREAMING_SNAKE_CASE</code> for compliance with the ProtoJSON specification</li> <li>Stricter field naming conventions (<code>camelCase</code> for JSON)</li> <li>More precise timestamp specifications (ISO 8601 with millisecond precision)</li> <li>Better-defined data types with clearer Optional vs Required semantics</li> </ul>

## 3. Improved Developer Experience

<ul> <li>Renamed operations for consistency and clarity</li> <li>Reorganized Agent Card structure for better logical grouping</li> <li>Enhanced extension mechanism with versioning and requirement declarations</li> <li>More explicit service parameter handling (A2A-Version, A2A-Extensions headers)</li> <li>Simplified ID format - Removed complex compound IDs (e.g., <code>tasks/{id}</code>) in favor of simple UUIDs</li> <li>Protocol versioning per interface - Each AgentInterface specifies its own protocol version for better backward compatibility</li> <li>Multi-tenancy support - Native tenant scoping in gRPC requests</li> </ul>

## 4. Enterprise-Ready Features

<ul> <li>Agent Card signature verification using JWS and JSON Canonicalization</li> <li>Formal specification of all three protocol bindings with equivalence guarantees</li> <li>Enhanced security scheme declarations with mutual TLS support</li> <li>Modern OAuth 2.0 flows - Added Device Code flow (RFC 8628), removed deprecated implicit/password flows</li> <li>PKCE support - Added <code>pkce_required</code> field to Authorization Code flow for enhanced security</li> <li>Cursor-based pagination for scalable task listing</li> </ul>

## Send Message (<code>message/send</code> → <code>SendMessage</code>)

<p>v0.3.0 Behavior:</p> <ul> <li>Operation named <code>message/send</code></li> <li>Less formal specification of when <code>Task</code> vs <code>Message</code> is returned</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operation now <code>SendMessage</code></li> <li>✅ CLARIFIED: More precise specification of Task vs Message return semantics</li> </ul>

## Send Streaming Message (<code>message/stream</code> → SendStreamingMessage)

<p>v0.3.0 Behavior:</p> <ul> <li>Operation named <code>message/stream</code></li> <li>Stream events had <code>kind</code> discriminator field</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operation now <code>SendStreamingMessage</code></li> <li>✅ BREAKING: Stream events no longer have <code>kind</code> field<ul> <li>Use JSON member names to discriminate between <code>TaskStatusUpdateEvent</code> and <code>TaskArtifactUpdateEvent</code></li> </ul> </li> <li>✅ REMOVED: <code>final</code> boolean field removed from TaskStatusUpdateEvent. Leverage protocol binding specific stream closure mechanism instead.</li> <li>✅ CLARIFIED: Multiple concurrent streams allowed; all receive same ordered events</li> </ul>

## Get Task (<code>tasks/get</code> → GetTask)

<p>v0.3.0 Behavior:</p> <ul> <li>Operation named <code>tasks/get</code></li> <li>Returns task with status, artifacts, and optionally history</li> <li>Less formal specification of what "include history" means</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operation now GetTask</li> <li>✅ NEW: <code>createdAt</code> and <code>lastModified</code> timestamp fields added to Task object</li> <li>✅ CLARIFIED: More precise specification of history inclusion behavior</li> <li>✅ NEW: Task object now includes <code>extensions[]</code> array in messages and artifacts</li> <li>✅ CLARIFIED: Authentication/authorization scoping - servers MUST only return tasks visible to caller</li> </ul>

## List Tasks (<code>tasks/list</code> → ListTasks)

<p>v0.3.0 Behavior:</p> <ul> <li>Operation named <code>tasks/list</code></li> <li>Available in gRPC and REST only</li> <li>Basic pagination with page numbers</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operation now ListTasks</li> <li>✅ BREAKING: Changed to cursor-based pagination for scalability<ul> <li>Request: <code>cursor</code> (opaque token from previous response), <code>limit</code> (max results)</li> <li>Response: <code>tasks[]</code>, <code>nextCursor</code> (for next page)</li> </ul> </li> <li>✅ NEW: Enhanced filtering capabilities with more explicit specifications</li> <li>✅ CLARIFIED: Task visibility scoped to authenticated caller</li> </ul>

## Cancel Task (<code>tasks/cancel</code> → CancelTask)

<p>v0.3.0 Behavior:</p> <ul> <li>Operation named <code>tasks/cancel</code></li> <li>Request with taskId, returns Task</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operation now CancelTask</li> <li>✅ CLARIFIED: More precise specification of when cancellation is allowed</li> <li>✅ CLARIFIED: Task state transitions for cancellation scenarios</li> </ul>

## Get Agent Card (Well-known URI and GetExtendedAgentCard)

<p>v0.3.0 Behavior:</p> <ul> <li>Discovery via <code>/.well-known/agent-card.json</code></li> <li>Extended card via <code>agent/getAuthenticatedExtendedCard</code></li> <li><code>supportsAuthenticatedExtendedCard</code> boolean at top level</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: <code>agent/getAuthenticatedExtendedCard</code> → GetExtendedAgentCard</li> <li>✅ BREAKING: <code>supportsAuthenticatedExtendedCard</code> moved to <code>capabilities.extendedAgentCard</code></li> <li>✅ NEW: Canonicalization (RFC 8785) clarified for Agent Card signature</li> <li>✅ BREAKING: <code>protocolVersion</code> moved from AgentCard to individual AgentInterface objects</li> <li>✅ BREAKING: <code>preferredTransport</code> and <code>additionalInterfaces</code> consolidated into <code>supportedInterfaces[]</code><ul> <li>Each interface has <code>url</code>, <code>protocolBinding</code>, and <code>protocolVersion</code></li> </ul> </li> </ul>

## Subscribe to task (<code>tasks/resubscribe</code> → SubscribeToTask)

<p>v0.3.0 Behavior:</p> <ul> <li>Used <code>tasks/resubscribe</code> to reconnect interrupted SSE streams</li> <li>Backfill behavior implementation-dependent</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operation now SubscribeToTask</li> <li>✅ CLARIFIED: Formal specification of streaming subscription lifecycle</li> <li>✅ CLARIFIED: Stream closure behavior when task reaches terminal state</li> <li>✅ CLARIFIED: Multiple concurrent subscriptions supported per task</li> </ul>

## Push Notification Operations

<p>v0.3.0 Operations:</p> <ul> <li><code>tasks/pushNotificationConfig/set</code></li> <li><code>tasks/pushNotificationConfig/get</code></li> <li><code>tasks/pushNotificationConfig/list</code></li> <li><code>tasks/pushNotificationConfig/delete</code></li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ RENAMED: Operations now CreatePushNotificationConfig, GetPushNotificationConfig, ListPushNotificationConfigs, DeletePushNotificationConfig</li> <li>✅ NEW: <code>createdAt</code> timestamp field added to PushNotificationConfig</li> <li>✅ CLARIFIED: Push notification payloads now use StreamResponse format</li> </ul>

## NEW: Multi-Tenancy Support

<p>v0.3.0:</p> <ul> <li>No native multi-tenancy support in protocol</li> <li>Tenants handled implicitly via authentication or URL paths</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ NEW: <code>tenant</code> field added to all gRPC request messages</li> <li>✅ NEW: <code>tenant</code> field added to <code>AgentInterface</code> to specify default tenant</li> <li>✅ CLARIFIED: Tenant can be provided per-request or inherited from AgentInterface</li> <li>✅ USE CASE: Enables agents to serve multiple organizations from single endpoint</li> </ul> <p>Example:</p> <pre><code>// Represents a request for the `SendMessage` method.
message SendMessageRequest {
  // Optional tenant, provided as a path parameter.
  string tenant = 4;
  // The message to send to the agent.
  Message message = 1 [(google.api.field_behavior) = REQUIRED];
  // Configuration for the send request.
  SendMessageConfiguration configuration = 2;
  // A flexible key-value map for passing additional context or parameters.
  google.protobuf.Struct metadata = 3;
}
</code></pre>

## ID Format Simplification (#1389)

<p>v0.3.0:</p> <ul> <li>Some operations used complex compound IDs like <code>tasks/{taskId}</code></li> <li>Required clients/servers to construct/deconstruct resource names</li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ BREAKING: All IDs are now simple literals</li> <li>✅ BREAKING: Operations that previously used compound IDs now separate parent and resource ID<ul> <li>Example: <code>tasks/{taskId}/pushNotificationConfigs/{configId}</code> → separate <code>task_id</code> and <code>config_id</code> fields</li> </ul> </li> <li>✅ BENEFIT: Simpler to implement - IDs map directly to database keys</li> </ul>

## HTTP URL Path Simplification (#1269)

<p>v0.3.0:</p> <ul> <li>HTTP+JSON binding used <code>/v1/</code> prefix in URLs</li> <li>Example: <code>POST /v1/message:send</code></li> </ul> <p>v1.0 Changes:</p> <ul> <li>✅ BREAKING: Removed <code>/v1</code> prefix from HTTP+JSON URL paths</li> <li>✅ NEW: Examples: <code>POST /message:send</code>, <code>GET /tasks/{id}</code></li> <li>✅ RATIONALE: Version specified in <code>AgentInterface.protocolVersion</code> field instead</li> <li>✅ BENEFIT: Cleaner URLs, version management at interface level</li> </ul>

## Task Object

<p>Removed Fields:</p> <ul> <li>⛔ <code>kind</code>: Discriminator field removed (was always "task")</li> </ul>

## TaskStatus Object

<p>Modified Fields:</p> <ul> <li>✅ <code>state</code>: BREAKING - Enum values changed from lowercase to <code>SCREAMING_SNAKE_CASE</code> with <code>TASK_STATE_</code> prefix<ul> <li>v0.3.0: <code>"submitted"</code>, <code>"working"</code>, <code>"completed"</code>, <code>"failed"</code>, <code>"canceled"</code>, <code>"rejected"</code>, <code>"input-required"</code>, <code>"auth-required"</code></li> <li>v1.0: <code>"TASK_STATE_SUBMITTED"</code>, <code>"TASK_STATE_WORKING"</code>, <code>"TASK_STATE_COMPLETED"</code>, <code>"TASK_STATE_FAILED"</code>, <code>"TASK_STATE_CANCELED"</code>, <code>"TASK_STATE_REJECTED"</code>, <code>"TASK_STATE_INPUT_REQUIRED"</code>, <code>"TASK_STATE_AUTH_REQUIRED"</code></li> </ul> </li> <li>✅ <code>timestamp</code>: Now explicitly ISO 8601 UTC with millisecond precision (YYYY-MM-DDTHHss.sssZ)</li> </ul> <p>Removed Fields:</p> <ul> <li>None</li> </ul> <p>Example Migration:</p> <pre><code>// v0.3.0
{
  "status": {
    "state": "completed",
    "timestamp": "2024-03-15T10:15:00Z"
  }
}

// v1.0
{
  "status": {
    "state": "TASK_STATE_COMPLETED",
    "timestamp": "2024-03-15T10:15:00.000Z"
  }
}
</code></pre>

## Message Object

<p>Added Fields:</p> <ul> <li>✅ <code>extensions[]</code>: Array of extension URIs applicable to this message</li> </ul> <p>Modified Fields:</p> <ul> <li>✅ <code>role</code>: BREAKING - Enum values changed from lowercase to <code>SCREAMING_SNAKE_CASE</code> with <code>ROLE_</code> prefix<ul> <li>v0.3.0: <code>"user"</code>, <code>"agent"</code></li> <li>v1.0: <code>"ROLE_USER"</code>, <code>"ROLE_AGENT"</code></li> </ul> </li> </ul> <p>Example Migration:</p> <pre><code>// v0.3.0
{
  "role": "user",
  "parts": [{"kind": "text", "text": "Hello"}]
}

// v1.0
{
  "role": "ROLE_USER",
  "parts": [{"text": "Hello"}],
}
</code></pre> <p>Behavior Changes:</p> <ul> <li>Parts array now uses member-based discrimination instead of <code>kind</code> field</li> </ul>

## Part Object

<p>BREAKING CHANGE - Complete Redesign:</p> <p>The Part structure has been completely redesigned in v1.0. Instead of separate TextPart, FilePart, and DataPart message types, there is now a single unified <code>Part</code> message.</p> <p>v0.3.0 Structure (Separate Types):</p> <pre><code>// Text example
{
  "kind": "text",
  "text": "Hello world"
}

// File example
{
  "kind": "file",
  "file": {
    "fileWithUri": "https://example.com/doc.pdf",
    "mimeType": "application/pdf"
  }
}

// Data example
{
  "kind": "data",
  "data": {"key": "value"}
}
</code></pre> <p>v1.0 Structure (Unified Part):</p> <pre><code>// Text example
{
  "text": "Hello world",
  "mediaType": "text/plain"
}

// File with URL example
{
  "url": "https://example.com/doc.pdf",
  "filename": "doc.pdf",
  "mediaType": "application/pdf"
}

// File with raw bytes example
{
  "raw": "base64encodedcontent==",
  "filename": "image.png",
  "mediaType": "image/png"
}

// Data example
{
  "data": {"key": "value"},
  "mediaType": "application/json"
}
</code></pre> <p>Changes:</p> <ul> <li>⛔ REMOVED: Separate <code>TextPart</code>, <code>FilePart</code>, and <code>DataPart</code> types</li> <li>⛔ REMOVED: <code>kind</code> discriminator field</li> <li>⛔ REMOVED: Nested <code>file</code> object structure</li> <li>✅ NEW: Single unified <code>Part</code> message with <code>oneof content</code> field</li> <li>✅ NEW: Content type determined by which field is present: <code>text</code>, <code>raw</code>, <code>url</code>, or <code>data</code></li> <li>✅ NEW: <code>mediaType</code> field (replaces <code>mimeType</code>) - available for all part types</li> <li>✅ NEW: <code>filename</code> field - available for all part types (not just files)</li> <li>✅ NEW: <code>raw</code> field for inline binary content (base64 in JSON)</li> <li>✅ NEW: <code>url</code> field for file references (replaces <code>file.fileWithUri</code>)</li> </ul> <p>Migration Examples:</p> <pre><code>// v0.3.0
const textPart = { kind: "text", text: "Hello" };
const filePart = { kind: "file", file: { fileWithUri: "https://...", mimeType: "image/png" } };
const dataPart = { kind: "data", data: { key: "value" } };

// v1.0
const textPart = { text: "Hello", mediaType: "text/plain" };
const filePart = { url: "https://...", mediaType: "image/png", filename: "image.png" };
const dataPart = { data: { key: "value" }, mediaType: "application/json" };

// Discrimination changed from kind field to member presence
if (part.kind === "text") { ... }  // v0.3.0
if ("text" in part) { ... }        // v1.0
</code></pre>

## Artifact Object

<p>Added Fields:</p> <ul> <li>✅ <code>extensions[]</code>: Array of extension URIs</li> </ul> <p>Modified Fields:</p> <ul> <li>✅ <code>parts[]</code>: Now uses member-based Part discrimination (see Part changes above)</li> </ul>

## AgentCard Object

<p>Added Fields:</p> <ul> <li>✅ <code>supportedInterfaces[]</code>: Array of <code>AgentInterface</code> objects</li> </ul> <p>Removed Fields:</p> <ul> <li>⛔ <code>protocolVersion</code>: Removed from AgentCard (now in each AgentInterface)</li> <li>⛔ <code>preferredTransport</code>: Consolidated into <code>supportedInterfaces</code></li> <li>⛔ <code>additionalInterfaces</code>: Consolidated into <code>supportedInterfaces</code></li> <li>⛔ <code>supportsAuthenticatedExtendedCard</code>: Moved to <code>capabilities.extendedAgentCard</code></li> <li>⛔ <code>url</code>: Primary endpoint now in <code>supportedInterfaces[0].url</code></li> </ul> <p>Structure Example:</p> <p>v0.3.0:</p> <pre><code>{
  "protocolVersion": "0.3",
  "url": "https://agent.example.com/a2a",
  "preferredTransport": "JSONRPC",
  "supportsAuthenticatedExtendedCard": true,
  "additionalInterfaces": [...]
}
</code></pre> <p>v1.0:</p> <pre><code>{
  "supportedInterfaces": [
    {
      "url": "https://agent.example.com/a2a",
      "protocolBinding": "JSONRPC",
      "protocolVersion": "1.0"
    }
  ],
  "capabilities": {
    "extendedAgentCard": true
  },
  "signatures": [...]
}
</code></pre>

## AgentCapabilities Object

<p>Removed Fields:</p> <ul> <li>⛔ <code>stateTransitionHistory</code> - Removed as no API implementation existed for this feature</li> </ul> <p>Rationale:</p> <p>The <code>stateTransitionHistory</code> capability flag was misleading as v1.0 has no corresponding API to:</p> <ul> <li>Store status history in Task objects</li> <li>Retrieve status history via Get/List operations</li> <li>Query historical state transitions</li> </ul> <p>This capability may be reintroduced in a future version with proper implementation.</p> <p>Modified Fields:</p> <ul> <li>✅ <code>extendedAgentCard</code>: Moved from top-level <code>supportsAuthenticatedExtendedCard</code> field</li> </ul>

## PushNotificationConfig Object

<p>Added Fields:</p> <ul> <li>✅ <code>configId</code>: Unique identifier for the configuration</li> <li>✅ <code>createdAt</code>: Timestamp - Configuration creation time</li> </ul> <p>Modified Fields:</p> <ul> <li>✅ <code>authentication</code>: Enhanced PushNotificationAuthenticationInfo structure</li> </ul>

## Stream Event Objects

<p>TaskStatusUpdateEvent:</p> <p>v0.3.0:</p> <pre><code>{
  "kind": "taskStatusUpdate",
  "taskId": "...",
  "contextId": "...",
  "status": {...},
  "final": true
}
</code></pre> <p>v1.0:</p> <pre><code>{
  "taskStatusUpdate": {
    "taskId": "...",
    "contextId": "...",
    "status": {...}
  }
}
</code></pre> <p>Changes:</p> <ul> <li>⛔ REMOVED: <code>kind</code> discriminator</li> <li>⛔ REMOVED: <code>final</code> boolean field (stream closure indicates completion instead)</li> <li>✅ NEW PATTERN: Event type determined by JSON member name (<code>taskStatusUpdate</code> or <code>taskArtifactUpdate</code>)</li> <li>✅ CLARIFIED: Terminal state indicated by protocol-specific stream closure mechanism</li> </ul> <p>TaskArtifactUpdateEvent:</p> <p>v0.3.0:</p> <pre><code>{
  "kind": "taskArtifactUpdate",
  "taskId": "...",
  "contextId": "...",
  "artifact": {...}
}
</code></pre> <p>v1.0:</p> <pre><code>{
  "taskArtifactUpdate": {
    "taskId": "...",
    "contextId": "...",
    "artifact": {...},
    "index": 0
  }
}
</code></pre> <p>Changes:</p> <ul> <li>⛔ REMOVED: <code>kind</code> discriminator</li> <li>✅ NEW PATTERN: Wrapped in <code>taskArtifactUpdate</code> object</li> <li>✅ NEW: <code>index</code> field indicates artifact position in task's artifacts array</li> </ul>

## OAuth 2.0 Security Updates (#1303)

<p>v1.0 modernizes OAuth 2.0 support in alignment with OAuth 2.0 Security Best Current Practice (BCP).</p> <p>Removed Flows (Deprecated by OAuth BCP):</p> <ul> <li>⛔ <code>ImplicitOAuthFlow</code> - Deprecated due to token leakage risks in browser history/logs</li> <li>⛔ <code>PasswordOAuthFlow</code> - Deprecated due to credential exposure risks</li> </ul> <p>Added Flows:</p> <ul> <li>✅ <code>DeviceCodeOAuthFlow</code> (RFC 8628) - For CLI tools, IoT devices, and input-constrained scenarios<ul> <li>Provides <code>device_authorization_url</code> endpoint</li> <li>Supports <code>verification_uri</code>, <code>user_code</code> pattern</li> <li>Ideal for headless environments</li> </ul> </li> </ul> <p>Enhanced Security:</p> <ul> <li>✅ <code>pkce_required</code> field added to <code>AuthorizationCodeOAuthFlow</code> (RFC 7636)<ul> <li>Indicates whether PKCE (Proof Key for Code Exchange) is mandatory</li> <li>Protects against authorization code interception attacks</li> <li>Recommended for all OAuth clients, required for public clients</li> </ul> </li> </ul> <p>Migration Guide:</p> <pre><code>// v0.3.0 - Implicit Flow (now removed)
{
  "implicitFlow": {
    "authorizationUrl": "https://auth.example.com/authorize",
    "scopes": {"read": "Read access"}
  }
}

// v1.0 - Use Authorization Code + PKCE instead
{
  "authorizationCodeFlow": {
    "authorizationUrl": "https://auth.example.com/authorize",
    "tokenUrl": "https://auth.example.com/token",
    "pkceRequired": true,
    "scopes": {"read": "Read access"}
  }
}
</code></pre>

## New Dependencies on Other Specifications

<p>v1.0 introduces several new formal dependencies on industry-standard specifications:</p>

## ✅ RFC 9457 - Problem Details for HTTP APIs

<ul> <li>Purpose: Standardized error response format</li> <li>Usage: HTTP+JSON binding error responses</li> <li>Impact: More consistent, machine-readable error handling in REST APIs</li> </ul>

## ✅ RFC 8785 - JSON Canonicalization Scheme (JCS)

<ul> <li>Purpose: Deterministic JSON serialization for signing</li> <li>Usage: Agent Card signature verification</li> <li>Impact: Enables cryptographic verification of Agent Card integrity</li> <li>Details: Canonical form used before JWS signing (excludes <code>signatures</code> field)</li> </ul>

## ✅ RFC 7515 - JSON Web Signature (JWS)

<ul> <li>Purpose: Cryptographic signing standard</li> <li>Usage: Agent Card signatures field</li> <li>Impact: Industry-standard signature format for trust verification</li> <li>Details: Supports detached signatures with public key retrieval via <code>jku</code> or trusted keystores</li> </ul>

## ✅ Google API Design Guidelines

<ul> <li>Purpose: gRPC best practices and conventions</li> <li>Usage: gRPC binding design patterns</li> <li>Impact: Better alignment with gRPC ecosystem expectations</li> </ul>

## ✅ ISO 8601

<ul> <li>Purpose: Timestamp format standard</li> <li>Usage: All timestamp fields (createdAt, lastModified, timestamp)</li> <li>Impact: Explicit format requirement: UTC with millisecond precision (YYYY-MM-DDTHHss.sssZ)</li> </ul>

## Existing Dependencies (Retained from v0.3.0)

<ul> <li>JSON-RPC 2.0</li> <li>gRPC / Protocol Buffers 3</li> <li>HTTP/HTTPS (various RFCs)</li> <li>Server-Sent Events (SSE) - W3C specification</li> <li>RFC 8615 - Well-known URIs</li> <li>OAuth 2.0, OpenID Connect (for authentication)</li> <li>TLS (RFC 8446 recommended)</li> </ul>

## Complementary Protocol

<p>Model Context Protocol (MCP):</p> <ul> <li>Relationship clarified: MCP handles tool/resource integration, A2A handles agent-to-agent coordination</li> <li>Protocols are complementary, not competing</li> <li>Agents may support both protocols for different use cases</li> </ul>

## 1. Part Type Unification (CRITICAL IMPACT)

<p>The most significant breaking change: TextPart, FilePart, and DataPart types have been removed and replaced with a single unified Part structure.</p> <p>Before (v0.3.0):</p> <pre><code>// Separate types with kind discriminator
if (part.kind === "text") {
  return part.text;
} else if (part.kind === "file") {
  if (part.file.fileWithUri) {
    return fetchFile(part.file.fileWithUri);
  } else {
    return part.file.fileWithBytes;
  }
} else if (part.kind === "data") {
  return part.data;
}
</code></pre> <p>After (v1.0):</p> <pre><code>// Unified Part with oneof content
if ("text" in part) {
  return part.text;
} else if ("url" in part) {
  return fetchFile(part.url);
} else if ("raw" in part) {
  return decodeBase64(part.raw);
} else if ("data" in part) {
  return part.data;
}
</code></pre>

## 2. Stream Event Discriminator Pattern (HIGH IMPACT)

<p>Stream events changed from kind-based to wrapper-based discrimination:</p> <p>Before (v0.3.0):</p> <pre><code>if (event.kind === "taskStatusUpdate") {
  handleStatusUpdate(event);
} else if (event.kind === "taskArtifactUpdate") {
  handleArtifactUpdate(event);
}
</code></pre> <p>After (v1.0):</p> <pre><code>if ("taskStatusUpdate" in event) {
  handleStatusUpdate(event.taskStatusUpdate);
} else if ("taskArtifactUpdate" in event) {
  handleArtifactUpdate(event.taskArtifactUpdate);
}
</code></pre>

## 3. Agent Card Structure (HIGH IMPACT)

<p>Agent discovery and capability checking requires updates:</p> <p>Before (v0.3.0):</p> <pre><code>const endpoint = agentCard.url;
const transport = agentCard.preferredTransport;
const supportsExtended = agentCard.supportsAuthenticatedExtendedCard;
</code></pre> <p>After (v1.0):</p> <pre><code>const primaryInterface = agentCard.supportedInterfaces[0];
const endpoint = primaryInterface.url;
const transport = primaryInterface.protocolBinding;
const supportsExtended = agentCard.capabilities.extendedAgentCard;
</code></pre>

## 4. Pagination (MEDIUM IMPACT)

<p>List Tasks implementation must switch from page-based to cursor-based:</p> <p>Before (v0.3.0):</p> <pre><code>const response = await listTasks({ page: 1, perPage: 50 });
</code></pre> <p>After (v1.0):</p> <pre><code>let cursor = undefined;
do {
  const response = await listTasks({ cursor, limit: 50 });
  // process response.tasks
  cursor = response.nextCursor;
} while (cursor);
</code></pre>

## 5. Enum Value Changes (HIGH IMPACT)

<p>All enum values now use SCREAMING_SNAKE_CASE with type prefixes:</p> <p>TaskState:</p> <pre><code>// v0.3.0
if (task.status.state === "completed") { ... }
if (task.status.state === "input-required") { ... }

// v1.0
if (task.status.state === "TASK_STATE_COMPLETED") { ... }
if (task.status.state === "TASK_STATE_INPUT_REQUIRED") { ... }
</code></pre> <p>MessageRole:</p> <pre><code>// v0.3.0
const message = { role: "user", parts: [...] };

// v1.0
const message = { role: "ROLE_USER", parts: [...] };
</code></pre> <p>Complete Mapping:</p> <ul> <li><code>"submitted"</code> → <code>"TASK_STATE_SUBMITTED"</code></li> <li><code>"working"</code> → <code>"TASK_STATE_WORKING"</code></li> <li><code>"completed"</code> → <code>"TASK_STATE_COMPLETED"</code></li> <li><code>"failed"</code> → <code>"TASK_STATE_FAILED"</code></li> <li><code>"canceled"</code> → <code>"TASK_STATE_CANCELED"</code></li> <li><code>"rejected"</code> → <code>"TASK_STATE_REJECTED"</code></li> <li><code>"input-required"</code> → <code>"TASK_STATE_INPUT_REQUIRED"</code></li> <li><code>"auth-required"</code> → <code>"TASK_STATE_AUTH_REQUIRED"</code></li> <li><code>"user"</code> → <code>"ROLE_USER"</code></li> <li><code>"agent"</code> → <code>"ROLE_AGENT"</code></li> </ul>

## 6. Field Name Changes (LOW IMPACT)

<ul> <li><code>file.mimeType</code> → <code>mediaType</code></li> <li>Operation names (aliases provided during transition)</li> </ul>

## 1. Blocking Parameter Control

<pre><code>// Wait for task completion
const result = await sendMessage(message, { blocking: true });

// Return immediately, poll later
const task = await sendMessage(message, { blocking: false });
</code></pre>

## 2. Agent Card Signature Verification

<pre><code>if (agentCard.signatures &amp;&amp; agentCard.signatures.length &gt; 0) {
  const verified = await verifyAgentCardSignature(agentCard);
  if (!verified) {
    throw new Error("Agent Card signature verification failed");
  }
}
</code></pre>

## 3. Extension Requirements

<pre><code>const requiredExtensions = agentCard.extensions
  .filter(ext =&gt; ext.required)
  .map(ext =&gt; ext.uri);

// Check if client supports required extensions
if (!clientSupportsAll(requiredExtensions)) {
  throw new Error("Missing required extension support");
}
</code></pre>

## 4. Enhanced Timestamp Tracking

<pre><code>const taskAge = Date.now() - new Date(task.createdAt).getTime();
const timeSinceUpdate = Date.now() - new Date(task.lastModified).getTime();
</code></pre>

## 5. Versioning Negotiation

<pre><code>// Client sends A2A-Version header
headers["A2A-Version"] = "1.0";

// Server validates and rejects if unsupported
if (!supportedVersions.includes(requestedVersion)) {
  throw new VersionNotSupportedError();
}
</code></pre>

## Phase 1: Compatibility Layer

<ol> <li>Add support for parsing both old and new discriminator patterns</li> <li>Implement version detection based on protocol version</li> <li>Support both Agent Card structures during transition</li> </ol>

## Phase 2: Dual Support

<ol> <li>Update all APIs to emit v1.0 format</li> <li>Maintain backward compatibility readers for v0.3.0</li> <li>Add A2A-Version header handling</li> <li>Implement cursor-based pagination alongside legacy page-based</li> </ol>

## Phase 3: v1.0 Only

<ol> <li>Deprecate v0.3.0 compatibility code</li> <li>Remove legacy discriminator parsing</li> <li>Remove page-based pagination</li> <li>Clean up dual-format support code</li> </ol>

## Backward Compatibility Strategy (#1401)

<p>v1.0 introduces a formal approach to protocol versioning that enables SDK backward compatibility.</p> <p>Protocol Version Per Interface:</p> <ul> <li>Each <code>AgentInterface</code> now specifies its own <code>protocolVersion</code> field</li> <li>Agents can support multiple protocol versions simultaneously by exposing multiple interfaces</li> <li>Clients negotiate version by selecting appropriate interface from Agent Card</li> </ul> <p>SDK Implementation Pattern:</p> <pre><code>// SDK can support multiple protocol versions
class A2AClient {
  async connect(agentCardUrl: string) {
    const card = await this.getAgentCard(agentCardUrl);

    // Find best matching interface
    const interface = card.supportedInterfaces.find(i =&gt;
      this.supportedVersions.includes(i.protocolVersion)
    );

    if (!interface) {
      throw new Error("No compatible protocol version");
    }

    // Use version-specific adapter
    return this.createAdapter(interface.protocolVersion, interface);
  }
}
</code></pre> <p>Benefits:</p> <ul> <li>SDKs can maintain support for multiple protocol versions</li> <li>Agents can gradually migrate by supporting both old and new versions</li> <li>Clients automatically select best compatible version</li> <li>Enables graceful deprecation of old protocol versions</li> </ul>

## Testing Considerations

<ul> <li>Test with both v0.3.0 and v1.0 formatted data</li> <li>Validate Agent Card signature verification</li> <li>Test cursor-based pagination edge cases (empty results, single page, etc.)</li> <li>Verify proper handling of new error types</li> <li>Test extension requirement validation</li> </ul>

## Critical (Do Immediately)

<ul> <li>Update Part and streaming event parsing (discriminator pattern)</li> <li>Update Agent Card parsing (structure changes)</li> <li>Add A2A-Version header to all requests</li> </ul>

## High (Within 1 Month)

<ul> <li>Implement cursor-based pagination</li> <li>Update enum value handling (state field)</li> <li>Add blocking parameter support</li> </ul>

## Medium (Within 3 Months)

<ul> <li>Implement Agent Card signature verification</li> <li>Add extension requirement checking</li> <li>Update timestamp handling to ISO 8601 format</li> <li>Implement new error types</li> </ul>

## Low (Nice to Have)

<ul> <li>Add createdAt/lastModified timestamp tracking</li> <li>Leverage enhanced metadata capabilities</li> <li>Implement mutual TLS authentication support</li> </ul>

## Conclusion

<p>A2A Protocol v1.0 represents a significant step forward in protocol maturity while maintaining the core architectural principles of v0.3.0. The changes focus on standardization, type safety, and enterprise readiness, requiring developers to update their implementations but providing clearer specifications and better developer experience in return.</p> <p>The breaking changes, while requiring code updates, are straightforward to implement and improve code clarity. The new capabilities around versioning, signatures, and enhanced extensions provide a solid foundation for future protocol evolution within the v1.x line.</p> <p>Developers should plan for a phased migration approach, prioritizing the critical breaking changes while gradually adopting new capabilities over time.</p>

---

# Page: /sdk/

## A2A SDK

<p>A2A currently hosts SDKs in five languages (Python, Go, JS, Java, .NET).</p> <p>The following table lists the supported languages and their stability.</p> Language Support Python Stable Go Stable Java Stable JavaScript Stable C#/.NET Stable <p>The A2A project provides numerous samples across supported languages in the a2a-samples repository.</p>

---

# Page: /sdk/python/

## Python SDK

<p>Redirecting to API reference...</p>

---

# Page: /topics/a2a-and-mcp/

## A2A and MCP: Detailed Comparison

<p>In AI agent development, two key protocol types emerge to facilitate interoperability. One connects agents to tools and resources. The other enables agent-to-agent collaboration. The Agent2Agent (A2A) Protocol and the Model Context Protocol (MCP) address these distinct but highly complementary needs.</p>

## Model Context Protocol

<p>The Model Context Protocol (MCP) defines how an AI agent interacts with and utilizes individual tools and resources, such as a database or an API.</p> <p>This protocol offers the following capabilities:</p> <ul> <li>Standardizes how AI models and agents connect to and interact with tools,   APIs, and other external resources.</li> <li>Defines a structured way to describe tool capabilities, similar to function   calling in Large Language Models.</li> <li>Passes inputs to tools and receives structured outputs.</li> <li>Supports common use cases, such as an LLM calling an external API, an agent   querying a database, or an agent connecting to predefined functions.</li> </ul>

## Agent2Agent Protocol

<p>The Agent2Agent Protocol focuses on enabling different agents to collaborate with one another to achieve a common goal.</p> <p>This protocol offers the following capabilities:</p> <ul> <li>Standardizes how independent, often opaque, AI agents communicate and   collaborate as peers.</li> <li>Provides an application-level protocol for agents to discover each other,   negotiate interactions, manage shared tasks, and exchange conversational   context and complex data.</li> <li>Supports typical use cases, including a customer service agent delegating an   inquiry to a billing agent, or a travel agent coordinating with flight,   hotel, and activity agents.</li> </ul>

## Why Different Protocols?

<p>Both the MCP and A2A protocols are essential for building complex AI systems, and they address distinct but highly complementary needs. The distinction between A2A and MCP depends on what an agent interacts with.</p> <ul> <li>Tools and Resources (MCP Domain):<ul> <li>Characteristics: These are typically primitives with well-defined,     structured inputs and outputs. They perform specific, often stateless,     functions. Examples include a calculator, a database query API, or a     weather lookup service.</li> <li>Purpose: Agents use tools to gather information and perform discrete     functions.</li> </ul> </li> <li>Agents (A2A domain):<ul> <li>Characteristics: These are more autonomous systems. They reason,     plan, use multiple tools, maintain state over longer interactions, and     engage in complex, often multi-turn dialogues to achieve novel or     evolving tasks.</li> <li>Purpose: Agents collaborate with other agents to tackle broader, more     complex goals.</li> </ul> </li> </ul>

## A2A ❤️ MCP: Complementary Protocols for Agentic Systems

<p>An agentic application might primarily use A2A to communicate with other agents. Each individual agent internally uses MCP to interact with its specific tools and resources.</p> <p></p> <p>An agentic application might use A2A to communicate with other agents, while each agent internally uses MCP to interact with its specific tools and resources.</p>

## Example Scenario: The Auto Repair Shop

<p>Consider an auto repair shop staffed by autonomous AI agent "mechanics". These mechanics use special-purpose tools, such as vehicle diagnostic scanners, repair manuals, and platform lifts, to diagnose and repair problems. The repair process can involve extensive conversations, research, and interaction with part suppliers.</p> <ul> <li> <p>Customer Interaction (User-to-Agent using A2A): A customer (or their     primary assistant agent) uses A2A to communicate with the "Shop Manager"     agent.</p> <p>For example, the customer might say, "My car is making a rattling noise".</p> </li> <li> <p>Multi-turn Diagnostic Conversation (Agent-to-Agent using A2A): The Shop     Manager agent uses A2A for a multi-turn diagnostic conversation.</p> <p>For example, the Manager might ask, "Can you send a video of the noise?" or "I see some fluid leaking. How long has this been happening?".</p> </li> <li> <p>Internal Tool Usage (Agent-to-Tool using MCP): The Mechanic agent,     assigned the task by the Shop Manager, needs to diagnose the issue. The     Mechanic agent uses MCP to interact with its specialized tools.</p> <p>For example:</p> <ul> <li>MCP call to a "Vehicle Diagnostic Scanner" tool:     <code>scan_vehicle_for_error_codes(vehicle_id='XYZ123')</code></li> <li>MCP call to a "Repair Manual Database" tool:     <code>get_repair_procedure(error_code='P0300', vehicle_make='Toyota',     vehicle_model='Camry')</code></li> <li>MCP call to a "Platform Lift" tool: <code>raise_platform(height_meters=2)</code></li> </ul> </li> <li> <p>Supplier Interaction (Agent-to-Agent using A2A): The Mechanic agent     determines that a specific part is needed. The Mechanic agent uses A2A to     communicate with a "Parts Supplier" agent to order a part.     For example, the     Mechanic agent might ask, "Do you have part #12345 in stock for a Toyota Camry 2018?"</p> </li> <li> <p>Order processing (Agent-to-Agent using A2A): The Parts Supplier agent,     which is also an A2A-compliant system, responds, potentially leading to an     order.</p> </li> </ul> <p>In this example:</p> <ul> <li>A2A facilitates the higher-level, conversational, and task-oriented     interactions between the customer and the shop, and between the shop's     agents and external supplier agents.</li> <li>MCP enables the mechanic agent to use its specific, structured tools to     perform its diagnostic and repair functions.</li> </ul> <p>An A2A server could expose some of its skills as MCP-compatible resources. However, A2A's primary strength lies in its support for more flexible, stateful, and collaborative interactions. These interactions go beyond a typical tool invocation. A2A focuses on agents partnering on tasks, whereas MCP focuses on agents using capabilities.</p>

## Representing A2A Agents as MCP Resources

<p>An A2A Server (a remote agent) could expose some of its skills as MCP-compatible resources, especially if those skills are well-defined and can be invoked in a more tool-like, stateless manner. In such a case, another agent might "discover" this A2A agent's specific skill through an MCP-style tool description (perhaps derived from its Agent Card).</p> <p>However, the primary strength of A2A lies in its support for more flexible, stateful, and collaborative interactions that go beyond typical tool invocation. A2A is about agents partnering on tasks, while MCP is more about agents using capabilities.</p> <p>By leveraging both A2A for inter-agent collaboration and MCP for tool integration, developers can build more powerful, flexible, and interoperable AI systems.</p>

---

# Page: /topics/agent-discovery/

## Agent Discovery in A2A

<p>To collaborate using the Agent2Agent (A2A) protocol, AI agents need to first find each other and understand their capabilities. A2A standardizes agent self-descriptions through the Agent Card. However, discovery methods for these Agent Cards vary by environment and requirements. The Agent Card defines what an agent offers. Various strategies exist for a client agent to discover these cards. The choice of strategy depends on the deployment environment and security requirements.</p>

## The Role of the Agent Card

<p>The Agent Card is a JSON document that serves as a digital "business card" for an A2A Server (the remote agent). It is crucial for agent discovery and interaction. The key information included in an Agent Card is as follows:</p> <ul> <li>Identity: Includes <code>name</code>, <code>description</code>, and <code>provider</code> information.</li> <li>Service Endpoint: Specifies the <code>url</code> for the A2A service.</li> <li>A2A Capabilities: Lists supported features such as <code>streaming</code> or <code>pushNotifications</code>.</li> <li>Authentication: Details the required <code>schemes</code> (e.g., "Bearer", "OAuth2").</li> <li>Skills: Describes the agent's tasks using <code>AgentSkill</code> objects, including <code>id</code>, <code>name</code>, <code>description</code>, <code>inputModes</code>, <code>outputModes</code>, and <code>examples</code>.</li> </ul> <p>Client agents use the Agent Card to determine an agent's suitability, structure requests, and ensure secure communication.</p>

## Discovery Strategies

<p>The following sections detail common strategies used by client agents to discover remote Agent Cards:</p>

## 1. Well-Known URI

<p>This approach is recommended for public agents or agents intended for broad discovery within a specific domain.</p> <ul> <li> <p>Mechanism: A2A Servers make their Agent Card discoverable by hosting it at a standardized, <code>well-known</code> URI on their domain. The standard path is <code>https://{agent-server-domain}/.well-known/agent-card.json</code>, following the principles of RFC 8615.</p> </li> <li> <p>Process:</p> <ol> <li>A client agent knows or programmatically discovers the domain of a potential A2A Server (e.g., <code>smart-thermostat.example.com</code>).</li> <li>The client performs an HTTP GET request to <code>https://smart-thermostat.example.com/.well-known/agent-card.json</code>.</li> <li>If the Agent Card exists and is accessible, the server returns it as a JSON response.</li> </ol> </li> <li> <p>Advantages:</p> <ul> <li>Ease of implementation</li> <li>Adheres to standards</li> <li>Facilitates automated discovery</li> </ul> </li> <li> <p>Considerations:</p> <ul> <li>Best suited for open or domain-controlled discovery scenarios.</li> <li>Authentication is necessary at the endpoint serving the Agent Card if it contains sensitive details.</li> </ul> </li> </ul>

## 2. Curated Registries (Catalog-Based Discovery)

<p>This approach is employed in enterprise environments or public marketplaces, where Agent Cards are often managed by a central registry. The curated registry acts as a central repository, allowing clients to query and discover agents based on criteria like "skills" or "tags".</p> <ul> <li> <p>Mechanism: An intermediary service (the registry) maintains a collection of Agent Cards. Clients query this registry to find agents based on various criteria (e.g., skills offered, tags, provider name, capabilities).</p> </li> <li> <p>Process:</p> <ol> <li>A2A Servers publish their Agent Cards to the registry.</li> <li>Client agents query the registry's API, and search by criteria such as "specific skills".</li> <li>The registry returns matching Agent Cards or references.</li> </ol> </li> <li> <p>Advantages:</p> <ul> <li>Centralized management and governance.</li> <li>Capability-based discovery (e.g., by skill).</li> <li>Support for access controls and trust frameworks.</li> <li>Applicable in both private and public marketplaces.</li> </ul> </li> <li>Considerations:<ul> <li>Requires deployment and maintenance of a registry service.</li> <li>The current A2A specification does not prescribe a standard API for curated registries.</li> </ul> </li> </ul>

## 3. Direct Configuration / Private Discovery

<p>This approach is used for tightly coupled systems, private agents, or development purposes, where clients are directly configured with Agent Card information or URLs.</p> <ul> <li>Mechanism: Client applications utilize hardcoded details, configuration files, environment variables, or proprietary APIs for discovery.</li> <li>Process: The process is specific to the application's deployment and configuration strategy.</li> <li>Advantages: This method is straightforward for establishing connections within known, static relationships.</li> <li>Considerations:<ul> <li>Inflexible for dynamic discovery scenarios.</li> <li>Changes to Agent Card information necessitate client reconfiguration.</li> <li>Proprietary API-based discovery also lacks standardization.</li> </ul> </li> </ul>

## Securing Agent Cards

<p>Agent Cards include sensitive information, such as:</p> <ul> <li>URLs for internal or restricted agents.</li> <li>Descriptions of sensitive skills.</li> </ul>

## Protection Mechanisms

<p>To mitigate risks, the following protection mechanisms should be considered:</p> <ul> <li>Authenticated Agent Cards: We recommend the use of authenticated extended agent cards for sensitive information or for serving a more detailed version of the card.</li> <li> <p>Secure Endpoints: Implement access controls on the HTTP endpoint serving the Agent Card (e.g., <code>/.well-known/agent-card.json</code> or registry API). The methods include:</p> <ul> <li>Mutual TLS (mTLS)</li> <li>Network restrictions (e.g., IP ranges)</li> <li>HTTP Authentication (e.g., OAuth 2.0)</li> </ul> </li> <li> <p>Registry Selective Disclosure: Registries return different Agent Cards based on the client's identity and permissions.</p> </li> </ul> <p>Any Agent Card containing sensitive data must be protected with authentication and authorization mechanisms. The A2A specification strongly recommends the use of out-of-band dynamic credentials rather than embedding static secrets within the Agent Card.</p>

## Future Considerations

<p>The A2A community explores standardizing registry interactions or advanced discovery protocols.</p>

---

# Page: /topics/enterprise-ready/

## Enterprise Implementation of A2A

<p>The Agent2Agent (A2A) protocol is designed with enterprise requirements at its core. Rather than inventing new, proprietary standards for security and operations, A2A aims to integrate seamlessly with existing enterprise infrastructure and widely adopted best practices. This approach allows organizations to use their existing investments and expertise in security, monitoring, governance, and identity management.</p> <p>A key principle of A2A is that agents are typically opaque because they don't share internal memory, tools, or direct resource access with each other. This opacity naturally aligns with standard client-server security paradigms, treating remote agents as standard HTTP-based enterprise applications.</p>

## Transport Level Security (TLS)

<p>Ensuring the confidentiality and integrity of data in transit is fundamental for any enterprise application.</p> <ul> <li>HTTPS Mandate: All A2A communication in production environments must     occur over <code>HTTPS</code>.</li> <li>Modern TLS Standards: Implementations should use modern TLS versions.     TLS 1.2 or higher is recommended. Strong, industry-standard cipher suites     should be used to protect data from eavesdropping and tampering.</li> <li>Server Identity Verification: A2A clients should verify the A2A server's     identity by validating its TLS certificate against trusted certificate     authorities during the TLS handshake. This prevents man-in-the-middle     attacks.</li> </ul>

## Authentication

<p>A2A delegates authentication to standard web mechanisms. It primarily relies on HTTP headers and established standards like OAuth2 and OpenID Connect. Authentication requirements are advertised by the A2A server in its Agent Card.</p> <ul> <li>No Identity in Payload: A2A protocol payloads, such as <code>JSON-RPC</code>     messages, don't carry user or client identity information directly. Identity     is established at the transport/HTTP layer.</li> <li>Agent Card Declaration: The A2A server's Agent Card describes the     authentication schemes it supports in its <code>security</code> field and aligns with     those defined in the OpenAPI Specification for authentication.</li> <li>Out-of-Band Credential Acquisition: The A2A Client obtains the necessary credentials,     such as OAuth 2.0 tokens or API keys, through processes external to the A2A protocol itself. Examples include OAuth flows or secure key distribution.</li> <li>HTTP Header Transmission: Credentials must be transmitted in standard     HTTP headers as per the requirements of the chosen authentication scheme.     Examples include <code>Authorization: Bearer &lt;TOKEN&gt;</code> or <code>API-Key: &lt;KEY_VALUE&gt;</code>.</li> <li>Server-Side Validation: The A2A server must authenticate every     incoming request using the credentials provided in the HTTP headers.<ul> <li>If authentication fails or credentials are missing, the server should     respond with a standard HTTP status code:<ul> <li><code>401 Unauthorized</code>: If the credentials are missing or invalid. This     response should include a <code>WWW-Authenticate</code> header to inform     the client about the supported authentication methods.</li> <li><code>403 Forbidden</code>: If the credentials are valid, but the authenticated     client does not have permission to perform the requested action.</li> </ul> </li> </ul> </li> <li>In-Task Authentication (Secondary Credentials): If an agent needs     additional credentials to access a different system or service during a     task (for example, to use a specific tool on the user's behalf), the A2A server     indicates to the client that more information is needed. The client     is then responsible for obtaining these secondary credentials through a     process outside of the A2A protocol itself (for example, an OAuth flow) and     providing them back to the A2A server to continue the task.</li> </ul>

## Authorization

<p>Once a client is authenticated, the A2A server is responsible for authorizing the request. Authorization logic is specific to the agent's implementation, the data it handles, and applicable enterprise policies.</p> <ul> <li>Granular Control: Authorization should be applied based on the     authenticated identity, which could represent an end user, a client     application, or both.</li> <li>Skill-Based Authorization: Access can be controlled on a per-skill     basis, as advertised in the Agent Card. For example, specific OAuth scopes     should grant an authenticated client access to invoke certain skills but     not others.</li> <li>Data and Action-Level Authorization: Agents that interact with backend     systems, databases, or tools must enforce appropriate authorization before     performing sensitive actions or accessing sensitive data through those     underlying resources. The agent acts as a gatekeeper.</li> <li>Principle of Least Privilege: Agents must grant only the necessary     permissions required for a client or user to perform their intended     operations through the A2A interface.</li> </ul>

## Data Privacy and Confidentiality

<p>Protecting sensitive data exchanged between agents is paramount, requiring strict adherence to privacy regulations and best practices.</p> <ul> <li>Sensitivity Awareness: Implementers must be acutely aware of the     sensitivity of data exchanged in Message and Artifact parts of A2A     interactions.</li> <li>Compliance: Ensure compliance with relevant data privacy regulations     such as GDPR, CCPA, and HIPAA, based on the domain and data involved.</li> <li>Data Minimization: Avoid including or requesting unnecessarily sensitive     information in A2A exchanges.</li> <li>Secure Handling: Protect data both in transit, using TLS as mandated,     and at rest if persisted by agents, according to enterprise data security     policies and regulatory requirements.</li> </ul>

## Tracing, Observability, and Monitoring

<p>A2A's reliance on HTTP allows for straightforward integration with standard enterprise tracing, logging, and monitoring tools, providing critical visibility into inter-agent workflows.</p> <ul> <li>Distributed Tracing: A2A Clients and Servers should participate in     distributed tracing systems. For example, use OpenTelemetry to propagate     trace context, including trace IDs and span IDs, through standard HTTP     headers, such as W3C Trace Context headers. This enables end-to-end     visibility for debugging and performance analysis.</li> <li>Comprehensive Logging: Log details on both client and server, including     taskId, sessionId, correlation IDs, and trace context for troubleshooting     and auditing.</li> <li>Metrics: A2A servers should expose key operational metrics, such as     request rates, error rates, task processing latency, and resource     utilization, to enable performance monitoring, alerting, and capacity     planning.</li> <li>Auditing: Audit significant events, such as task creation, critical     state changes, and agent actions, especially when involving sensitive data     or high-impact operations.</li> </ul>

## API Management and Governance

<p>For A2A servers exposed externally, across organizational boundaries, or even within large enterprises, integration with API Management solutions is highly recommended, as this provides:</p> <ul> <li>Centralized Policy Enforcement: Consistent application of security     policies such as authentication and authorization, rate limiting, and quotas.</li> <li>Traffic Management: Load balancing, routing, and mediation.</li> <li>Analytics and Reporting: Insights into agent usage, performance, and     trends.</li> <li>Developer Portals: Facilitate discovery of A2A-enabled agents, provide documentation such as Agent Cards, and streamline onboarding for client developers.</li> </ul> <p>By adhering to these enterprise-grade practices, A2A implementations can be deployed securely, reliably, and manageably within complex organizational environments. This fosters trust and enables scalable inter-agent collaboration.</p>

---

# Page: /topics/extensions/

## Extensions in A2A

<p>The Agent2Agent (A2A) protocol provides a strong foundation for inter-agent communication. However, specific domains or advanced use cases often require additional structure, custom data, or new interaction patterns beyond the generic methods. Extensions are A2A's powerful mechanism for layering new capabilities onto the base protocol.</p> <p>Extensions allow for extending the A2A protocol with new data, requirements, RPC methods, and state machines. Agents declare their support for specific extensions in their Agent Card, and clients can then opt in to the behavior offered by an extension as part of requests they make to the agent. Extensions are identified by a URI and defined by their own specification. Anyone is able to define, publish, and implement an extension.</p> <p>The flexibility of extensions allows for customizing A2A without fragmenting the core standard, fostering innovation and domain-specific optimizations.</p>

## Scope of Extensions

<p>The exact set of possible ways to use extensions is intentionally broad, facilitating the ability to expand A2A beyond known use cases. However, some foreseeable applications include:</p> <ul> <li>Data-only Extensions: Exposing new, structured information in the Agent     Card that doesn't impact the request-response flow. For example, an     extension could add structured data about an agent's GDPR compliance.</li> <li>Profile Extensions: Overlaying additional structure and state change     requirements on the core request-response messages. This type effectively     acts as a profile on the core A2A protocol, narrowing the space of allowed     values (for example, requiring all messages to use <code>DataParts</code> adhering to     a specific schema). This can also include augmenting existing states in the     task state machine by using metadata. For example, an extension could define     a 'generating-image' substate when <code>TaskStatus.state</code> is 'working' and     <code>TaskStatus.message.metadata["generating-image"]</code> is true.</li> <li>Method Extensions (Extended Skills): Adding entirely new RPC methods     beyond the core set defined by the protocol. An Extended Skill refers to a     capability or function an agent gains or exposes specifically through the     implementation of an extension that defines new RPC methods. For example, a     <code>task-history</code> extension might add a <code>tasks/search</code> RPC method to retrieve     a list of previous tasks, effectively providing the agent with a new,     extended skill.</li> <li>State Machine Extensions: Adding new states or transitions to the task   state machine.</li> </ul>

## List of Example Extensions

Extension Description Secure Passport Extension Adds a trusted, contextual layer for immediate personalization and reduced overhead (v1). Hello World or Timestamp Extension A simple extension demonstrating how to augment base A2A types by adding timestamps to the <code>metadata</code> field of <code>Message</code> and <code>Artifact</code> objects (v1). Traceability Extension Explore the Python implementation and basic usage of the Traceability Extension (v1). Agent Gateway Protocol (AGP) Extension A Core Protocol Layer or Routing Extension that introduces Autonomous Squads (ASq) and routes Intent payloads based on declared Capabilities, enhancing scalability (v1).

## Limitations

<p>There are some changes to the protocol that extensions don't allow, primarily to prevent breaking core type validations:</p> <ul> <li>Changing the Definition of Core Data Structures: For example, adding new     fields or removing required fields to protocol-defined data structures.     Extensions should place custom attributes in the <code>metadata</code> map present on     core data structures.</li> <li>Adding New Values to Enum Types: Extensions should use existing enum values     and annotate additional semantic meaning in the <code>metadata</code> field.</li> </ul>

## Extension Declaration

<p>Agents declare their support for extensions in their Agent Card by including <code>AgentExtension</code> objects within their <code>AgentCapabilities</code> object.</p> <p>A declaration of a protocol extension supported by an Agent.</p> Field Type Required Description <code>uri</code> <code>string</code> No The unique URI identifying the extension. <code>description</code> <code>string</code> No A human-readable description of how this agent uses the extension. <code>required</code> <code>boolean</code> No If true, the client must understand and comply with the extension's requirements. <code>params</code> <code>object</code> No Optional. Extension-specific configuration parameters. <p>The following is an example of an Agent Card with an extension:</p> <pre><code>{
  "name": "Magic 8-ball",
  "description": "An agent that can tell your future... maybe.",
  "version": "0.1.0",
  "url": "https://example.com/agents/eightball",
  "capabilities": {
    "streaming": true,
    "extensions": [
      {
        "uri": "https://example.com/ext/konami-code/v1",
        "description": "Provide cheat codes to unlock new fortunes",
        "required": false,
        "params": {
          "hints": [
            "When your sims need extra cash fast",
            "You might deny it, but we've seen the evidence of those cows."
          ]
        }
      }
    ]
  },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"],
  "skills": [
    {
      "id": "fortune",
      "name": "Fortune teller",
      "description": "Seek advice from the mystical magic 8-ball",
      "tags": ["mystical", "untrustworthy"]
    }
  ]
}
</code></pre>

## Required Extensions

<p>While extensions generally offer optional functionality, some agents may have stricter requirements. When an Agent Card declares an extension as <code>required: true</code>, it signals to clients that some aspect of the extension impacts how requests are structured or processed, and that the client must abide by it. Agents shouldn't mark data-only extensions as required. If a client does not request activation of a required extension, or fails to follow its protocol, the agent should reject the incoming request with an appropriate error.</p>

## Extension Specification

<p>The detailed behavior and structure of an extension are defined by its specification. While the exact format is not mandated, it should contain at least:</p> <ul> <li>The specific URI(s) that identify the extension.</li> <li>The schema and meaning of objects specified in the <code>params</code> field of the     <code>AgentExtension</code> object.</li> <li>Schemas of any additional data structures communicated between client and     agent.</li> <li>Details of new request-response flows, additional endpoints, or any other     logic required to implement the extension.</li> </ul>

## Extension Dependencies

<p>Extensions might depend on other extensions. This can be a required dependency (where the extension cannot function without the dependent) or an optional one (where additional functionality is enabled if another extension is present). Extension specifications should document these dependencies. It is the client's responsibility to activate an extension and all its required dependencies as listed in the extension's specification.</p>

## Extension Activation

<p>Extensions default to being inactive, providing a baseline experience for extension-unaware clients. Clients and agents perform negotiation to determine which extensions are active for a specific request.</p> <ol> <li>Client Request: A client requests extension activation by including the     <code>A2A-Extensions</code> header in the HTTP request to the agent. The value is a     comma-separated list of extension URIs the client intends to activate.</li> <li>Agent Processing: Agents are responsible for identifying supported     extensions in the request and performing the activation. Any requested     extensions not supported by the agent can be ignored.</li> <li>Response: Once the agent has identified all activated extensions, the     response SHOULD include the <code>A2A-Extensions</code> header, listing all     extensions that were successfully activated for that request.</li> </ol> <p></p> <p>Example request showing extension activation:</p> <pre><code>POST /agents/eightball HTTP/1.1
Host: example.com
Content-Type: application/json
A2A-Extensions: https://example.com/ext/konami-code/v1
Content-Length: 519
{
  "jsonrpc": "2.0",
  "method": "SendMessage",
  "id": "1",
  "params": {
    "message": {
      "messageId": "1",
      "role": "ROLE_USER",
      "parts": [{"text": "Oh magic 8-ball, will it rain today?"}]
    },
    "metadata": {
      "https://example.com/ext/konami-code/v1/code": "motherlode"
    }
  }
}
</code></pre> <p>Corresponding response echoing activated extensions:</p> <pre><code>HTTP/1.1 200 OK
Content-Type: application/json
A2A-Extensions: https://example.com/ext/konami-code/v1
Content-Length: 338
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "message": {
      "messageId": "2",
      "role": "ROLE_AGENT",
      "parts": [{"text": "That's a bingo!"}]
    }
  }
}
</code></pre>

## Implementation Considerations

<p>While the A2A protocol defines the functionality of extensions, this section provides guidance on their implementation—best practices for authoring, versioning, and distributing extension implementations.</p> <ul> <li>Versioning: Extension specifications evolve. It is     crucial to have a clear versioning strategy to ensure that clients and     agents can negotiate compatible implementations.<ul> <li>Recommendation: Use the extension's URI as the primary version     identifier, ideally including a version number (for example,     <code>https://example.com/ext/my-extension/v1</code>).</li> <li>Breaking Changes: A new URI MUST be used when introducing a breaking     change to an extension's logic, data structures, or required parameters.</li> <li>Handling Mismatches: If a client requests a version not supported by     the agent, the agent SHOULD ignore the activation request for that     extension; it MUST NOT fall back to a different version.</li> </ul> </li> <li>Discoverability and Publication:<ul> <li>Specification Hosting: The extension specification document should be     hosted at the extension's URI.</li> <li>Permanent Identifiers: Authors are encouraged to use a permanent     identifier service, such as <code>w3id.org</code>, for their extension URIs to     prevent broken links.</li> <li>Community Registry (Future): The A2A community might establish a     central registry for discovering and browsing available extensions in     the future.</li> </ul> </li> <li> <p>Packaging and Reusability (A2A SDKs and Libraries):     To promote adoption, extension logic should be packaged into reusable         libraries that can be integrated into existing A2A client and         server applications.</p> <ul> <li>An extension implementation should be distributed as a     standard package for its language ecosystem (for example, a PyPI package     for Python, an npm package for TypeScript/JavaScript).</li> <li> <p>The objective is to provide a streamlined integration experience for     developers. A well-designed extension package should allow a developer     to add it to their server with minimal code, for example:</p> <pre><code>import logging
import os

import click

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent import ReimbursementAgent
from agent_executor import ReimbursementAgentExecutor
from dotenv import load_dotenv
from timestamp_ext import TimestampExtension


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GEMINI_API_KEY'):
                raise MissingAPIKeyError(
                    'GEMINI_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        hello_ext = TimestampExtension()
        capabilities = AgentCapabilities(
            streaming=True,
            extensions=[
                hello_ext.agent_extension(),
            ],
        )
        skill = AgentSkill(
            id='process_reimbursement',
            name='Process Reimbursement Tool',
            description='Helps with the reimbursement process for users given the amount and purpose of the reimbursement.',
            tags=['reimbursement'],
            examples=[
                'Can you reimburse me $20 for my lunch with the clients?'
            ],
        )
        agent_card = AgentCard(
            name='Reimbursement Agent',
            description='This agent handles the reimbursement process for the employees given the amount and purpose of the reimbursement.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            default_input_modes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        agent_executor = ReimbursementAgentExecutor()
        # Use the decorator version of the extension for highest ease of use.
        agent_executor = hello_ext.wrap_executor(agent_executor)
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        import uvicorn

        uvicorn.run(server.build(), host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
</code></pre> <p>This example showcases how A2A SDKs or libraries such as <code>a2a.server</code> in Python facilitate the implementation of A2A agents and extensions.</p> </li> </ul> </li> <li> <p>Security: Extensions modify the core behavior of the A2A protocol, and therefore     introduce new security considerations:</p> <ul> <li>Input Validation: Any new data fields, parameters, or methods     introduced by an extension MUST be rigorously validated. Treat all     extension-related data from an external party as untrusted input.</li> <li>Scope of Required Extensions: Be mindful when marking an extension as     <code>required: true</code> in an Agent Card. This creates a hard dependency for     all clients and should only be used for extensions fundamental to the     agent's core function and security (for example, a message signing     extension).</li> <li>Authentication and Authorization: If an extension adds new methods,     the implementation MUST ensure these methods are subject to the same     authentication and authorization checks as the core A2A methods. An     extension MUST NOT provide a way to bypass the agent's primary security     controls.</li> </ul> </li> </ul> <p>For more information, see the A2A Extensions: Empowering Custom Agent Functionality blog post.</p>

---

# Page: /topics/key-concepts/

## Core Concepts and Components in A2A

<p>A2A uses a set of core concepts that define how agents interact. Understand these core building blocks to develop or integrate with A2A-compliant systems.</p> <p></p>

## Core Actors in A2A Interactions

<ul> <li>User: The end user, which can be a human operator or an automated     service. The user initiates a request or defines a goal that requires     assistance from one or more AI agents.</li> <li>A2A Client (Client Agent): An application, service, or another AI agent     that acts on behalf of the user. The client initiates communication using the     A2A protocol.</li> <li>A2A Server (Remote Agent): An AI agent or an agentic system that exposes     an HTTP endpoint implementing the A2A protocol. It receives requests from     clients, processes tasks, and returns results or status updates. From the client's perspective,     the remote agent operates as an opaque (black-box) system, meaning its internal workings, memory, or tools are not exposed.</li> </ul>

## Fundamental Communication Elements

<p>The following table describes the fundamental communication elements in A2A:</p> Element Description Key Purpose Agent Card A JSON metadata document describing an agent's identity, capabilities, endpoint, skills, and authentication requirements. Enables clients to discover agents and understand how to interact with them securely and effectively. Task A stateful unit of work initiated by an agent, with a unique ID and defined lifecycle. Facilitates tracking of long-running operations and enables multi-turn interactions and collaboration. Message A single turn of communication between a client and an agent, containing content and a role ("user" or "agent"). Conveys instructions, context, questions, answers, or status updates that are not necessarily formal artifacts. Part The fundamental content container used within Messages and Artifacts. A Part holds one of: text content, a file reference (URL or inline bytes), or structured data. Provides flexibility for agents to exchange various content types within messages and artifacts. Artifact A tangible output generated by an agent during a task (for example, a document, image, or structured data). Delivers the concrete results of an agent's work, ensuring structured and retrievable outputs.

## Interaction Mechanisms

<p>The A2A Protocol supports various interaction patterns to accommodate different needs for responsiveness and persistence. These mechanisms ensure that agents can exchange information efficiently and reliably, regardless of the task's complexity or duration:</p> <ul> <li>Request/Response (Polling): Clients send a request and the server     responds. For long-running tasks, the client periodically polls the server     for updates.</li> <li>Streaming with Server-Sent Events (SSE): Clients initiate a stream to     receive real-time, incremental results or status updates from the server     over an open HTTP connection.</li> <li>Push Notifications: For very long-running tasks or disconnected     scenarios, the server can actively send asynchronous notifications to a     client-provided webhook when significant task updates occur.</li> </ul> <p>For a detailed exploration of streaming and push notifications, refer to the Streaming &amp; Asynchronous Operations document.</p>

## Agent Cards

<p>The Agent Card is a JSON document that serves as a digital business card for initial discovery and interaction setup. It provides essential metadata about an agent. Clients parse this information to determine if an agent is suitable for a given task, how to structure requests, and how to communicate securely. Key information includes identity, service endpoint (URL), A2A capabilities, authentication requirements, and a list of skills.</p>

## Messages and Parts

<p>A message represents a single turn of communication between a client and an agent. It includes a role ("user" or "agent") and a unique <code>messageId</code>. It contains one or more Part objects, which are granular containers for the actual content. This design allows A2A to be modality independent.</p> <p>The <code>Part</code> object is a flexible container that can hold different types of content using a <code>oneof</code> field structure. A Part must contain exactly one of the following content fields:</p> <ul> <li><code>text</code>: A string containing plain textual content.</li> <li><code>raw</code>: A byte array containing binary file data (inline).</li> <li><code>url</code>: A string URI referencing external file content.</li> <li><code>data</code>: A structured JSON value (e.g., object, array) for machine-readable data.</li> </ul> <p>Additionally, every <code>Part</code> can include:</p> <ul> <li><code>mediaType</code>: The MIME type of the content (e.g., <code>"text/plain"</code>, <code>"image/png"</code>, <code>"application/json"</code>).</li> <li><code>filename</code>: An optional name for the file or content.</li> <li><code>metadata</code>: A key-value map for additional context.</li> </ul>

## Artifacts

<p>An artifact represents a tangible output or a concrete result generated by a remote agent during task processing. Unlike general messages, artifacts are the actual deliverables. An artifact has a unique <code>artifactId</code>, a human-readable name, and consists of one or more part objects. Artifacts are closely tied to the task lifecycle and can be streamed incrementally to the client.</p>

## Agent Response: Task or Message

<p>The agent response can be a new <code>Task</code> (when the agent needs to perform a long-running operation) or a <code>Message</code> (when the agent can respond immediately).</p> <p>For more details, see Life of a Task.</p>

## Other Important Concepts

<ul> <li>Context (<code>contextId</code>): A server-generated identifier that can be used to logically group multiple related <code>Task</code> objects, providing context across a series of interactions.</li> <li>Transport and Format: A2A communication occurs over HTTP(S). JSON-RPC 2.0 is used as the payload format for all requests and responses.</li> <li>Authentication &amp; Authorization: A2A relies on standard web security practices. Authentication requirements are declared in the Agent Card, and credentials (e.g., OAuth tokens, API keys) are typically passed through HTTP headers, separate from the A2A protocol messages themselves. For more information, see Enterprise-Ready Features.</li> <li>Agent Discovery: The process by which clients find Agent Cards to learn about available A2A Servers and their capabilities. For more information, see Agent Discovery.</li> <li>Extensions: A2A allows agents to declare custom protocol extensions as part of their AgentCard. For more information, see Extensions.</li> </ul>

---

# Page: /topics/life-of-a-task/

## Life of a Task

<p>In the Agent2Agent (A2A) Protocol, interactions can range from simple, stateless exchanges to complex, long-running processes. When an agent receives a message from a client, it can respond in one of two fundamental ways:</p> <ul> <li>Respond with a Stateless <code>Message</code>: This type of response is     typically used for immediate, self-contained interactions that conclude     without requiring further state management.</li> <li>Initiate a Stateful <code>Task</code>: If the response is a <code>Task</code>, the agent will     process it through a defined lifecycle, communicating progress and requiring     input as needed, until it reaches an interrupted state (e.g.,     <code>input-required</code>, <code>auth-required</code>) or a terminal state (e.g., <code>completed</code>,     <code>canceled</code>, <code>rejected</code>, <code>failed</code>).</li> </ul>

## Group Related Interactions

<p>A <code>contextId</code> is a crucial identifier that logically groups multiple <code>Task</code> objects and independent <code>Message</code> objects, providing continuity across a series of interactions.</p> <ul> <li>When a client sends a message for the first time, the agent responds     with a new <code>contextId</code>. If a task is initiated, it will also have a <code>taskId</code>.</li> <li>Clients can send subsequent messages and include the same <code>contextId</code> to     indicate that they are continuing their previous interaction within the same     context.</li> <li>Clients optionally attach the <code>taskId</code> to a subsequent message to     indicate that it continues that specific task.</li> </ul> <p>The <code>contextId</code> enables collaboration towards a common goal or a shared contextual session across multiple, potentially concurrent tasks. Internally, an A2A agent (especially one using an LLM) uses the <code>contextId</code> to manage its internal conversational state or its LLM context.</p>

## Agent Response: Message or Task

<p>The choice between responding with a <code>Message</code> or a <code>Task</code> depends on the nature of the interaction and the agent's capabilities:</p> <ul> <li>Messages for Trivial Interactions: <code>Message</code> objects are suitable for     transactional interactions that don't require long-running     processing or complex state management. An agent might use messages to     negotiate the acceptance or scope of a task before committing to a <code>Task</code>     object.</li> <li>Tasks for Stateful Interactions: Once an agent maps the intent of an     incoming message to a supported capability that requires substantial,     trackable work over an extended period, the agent responds with a <code>Task</code>     object.</li> </ul> <p>Conceptually, agents operate at different levels of complexity:</p> <ul> <li>Message-only Agents: Always respond with <code>Message</code> objects. They     typically don't manage complex state or long-running executions, and use     <code>contextId</code> to tie messages together. These agents might directly wrap LLM     invocations and simple tools.</li> <li>Task-generating Agents: Always respond with <code>Task</code> objects, even for     responses, which are then modeled as completed tasks. Once a task is     created, the agent will only return <code>Task</code> objects in response to messages     sent, and once a task is complete, no more messages can be sent. This     approach avoids deciding between <code>Task</code> versus <code>Message</code>, but creates completed task objects     for even simple interactions.</li> <li>Hybrid Agents: Generate both <code>Message</code> and <code>Task</code> objects. These agents     use messages to negotiate agent capability and the scope of work for a task,     then send a <code>Task</code> object to track execution and manage states like     <code>input-required</code> or error handling. Once a task is created, the agent will     only return <code>Task</code> objects in response to messages sent, and once a task is     complete, no more messages can be sent. A hybrid agent uses messages to     negotiate the scope of a task, and then generate a task to track its     execution.     For more information about hybrid agents, see A2A protocol: Demystifying Tasks vs Messages.</li> </ul>

## Task Refinements

<p>Clients often need to send new requests based on task results or refine the outputs of previous tasks. This is modeled by starting another interaction using the same <code>contextId</code> as the original task. Clients further hint the agent by providing references to the original task using <code>referenceTaskIds</code> in the <code>Message</code> object. The agent then responds with either a new <code>Task</code> or a <code>Message</code>.</p>

## Task Immutability

<p>Once a task reaches a terminal state (completed, canceled, rejected, or failed), it cannot restart. Any subsequent interaction related to that task, such as a refinement, must initiate a new task within the same <code>contextId</code>. This principle offers several benefits:</p> <ul> <li>Task Immutability. Clients reliably reference tasks and their     associated state, artifacts, and messages, providing a clean mapping of     inputs to outputs. This is valuable for orchestration and traceability.</li> <li>Clear Unit of Work. Every new request, refinement, or follow-up becomes     a distinct task. This simplifies bookkeeping, allows for granular tracking     of an agent's work, and enables tracing each artifact to a specific unit of     work.</li> <li>Easier Implementation. This removes ambiguity for agent developers     regarding whether to create a new task or restart an existing one.</li> </ul>

## Parallel Follow-ups

<p>A2A supports parallel work by enabling agents to create distinct, parallel tasks for each follow-up message sent within the same <code>contextId</code>. This allows clients to track individual tasks and create new dependent tasks as soon as a prerequisite task is complete.</p> <p>For example:</p> <ul> <li>Task 1: Book a flight to Helsinki.</li> <li>Task 2: Based on Task 1, book a hotel.</li> <li>Task 3: Based on Task 1, book a snowmobile activity.</li> <li>Task 4: Based on Task 2, add a spa reservation to the hotel booking.</li> </ul>

## Referencing Previous Artifacts

<p>The serving agent infers the relevant artifact from a referenced task or from the <code>contextId</code>. As the domain expert, the serving agent is best suited to resolve ambiguity or identify missing information. If there is ambiguity, the agent asks the client for clarification by returning an <code>input-required</code> state. The client then specifies the artifact in its response, optionally populating artifact references (<code>artifactId</code>, <code>taskId</code>) in <code>Part</code> metadata.</p>

## Tracking Artifact Mutation

<p>Follow-up or refinement tasks often lead to the creation of new artifacts based on older ones. Tracking these mutations is important to ensure that only the most recent version of an artifact is used in subsequent interactions. This could be conceptualized as a version history, where each new artifact is linked to its predecessor.</p> <p>However, the client is in the best position to manage this artifact linkage. The client determines what constitutes an acceptable result and has the ability to accept or reject new versions. Therefore, the serving agent shouldn't be responsible for tracking artifact mutations, and this linkage is not part of the A2A protocol specification. Clients should maintain this version history on their end and present the latest acceptable version to the user.</p> <p>To facilitate client-side tracking, serving agents should use a consistent <code>artifact-name</code> when generating a refined version of an existing artifact.</p> <p>When initiating follow-up or refinement tasks, the client should explicitly reference the specific artifact they intend to refine, ideally the "latest" version from their perspective. If the artifact reference is not provided, the serving agent can:</p> <ul> <li>Attempt to infer the intended artifact based on the current <code>contextId</code>.</li> <li>If there is ambiguity or insufficient context, the agent should respond with an <code>input-required</code> task state to request clarification from the client.</li> </ul>

## Example Follow-up Scenario

<p>The following example illustrates a typical task flow with a follow-up:</p> <ol> <li> <p>Client sends a message to the agent:</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "text": "Generate an image of a sailboat on the ocean."
        }
      ],
      "messageId": "msg-user-001"
    }
  }
}
</code></pre> </li> <li> <p>Agent responds with a boat image (completed task):</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "task": {
      "id": "task-boat-gen-123",
      "contextId": "ctx-conversation-abc",
      "status": {
        "state": "TASK_STATE_COMPLETED"
      },
      "artifacts": [
        {
          "artifactId": "artifact-boat-v1-xyz",
          "name": "sailboat_image.png",
          "description": "A generated image of a sailboat on the ocean.",
          "parts": [
            {
              "filename": "sailboat_image.png",
              "mediaType": "image/png",
              "raw": "base64_encoded_png_data_of_a_sailboat"
            }
          ]
        }
      ]
    }
  }
}
</code></pre> </li> <li> <p>Client asks to color the boat red. This refinement request refers to the     previous <code>taskId</code> and uses the same <code>contextId</code>.</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": "req-002",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-user-002",
      "contextId": "ctx-conversation-abc",
      "referenceTaskIds": [
        "task-boat-gen-123"
      ],
      "parts": [
        {
          "text": "Please modify the sailboat to be red."
        }
      ]
    }
  }
}
</code></pre> </li> <li> <p>Agent responds with a new image artifact (new task, same context, same     artifact name): The agent creates a new task within the same <code>contextId</code>. The     new boat image artifact retains the same name but has a new <code>artifactId</code>.</p> <pre><code>{
  "jsonrpc": "2.0",
  "id": "req-002",
  "result": {
    "task": {
      "id": "task-boat-color-456",
      "contextId": "ctx-conversation-abc",
      "status": {
        "state": "TASK_STATE_COMPLETED"
      },
      "artifacts": [
        {
          "artifactId": "artifact-boat-v2-red-pqr",
          "name": "sailboat_image.png",
          "description": "A generated image of a red sailboat on the ocean.",
          "parts": [
            {
              "filename": "sailboat_image.png",
              "mediaType": "image/png",
              "raw": "base64_encoded_png_data_of_a_RED_sailboat"
            }
          ]
        }
      ]
    }
  }
}
</code></pre> </li> </ol>

---

# Page: /topics/streaming-and-async/

## Streaming and Asynchronous Operations for Long-Running Tasks

<p>The Agent2Agent (A2A) protocol is explicitly designed to handle tasks that might not complete immediately. Many AI-driven operations are often long-running, involve multiple steps, produce incremental results, or require human intervention. A2A provides mechanisms for managing such asynchronous interactions, ensuring that clients receive updates effectively, whether they remain continuously connected or operate in a more disconnected fashion.</p>

## Streaming with Server-Sent Events (SSE)

<p>For tasks that produce incremental results (like generating a long document or streaming media) or provide ongoing status updates, A2A supports real-time communication using Server-Sent Events (SSE). This approach is ideal when the client is able to maintain an active HTTP connection with the A2A Server.</p> <p>The following key features detail how SSE streaming is implemented and managed within the A2A protocol:</p> <ul> <li> <p>Server Capability: The A2A Server must indicate its support for streaming by setting <code>capabilities.streaming: true</code> in its Agent Card.</p> </li> <li> <p>Initiating a Stream: The client uses the <code>SendStreamingMessage</code> RPC method to send an initial message (for example, a prompt or command) and simultaneously subscribe to updates for that task.</p> </li> <li> <p>Server Response and Connection: If the subscription is successful, the server responds with an HTTP 200 OK status and a <code>Content-Type: text/event-stream</code>. This HTTP connection remains open for the server to push events to the client.</p> </li> <li> <p>Event Structure and Types: The server sends events over this stream. Each event's <code>data</code> field contains a JSON-RPC 2.0 Response object, typically a <code>SendStreamingMessageResponse</code>. The <code>result</code> field of the <code>SendStreamingMessageResponse</code> contains:</p> <ul> <li><code>Task</code>: Represents the current state of the work.</li> <li><code>TaskStatusUpdateEvent</code>: Communicates changes in the task's lifecycle state (for example, from <code>working</code> to <code>input-required</code> or <code>completed</code>). It also provides intermediate messages from the agent.</li> <li><code>TaskArtifactUpdateEvent</code>: Delivers new or updated Artifacts generated by the task. This is used to stream large files or data structures in chunks, with fields like <code>append</code> and <code>lastChunk</code> to help reassemble.</li> </ul> </li> <li> <p>Stream Termination: When a task reaches a terminal or interrupted state (e.g., <code>COMPLETED</code>, <code>FAILED</code>, <code>CANCELED</code>, <code>REJECTED</code>, or <code>INPUT_REQUIRED</code>), the server closes the stream and sends no further updates.</p> </li> <li> <p>Resubscription: If a client's SSE connection breaks prematurely while a task is still active, the client is able to attempt to reconnect to the stream using the <code>SubscribeToTask</code> RPC method.</p> </li> </ul>

## When to Use Streaming

<p>Streaming with SSE is best suited for:</p> <ul> <li>Real-time progress monitoring of long-running tasks.</li> <li>Receiving large results (artifacts) incrementally.</li> <li>Interactive, conversational exchanges where immediate feedback or partial responses are beneficial.</li> <li>Applications requiring low-latency updates from the agent.</li> </ul>

## Protocol Specification References

<p>Refer to the Protocol Specification for detailed structures:</p> <ul> <li><code>SendStreamingMessage</code></li> <li><code>SubscribeToTask</code></li> </ul>

## Push Notifications for Disconnected Scenarios

<p>For very long-running tasks (for example, lasting minutes, hours, or even days) or when clients are unable to or prefer not to maintain persistent connections (like mobile clients or serverless functions), A2A supports asynchronous updates using push notifications. This allows the A2A Server to actively notify a client-provided webhook when a significant task update occurs.</p> <p>The following key features detail how push notifications are implemented and managed within the A2A protocol:</p> <ul> <li>Server Capability: The A2A Server must indicate its support for this feature by setting <code>capabilities.pushNotifications: true</code> in its Agent Card.</li> <li>Configuration: The client provides a <code>PushNotificationConfig</code> to the server. This configuration is supplied:<ul> <li>Within the initial <code>SendMessage</code> or <code>SendStreamingMessage</code> request, or</li> <li>Separately, using the <code>CreateTaskPushNotificationConfig</code> RPC method for an existing task. The <code>PushNotificationConfig</code> includes a <code>url</code> (the HTTPS webhook URL), an optional <code>token</code> (for client-side validation), and optional <code>authentication</code> details (for the A2A Server to authenticate to the webhook).</li> </ul> </li> <li>Notification Trigger: The A2A Server decides when to send a push notification, typically when a task reaches a significant state change (for example, terminal state, <code>input-required</code>, or <code>auth-required</code>).</li> <li>Notification Payload: The A2A protocol defines the HTTP body payload as a <code>StreamResponse</code> object, matching the format used in streaming operations. The payload contains one of: <code>task</code>, <code>message</code>, <code>statusUpdate</code>, or <code>artifactUpdate</code>. See Push Notification Payload for detailed structure.</li> <li>Client Action: Upon receiving a push notification (and successfully verifying its authenticity), the client typically uses the <code>GetTask</code> RPC method with the <code>taskId</code> from the notification to retrieve the complete, updated <code>Task</code> object, including any new artifacts.</li> </ul>

## When to Use Push Notifications

<p>Push notifications are ideal for:</p> <ul> <li>Very long-running tasks that can take minutes, hours, or days to complete.</li> <li>Clients that cannot or prefer not to maintain persistent connections, such as mobile applications or serverless functions.</li> <li>Scenarios where clients only need to be notified of significant state changes rather than continuous updates.</li> </ul>

## Protocol Specification References

<p>Refer to the Protocol Specification for detailed structures:</p> <ul> <li><code>CreateTaskPushNotificationConfig</code></li> <li><code>GetTask</code></li> </ul>

## Client-Side Push Notification Service

<p>The <code>url</code> specified in <code>PushNotificationConfig.url</code> points to a client-side Push Notification Service. This service is responsible for receiving the HTTP POST notification from the A2A Server. Its responsibilities include authenticating the incoming notification, validating its relevance, and relaying the notification or its content to the appropriate client application logic or system.</p>

## Security Considerations for Push Notifications

<p>Security is paramount for push notifications due to their asynchronous and server-initiated outbound nature. Both the A2A Server (sending the notification) and the client's webhook receiver have critical responsibilities.</p>

## A2A Server Security (when sending notifications to client webhook)

<ul> <li>Webhook URL Validation: Servers SHOULD NOT blindly trust and send POST requests to any URL provided by a client. Malicious clients could provide URLs pointing to internal services or unrelated third-party systems, leading to Server-Side Request Forgery (SSRF) attacks or acting as Distributed Denial of Service (DDoS) amplifiers.<ul> <li>Mitigation strategies: Allowlisting of trusted domains, ownership verification (for example, challenge-response mechanisms), and network controls (e.g., egress firewalls).</li> </ul> </li> <li>Authenticating to the Client's Webhook: The A2A Server MUST authenticate itself to the client's webhook URL according to the scheme specified in <code>PushNotificationConfig.authentication</code>. Common schemes include Bearer Tokens (OAuth 2.0), API keys, HMAC signatures, or mutual TLS (mTLS).</li> </ul>

## Client Webhook Receiver Security (when receiving notifications from A2A server)

<ul> <li>Authenticating the A2A Server: The webhook endpoint MUST rigorously verify the authenticity of incoming notification requests to ensure they originate from the legitimate A2A Server and not an imposter.<ul> <li>Verification methods: Verify signatures/tokens (for example, JWT signatures against the A2A Server's trusted public keys, HMAC signatures, or API key validation). Also, validate the <code>PushNotificationConfig.token</code> if provided.</li> </ul> </li> <li>Preventing Replay Attacks:<ul> <li>Timestamps: Notifications SHOULD include a timestamp. The webhook SHOULD reject notifications that are too old.</li> <li>Nonces/unique IDs: For critical notifications, consider using unique, single-use identifiers (for example, JWT's <code>jti</code> claim or event IDs) to prevent processing duplicate notifications.</li> </ul> </li> <li>Secure Key Management and Rotation: Implement secure key management practices, including regular key rotation, especially for cryptographic keys. Protocols like JWKS (JSON Web Key Set) facilitate key rotation for asymmetric keys.</li> </ul>

## Example Asymmetric Key Flow (JWT + JWKS)

<ol> <li>Client creates a <code>PushNotificationConfig</code> specifying <code>authentication.scheme: "Bearer"</code> and possibly an expected <code>issuer</code> or <code>audience</code> for the JWT.</li> <li>A2A Server, when sending a notification:<ul> <li>Generates a JWT, signing it with its private key. The JWT includes claims like <code>iss</code> (issuer), <code>aud</code> (audience), <code>iat</code> (issued at), <code>exp</code> (expires), <code>jti</code> (JWT ID), and <code>taskId</code>.</li> <li>The JWT header indicates the signing algorithm and key ID (<code>kid</code>).</li> <li>The A2A Server makes its public keys available through a JWKS endpoint.</li> </ul> </li> <li>Client Webhook, upon receiving the notification:<ul> <li>Extracts the JWT from the Authorization header.</li> <li>Inspects the <code>kid</code> (key ID) in the JWT header.</li> <li>Fetches the corresponding public key from the A2A Server's JWKS endpoint (caching keys is recommended).</li> <li>Verifies the JWT signature using the public key.</li> <li>Validates claims (<code>iss</code>, <code>aud</code>, <code>iat</code>, <code>exp</code>, <code>jti</code>).</li> <li>Checks the <code>PushNotificationConfig.token</code> if provided.</li> </ul> </li> </ol> <p>This comprehensive, layered approach to security for push notifications helps ensure that messages are authentic, integral, and timely, protecting both the sending A2A Server and the receiving client webhook infrastructure.</p>

---

# Page: /topics/what-is-a2a/

## What is A2A?

<p>The A2A protocol is an open standard that enables seamless communication and collaboration between AI agents. It provides a common language for agents built using diverse frameworks and by different vendors, fostering interoperability and breaking down silos. Agents are autonomous problem-solvers that act independently within their environment. A2A allows agents from different developers, built on different frameworks, and owned by different organizations to unite and work together.</p>

## Why Use the A2A Protocol

<p>A2A addresses key challenges in AI agent collaboration. It provides a standardized approach for agents to interact. This section explains the problems A2A solves and the benefits it offers.</p>

## Problems that A2A Solves

<p>Consider a user request for an AI assistant to plan an international trip. This task involves orchestrating multiple specialized agents, such as:</p> <ul> <li>A flight booking agent</li> <li>A hotel reservation agent</li> <li>An agent for local tour recommendations</li> <li>A currency conversion agent</li> </ul> <p>Without A2A, integrating these diverse agents presents several challenges:</p> <ul> <li>Agent Exposure: Developers often wrap agents as tools to expose them to     other agents, similar to how tools are exposed in a Multi-agent Control     Platform (Model Context Protocol). However, this approach is inefficient because agents are     designed to negotiate directly. Wrapping agents as tools limits their capabilities.     A2A allows agents to be exposed as they are, without requiring this wrapping.</li> <li>Custom Integrations: Each interaction requires custom, point-to-point     solutions, creating significant engineering overhead.</li> <li>Slow Innovation: Bespoke development for each new integration slows     innovation.</li> <li>Scalability Issues: Systems become difficult to scale and maintain as     the number of agents and interactions grows.</li> <li>Interoperability: This approach limits interoperability,     preventing the organic formation of complex AI ecosystems.</li> <li>Security Gaps: Ad hoc communication often lacks consistent security     measures.</li> </ul> <p>The A2A protocol addresses these challenges by establishing interoperability for AI agents to interact reliably and securely.</p>

## A2A Example Scenario

<p>This section provides an example scenario to illustrate the benefits of using an A2A (Agent2Agent) protocol for complex interactions between AI agents.</p>

## A User's Complex Request

<p>A user interacts with an AI assistant, giving it a complex prompt like "Plan an international trip."</p> <pre><code>graph LR
    User --&gt; Prompt --&gt; AI_Assistant[AI Assistant]</code></pre>

## The Need for Collaboration

<p>The AI assistant receives the prompt and realizes it needs to call upon multiple specialized agents to fulfill the request. These agents include a Flight Booking Agent, a Hotel Reservation Agent, a Currency Conversion Agent, and a Local Tours Agent.</p> <pre><code>graph LR
    subgraph "Specialized Agents"
        FBA[✈️ Flight Booking Agent]
        HRA[🏨 Hotel Reservation Agent]
        CCA[💱 Currency Conversion Agent]
        LTA[🚌 Local Tours Agent]
    end

    AI_Assistant[🤖 AI Assistant] --&gt; FBA
    AI_Assistant --&gt; HRA
    AI_Assistant --&gt; CCA
    AI_Assistant --&gt; LTA</code></pre>

## The Interoperability Challenge

<p>The core problem: The agents are unable to work together because each has its own bespoke development and deployment.</p> <p>The consequence of a lack of a standardized protocol is that these agents cannot collaborate with each other let alone discover what they can do. The individual agents (Flight, Hotel, Currency, and Tours) are isolated.</p>

## The "With A2A" Solution

<p>The A2A Protocol provides standard methods and data structures for agents to communicate with one another, regardless of their underlying implementation, so the same agents can be used as an interconnected system, communicating seamlessly through the standardized protocol.</p> <p>The AI assistant, now acting as an orchestrator, receives the cohesive information from all the A2A-enabled agents. It then presents a single, complete travel plan as a seamless response to the user's initial prompt.</p> <p></p>

## Core Benefits of A2A

<p>Implementing the A2A protocol offers significant advantages across the AI ecosystem:</p> <ul> <li>Secure collaboration: Without a standard, it's difficult to ensure     secure communication between agents. A2A uses HTTPS for secure communication     and maintains opaque operations, so agents can't see the inner workings of     other agents during collaboration.</li> <li>Interoperability: A2A breaks down silos between different AI     agent ecosystems, enabling agents from various vendors and frameworks to work     together seamlessly.</li> <li>Agent autonomy: A2A allows agents to retain their individual capabilities     and act as autonomous entities while collaborating with other agents.</li> <li>Reduced integration complexity: The protocol standardizes agent     communication, enabling teams to focus on the unique value their agents     provide.</li> <li>Support for LRO: The protocol supports long-running operations (LRO) and     streaming with Server-Sent Events (SSE) and asynchronous execution.</li> </ul>

## Key Design Principles of A2A

<p>A2A development follows principles that prioritize broad adoption, enterprise-grade capabilities, and future-proofing.</p> <ul> <li>Simplicity: A2A leverages existing standards like HTTP, JSON-RPC, and     Server-Sent Events (SSE). This avoids reinventing core technologies and     accelerates developer adoption.</li> <li>Enterprise Readiness: A2A addresses critical enterprise needs. It aligns     with standard web practices for robust authentication, authorization,     security, privacy, tracing, and monitoring.</li> <li>Asynchronous: A2A natively supports long-running tasks. It handles     scenarios where agents or users might not remain continuously connected. It     uses mechanisms like streaming and push notifications.</li> <li>Modality Independent: The protocol allows agents to communicate using a     wide variety of content types. This enables rich and flexible interactions     beyond plain text.</li> <li>Opaque Execution: Agents collaborate effectively without exposing their     internal logic, memory, or proprietary tools. Interactions rely on declared     capabilities and exchanged context. This preserves intellectual property and     enhances security.</li> </ul>

## Understanding the Agent Stack: A2A, MCP, Agent Frameworks and Models

<p>A2A is situated within a broader agent stack, which includes:</p> <ul> <li>A2A: Standardizes communication among agents deployed in different organizations and developed using diverse frameworks.</li> <li>MCP: Connects models to data and external resources.</li> <li>Frameworks (like ADK): Provide toolkits for constructing agents.</li> <li>Models: Fundamental to an agent's reasoning, these can be any Large Language Model (LLM).</li> </ul> <p></p>

## A2A and MCP

<p>In the broader ecosystem of AI communication, you might be familiar with protocols designed to facilitate interactions between agents, models, and tools. Notably, the Model Context Protocol (MCP) is an emerging standard focused on connecting Large Language Models (LLMs) with data and external resources.</p> <p>The Agent2Agent (A2A) protocol is designed to standardize communication between AI agents, particularly those deployed in external systems. A2A is positioned to complement MCP, addressing a distinct yet related aspect of agent interaction.</p> <ul> <li>MCP's Focus: Reducing the complexity involved in connecting agents with tools and data. Tools are typically stateless and perform specific, predefined functions (e.g., a calculator, a database query).</li> <li>A2A's Focus: Enabling agents to collaborate within their native modalities, allowing them to communicate as agents (or as users) rather than being constrained to tool-like interactions. This enables complex, multi-turn interactions where agents reason, plan, and delegate tasks to other agents. For example, this facilitates multi-turn interactions, such as those involving negotiation or clarification when placing an order.</li> </ul> <p></p> <p>The practice of encapsulating an agent as a simple tool is fundamentally limiting, as it fails to capture the agent's full capabilities. This critical distinction is explored in the post, Why Agents Are Not Tools.</p> <p>For a more in-depth comparison, refer to the A2A and MCP Comparison document.</p>

## A2A and ADK

<p>The Agent Development Kit (ADK) is an open-source agent development toolkit developed by Google. A2A is a communication protocol for agents that enables inter-agent communication, regardless of the framework used for their construction (e.g., ADK, LangGraph, or Crew AI). ADK is a flexible and modular framework for developing and deploying AI agents. While optimized for Gemini AI and the Google ecosystem, ADK is model-agnostic, deployment-agnostic, and built for compatibility with other frameworks.</p>

## A2A Request Lifecycle

<p>The A2A request lifecycle is a sequence that details the four main steps a request follows: agent discovery, authentication, <code>sendMessage</code> API, and <code>sendMessageStream</code> API. The following diagram provides a deeper look into the operational flow, illustrating the interactions between the client, A2A server, and auth server.</p> <pre><code>sequenceDiagram
    participant Client
    participant A2A Server
    participant Auth Server

    rect rgb(240, 240, 240)
    Note over Client, A2A Server: 1. Agent Discovery
    Client-&gt;&gt;A2A Server: GET agent card eg: (/.well-known/agent-card)
    A2A Server--&gt;&gt;Client: Returns Agent Card
    end

    rect rgb(240, 240, 240)
    Note over Client, Auth Server: 2. Authentication
    Client-&gt;&gt;Client: Parse Agent Card for securitySchemes
    alt securityScheme is "openIdConnect"
        Client-&gt;&gt;Auth Server: Request token based on "authorizationUrl" and "tokenUrl".
        Auth Server--&gt;&gt;Client: Returns JWT
    end
    end

    rect rgb(240, 240, 240)
    Note over Client, A2A Server: 3. sendMessage API
    Client-&gt;&gt;Client: Parse Agent Card for "url" param to send API requests to.
    Client-&gt;&gt;A2A Server: POST /sendMessage (with JWT)
    A2A Server-&gt;&gt;A2A Server: Process message and create task
    A2A Server--&gt;&gt;Client: Returns Task Response
    end

    rect rgb(240, 240, 240)
    Note over Client, A2A Server: 4. sendMessageStream API
    Client-&gt;&gt;A2A Server: POST /sendMessageStream (with JWT)
    A2A Server--&gt;&gt;Client: Stream: Task (Submitted)
    A2A Server--&gt;&gt;Client: Stream: TaskStatusUpdateEvent (Working)
    A2A Server--&gt;&gt;Client: Stream: TaskArtifactUpdateEvent (artifact A)
    A2A Server--&gt;&gt;Client: Stream: TaskArtifactUpdateEvent (artifact B)
    A2A Server--&gt;&gt;Client: Stream: TaskStatusUpdateEvent (Completed)
    end</code></pre>

## What's Next

<p>Learn about the Key Concepts that form the foundation of the A2A protocol.</p>

---

# Page: /tutorials/

## Python

Tutorial Description Difficulty A2A and Python Quickstart Learn to build a simple Python-based "echo" A2A server and client. Easy ADK facts Build and test a simple Personal Assistant agent using the Agent Development Kit (ADK) that can provide interesting facts. Easy ADK agent on Cloud Run Deploy, manage, and observe an ADK-based agent as a scalable, serverless service on Google Cloud Run. Easy Multi-agent collaboration using A2A Learn how to set up an orchestrator (host agent) that routes and manages requests among several specialized A2A-compatible agents. Easy Airbnb and weather multi-agent Build a complex multi-agent system where agents collaborate using A2A to plan a trip, finding both Airbnb accommodations and weather information. Medium A2A Client-Server example using remote ADK agent Learn how a local A2A client agent discovers and consumes the capabilities of a separate, remote ADK-based agent (for example, a prime number checker). Easy Colab Notebook Use Colab Notebook to deploy A2A agents to Cloud Run from your browser, and then evaluate their performance with Vertex AI. Easy

## Java

Tutorial Description Difficulty Weather Agent Build a weather information agent using an MCP server.To make use of this agent in a multi-language, multi-agent system, check out the weather_and_airbnb_planner sample. Easy Content Writer Agent Build a content writer agent that generates engaging pieces of content from outlines.To make use of this agent in a content creation multi-language, multi-agent system, check out the content_creation sample. Easy Content Editor Agent Build a content editor agent that proof-reads and polishes content.To make use of this agent in a content creation multi-language, multi-agent system, check out the content_creation sample. Easy Dice Agent (Multi-Transport) Build a multi-transport agent that rolls dice and checks for prime numbers. Medium Magic 8 Ball Agent (Security) Build a Magic 8 Ball agent to learn how to secure A2A servers with Keycloak using bearer token authentication and configure an A2A client to obtain and pass the required token. Medium

## JavaScript

Tutorial Description Movie research agent using JavaScript Build an A2A agent with Node.js that uses the TMDB (The Movie Database) API to handle movie searches and queries.

## C#/.NET

Tutorial Description All .NET samples Repository of foundational samples showing how to build A2A clients and servers, including an Echo Agent, using the C#/.NET SDK.

---

# Page: /tutorials/python/1-introduction/

## Python Quickstart Tutorial: Building an A2A Agent

<p>Welcome to the Agent2Agent (A2A) Python Quickstart Tutorial!</p> <p>In this tutorial, you will explore a simple "echo" A2A server using the Python SDK. This will introduce you to the fundamental concepts and components of an A2A server. You will then look at a more advanced example that integrates a Large Language Model (LLM).</p> <p>This hands-on guide will help you understand:</p> <ul> <li>The basic concepts behind the A2A protocol.</li> <li>How to set up a Python environment for A2A development using the SDK.</li> <li>How Agent Skills and Agent Cards describe an agent.</li> <li>How an A2A server handles tasks.</li> <li>How to interact with an A2A server using a client.</li> <li>How streaming capabilities and multi-turn interactions work.</li> <li>How an LLM can be integrated into an A2A agent.</li> </ul> <p>By the end of this tutorial, you will have a functional understanding of A2A agents and a solid foundation for building or integrating A2A-compliant applications.</p>

## Tutorial Sections

<p>The tutorial is broken down into the following steps:</p> <ol> <li>Introduction (This Page)</li> <li>Setup: Prepare your Python environment and the A2A SDK.</li> <li>Agent Skills &amp; Agent Card: Define what your agent can do and how it describes itself.</li> <li>The Agent Executor: Understand how the agent logic is implemented.</li> <li>Starting the Server: Run the Helloworld A2A server.</li> <li>Interacting with the Server: Send requests to your agent.</li> <li>Streaming &amp; Multi-Turn Interactions: Explore advanced capabilities with the LangGraph example.</li> <li>Next Steps: Explore further possibilities with A2A.</li> </ol> <p>Let's get started!</p>

---

# Page: /tutorials/python/2-setup/

## Prerequisites

<ul> <li>Python 3.10 or higher.</li> <li>Access to a terminal or command prompt.</li> <li>Git, for cloning the repository.</li> <li>A code editor (e.g., Visual Studio Code) is recommended.</li> </ul>

## Clone the Repository

<p>If you haven't already, clone the A2A Samples repository:</p> <pre><code>git clone https://github.com/a2aproject/a2a-samples.git -b main --depth 1
cd a2a-samples
</code></pre>

## Python Environment &amp; SDK Installation

<p>We recommend using a virtual environment for Python projects. The A2A Python SDK uses <code>uv</code> for dependency management, but you can use <code>pip</code> with <code>venv</code> as well.</p> <ol> <li> <p>Create and activate a virtual environment:</p> <p>Using <code>venv</code> (standard library):</p> Mac/LinuxWindows <pre><code>python -m venv .venv
source .venv/bin/activate
</code></pre> <pre><code>python -m venv .venv
.venv\Scripts\activate
</code></pre> </li> <li> <p>Install needed Python dependencies along with the A2A SDK and its dependencies:</p> <pre><code>pip install -r samples/python/requirements.txt
</code></pre> </li> </ol>

## Verify Installation

<p>After installation, you should be able to import the <code>a2a</code> package in a Python interpreter:</p> <pre><code>python -c "import a2a; print('A2A SDK imported successfully')"
</code></pre> <p>If this command runs without error and prints the success message, your environment is set up correctly.</p>

---

# Page: /tutorials/python/3-agent-skills-and-card/

## 3. Agent Skills &amp; Agent Card

<p>Before an A2A agent can do anything, it needs to define what it can do (its skills) and how other agents or clients can find out about these capabilities (its Agent Card).</p> <p>We'll use the <code>helloworld</code> example located in <code>a2a-samples/samples/python/agents/helloworld/</code>.</p>

## Agent Skills

<p>An Agent Skill describes a specific capability or function the agent can perform. It's a building block that tells clients what kinds of tasks the agent is good for.</p> <p>Key attributes of an <code>AgentSkill</code> (defined in <code>a2a.types</code>):</p> <ul> <li><code>id</code>: A unique identifier for the skill.</li> <li><code>name</code>: A human-readable name.</li> <li><code>description</code>: A more detailed explanation of what the skill does.</li> <li><code>tags</code>: Keywords for categorization and discovery.</li> <li><code>examples</code>: Sample prompts or use cases.</li> <li><code>inputModes</code> / <code>outputModes</code>: Supported Media Types for input and output (e.g., "text/plain", "application/json").</li> </ul> <p>In <code>__main__.py</code>, you can see how a skill for the Helloworld agent is defined:</p> <pre><code>skill = AgentSkill(
    id='hello_world',
    name='Returns hello world',
    description='just returns hello world',
    tags=['hello world'],
    examples=['hi', 'hello world'],
)
</code></pre> <p>This skill is very simple: it's named "Returns hello world" and primarily deals with text.</p>

## Agent Card

<p>The Agent Card is a JSON document that an A2A Server makes available, typically at a <code>.well-known/agent-card.json</code> endpoint. It's like a digital business card for the agent.</p> <p>Key attributes of an <code>AgentCard</code> (defined in <code>a2a.types</code>):</p> <ul> <li><code>name</code>, <code>description</code>, <code>version</code>: Basic identity information.</li> <li><code>url</code>: The endpoint where the A2A service can be reached.</li> <li><code>capabilities</code>: Specifies supported A2A features like <code>streaming</code> or <code>pushNotifications</code>.</li> <li><code>defaultInputModes</code> / <code>defaultOutputModes</code>: Default Media Types for the agent.</li> <li><code>skills</code>: A list of <code>AgentSkill</code> objects that the agent offers.</li> </ul> <p>The <code>helloworld</code> example defines its Agent Card like this:</p> <pre><code># This will be the public-facing agent card
public_agent_card = AgentCard(
    name='Hello World Agent',
    description='Just a hello world agent',
    url='http://localhost:9999/',
    version='1.0.0',
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],  # Only the basic skill for the public card
    supports_authenticated_extended_card=True,
)
</code></pre> <p>This card tells us the agent is named "Hello World Agent", runs at <code>http://localhost:9999/</code>, supports text interactions, and has the <code>hello_world</code> skill. It also indicates public authentication, meaning no specific credentials are required.</p> <p>Understanding the Agent Card is crucial because it's how a client discovers an agent and learns how to interact with it.</p>

---

# Page: /tutorials/python/4-agent-executor/

## 4. The Agent Executor

<p>The core logic of how an A2A agent processes requests and generates responses/events is handled by an Agent Executor. The A2A Python SDK provides an abstract base class <code>a2a.server.agent_execution.AgentExecutor</code> that you implement.</p>

## <code>AgentExecutor</code> Interface

<p>The <code>AgentExecutor</code> class defines two primary methods:</p> <ul> <li><code>async def execute(self, context: RequestContext, event_queue: EventQueue)</code>: Handles incoming requests that expect a response or a stream of events. It processes the user's input (available via <code>context</code>) and uses the <code>event_queue</code> to send back <code>Message</code>, <code>Task</code>, <code>TaskStatusUpdateEvent</code>, or <code>TaskArtifactUpdateEvent</code> objects.</li> <li><code>async def cancel(self, context: RequestContext, event_queue: EventQueue)</code>: Handles requests to cancel an ongoing task.</li> </ul> <p>The <code>RequestContext</code> provides information about the incoming request, such as the user's message and any existing task details. The <code>EventQueue</code> is used by the executor to send events back to the client.</p>

## Helloworld Agent Executor

<p>Let's look at <code>agent_executor.py</code>. It defines <code>HelloWorldAgentExecutor</code>.</p> <ol> <li> <p>The Agent (<code>HelloWorldAgent</code>):     This is a simple helper class that encapsulates the actual "business logic".</p> <pre><code>class HelloWorldAgent:
    """Hello World Agent."""

    async def invoke(self) -&gt; str:
        return 'Hello World'
</code></pre> <p>It has a simple <code>invoke</code> method that returns the string "Hello World".</p> </li> <li> <p>The Executor (<code>HelloWorldAgentExecutor</code>):     This class implements the <code>AgentExecutor</code> interface.</p> <ul> <li> <p><code>__init__</code>:</p> <pre><code>class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()
</code></pre> <p>It instantiates the <code>HelloWorldAgent</code>.</p> </li> <li> <p><code>execute</code>:</p> <pre><code>async def execute(
    self,
    context: RequestContext,
    event_queue: EventQueue,
) -&gt; None:
    result = await self.agent.invoke()
    await event_queue.enqueue_event(new_agent_text_message(result))
</code></pre> <p>When a <code>message/send</code> or <code>message/stream</code> request comes in (both are handled by <code>execute</code> in this simplified executor):</p> <ol> <li>It calls <code>self.agent.invoke()</code> to get the "Hello World" string.</li> <li>It creates an A2A <code>Message</code> object using the <code>new_agent_text_message</code> utility function.</li> <li>It enqueues this message onto the <code>event_queue</code>. The underlying <code>DefaultRequestHandler</code> will then process this queue to send the response(s) to the client. For a single message like this, it will result in a single response for <code>message/send</code> or a single event for <code>message/stream</code> before the stream closes.</li> </ol> </li> <li> <p><code>cancel</code>:     The Hello World example's <code>cancel</code> method simply raises an exception, indicating that cancellation is not supported for this basic agent.</p> <pre><code>async def cancel(
    self, context: RequestContext, event_queue: EventQueue
) -&gt; None:
    raise Exception('cancel not supported')
</code></pre> </li> </ul> </li> </ol> <p>The <code>AgentExecutor</code> acts as the bridge between the A2A protocol (managed by the request handler and server application) and your agent's specific logic. It receives context about the request and uses an event queue to communicate results or updates back.</p>

---

# Page: /tutorials/python/5-start-server/

## 5. Starting the Server

<p>Now that we have an Agent Card and an Agent Executor, we can set up and start the A2A server.</p> <p>The A2A Python SDK provides an <code>A2AStarletteApplication</code> class that simplifies running an A2A-compliant HTTP server. It uses Starlette for the web framework and is typically run with an ASGI server like Uvicorn.</p>

## Server Setup in Helloworld

<p>Let's look at <code>__main__.py</code> again to see how the server is initialized and started.</p> <pre><code>import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import (
    HelloWorldAgentExecutor,  # type: ignore[import-untyped]
)


if __name__ == '__main__':
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    extended_skill = AgentSkill(
        id='super_hello_world',
        name='Returns a SUPER Hello World',
        description='A more enthusiastic greeting, only for authenticated users.',
        tags=['hello world', 'super', 'extended'],
        examples=['super hi', 'give me a super hello'],
    )

    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )

    # This will be the authenticated extended agent card
    # It includes the additional 'extended_skill'
    specific_extended_agent_card = public_agent_card.model_copy(
        update={
            'name': 'Hello World Agent - Extended Edition',  # Different name for clarity
            'description': 'The full-featured hello world agent for authenticated users.',
            'version': '1.0.1',  # Could even be a different version
            # Capabilities and other fields like url, default_input_modes, default_output_modes,
            # supports_authenticated_extended_card are inherited from public_agent_card unless specified here.
            'skills': [
                skill,
                extended_skill,
            ],  # Both skills for the extended card
        }
    )

    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)
</code></pre> <p>Let's break this down:</p> <ol> <li> <p><code>DefaultRequestHandler</code>:</p> <ul> <li>The SDK provides <code>DefaultRequestHandler</code>. This handler takes your <code>AgentExecutor</code> implementation (here, <code>HelloWorldAgentExecutor</code>) and a <code>TaskStore</code> (here, <code>InMemoryTaskStore</code>).</li> <li>It routes incoming A2A RPC calls to the appropriate methods on your executor (like <code>execute</code> or <code>cancel</code>).</li> <li>The <code>TaskStore</code> is used by the <code>DefaultRequestHandler</code> to manage the lifecycle of tasks, especially for stateful interactions, streaming, and resubscription. Even if your agent executor is simple, the handler needs a task store.</li> </ul> </li> <li> <p><code>A2AStarletteApplication</code>:</p> <ul> <li>The <code>A2AStarletteApplication</code> class is instantiated with the <code>agent_card</code> and the <code>request_handler</code> (referred to as <code>http_handler</code> in its constructor).</li> <li>The <code>agent_card</code> is crucial because the server will expose it at the <code>/.well-known/agent-card.json</code> endpoint (by default).</li> <li>The <code>request_handler</code> is responsible for processing all incoming A2A method calls by interacting with your <code>AgentExecutor</code>.</li> </ul> </li> <li> <p><code>uvicorn.run(server_app_builder.build(), ...)</code>:</p> <ul> <li>The <code>A2AStarletteApplication</code> has a <code>build()</code> method that constructs the actual Starlette application.</li> <li>This application is then run using <code>uvicorn.run()</code>, making your agent accessible over HTTP.</li> <li><code>host='0.0.0.0'</code> makes the server accessible on all network interfaces on your machine.</li> <li><code>port=9999</code> specifies the port to listen on. This matches the <code>url</code> in the <code>AgentCard</code>.</li> </ul> </li> </ol>

## Running the Helloworld Server

<p>Navigate to the <code>a2a-samples</code> directory in your terminal (if you're not already there) and ensure your virtual environment is activated.</p> <p>To run the Helloworld server:</p> <pre><code># from the a2a-samples directory
python samples/python/agents/helloworld/__main__.py
</code></pre> <p>You should see output similar to this, indicating the server is running:</p> <pre><code>INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9999 (Press CTRL+C to quit)
</code></pre> <p>Your A2A Helloworld agent is now live and listening for requests! In the next step, we'll interact with it.</p>

---

# Page: /tutorials/python/6-interact-with-server/

## 6. Interacting with the Server

<p>With the Helloworld A2A server running, let's send some requests to it. The SDK includes a client (<code>A2AClient</code>) that simplifies these interactions.</p>

## The Helloworld Test Client

<p>The <code>test_client.py</code> script demonstrates how to:</p> <ol> <li>Fetch the Agent Card from the server.</li> <li>Create an <code>A2AClient</code> instance.</li> <li>Send both non-streaming (<code>message/send</code>) and streaming (<code>message/stream</code>) requests.</li> </ol> <p>Open a new terminal window, activate your virtual environment, and navigate to the <code>a2a-samples</code> directory.</p> <p>Activate virtual environment (Be sure to do this in the same directory where you created the virtual environment):</p> Mac/LinuxWindows <pre><code>source .venv/bin/activate
</code></pre> <pre><code>.venv\Scripts\activate
</code></pre> <p>Run the test client:</p> <pre><code># from the a2a-samples directory
python samples/python/agents/helloworld/test_client.py
</code></pre>

## Understanding the Client Code

<p>Let's look at key parts of <code>test_client.py</code>:</p> <ol> <li> <p>Fetching the Agent Card &amp; Initializing the Client:</p> <pre><code>base_url = 'http://localhost:9999'

async with httpx.AsyncClient() as httpx_client:
    # Initialize A2ACardResolver
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
        # agent_card_path uses default, extended_agent_card_path also uses default
    )
</code></pre> <p>The <code>A2ACardResolver</code> class is a convenience. It first fetches the <code>AgentCard</code> from the server's <code>/.well-known/agent-card.json</code> endpoint (based on the provided base URL) and then initializes the client with it.</p> </li> <li> <p>Sending a Non-Streaming Message (<code>send_message</code>):</p> <pre><code>client = A2AClient(
    httpx_client=httpx_client, agent_card=final_agent_card_to_use
)
logger.info('A2AClient initialized.')

send_message_payload: dict[str, Any] = {
    'message': {
        'role': 'user',
        'parts': [
            {'kind': 'text', 'text': 'how much is 10 USD in INR?'}
        ],
        'messageId': uuid4().hex,
    },
}
request = SendMessageRequest(
    id=str(uuid4()), params=MessageSendParams(**send_message_payload)
)

response = await client.send_message(request)
print(response.model_dump(mode='json', exclude_none=True))
</code></pre> <ul> <li>The <code>send_message_payload</code> constructs the data for <code>MessageSendParams</code>.</li> <li>This is wrapped in a <code>SendMessageRequest</code>.</li> <li>It includes a <code>message</code> object with the <code>role</code> set to "user" and the content in <code>parts</code>.</li> <li>The Helloworld agent's <code>execute</code> method will enqueue a single "Hello World" message. The <code>DefaultRequestHandler</code> will retrieve this and send it as the response.</li> <li>The <code>response</code> will be a <code>SendMessageResponse</code> object, which contains either a <code>SendMessageSuccessResponse</code> (with the agent's <code>Message</code> as the result) or a <code>JSONRPCErrorResponse</code>.</li> </ul> </li> <li> <p>Handling Task IDs (Illustrative Note for Helloworld):</p> <p>The Helloworld client (<code>test_client.py</code>) doesn't attempt <code>get_task</code> or <code>cancel_task</code> directly because the simple Helloworld agent's <code>execute</code> method, when called via <code>message/send</code>, results in the <code>DefaultRequestHandler</code> returning a direct <code>Message</code> response rather than a <code>Task</code> object. More complex agents that explicitly manage tasks (like the LangGraph example) would return a <code>Task</code> object from <code>message/send</code>, and its <code>id</code> could then be used for <code>get_task</code> or <code>cancel_task</code>.</p> </li> <li> <p>Sending a Streaming Message (<code>send_message_streaming</code>):</p> <pre><code>streaming_request = SendStreamingMessageRequest(
    id=str(uuid4()), params=MessageSendParams(**send_message_payload)
)

stream_response = client.send_message_streaming(streaming_request)

async for chunk in stream_response:
    print(chunk.model_dump(mode='json', exclude_none=True))
</code></pre> <ul> <li>This method calls the agent's <code>message/stream</code> endpoint. The <code>DefaultRequestHandler</code> will invoke the <code>HelloWorldAgentExecutor.execute</code> method.</li> <li>The <code>execute</code> method enqueues one "Hello World" message, and then the event queue is closed.</li> <li>The client will receive this single message as one <code>SendStreamingMessageResponse</code> event, and then the stream will terminate.</li> <li>The <code>stream_response</code> is an <code>AsyncGenerator</code>.</li> </ul> </li> </ol>

## Expected Output

<p>When you run <code>test_client.py</code>, you'll see JSON outputs for:</p> <ul> <li>The non-streaming response (a single "Hello World" message).</li> <li>The streaming response (a single "Hello World" message as one chunk, after which the stream ends).</li> </ul> <p>The <code>id</code> fields in the output will vary with each run.</p> <pre><code>// Non-streaming response
{"jsonrpc":"2.0","id":"xxxxxxxx","result":{"message":{"role":"ROLE_AGENT","parts":[{"text":"Hello World"}],"messageId":"yyyyyyyy"}}}
// Streaming response (one chunk)
{"jsonrpc":"2.0","id":"zzzzzzzz","result":{"message":{"role":"ROLE_AGENT","parts":[{"text":"Hello World"}],"messageId":"wwwwwwww"}}}
</code></pre> <p>(Actual IDs like <code>xxxxxxxx</code>, <code>yyyyyyyy</code>, <code>zzzzzzzz</code>, <code>wwwwwwww</code> will be different UUIDs/request IDs)</p> <p>This confirms your server is correctly handling basic A2A interactions with the updated SDK structure!</p> <p>Now you can shut down the server by typing Ctrl+C in the terminal window where <code>__main__.py</code> is running.</p>

---

# Page: /tutorials/python/7-streaming-and-multiturn/

## 7. Streaming &amp; Multi-Turn Interactions (LangGraph Example)

<p>The Hello World example demonstrates the basic mechanics of A2A. For more advanced features like robust streaming, task state management, and multi-turn conversations powered by an LLM, we'll turn to the LangGraph example located in <code>a2a-samples/samples/python/agents/langgraph/</code>.</p> <p>This example features a "Currency Agent" that uses the Gemini model via LangChain and LangGraph to answer currency conversion questions.</p>

## Setting up the LangGraph Example

<ol> <li> <p>Create a Gemini API Key, if you don't already have one.</p> </li> <li> <p>Environment Variable:</p> <p>Create a <code>.env</code> file in the <code>a2a-samples/samples/python/agents/langgraph/</code> directory:</p> <pre><code>echo "GOOGLE_API_KEY=YOUR_API_KEY_HERE" &gt; .env
</code></pre> <p>Replace <code>YOUR_API_KEY_HERE</code> with your actual Gemini API key.</p> </li> <li> <p>Install Dependencies (if not already covered):</p> <p>The <code>langgraph</code> example has its own <code>pyproject.toml</code> which includes dependencies like <code>langchain-google-genai</code> and <code>langgraph</code>. When you installed the SDK from the <code>a2a-samples</code> root using <code>pip install -e .[dev]</code>, this should have also installed the dependencies for the workspace examples, including <code>langgraph-example</code>. If you encounter import errors, ensure your primary SDK installation from the root directory was successful.</p> </li> </ol>

## Running the LangGraph Server

<p>Navigate to the <code>a2a-samples/samples/python/agents/langgraph/app</code> directory in your terminal and ensure your virtual environment (from the SDK root) is activated.</p> <p>Start the LangGraph agent server:</p> <pre><code>python __main__.py
</code></pre> <p>This will start the server, usually on <code>http://localhost:10000</code>.</p>

## Interacting with the LangGraph Agent

<p>Open a new terminal window, activate your virtual environment, and navigate to <code>a2a-samples/samples/python/agents/langgraph/app</code>.</p> <p>Run its test client:</p> <pre><code>python test_client.py
</code></pre> <p>Now, you can shut down the server by typing Ctrl+C in the terminal window where <code>__main__.py</code> is running.</p>

## Key Features Demonstrated

<p>The <code>langgraph</code> example showcases several important A2A concepts:</p> <ol> <li> <p>LLM Integration:</p> <ul> <li><code>agent.py</code> defines <code>CurrencyAgent</code>. It uses <code>ChatGoogleGenerativeAI</code> and LangGraph's <code>create_react_agent</code> to process user queries.</li> <li>This demonstrates how a real LLM can power the agent's logic.</li> </ul> </li> <li> <p>Task State Management:</p> <ul> <li> <p><code>samples/langgraph/__main__.py</code> initializes a <code>DefaultRequestHandler</code> with an <code>InMemoryTaskStore</code>.</p> <pre><code>httpx_client = httpx.AsyncClient()
push_config_store = InMemoryPushNotificationConfigStore()
push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                config_store=push_config_store)
request_handler = DefaultRequestHandler(
    agent_executor=CurrencyAgentExecutor(),
    task_store=InMemoryTaskStore(),
    push_config_store=push_config_store,
    push_sender= push_sender
)
server = A2AStarletteApplication(
    agent_card=agent_card, http_handler=request_handler
)

uvicorn.run(server.build(), host=host, port=port)
</code></pre> </li> <li> <p>The <code>CurrencyAgentExecutor</code> (in <code>samples/langgraph/agent_executor.py</code>), when its <code>execute</code> method is called by the <code>DefaultRequestHandler</code>, interacts with the <code>RequestContext</code> which contains the current task (if any).</p> </li> <li>For <code>message/send</code>, the <code>DefaultRequestHandler</code> uses the <code>TaskStore</code> to persist and retrieve task state across interactions. The response to <code>message/send</code> will be a full <code>Task</code> object if the agent's execution flow involves multiple steps or results in a persistent task.</li> <li>The <code>test_client.py</code>'s <code>run_single_turn_test</code> demonstrates getting a <code>Task</code> object back and then querying it using <code>get_task</code>.</li> </ul> </li> <li> <p>Streaming with <code>TaskStatusUpdateEvent</code> and <code>TaskArtifactUpdateEvent</code>:</p> <ul> <li>The <code>execute</code> method in <code>CurrencyAgentExecutor</code> is responsible for handling both non-streaming and streaming requests, orchestrated by the <code>DefaultRequestHandler</code>.</li> <li>As the LangGraph agent processes the request (which might involve calling tools like <code>get_exchange_rate</code>), the <code>CurrencyAgentExecutor</code> enqueues different types of events onto the <code>EventQueue</code>:<ul> <li><code>TaskStatusUpdateEvent</code>: For intermediate updates (e.g., "Looking up exchange rates...", "Processing the exchange rates..").</li> <li><code>TaskArtifactUpdateEvent</code>: When the final answer is ready, it's enqueued as an artifact. The <code>lastChunk</code> flag is <code>True</code>.</li> <li>A final <code>TaskStatusUpdateEvent</code> with <code>state=TaskState.completed</code> is sent to signify the end of the task, closing the stream.</li> </ul> </li> <li>The <code>test_client.py</code>'s <code>run_streaming_test</code> function will print these individual event chunks as they are received from the server.</li> </ul> </li> <li> <p>Multi-Turn Conversation (<code>TaskState.input_required</code>):</p> <ul> <li>The <code>CurrencyAgent</code> can ask for clarification if a query is ambiguous (e.g., user asks "how much is 100 USD?").</li> <li>When this happens, the <code>CurrencyAgentExecutor</code> will enqueue a <code>TaskStatusUpdateEvent</code> where <code>status.state</code> is <code>TaskState.input_required</code> and <code>status.message</code> contains the agent's question (e.g., "To which currency would you like to convert?"). The stream closes after this event.</li> <li>The <code>test_client.py</code>'s <code>run_multi_turn_test</code> function demonstrates this:<ul> <li>It sends an initial ambiguous query.</li> <li>The agent responds (via the <code>DefaultRequestHandler</code> processing the enqueued events) with a <code>Task</code> whose status is <code>input_required</code>.</li> <li>The client then sends a second message, including the <code>taskId</code> and <code>contextId</code> from the first turn's <code>Task</code> response, to provide the missing information ("in GBP"). This continues the same task.</li> </ul> </li> </ul> </li> </ol>

## Exploring the Code

<p>Take some time to look through these files:</p> <ul> <li><code>__main__.py</code>: Server setup using <code>A2AStarletteApplication</code> and <code>DefaultRequestHandler</code>. Note the <code>AgentCard</code> definition includes <code>capabilities.streaming=True</code>.</li> <li><code>agent.py</code>: The <code>CurrencyAgent</code> with LangGraph, LLM model, and tool definitions.</li> <li><code>agent_executor.py</code>: The <code>CurrencyAgentExecutor</code> implementing the <code>execute</code> (and <code>cancel</code>) method. It uses the <code>RequestContext</code> to understand the ongoing task and the <code>EventQueue</code> to send back various events (<code>TaskStatusUpdateEvent</code>, <code>TaskArtifactUpdateEvent</code>, new <code>Task</code> object implicitly via the first event if no task exists).</li> <li><code>test_client.py</code>: Demonstrates various interaction patterns, including retrieving task IDs and using them for multi-turn conversations.</li> </ul> <p>This example provides a much richer illustration of how A2A facilitates complex, stateful, and asynchronous interactions between agents.</p>

---

# Page: /tutorials/python/8-next-steps/

## Next Steps

<p>Congratulations on completing the A2A Python SDK Tutorial! You've learned how to:</p> <ul> <li>Set up your environment for A2A development.</li> <li>Define Agent Skills and Agent Cards using the SDK's types.</li> <li>Implement a basic HelloWorld A2A server and client.</li> <li>Understand and implement streaming capabilities.</li> <li>Integrate a more complex agent using LangGraph, demonstrating task state management and tool use.</li> </ul> <p>You now have a solid foundation for building and integrating your own A2A-compliant agents.</p>

## Where to Go From Here?

<p>Here are some ideas and resources to continue your A2A journey:</p> <ul> <li>Explore Other Examples:<ul> <li>Check out the other examples in the a2a-samples GitHub repository for more complex agent integrations and features.</li> </ul> </li> <li>Deepen Your Protocol Understanding:<ul> <li>📚 Read the complete A2A Protocol Documentation site for a comprehensive overview.</li> <li>📝 Review the detailed A2A Protocol Specification to understand the nuances of all data structures and RPC methods.</li> </ul> </li> <li>Review Key A2A Topics:<ul> <li>A2A and MCP: Understand how A2A complements the Model Context Protocol for tool usage.</li> <li>Enterprise-Ready Features: Learn about security, observability, and other enterprise considerations.</li> <li>Streaming &amp; Asynchronous Operations: Get more details on SSE and push notifications.</li> <li>Agent Discovery: Explore different ways agents can find each other.</li> </ul> </li> <li>Build Your Own Agent:<ul> <li>Try creating a new A2A agent using your favorite Python agent framework (like LangChain, CrewAI, AutoGen, Semantic Kernel, or a custom solution).</li> <li>Implement the <code>a2a.server.AgentExecutor</code> interface to bridge your agent's logic with the A2A protocol.</li> <li>Think about what unique skills your agent could offer and how its Agent Card would represent them.</li> </ul> </li> <li>Experiment with Advanced Features:<ul> <li>Implement robust task management with a persistent <code>TaskStore</code> if your agent handles long-running or multi-session tasks.</li> <li>Explore implementing push notifications if your agent's tasks are very long-lived.</li> <li>Consider more complex input and output modalities (e.g., handling file uploads/downloads via file Parts, or structured data via data Parts).</li> </ul> </li> <li>Contribute to the A2A Community:<ul> <li>Join the discussions on the A2A GitHub Discussions page.</li> <li>Report issues or suggest improvements via GitHub Issues.</li> <li>Consider contributing code, examples, or documentation. See the CONTRIBUTING.md guide.</li> </ul> </li> </ul> <p>The A2A protocol aims to foster an ecosystem of interoperable AI agents. By building and sharing A2A-compliant agents, you can be a part of this exciting development!</p>

---

