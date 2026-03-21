# Cloud Brain -- Your Lab's AI Toolkit for Scientific Databases

Cloud Brain is LabClaw's unified API server for querying scientific databases.
Instead of learning a dozen different REST APIs (PubMed, UniProt, ChEMBL,
NCBI Gene, PubChem, OpenTargets, ClinicalTrials, BLAST, and more), you send
all your requests to a single endpoint. Cloud Brain routes each query to the
right backend and returns structured JSON.

This guide walks you through setup, every skill the server ships with,
and copy-paste examples you can run today.

---

## 1. What Is Cloud Brain?

Cloud Brain is a FastAPI server that bundles five **skills** -- modular
connectors to scientific tools and databases:

| Skill | What It Connects To |
|-------|---------------------|
| **ToolUniverse** | 2000+ tools: UniProt, ChEMBL, PubChem, OpenTargets, FAERS, ClinicalTrials, PubMed, NCBI Gene, and more |
| **Biomni** | Stanford SNAP autonomous biomedical agent -- 150+ tools across 59 databases |
| **K-Dense** | 170+ scientific skills covering bioinformatics, cheminformatics, clinical research, lab automation |
| **LifeSci** | LLM-powered life science reasoning -- hypothesis generation, experiment design |
| **Write** | Scientific writing -- abstracts, methods, results, discussions, citations |

You interact with all of them through one base URL: `http://localhost:18802/brain/`.

**Key endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/brain/skills` | List registered skills and their capabilities |
| `GET` | `/brain/tools` | List every tool across all skills |
| `GET` | `/brain/inventory` | Categorized summary with tool counts |
| `GET` | `/brain/health` | Health check all skill backends |
| `POST` | `/brain/execute` | Run any tool by name with arguments |

---

## 2. Starting the Server

### Install LabClaw

```bash
pip install labclaw
# or, for development:
make dev-install
```

### Launch Cloud Brain

```bash
labclaw brain
```

The server starts on port **18802** by default. To use a different port:

```bash
labclaw brain --port 9000
```

### Verify it is running

```bash
curl http://localhost:18802/brain/health
```

Expected output:

```json
{
  "tooluniverse": true,
  "biomni": false,
  "kdense": true,
  "write": true,
  "lifesci": false
}
```

A `false` value means that skill's backend is not installed or not reachable.
The server still works -- you just cannot use that particular skill until its
dependency is installed.

### Optional dependencies

Each skill has its own backend. Install only what you need:

```bash
# ToolUniverse -- 2000+ scientific tools
pip install tooluniverse

# Biomni -- Stanford SNAP autonomous agent (requires Anthropic API key)
pip install biomni

# K-Dense -- 170+ scientific skills via MCP
pip install claude-skills-mcp
```

LifeSci and Write skills work out of the box (template mode). For LLM-powered
responses, configure an LLM provider in LabClaw's config.

---

## 3. Available Skills

### Full tool inventory

Every tool registered across all skills:

| Tool Name | Skill | What It Does |
|-----------|-------|--------------|
| `tu_run` | ToolUniverse | Execute any of the 2000+ tools (UniProt, ChEMBL, PubChem, etc.) |
| `tu_find_tools` | ToolUniverse | Search tools by natural language description |
| `tu_get_spec` | ToolUniverse | Get parameter schema for a specific tool |
| `tu_list_categories` | ToolUniverse | List all tool categories |
| `biomni_go` | Biomni | Run a biomedical query through the autonomous agent |
| `biomni_list_tools` | Biomni | List custom tools in the Biomni agent |
| `biomni_add_data` | Biomni | Add custom datasets for analysis |
| `kdense_find_skills` | K-Dense | Find relevant skills by description |
| `kdense_read_skill` | K-Dense | Read full skill documentation |
| `kdense_list_skills` | K-Dense | List all 170+ skills |
| `reason_lifesci` | LifeSci | Life science domain reasoning with confidence levels |
| `design_experiment` | LifeSci | Design rigorous experiments from a hypothesis |
| `generate_section` | Write | Generate scientific text (abstract, methods, results, discussion) |
| `format_citation` | Write | Format citations in APA or other styles |

### Capability mapping

Skills map to stages of the scientific method:

| Capability | Skills |
|------------|--------|
| Literature Search | ToolUniverse, K-Dense |
| Data Analysis | ToolUniverse, Biomni |
| Hypothesis Generation | Biomni, LifeSci |
| Instrument Knowledge | ToolUniverse, K-Dense |
| Scientific Writing | Write |
| General Reasoning | Biomni, K-Dense, LifeSci |

---

## 4. Searching Literature (PubMed)

### Find the right tool first

Not sure which tool to use? Ask `tu_find_tools`:

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_find_tools",
    "arguments": {
      "description": "search PubMed for research articles",
      "limit": 5
    }
  }'
```

