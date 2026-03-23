# Cloud Brain User Guide

> One API to access 2,400+ scientific tools. No installation required.

---

## What is Cloud Brain?

Cloud Brain is LabClaw's unified API gateway for scientific AI tools. It aggregates
thousands of tools from multiple providers into a single REST API, so researchers
can query proteins, search literature, analyze drugs, and generate scientific text
without installing any specialized software.

**Tool sources:**

| Provider | Tools | Coverage |
|----------|-------|----------|
| [ToolUniverse](https://github.com/mims-harvard/ToolUniverse) | 2,000+ tools, 58 research skills | UniProt, ChEMBL, PubChem, OpenTargets, FAERS, ClinicalTrials, and 440+ more |
| [Biomni](https://github.com/snap-stanford/biomni) | 150+ tools across 59 databases | Autonomous biomedical AI agent for multi-step reasoning |
| [K-Dense AI](https://github.com/anthropics/claude-skills-mcp) | 170+ skills, 250+ databases | Bioinformatics, cheminformatics, clinical research, lab automation |
| LifeSci MCP | 5 specialized servers | PubMed, bioRxiv, ChEMBL, OpenTargets, ClinicalTrials.gov |
| LifeSci Reasoning | 2 tools | Domain expert reasoning and experiment design |
| Scientific Writing | 2 tools | Paper section generation and citation formatting |

**Key benefits:**

- **No installation** -- everything runs server-side. You send HTTP requests and get JSON back.
- **One endpoint for everything** -- `POST /brain/execute` runs any of the 2,400+ tools.
- **Tool discovery** -- search tools by description or browse by category.
- **Rate-limited and safe** -- built-in request throttling and response size limits.

---

## Quick Start

### Step 1: Open the Dashboard

Navigate to [brain.labclaw.org](https://brain.labclaw.org) in your browser. The
dashboard shows the Cloud Brain status and provides links to the Tool Explorer,
Query Playground, and API documentation.

### Step 2: Try a Quick Query

The fastest way to test Cloud Brain is with a `curl` command. Look up a protein
by its UniProt accession number:

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "UniProt_get_entry_by_accession",
      "arguments": {"accession": "P04637"}
    }
  }' | python3 -m json.tool
```

You should receive a JSON response containing the full UniProt entry for human
tumor protein p53 (TP53).

### Step 3: Explore Tools by Category

List all available tool categories:

```bash
curl -s https://brain.labclaw.org/brain/tools | python3 -m json.tool
```

Or get a structured inventory with per-category counts:

```bash
curl -s https://brain.labclaw.org/brain/inventory | python3 -m json.tool
```

### Step 4: Find Tools by Description

Don't know the exact tool name? Use natural language search:

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_find_tools",
    "arguments": {
      "description": "protein structure prediction",
      "limit": 5
    }
  }' | python3 -m json.tool
```

---

## Available Tools

Cloud Brain exposes tools through five registered skills. Each skill provides
multiple tools accessible via `POST /brain/execute`.

### ToolUniverse (2,000+ tools)

The largest collection, covering databases across genomics, proteomics, drug
discovery, clinical research, and more. All ToolUniverse tools are accessed
through the `tu_run` wrapper.

#### Protein & Genomics

| Tool Name | Description |
|-----------|-------------|
| `UniProt_get_entry_by_accession` | Full protein entry (function, sequence, structure, GO terms) |
| `UniProt_get_function_by_accession` | Protein function annotation |
| `UniProt_get_sequence_by_accession` | Amino acid sequence in FASTA format |
| `NCBI_gene_search` | Search NCBI Gene database |
| `Ensembl_get_sequence` | Retrieve genomic/transcript/protein sequences |
| `AlphaFold_get_prediction` | AlphaFold protein structure prediction |
| `STRING_get_interactions` | Protein-protein interaction networks |
| `BioGRID_search_interactions` | Protein interaction data from BioGRID |

**Example -- get protein function:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "UniProt_get_function_by_accession",
      "arguments": {"accession": "P04637"}
    }
  }'
