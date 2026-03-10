# LabClaw Roadmap

LabClaw's core architecture is **domain-agnostic** — the plugin system supports any science domain through `DomainPlugin`. This document outlines the release plan and domain expansions.

## Release Plan

### v0.0.10 — Foundation ✅
- 5-layer architecture (Hardware → Platform → Engine → Memory → Persona)
- 7-step scientific method loop (OBSERVE → ASK → HYPOTHESIZE → PREDICT → EXPERIMENT → ANALYZE → CONCLUDE)
- Event-driven architecture with in-memory bus
- Plugin protocols (DevicePlugin, DomainPlugin, AnalysisPlugin)
- MCP server (labclaw-mcp)
- REST API (FastAPI, port 18800)
- 100% test coverage enforced

### v0.0.11 — Agentic Steps ✅
- LLM-backed ConcludeStep (natural-language synthesis with template fallback)
- LLM-backed ExperimentStep (LLM evaluates Bayesian proposals against domain knowledge)
- Unified OrchestratorConfig (max_llm_calls, seed, skip_steps)
- CLI `--llm` / `--no-llm` toggle

### v0.0.14 — Persistent Knowledge Graph ✅
- SQLiteTierBBackend as default (FTS5 search, restart survival)
- Past findings feed into HypothesizeStep via context_findings
- Pattern deduplication in AskStep
- Memory search API (findings, KG nodes, KG neighbors)

### v0.0.12 — Plugin Wiring ✅
- Plugin → Sentinel translation layer
- Sentinels wired into ObserveStep
- Plugin hypothesis templates wired into HypothesisGenerator
- Plugin lifecycle management in daemon
- Functional neuroscience plugin (DomainPlugin + AnalysisPlugin)
- Plugin CLI scaffold (`labclaw plugin create`)

### v0.0.13 — MCP Client & Agent Bridge (current)
- **MCP client**: bidirectional MCP — LabClaw as both server and client
- **MCP tool adapter**: convert external MCP tool schemas → AgentTool instances
- **ToolUniverse integration**: 1000+ scientific tools via Compact Mode (4 meta-tools)
- **BioMCP integration**: pre-configured PubMed, ClinicalTrials, MyVariant, MyGene access
- **OrchestratorAgent**: LLM decides when to call external tools during the scientific loop
- **Plugin-to-MCP exposure**: auto-register plugin capabilities as MCP server tools

### v0.0.15 — Publish & Stabilize
- PyPI release: `pip install labclaw[science,memory,llm]`
- Docker on GHCR (multi-platform amd64/arm64)
- Crash recovery (daemon state persistence)
- SQLite schema versioning + migrations
- MkDocs documentation site
- 1-hour CI soak test

### v0.0.16 — Scientific Tool Ecosystem
- **K-Dense scientific skills bridge**: 170+ Claude-optimized skills as LabClaw plugins
- **Lab automation adapters**: Opentrons MCP, SiLA2 protocol bridge
- **BayBE optimization plugin**: Bayesian optimization for chemistry/materials (Merck, Apache 2.0)
- **Tool registry + marketplace API**: unified tool discovery across internal + MCP + ToolUniverse
- **Multi-agent data scientist**: parallel sub-agent analysis during AnalyzeStep
- **Tool usage memory**: track tool success rates, feed into self-evolution engine

---

## MCP Ecosystem Integration

LabClaw connects to the growing ecosystem of scientific MCP servers:

| MCP Server | Tools | Integration |
|------------|-------|-------------|
| **ToolUniverse** (Harvard MIMS) | 1000+ scientific tools | Compact Mode meta-tools |
| **BioMCP** | PubMed, ClinicalTrials, MyVariant, MyGene | Literature + variant search |
| **Holy Bio MCP** | KEGG, UniProt, PDB, BLAST | Structural biology + pathways |
| **Opentrons MCP** | Liquid handler automation | Lab hardware control |
| **BioContextAI** | 45+ registries (GEO, ENCODE, ClinVar) | Multi-database queries |
| **claude-skills-mcp** (K-Dense) | 170+ scientific skills | Semantic skill discovery |

---

## Domain Plugin Architecture

Each domain plugin provides:

```python
class DomainPlugin(Protocol):
    metadata: PluginMetadata

    def get_sample_node_types(self) -> dict[str, type]: ...
    def get_sentinel_rules(self) -> list[dict[str, Any]]: ...
    def get_hypothesis_templates(self) -> list[dict[str, Any]]: ...
```

A new domain = **< 100 lines** of Python to define sample types, safety rules, and analysis defaults.

## Planned Domains

### Tier 1 — Near-term (v0.1.x)

| Domain | Key Instruments | Data Types | Status |
|--------|----------------|------------|--------|
| **Neuroscience** | Two-photon, EEG, behavioral rigs | TIFF, NWB, CSV, video | **Built** |
| **Molecular Biology** | qPCR, gel imager, plate reader | CSV, TIFF, absorbance | **Partial** |
| **Chemistry** | Spectrometers, HPLC, LC-MS | CSV, mzML, JCAMP-DX | Planned |
| **Materials Science** | SEM, XRD, tensile testing | TIFF, CSV, CIF | Planned |