**Python:**

```python
import requests

BASE = "http://localhost:18802"

resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_find_tools",
    "arguments": {
        "description": "search PubMed for research articles",
        "limit": 5,
    },
})
tools = resp.json()["data"]["tools"]
for t in tools:
    print(f"  {t['name']}: {t['description'][:80]}")
```

### Run a PubMed search

Once you know the tool name (e.g., `PubMed_search`), run it:

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "PubMed_search",
      "arguments": {
        "query": "CRISPR base editing efficiency 2024",
        "max_results": 10
      }
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "PubMed_search",
        "arguments": {
            "query": "CRISPR base editing efficiency 2024",
            "max_results": 10,
        },
    },
})

results = resp.json()
if results["success"]:
    for article in results["data"]:
        print(article.get("title", "No title"))
else:
    print(f"Error: {results['error']}")
```

### Using Biomni for complex literature queries

Biomni can handle multi-step literature analysis -- it autonomously decides
which databases to query:

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "biomni_go",
    "arguments": {
      "query": "Find recent papers on optogenetic control of dopamine neurons in VTA and summarize the main findings"
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "biomni_go",
    "arguments": {
        "query": (
            "Find recent papers on optogenetic control of "
            "dopamine neurons in VTA and summarize the main findings"
        ),
    },
})
print(resp.json()["data"]["result"])
```

---

## 5. Protein & Gene Queries

### UniProt -- look up a protein by accession

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "UniProt_get_entry_by_accession",
      "arguments": {
        "accession": "P04637"
      }
    }
  }'
```

**Python:**

```python
# Look up TP53 (tumor protein p53)
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "UniProt_get_entry_by_accession",
        "arguments": {"accession": "P04637"},
    },
})

protein = resp.json()["data"]
print(f"Protein: {protein.get('proteinDescription', {}).get('recommendedName', '')}")
print(f"Organism: {protein.get('organism', {}).get('scientificName', '')}")
print(f"Sequence length: {protein.get('sequence', {}).get('length', 'N/A')}")
```

### UniProt -- search by keyword

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "UniProt_search_proteins",
      "arguments": {
        "query": "insulin receptor AND organism:human",
        "limit": 5
      }
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "UniProt_search_proteins",
        "arguments": {
            "query": "insulin receptor AND organism:human",
            "limit": 5,
        },
    },
})

for entry in resp.json()["data"]:
    print(f"  {entry.get('primaryAccession')}: {entry.get('proteinDescription', '')}")
```

### NCBI Gene -- look up a gene

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "NCBI_Gene_search",
      "arguments": {
        "query": "BRCA1",
        "organism": "human"
      }
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "NCBI_Gene_search",
        "arguments": {
            "query": "BRCA1",
            "organism": "human",
        },
    },
})

gene_data = resp.json()["data"]
print(f"Gene ID: {gene_data.get('gene_id')}")
print(f"Symbol: {gene_data.get('symbol')}")
print(f"Description: {gene_data.get('description')}")
```

### Finding the right tool for your database

If you are not sure which tool name to use, search first:

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_find_tools",
    "arguments": {
        "description": "look up gene expression data in NCBI",
        "limit": 5,
    },
})

for tool in resp.json()["data"]["tools"]:
    print(f"  {tool['name']}: {tool['description'][:100]}")
```

Then get the full parameter schema:

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_get_spec",
    "arguments": {"tool_name": "NCBI_Gene_search"},
})
print(resp.json()["data"])
```

---

## 6. Chemical Compound Search

### ChEMBL -- search by compound name

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "ChEMBL_search_compound",
      "arguments": {
        "query": "aspirin"
      }
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "ChEMBL_search_compound",
        "arguments": {"query": "aspirin"},
    },
})

compounds = resp.json()["data"]
for c in compounds:
    print(f"  ChEMBL ID: {c.get('molecule_chembl_id')}")
    print(f"  Name: {c.get('pref_name')}")
    print(f"  Formula: {c.get('molecule_properties', {}).get('full_molformula', 'N/A')}")
    print()
```

### PubChem -- look up by CID

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "PubChem_get_compound_by_cid",
      "arguments": {
        "cid": 2244
      }
    }
  }'