```

#### Drug Discovery & Pharmacology

| Tool Name | Description |
|-----------|-------------|
| `ChEMBL_search_molecule` | Search molecules by name or structure |
| `ChEMBL_get_molecule` | Detailed molecule information |
| `PubChem_search_compound` | Search PubChem compound database |
| `PubChem_get_compound` | Compound properties, synonyms, and structure |
| `DrugBank_search` | DrugBank drug information |
| `ADMETAI_predict` | ADMET property prediction for drug candidates |
| `OpenTargets_search_target` | Drug target validation data |
| `OpenTargets_search_drug` | Drug-disease association evidence |

**Example -- search for a molecule:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "ChEMBL_search_molecule",
      "arguments": {"query": "aspirin"}
    }
  }'
```

#### Clinical Research

| Tool Name | Description |
|-----------|-------------|
| `ClinicalTrials_search` | Search ClinicalTrials.gov |
| `ClinicalTrials_get_study` | Full clinical trial record |
| `FAERS_search_events` | FDA adverse event reports |
| `GWAS_Catalog_search` | GWAS Catalog variant-trait associations |
| `ClinVar_search_variant` | Clinical significance of genetic variants |
| `OMIM_search` | Online Mendelian Inheritance in Man |

#### Literature & Knowledge

| Tool Name | Description |
|-----------|-------------|
| `SemanticScholar_search` | Semantic Scholar paper search |
| `EuropePMC_search` | Europe PMC literature search |
| `ArXiv_search` | arXiv preprint search |
| `Reactome_get_pathway` | Reactome pathway data |
| `KEGG_get_pathway` | KEGG pathway maps |
| `WikiPathways_search` | WikiPathways community pathways |

#### Additional Categories

ToolUniverse covers 440+ tool configurations spanning:

- **Genomics**: NCBI, Ensembl, UCSC Genome Browser, ENCODE, JASPAR
- **Proteomics**: PDB, PDBe, InterPro, Pfam, CATH
- **Imaging**: Allen Brain Atlas, microscopy analysis
- **Metabolomics**: HMDB, MetaboLights, KEGG Compound
- **Immunology**: IEDB, IMGT, TCR/BCR repertoire analysis
- **Rare diseases**: Orphanet, OMIM, ClinGen

Use `tu_find_tools` or `tu_list_categories` to discover all available tools.

### Biomni (150+ tools)

Stanford SNAP's autonomous biomedical AI agent. Unlike individual tool calls,
Biomni handles multi-step reasoning chains automatically.

| Tool Name | Description |
|-----------|-------------|
| `biomni_go` | Run a biomedical query through the autonomous agent |
| `biomni_list_tools` | List all custom tools in the Biomni agent |
| `biomni_add_data` | Add custom datasets for Biomni to analyze |

**Example -- autonomous biomedical query:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "biomni_go",
    "arguments": {
      "query": "What are the known drug targets for glioblastoma and which approved drugs interact with them?"
    }
  }'
```

> **Note:** Biomni requires `ANTHROPIC_API_KEY` to be configured on the server.
> Queries may take up to 120 seconds for complex multi-step reasoning.

### K-Dense AI (170+ skills)

Scientific skills accessed via MCP protocol, covering bioinformatics,
cheminformatics, clinical research, ML/AI, and lab automation.

| Tool Name | Description |
|-----------|-------------|
| `kdense_find_skills` | Search for relevant scientific skills by description |
| `kdense_read_skill` | Read the full content of a skill document with code examples |
| `kdense_list_skills` | List all available K-Dense skills |

**Example -- find skills for a task:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "kdense_find_skills",
    "arguments": {
      "description": "CRISPR guide RNA design",
      "limit": 3
    }
  }'
```

### Life Science MCP Tools

Direct access to biomedical databases through dedicated MCP servers.

