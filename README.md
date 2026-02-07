# Abductive Dialogue Pipeline

> **Empathy-Driven Abductive Reasoning in Multi-Agent Dialogue Systems**

Research implementation of a multi-agent dialogue pipeline using abductive reasoning (hypothesis-generating inference).
Through ablation experiments manipulating three variables: Personal Knowledge Graph (PKG), external search (RAG), and diagnostic Judge,
we observe the role of each component in empathetic dialogue.

---

## Research Questions

| # | Question |
|---|---------|
| RQ1 | How does an explicit abductive pipeline (O/A → Hypothesis → Judge → Decision) affect hypothesis diversity and explanation quality? |
| RQ2 | How do PKG and external evidence (RAG) contribute to hypothesis grounding and persona consistency? |
| RQ3 | Does Agent-as-a-Judge diagnostics improve the selection of empathetic and evidence-based responses? |

---

## Architecture

```
User Input + Persona + PKG
        │
        ▼
┌──────────────┐
│ ContextAgent │  Extract observations (O) and assumptions (A), generate triggers and RAG queries
└──────┬───────┘
       ▼
┌──────────────┐
│ExplorerAgent │  Web search → LLM interpretation → evidence_items + external_observations (Oext)
└──────┬───────┘  [Skipped when use_rag=false]
       ▼
┌────────────────┐
│HypothesisAgent │  Generate 3-5 hypotheses (explains O+Oext, assumes A, predictions, discriminating_questions)
└──────┬─────────┘
       ▼
┌────────────┐
│ JudgeAgent │  Diagnostic review (fatal_flaws / explains_confirmed / safety_risk_notes)
└──────┬─────┘  [Skipped when use_judge=false]
       ▼
┌───────────────┐
│ DecisionAgent │  Contrastive selection of 2 hypotheses (selected + contrasting)
└──────┬────────┘
       ▼
┌────────────────┐
│ DialogueAgent  │  Generate dialogue response with empathy + nudge + discriminating questions
└────────────────┘
       │
       ▼
   final_response + JSON logs + Neo4j PKG update
```

---

## Ablation Conditions

| Condition | `use_pkg` | `use_rag` | `use_judge` | `is_single` | Purpose |
|-----------|-----------|-----------|-------------|-------------|---------|
| **A** (Full)    | ✓ | ✓ | ✓ | ✗ | All features enabled |
| **B** (−PKG)    | ✗ | ✓ | ✓ | ✗ | Observe PKG role |
| **C** (−RAG)    | ✓ | ✗ | ✓ | ✗ | Observe RAG role |
| **D** (Single)  | ✓ | ✓ | ✓ | ✓ | No pipeline decomposition (single agent) |

---

## Directory Structure

```
.
├── docker-compose.yml         # Neo4j (community) container definition
├── requirements.txt           # Python dependencies
├── .env.sample                # Environment variable template
├── neo4j/                     # Neo4j data persistence (Docker volume)
└── newresearch/               # ★ Main package
    ├── config.py              # RunConfig, ABLATION_CONDITIONS, AzureSettings
    ├── schemas.py             # Pydantic I/O schemas (all agents)
    ├── scenarios.py           # 10 scenarios × 3 persona definitions
    ├── seed_pkg.py            # Neo4j PKG seed script
    ├── neo4j_pkg.py           # Neo4j PKG reader
    ├── pkg_store.py           # PKG read/write (dynamic graph update)
    ├── pipeline.py            # Multi-agent pipeline (conditions A/B/C)
    ├── pipeline_single.py     # Single-agent pipeline (condition D)
    ├── runner.py              # Ablation experiment runner
    ├── metrics.py             # Metrics extraction → CSV
    ├── run_A/B/C/D.py         # Condition-specific run scripts
    ├── agents/
    │   ├── base.py            # BaseAgent (Azure OpenAI call + logging)
    │   ├── context.py         # ContextAgent — O/A extraction + triggers
    │   ├── explorer.py        # ExplorerAgent — Web search + LLM interpretation
    │   ├── hypothesis.py      # HypothesisAgent — Diverse hypothesis generation
    │   ├── judge.py           # JudgeAgent — Diagnostic evaluation
    │   ├── decision.py        # DecisionAgent — 2-hypothesis contrastive selection
    │   ├── dialogue.py        # DialogueAgent — Empathy + nudge response
    │   └── single.py          # SingleAgent (for condition D)
    ├── prompts/               # Agent prompts (.txt)
    └── results/
        ├── runs/{A,B,C,D}/    # Run logs per condition (JSON)
        └── figures/           # Generated graphs
```

---

## Scenarios

10 scenarios × 3 personas = 30 pairs. Each scenario requires creative judgment with no single correct answer
and stress-tests a specific cognitive bias category.

| ID | Bias Category | Overview |
|----|-----------------|------|
| S1 | Authenticity | "I want to walk in authentic life not in guidebooks" |
| S2 | Efficiency | "Want to maximize efficiency with minute-by-minute scheduling" |
| S3 | Expertise | "I know Kanazawa's traditional architecture better than anyone" |
| S4 | Authenticity | "I absolutely don't want to go to tourist restaurants" |
| S5 | Efficiency | "Travel plan with thoroughly minimized costs" |
| S6 | Expertise | "I know Yakushima's forest better than anyone" |
| S7 | Safety | "I only travel abroad on tours" |
| S8 | Nostalgia | "I want to recapture the emotion of Kyoto from my student days" |
| S9 | Cost | "30,000 yen per night at an inn is too expensive" |
| S10 | Record | "The purpose of travel is to take perfect photos for SNS" |

