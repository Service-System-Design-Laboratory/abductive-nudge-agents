# セットアップガイド

このガイドは、Abductive Nudge Agents プロジェクトのセットアップ手順を説明します。

詳細なプロジェクト説明は [README.md](README.md) を参照してください。

## 前提条件

- **Python 3.10-3.13** 推奨（3.14でも動作可能）
- **Docker & Docker Compose** - Neo4j実行用
- **Azure OpenAI API** アカウント
- **Serper API** アカウント（オプション、Google検索機能用）

## ステップバイステップセットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd abductive-nudge-agents
```

### 2. Neo4jの起動

```bash
# Docker Composeでneo4jコンテナを起動
docker-compose up -d

# 起動確認
docker ps | grep neo4j

# Neo4jブラウザを開く（ブラウザで以下にアクセス）
# http://localhost:7474
```

Neo4jブラウザでは認証なしでアクセスできます（`docker-compose.yml`で`NEO4J_AUTH=none`設定済み）。

### 3. Python仮想環境のセットアップ

```bash
# 仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
# macOS/Linux:
source .venv/bin/activate

# Windows:
# .venv\Scripts\activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

**Python 3.14を使用する場合:**

一部のパッケージ（pydantic-core）のビルド時にPyO3の互換性問題が発生する可能性があります。以下の環境変数を設定してください:

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env.sample`ファイルをコピーして`.env`ファイルを作成します:

```bash
# .env.sampleを.envにコピー
cp .env.sample .env
```

`.env`ファイルを開き、以下の項目に実際の値を設定します:

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
# https://serper.dev/ でAPIキーを取得してください
SERPER_API_KEY=your_serper_api_key_here
```

**API キーの取得方法:**