```

**Python:**

```python
# PubChem CID 2244 = aspirin
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "PubChem_get_compound_by_cid",
        "arguments": {"cid": 2244},
    },
})

compound = resp.json()["data"]
print(f"Name: {compound.get('name')}")
print(f"SMILES: {compound.get('canonical_smiles')}")
print(f"Molecular weight: {compound.get('molecular_weight')}")
```

### Find drug targets with OpenTargets

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "OpenTargets_search_target",
      "arguments": {
        "query": "EGFR",
        "limit": 5
      }
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_run",
    "arguments": {
        "name": "OpenTargets_search_target",
        "arguments": {"query": "EGFR", "limit": 5},
    },
})

for target in resp.json()["data"]:
    print(f"  {target.get('id')}: {target.get('approvedName')}")
```

---

## 7. Sequence Analysis

### Life science reasoning for sequence questions

Use the `reason_lifesci` tool for domain-specific analysis:

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "reason_lifesci",
    "arguments": {
      "question": "What is the functional significance of the BRCA1 RING domain mutation C61G?",
      "domain": "genomics"
    }
  }'
```

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "reason_lifesci",
    "arguments": {
        "question": (
            "What is the functional significance of the "
            "BRCA1 RING domain mutation C61G?"
        ),
        "domain": "genomics",
    },
})

answer = resp.json()["data"]
print(answer.get("answer", answer.get("note")))
```

### BLAST via Biomni

Biomni can run BLAST searches as part of its autonomous reasoning:

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "biomni_go",
    "arguments": {
      "query": "Run BLAST for this protein sequence against nr database: MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH"
    }
  }'
```

**Python:**

```python
sequence = "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH"

resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "biomni_go",
    "arguments": {
        "query": f"Run BLAST for this protein sequence against nr database: {sequence}",
    },
})

print(resp.json()["data"]["result"])
```

### Find BLAST-specific tools in ToolUniverse

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_find_tools",
    "arguments": {
        "description": "BLAST sequence alignment search",
        "limit": 5,
    },
})

for tool in resp.json()["data"]["tools"]:
    print(f"  {tool['name']}: {tool['description'][:100]}")
```

### Experiment design from sequence findings

After getting sequence analysis results, use the `design_experiment` tool
to plan follow-up work:

**Python:**

```python
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "design_experiment",
    "arguments": {
        "hypothesis": "The C61G mutation in BRCA1 RING domain abolishes E3 ubiquitin ligase activity",
        "constraints": "Budget: $5000, Timeline: 2 weeks",
        "available_equipment": [
            "Western blot apparatus",
            "Cell culture facility",
            "Flow cytometer",
        ],
    },
})

design = resp.json()["data"]
print(design.get("design", design.get("note")))
```

---

## 8. Tool Discovery

Cloud Brain provides two endpoints for understanding what is available.

### GET /brain/tools -- flat list of every tool

**curl:**

```bash
curl http://localhost:18802/brain/tools | python -m json.tool
```

**Python:**

```python
resp = requests.get(f"{BASE}/brain/tools")
tools = resp.json()

print(f"Total tools available: {len(tools)}\n")
for tool in tools:
    print(f"  {tool['name']}")
    print(f"    {tool['description'][:80]}")
    print(f"    Parameters: {list(tool.get('parameters', {}).keys())}")
    print()
```

### GET /brain/inventory -- categorized summary

**curl:**

```bash
curl http://localhost:18802/brain/inventory | python -m json.tool
```

**Python:**

```python
resp = requests.get(f"{BASE}/brain/inventory")
inv = resp.json()

print(f"Total skills: {inv['total_skills']}")
print(f"Total tools: {inv['total_tools']}\n")

for cat in inv["categories"]:
    print(f"  [{cat['capability']}]")
    print(f"    Skills: {', '.join(cat['skills'])} ({cat['tool_count']} tools)")
```

Example output:

```
Total skills: 5
Total tools: 14

  [data_analysis]
    Skills: biomni, tooluniverse (7 tools)
  [general_reasoning]
    Skills: biomni, kdense, lifesci (8 tools)
  [hypothesis_generation]
    Skills: biomni, lifesci (5 tools)
  [instrument_knowledge]
    Skills: kdense, tooluniverse (7 tools)
  [literature_search]
    Skills: kdense, tooluniverse (7 tools)
  [scientific_writing]
    Skills: write (2 tools)
```

### GET /brain/skills -- skill metadata

