# Lab Memory — How LabClaw Remembers Everything

Every lab accumulates hard-won knowledge: which antibody dilutions work,
why that rig drifts after 40 minutes, which parameters produced a clean
result last March. Most of it lives in someone's head or a Slack thread
no one will find again.

LabClaw captures that knowledge automatically, makes it searchable, and
feeds it back into future analysis. The longer it runs, the smarter it
gets.

---

## 1. Why Lab Memory Matters

When a postdoc leaves, their mental model walks out the door. LabClaw
treats lab knowledge as infrastructure, not folklore:

- **Findings** from every analysis cycle stored with full provenance.
- **Hypotheses** recorded whether they succeeded or failed.
- **Parameters** linked to the sessions that used them.
- **Decisions** about protocol changes timestamped and searchable.

---

## 2. The Three Tiers

### Tier A: The Lab Notebook (Markdown)

**Analogy:** A shared, append-only lab notebook tracked by git.

Tier A stores knowledge as plain markdown — `SOUL.md` for identity and
`MEMORY.md` for the running log:

```
lab/lab/
  SOUL.md       # What this lab is about
  MEMORY.md     # Observations and conclusions
lab/alice/
  SOUL.md       # Alice's role and expertise
  MEMORY.md     # Alice's activity log
devices/microscope-01/
  SOUL.md       # Device specs and quirks
  MEMORY.md     # Maintenance and calibration history
```

Tier A is the **source of truth** — readable with any text editor, diffable
in git, greppable from the terminal. If the database disagrees with the
markdown, the markdown wins.

### Tier B: The Filing Cabinet (Knowledge Graph)

**Analogy:** A filing cabinet where every folder is labeled,
cross-referenced, and indexed by any combination of criteria.

Tier B is a SQLite-backed knowledge graph with FTS5 full-text search.
Where Tier A stores narrative text, Tier B stores typed entities and
relationships:

| Node type    | Represents                           |
|--------------|--------------------------------------|
| `session`    | An experimental session              |
| `recording`  | A data file from a session           |
| `analysis`   | An analysis result                   |
| `parameter`  | An experimental parameter            |
| `finding`    | A discovered pattern or conclusion   |

Nodes connect via typed edges (`produced_by`, `supports`, `contradicts`,
`contains`). Every node carries timestamps for temporal queries. FTS5 uses
Porter stemming, so "firing" also matches "fired" and "fires".

### Tier C: The Scratch Pad (Agent State)

**Analogy:** The whiteboard next to the microscope — working notes that
agents share and pick up where they left off.

Tier C is a key-value store for AI agent working state. You rarely
interact with it directly, but it is what lets LabClaw resume analysis
after a restart without losing context.

### How the Tiers Relate

```
Tier A (Markdown)  ─────>  Tier B (Knowledge Graph)
       ^                          │
       │                          v
       └──────── Tier C (Agent State) ──┘
```

1. **A to B:** Daemon extracts structured facts from markdown into graph nodes.
2. **B to C:** Agents query the graph and store working conclusions in blocks.
3. **C to A:** Agents write human-readable summaries back for your review.

---

## 3. What Gets Stored Automatically

Every discovery cycle persists without configuration:

- **Findings:** description, statistical evidence (p-values, effect sizes),
  data source, and confidence score.
- **Hypotheses:** both successful and failed — failed ones prevent
  re-testing dead ends.
- **Validations:** linked back to the original hypothesis, building an
  evidence web over time.
- **Provenance:** full lineage — raw data files, pipeline steps, active
  parameters, LabClaw version. Trace any conclusion back to its source.

---

## 4. Querying Memory from the CLI

### Search for findings

```bash
labclaw memory query "calcium imaging"
labclaw memory query "firing rate" --memory-root ./my-project/lab
labclaw memory query "optogenetics" --memory-root ./lab --db ./data/labclaw.db
```

Results print as JSON with provenance and relevance scores.

### Check memory health

```bash
labclaw memory stats
labclaw memory stats --memory-root ./lab --db ./data/labclaw.db
```

