# Abductive Dialogue Pipeline

> **Empathy-Driven Abductive Reasoning in Multi-Agent Dialogue Systems**

アブダクティブ推論（仮説生成型推論）を用いたマルチエージェント対話パイプラインの研究実装です。
パーソナルナレッジグラフ（PKG）、外部検索（RAG）、診断型 Judge の 3 変数を操作する
アブレーション実験を通じて、共感的対話における各構成要素の役割を観察します。

---

## Research Questions

| # | Question |
|---|---------|
| RQ1 | 明示的なアブダクティブパイプライン (O/A → Hypothesis → Judge → Decision) は、仮説の多様性と説明品質にどう影響するか？ |
| RQ2 | PKG と外部エビデンス (RAG) は、仮説の根拠付けとペルソナ整合性にどう寄与するか？ |
| RQ3 | Agent-as-a-Judge 診断は、共感的で根拠のある応答の選択を改善するか？ |

---

## Architecture

```
User Input + Persona + PKG
        │
        ▼
┌──────────────┐
│ ContextAgent │  観察 (O) と仮定 (A) を抽出、トリガーと RAG クエリを生成
└──────┬───────┘
       ▼
┌──────────────┐
│ExplorerAgent │  Web 検索 → LLM 解釈 → evidence_items + external_observations (Oext)
└──────┬───────┘  [use_rag=false でスキップ]
       ▼
┌────────────────┐
│HypothesisAgent │  3–5 仮説を生成（explains O+Oext, assumes A, predictions, discriminating_questions）
└──────┬─────────┘
       ▼
┌────────────┐
│ JudgeAgent │  診断的レビュー（fatal_flaws / explains_confirmed / safety_risk_notes）
└──────┬─────┘  [use_judge=false でスキップ]
       ▼
┌───────────────┐
│ DecisionAgent │  2 仮説の対比的選択（selected + contrasting）
└──────┬────────┘
       ▼
┌────────────────┐
│ DialogueAgent  │  共感 + ナッジ + 判別質問を含む対話応答の生成
└────────────────┘
       │
       ▼
   final_response + JSON logs + Neo4j PKG update
```

---

## Ablation Conditions

| Condition | `use_pkg` | `use_rag` | `use_judge` | `is_single` | Purpose |
|-----------|-----------|-----------|-------------|-------------|---------|
| **A** (Full)    | ✓ | ✓ | ✓ | ✗ | 全機能有効 |
| **B** (−PKG)    | ✗ | ✓ | ✓ | ✗ | PKG の役割を観察 |
| **C** (−RAG)    | ✓ | ✗ | ✓ | ✗ | RAG の役割を観察 |
| **D** (Single)  | ✓ | ✓ | ✓ | ✓ | パイプライン分解なし（単一エージェント） |

---

## Directory Structure

```
.
├── docker-compose.yml         # Neo4j (community) コンテナ定義
├── requirements.txt           # Python 依存関係
├── .env.sample                # 環境変数テンプレート
├── neo4j/                     # Neo4j データ永続化 (Docker volume)
└── newresearch/               # ★ メインパッケージ
    ├── config.py              # RunConfig, ABLATION_CONDITIONS, AzureSettings
    ├── schemas.py             # Pydantic I/O スキーマ（全エージェント）
    ├── scenarios.py           # 10 シナリオ × 3 ペルソナ定義
    ├── seed_pkg.py            # Neo4j PKG シードスクリプト
    ├── neo4j_pkg.py           # Neo4j PKG リーダー
    ├── pkg_store.py           # PKG 読み書き（動的グラフ更新）
    ├── pipeline.py            # マルチエージェントパイプライン (条件 A/B/C)
    ├── pipeline_single.py     # シングルエージェントパイプライン (条件 D)
    ├── runner.py              # アブレーション実験ランナー（PKG 自動リセット付き）
    ├── metrics.py             # メトリクス抽出 → CSV
    ├── run_A/B/C/D.py         # 条件別実行スクリプト
    ├── agents/
    │   ├── base.py            # BaseAgent (Azure OpenAI 呼び出し + ログ)
    │   ├── context.py         # ContextAgent — O/A 抽出 + トリガー
    │   ├── explorer.py        # ExplorerAgent — Web 検索 + LLM 解釈
    │   ├── hypothesis.py      # HypothesisAgent — 多様な仮説生成
    │   ├── judge.py           # JudgeAgent — 診断型評価
    │   ├── decision.py        # DecisionAgent — 2 仮説対比選択
    │   ├── dialogue.py        # DialogueAgent — 共感 + ナッジ応答
    │   └── single.py          # SingleAgent (条件 D 用)
    ├── prompts/               # エージェントプロンプト (.txt)
    └── results/
        ├── runs/{A,B,C,D}/    # 各実行ログ (JSON)
        └── figures/           # 生成グラフ
```

---

## Scenarios

10 シナリオ × 3 ペルソナ = 30 ペア。各シナリオは正解が存在しない創造的判断を要求し、
特定の認知バイアスカテゴリをストレステストする。

| ID | バイアスカテゴリ | 概要 |
|----|-----------------|------|
| S1 | Authenticity | 「ガイドブックに載っていない本物の生活を歩きたい」 |
| S2 | Efficiency | 「分刻みスケジュールで効率最大化したい」 |
| S3 | Expertise | 「金沢の伝統建築は誰よりも分かっている」 |
| S4 | Authenticity | 「観光客向け飲食店には絶対入りたくない」 |
| S5 | Efficiency | 「徹底的にコストを抑えた旅行計画」 |
| S6 | Expertise | 「屋久島の森のことは誰よりも分かっている」 |
| S7 | Safety | 「海外旅行はツアーでしか行かない」 |
| S8 | Nostalgia | 「学生時代の京都の感動を取り戻したい」 |
| S9 | Cost | 「旅館に一泊3万円は高すぎる」 |
| S10 | Record | 「SNS用の完璧な写真を撮ることが旅の目的」 |