```python
resp = requests.get(f"{BASE}/brain/skills")
for skill in resp.json():
    print(f"  {skill['name']} v{skill['version']}")
    print(f"    {skill['description']}")
    print(f"    Capabilities: {skill['capabilities']}")
    print(f"    Requires API key: {skill['requires_api_key']}")
    print()
```

### Searching within K-Dense skill library

K-Dense has 170+ built-in skills with detailed documentation:

```python
# Find relevant skills
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "kdense_find_skills",
    "arguments": {
        "description": "protein structure prediction",
        "limit": 3,
    },
})
print(resp.json()["data"])

# Read full documentation for a skill
resp = requests.post(f"{BASE}/brain/execute", json={
    "tool_name": "kdense_read_skill",
    "arguments": {"skill_name": "alphafold_analysis"},
})
print(resp.json()["data"]["content"])
```

---

## 9. API Authentication

### When authentication is needed

By default, Cloud Brain runs **without authentication** -- open access for
local development. This is fine when the server is only reachable from your
machine.

Enable API key authentication when you:
- Expose the server to your lab network
- Share the server across multiple users
- Deploy behind a reverse proxy

### Setting up API keys

Set the `LABCLAW_API_KEYS` environment variable with one or more
comma-separated keys:

```bash
# Single key
export LABCLAW_API_KEYS="sk-lab-abc123def456"

# Multiple keys (one per user)
export LABCLAW_API_KEYS="sk-alice-key1,sk-bob-key2,sk-charlie-key3"

# Then start the server
labclaw brain
```

### Using keys in requests

Pass the key in the `X-API-Key` header:

**curl:**

```bash
curl -X POST http://localhost:18802/brain/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-lab-abc123def456" \
  -d '{
    "tool_name": "tu_find_tools",
    "arguments": {"description": "protein search", "limit": 3}
  }'
```

**Python:**

```python
session = requests.Session()
session.headers.update({"X-API-Key": "sk-lab-abc123def456"})

resp = session.post(f"{BASE}/brain/execute", json={
    "tool_name": "tu_find_tools",
    "arguments": {"description": "protein search", "limit": 3},
})
```

### What happens without a valid key

When `LABCLAW_API_KEYS` is set and the request has no key or a wrong key:

```json
{"detail": "Invalid or missing API key"}
```

HTTP status: **403 Forbidden**.

### Biomni API key

Biomni requires an Anthropic API key for its LLM backend:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

This is separate from the Cloud Brain access keys. The Anthropic key is used
by the Biomni agent internally; it is never exposed through the API.

### Rate limiting

Cloud Brain applies per-key (or per-IP if no key) rate limits:

| Endpoint | Limit |
|----------|-------|
| `GET /brain/skills`, `/brain/tools`, `/brain/inventory`, `/brain/health` | 120 requests/minute |
| `POST /brain/execute` | 60 requests/minute |

Exceeding the limit returns HTTP **429 Too Many Requests**.

---

## 10. Python Client Example

Here is a minimal wrapper class you can drop into your project. It handles
the common patterns: authentication, error checking, and typed responses.

