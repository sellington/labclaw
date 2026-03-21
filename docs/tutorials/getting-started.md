# Getting Started for Scientists — From Raw Data to First Discovery

You have CSV files from your behavioral tracking experiments -- DeepLabCut
output, open-field locomotion data, trial-by-trial performance logs. You want
to find patterns you might have missed and keep a running record of what your
lab has learned. This tutorial walks you through that.

---

## What You'll Learn

- Install LabClaw and run a built-in demo to see the system in action
- Point LabClaw at your own data and get automatic pattern discovery
- Query accumulated knowledge and export findings in standard formats
- Run a single analysis cycle or leave the system running continuously

If you can open a terminal and type `pip install`, you have everything you
need.

---

## Prerequisites

You need two things:

1. **Python 3.11 or newer.** Check with `python --version`. If needed,
install from [python.org](https://www.python.org/downloads/) or via your
package manager (`brew install python@3.12` / `sudo apt install python3.12`).

2. **pip** (Python's package installer). Ships with Python by default. Verify
with `pip --version`.

That is it. No Docker, no database servers, no cloud accounts.

---

## Installation

The basics:

```bash
pip install labclaw
```

This gives you the CLI, the discovery engine, the memory system, and the REST
API. For scientific analysis (numpy, scipy, scikit-learn), add the `science`
extra:

```bash
pip install "labclaw[science]"
```

LabClaw has optional feature bundles ("extras") you can mix and match:

| Extra | What it installs | When you need it |
|-------|-----------------|------------------|
| `science` | numpy, scipy, scikit-learn, scikit-optimize, umap-learn | You want statistical analysis and dimensionality reduction |
| `nwb` | pynwb, hdmf, neuroconv | You want to export findings in Neurodata Without Borders format |
| `memory` | graphiti-core, sentence-transformers | You want semantic search over your lab's accumulated knowledge |

You can install multiple extras at once:

```bash
pip install "labclaw[science,nwb,memory]"
```

Verify the installation by running `labclaw` with no arguments. You should
see a list of available commands. If you get `command not found`, try
`python -m labclaw` instead.

---

## Your First Run: The Demo

Before touching your own data, let's see what LabClaw does with sample data.
The demo needs no API keys, no configuration, and no internet connection.

### Run the neuroscience demo

```bash
labclaw demo --domain neuroscience
```

This command creates a temporary workspace, loads a built-in dataset of
behavioral tracking data (200 rows of trial data from 4 animals), and runs a
complete analysis cycle.

### What happens during the demo

The demo runs four steps in sequence. Watch the terminal output as each one
completes:

**Step 1 -- Data Ingestion.** LabClaw reads the CSV file and detects its
columns automatically. No schema file, no column mapping. It finds columns
like `animal_id`, `trial_num`, `stimulus_hz`, `response_latency_ms`,
`velocity_cm_s`, `freezing_pct`, and others. Numeric columns are identified
for analysis; categorical columns (like `stimulus_type` and `zone`) are noted
for grouping.

**Step 2 -- Pattern Mining.** The system scans all pairs of numeric columns
looking for correlations, anomalies, and temporal trends. For example, it
might find that higher stimulus frequency correlates with shorter response
latency (r > 0.6), or that one animal (M003) has systematically different
behavior from the rest.

**Step 3 -- Scientific Method Cycle.** This is the core of LabClaw. It runs a
7-step loop modeled on the scientific method:

1. **Observe** -- Summarize the incoming data
2. **Ask** -- Generate research questions from detected patterns
3. **Hypothesize** -- Formulate testable hypotheses
4. **Predict** -- Build predictive models with uncertainty estimates
5. **Experiment** -- Propose what to try next (via Bayesian optimization)
6. **Analyze** -- Extract features and compute statistics
7. **Conclude** -- Run statistical validation and generate a report

Each step logs what it found. The cycle typically completes in a few seconds
on the demo data.

**Step 4 -- Evolution.** LabClaw evaluates how well the current analysis
performed and proposes improvements. It measures a fitness score based on how
many patterns it found and how much of the data those patterns cover. Then it
generates a candidate configuration (for instance, adjusting the minimum
number of sessions required before declaring a pattern significant), tests
that candidate, and promotes it if it performs better.

### Keeping the workspace

By default, the demo cleans up its temporary files. To inspect the results,
add `--keep`:

```bash
labclaw demo --domain neuroscience --keep
```

The output tells you where the workspace lives (`/tmp/labclaw-demo-XXXXXXXX/`)
containing the sample CSV and the generated `evolution_state.json`.

### Other demo domains

```bash
labclaw demo --domain neuroscience   # animal behavior trials
labclaw demo --domain chemistry      # reaction yields and conditions
labclaw demo                         # generic tabular data (default)
```

---

## Analyzing Your Own Data

### Create a project

```bash
labclaw init my-behavior-study
cd my-behavior-study
```

This creates a clean project structure:

```
my-behavior-study/
  configs/default.yaml     # configuration (LLM provider, ports, intervals)
  data/                    # put your data files here
  lab/
    SOUL.md              # describe your lab's identity and goals
    MEMORY.md            # LabClaw writes its accumulated knowledge here
```

### Describe your lab

Open `lab/SOUL.md` in any text editor and describe what your lab does. This
helps LabClaw generate hypotheses that make sense for your domain:

```markdown
# Behavioral Neuroscience Lab

## Identity

We study decision-making and motor learning in freely moving mice.

## Current Focus

Open-field locomotion under varying stimulus conditions (tone, light,
combined). Four cohorts, 50 trials per animal.

## Protocols

- Open-field tracking at 30 fps using DeepLabCut
- Stimulus delivery via Arduino-controlled speakers and LEDs
- Trial duration: 60 seconds, inter-trial interval: 120 seconds
```

Write whatever helps an AI assistant understand your work -- no formal
structure required.

### Add your data

Copy your CSV files into the `data/` directory:

```bash
cp /path/to/session_001.csv data/
cp /path/to/session_002.csv data/
cp /path/to/session_003.csv data/
```

Any CSV or TSV with numeric columns works -- no required column names, no
special formatting. A typical behavioral tracking CSV might look like this:

```
animal_id,trial,stimulus_type,stimulus_hz,latency_ms,velocity_cm_s,distance_cm,freezing_pct
M001,1,tone,4000,263.7,9.86,88.2,7.9
M001,2,light,8000,229.3,13.70,140.7,7.7
M001,3,tone_light,12000,184.4,16.21,286.6,6.0
...
```

### Start the daemon

```bash
labclaw serve --data-dir ./data --memory-root ./lab
```

This starts LabClaw's background services:

| Service | What it does |
|---------|-------------|
| **File Watcher** | Monitors the `data/` directory. When you add new CSV files, they are automatically ingested. |
| **Discovery Loop** | Every 5 minutes, runs the full scientific method cycle on all accumulated data. |
| **Evolution Loop** | Every 30 minutes, evaluates and improves the analysis pipeline. |
| **REST API** | Listens on port 18800 for programmatic queries. |

Leave this running in a terminal. As you add more files over the course of
your experiment, LabClaw picks them up automatically.

### What happens automatically

Once the daemon is running:

1. **Detects your files.** Every CSV in `data/` is read; columns are
   categorized as numeric or categorical.
2. **Mines patterns.** Pairwise correlations (Pearson, Spearman), outlier
   detection, temporal trends, and behavioral clustering.
3. **Generates hypotheses.** For example: "Animals in the center zone show
   higher velocity than those in the periphery (p < 0.05, t-test)."
4. **Validates statistically.** Only findings that pass validation are stored.
5. **Improves itself.** The evolution engine tunes analysis parameters. After
   several cycles, pattern detection becomes more effective for your data.

---

## Understanding Results

### Where findings appear

LabClaw stores its findings in two places:

**1. lab/MEMORY.md** -- A human-readable Markdown file that accumulates
discoveries over time. Each entry includes what was found, when, and which
data contributed. This file is git-friendly, so you get full history.

**2. The knowledge graph** -- A structured SQLite database storing entities
(animals, conditions, measurements), relationships, and temporal links. Query
it through the CLI or REST API for semantic search across experiments.

### How to read MEMORY.md

Open the file after a few discovery cycles have run:

```bash
cat lab/MEMORY.md
```

You will see entries like this:

```markdown
## Findings

### 2026-03-20T14:32:00 — Correlation: stimulus_hz vs response_latency_ms

Strong negative correlation detected (r = -0.67, p < 0.001).
Higher stimulus frequencies are associated with shorter response latencies
across all animals. Effect is strongest in M003 (r = -0.82).

**Data source:** session_001.csv, session_002.csv
**Confidence:** 0.89
**Validation:** Passed (Spearman rho = -0.64, Bonferroni-corrected p < 0.01)
```

Each finding has a timestamp, description, data sources, confidence score,
and validation details.

### Checking memory statistics

```bash
labclaw memory stats --memory-root ./lab
```

This prints the total finding count and retrieval rate.

---

## Querying Your Lab's Knowledge

Search accumulated knowledge using natural language:

```bash
labclaw memory query "freezing behavior" --memory-root ./lab
```

This returns matching findings as JSON:

```json
[
  {
    "finding_id": "f-a1b2c3d4",
    "description": "M002 shows significantly higher freezing percentage (11.3%) compared to cohort mean (7.4%)",
    "confidence": 0.85,
    "timestamp": "2026-03-20T14:37:00",
    "sources": ["session_001.csv"]
  }
]
```

More examples:

```bash
# Find everything about a specific animal
labclaw memory query "M003" --memory-root ./lab

# Search for stimulus-related findings
labclaw memory query "stimulus frequency response" --memory-root ./lab

# Look for temporal trends
labclaw memory query "learning curve improvement over trials" --memory-root ./lab
```

With the `memory` extra installed, queries use semantic embedding search --
a query for "habituation" can match findings about "decreased response over
repeated trials" even without exact keyword overlap.

---

## Running a Single Analysis Cycle

Just finished collecting data and want results now? Use the `pipeline` command
instead of the daemon:

```bash
labclaw pipeline --once --data-dir ./data
```

This runs one full cycle (Observe through Conclude) and prints JSON results.
To also persist findings to MEMORY.md:

```bash
labclaw pipeline --once --data-dir ./data --memory-root ./lab
```

### Reproducible runs

For a paper or lab meeting, use `--seed` to get deterministic output:

```bash
labclaw pipeline --once --data-dir ./data --seed 42
```

Same seed + same data = identical output. Verify explicitly:

```bash
labclaw reproduce --data-dir ./data --seed 42
```

### What the JSON output looks like

```json
{
  "cycle_id": "c-8f3a21b7-...",
  "success": true,
  "total_duration": 3.42,
  "steps_completed": ["observe", "ask", "hypothesize", "predict",
                       "experiment", "analyze", "conclude"],
  "patterns_found": 12,
  "hypotheses_generated": 5
}
```

Key fields: `patterns_found` (statistical patterns detected),
`hypotheses_generated` (testable hypotheses formulated),
`steps_completed` (which scientific method steps ran), and
`total_duration` (wall-clock seconds).

---

## Exporting Results

### JSON export

Export your session's findings and their provenance chain to a JSON file:

```bash
labclaw export --format json --session my-session-001 --output results.json
```

The output includes findings, analysis steps, and data lineage.

### NWB export (Neurodata Without Borders)

For neuroscience workflows compatible with DANDI Archive and NWB tools:

```bash
pip install "labclaw[nwb]"
labclaw export --format nwb --session my-session-001 --output session_001.nwb
```

Open the resulting file with pynwb, NWB Explorer, or Neurosift, or upload
directly to DANDI.

| Format | Best for |
|--------|---------|
| JSON | Sharing with collaborators, feeding into other scripts, archiving |
| NWB | Neuroscience-specific workflows, DANDI uploads, long-term archival |

---

## Next Steps

**Keep the daemon running.** The longer LabClaw runs, the more it learns.
Drop new CSV files into `data/` as experiments progress.

**Explore the dashboard.** Open [http://localhost:18801](http://localhost:18801)
while the daemon is running for a visual interface showing live discoveries,
evolution progress, and the knowledge graph.

**Connect to Claude Desktop.** Run `labclaw mcp` to use LabClaw as an MCP
tool in Claude Desktop. See the [quickstart guide](../quickstart.md) for
configuration details.

**Configure an LLM provider.** The demo and pipeline work without API keys
(using built-in templates). For richer hypothesis generation, add an LLM to
`configs/default.yaml`:

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
```

Then `export ANTHROPIC_API_KEY=sk-ant-...` in your shell.

### Read more

| Topic | Where to find it |
|-------|-----------------|
| Full configuration options | [Configuration](../configuration.md) |
| System architecture | [Architecture](../architecture.md) |
| Practical recipes for common tasks | [Cookbook](../cookbook.md) |
| Memory system deep dive | [Memory System](../memory-system.md) |
| Writing custom plugins | [Plugin Development](../plugin-development.md) |
| Self-evolution explained | [Self-Evolution](../self-evolution.md) |
| REST API reference | [API Reference](../api-reference.md) |
| Production deployment | [Deployment Guide](../../deploy/) |

---

## Quick Reference

A cheat sheet of every command used in this tutorial:

```bash
# Install
pip install "labclaw[science]"

# Run the demo
labclaw demo --domain neuroscience

# Create a project
labclaw init my-behavior-study

# Start the daemon (runs continuously)
labclaw serve --data-dir ./data --memory-root ./lab

# Run one analysis cycle and exit
labclaw pipeline --once --data-dir ./data --memory-root ./lab

# Query accumulated knowledge
labclaw memory query "freezing behavior" --memory-root ./lab

# Check memory statistics
labclaw memory stats --memory-root ./lab

# Export to JSON
labclaw export --format json --session my-session-001 --output results.json

# Export to NWB
labclaw export --format nwb --session my-session-001 --output session_001.nwb

# Reproducible run
labclaw pipeline --once --data-dir ./data --seed 42

# Verify reproducibility
labclaw reproduce --data-dir ./data --seed 42
```
