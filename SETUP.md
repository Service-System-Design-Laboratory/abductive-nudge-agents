# Setup Guide

Instructions for environment setup and experiment reproduction.
Refer to [README.md](README.md) for project overview.

---

## Prerequisites

| Item | Requirement |
|------|------|
| Python | 3.10 or higher (3.12 recommended) |
| Docker & Docker Compose | For Neo4j container execution |
| Azure OpenAI API | GPT-4.1 deployment |
| Web Search API (optional) | One of: Serper / Google Custom Search / Bing |

---

## 1. Clone Repository

```bash
git clone <repository-url>
cd AI-one-hour
git checkout plan_masaki
```

---

## 2. Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Environment Variable Configuration

```bash
cp .env.sample .env
```

Open `.env` and configure the following:

```env
# ── Azure OpenAI（必須）──────────────────────────
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# ── Neo4j ────────────────────────────────────────
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# ── Web Search（任意）────────────────────────────
# SEARCH_PROVIDER で切替: serper (default) / google / bing
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_key

# Google Custom Search を使う場合:
# SEARCH_PROVIDER=google
# GOOGLE_API_KEY=your_google_key
# GOOGLE_CX=your_custom_search_engine_id

# Bing Web Search を使う場合:
# SEARCH_PROVIDER=bing
# BING_API_KEY=your_bing_key
```

### API キーの取得先

| API | 取得先 |
|-----|--------|
| Azure OpenAI | [Azure Portal](https://portal.azure.com/) → OpenAI リソース → Keys and Endpoint |
| Serper | [serper.dev](https://serper.dev/) — 無料枠 2,500 回/月 |
| Google Custom Search | [Google Cloud Console](https://console.cloud.google.com/) + [Programmable Search Engine](https://programmablesearchengine.google.com/) |
| Bing Search | [Azure Portal](https://portal.azure.com/) → Bing Search v7 リソース |

> **Note**: Web Search API が未設定でも実験は実行可能です。
> 条件 C (−RAG) では検索を使用せず、条件 A/B/D でも検索失敗時は LLM の既存知識で続行します。

---

## 4. Start Neo4j

```bash
docker compose up -d graph-db
```

Verify startup:

```bash
# Check container
docker ps | grep neo4j-local

# Access in browser (no authentication)
# http://localhost:7474
```

> `docker-compose.yml` is configured with `NEO4J_AUTH=none`, so no authentication required.

---

## 5. Seed PKG Data

Load the Personal Knowledge Graphs for 3 personas (P01, P05, P07) into Neo4j.

```bash
python -m newresearch.seed_pkg
```

Verification:

```bash
python -m newresearch.seed_pkg --check
```

Verify in Neo4j Browser (http://localhost:7474):

```cypher
MATCH (u:ExpUser) RETURN u.persona_id, u.name
```

If 3 personas are displayed, seeding succeeded.

---

## 6. Run Experiments

### Single Scenario Execution

```bash
# Condition A (Full: PKG + RAG + Judge) × S1 × P01
python -m newresearch.run_A --scenario S1 --persona P01

# Condition B (-PKG)
python -m newresearch.run_B --scenario S1 --persona P01

# Condition C (-RAG)
python -m newresearch.run_C --scenario S1 --persona P01

# Condition D (Single Agent)
python -m newresearch.run_D --scenario S1 --persona P01
```

### Run All Ablation Experiments

```bash
# 4 conditions × 10 scenarios × 3 personas = 120 runs
python -m newresearch.runner --all

# Specify personas/scenarios
python -m newresearch.runner --personas P01 --scenarios S1 S2 S3
```

### Extract Metrics

```bash
python -m newresearch.metrics
# → newresearch/results/metrics.csv
```

---

## 7. Check Results

Each run is saved to `newresearch/results/runs/{A,B,C,D}/{run_id}/`:

```
config.json       Run configuration
context.json      Observations (O), assumptions (A), triggers
evidence.json     External evidence + external observations (Oext)
hypotheses.json   3-5 hypotheses
judgements.json   Diagnostic results
decision.json     2-hypothesis contrastive selection
final.json        Final response + empathy/nudge markers
response.txt      Plain text response
```

### Dynamic Graph Verification in Neo4j

In conditions A/C (`use_pkg=true`), reasoning results are written to Neo4j during pipeline execution.

```cypher
-- Display entire graph
MATCH (n)-[r]->(m) RETURN n, r, m

-- By persona
MATCH (u:ExpUser {persona_id: "P01"})-[*1..3]-(connected)
RETURN u, connected

-- Runtime writes only
MATCH (n) WHERE n.run_id IS NOT NULL
MATCH (n)-[r]-(m) RETURN n, r, m
```

---

## Troubleshooting

### Cannot Connect to Neo4j

```bash
docker ps -a | grep neo4j     # Check container status
docker compose restart graph-db  # Restart
```

### Azure OpenAI 401 / 429 Errors

1. Check API key and endpoint in `.env`
2. Verify deployment name is correct (default: `gpt-4.1`)
3. Check quota limits in Azure Portal

### PKG Seed Errors

```bash
# Clear and re-seed
python -m newresearch.seed_pkg --clear
```

### Port 7474/7687 Already in Use

```bash
# Stop existing Neo4j container
docker stop $(docker ps -q --filter "publish=7474")
docker compose up -d graph-db
```
