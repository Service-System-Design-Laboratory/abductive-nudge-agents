# Abductive Dialogue Pipeline — Extended Paper Experiment

> **Empathy-Driven Abductive Reasoning in Multi-Agent Dialogue Systems**
>
> This module implements a reproducible experiment for observing how **explicit
> abductive reasoning** (Observation → Assumption → Hypothesis → Diagnosis →
> Selection) contributes to empathetic and creative dialogue, with internal
> ablation across three knowledge-source dimensions: **PKG**, **RAG**, and **Judge**.

---

## 1. Research Questions

| # | Question |
|---|---------|
| RQ1 | How does the explicit abductive pipeline (O/A → Hypothesis → Judge → Decision) shape the **diversity and explanatory quality** of generated hypotheses? |
| RQ2 | What roles do **Personal Knowledge Graphs (PKG)** and **external evidence (RAG)** play in hypothesis grounding and persona alignment? |
| RQ3 | Does **agent-as-a-judge diagnostic review** improve the selection of empathetic, well-grounded responses? |

---

## 2. Core Design: Abductive Reasoning with O/A

### 2.1 Abductive Cycle

The pipeline implements Peirce's abductive inference as a structured agent chain:

```
Observation (O) — facts extracted from user input (cannot be denied)
        ↓
Assumption (A) — tentative premises placed by ContextAgent (revisable)
        ↓
Hypothesis (H) — "best explanation" candidates that explain O under A
        ↓
Prediction (P) — what each H predicts if true
        ↓
Test (T)       — discriminating questions to differentiate Hs
        ↓
Selection      — choose the H with best explanatory fit
        ↓
Response       — empathetic response that includes T to close the loop
```

### 2.2 Design Rules (Per Agent)

| Agent | Key Rules |
|-------|-----------|
| **ContextAgent** | ① O = facts from input only (no interpretation). ② A = tentative + revisable. ③ triggers derive from gaps between O and A. ④ rag_queries target what is unknown. ⑤ 実験条件フラグ (`use_pkg`, `use_rag`) により PKG参照・RAGクエリ生成を制御 |
| **ExplorerAgent** | ① URL required for every evidence item. ② 0 results is acceptable (fallback continues). ③ source_type classification required. ④ **外部観察 (external_observations)** を検索結果から抽出 — 世の中の事実・動向・構造を Oext1, Oext2... として返す。⑤ ユーザー発話の繰り返しは避ける |
| **HypothesisAgent** | ① Each H must declare which O it explains (`explains: [O1, Oext1]`) — ユーザー観察と外部観察の両方を対象にできる. ② Each H must declare its assumptions (`assumes: [A1]`). ③ `predictions` = observable consequences if H is true. ④ `discriminating_questions` = questions that differentiate this H from others. ⑤ `type` must be diverse (≥3 types). ⑥ **条件付き探索空間**: PKG/RAGありの場合は構造的・制度的要因の探索が可能、両方なしの場合は一般原理ベースに留める |
| **JudgeAgent** | ① **点数を付けない（診断型）**。② `fatal_flaws` = 致命的な問題のゲート。③ `explains_confirmed` = 実際に説明できている観察の確認。④ `best_discriminating_question` = 最も判別力のある質問。⑤ `safety_risk_notes` = ユーザーに伝える際のリスク |
| **DecisionAgent** | ① **2仮説対比**で選択（selected + contrasting）。② 2つは「程度の違い」ではなく「質的に異なる説明の切り口」。③ fatal_flawsがある仮説は除外。④ Judge診断の explains_confirmed と type の違いを活用 |
| **DialogueAgent** | ① acknowledgement + reflection (empathy minimum). ② Options + small action (nudge minimum). ③ 2択は2つの仮説から生成（質的対立）。④ Never assert — present as possibility. ⑤ 実験条件フラグにより語彙・トーン・確信度を制御 |

---

## 3. Directory Structure

