# Export & Reproducibility — Sharing and Verifying Your Results

This guide walks you through exporting LabClaw findings for publication,
sharing results with collaborators, and verifying that your analysis is
fully reproducible. Every command shown here works out of the box with a
standard LabClaw project directory.

---

## Table of Contents

1. [Why Export & Reproducibility Matter](#1-why-export--reproducibility-matter)
2. [Understanding Provenance Chains](#2-understanding-provenance-chains)
3. [Exporting to NWB](#3-exporting-to-nwb)
4. [Exporting to JSON](#4-exporting-to-json)
5. [Provenance in Exports](#5-provenance-in-exports)
6. [The Reproduce Command](#6-the-reproduce-command)
7. [Reproducibility for Papers](#7-reproducibility-for-papers)
8. [Sharing Your Lab's Memory](#8-sharing-your-labs-memory)
9. [Next Steps](#9-next-steps)

---

## 1. Why Export & Reproducibility Matter

Scientific findings only count if others can verify them. Export and
reproducibility matter for three concrete reasons:

**Journal requirements.** Top-tier journals (Nature, Science, eLife) now
mandate that authors deposit analysis code, intermediate results, and
provenance metadata alongside manuscripts. LabClaw exports satisfy these
requirements directly.

**Collaboration.** When you share data with a collaborator at another
institution, they need more than a CSV. They need to know which pipeline
version produced the result, what parameters were used, and how each
finding traces back to the raw acquisition files.

**Self-verification.** Six months from now, when a reviewer asks whether
your clustering result is robust to seed changes, you want a one-command
answer — not a week of archaeology through old notebooks.

LabClaw addresses all three by building provenance tracking into the
analysis pipeline itself, then exposing that provenance through standard
export formats.

---

## 2. Understanding Provenance Chains

A provenance chain is an ordered sequence of steps that links a finding
back to its raw data. Every finding that LabClaw produces carries one.

A chain consists of **ProvenanceStep** entries. Each step records:

| Field         | Description                                       |
|---------------|---------------------------------------------------|
| `node_id`     | Unique identifier for this processing node        |
| `node_type`   | What kind of node — `raw_file`, `transform`, `finding`, etc. |
| `description` | Human-readable summary of what happened           |
| `timestamp`   | When this step was executed (ISO 8601)             |

Steps are assembled into a **ProvenanceChain**:

| Field         | Description                                       |
|---------------|---------------------------------------------------|
| `chain_id`    | UUID for the chain itself                         |
| `finding_id`  | The finding this chain traces                     |
| `steps`       | Ordered list of ProvenanceStep entries             |
| `created_at`  | When the chain was built                          |

A typical chain reads like a story from bottom to top:

```
raw_file   →  "electrophysiology_session_042.csv" (SHA256: a3f8c2...)
transform  →  "Outlier removal: IQR method, 1.5x threshold"
transform  →  "Z-score normalization across channels"
mining     →  "Frequent pattern mining: min_support=0.05"
finding    →  "Correlated firing between channels 3 and 7 (r=0.82)"
```

Every export format preserves this full chain, so anyone receiving your
results can trace each conclusion back to the source file on disk.

---

## 3. Exporting to NWB

[Neurodata Without Borders (NWB)](https://www.nwb.org/) is the standard
format for neurophysiology data. If you are publishing in neuroscience,
reviewers and data repositories (DANDI Archive) expect NWB files.

### Prerequisites

Install the optional NWB dependency:

```bash
pip install "labclaw[science]"
# This pulls in pynwb and hdmf
```

### Basic NWB Export

```bash
labclaw export --format nwb \
  --session my-session-2026-03-15 \
  --output results/session_042.nwb
```

This produces an HDF5-based `.nwb` file containing:

- **Session metadata** — session ID, start time, description
- **Lab metadata** — a `labclaw_provenance` entry under `lab_meta_data`
- **Scratch data** — the full provenance chain as a JSON blob in the
  NWB scratch space, portable across NWB versions

### Verifying the NWB File

You can inspect the exported file with `pynwb` directly:

```python
from pynwb import NWBHDF5IO
import json

with NWBHDF5IO("results/session_042.nwb", "r") as io:
    nwb = io.read()
    print(f"Session: {nwb.identifier}")
    print(f"Description: {nwb.session_description}")

    # Read provenance from scratch
    provenance_json = nwb.scratch["labclaw_provenance"].data
    provenance = json.loads(provenance_json)
    print(f"Findings: {len(provenance['findings'])}")
    print(f"Provenance steps: {len(provenance['provenance_steps'])}")
```

### When pynwb Is Not Installed

If `pynwb` is not available in your environment, the `--format nwb`
command automatically falls back to a structured JSON file with the same
schema. You will see a log message:

```
DEBUG: pynwb not installed; using JSON fallback
```

The fallback file uses the same field names and structure as the NWB
scratch data, so downstream tools can consume it identically.

---

## 4. Exporting to JSON

JSON export is the right choice when you need machine-readable output
for custom analysis scripts, web dashboards, or non-neuroscience
collaborators who do not use NWB tooling.

### Basic JSON Export

```bash
labclaw export --format json \
  --session my-session-2026-03-15 \
  --output results/session_042.json
```

### JSON Output Structure

The exported file follows this schema:

```json
{
  "format": "labclaw-json-stub",
  "version": "1.0",
  "session_id": "my-session-2026-03-15",
  "session_start_time": "2026-03-15T14:30:00+00:00",
  "description": "LabClaw export for session my-session-2026-03-15",
  "findings": [
    {
      "finding_id": "f-001",
      "description": "Correlated firing between channels 3 and 7",
      "confidence": 0.92,
      "p_value": 0.003
    }
  ],
  "provenance_steps": [
    {
      "node_id": "step-001",
      "node_type": "raw_file",
      "description": "electrophysiology_session_042.csv",
      "timestamp": "2026-03-15T14:30:00+00:00"
    }
  ],
  "finding_chains": [
    {
      "chain_id": "c-001",
      "finding_id": "f-001",
      "steps": ["step-001", "step-002", "step-003"]
    }
  ],
  "metadata": {},
  "exported_at": "2026-03-15T16:45:12+00:00"
}
```

### Loading in Python

```python
import json
from pathlib import Path

data = json.loads(Path("results/session_042.json").read_text())

for finding in data["findings"]:
    print(f"  {finding['description']} (p={finding.get('p_value', 'N/A')})")

for chain in data["finding_chains"]:
    print(f"  Chain {chain['chain_id']} traces finding {chain['finding_id']}")
    print(f"    Steps: {len(chain['steps'])}")
```

### Loading in R

```r
library(jsonlite)

data <- fromJSON("results/session_042.json")
findings <- data$findings
print(paste("Found", nrow(findings), "findings"))
```

---

## 5. Provenance in Exports

Both NWB and JSON exports embed the full provenance chain. Here is how
the traceability works end to end.

### File Integrity via SHA256

LabClaw tracks source files using the `FileReference` model, which
records a SHA256 checksum for every ingested file:

```
path:       /data/rig-1/session_042.csv
sha256:     a3f8c2e19b...
size_bytes: 1048576
mime_type:  text/csv
```

When your export references raw data, anyone can verify the source file
has not been modified:

```bash
sha256sum /data/rig-1/session_042.csv
# a3f8c2e19b...  /data/rig-1/session_042.csv
```

If the checksum matches the value in the export, the data is identical
to what LabClaw analyzed.

### Building a Chain Programmatically

If you are writing a custom analysis plugin, you can build provenance
chains using the `ProvenanceTracker`:

```python
from labclaw.validation.provenance import ProvenanceTracker
from labclaw.validation.statistics import ProvenanceStep

tracker = ProvenanceTracker()

steps = [
    ProvenanceStep(
        node_id="raw-001",
        node_type="raw_file",
        description="session_042.csv (SHA256: a3f8c2e19b...)",
    ),
    ProvenanceStep(
        node_id="transform-001",
        node_type="transform",
        description="Outlier removal: IQR method, 1.5x threshold",
    ),
    ProvenanceStep(
        node_id="finding-001",
        node_type="finding",
        description="Correlated firing between channels 3 and 7 (r=0.82)",
    ),
]

chain = tracker.build_chain(finding_id="f-001", steps=steps)
print(f"Chain ID: {chain.chain_id}")
print(f"Steps: {len(chain.steps)}")
```

### Verifying a Chain

```python
is_valid = tracker.verify_chain(chain)
print(f"Chain valid: {is_valid}")
# Chain valid: True
```

Verification checks that the chain has a non-empty `finding_id`, at
least one step, and every step has a valid `node_id` and `node_type`.

### Serializing for External Tools

```python
from labclaw.validation.provenance import to_dict, from_dict

# Serialize to JSON-safe dict
chain_dict = to_dict(chain)

# Round-trip back to a validated ProvenanceChain
restored = from_dict(chain_dict)
assert restored.chain_id == chain.chain_id
```

---

## 6. The Reproduce Command

The `labclaw reproduce` command runs the same pipeline twice with an
identical random seed and verifies that both runs produce the same
output. This is your single-command proof of determinism.

### Basic Usage

```bash
labclaw reproduce \
  --data-dir ./data \
  --seed 42
```

### What Happens Under the Hood

1. LabClaw loads all `.csv` files from `--data-dir`
2. Seeds the random number generator with `--seed`
3. Runs the full scientific loop (Observe, Ask, Hypothesize, Predict,
   Experiment, Analyze, Conclude)
4. Resets the seed and runs the identical loop a second time
5. Normalizes both outputs (strips per-run UUIDs and timestamps)
6. Compares the two results

### Interpreting the Output

**Success** — the outputs match:

```json
{
  "reproducible": true,
  "run1": { "...": "..." },
  "run2": { "...": "..." },
  "diff": null
}
```

**Failure** — the outputs diverge:

```json
{
  "reproducible": false,
  "run1": { "...": "..." },
  "run2": { "...": "..." },
  "diff": ["findings", "final_context"]
}
```

The `diff` array lists which top-level keys differ between the two
runs. The exit code is `0` for reproducible, `1` for divergent — so you
can use it directly in CI pipelines.

### With Memory

If your pipeline uses persistent memory, pass the memory root so both
runs share the same context:

```bash
labclaw reproduce \
  --data-dir ./data \
  --seed 42 \
  --memory-root ./lab
```

### In CI/CD

Add a reproducibility check to your GitHub Actions or GitLab CI:

```yaml
# .github/workflows/reproducibility.yml
- name: Verify reproducibility
  run: labclaw reproduce --data-dir tests/fixtures/sample_data --seed 42
```

If the pipeline is non-deterministic (for example, an LLM call without
temperature=0), the command will fail with exit code 1 and show which
fields diverged.

---

## 7. Reproducibility for Papers

When writing a paper that includes LabClaw-generated results, include
these elements to satisfy reproducibility requirements.

### Methods Section Template

> Statistical patterns were identified using LabClaw v0.x.x
> (https://github.com/labclaw/labclaw). The discovery pipeline was run
> in deterministic mode (seed=42, --no-llm) on the raw CSV data. All
> findings include provenance chains tracing each result to its source
> file via SHA256 checksums. Reproducibility was verified using
> `labclaw reproduce --seed 42`, confirming identical output across
> independent runs.

### Supplementary Materials Checklist

| Item | What to include | Format |
|------|-----------------|--------|
| Raw data | Original CSV/NWB files | DANDI Archive or Zenodo |
| LabClaw config | `configs/default.yaml` | Git repository |
| Export file | `labclaw export --format nwb` output | `.nwb` alongside data |
| Reproduce log | `labclaw reproduce --seed 42` output | JSON in supplement |
| Software version | `pip freeze \| grep labclaw` | Text in methods |
| Lab identity | `lab/SOUL.md` (protocols, equipment) | Git repository |

### Locking Your Environment

Pin exact dependency versions so reviewers can recreate your setup:

```bash
# Record exact versions
pip freeze > requirements-lock.txt

# Reviewers reproduce with:
pip install -r requirements-lock.txt
labclaw reproduce --data-dir ./data --seed 42
```

### End-to-End Example

Here is a complete workflow from analysis to paper-ready export:

```bash
# 1. Run the discovery pipeline with a fixed seed
labclaw pipeline --once \
  --data-dir ./data \
  --seed 42 \
  --no-llm > results/pipeline_output.json

# 2. Verify reproducibility
labclaw reproduce --data-dir ./data --seed 42

# 3. Export findings with provenance for the paper
labclaw export --format nwb \
  --session experiment-2026-03-15 \
  --output results/experiment_2026-03-15.nwb

# 4. Export a JSON copy for collaborators without NWB tools
labclaw export --format json \
  --session experiment-2026-03-15 \
  --output results/experiment_2026-03-15.json
```

---

## 8. Sharing Your Lab's Memory

LabClaw's three-tier memory system holds your lab's accumulated
knowledge. When sharing with collaborators, be deliberate about what
you include.

### What to Share

**Tier A: Markdown files (always safe to share)**

These are human-readable files under `lab/` that describe your lab's
identity, protocols, and accumulated observations:

```
lab/
  lab/
    SOUL.md      # Lab identity, mission, standard protocols
    MEMORY.md    # Chronological observation log
```

Share these by including them in your data repository:

```bash
# Copy lab identity to your shared repo
cp -r lab/ shared-repo/lab/
```

**Tier B: Knowledge graph (share selectively)**

The SQLite-backed knowledge graph contains structured relationships
between entities. Export relevant subsets:

```python
from labclaw.memory.sqlite_backend import SQLiteTierBBackend
from pathlib import Path

backend = SQLiteTierBBackend(Path("data/labclaw.db"))
await backend.init_db()

# Search for findings related to your paper
results = await backend.search("calcium imaging correlation")
for r in results:
    print(f"{r.node.name}: {r.node.node_type}")
```

**Tier C: Agent working memory (generally not shared)**

Agent state blocks are transient and specific to your local setup. They
are not useful for collaborators.

### Minimum Sharing Bundle

For a collaborator to reproduce your results, share this directory
structure:

```
shared-bundle/
  data/               # Raw CSV/NWB data files
  configs/
    default.yaml      # LabClaw configuration (redact API keys)
  lab/
    lab/
      SOUL.md         # Lab identity and protocols
      MEMORY.md       # Observation log
  results/
    session.nwb       # Exported findings with provenance
    session.json      # JSON copy for non-NWB users
  requirements-lock.txt
  README.md           # Reproduction instructions
```

### Security Considerations

Before sharing, verify you are not leaking sensitive information:

```bash
# Check that no API keys are in the config
grep -r "sk-" configs/
grep -r "api_key" configs/

# Redact if needed
sed -i 's/api_key_env: .*/api_key_env: YOUR_KEY_HERE/' configs/default.yaml
```

Never share:

- API keys or tokens (use `api_key_env` to reference environment variables)
- `.env` files
- Patient or subject identifiers (de-identify first)
- Agent working memory (Tier C) that may contain intermediate API responses

---

## 9. Next Steps

Now that you can export and reproduce your results:

- **Run `labclaw demo`** if you have not already — it produces sample
  findings you can practice exporting.
- **Read the [Cookbook](../cookbook.md)** for recipes on setting up memory,
  connecting instruments, and running evolution experiments.
- **Set up CI reproducibility checks** using the `labclaw reproduce`
  command in your GitHub Actions workflow.
- **Explore NWB tooling** — the DANDI Archive, NWB Widgets, and
  NWB Inspector all work with LabClaw's NWB exports.
- **Build custom provenance** in your analysis plugins using the
  `ProvenanceTracker` API documented in section 5.

For questions or issues, open a ticket on the LabClaw repository.