Reports **total findings** and **retrieval rate** (fraction of historical
findings retrievable after restart; target: 90%+).

---

## 5. Querying via API

When LabClaw runs as a daemon (`labclaw serve`), REST endpoints are
available on port 18800 under `/memory`.

### Search

```bash
curl "http://localhost:18800/memory/search/query?q=calcium+imaging&limit=5"
```

```python
import httpx

resp = httpx.get(
    "http://localhost:18800/memory/search/query",
    params={"q": "calcium imaging", "limit": 5},
)
for hit in resp.json():
    print(f"[{hit['source']}] {hit['entity_id']}: {hit['snippet']}")
```

### Read SOUL.md and MEMORY.md

```bash
curl "http://localhost:18800/memory/lab/soul"
curl "http://localhost:18800/memory/lab/memory"
```

### Append a memory entry

```python
resp = httpx.post(
    "http://localhost:18800/memory/lab/memory",
    json={"category": "observation", "detail": "Mouse 12 showed increased grooming."},
)
assert resp.status_code == 201
```

### List findings and graph nodes

```bash
curl "http://localhost:18800/memory/findings?limit=20"
curl "http://localhost:18800/memory/kg/nodes?node_type=session&limit=10"
curl "http://localhost:18800/memory/kg/neighbors/node-abc123?direction=outgoing"
```

---

## 6. Reading the Lab Notebook

### SOUL.md

Identity file with YAML frontmatter and markdown body:

```markdown
---
name: LabClaw
type: lab
created: 2026-01-15
---
# LabClaw
## Identity
Motor control and decision-making in freely moving rodents.
## Protocols
- Two-photon calcium imaging: 30 Hz, GCaMP8f, 200 um depth
```

Edit whenever your lab changes. LabClaw re-reads these at startup.

### MEMORY.md

Append-only log with timestamps and categories:

```markdown
## 2026-02-20T14:30:00+00:00
**Category:** discovery
Cycle abc123: 5 patterns detected. Strong correlation (r=0.84, p<0.001)
between firing rate and movement onset latency in session 20260220-01.

## 2026-02-20T15:00:00+00:00
**Category:** evolution
Updated minimum cluster size from 10 to 25 based on false-positive rate.
```

Append entries manually or use the CLI/API.

### Python access

```python
from pathlib import Path
from labclaw.memory.markdown import TierABackend

backend = TierABackend(Path("lab"))
soul = backend.read_soul("lab")
print(soul.frontmatter)  # {"name": "LabClaw", "type": "lab", ...}

results = backend.search("calcium imaging", limit=5)
for r in results:
    print(f"  {r.entity_id}/{r.source}: {r.snippet} (score={r.score})")
```

---

## 7. Knowledge Graph Exploration

### Entities and relations

```
Session 001 ──contains──> Recording ephys-001.nwb
Session 001 ──contains──> Recording video-001.mp4
Recording ephys-001.nwb ──produced──> Analysis spike-sort-001
Analysis spike-sort-001 ──found──> Finding "FR correlates with accuracy"
Finding "FR ~ accuracy" ──supports──> Hypothesis "M1 encodes decision"
```

### Querying the graph

```python
from pathlib import Path
from datetime import datetime, timedelta, UTC
from labclaw.memory.knowledge_graph import SQLiteTierBBackend, KGQueryFilter

backend = SQLiteTierBBackend(Path("data/labclaw.db"))
await backend.init_db()

# Sessions from the last week
results = await backend.query_nodes(KGQueryFilter(
    node_type="session",
    created_after=datetime.now(UTC) - timedelta(days=7),
))

# What did a session produce?
for node, edge in await backend.get_neighbors("session-001", direction="outgoing"):
    print(f"  --{edge.relation}--> {node.name} ({node.node_type})")
```

### Temporal tracking

Every node carries `created_at` and `updated_at`, enabling questions
text search cannot answer: "What findings came from February data?" or
"Has this hypothesis changed since the protocol switch?"

---

## 8. Memory-Assisted Hypothesis Generation

When LabClaw runs a new analysis cycle, it queries memory first:

