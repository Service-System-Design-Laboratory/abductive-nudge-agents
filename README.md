# Abductive Nudge Agents

**Empathy-Driven Abductive Reasoning in Multi-Agent Dialogue Systems**

アブダクティブ推論（仮説生成型推論）とマルチエージェントシステムを活用した、共感的対話システムの研究実装プロジェクトです。

## 🌟 概要

このプロジェクトは、6つの専門AIエージェントが協調してアブダクティブ推論サイクルを実行し、ユーザーの発話から観察を抽出し、仮説を生成・検証し、共感的かつパーソナライズされたナッジメッセージを生成する対話システムです。

### 主要な特徴

- **アブダクティブ推論パイプライン**: 観察(O) → 仮定(A) → 仮説(H) → 診断 → 選択のサイクルを実装
- **パーソナルナレッジグラフ(PKG)**: Neo4jを使用したユーザー属性・興味・価値観の構造化表現
- **外部エビデンス検索(RAG)**: Serper APIによるリアルタイム情報収集
- **診断的評価**: Agent-as-a-Judge による仮説の致命的欠陥検出と説明力評価
- **実験的デザイン**: 4条件（Full, -PKG, -RAG, -Judge）でのアブレーション実験に対応

### エージェント構成

1. **ContextAgent** - ユーザー発話から観察(O)と仮定(A)を抽出、トリガーとRAGクエリを生成
2. **ExplorerAgent** - Serper API検索と外部観察(Oext)の抽出
3. **HypothesisAgent** - 多様な仮説(H)の生成（各仮説は説明対象・予測・判別質問を含む）
4. **JudgeAgent** - 診断的評価（致命的欠陥、説明力、判別質問の有効性）
5. **DecisionAgent** - 2仮説の対比的選択
6. **DialogueAgent** - 共感とナッジと判別質問を含む対話応答の生成

## 🏗️ アーキテクチャ

### アブダクティブ推論サイクル

```
User Input
    ↓
┌─────────────────────────────────────────┐
│ ContextAgent                            │
│ • 観察(O): 確定的事実の抽出             │
│ • 仮定(A): 暫定的前提の設定             │
│ • Triggers: O/Aのギャップから導出       │
│ • RAG Queries: 未知の情報への問い       │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ ExplorerAgent                           │
│ • Serper API検索実行                    │
│ • 外部観察(Oext)の抽出                  │
│ • URL・ソースタイプの記録               │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ HypothesisAgent                         │
│ • 仮説(H)の多様な生成                   │
│ • 各仮説に対して:                       │
│   - explains: [O1, Oext1...]           │
│   - assumes: [A1...]                   │
│   - predictions: 予測される帰結         │
│   - discriminating_questions: 判別質問  │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ JudgeAgent                              │
│ • 診断的評価（点数なし）:               │
│   - fatal_flaws: 致命的欠陥             │
│   - explains_confirmed: 説明力確認      │
│   - best_discriminating_question 選定   │
│   - safety_risk_notes: リスク注記       │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ DecisionAgent                           │
│ • 2仮説の対比的選択                     │
│ • 質的に異なる説明の切り口を提示        │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ DialogueAgent                           │
│ • Acknowledgement + Reflection (共感)   │
│ • Options + Small Action (ナッジ)       │
│ • 判別質問を含む応答生成                │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ Neo4j Database                          │
│ • Personal Knowledge Graph (PKG)        │
│ • ペルソナ属性・興味・価値観            │
└─────────────────────────────────────────┘
```

## 📁 プロジェクト構造

