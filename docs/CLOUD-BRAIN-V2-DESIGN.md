# Cloud Brain v2 — Architecture Design Document

**Status:** COMPLETE
**Date:** 2026-03-21
**Author:** CTO Agent + 5 research agents (arch, deploy, code-review, tools, inventory)

## 1. Current State (Brutal Honest Assessment)

### What works
- `WriteSkill.format_citation()` — string formatting, always works
- `WriteSkill.generate_section()` — template mode only (no LLM = boilerplate)
- Everything else is a **facade** — imports succeed, but no tool produces real output

### Critical bugs in current implementation
1. **Race conditions** — all lazy singletons (`_tu_instance`, `_biomni_agent`, `_mcp_session`) have no locks. Concurrent requests corrupt state.
2. **Event loop blocking** — `_find_tools`, `_biomni_go`, `_biomni_list_tools` call sync functions in async context without `run_in_executor`. Freezes FastAPI.
3. **Zero timeouts** — one hung backend blocks the entire server indefinitely.
4. **Security holes** — `biomni_add_data` accepts arbitrary file paths. `_run_tool` passes unvalidated user input to ToolUniverse.
5. **`configure(reset=True)` crashes** — calls `run_until_complete()` inside running event loop.

### Test reality
- 242 tests pass, 100% coverage on skills module
- All tests mock everything — they test the mocking framework, not the code
- Zero integration tests. Zero BDD features (violates CLAUDE.md requirement).

## 2. What We're Building

**Cloud Brain** = A unified API that gives any researcher access to 2,400+ scientific tools through one endpoint.

Think: **HuggingFace Inference API, but for lab tools instead of ML models.**

User sends: `POST /brain/execute {"tool": "UniProt_get_function", "args": {"accession": "P05067"}}`
Gets back: Real protein function data from UniProt.

### Scale targets
- Phase 1: 10 users, 100 tools working end-to-end
- Phase 2: 50 users, 500 tools
- Phase 3: 100+ users, 2,400+ tools

## 3. Architecture

### 3.1 Smart Monolith (Phase 1-2)

```
              Cloudflare Tunnel (free, SSL, DDoS)
                         |
                   [DO Droplet s-4vcpu-8gb $48/mo]
                         |
                   Nginx reverse proxy
                         |
            Gunicorn + 2 Uvicorn workers (--preload)
                         |
                   FastAPI (Cloud Brain)
                  /       |         \
        ToolUniverse   MCP Manager   HTTP Pool
        (in-process)   (subprocess)  (httpx.AsyncClient)
             |            |    |          |
         2062 tools    K-Dense LifeSci  UniProt
         (lazy-loaded) (stdio) (stdio)  PubChem
                                        ChEMBL
```

### 3.2 Three Tool Hosting Tiers

| Tier | Examples | Execution | Concurrency |
|------|----------|-----------|-------------|
| **In-process Python** | ToolUniverse, Biomni, RDKit, Scanpy | `run_in_executor(thread_pool, fn)` | Thread-safe via executor |
| **MCP subprocess** | K-Dense, Claude Life Sci, PubMed MCP | `MCPProcessManager` with lock + health check + auto-restart | Lock per session |
| **External HTTP** | UniProt, PubChem, Semantic Scholar | `httpx.AsyncClient` with connection pooling | Fully concurrent |

### 3.3 Key Design Decisions

**a) Thread pool for sync SDKs (NOT asyncio)**
ToolUniverse and Biomni are sync libraries. Wrapping in asyncio doesn't make them async — it just adds complexity. Use `loop.run_in_executor()` consistently for ALL sync SDK calls.

**b) Lock per singleton**
```python
_lock = asyncio.Lock()
_instance = None

async def get_instance():
    async with _lock:
        if _instance is None:
            _instance = create_instance()
        return _instance
```

**c) MCPProcessManager for subprocess lifecycle**
Each MCP server gets a dedicated manager with:
- asyncio.Lock for session access
- Health check ping before each call
- Auto-restart on failure (max 3 restarts)
- Proper cleanup on shutdown