| Tool Name | Description | Source |
|-----------|-------------|-------|
| `lifesci_search_pubmed` | Search PubMed for biomedical literature | PubMed |
| `lifesci_search_biorxiv` | Search bioRxiv/medRxiv for preprints | bioRxiv |
| `lifesci_query_chembl` | Query ChEMBL for drug compound data | ChEMBL |
| `lifesci_query_opentargets` | Disease-gene-drug associations | OpenTargets |
| `lifesci_search_clinical_trials` | Search ClinicalTrials.gov | ClinicalTrials.gov |

**Example -- search PubMed:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "lifesci_search_pubmed",
    "arguments": {
      "query": "single cell RNA-seq neurodegeneration 2025",
      "max_results": 5
    }
  }'
```

### AI Reasoning & Writing

Domain-expert reasoning and scientific text generation.

| Tool Name | Description |
|-----------|-------------|
| `reason_lifesci` | Life science expert reasoning on biological questions |
| `design_experiment` | Design rigorous experiments with controls, sample sizes, and protocols |
| `generate_section` | Generate paper sections (abstract, methods, results, discussion, summary) |
| `format_citation` | Format citations in APA or other styles |

**Example -- generate an abstract:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "generate_section",
    "arguments": {
      "section_type": "abstract",
      "findings": [
        "RNA-seq revealed 342 differentially expressed genes in treatment vs control",
        "GO enrichment showed significant upregulation of immune response pathways",
        "Three novel biomarker candidates identified with AUC > 0.92"
      ],
      "data_context": "Murine glioblastoma model, n=12 per group, FDR < 0.05"
    }
  }'
```

**Example -- format a citation:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "format_citation",
    "arguments": {
      "title": "ToolUniverse: A Framework for AI Scientists",
      "authors": ["Gao S.", "Huang K.", "Zitnik M."],
      "year": 2025,
      "journal": "Nature Methods",
      "doi": "10.1038/s41592-025-xxxxx",
      "style": "apa"
    }
  }'
```

---

## API Reference

### Base URL

```
https://brain.labclaw.org
```

For local development:

```
http://localhost:18802
```

(Launch locally with `labclaw brain` or `labclaw brain --port 8000`.)

### Authentication

Cloud Brain uses API key authentication via the `X-API-Key` header. When no
keys are configured on the server (`LABCLAW_API_KEYS` env var is empty), the
API runs in **open access mode** -- no key is required.

```bash
# With authentication enabled
curl -H "X-API-Key: your-key-here" https://brain.labclaw.org/brain/skills