```
abductive-nudge-agents/
├── newresearch/             # メイン研究実装
│   ├── agents/              # AIエージェント実装
│   │   ├── base.py          # BaseAgent (LLM call + logging)
│   │   ├── context.py       # ContextAgent
│   │   ├── explorer.py      # ExplorerAgent
│   │   ├── hypothesis.py    # HypothesisAgent
│   │   ├── judge.py         # JudgeAgent
│   │   ├── decision.py      # DecisionAgent
│   │   └── dialogue.py      # DialogueAgent
│   ├── prompts/             # エージェントプロンプト
│   │   ├── context.txt
│   │   ├── explorer.txt
│   │   ├── hypothesis.txt
│   │   ├── judge.txt
│   │   ├── decision.txt
│   │   └── dialogue.txt
│   ├── results/             # 実験結果出力
│   │   └── runs/            # 各実行ログ
│   ├── config.py            # 実行設定
│   ├── schemas.py           # Pydanticスキーマ
│   ├── scenarios.py         # 実験シナリオ定義
│   ├── seed_pkg.py          # Neo4j PKGシードスクリプト
│   ├── neo4j_pkg.py         # Neo4j PKGリーダー
│   ├── pipeline.py          # パイプライン実行
│   ├── run_A.py             # 実験条件A (Full)
│   ├── run_B.py             # 実験条件B (-PKG)
│   ├── run_C.py             # 実験条件C (-RAG)
│   ├── run_D.py             # 実験条件D (-Judge)
│   ├── metrics.py           # メトリクス抽出
│   └── visualize.py         # 可視化
├── src/                     # (旧実装・参考用)
│   └── ...
├── neo4j/                   # Neo4jデータ永続化
│   ├── data/
│   ├── logs/
│   └── plugins/
├── tests/                   # テスト
│   └── test_system.py
├── cli.py                   # CLIインターフェース
├── docker-compose.yml       # Neo4j Docker設定
├── requirements.txt         # Python依存関係
├── .env                     # 環境変数（要作成）
└── README.md               # このファイル
```

## 🚀 セットアップ

### 前提条件

- **Python 3.10-3.13** 推奨（3.14でも動作可能だが、一部パッケージでビルド問題が発生する可能性あり）
- **Docker & Docker Compose** - Neo4j実行用
- **Azure OpenAI API** - GPTモデルアクセス用
- **Serper API** (オプション) - Google検索機能用

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd abductive-nudge-agents
```

### 2. Python仮想環境のセットアップ

```bash
# 仮想環境作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -r requirements.txt
```

**Python 3.14を使用する場合の注意:**
一部のパッケージ（pydantic-core）がPyO3のビルドで問題が発生する場合、以下の環境変数を設定してください:

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
```

### 3. Neo4jの起動

```bash
# Docker Composeでneo4jを起動
docker-compose up -d

# Neo4j Browser でアクセス確認
# http://localhost:7474
# 初期認証: なし（docker-compose.ymlでNEO4J_AUTH=none設定済み）
```

### 4. 環境変数の設定

`.env.sample`ファイルをコピーして`.env`ファイルを作成し、実際の値を設定:

```bash
# .env.sampleを.envにコピー
cp .env.sample .env

# エディタで開いて実際の値を設定
# macOS: open .env
# Linux: nano .env または vi .env
```

設定が必要な項目:

```env
# Azure OpenAI設定
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# Neo4j設定
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Serper API設定（オプション）
# https://serper.dev/ でAPIキーを取得
SERPER_API_KEY=your_serper_api_key_here
```

**注意**: 
- Serper APIキーが未設定の場合、ExplorerAgentはLLMの既存知識のみを使用します
- Neo4jの認証をdocker-compose.ymlで無効化している場合、USERNAME/PASSWORDは任意の値で可

### 5. Personal Knowledge Graph (PKG) のシード

```bash
# 3つのペルソナをNeo4jにシード
python -m newresearch.seed_pkg
```

以下のペルソナがデータベースに登録されます:
- **P01**: 杉浦 泰章 (里山散策、地域行事、書道に興味を持つ)
- **P05**: 鈴木 弥一 (データ分析、節約志向、レトロゲームに興味を持つ)
- **P07**: 岡田 咲弥 (計画的運営、地域文化への敬意、有機野菜ブランドに関心を持つ)

## 💻 使用方法

### 単一シナリオ実行

```bash
# 実験条件A（Full: PKG + RAG + Judge）でシナリオS1を実行
python -m newresearch.run_A --scenario S1

# 他の条件でも実行可能
python -m newresearch.run_B --scenario S1  # -PKG
python -m newresearch.run_C --scenario S1  # -RAG
python -m newresearch.run_D --scenario S1  # -Judge
```

### 利用可能なシナリオ