1. **New data arrives** (e.g., a recording from today's session).
2. Discovery engine detects patterns.
3. Before generating hypotheses, it **searches memory**: "Have we seen
   this before? What did we conclude?"
4. If a match exists with high confidence, LabClaw cites the prior finding
   instead of re-generating the same hypothesis.
5. If the pattern is new or contradicts a prior finding, it flags it as
   novel.

Over months, this accumulates. A firing rate correlation is not just a
p-value — LabClaw knows it was seen in sessions 014, 023, 041, absent
under anesthesia, and imaging data suggests layer 5 origin.

### The hybrid search engine

`HybridSearchEngine` searches both tiers with configurable temporal decay:

```python
from labclaw.memory.search import (
    HybridSearchEngine, HybridSearchQuery, HybridSearchConfig,
)

config = HybridSearchConfig(
    tier_a_weight=1.0,
    tier_b_weight=1.0,
    temporal_decay_half_life_days=30.0,
    enable_temporal_decay=True,
)
engine = HybridSearchEngine(tier_a=backend_a, tier_b=backend_b, config=config)

results = engine.search(HybridSearchQuery(
    text="firing rate movement onset",
    limit=10,
    tiers=["a", "b"],
))
for r in results:
    print(f"  [{r.source_tier}] {r.entity_id}: {r.snippet} (score={r.score})")
```

---

## 9. Pattern Deduplication

When the conclude step produces a finding, LabClaw:

1. **Searches existing findings** using the description as a query.
2. **Compares similarity.** Above-threshold matches are linked to the
   existing finding instead of stored as duplicates.
3. **Updates confidence.** Replication across sessions strengthens evidence.

The result: no 50 copies of "firing rate correlates with movement."
Confidence grows with replication. Contradictions are surfaced as
discrepancies worth investigating.

### Cross-session persistence

`SessionMemoryManager` writes to both Tier A and Tier B, ensuring findings
survive daemon restarts:

```python
from pathlib import Path
from labclaw.memory.session_memory import SessionMemoryManager

mgr = SessionMemoryManager(memory_root=Path("lab"), db_path=Path("data/findings.db"))
await mgr.init()

await mgr.store_finding({
    "description": "Firing rate predicts movement accuracy",
    "p_value": 0.0003,
    "effect_size": 0.72,
    "session": "20260220-01",
})

findings = await mgr.retrieve_findings(query="firing rate")
print(f"Retrieval rate: {mgr.get_retrieval_rate():.0%}")  # Target: >= 90%
```

---

## 10. Backing Up and Sharing Memory

### Tier A: Use git

```bash
cd your-project/lab
git init && git add . && git commit -m "Initial lab memory snapshot"
```

Some teams auto-commit daily via cron:

```bash
0 23 * * * cd /path/to/lab && git add -A && git commit -m "Daily snapshot $(date +%Y-%m-%d)" || true
```

Because Tier A is the source of truth, a git backup lets you reconstruct
Tiers B and C from scratch.

### Tier B: Export the database

```bash
labclaw export --format json --output findings-backup.json
labclaw export --format nwb --output session-001.nwb
```

### Tier C: Ephemeral by design

Agent working memory is rebuilt on restart. Important conclusions are
always written to Tiers A and B before the cycle completes.

### Sharing across labs

- **New member:** Clone the git repo for instant history access.
- **Collaborators:** Share read-only for searching without running LabClaw.
- **Publications:** Export findings with provenance for supplements.

---

## 11. Next Steps

- **Set up your lab identity.** `labclaw init my-lab` scaffolds SOUL.md
  and MEMORY.md. Edit SOUL.md to describe your mission and equipment.
- **Run a cycle.** `labclaw pipeline --once --data-dir ./data` populates
  memory with findings.
- **Search.** `labclaw memory query "your term"` shows what LabClaw has
  learned.
- **Explore the graph.** Use the Python API or REST endpoints to traverse
  sessions, recordings, and findings.
- **Read the architecture docs.** [Memory System](../memory-system.md)
  covers the full schema, threading model, and event system.
- **Version your notebook.** Put `lab/` under git. Future you will be glad.
