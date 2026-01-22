# セットアップガイド

## 前提条件

- Python 3.8以上
- Docker & Docker Compose
- Azure OpenAIアカウント

## ステップバイステップセットアップ

### 1. リポジトリのクローン（既にある場合はスキップ）

```bash
cd /Users/matsuokahiroshiyou/Documents/programming/AI-one-hour
```

### 2. Neo4jの起動

```bash
# Docker Composeでneo4jコンテナを起動
docker-compose up -d

# 起動確認
docker ps | grep neo4j

# Neo4jブラウザを開く
# http://localhost:7474
```

Neo4jブラウザでは認証なしでアクセスできます（NEO4J_AUTH=none設定のため）。

### 3. Python仮想環境のセットアップ

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate

# Windows:
# .\venv\Scripts\activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 環境変数の確認

`.env`ファイルが既に存在し、以下の内容が含まれています:

```env
AZURE_OPENAI_API_KEY=EQx5NK7BQ5mf1oUvrG55Ad8UxXZ2jYz4YxRD0TqllxJJMi48VJsRJQQJ99BJACYeBjFXJ3w3AAABACOGeZ5b
AZURE_OPENAI_ENDPOINT=https://aoi-res19.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=
NEO4J_PASSWORD=
```

### 5. 動作確認

#### Neo4j接続テスト

```bash
# Python対話モードで確認
python3 -c "from src.utils.neo4j_client import neo4j_db; print('Neo4j connection successful!')"
```

#### システムテスト

```bash
# テストを実行
pytest tests/ -v
```

### 6. システムの起動

#### インタラクティブモード

```bash
python cli.py --user test_user
```

表示されるプロンプトで会話を開始できます:

```
You: 健康的な生活を送りたいです
```

#### シングルメッセージモード

```bash
python cli.py --user test_user --message "運動習慣を身につけたいです"
```

## トラブルシューティング

### Neo4j接続エラー

```bash
# Neo4jコンテナの状態確認
docker ps -a | grep neo4j

# ログ確認
docker logs neo4j-local

# 再起動
docker-compose restart
```

### Python依存関係エラー

```bash
# 仮想環境を削除して再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Azure OpenAI接続エラー

1. `.env`ファイルのAPIキーとエンドポイントを確認
2. Azure OpenAIのデプロイメント名が正しいか確認
3. クォータ制限に達していないか確認

## ユーザー属性の設定

初回使用時にユーザー属性を設定すると、よりパーソナライズされた応答が得られます:

```bash
python cli.py --user your_user_id --update-attrs '{
  "demographics": {
    "age": 30,
    "gender": "male",
    "occupation": "engineer"
  },
  "preferences": {
    "communication_style": "casual",
    "topics_of_interest": ["technology", "health", "fitness"]
  },
  "nudge_receptivity": {
    "social_proof": "high",
    "loss_aversion": "medium",
    "framing": "high"
  }
}'
```

## Neo4jブラウザでのデータ確認

Neo4jブラウザ（http://localhost:7474）で以下のクエリを実行してデータを確認できます:

```cypher
// すべてのユーザーを表示
MATCH (u:User) RETURN u LIMIT 25

// 特定ユーザーの会話履歴
MATCH (u:User {user_id: "test_user"})-[:HAS_CONVERSATION]->(c:Conversation)-[:CONTAINS]->(m:Message)
RETURN u, c, m
ORDER BY m.timestamp

// ナレッジグラフを表示
MATCH (c:Conversation)-[:EXTRACTED_ENTITY]->(e:Entity)
OPTIONAL MATCH (e)-[r:RELATES_TO]->(e2:Entity)
RETURN c, e, r, e2
LIMIT 50
```

## 次のステップ

1. インタラクティブモードで様々な質問を試してみる
2. ユーザー属性を調整して応答の変化を確認
3. Neo4jブラウザで蓄積されたナレッジグラフを確認
4. 複数の会話セッションを作成して履歴を比較

## 開発モード

開発中は詳細なログを有効にすると便利です:

```bash
python cli.py --user dev_user --verbose
```

これにより、各エージェントの処理内容が詳細に表示されます。