### Personas

Nemotron-Personas-Japan データセットから選定した 3 ペルソナ。

| ID | 名前 | 属性 | PKG |
|----|------|------|-----|
| P01 | 杉浦 泰章 | 47歳, 郵便局勤務, 新潟県 — 里山散策・地域行事・書道 | 10 nodes, 8 edges |
| P05 | 鈴木 弥一 | 53歳, 遊技場経営, 千葉県 — データ分析・節約志向・レトロゲーム | 10 nodes, 8 edges |
| P07 | 岡田 咲弥 | 27歳, 農業, 宮城県 — 計画的運営・地域文化・有機野菜ブランド | 10 nodes, 8 edges |

---

## Quick Start

セットアップの詳細は [SETUP.md](SETUP.md) を参照。

```bash
# 1. 仮想環境 + 依存関係
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 環境変数
cp .env.sample .env   # → 実際の API キーを設定

# 3. Neo4j 起動 + PKG シード
docker compose up -d graph-db
python -m newresearch.seed_pkg

# 4. Single run
#    ⚠ WARNING: run_A/B/C/D.py do NOT reset PKG before execution.
#    Running them consecutively may cause cross-run contamination.
#    Use `runner.py --all` for reproducible experiments.
python -m newresearch.run_A --scenario S1 --persona P01

# 5. Full ablation (4 conditions × 10 scenarios × 3 personas)
#    PKG is automatically reset (reset_to_seed) before each run — no manual init needed.
#    If interrupted, already-completed runs for the day are auto-skipped on restart.
python -m newresearch.runner --all

# Subset examples
python -m newresearch.runner --all --conditions A B
python -m newresearch.runner --all --personas P01 --scenarios S1 S2 S3

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

各実行は `newresearch/results/runs/{condition}/{run_id}/` に以下を生成：

| File | Content |
|------|---------|
| `config.json` | 実行設定 (条件フラグ、ペルソナ、シナリオ) |
| `context.json` | 観察 (O)、仮定 (A)、トリガー、RAG クエリ |
| `evidence.json` | 外部エビデンス + 外部観察 (Oext) |
| `hypotheses.json` | 3–5 仮説 (explains, assumes, predictions, discriminating_questions) |
| `judgements.json` | 診断結果 (fatal_flaws, explains_confirmed, safety_risk_notes) |
| `decision.json` | 2 仮説対比選択 + user_facing_frame |
| `final.json` | 最終応答 + empathy/nudge マーカー |
| `response.txt` | プレーンテキスト応答 |

---

## Neo4j Data Model

```
(:ExpUser {persona_id, name, summary})
  -[:HAS_PKG_NODE]->
(:PKGNode {node_id, label, type, weight})
  -[:motivates|drives|requires|strengthens|...]->
(:PKGNode)
```

**Dynamic graph update:** Under conditions A/C (`use_pkg=true`), observations, triggers,
hypotheses, judgements, and decisions are written to Neo4j during pipeline execution,
dynamically extending the PKG.

**Automatic PKG reset:** `runner.py` calls `reset_to_seed()` immediately before each run,
deleting all runtime-generated nodes (those with a `source` property) and restoring the
graph to its seed state. This prevents cross-run contamination and guarantees that every
run starts from the same initial PKG (10 nodes, 8 edges).

**⚠ Note:** `run_A.py` / `run_B.py` / `run_C.py` / `run_D.py` do **NOT** call
`reset_to_seed()`. Running them consecutively without manual reset may cause
cross-run contamination in Neo4j.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| LLM | Azure OpenAI (GPT-4.1) |
| Knowledge Graph | Neo4j Community Edition (Docker) |
| Web Search | Serper API / Google Custom Search / Bing Search (`SEARCH_PROVIDER` 環境変数で切替) |
| Data Validation | Pydantic v2 |
| Language | Python 3.10+ |

---

## References

1. **Nemotron-Personas-Japan** — ペルソナデータセットの基盤
   - NVIDIA. *Nemotron-CC: Curating High-Quality Synthetic Data for LLM Training.* 2024.
   - 本実験の 3 ペルソナ (P01, P05, P07) は Nemotron-Personas-Japan データセットから選定・拡張。

2. **Peirce's Abductive Inference** — 推論フレームワークの理論的基盤
   - Peirce, C. S. *Collected Papers of Charles Sanders Peirce.* Harvard University Press, 1931–1958.

3. **Personal Knowledge Graphs (PKG)** — ユーザーモデリング
   - Balog, K., & Kenter, T. *Personal Knowledge Graphs: A Research Agenda.* ICTIR 2019.

4. **Agent-as-a-Judge** — LLM による診断的評価
   - Zhuge, M., et al. *Agent-as-a-Judge: Evaluate Agents with Agents.* arXiv:2410.10934, 2024.

5. **Nudge Theory** — 行動変容のための選択設計
   - Thaler, R. H., & Sunstein, C. R. *Nudge: Improving Decisions About Health, Wealth, and Happiness.* Yale University Press, 2008.

6. **Neo4j** — グラフデータベース
   - Neo4j, Inc. *The Neo4j Graph Database.* https://neo4j.com/

7. **Azure OpenAI Service** — LLM 推論基盤
   - Microsoft. *Azure OpenAI Service.* https://azure.microsoft.com/products/ai-services/openai-service
   - 本実験では GPT-4.1 デプロイメントを使用。

8. **Serper API** — Web 検索 API
   - Serper. *Google Search API.* https://serper.dev/

---

## License

MIT License