| ID | ユーザー | 発話内容 |
|----|---------|---------|
| S1 | P01 (杉浦) | 「最近、地域の若い人たちが祭りに参加してくれない...」 |
| S2 | P05 (鈴木) | 「従業員のモチベーション管理が...」 |
| S3 | P07 (岡田) | 「有機野菜の販路拡大で悩んでいる...」 |

### 複数実行・メトリクス抽出

```bash
# 全条件・全シナリオを実行
python -m newresearch.runner

# メトリクスをCSV出力
python -m newresearch.metrics

# 可視化
python -m newresearch.visualize
```

### CLIインタラクティブモード（旧実装）

```bash
python cli.py --user your_user_id
```

## 📊 実験デザイン

### 4つの実験条件

| 条件 | PKG | RAG | Judge | 説明 |
|------|-----|-----|-------|------|
| **A (Full)** | ✓ | ✓ | ✓ | 全機能有効 |
| **B (-PKG)** | ✗ | ✓ | ✓ | パーソナルナレッジグラフなし |
| **C (-RAG)** | ✓ | ✗ | ✓ | 外部検索なし |
| **D (-Judge)** | ✓ | ✓ | ✗ | 診断的評価なし |

### 研究課題

| # | 問い |
|---|------|
| RQ1 | 明示的なアブダクティブパイプラインは、仮説の多様性と説明品質にどう影響するか？ |
| RQ2 | PKGと外部エビデンス(RAG)は、仮説の根拠付けとペルソナ整合性にどう寄与するか？ |
| RQ3 | Agent-as-a-Judge診断は、共感的で根拠のある応答の選択を改善するか？ |

## 🧪 テスト

```bash
# テスト実行
pytest tests/ -v

# または特定のテストファイル
python tests/test_system.py
```

## 📊 Neo4jデータモデル

### ノードタイプ

- **ExpUser** - 実験用ペルソナ
  - `persona_id`: ペルソナID（P01, P05, P07）
  - `name`: 名前
  - その他属性

- **PKGNode** - パーソナルナレッジグラフのノード
  - `node_id`: ノードID
  - `label`: ラベル（興味、価値観、スキル、関心事など）
  - `node_type`: タイプ（interest, value, skill, concern）
  - `weight`: 重要度

### リレーションシップ

- `(ExpUser)-[:HAS_PKG_NODE]->(PKGNode)` - ペルソナがPKGノードを持つ
- `(PKGNode)-[:motivates|drives|requires|...]->(PKGNode)` - ノード間の関係性

## 🔧 技術スタック

- **Azure OpenAI** - GPT-4.1を使用したアブダクティブ推論
- **LangChain** - LLMアプリケーションフレームワーク
- **Neo4j** - パーソナルナレッジグラフデータベース
- **Serper API** - リアルタイムGoogle検索
- **Pydantic** - データバリデーション
- **Python 3.10-3.13** - プログラミング言語

## 📝 出力例

各実行は `newresearch/results/runs/{run_id}/` に以下のファイルを生成します:

- `config.json` - 実行設定
- `context.json` - ContextAgentの出力（O/A/triggers）
- `evidence.json` - ExplorerAgentの外部エビデンス
- `hypotheses.json` - HypothesisAgentの生成仮説
- `judge.json` - JudgeAgentの診断結果
- `decision.json` - DecisionAgentの選択結果
- `dialogue.json` - DialogueAgentの最終応答

## 🔍 トラブルシューティング

### Python 3.14でpydantic-coreのビルドエラーが発生する

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
```

### Neo4jに接続できない

1. Docker Composeが起動しているか確認: `docker ps`
2. Neo4j Browser (http://localhost:7474) にアクセスできるか確認
3. `.env`ファイルの`NEO4J_URI`が `bolt://localhost:7687` になっているか確認

### Serper APIエラーが発生する

- Serper APIキーが設定されていない場合、ExplorerAgentはLLMの知識のみを使用（エラーではない）
- APIキーを取得した場合は `.env` の `SERPER_API_KEY` に設定

## 📚 参考文献

詳細な研究デザインと実験プロトコルは [newresearch/README.md](newresearch/README.md) を参照してください。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📞 サポート

問題が発生した場合は、GitHubのissueを作成してください。