### Tier 2 — Mid-term (v0.2.x)

| Domain | Key Instruments | Data Types |
|--------|----------------|------------|
| **Genomics/Bioinformatics** | Sequencers, flow cytometers | FASTQ, BAM, FCS |
| **Medical/Clinical** | Imaging, lab analyzers | DICOM, HL7/FHIR, CSV |
| **Cell Biology** | Confocal, flow cytometry, incubators | TIFF, FCS, time-lapse |
| **Pharmacology** | Plate readers, dose-response | CSV, dose-response curves |

### Tier 3 — Long-term (v1.0+)

| Domain | Key Instruments | Data Types |
|--------|----------------|------------|
| **Physics** | Oscilloscopes, laser systems | HDF5, ROOT, CSV |
| **Environmental Science** | Weather stations, water samplers | NetCDF, CSV, GeoJSON |
| **Robotics/AI** | Robot arms, sensors, cameras | ROS bags, video, telemetry |
| **Agriculture** | Soil sensors, drone imaging | GeoTIFF, CSV, multispectral |

## Domain-Specific Features

### Neuroscience (built)

```
labclaw-neuro plugin:
├── AnimalSampleNode (species, strain, age, sex)
├── Sentinel rules (behavioral thresholds, neural activity alerts)
├── Hypothesis templates (neural correlates, behavioral patterns)
├── Device drivers (two-photon TIFF, Olympus BX, behavioral video)
└── Analysis defaults (spike sorting params, behavioral metrics)
```

### Chemistry (planned)

```
labclaw-chem plugin:
├── ReactionSampleNode (reagents, conditions, yield)
├── Sentinel rules (yield thresholds, safety alerts, temperature limits)
├── Hypothesis templates (structure-activity, reaction optimization)
├── Device drivers (HPLC CSV, spectrophotometer, balance)
└── Analysis defaults (peak detection, concentration curves)
```

### Materials Science (planned)

```
labclaw-materials plugin:
├── MaterialSampleNode (composition, processing, properties)
├── Sentinel rules (property thresholds, phase transition alerts)
├── Hypothesis templates (composition-property, processing-structure)
├── Device drivers (SEM TIFF, XRD CSV, tensile CSV)
└── Analysis defaults (peak fitting, stress-strain analysis)
```

### Genomics (planned)

```
labclaw-genomics plugin:
├── SequencingSampleNode (organism, library type, coverage)
├── Sentinel rules (quality scores, contamination alerts)
├── Hypothesis templates (differential expression, variant effects)
├── Device drivers (Illumina output, 10x Genomics, Nanopore)
└── Analysis defaults (QC thresholds, alignment params)
```

## Creating a Domain Plugin

```bash
# Scaffold a new domain plugin
labclaw plugin create my-domain --type domain

# Structure:
labclaw-my-domain/
├── pyproject.toml          # entry_points for labclaw.plugins.domain
├── src/
│   └── labclaw_my_domain/
│       ├── __init__.py     # DomainPlugin implementation
│       ├── nodes.py        # Custom GraphNode subclasses
│       ├── rules.py        # Sentinel rules
│       └── drivers/        # Device drivers (optional)
└── tests/
```

```python
# Minimal domain plugin (~50 lines)
from labclaw.plugins.base import PluginMetadata

class MyDomainPlugin:
    metadata = PluginMetadata(
        name="labclaw-my-domain",
        version="0.1.0",
        description="My science domain for LabClaw",
        plugin_type="domain",
    )

    def get_sample_node_types(self):
        return {"my_sample": MySampleNode}

    def get_sentinel_rules(self):
        return [{"name": "quality_check", "condition": {...}}]

    def get_hypothesis_templates(self):
        return [{"template": "If {condition}, then {outcome}", "required_evidence": ["correlation"]}]
```

## Community Contribution Model

```
Phase 1: Core team builds 3-4 domain packs (neuro, chem, bio, materials)
Phase 2: Template + docs enable community domain contributions
Phase 3: Domain Plugin Hub — searchable registry of community plugins
Phase 4: Cross-domain analysis — LabClaw finds patterns ACROSS domains
```

## Cross-Domain Discovery (v1.0+ vision)

The ultimate power of LabClaw: a lab running both chemistry and biology experiments where LabClaw discovers that a chemical compound (from chemistry data) correlates with a biological response (from biology data) — a cross-domain insight that siloed tools would never find.

```
Chemistry data ──┐
                 ├──► LabClaw Knowledge Graph ──► Cross-domain patterns
Biology data ────┘
```

This requires:
1. Shared knowledge graph (Tier B) across domains
2. Domain-aware embedding for cross-domain similarity
3. LLM-powered cross-domain hypothesis generation

## Contributing a Domain

See [plugin-development.md](plugin-development.md) for the full plugin development guide.

1. Fork the repo
2. `labclaw plugin create your-domain --type domain`
3. Implement `DomainPlugin` protocol
4. Add sample data + tests
5. Submit PR

We welcome domain experts who want to bring LabClaw to their field.