**d) Response size limits**
All tool results truncated to 100KB max. Large results return a summary + download URL.

**e) Timeouts on everything**
- Tool execution: 30s default, 120s for heavy tools (Biomni)
- MCP session: 10s connection timeout
- Health checks: 5s per skill, concurrent (not sequential)
- HTTP external calls: 30s

## 4. Production Guardrails

### 4.1 Rate Limiting (SlowAPI)
- 60 requests/min per API key (general)
- 10 requests/min for Biomni (expensive — uses Anthropic API)
- 1000 requests/day per free tier key

### 4.2 Input Validation
- Max request body: 1MB
- Max tool argument string: 10KB
- Blocklist for file paths in all tools (no /etc/, /proc/, /sys/)
- Prompt injection detection for Biomni queries

### 4.3 API Key Management
- One key per user/team
- Keys stored in `.env` file (Phase 1) → SQLite (Phase 2) → Postgres (Phase 3)
- FastAPI middleware with `X-API-Key` header

### 4.4 Monitoring
- Structured JSON logging to stdout
- DO built-in Droplet monitoring (CPU/RAM/disk alerts)
- `/brain/health` endpoint with per-skill status
- Phase 2: Prometheus metrics export

## 5. Deployment

### 5.1 Infrastructure ($49/mo)
- DO Droplet `s-4vcpu-8gb`: $48/mo
- Cloudflare Tunnel: free (SSL, DDoS, CDN)
- Domain: ~$1/mo

### 5.2 Docker Compose
```yaml
services:
  brain:
    build: .
    ports: ["127.0.0.1:8000:8000"]
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TOOLUNIVERSE_LAZY_LOADING=true
    volumes:
      - tu_cache:/root/.cache/tooluniverse
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CF_TUNNEL_TOKEN}
    restart: unless-stopped
```

### 5.3 Memory Budget
- ToolUniverse: 124 MB RSS (measured)
- FastAPI + Uvicorn: ~50 MB
- MCP subprocesses: ~100 MB each × 2 = 200 MB
- OS + buffers: 500 MB
- **Total: ~900 MB / 8 GB available = 11% utilization**

## 6. Implementation Plan

### Phase 1: Make It Real (Week 1)
**Goal: 10 tools that actually return real data end-to-end**

1. Fix all 5 high-severity bugs (locks, executor, timeouts, security, configure)
2. Install ToolUniverse SDK, verify 10 most useful tools work
3. Add API key auth + rate limiting
4. Deploy to DO droplet with Docker Compose
5. Write 10 integration tests with real ToolUniverse SDK

### Phase 2: Breadth (Week 2-3)
**Goal: 100+ tools, 15 REST API MCP servers**

1. Wrap 15 REST APIs as MCP servers (Semantic Scholar, PubMed, etc.)
2. Install Biomni, verify 5 key tools
3. Connect K-Dense MCP, verify skill discovery
4. Add structured logging + DO monitoring
5. Write BDD feature files

### Phase 3: Scale (Week 4+)
**Goal: Full 2,400+ tools, 50+ users**

1. All ToolUniverse tools verified
2. Caching layer (LRU + disk)
3. Usage analytics per user
4. Upgrade to `g-4vcpu-16gb` ($120/mo) if needed
5. Add Redis/Valkey for shared rate-limit state

## 7. What NOT to Do

1. **Don't build microservices** — smart monolith until 100+ users
2. **Don't add Redis/Valkey yet** — in-process LRU is enough for Phase 1-2
3. **Don't use DO App Platform** — gVisor sandbox breaks MCP subprocess management
4. **Don't use Kubernetes** — massive overkill for 10-100 users
5. **Don't write more mock-only tests** — every new test must call a real API or real SDK
6. **Don't add tools that aren't verified** — better 10 working tools than 2,400 facades

## 8. Architecture Lessons from Industry (Research Findings)

### 8.1 Three-Layer Tool Discovery (Critical)

**Problem:** 2,400 tool descriptions = ~400K tokens. Cannot send to LLM.
**Solution (from ToolUniverse + HuggingFace):**