- **Azure OpenAI**: [Azure Portal](https://portal.azure.com/) でOpenAIリソースを作成し、APIキーとエンドポイントを取得
- **Serper API** (オプション): [Serper.dev](https://serper.dev/) でアカウントを作成し、APIキーを取得（無料プランあり）

**注意**: Serper APIキーが未設定の場合、ExplorerAgentはLLMの既存知識のみを使用します。

### 5. Personal Knowledge Graph (PKG) のシード

```bash
# 3つのペルソナをNeo4jデータベースにシード
python -m newresearch.seed_pkg
```

成功すると、以下のペルソナがデータベースに登録されます:

- **P01**: 杉浦 泰章 - 10ノード、8エッジ（里山散策、地域行事、書道など）
- **P05**: 鈴木 弥一 - 10ノード、8エッジ（データ分析、節約志向、レトロゲームなど）
- **P07**: 岡田 咲弥 - 10ノード、8エッジ（計画的運営、地域文化、有機野菜など）

### 6. 動作確認

#### Neo4j接続テスト

```bash
# Neo4jブラウザ (http://localhost:7474) でCypherクエリを実行
MATCH (u:ExpUser) RETURN u.name, u.persona_id
```

3つのペルソナが表示されれば成功です。

#### システムテスト

```bash
# テストを実行（オプション）
pytest tests/ -v
```

### 7. 実験の実行

#### 単一シナリオの実行

```bash
# 実験条件A（Full: PKG + RAG + Judge）でシナリオS1を実行
python -m newresearch.run_A --scenario S1

# 他の条件も実行可能
python -m newresearch.run_B --scenario S1  # -PKG
python -m newresearch.run_C --scenario S1  # -RAG
python -m newresearch.run_D --scenario S1  # -Judge
```

#### 全実験の実行

```bash
# 全条件・全シナリオを実行
python -m newresearch.runner
```

実行結果は `newresearch/results/runs/` に保存されます。

## トラブルシューティング

### 1. Python 3.14でpydantic-coreのビルドエラー

**症状**: `PyO3's maximum supported version (3.13)` エラー

**解決策**:
```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
```

### 2. Neo4j接続エラー

**症状**: `Unable to connect to Neo4j`

**解決策**:
```bash
# Neo4jコンテナの状態確認
docker ps -a | grep neo4j

# ログ確認
docker logs <container-id>

# 再起動
docker-compose restart

# 完全な再起動が必要な場合
docker-compose down
docker-compose up -d
```

### 3. Azure OpenAI API エラー

**症状**: `401 Unauthorized` または `429 Too Many Requests`

**解決策**:
1. `.env`ファイルのAPIキーとエンドポイントを確認
2. Azure OpenAIのデプロイメント名が正しいか確認（`gpt-4.1`など）
3. クォータ制限に達していないかAzure Portalで確認
4. API バージョンが最新か確認

### 4. Serper API エラー

**症状**: Serper API関連のエラー

**解決策**:
- Serper APIキーが設定されていない場合、ExplorerAgentはLLMの知識のみを使用（正常動作）
- APIキーを使用したい場合は [Serper.dev](https://serper.dev/) で取得し `.env` に設定

### 5. PKGシードエラー

**症状**: `ExpUser 'P01' not found`

**解決策**:
```bash
# PKGを再シード
python -m newresearch.seed_pkg

# Neo4jブラウザで確認
# http://localhost:7474
# Cypherクエリ: MATCH (u:ExpUser) RETURN u
```

## Neo4jブラウザでのデータ確認

Neo4jブラウザ（http://localhost:7474）で以下のCypherクエリを実行してデータを確認できます:

### ペルソナの確認

```cypher
// すべてのペルソナを表示
MATCH (u:ExpUser) 
RETURN u.persona_id, u.name

// 特定ペルソナのPKGを表示
MATCH (u:ExpUser {persona_id: "P01"})-[:HAS_PKG_NODE]->(n:PKGNode)
RETURN u, n

// PKGノード間の関係を表示
MATCH (u:ExpUser {persona_id: "P01"})-[:HAS_PKG_NODE]->(n1:PKGNode)-[r]->(n2:PKGNode)
RETURN n1, r, n2
```

### データのクリア（必要な場合）

```cypher
// すべてのデータを削除（注意: 実験データも消えます）
MATCH (n)
DETACH DELETE n
```

## 次のステップ

### 1. 実験の実行

単一シナリオから始めて、システムの動作を確認してください:

```bash
# シナリオS1を条件A（Full）で実行
python -m newresearch.run_A --scenario S1
```

### 2. 結果の確認

実行結果は `newresearch/results/runs/` 以下に保存されています:

- `context.json` - 観察(O)と仮定(A)
- `evidence.json` - 外部エビデンス（RAG結果）
- `hypotheses.json` - 生成された仮説
- `judge.json` - 診断結果
- `decision.json` - 選択された仮説
- `dialogue.json` - 最終的な対話応答

### 3. メトリクスの分析

複数の実験を実行した後、メトリクスを抽出・可視化できます:

```bash
# メトリクスをCSVに抽出
python -m newresearch.metrics

# 結果を可視化
python -m newresearch.visualize
```

### 4. CLIモードの探索（旧実装）

インタラクティブなCLIモードも利用可能です:

```bash
python cli.py --user test_user
```

## 開発者向け情報

### プロジェクト構造

- `newresearch/` - メイン研究実装
  - `agents/` - 各エージェントの実装
  - `prompts/` - エージェントプロンプト
  - `results/` - 実験結果
- `src/` - 旧実装（参考用）
- `neo4j/` - Neo4jデータ永続化

### 詳細ドキュメント

- [README.md](README.md) - プロジェクト概要とアーキテクチャ
- [newresearch/README.md](newresearch/README.md) - 研究デザインと実験プロトコル

### 開発モード

詳細なログを確認したい場合は、各スクリプト内のログレベルを調整してください。

## よくある質問（FAQ）

**Q: Python 3.14は必須ですか？**

A: いいえ。Python 3.10-3.13を推奨します。3.14でも動作しますが、一部パッケージのビルド時に追加の設定が必要になる場合があります。

**Q: Serper APIは必須ですか？**

A: いいえ。オプションです。未設定の場合、ExplorerAgentはLLMの既存知識のみを使用します。実験条件C (-RAG)では使用されません。

**Q: Neo4jの認証情報は何ですか？**

A: `docker-compose.yml`で`NEO4J_AUTH=none`と設定しているため、認証なしでアクセスできます。セキュリティが必要な環境では設定を変更してください。

**Q: 実験結果はどこに保存されますか？**

A: `newresearch/results/runs/{run_id}/` 以下に各実行のJSON形式の結果が保存されます。

**Q: エラーが発生した場合はどうすればよいですか？**

A: 上記の「トラブルシューティング」セクションを参照してください。解決しない場合はGitHubのissueを作成してください。

## サポート

問題が発生した場合は、以下の情報を含めてGitHubのissueを作成してください:

1. Pythonバージョン（`python --version`）
2. OSとバージョン
3. エラーメッセージの全文
4. 実行したコマンド
5. `.env`ファイルの内容（APIキーは除く）