# Open access mode (no key needed)
curl https://brain.labclaw.org/brain/skills
```

### Endpoints

#### `GET /brain/skills`

List all registered skill providers with their metadata.

**Request:**

```bash
curl -s https://brain.labclaw.org/brain/skills
```

**Response:**

```json
[
  {
    "name": "tooluniverse",
    "version": "0.2.0",
    "description": "2000+ scientific tools via ToolUniverse SDK: UniProt, ChEMBL, PubChem, OpenTargets, ClinicalTrials, and more.",
    "capabilities": ["instrument_knowledge", "data_analysis", "literature_search"],
    "author": "labclaw-core",
    "requires_api_key": false,
    "api_key_env": ""
  },
  {
    "name": "biomni",
    "version": "0.2.0",
    "description": "Stanford SNAP Biomni: autonomous biomedical AI agent with 150+ tools across 59 databases.",
    "capabilities": ["data_analysis", "general_reasoning", "hypothesis_generation"],
    "author": "labclaw-core",
    "requires_api_key": true,
    "api_key_env": "ANTHROPIC_API_KEY"
  },
  {
    "name": "kdense",
    "version": "0.2.0",
    "description": "K-Dense AI: 170+ scientific skills, 250+ databases.",
    "capabilities": ["literature_search", "general_reasoning", "instrument_knowledge"],
    "author": "labclaw-core",
    "requires_api_key": false,
    "api_key_env": ""
  },
  {
    "name": "write",
    "version": "0.1.0",
    "description": "Scientific writing: abstracts, methods, results, discussions, citations.",
    "capabilities": ["scientific_writing"],
    "author": "labclaw-core",
    "requires_api_key": false,
    "api_key_env": ""
  },
  {
    "name": "lifesci",
    "version": "0.1.0",
    "description": "Life science domain reasoning, experiment design, and biological analysis.",
    "capabilities": ["hypothesis_generation", "general_reasoning"],
    "author": "labclaw-core",
    "requires_api_key": false,
    "api_key_env": ""
  }
]
```

#### `GET /brain/tools`

List all individual tools across all skills with their parameter schemas.

**Request:**

```bash
curl -s https://brain.labclaw.org/brain/tools
```

**Response (truncated):**

```json
[
  {
    "name": "tu_run",
    "description": "Execute any ToolUniverse tool by name. 2000+ tools: UniProt, ChEMBL, PubChem, OpenTargets, FAERS, ClinicalTrials, etc.",
    "parameters": {
      "name": {
        "type": "string",
        "description": "Tool name (e.g. UniProt_get_entry_by_accession)"
      },
      "arguments": {
        "type": "object",
        "description": "Tool arguments as key-value pairs"
      }
    }
  },
  {
    "name": "tu_find_tools",
    "description": "Find relevant scientific tools by description. Searches 2000+ tools by keyword matching.",
    "parameters": {
      "description": {
        "type": "string",
        "description": "What you need the tool to do"
      },
      "limit": {
        "type": "integer",
        "description": "Max results (default 5)"
      }
    }
  }
]
```

#### `GET /brain/health`

Health check all registered skills. Returns a map of skill names to health status.

**Request:**

```bash
curl -s https://brain.labclaw.org/brain/health
```

**Response:**

```json
{
  "tooluniverse": true,
  "biomni": false,
  "kdense": true,
  "write": true,
  "lifesci": false
}
```

A `false` value indicates the skill's backend is unreachable (e.g., missing API
key, MCP server not installed, or LLM provider not configured).

#### `POST /brain/execute`

Execute any tool by name. This is the primary endpoint for running scientific queries.

**Request:**

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_run",
    "arguments": {
      "name": "PubChem_search_compound",
      "arguments": {"query": "ibuprofen"}
    }
  }'
```

**Request body schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_name` | string | Yes | Name of the tool to execute (from `GET /brain/tools`) |
| `arguments` | object | No | Key-value arguments for the tool (default: `{}`) |

**Response:**

```json
{
  "success": true,
  "data": {
    "cid": 3672,
    "iupac_name": "2-[4-(2-methylpropyl)phenyl]propanoic acid",
    "molecular_formula": "C13H18O2",
    "molecular_weight": 206.28
  },
  "error": ""
}
```

**Error response (tool not found):**

```json
{
  "success": false,
  "data": null,
  "error": "Tool 'nonexistent_tool' not found"
}
```

**Error response (execution failure):**

```json
{
  "success": false,
  "data": null,
  "error": "UniProt API returned 404 for accession XXXXX"
}
```

#### `GET /brain/inventory`

Full inventory with per-capability categories and tool counts.

**Request:**

```bash
curl -s https://brain.labclaw.org/brain/inventory
```

**Response:**

```json
{
  "total_skills": 5,
  "total_tools": 16,
  "categories": [
    {
      "capability": "data_analysis",
      "skill_count": 2,
      "tool_count": 7,
      "skills": ["biomni", "tooluniverse"]
    },
    {
      "capability": "general_reasoning",
      "skill_count": 3,
      "tool_count": 8,
      "skills": ["biomni", "kdense", "lifesci"]
    },
    {
      "capability": "hypothesis_generation",
      "skill_count": 2,
      "tool_count": 5,
      "skills": ["biomni", "lifesci"]
    },
    {
      "capability": "instrument_knowledge",
      "skill_count": 2,
      "tool_count": 7,
      "skills": ["kdense", "tooluniverse"]
    },
    {
      "capability": "literature_search",
      "skill_count": 2,
      "tool_count": 7,
      "skills": ["kdense", "tooluniverse"]
    },
    {
      "capability": "scientific_writing",
      "skill_count": 1,
      "tool_count": 2,
      "skills": ["write"]
    }
  ]
}
```

### Code Examples

#### Python

```python
import requests