```python
"""cloud_brain.py -- Python client for LabClaw Cloud Brain."""

from __future__ import annotations

from typing import Any

import requests


class CloudBrain:
    """Thin client for the Cloud Brain API."""

    def __init__(
        self,
        base_url: str = "http://localhost:18802",
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        if api_key:
            self._session.headers["X-API-Key"] = api_key

    # -- Discovery --------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools."""
        return self._get("/brain/tools")

    def inventory(self) -> dict[str, Any]:
        """Get categorized inventory of skills and tools."""
        return self._get("/brain/inventory")

    def health(self) -> dict[str, bool]:
        """Health check all skill backends."""
        return self._get("/brain/health")

    # -- Execution --------------------------------------------------------

    def execute(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool by name. Returns the data field on success."""
        resp = self._post("/brain/execute", {
            "tool_name": tool_name,
            "arguments": kwargs,
        })
        if not resp.get("success"):
            raise RuntimeError(f"Tool {tool_name} failed: {resp.get('error')}")
        return resp.get("data", {})

    # -- Convenience methods ----------------------------------------------

    def search_pubmed(self, query: str, max_results: int = 10) -> Any:
        """Search PubMed for articles matching the query."""
        return self.execute(
            "tu_run",
            name="PubMed_search",
            arguments={"query": query, "max_results": max_results},
        )

    def get_protein(self, accession: str) -> Any:
        """Look up a UniProt protein by accession."""
        return self.execute(
            "tu_run",
            name="UniProt_get_entry_by_accession",
            arguments={"accession": accession},
        )

    def search_compound(self, query: str) -> Any:
        """Search ChEMBL for a compound by name."""
        return self.execute(
            "tu_run",
            name="ChEMBL_search_compound",
            arguments={"query": query},
        )

    def find_tools(self, description: str, limit: int = 5) -> Any:
        """Find tools by natural language description."""
        return self.execute(
            "tu_find_tools",
            description=description,
            limit=limit,
        )

    def ask_biomni(self, query: str) -> str:
        """Run a biomedical query through Biomni's autonomous agent."""
        result = self.execute("biomni_go", query=query)
        return result.get("result", "")

    def reason(self, question: str, domain: str = "general") -> str:
        """Ask a life science question with domain reasoning."""
        result = self.execute(
            "reason_lifesci",
            question=question,
            domain=domain,
        )
        return result.get("answer", result.get("note", ""))

    def design_experiment(
        self,
        hypothesis: str,
        constraints: str = "",
        equipment: list[str] | None = None,
    ) -> str:
        """Design an experiment for a hypothesis."""
        kwargs: dict[str, Any] = {"hypothesis": hypothesis}
        if constraints:
            kwargs["constraints"] = constraints
        if equipment:
            kwargs["available_equipment"] = equipment
        result = self.execute("design_experiment", **kwargs)
        return result.get("design", result.get("note", ""))

    def generate_section(
        self,
        section_type: str,
        findings: list[str] | None = None,
        context: str = "",
    ) -> str:
        """Generate a scientific text section."""
        kwargs: dict[str, Any] = {"section_type": section_type}
        if findings:
            kwargs["findings"] = findings
        if context:
            kwargs["data_context"] = context
        result = self.execute("generate_section", **kwargs)
        return result.get("text", "")

    # -- Internal ---------------------------------------------------------

    def _get(self, path: str) -> Any:
        resp = self._session.get(f"{self.base_url}{path}")
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict[str, Any]) -> Any:
        resp = self._session.post(f"{self.base_url}{path}", json=data)
        resp.raise_for_status()
        return resp.json()
```

### Using the client

```python
from cloud_brain import CloudBrain

brain = CloudBrain(api_key="sk-lab-abc123def456")

# Search literature
articles = brain.search_pubmed("CRISPR base editing 2024", max_results=5)

# Look up a protein
tp53 = brain.get_protein("P04637")

# Search for a drug
aspirin = brain.search_compound("aspirin")

# Ask a complex biomedical question
answer = brain.ask_biomni(
    "What are the known drug targets for Alzheimer's disease "
    "and which ones have active clinical trials?"
)

# Get domain reasoning
analysis = brain.reason(
    "Why does the C61G mutation in BRCA1 affect DNA repair?",
    domain="genomics",
)

# Design a follow-up experiment
plan = brain.design_experiment(
    hypothesis="BRCA1 C61G abolishes E3 ligase activity",
    constraints="Budget $5000, 2 weeks",
    equipment=["Western blot", "Cell culture", "Flow cytometer"],
)

# Generate a methods section
methods = brain.generate_section(
    "methods",
    findings=["Mutation reduces ubiquitination by 90%"],
    context="In vitro ubiquitination assay with purified BRCA1/BARD1",
)
print(methods)
```

---

## 11. Next Steps

**Explore what is available.** Run `GET /brain/inventory` and
`GET /brain/tools` to see every tool the server exposes. Use `tu_find_tools`
to search by what you want to do, not by database name.

**Check tool parameters.** Before calling a new tool, run `tu_get_spec` to
see its exact parameter schema. This avoids guessing argument names.

**Chain queries.** A typical workflow:

1. `tu_find_tools` -- find the right tool for your question
2. `tu_get_spec` -- check what parameters it needs
3. `tu_run` -- execute the tool with your data
4. `reason_lifesci` -- interpret the results with domain reasoning
5. `generate_section` -- draft a methods or results section

**Add your own data to Biomni.** Use `biomni_add_data` to load custom
datasets (e.g., your RNA-seq results), then ask questions against them
with `biomni_go`.

**Install additional backends.** Each backend you install unlocks more tools.
Check `GET /brain/health` to see which ones are active.

**Build pipelines.** The `CloudBrain` Python client makes it straightforward
to script multi-step analyses. Combine it with Jupyter notebooks for
interactive exploration, or with cron jobs for automated literature monitoring.

For the full API reference, see the auto-generated docs at:

```
http://localhost:18802/docs
```

FastAPI serves interactive Swagger UI documentation at that URL whenever the
server is running.