```
newresearch/
├── README.md              ← This file (design doc + progress log)
├── __init__.py
├── config.py              ← RunConfig & global settings
├── schemas.py             ← Pydantic I/O contracts (all agents)
├── scenarios.py           ← 3 scenarios + get_persona() (Neo4J連携)
├── seed_pkg.py            ← Neo4J PKG シードスクリプト
├── neo4j_pkg.py           ← Neo4J PKG リーダー
├── run_A.py               ← Condition A (Full) 実行ファイル
├── run_B.py               ← Condition B (−PKG) 実行ファイル
├── run_C.py               ← Condition C (−RAG) 実行ファイル
├── run_D.py               ← Condition D (−Judge) 実行ファイル
├── agents/
│   ├── __init__.py
│   ├── base.py            ← BaseAgent (LLM call + logging)
│   ├── context.py         ← ContextAgent  — O/A extraction + triggers
│   ├── explorer.py        ← ExplorerAgent — Serper検索 + LLM解釈
│   ├── hypothesis.py      ← HypothesisAgent — Diversified abductive generation
│   ├── judge.py           ← JudgeAgent    — Agent-as-a-Judge (4-axis)
│   ├── decision.py        ← DecisionAgent — Select 1 hypothesis
│   └── dialogue.py        ← DialogueAgent — Empathy + Nudge + Test question
├── prompts/
│   ├── context.txt
│   ├── explorer.txt       ← Serper検索結果のLLM解釈用
│   ├── hypothesis.txt
│   ├── judge.txt
│   ├── decision.txt
│   └── dialogue.txt
├── pipeline.py            ← End-to-end pipeline orchestrator
├── runner.py              ← 12-run ablation executor (統合版)
├── metrics.py             ← Quantitative metric extraction → CSV
├── visualize.py           ← Figure generation (matplotlib)
└── results/               ← 全出力を格納
    ├── metrics.csv        ← 抽出メトリクス
    ├── figures/            ← 生成グラフ (fig_a〜fig_d)
    └── runs/              ← 各実行ログ (git-ignored)
        └── {run_id}/
            ├── config.json
            ├── context.json
            ├── evidence.json
            ├── hypotheses.json
            ├── judgements.json
            ├── decision.json
            └── final.json
```

---

## 4. Pipeline Architecture

```
user_input + persona + PKG + config
        │
        ▼
┌──────────────┐
│ ContextAgent │  Extract O (observations), A (assumptions), triggers, rag_queries
└──────┬───────┘  [config flags injected: use_pkg, use_rag]
       │
       ▼
┌──────────────┐
│ExplorerAgent │  Serper API → LLM interpretation
└──────┬───────┘  ① evidence_items (従来の証拠)
       │          ② external_observations (外部事実 → Oext1, Oext2...)
       │          [skip if use_rag=false]
       ▼
┌────────────────┐
│HypothesisAgent │  3–5 hypotheses: explains O+Oext, assumes A, predicts P, tests T
└──────┬─────────┘  [PKG seeds diversity if use_pkg=true]
       │            [条件付き探索空間: PKG/RAGの有無で探索の深さが変化]
       ▼
┌────────────┐
│ JudgeAgent │  Diagnostic review (no scores)
└──────┬─────┘  fatal_flaws / explains_confirmed / best_discriminating_question
       │        / safety_risk_notes  [skip if use_judge=false]
       ▼
┌───────────────┐
│ DecisionAgent │  Select 2 Hs for contrast (selected + contrasting)
└──────┬────────┘  → user_facing_frame (質的に異なる2択 + 判別質問)
       │
       ▼
┌────────────────┐
│ DialogueAgent  │  Empathy + Nudge + 2仮説対比による判別質問
└────────────────┘  [語彙・トーン・確信度は実験条件フラグで制御]
       │
       ▼
   final_response + full JSON logs
```

---

## 5. Ablation Conditions

| Condition | `use_pkg` | `use_rag` | `use_judge` | Purpose |
|-----------|-----------|-----------|-------------|---------|
| **A** (Full) | ✓ | ✓ | ✓ | All components active |
| **B** (−PKG) | ✗ | ✓ | ✓ | Observe PKG's role in persona alignment & hypothesis diversity |
| **C** (−RAG) | ✓ | ✗ | ✓ | Observe RAG's role in evidence grounding |
| **D** (−Judge) | ✓ | ✓ | ✗ | Observe Judge's role in hypothesis selection quality |

---

## 6. Scenarios (Creative Judgment Scenarios)

