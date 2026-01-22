# Multi-Agent System with Azure OpenAI, LangChain, and Neo4j

マルチエージェントシステム - Azure OpenAI、LangChain、Neo4jを使用した高度な会話AIシステム

## 🌟 概要

このプロジェクトは、7つの専門AIエージェントが協調して動作するマルチエージェントシステムです。ユーザーの入力を分析し、外部情報を探索し、仮説を立て、検証し、最終的にユーザー属性に基づいたパーソナライズされたナッジメッセージを生成します。

### エージェント構成

1. **Context Agent** (旧 Perception Agent) - ユーザー入力からナレッジグラフを作成
2. **Chair Agent** (1回目) - 議題と会話の方向性を決定
3. **Explorer Agent** - Serper API（Google検索）を使用して外部情報を探索
4. **Abstract Agent** (旧 Witness Agent) - 探索結果から仮説を生成
5. **Critic Agent** - 仮説を検証
6. **Chair Agent** (2回目) - 仮説の優先順位付け
7. **Dialog Agent** (旧 Nudge Agent) - パーソナライズされた出力を生成

## 🏗️ アーキテクチャ

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Context Agent                         │
│   - Knowledge Graph作成                 │
│   - エンティティ・関係性抽出             │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Chair Agent (議題設定)                │
│   - 会話の方向性決定                     │
│   - サブトピック分解                     │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Explorer Agent                        │
│   - Serper API (Google検索)による        │
│     外部情報探索                         │
│   - 関連性評価                           │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Abstract Agent                        │
│   - 仮説生成                             │
│   - 抽象化・洞察導出                     │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Critic Agent                          │
│   - 仮説検証                             │
│   - 議題との整合性確認                   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Chair Agent (優先順位付け)            │
│   - ユーザー属性に基づく優先順位決定     │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Dialog Agent                          │
│   - パーソナライズされたナッジ生成       │
│   - 行動変容の促進                       │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Neo4j Database                        │
│   - 会話履歴保存                         │
│   - ユーザー属性管理                     │
│   - ナレッジグラフ保存                   │
└─────────────────────────────────────────┘
```

## 📁 プロジェクト構造

```
AI-one-hour/
├── src/
│   ├── agents/              # AIエージェント
│   │   ├── base_agent.py    # ベースエージェントクラス
│   │   ├── context.py       # Context Agent
│   │   ├── chair.py         # Chair Agent
│   │   ├── explorer.py      # Explorer Agent
│   │   ├── abstract.py      # Abstract Agent
│   │   ├── critic.py        # Critic Agent
│   │   └── dialog.py        # Dialog Agent
│   ├── models/              # データモデル
│   │   └── schemas.py       # Pydanticスキーマ
│   ├── orchestration/       # オーケストレーション
│   │   └── workflow.py      # LangGraphワークフロー
│   ├── utils/               # ユーティリティ
│   │   ├── config.py        # 設定管理
│   │   ├── neo4j_client.py  # Neo4jクライアント
│   │   ├── azure_openai_client.py  # Azure OpenAIクライアント
│   │   ├── serper_client.py # Serper API (Google検索)クライアント
│   │   ├── logger.py        # 会話ログ管理
│   │   └── visualizer.py    # ワークフロー可視化
│   └── main.py              # メインアプリケーション
├── tests/                   # テスト
│   └── test_system.py
├── logs/                    # 会話ログ（自動生成）
├── cli.py                   # CLIインターフェース
├── docker-compose.yml       # Docker設定
├── requirements.txt         # Python依存関係
├── .env                     # 環境変数
├── workflow_diagram.mermaid # ワークフロー図（自動生成）
├── workflow_diagram.html    # ワークフロー図HTML（自動生成）
├── .gitignore
└── README.md
```

## 🚀 セットアップ

### 1. Neo4jの起動

```bash
# Docker Composeでneo4jを起動
docker-compose up -d

# ブラウザでNeo4jにアクセス
# http://localhost:7474
```

### 2. Python仮想環境のセットアップ

```bash
# 仮想環境作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate  # macOS/Linux
# または
.\venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env`ファイルに以下の設定が必要です:

```env
# Azure OpenAI設定
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# Neo4j設定
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=
NEO4J_PASSWORD=

# Serper API設定（Google検索API）
# https://serper.dev/ でAPIキーを取得してください
SERPER_API_KEY=your_serper_api_key_here
```

#### Serper APIキーの取得方法

1. [Serper.dev](https://serper.dev/)にアクセス
2. アカウントを作成（無料プランあり）
3. ダッシュボードでAPIキーを取得
4. `.env`ファイルの`SERPER_API_KEY`に設定

**注意**: Serper APIが設定されていない場合、Explorer AgentはLLMの知識のみを使用します。

## 💻 使用方法

### インタラクティブモード

```bash
python cli.py --user your_user_id
```

対話形式でシステムと会話できます。

### シングルメッセージモード

```bash
python cli.py --user your_user_id --message "健康的な食事について教えてください"
```

### ユーザー属性の更新

```bash
python cli.py --user your_user_id --update-attrs '{"demographics": {"age": 35, "gender": "male"}, "preferences": {"communication_style": "formal"}}'
```

### CLIコマンド一覧

インタラクティブモード内で使用できるコマンド:

- `exit` / `quit` - セッション終了
- `new` - 新しい会話を開始
- `update` - ユーザー属性を更新

## 🧪 テスト

```bash
# テスト実行
pytest tests/ -v

# または特定のテストファイル
python tests/test_system.py
```

## 📊 Neo4jデータモデル

### ノードタイプ

- **User** - ユーザー情報
  - `user_id`: ユーザーID
  - `preferences`: 好み
  - `demographics`: 人口統計情報
  - `behavior_patterns`: 行動パターン
  - `nudge_receptivity`: ナッジ受容性

- **Conversation** - 会話セッション
  - `conversation_id`: 会話ID
  - `created_at`: 作成日時
  - `metadata`: メタデータ

- **Message** - メッセージ
  - `message_id`: メッセージID
  - `role`: ロール (user/assistant)
  - `content`: 内容
  - `agent_name`: エージェント名
  - `timestamp`: タイムスタンプ

- **Entity** - エンティティ (ナレッジグラフ)
  - `name`: 名前
  - `type`: タイプ
  - `properties`: プロパティ

### リレーションシップ

- `(User)-[:HAS_CONVERSATION]->(Conversation)`
- `(Conversation)-[:CONTAINS]->(Message)`
- `(Conversation)-[:EXTRACTED_ENTITY]->(Entity)`
- `(Entity)-[:RELATES_TO]->(Entity)`

## 🔧 技術スタック

- **Azure OpenAI** - GPT-4.1を使用した自然言語処理
- **LangChain** - LLMアプリケーションフレームワーク
- **LangGraph** - マルチエージェントワークフローオーケストレーション
- **Neo4j** - グラフデータベース
- **Pydantic** - データバリデーション
- **Python 3.8+** - プログラミング言語

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📞 サポート

問題が発生した場合は、GitHubのissueを作成してください。