### Personas

Three personas selected from the Nemotron-Personas-Japan dataset.

| ID | Name | Attributes | PKG |
|----|------|------|-----|
| P01 | Yasuaki Sugiura | 47 years old, postal clerk, Niigata Prefecture — rural walks, community events, calligraphy | 10 nodes, 8 edges |
| P05 | Yaichi Suzuki | 53 years old, arcade management, Chiba Prefecture — data analysis, budget-conscious, retro games | 10 nodes, 8 edges |
| P07 | Sakiya Okada | 27 years old, farming, Miyagi Prefecture — planned management, regional culture, organic vegetable brand | 10 nodes, 8 edges |

---

## Quick Start

Refer to [SETUP.md](SETUP.md) for detailed setup instructions.

```bash
# 1. Virtual environment + dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Environment variables
cp .env.sample .env   # → Configure actual API keys

# 3. Start Neo4j + seed PKG
docker compose up -d graph-db
python -m newresearch.seed_pkg

# 4. Single run
python -m newresearch.run_A --scenario S1 --persona P01

# 5. Run all ablation experiments (4 conditions × 10 scenarios × 3 personas)
python -m newresearch.runner --all

# 6. Extract metrics
python -m newresearch.metrics
```

---

## Metrics

| Category | Metric | Source |
|----------|--------|-------|
| Hypothesis Diversity | `hypothesis_count`, `type_diversity` | hypotheses.json |
| Observation Space | `observation_count`, `external_observation_count` | context.json + evidence.json |
| Abductive Structure | `observation_coverage`, `avg_predictions_per_h` | hypotheses + context |
| Judge Diagnostics | `fatal_flaw_avoided`, `selected_explains_count`, `discriminating_q_coverage` | judgements + decision |
| 2-Hypothesis Contrast | `has_contrasting`, `contrast_type_diff` | decision + hypotheses |
| Source Utilisation | `persona_link_count`, `evidence_link_count` | hypotheses.json |
| Empathy / Nudge | empathy marker rate, nudge marker rate, `directive_level` | final.json |

---

## Output Format

Each run generates the following files in `newresearch/results/runs/{condition}/{run_id}/`:

| File | Content |
|------|---------|  
| `config.json` | Run configuration (condition flags, persona, scenario) |
| `context.json` | Observations (O), assumptions (A), triggers, RAG queries |
| `evidence.json` | External evidence + external observations (Oext) |
| `hypotheses.json` | 3-5 hypotheses (explains, assumes, predictions, discriminating_questions) |
| `judgements.json` | Diagnostic results (fatal_flaws, explains_confirmed, safety_risk_notes) |
| `decision.json` | 2-hypothesis contrastive selection + user_facing_frame |
| `final.json` | Final response + empathy/nudge markers |
| `response.txt` | Plain text response |

---

## Neo4j Data Model

```
(:ExpUser {persona_id, name, summary})
  -[:HAS_PKG_NODE]->
(:PKGNode {node_id, label, type, weight})
  -[:motivates|drives|requires|strengthens|...]->
(:PKGNode)
```

**Dynamic graph updates**: In conditions A/C (`use_pkg=true`), observations, triggers, hypotheses,
judgments, and decisions are written to Neo4j during pipeline execution, dynamically expanding the PKG.

---

## References

1. **Nemotron-Personas-Japan** — Foundation for persona dataset
   - NVIDIA. *Nemotron-CC: Curating High-Quality Synthetic Data for LLM Training.* 2024.
   - The 3 personas (P01, P05, P07) in this experiment are selected and extended from the Nemotron-Personas-Japan dataset.

2. **Peirce's Abductive Inference** — Theoretical foundation for reasoning framework
   - Peirce, C. S. *Collected Papers of Charles Sanders Peirce.* Harvard University Press, 1931–1958.

3. **Personal Knowledge Graphs (PKG)** — User modeling
   - Balog, K., & Kenter, T. *Personal Knowledge Graphs: A Research Agenda.* ICTIR 2019.

4. **Agent-as-a-Judge** — Diagnostic evaluation by LLM
   - Zhuge, M., et al. *Agent-as-a-Judge: Evaluate Agents with Agents.* arXiv:2410.10934, 2024.

5. **Nudge Theory** — Choice architecture for behavior change
   - Thaler, R. H., & Sunstein, C. R. *Nudge: Improving Decisions About Health, Wealth, and Happiness.* Yale University Press, 2008.

6. **Neo4j** — Graph database
   - Neo4j, Inc. *The Neo4j Graph Database.* https://neo4j.com/

7. **Azure OpenAI Service** — LLM inference platform
   - Microsoft. *Azure OpenAI Service.* https://azure.microsoft.com/products/ai-services/openai-service
   - This experiment uses GPT-4.1 deployment.

8. **Serper API** — Web search API
   - Serper. *Google Search API.* https://serper.dev/

---

## License

MIT License