各シナリオは「正解が存在しない創造的判断」を要求し、特定のアブレーション変数をストレステストするよう設計されている。

| ID | Focus | Stress Target | Input (user_input) |
|----|-------|---------------|---------------------|
| **S1** | Conflicting evaluation | **Judge** — 矛盾するフィードバック下での仮説優先順位付け | 対話システムについて「技術的に面白い」vs「ユーザー価値が分かりにくい」の矛盾するフィードバック。手応えを感じつつ方向性を迷っている。 |
| **S2** | Persona-dependent direction | **PKG** — 個人の価値観・スキルに基づく二者択一 | 「新しい対話モデル設計」vs「既存システムのユーザー調査評価」どちらを主軸にするか。限られた時間での判断。 |
| **S3** | Trend-dependent future decision | **RAG** — 外部動向に基づく不確実な将来判断 | 「対話の共感性・体験向上」vs「安全性・評価フレームワーク」どちらに注力するか。判断材料が不足。 |

All scenarios use a **single fixed persona** (田中翔太: 学部4年, 情報工学・AI専攻, 10 PKG nodes, 7 edges).

---

## 7. Agent I/O Contracts (JSON)

### 7.1 ContextAgent

```json
{
  "observations": [
    {"id": "O1", "text": "fact extracted from input"}
  ],
  "assumptions": [
    {"id": "A1", "text": "tentative premise", "status": "tentative"}
  ],
  "triggers": [
    {"type": "information_gap | ambiguity | contradiction | focus", "text": "..."}
  ],
  "questions": ["..."],
  "rag_queries": ["..."],
  "constraints": {"tone": "supportive", "safety": "avoid determinism"}
}
```

### 7.2 ExplorerAgent

```json
{
  "evidence_items": [
    {"rank": 1, "title": "...", "snippet": "...", "url": "https://...", "source_type": "edu|gov|org|com|other"}
  ],
  "external_observations": [
    {"id": "Oext1", "text": "外部世界の事実・動向を1文で", "source_url": "https://..."}
  ],
  "notes": ""
}
```

### 7.3 HypothesisAgent

```json
{
  "hypotheses": [
    {
      "hypothesis_id": "H1",
      "type": "psychological | environmental | social | skill | value | evidence_gap | goal_mismatch | constraint_conflict | other",
      "explains": ["O1", "O2"],
      "assumes": ["A1"],
      "statement": "...",
      "mechanism": "...",
      "predictions": ["if true, then ..."],
      "discriminating_questions": ["question that differentiates this H from others"],
      "persona_link": ["pkg:node_id"],
      "evidence_link": ["ev:1"]
    }
  ]
}
```

### 7.4 JudgeAgent (Diagnostic — No Scores)

```json
{
  "judgements": [
    {
      "hypothesis_id": "H1",
      "diagnosis": {
        "fatal_flaws": [],
        "explains_confirmed": ["O1", "O2", "Oext1"],
        "key_assumptions": ["前提の説明"],
        "best_discriminating_question": "この仮説を他と区別する質問",
        "testability_notes": "検証しやすさの説明",
        "safety_risk_notes": "提示時のリスク"
      },
      "rationale": "..."
    }
  ]
}
```

### 7.5 DecisionAgent (2-Hypothesis Contrast)

```json
{
  "selected_hypothesis_id": "H2",
  "contrasting_hypothesis_id": "H4",
  "selection_rationale": "選択理由と対比の意図（2-3文）",
  "user_facing_frame": {
    "framing": "options",
    "questions": ["どちらの見方が今の感覚に近いですか？"],
    "options": ["H2の説明を1文で", "H4の説明を1文で"]
  }
}
```

### 7.6 DialogueAgent

```json
{
  "final_response": "...",
  "markers": {
    "empathy": {
      "acknowledgement": true,
      "reflection": true,
      "perspective_prompt": false
    },
    "nudge": {
      "has_question": true,
      "has_options": true,
      "has_small_action": true,
      "directive_level": "low"
    }
  }
}
```

---

## 8. Metrics (Observational — No Statistical Claims)