BASE_URL = "https://brain.labclaw.org"

# Optional: set API key if authentication is enabled
HEADERS = {
    "Content-Type": "application/json",
    # "X-API-Key": "your-key-here",
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a Cloud Brain tool and return the result."""
    response = requests.post(
        f"{BASE_URL}/brain/execute",
        headers=HEADERS,
        json={"tool_name": tool_name, "arguments": arguments},
    )
    response.raise_for_status()
    return response.json()


# Example 1: Look up a protein
result = execute_tool("tu_run", {
    "name": "UniProt_get_entry_by_accession",
    "arguments": {"accession": "P04637"},
})
print(result["data"])


# Example 2: Search PubMed
result = execute_tool("lifesci_search_pubmed", {
    "query": "CRISPR base editing 2025",
    "max_results": 5,
})
print(result["data"])


# Example 3: Generate a methods section
result = execute_tool("generate_section", {
    "section_type": "methods",
    "findings": ["Western blot analysis of p53 expression"],
    "data_context": "HEK293T cells, 48h post-transfection",
})
print(result["data"]["text"])


# Example 4: Find tools for a task
result = execute_tool("tu_find_tools", {
    "description": "gene ontology enrichment analysis",
    "limit": 3,
})
print(result["data"])
```

#### JavaScript (Node.js / Browser `fetch`)

```javascript
const BASE_URL = "https://brain.labclaw.org";

async function executeTool(toolName, args = {}) {
  const response = await fetch(`${BASE_URL}/brain/execute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // "X-API-Key": "your-key-here",
    },
    body: JSON.stringify({
      tool_name: toolName,
      arguments: args,
    }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// Look up a protein
const protein = await executeTool("tu_run", {
  name: "UniProt_get_entry_by_accession",
  arguments: { accession: "P04637" },
});
console.log(protein.data);

// Search for drugs
const drugs = await executeTool("tu_run", {
  name: "ChEMBL_search_molecule",
  arguments: { query: "aspirin" },
});
console.log(drugs.data);

// List all skills
const skills = await fetch(`${BASE_URL}/brain/skills`);
console.log(await skills.json());
```

#### cURL

```bash
# List all skills
curl -s https://brain.labclaw.org/brain/skills | python3 -m json.tool

# List all tools
curl -s https://brain.labclaw.org/brain/tools | python3 -m json.tool

# Health check
curl -s https://brain.labclaw.org/brain/health

# Execute a ToolUniverse tool
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "tu_run", "arguments": {"name": "PubChem_get_compound", "arguments": {"cid": "2244"}}}'

# Run Biomni autonomous query
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "biomni_go", "arguments": {"query": "Find approved drugs targeting EGFR"}}'

# Search K-Dense skills
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "kdense_find_skills", "arguments": {"description": "protein docking", "limit": 3}}'

# Get full inventory
curl -s https://brain.labclaw.org/brain/inventory | python3 -m json.tool
```

---

## Rate Limits

Cloud Brain enforces per-client rate limits to ensure fair access.

| Endpoint Type | Rate Limit |
|---------------|------------|
| GET endpoints (`/brain/skills`, `/brain/tools`, `/brain/health`, `/brain/inventory`) | 120 requests/minute |
| POST endpoints (`/brain/execute`) | 60 requests/minute |

Rate limiting is applied per API key (if authentication is enabled) or per IP
address (in open access mode).

When you exceed the limit, you receive a `429 Too Many Requests` response:

```json
{"detail": "Rate limit exceeded"}
```

**Request size limits:**

| Limit | Value |
|-------|-------|
| Maximum request body | 1 MB |
| Maximum response body (before truncation) | 100 KB |

Responses exceeding 100 KB are automatically truncated. The response will include
a `truncated: true` flag and a `preview` field with the first 100 KB of data.

---

## FAQ

### What data formats are returned?

All responses are JSON. The `POST /brain/execute` endpoint returns a consistent
envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": ""
}
```

The structure inside `data` depends on the specific tool. ToolUniverse tools
return whatever the upstream API provides (protein records, molecule data,
pathway maps, etc.). Writing tools return `{"text": "...", "section_type": "..."}`.

### Is there a size limit on responses?

Yes. Responses larger than 100 KB are automatically truncated. If you need the
full response for a data-heavy query, consider narrowing your query parameters
(e.g., requesting specific fields rather than full records).

### Which tools require API keys?

Most tools work without API keys:

| Skill | Requires API Key | Key Variable |
|-------|-----------------|--------------|
| ToolUniverse | No | -- |
| K-Dense AI | No | -- |
| Scientific Writing | No | -- |
| Life Science MCP | No | -- |
| **Biomni** | **Yes** | `ANTHROPIC_API_KEY` |
| **LifeSci Reasoning** | **Yes** (for LLM) | `ANTHROPIC_API_KEY` |

Biomni and LifeSci reasoning tools require an Anthropic API key configured on
the server. If the key is not set, these tools return a descriptive error.

### How long do queries take?

| Tool Type | Typical Latency | Timeout |
|-----------|----------------|---------|
| ToolUniverse tools | 1-10 seconds | 30 seconds |
| K-Dense skills | 2-10 seconds | 30 seconds |
| Life Science MCP | 2-15 seconds | 30 seconds |
| Biomni autonomous queries | 10-60 seconds | 120 seconds |
| Writing / Citation | < 2 seconds | 30 seconds |

### How do I get the parameter schema for a specific ToolUniverse tool?

Use `tu_get_spec` to retrieve the OpenAI function-calling format schema for
any ToolUniverse tool:

```bash
curl -s https://brain.labclaw.org/brain/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "tu_get_spec",
    "arguments": {"tool_name": "UniProt_get_entry_by_accession"}
  }'
```

### How do I report bugs?

Open an issue on the [LabClaw GitHub repository](https://github.com/labclaw/labclaw)
with the label `cloud-brain`. Include:

1. The exact request you sent (sanitize any API keys).
2. The response you received.
3. What you expected to happen.

### Can I run Cloud Brain locally?

Yes. Install LabClaw and start the server:

```bash
pip install labclaw
labclaw brain --port 8000
```

Then use `http://localhost:8000` as your base URL. For production deployment
with Cloudflare Tunnel, see `deploy/cloud-brain/` in the repository.

### What are the available skill capabilities?

Cloud Brain organizes tools by scientific loop step:

| Capability | Description | Skills |
|------------|-------------|--------|
| `literature_search` | Find and retrieve scientific literature | ToolUniverse, K-Dense |
| `hypothesis_generation` | Generate and evaluate scientific hypotheses | Biomni, LifeSci |
| `instrument_knowledge` | Lab instrument and tool expertise | ToolUniverse, K-Dense |
| `data_analysis` | Analyze experimental data | ToolUniverse, Biomni |
| `scientific_writing` | Generate papers, reports, citations | Write |
| `general_reasoning` | Domain expert reasoning | Biomni, K-Dense, LifeSci |

### Is CORS enabled?

Yes. Cloud Brain allows cross-origin requests from any origin with `GET` and
`POST` methods. The `Content-Type` and `X-API-Key` headers are permitted.
This means you can call the API directly from browser-based applications.
