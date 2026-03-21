# Cloud Brain Architecture Research: How Top AI Platforms Build Tool/Skill Hubs

**Date**: 2026-03-20
**Purpose**: Deep research for designing LabClaw Cloud Brain — a unified service giving researchers access to 2400+ scientific tools through one API.

---

## Table of Contents

1. [HuggingFace Inference API](#1-huggingface-inference-api)
2. [LangChain/LangGraph Tool System](#2-langchainlanggraph-tool-system)
3. [OpenAI Plugins / GPT Actions](#3-openai-plugins--gpt-actions)
4. [Anthropic MCP](#4-anthropic-mcp-model-context-protocol)
5. [Microsoft Semantic Kernel](#5-microsoft-semantic-kernel)
6. [ToolUniverse Architecture](#6-tooluniverse-architecture)
7. [Biomni Architecture](#7-biomni-architecture)
8. [Tool Selection at Scale — Cross-Cutting Research](#8-tool-selection-at-scale)
9. [Top 5 Lessons for Cloud Brain](#9-top-5-lessons-for-cloud-brain)
10. [Recommended Architecture](#10-recommended-architecture)
11. [Mistakes to Avoid](#11-mistakes-to-avoid)

---

## 1. HuggingFace Inference API

### Architecture Overview

HuggingFace operates TWO complementary inference systems:

**A) Text Generation Inference (TGI) — the execution engine**

Three-tier distributed architecture (all Rust + Python):

```
┌─────────────────────────────────────────────────┐
│                   LAUNCHER (Rust)                │
│  - Parses CLI args, loads model config from Hub  │
│  - Determines optimal batch sizes from VRAM      │
│  - Spawns Router + Server processes              │
│  - Monitors process health, forwards signals     │
└────────────┬──────────────────┬──────────────────┘
             │                  │
    ┌────────▼────────┐  ┌──────▼──────────────────┐
    │  ROUTER (Rust)  │  │    SERVER (Python/gRPC)  │
    │  Axum HTTP      │  │  - Loads model via       │
    │  - Validation   │  │    factory pattern        │
    │  - Tokenization │  │  - KV cache management   │
    │  - Continuous   │  │  - Flash Attention v2    │
    │    batching     │  │  - Paged Attention       │
    │  - Chat template│  │  - Multi-GPU via NCCL   │
    │  - gRPC client  │  │  - Quantization support  │
    └────────┬────────┘  └──────▲──────────────────┘
             │                  │
             └──── UDS gRPC ────┘
         (Unix Domain Socket /tmp/tgs-*)
```

**B) Inference Providers — the routing layer**

Proxy-based multi-provider routing through `router.huggingface.co`:

```
┌──────────────────────────────────────────────────────┐
│                    CLIENT REQUEST                     │
│  model="deepseek-ai/DeepSeek-R1:fastest"             │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│            HF ROUTING PROXY                          │
│  router.huggingface.co                               │
│                                                      │
│  1. Parse model ID + policy suffix (:fastest,        │
│     :cheapest, :preferred)                           │
│  2. Lookup compatible providers for model            │
│  3. Select provider based on policy                  │
│  4. Transform request to provider-specific format    │
│  5. Route request, handle auth                       │
│  6. Automatic failover if provider unavailable       │
│  7. Unified billing (pass-through, no markup)        │
└──┬────────┬────────┬────────┬────────┬───────────────┘
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────────┐
│Samba-││Togeth││Groq  ││Repli-││15+ other │
│Nova  ││er AI ││      ││cate  ││providers │
└──────┘└──────┘└──────┘└──────┘└──────────┘
```

### Key Design Decisions

| Decision | Trade-off |
|----------|-----------|
| Rust Router + Python Server | Performance (Rust async I/O) vs ML ecosystem (Python) |
| Unix Domain Sockets for IPC | Low latency, but single-machine only |
| Continuous batching | Higher GPU utilization vs implementation complexity |
| Paged Attention (block-based KV cache) | Memory efficiency vs fragmentation overhead |
| RadixAllocator for prefix caching | Reuse common prompts vs memory for radix tree |
| Provider proxy with policy suffixes | User flexibility vs routing complexity |
| OpenAI-compatible API | Easy migration vs constrained to OpenAI's schema |
| No markup on provider rates | Attracts users vs revenue comes from Pro/Enterprise |

### What Scales Well

- **Continuous batching**: New requests join mid-inference without waiting
- **Prefix caching**: Common system prompts cached across requests (RadixAllocator)
- **Multi-provider routing**: Failover across 17+ providers
- **Policy-based selection**: `:fastest`, `:cheapest`, `:preferred` — users control the tradeoff
- **Hardware abstraction**: Same Router/Launcher works across CUDA, ROCm, Intel, Gaudi, TPU

### What Breaks at Scale

- **Cold starts**: Scaled-to-zero endpoints require model re-download (minutes for large models)
- **GPU snapshotting**: Community explored restoring 70B models in ~2 seconds via GPU runtime snapshots — HF has not adopted this yet
- **Provider mapping**: Centrally maintained model-to-provider compatibility matrix — manual, not auto-discovered

### Failure Modes

- EmptyInput / temperature / token limit validation errors → rejected at Router
- gRPC connection failures → Tonic client retries
- Process crashes → Launcher detects and propagates shutdown signals
- Provider unavailability → automatic failover to alternative provider

### Tool Discovery

Not applicable — HF is model-centric, not tool-centric. Models are discovered through the Hub (model cards, tags, trending), not semantic search.

### Tool Composition

No built-in composition. Users chain models in their application code. HF provides the infrastructure, not the orchestration.

---

## 2. LangChain/LangGraph Tool System

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                  │
│  Agent (LLM + tool selection via function calling)   │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              AGENT EXECUTOR / LANGGRAPH              │
│  - ReAct loop: Reason → Act → Observe               │
│  - Dynamic tool selection based on state             │
│  - Graph-based flow control (LangGraph)              │
│  - Checkpointing, branching, human-in-the-loop      │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                 TOOL ABSTRACTION LAYER               │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ @tool    │  │StructuredTool│  │   BaseTool    │  │
│  │ decorator│  │.from_function│  │   subclass    │  │
│  │ (simple) │  │ (medium)     │  │   (advanced)  │  │
│  └──────────┘  └──────────────┘  └───────────────┘  │
│                                                      │
│  All implement Runnable Interface:                   │
│  - with_retry() → configurable retry policies        │
│  - with_fallbacks() → graceful degradation           │
│  - batch() → parallel execution                      │
│  - astream() → async streaming                       │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│               PRODUCTION CONCERNS                    │
│                                                      │
│  Rate Limiting: Exponential backoff decorators       │
│  Caching: TTL-based, reduces redundant API calls     │
│  Validation: Pydantic schemas, injection prevention  │
│  Output Sanitization: Filter secrets before LLM      │
│  Tracing: LangSmith (LANGCHAIN_TRACING_V2=true)     │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Trade-off |
|----------|-----------|
| Runnable Interface for everything | Uniform composition vs learning curve |
| 3 tool creation levels (@tool, StructuredTool, BaseTool) | Progressive complexity vs API surface area |
| LLM-based tool selection (via function calling) | Flexible vs prompt-dependent accuracy |
| Pydantic for parameter validation | Type safety vs schema verbosity |
| LangGraph replacing AgentExecutor | Better control flow vs migration burden |
| LangSmith for observability | Deep tracing vs vendor lock-in |

### What Scales Well

- **Runnable composition**: `.pipe()`, `.batch()`, `.astream()` — uniform interface for chaining
- **Dynamic tool filtering**: Tools can be filtered by auth state, permissions, conversation stage
- **LangGraph state machines**: Fine-grained control over agent flow with checkpointing
- **Retry policies**: Node-level retry with configurable backoff, exception filtering

### What Breaks at Scale

- **Tool description quality**: LLMs struggle with >10-20 tools — accuracy drops rapidly
- **No built-in tool registry**: All tools must be passed at agent creation time or dynamically injected
- **Prompt bloat**: Each tool's Pydantic schema is serialized into the prompt (token-expensive)
- **Error cascading**: Without circuit breakers, one failing tool can consume retry budget

### Failure Modes

- Schema validation errors → Pydantic catches before execution
- Tool execution errors → ToolNode captures and reports to LLM
- HTTP 5xx → automatic retry; 4xx → no retry by default
- Retry exhaustion → configurable fallback or graph termination
- Parsing errors → output parser retry with LLM self-correction

### Tool Discovery

LLM-driven: the agent sees tool names + descriptions in its context and decides which to call. No semantic search, no embedding-based retrieval. Tool selection quality depends entirely on description quality and LLM capability.

### Tool Composition

- **RouterChain**: routes queries to specialized sub-chains
- **MultiPromptChain**: switches prompt behavior dynamically
- **LangGraph**: graph-based composition with conditional edges, parallel branches
- **No declarative workflow language** — composition is code-level

---

## 3. OpenAI Plugins / GPT Actions

### Architecture Overview (Historical — Deprecated)

```
┌────────────────────────────────────────────────────┐
│                   ChatGPT                          │
│                                                    │
│  1. User sends message                             │
│  2. ChatGPT checks registered plugins              │
│  3. Decides if plugin needed (via function calling)│
│  4. Generates API call parameters                  │
│  5. Makes HTTP request to plugin server            │
│  6. Receives response, integrates into answer      │
└───────────────────────┬────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────┐
│           PLUGIN DISCOVERY & REGISTRATION          │
│                                                    │
│  GET /.well-known/ai-plugin.json                   │
│  ┌──────────────────────────────────────────────┐  │
│  │ {                                            │  │
│  │   "schema_version": "v1",                    │  │
│  │   "name_for_human": "...",                   │  │
│  │   "name_for_model": "...",                   │  │
│  │   "description_for_human": "...",            │  │
│  │   "description_for_model": "...",            │  │
│  │   "auth": { "type": "oauth" },               │  │
│  │   "api": { "type": "openapi",                │  │
│  │            "url": "/openapi.yaml" }          │  │
│  │ }                                            │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  OpenAPI Spec → compiled into prompt describing    │
│  each endpoint, parameters, and expected responses │
└────────────────────────────────────────────────────┘
```

### Timeline of Failure

| Date | Event |
|------|-------|
| Mar 2023 | Plugins beta launched |
| Nov 2023 | GPTs with Actions announced |
| Jan 2024 | GPT Store launched |
| Mar 19, 2024 | Plugin store closed to new conversations |
| Apr 9, 2024 | All plugin chats shut down |
| 2024-2025 | GPT Actions also largely deprecated |

### What Went Wrong — Lessons

1. **OpenAPI spec → prompt was fragile**: The model had to interpret complex API schemas injected into its context. Schema misinterpretation was common. The model would ignore constraints, hallucinate parameters, or call wrong endpoints.

2. **Quality control impossible at scale**: Plugin marketplace had wildly varying quality. No verification that plugins actually worked as described.

3. **No composition model**: Plugins were isolated — you couldn't chain Plugin A's output into Plugin B. Each plugin was a standalone API call.

4. **Auth was a nightmare**: OAuth flows for hundreds of third-party services, each with different token refresh mechanisms. Users got stuck in auth loops.

5. **Discovery was poor**: The plugin "store" was just a list. No semantic search, no recommendation, no "right tool for this query" intelligence.

6. **Actions (GPTs) had the same fundamental problems**: OpenAPI specs still needed manual maintenance, LLM still misunderstood schemas, non-technical teams couldn't debug failures.

### Key Takeaway

**OpenAPI-spec-as-tool-definition does not work reliably.** The gap between "what the spec says" and "what the LLM understands" is too large. Plugins/Actions proved that tool definitions need to be LLM-native (designed for LLM consumption), not API-native (designed for developer consumption).

---

## 4. Anthropic MCP (Model Context Protocol)

### Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    HOST APPLICATION                   │
│              (Claude Desktop, IDE, etc.)              │
│                                                      │
│  ┌──────────────────────────────────────────────────┐│
│  │              MCP CLIENT                          ││
│  │  - Manages connections to multiple servers       ││
│  │  - Translates between host needs and protocol    ││
│  │  - Registers discovered capabilities             ││
│  └──────┬───────────────┬───────────────┬───────────┘│
└─────────┼───────────────┼───────────────┼────────────┘
          │               │               │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │MCP Server │   │MCP Server │   │MCP Server │
    │ (Local)   │   │ (Local)   │   │ (Remote)  │
    │           │   │           │   │           │
    │ Tools     │   │ Tools     │   │ Tools     │
    │ Resources │   │ Resources │   │ Resources │
    │ Prompts   │   │ Prompts   │   │ Prompts   │
    └───────────┘   └───────────┘   └───────────┘
     via STDIO       via STDIO     via Streamable HTTP
```

### Three Capability Types

| Type | Control | Purpose |
|------|---------|---------|
| **Tools** | Model-controlled | Functions the LLM can invoke (search, send message) |
| **Resources** | Application-controlled | Data the app can expose (files, DB records) |
| **Prompts** | User-controlled | Templates for common interaction patterns |

### Transport Evolution

| Transport | Status | Use Case |
|-----------|--------|----------|
| STDIO | Stable | Local process, same-machine communication |
| HTTP+SSE | **Deprecated** | Was used for remote; replaced by Streamable HTTP |
| Streamable HTTP | Current standard | Single HTTP endpoint, bidirectional via JSON-RPC 2.0 |

### Key Design Decisions

| Decision | Trade-off |
|----------|-----------|
| JSON-RPC 2.0 wire format | Standardized vs verbose |
| Server Cards (/.well-known/mcp.json) | Pre-connection discovery vs extra roundtrip |
| STDIO for local, HTTP for remote | Simple local dev vs complex remote deployment |
| OAuth 2.1 + PKCE for auth | Security vs integration complexity |
| Stateless protocol direction (2026) | Horizontal scaling vs loss of session features |
| Server-initiated sampling | Servers can request LLM completions without API keys |

### What Scales Well

- **Composability**: Multiple servers compose naturally — client connects to N servers, each exposes independent capabilities
- **Protocol simplicity**: JSON-RPC is well-understood, tooling exists everywhere
- **Server Cards**: Enable discovery without live connections (coming 2026)
- **Language-agnostic**: Servers in any language that can speak JSON-RPC

### What Breaks at Scale

- **Stateful sessions vs load balancers**: Sticky routing required, preventing auto-scaling (being fixed in 2026)
- **JSON-RPC payload parsing for routing**: Load balancers must parse full payloads, can't use standard HTTP routing
- **No built-in tool discovery intelligence**: Client gets ALL tools from ALL servers — no semantic filtering
- **Security gaps**: Research found "all verified servers lacking any form of authentication" for data exfiltration vectors
- **No composition standard**: Chaining Server A → Server B is application-level, not protocol-level

### 2026 Roadmap Priorities

1. Evolve transport for horizontal scaling (stateless sessions)
2. Agent communication (retry semantics, result expiry)
3. Enterprise readiness (audit trails, SSO, gateway behavior)
4. Server Cards for `.well-known` metadata discovery

### Key Takeaway

MCP is becoming the **USB-C of AI tool connectivity** — a universal standard. But it solves the *connectivity* problem, not the *discovery* problem. For 2400+ tools, you still need an intelligent routing/selection layer on top of MCP.

---

## 5. Microsoft Semantic Kernel

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                      KERNEL                          │
│              (Central Orchestrator)                   │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │              PLUGIN REGISTRY                  │   │
│  │                                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ Native   │ │ OpenAPI  │ │ MCP Server   │  │   │
│  │  │ Plugin   │ │ Plugin   │ │ Plugin       │  │   │
│  │  │          │ │          │ │              │  │   │
│  │  │@Kernel   │ │Import    │ │Auto-discover │  │   │
│  │  │Function  │ │from spec │ │& register    │  │   │
│  │  └──────────┘ └──────────┘ └──────────────┘  │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │           FUNCTION CALLING ENGINE             │   │
│  │                                               │   │
│  │  1. Send all plugin schemas to LLM            │   │
│  │  2. LLM decides which functions to call       │   │
│  │  3. SK marshals request to correct function   │   │
│  │  4. Execute function, return result to LLM    │   │
│  │  5. LLM generates final response              │   │
│  │                                               │   │
│  │  FunctionChoiceBehavior.Auto() = auto-invoke  │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │           AI SERVICES                         │   │
│  │  Azure OpenAI | OpenAI | local models         │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Trade-off |
|----------|-----------|
| Plugins = groups of functions | Enterprise-friendly (mirrors services) vs abstraction overhead |
| Semantic descriptions on everything | Better LLM understanding vs developer burden |
| Dependency injection in plugin constructors | Testable, composable vs complexity |
| Three import paths (native, OpenAPI, MCP) | Flexibility vs maintenance of 3 codepaths |
| Auto function calling via LLM | Powerful vs OpenAI recommends max 10-20 tools |
| Parameter marshaling via reflection | Automatic schema generation vs type system constraints |

### What Scales Well

- **Plugin ↔ DI integration**: Enterprise apps can inject database connections, HTTP clients into plugins
- **Three import paths**: Native code for performance, OpenAPI for cross-platform, MCP for live discovery
- **Complex parameter marshaling**: Automatic JSON Schema generation from C#/Python/Java types
- **Local state pattern**: Store large/sensitive data locally, pass only state IDs to LLM (reduces token cost)

### What Breaks at Scale

- **>20 tools degrades accuracy**: OpenAI explicitly recommends no more than 20 tools per API call, ideally <10
- **Description quality is critical**: "Don't be afraid to provide detailed descriptions" — bad descriptions = wrong tool calls
- **Function calling overhead**: Each call = network roundtrip + token consumption for schema + result
- **No built-in tool discovery/search**: All registered plugins are sent to LLM — no semantic filtering

### Tool Discovery

Three mechanisms:
1. **Native plugins**: Explicitly registered in code
2. **OpenAPI import**: Import from spec at build time
3. **MCP auto-discovery**: Connect to MCP server → discover tools → register as kernel functions at runtime

### Tool Composition

- **Function chaining**: Output of one function feeds into the next via LLM reasoning
- **FunctionChoiceBehavior.Auto()**: LLM automatically chains multiple function calls
- **No declarative workflow**: Composition is emergent from LLM reasoning, not explicitly defined

### Key Takeaway

SK's strength is enterprise integration (DI, cross-platform, OpenAPI/MCP). Its weakness is the same as everyone else's: **LLM function calling breaks down beyond 10-20 tools**. For 2400+ tools, you MUST have a retrieval layer that filters down to <10 relevant tools before presenting to the LLM.

---

## 6. ToolUniverse Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│               APPLICATIONS / AGENTS                  │
│          (BioAgent, custom pipelines)                │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              TOOLUNIVERSE CORE ENGINE                │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │              TOOL FINDER                    │    │
│  │                                             │    │
│  │  Strategy 1: KEYWORD SEARCH                 │    │
│  │    - Regex tokenization                     │    │
│  │    - 45+ stop words removed                 │    │
│  │    - Suffix-based stemming                  │    │
│  │    - TF-IDF scoring                         │    │
│  │    - 2.0x bonus for name match              │    │
│  │    - 1.5x bonus for exact phrase in desc    │    │
│  │                                             │    │
│  │  Strategy 2: EMBEDDING SEARCH               │    │
│  │    - Fine-tuned GTE-Qwen2-1.5B model        │    │
│  │    - Trained on synthetic query-tool pairs   │    │
│  │    - Cosine similarity in vector DB          │    │
│  │                                             │    │
│  │  Strategy 3: LLM IN-CONTEXT SEARCH          │    │
│  │    - Sends tool name + description only      │    │
│  │    - Compact formatting (minimize tokens)    │    │
│  │    - LLM reasons about best match            │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │           TOOL REGISTRY                     │    │
│  │                                             │    │
│  │  - @register_tool decorator                 │    │
│  │  - Lazy loading (import on first use)       │    │
│  │  - JSON config → Python module mapping      │    │
│  │  - 60+ tool classes across domains          │    │
│  │  - BaseTool inheritance pattern             │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │           TOOL COMPOSER                     │    │
│  │                                             │    │
│  │  - Sequential execution                     │    │
│  │  - Parallel execution                       │    │
│  │  - Feedback-driven loops                    │    │
│  │  - Pre-built workflows:                     │    │
│  │    - drug_discovery, biomarker, literature   │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │           CACHING                           │    │
│  │                                             │    │
│  │  - Dynamic loading: first request → cache    │    │
│  │  - Platform-specific cache dirs              │    │
│  │  - Per-tool fingerprinting                  │    │
│  │  - Offline support via cached results        │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │           MCP BRIDGE                        │    │
│  │                                             │    │
│  │  Server: FastMCP wrapping all tools          │    │
│  │  Client: MCPAutoLoaderTool for remote tools  │    │
│  │  CLI: tooluniverse-smcp, tooluniverse-smcp-  │    │
│  │       stdio                                 │    │
│  └─────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│          TOOL IMPLEMENTATION MODULES                 │
│                                                      │
│  Pharmaceutical: FDA, DailyMed, ChEMBL              │
│  Genomics: GWAS, Gene Ontology, UniProt, AlphaFold  │
│  Literature: Semantic Scholar, Europe PMC, PubTator  │
│  Structural: RCSB PDB, Boltz                        │
│  Clinical: ClinicalTrials.gov, OpenTargets, HPA     │
│  Workflows: ComposeTool, PackageTool, DatasetTool   │
│  Remote: expert_feedback, immune_compass, etc.       │
└─────────────────────────────────────────────────────┘
```

### Tool Organization: 600+ tools across categories

| Category | Count | Examples |
|----------|-------|---------|
| APIs | 281 | FDA, PubChem, UniProt, GWAS |
| Scientific packages | 164 | BioPython, RDKit, PyMOL |
| Databases | 84 | ClinicalTrials, OpenTargets, HPA |
| AI Agents | 38 | Specialized sub-agents |
| ML Models | 17 | AlphaFold, ESMFold |
| Human Expert Feedback | 6 | Expert-in-the-loop validation |
| Embedding Stores | 4 | Vector databases |
| Robotics | 1 | Lab automation |

### Key Design Decisions

| Decision | Trade-off |
|----------|-----------|
| Three-strategy ToolFinder (keyword + embedding + LLM) | High recall vs 3 systems to maintain |
| JSON-based tool configuration | Data-driven extensibility vs config sprawl |
| @register_tool decorator + naming conventions | Easy registration vs implicit magic |
| Lazy loading (import on first use) | Fast startup vs first-call latency |
| MCP bridge (FastMCP wrapper) | Standards compliance vs another protocol layer |
| Fine-tuned embedding model (GTE-Qwen2-1.5B) | Better semantic matching vs training/maintenance cost |
| Pre-built composition workflows | Ready-to-use vs rigid workflows |

### What Scales Well

- **Three-strategy finder**: Keyword for speed, embedding for semantics, LLM for complex reasoning
- **Lazy loading**: Only imports tool modules when first used — 600+ tools don't all load at startup
- **JSON config separation**: Add tools without touching core engine code
- **MCP bridge**: Exposes all tools to any MCP-compatible client
- **Per-tool fingerprinting for cache**: Cache invalidation tied to tool version/config changes

### What Breaks at Scale

- **No distributed execution**: All tools run in same Python process
- **LLM tool finder cost**: Sending tool descriptions to LLM = token cost per query
- **No rate limiting or quotas**: External API calls have no built-in throttling
- **No telemetry/observability**: No built-in metrics or tracing for tool execution
- **Single embedding model**: If GTE-Qwen2-1.5B is poor for a domain, no fallback

### Key Takeaway for Cloud Brain

ToolUniverse's **three-strategy ToolFinder is the most sophisticated tool discovery system** in this research. The keyword → embedding → LLM cascade is the right pattern for 2400+ tools. However, ToolUniverse lacks production infrastructure: no rate limiting, no distributed execution, no observability.

---

## 7. Biomni Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   USER QUERY                         │
│  "Perform scRNA-seq annotation for this dataset"     │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              BIOMNI-A1 (Agent)                       │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │        TOOL RETRIEVER                       │    │
│  │  LLM-based (OpenAI or Anthropic)            │    │
│  │  Parses query → selects relevant:           │    │
│  │    - Tools (from 150)                       │    │
│  │    - Software (from 105)                    │    │
│  │    - Databases (from 59)                    │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │        PLANNING                             │    │
│  │  LLM reasons about task requirements         │    │
│  │  Generates step-by-step plan                 │    │
│  │  Each step = executable code                 │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │        CODE GENERATION & EXECUTION          │    │
│  │  Supports Python, R, Bash                    │    │
│  │  Loops, parallelization, conditionals        │    │
│  │  Tool APIs → natural language → LLM → code   │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │        OBSERVE & REFINE                     │    │
│  │  Parse tool outputs + structured logs        │    │
│  │  Self-critique → re-plan if needed           │    │
│  │  Iterate until convergence                   │    │
│  └─────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              BIOMNI-E1 (Environment)                 │
│                                                      │
│  150 specialized tools                               │
│  105 software packages (pre-installed)               │
│  59 databases (with natural language query)           │
│  ~11GB data lake (auto-downloaded on first run)       │
│                                                      │
│  Schema DB: pickled objects for rapid tool discovery  │
│  Logging: PromptLogger + NodeLogger for tracing      │
│  LangGraph for workflow orchestration                │
└─────────────────────────────────────────────────────┘
```

### How E1 Was Built

Unique approach: **mined 2,500 recent bioRxiv publications** across 25 biomedical subfields using an AI-driven discovery agent to extract tools, databases, and protocols. This is automated curation, not manual catalog building.

### Key Design Decisions

| Decision | Trade-off |
|----------|-----------|
| Code as universal action interface | Maximum flexibility (loops, conditionals) vs execution safety |
| LLM-based ToolRetriever (not embedding) | Better reasoning about complex queries vs cost per retrieval |
| Pre-installed software in environment | Zero setup for users vs 11GB+ environment size |
| Pickled schema DB for discovery | Fast offline lookup vs binary format, hard to update |
| Natural language → database queries via LLM | Accessible to non-programmers vs query accuracy depends on LLM |
| AI-mined tool catalog from publications | Automated curation vs may miss undocumented tools |

### What Scales Well

- **Code generation for composition**: No need for declarative workflow language — LLM writes the glue code
- **Multi-language support**: Python, R, Bash all in one environment
- **Self-correcting loop**: Agent observes failures and re-plans
- **AI-driven discovery**: Automated tool catalog curation from literature

### What Breaks at Scale

- **Single-machine execution**: Everything runs in one Conda environment
- **11GB data lake**: Heavy for distribution, slow to update
- **LLM-only retrieval**: No keyword/embedding fast path — every retrieval costs LLM tokens
- **No multi-tenancy**: Designed for single-user research, not shared service
- **No caching of tool results**: Each execution is fresh
- **Binary schema format**: Pickled objects are opaque and Python-version-sensitive

### Key Takeaway for Cloud Brain

Biomni's **code-as-action-interface is powerful** — it enables arbitrary composition without a restrictive workflow DSL. The **AI-mined catalog from publications** is a unique approach to keeping the tool inventory current. However, the architecture is purely academic — no production concerns (auth, rate limiting, multi-tenancy, billing).

---

## 8. Tool Selection at Scale

Cross-cutting research on how to find the right tool from 1000+ options.

### The Core Problem

One MCP server with 26 tools consumes over 4,600 tokens. For 2400 tools, sending all descriptions to an LLM is impossible (~400K+ tokens). You MUST filter before the LLM sees tools.

### Approaches Ranked by Effectiveness

| Approach | Mechanism | Performance | Cost |
|----------|-----------|-------------|------|
| **Knowledge Graph retrieval** | Tools + agents as graph nodes, metadata edges, graph traversal | Recall@5 = 0.85, nDCG@5 = 0.48 | Medium (graph DB) |
| **Embedding retrieval (unified vector space)** | Embed tools + agents together, nearest-neighbor search | 19.4% better Recall@5 vs baselines | Low (vector DB) |
| **Hierarchical routing** | Domain → category → tool (tree search, DFS-based) | Works for structured catalogs | Very low |
| **Multi-stage pipeline** | Embed → retrieve → rerank (embedding or LLM-based) | Best overall quality | Medium-high |
| **Generative (ToolGen)** | Each tool = virtual token, constrained decoding | Novel but unproven at scale | High (custom training) |

### Best Practices from Research

1. **Enhanced tool documents**: Include tool name + description + argument schema + synthetic example queries + key topics — all embedded together
2. **Metadata filtering first**: Use domain, category, input/output type to narrow before semantic search
3. **Reranking is essential**: Raw retrieval has noise; LLM-based reranking at top-k provides significant quality boost
4. **Hierarchical categorization**: For large multi-domain toolsets, tree-structured routing outperforms flat search
5. **Keep final tool set small**: Pass max 10-20 tools to the LLM for function calling

---

## 9. Top 5 Lessons for Cloud Brain

### Lesson 1: Build a Three-Layer Discovery Pipeline (ToolUniverse pattern)

**Why**: No single retrieval strategy works for 2400+ tools. Keyword search is fast but misses semantics. Embedding search captures meaning but misses exact matches. LLM search is accurate but expensive.

**Architecture**:
```
User Query
    ↓
Layer 1: METADATA FILTER (domain, modality, task type) → 2400 → ~200
    ↓
Layer 2: EMBEDDING SEARCH (fine-tuned model, cosine similarity) → 200 → ~20
    ↓
Layer 3: LLM RERANKER (reasons about relevance, selects top-k) → 20 → ~5-10
    ↓
Pass 5-10 tools to agent for function calling
```

This is the pattern ToolUniverse uses (keyword + embedding + LLM), but with a metadata pre-filter stage added. Research shows this multi-stage approach achieves the best recall and precision.

### Lesson 2: MCP as the Connectivity Standard, NOT the Discovery Standard

**Why**: MCP solves how to connect to tools (transport, auth, protocol). It does NOT solve how to find the right tool. Every platform in this research has this gap.

**Architecture**:
```
Cloud Brain API (discovery + routing + billing)
    ↓
MCP Client Layer (connects to tool servers)
    ↓
Tool Servers (each exposes tools via MCP)
```

MCP provides the universal connector. Cloud Brain provides the intelligence layer on top: discovery, ranking, composition, caching, billing.

### Lesson 3: Proxy-Router Architecture for Multi-Provider (HuggingFace pattern)

**Why**: HuggingFace's Inference Providers architecture is the model for routing to heterogeneous backends through one API. Their router at `router.huggingface.co` handles provider selection, auth translation, failover, and billing — all transparent to the client.

**For Cloud Brain**:
```
cloud-brain.labclaw.org/v1/tools/execute
    ↓
Router: policy-based tool selection (fastest, cheapest, preferred)
    ↓
Backend A: local Python execution (lightweight tools)
Backend B: GPU cluster (ML model tools)
Backend C: external API passthrough (PubChem, UniProt, etc.)
Backend D: partner MCP servers (community tools)
```

Key features to adopt:
- Policy suffixes (`:fastest`, `:cheapest`)
- Automatic failover to alternative backends
- Unified billing with no markup on passthrough
- OpenAI-compatible API format

### Lesson 4: Code-as-Action for Tool Composition (Biomni pattern)

**Why**: Every attempt at declarative tool composition (OpenAI plugins, SK planners) has struggled. Biomni's approach of generating executable code as the composition medium is more powerful and flexible.

**Why it works**:
- Code supports loops, conditionals, error handling natively
- LLMs are excellent at generating Python/R code
- No need for a custom workflow DSL
- Users can inspect, modify, and rerun generated code

**What to add** (Biomni lacks these):
- Sandboxed execution (containerized, resource-limited)
- Caching of intermediate results
- Progress tracking and partial results
- Human-in-the-loop approval gates

### Lesson 5: Don't Repeat OpenAI's Plugin Mistakes

**The three fatal flaws of OpenAI Plugins**:

1. **Raw API specs as tool definitions**: OpenAPI specs are designed for developers, not LLMs. Tool definitions must be written FOR LLMs — clear natural language, expected behavior, example inputs/outputs, failure modes.

2. **No quality gate**: Plugins varied wildly in quality. Cloud Brain must validate every tool: does it respond? Is the output parseable? Does it match the description?

3. **No composition**: Plugins were islands. Cloud Brain must have first-class support for multi-tool workflows, with the LLM generating the orchestration code (Lesson 4).

---

## 10. Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT / APPLICATION                      │
│  cloud-brain.labclaw.org/v1                                 │
│  OpenAI-compatible chat completions + tool execution        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    API GATEWAY                               │
│                                                              │
│  Auth (API keys + OAuth 2.1)                                │
│  Rate limiting (token-based, not request-based)              │
│  Billing metering                                            │
│  Request validation                                          │
│  Telemetry (traces, metrics)                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              TOOL DISCOVERY ENGINE                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Metadata     │  │ Embedding    │  │ LLM Reranker    │  │
│  │ Filter       │  │ Search       │  │                  │  │
│  │              │  │              │  │ Top-20 → Top-5   │  │
│  │ Domain,      │  │ Fine-tuned   │  │ Reasons about    │  │
│  │ modality,    │  │ model on     │  │ relevance,       │  │
│  │ task type    │  │ tool specs   │  │ user intent      │  │
│  │              │  │              │  │                  │  │
│  │ 2400→~200    │  │ ~200→~20     │  │ ~20→~5-10       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              EXECUTION ROUTER                                │
│                                                              │
│  Policy: :fastest | :cheapest | :preferred | :local          │
│  Failover: circuit breaker + automatic retry                 │
│  Caching: LRU + SQLite with per-tool fingerprinting          │
│  Progress tracking for long-running tools                    │
└────┬──────────┬──────────┬──────────┬───────────────────────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐
│Local   │ │GPU     │ │External│ │Community      │
│Python  │ │Cluster │ │API     │ │MCP Servers    │
│Executor│ │(ML     │ │Proxy   │ │(via MCP       │
│        │ │models) │ │(PubChem│ │ client)       │
│Light-  │ │AlphaFld│ │UniProt │ │Third-party    │
│weight  │ │ESMFold │ │GWAS    │ │contributions  │
│tools   │ │docking │ │FDA)    │ │               │
└────────┘ └────────┘ └────────┘ └────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              TOOL REGISTRY                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ For each tool:                                      │    │
│  │   - ID, name, version                               │    │
│  │   - LLM-optimized description (NOT raw API spec)    │    │
│  │   - Input/output JSON Schema                        │    │
│  │   - Example queries (synthetic)                     │    │
│  │   - Domain tags, modality tags                      │    │
│  │   - Embedding vector (pre-computed)                 │    │
│  │   - Backend type (local/GPU/API/MCP)                │    │
│  │   - Avg latency, cost estimate                      │    │
│  │   - Health status, last validation timestamp        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Storage: PostgreSQL (metadata) + vector DB (embeddings)     │
│  Update: automated validation + AI-mined from literature     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              COMPOSITION ENGINE                              │
│                                                              │
│  LLM generates Python code to orchestrate multi-tool         │
│  workflows. Executed in sandboxed containers with:           │
│  - Resource limits (CPU, memory, time)                       │
│  - Network isolation (only allowed API endpoints)            │
│  - Intermediate result caching                               │
│  - Progress streaming to client                              │
│  - Human-in-the-loop approval gates                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

| Component | Inspired By | Our Enhancement |
|-----------|-------------|-----------------|
| Three-layer discovery | ToolUniverse | Add metadata pre-filter + knowledge graph |
| Proxy router | HuggingFace Inference Providers | Add tool-level (not just model-level) routing |
| MCP connectivity | Anthropic MCP | As transport layer, not discovery layer |
| Code-based composition | Biomni | Add sandboxing, caching, approval gates |
| Plugin registry with DI | Semantic Kernel | Add health monitoring, auto-validation |
| Retry + circuit breakers | LangGraph/API Gateway patterns | Token-based rate limiting, not request-based |
| Avoid raw API specs | OpenAI Plugins failure | LLM-optimized tool descriptions |

---

## 11. Mistakes to Avoid

### Mistake 1: Using OpenAPI/raw API specs as tool definitions
**Evidence**: OpenAI Plugins failed because LLMs misinterpret API specs. Tool descriptions must be written FOR LLMs — natural language, examples, expected behavior, failure modes.

### Mistake 2: Sending all 2400 tool descriptions to the LLM
**Evidence**: OpenAI recommends max 10-20 tools. One MCP server with 26 tools = 4,600 tokens. 2400 tools would be 400K+ tokens. You MUST have retrieval/filtering before the LLM.

### Mistake 3: Building only one tool discovery strategy
**Evidence**: ToolUniverse uses three (keyword + embedding + LLM). Research shows multi-stage pipelines significantly outperform single-strategy approaches. Keyword search misses semantics; embedding search misses exact matches; LLM search is too expensive for first pass.

### Mistake 4: Stateful protocol for the routing layer
**Evidence**: MCP learned this the hard way — stateful sessions "fight with load balancers" and prevent horizontal scaling. Their 2026 roadmap is explicitly moving to stateless protocol. Build stateless from day one.

### Mistake 5: Ignoring tool quality validation
**Evidence**: OpenAI Plugin marketplace had wildly varying quality. Biomni and ToolUniverse don't validate that tools actually work. Cloud Brain must continuously validate: does the tool respond? Is output parseable? Does it match the description? Auto-disable broken tools.

### Mistake 6: No billing/metering from the start
**Evidence**: HuggingFace retrofitted billing into Inference Providers. It's much harder to add billing after the fact. Design metering into the API gateway from day one — track per-tool, per-user, per-request costs.

### Mistake 7: Monolithic execution environment
**Evidence**: Biomni's 11GB Conda environment is not distributable. ToolUniverse runs everything in one Python process. For production, each tool category needs independent scaling — lightweight tools on CPU, ML models on GPU, external APIs via proxy.

---

## Sources

### HuggingFace
- [TGI System Architecture (DeepWiki)](https://deepwiki.com/huggingface/text-generation-inference/2-system-architecture)
- [TGI Router Component (DeepWiki)](https://deepwiki.com/huggingface/text-generation-inference/2.1-router-component)
- [Serverless Inference API Docs](https://huggingface.co/docs/api-inference/en/index)
- [Inference Providers Docs](https://huggingface.co/docs/inference-providers/index)
- [Inference Providers Blog](https://huggingface.co/blog/inference-providers)
- [Pricing and Rate Limits](https://huggingface.co/docs/api-inference/en/pricing)

### LangChain/LangGraph
- [LangChain Tools Complete Guide 2025](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langchain-setup-tools-agents-memory/langchain-tools-complete-guide-creating-using-custom-llm-tools-code-examples-2025)
- [StructuredTool API Reference](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.structured.StructuredTool.html)
- [LangGraph Error Handling & Retries](https://dev.to/aiengineering/a-beginners-guide-to-handling-errors-in-langgraph-with-retry-policies-h22)
- [Dynamic Tool Calling in LangGraph](https://changelog.langchain.com/announcements/dynamic-tool-calling-in-langgraph-agents)
- [LangChain Agents Complete Guide 2026](https://www.leanware.co/insights/langchain-agents-complete-guide-in-2025)

### OpenAI Plugins
- [ChatGPT Killing Off Plugins Analysis](https://www.youreverydayai.com/chatgpt-is-killing-off-plugins-what-it-means/)
- [Custom GPT Actions in 2026](https://www.lindy.ai/blog/custom-gpt-actions)
- [How ChatGPT Plugins Work (Microsoft)](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/how-chatgpt-plugins-could-work/3761483)
- [ChatGPT Plugin Development Guide](https://chataibot.pro/blog/chatgpt-plugin-development/)

### Anthropic MCP
- [MCP Deep Dive (Descope)](https://www.descope.com/learn/post/mcp)
- [MCP Official Introduction](https://www.anthropic.com/news/model-context-protocol)
- [MCP Transport Future (2025)](https://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/)
- [2026 MCP Roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/)
- [Why MCP Deprecated SSE](https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/)
- [MCP Servers GitHub](https://github.com/modelcontextprotocol/servers)

### Microsoft Semantic Kernel
- [Plugins in Semantic Kernel (MS Learn)](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/)
- [Orchestrating AI Agents with SK Plugins](https://devblogs.microsoft.com/semantic-kernel/guest-blog-orchestrating-ai-agents-with-semantic-kernel-plugins-a-technical-deep-dive/)
- [Planning with Auto Function Calling](https://devblogs.microsoft.com/semantic-kernel/planning-with-semantic-kernel-using-automatic-function-calling/)
- [MCP Integration with SK](https://devblogs.microsoft.com/agent-framework/integrating-model-context-protocol-tools-with-semantic-kernel-a-step-by-step-guide/)
- [SK Architecture Analysis](https://atoms.dev/insights/semantic-kernel-an-in-depth-analysis-of-architecture-capabilities-and-real-world-applications/c84b6d35e2744b2bade35c39db516304)

### ToolUniverse
- [ToolUniverse GitHub](https://github.com/mims-harvard/ToolUniverse)
- [ToolUniverse Paper (arXiv)](https://arxiv.org/html/2509.23426v1)
- [ToolUniverse Architecture Docs](https://zitniklab.hms.harvard.edu/ToolUniverse/expand_tooluniverse/architecture.html)
- [MCP Support Docs](https://zitniklab.hms.harvard.edu/ToolUniverse/guide/mcp_support.html)
- [ToolUniverse PyPI](https://pypi.org/project/tooluniverse/)

### Biomni
- [Biomni GitHub](https://github.com/snap-stanford/Biomni)
- [Biomni Paper (bioRxiv)](https://www.biorxiv.org/content/10.1101/2025.05.30.656746v1)
- [Biomni Details (GitHub)](https://github.com/snap-stanford/Biomni/blob/main/DETAILS.md)
- [Biomni PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12157518/)

### Tool Selection at Scale
- [Tool-to-Agent Retrieval (arXiv)](https://arxiv.org/abs/2511.01854)
- [Agent-as-a-Graph (arXiv)](https://arxiv.org/html/2511.18194v1)
- [ToolFlood: Beyond Selection (arXiv)](https://arxiv.org/html/2603.13950)
- [LLM Tool Learning Survey (Springer)](https://link.springer.com/article/10.1007/s41019-025-00296-9)

### API Gateway Patterns
- [Production API Gateway Patterns for MS Foundry](https://techcommunity.microsoft.com/blog/startupsatmicrosoftblog/production-grade-api-gateway-patterns-for-microsoft-foundry/4490494)