| Category | Metric | Source |
|----------|--------|-------|
| **Hypothesis Diversity** | `hypothesis_count` | hypotheses.json |
| | `type_diversity` (unique types) | hypotheses.json |
| **Observation Space** | `observation_count` (user + external) | context.json + evidence.json |
| | `external_observation_count` | evidence.json |
| **Abductive Structure** | `observation_coverage` (% of O explained by ≥1 H) | hypotheses + context |
| | `avg_predictions_per_h` | hypotheses.json |
| | `avg_disc_questions_per_h` | hypotheses.json |
| **Judge Diagnostics** | `fatal_flaw_avoided` (0/1) | judgements + decision |
| | `fatal_flaw_h_count` | judgements.json |
| | `selected_explains_count` | judgements.json |
| | `selected_is_max_explains` (0/1) | judgements + decision |
| | `discriminating_q_coverage` (0-1) | judgements.json |
| **2-Hypothesis Contrast** | `has_contrasting` (0/1) | decision.json |
| | `contrast_type_diff` (0/1) | decision + hypotheses |
| **Source Utilisation** | `persona_link_count` / `_unique` / `_per_h` | hypotheses.json |
| | `evidence_link_count` / `_unique` / `_per_h` | hypotheses.json |
| **Empathy / Nudge** | empathy marker rate (3 types) | final.json |
| | nudge marker rate (3 types) | final.json |
| | `directive_level` distribution | final.json |

---

## 9. Planned Figures

| Figure | Type | Content |
|--------|------|---------|
| Fig. A | Bar | Judge diagnostic quality by condition (fatal_flaw_avoided, explains coverage, discriminating_q, contrast_type_diff) |
| Fig. B | Grouped Bar | `type_diversity` by ablation condition |
| Fig. C | Stacked Bar | Empathy/Nudge marker rates by condition |
| Fig. D | Table | Per-run summary (scenario × condition → key metrics) |

---

## 10. Execution

```bash
# Run all 12 ablation experiments
python -m newresearch.runner --all

# Run a single condition
python -m newresearch.runner --scenario S1 --condition A

# Collect metrics → CSV
python -m newresearch.metrics

# Generate figures
python -m newresearch.visualize
```

### Execution Matrix: 3 scenarios × 4 conditions = **12 runs**

---

## 11. Fallback Handling

| Failure | Recovery |
|---------|----------|
| JSON parse error | 1× repair prompt retry |
| 0 evidence items | Continue; Hypothesis generates without evidence_link |
| 0 external_observations | Continue; Hypothesis uses user observations only |
| Too few hypotheses | 1× regeneration with explicit count constraint |
| No contrasting hypothesis | DecisionAgent falls back to best single H |

---

## 12. Completion Criteria

- [ ] 12 runs completed without error
- [ ] All JSON logs saved under `runs/`
- [ ] `metrics.csv` generated
- [ ] ≥ 2 figures generated (Judge scores + Empathy/Nudge)

---

## 13. Progress Log

### Phase 1: 初期実装 (2026-02-06 AM)

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-02-06 | README.md (design doc) | ✅ | O/A abduction pattern, design rules per agent, I/O contracts, metrics定義 |
| 2026-02-06 | schemas.py | ✅ | Pydantic models for all agents |
| 2026-02-06 | config.py | ✅ | RunConfig, ABLATION_CONDITIONS (A/B/C/D), AzureSettings |
| 2026-02-06 | scenarios.py (v1) | ✅ | 初期シナリオ3本 + 固定ペルソナ |
| 2026-02-06 | agents/ (6 agents + prompts) | ✅ | Context, Explorer, Hypothesis, Judge, Decision, Dialogue |
| 2026-02-06 | pipeline.py | ✅ | 6エージェント逐次実行 |
| 2026-02-06 | 全12実験実行 | ✅ | 3シナリオ×4条件=12runs 完了 |
| 2026-02-06 | metrics.py / visualize.py | ✅ | CSV出力 + Fig A-D 生成 |

### Phase 2: Neo4J PKG 接続 + 条件分離 (2026-02-06 PM)

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-02-06 | Neo4J PKG 接続 | ✅ | seed_pkg.py → Neo4J 5.15.0。neo4j_pkg.py で `load_persona_from_neo4j()` 実装 |
| 2026-02-06 | 4条件別実行ファイル | ✅ | run_A/B/C/D.py — 各条件を固定し実行 |
| 2026-02-06 | Explorer LLM解釈 | ✅ | Serper → LLM解釈に変更。prompts/explorer.txt が実際に使用 |