```
User query: "find genes associated with Alzheimer's"
    ↓
Layer 1: Metadata filter (category, tags)    2400 → 200 tools    <1ms
    ↓
Layer 2: Embedding search (sentence-transformer) 200 → 20 tools   ~50ms
    ↓
Layer 3: LLM reranker (optional)               20 → 5 tools     ~500ms
    ↓
Execute top-ranked tool
```

ToolUniverse already implements this with their ToolFinder (keyword/TF-IDF + fine-tuned embedding + LLM). We should USE ToolUniverse's ToolFinder, not rebuild it.

### 8.2 Proxy-Router Architecture (from HuggingFace)

HuggingFace Inference Providers routes to 17+ backends through one API with policy-based selection (`:fastest`, `:cheapest`, `:preferred`) and automatic failover.

Our Cloud Brain should do the same:
```
/brain/execute
    → Router (which backend?)
        → In-process Python (ToolUniverse, RDKit)
        → MCP subprocess (K-Dense, PubMed)
        → External HTTP (UniProt REST, Semantic Scholar)
        → Remote GPU (future: AlphaFold inference)
```

### 8.3 What Failed (OpenAI Plugins, 2023-2024)

OpenAI Plugins failed because:
1. Raw OpenAPI specs as tool definitions — LLMs can't parse them
2. No quality control — broken plugins everywhere
3. No composition — plugins couldn't call each other
4. Broken auth flows — OAuth was a nightmare

**Lesson:** LLM-optimized tool descriptions (not raw specs), quality validation gate, composition support from day one.

### 8.4 MCP is Transport, Not Intelligence

MCP solves connectivity (stdio/HTTP/SSE). But:
- Discovery: MCP has no built-in tool search
- Ranking: MCP can't prioritize tools
- Caching: MCP has no result cache
- Billing: MCP has no metering

**We build the intelligence layer ON TOP of MCP.**

### 8.5 Code-as-Action for Composition (from Biomni)

When a query needs multiple tools, don't build a declarative workflow DSL. Instead, the LLM generates Python code that orchestrates the tools:

```python
# LLM generates this:
gene_data = await brain.execute("UniProt_get_function", accession="P05067")
papers = await brain.execute("search_pubmed", query=gene_data["function"][:100])
synthesis = await brain.execute("generate_section", section_type="results", findings=[...])
```

This is more flexible and debuggable than a DAG-based orchestrator.

## 9. Quick Wins (ordered by effort)

| # | Tool | Effort | Impact | Type |
|---|------|--------|--------|------|
| 1 | UniProt (via ToolUniverse) | Done | High | In-process |
| 2 | PubMed search | 1 day | High | REST API → MCP |
| 3 | Semantic Scholar | 1 day | High | REST API → MCP |
| 4 | ChEMBL query | 1 day | High | REST API → MCP |
| 5 | OpenAlex papers | 1 day | High | REST API → MCP |
| 6 | ClinicalTrials.gov | 1 day | Medium | REST API → MCP |
| 7 | PubChem compounds | 1 day | Medium | REST API → MCP |
| 8 | RDKit (chemistry) | 2 days | High | Python SDK |
| 9 | Biopython (sequences) | 1 day | Medium | Python SDK |
| 10 | OpenTargets | 1 day | Medium | REST API → MCP |

## 10. Research Sources

- HuggingFace Inference API: TGI engine (Rust+Python), Inference Providers routing
- LangChain/LangGraph: Three-level tool abstraction, graph-based flow
- OpenAI Plugins: Failed Mar 2024, fatal flaws documented
- Anthropic MCP: JSON-RPC 2.0, moving to stateless for horizontal scaling
- Microsoft Semantic Kernel: Plugin DI, max 10-20 tools per LLM call
- ToolUniverse: Three-strategy ToolFinder, 600+ tools, MCP bridge
- Biomni: AI-mined catalog from 2,500 bioRxiv papers, code-as-action
- DigitalOcean: Droplet pricing, App Platform limits (gVisor breaks MCP)
- ToolUniverse RSS: 124 MB measured, lazy loading default