### Phase 3: 実験条件の明示化 + 差分強化 (2026-02-06 PM〜)

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-02-06 | **Config flag passing** | ✅ | 全6プロンプト + 全6エージェントに `## 実験条件 (Experimental Condition)` ブロックと `{config_block}` テンプレート変数を追加。`base.py` に `_build_config_block()` ヘルパー |
| 2026-02-06 | **条件付き探索空間** | ✅ | hypothesis.txt に「条件付き探索空間の拡張」ブロック追加。PKG/RAGありの場合のみ構造的・制度的要因を探索可能に。型ではなく生成経路で差を出す設計 |
| 2026-02-06 | **Dialogue語彙制約** | ✅ | dialogue.txt を3ラウンド改訂: ① Judge内部プロセスの非露出 ② use_pkg=false → PKG由来語彙を全禁止、use_rag=false → 外部世界語彙を全禁止 ③ 2択を「質的に異なる説明の対立」に制約 |
| 2026-02-06 | **Scenario redesign** | ✅ | 全3シナリオを「創造的判断シナリオ」として再設計。S1=Judge stress, S2=PKG stress, S3=RAG stress |

### Phase 4: Explorer外部観察 + Judge/Decision構造改革 (2026-02-06)

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-02-06 | **Explorer外部観察** | ✅ | `ExternalObservation` schema追加。検索結果から「外部世界の事実」を Oext1, Oext2... として抽出。Hypothesis の explains 対象に含まれ、RAGあり条件では観察空間自体が拡張される |
| 2026-02-06 | **Judge: 点数型→診断型** | ✅ | `JudgeScores` (4軸×1-5点) を廃止 → `JudgeDiagnosis` に変更: `fatal_flaws`, `explains_confirmed`, `key_assumptions`, `best_discriminating_question`, `testability_notes`, `safety_risk_notes` |
| 2026-02-06 | **Decision: 1仮説→2仮説対比** | ✅ | 「合計点最大を選ぶだけの計算機」問題を解消。`selected_hypothesis_id` + `contrasting_hypothesis_id` で質的に異なる2つの仮説を対比。options は2仮説の核心をそれぞれ1文で |
| 2026-02-06 | **metrics.py 刷新** | ✅ | score系指標を全廃止 → 診断系指標に: `fatal_flaw_avoided`, `selected_explains_count`, `discriminating_q_coverage`, `has_contrasting`, `contrast_type_diff`, `external_observation_count` |
| 2026-02-06 | **検証: A×S1** | ✅ | H2(psychological) × H4(environmental) の対比が生成。「個人の心理的不安」vs「分野全体の環境的要請」という質的に異なる2択 |

### 設計上の重要な判断

1. **Judgeは点数を付けない**: 点数最大を選ぶだけならDecisionAgentは不要。Judgeの価値は「失敗を減らすガードレール」(fatal_flaws, safety_risk) と「判別質問の質を高める」こと
2. **Decisionは2仮説を選ぶ**: 1仮説から2択を作ると「ある/ない」の程度差にしかならない。2仮説を対比させることで「内的要因 vs 外的要因」のような質的対立が生まれる
3. **Explorerは証拠だけでなく観察も出す**: 外部検索で得た情報を evidence_link（仮説の裏付け）だけでなく、external_observations（新しい観察事実）としても扱うことで、RAGあり条件では観察空間自体が広がり、仮説の多様性が構造的に変化する
4. **差分は「型」ではなく「生成経路」で作る**: 仮説タイプを増やしても全条件が同じタイプを出すだけ。PKG/RAGの有無で「何を参照して仮説が生まれたか」が変わることで、自然に差が出る

---

## 14. TODO (今後)

- [ ] 全4条件 × 3シナリオ (12runs) を新パイプラインで実行
- [ ] metrics.csv を新指標で再生成
- [ ] 可視化を新指標に対応させる
- [ ] 試行回数を増やした安定性確認 (各条件×3-5回)
- [ ] ペルソナの追加検討 (Nemotron dataset 10ペルソナ)
