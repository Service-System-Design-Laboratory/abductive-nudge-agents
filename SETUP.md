# セットアップガイド

本プロジェクトの環境構築と実験再現の手順です。
プロジェクト概要は [README.md](README.md) を参照してください。

---

## 前提条件

| 項目 | 要件 |
|------|------|
| Python | 3.10 以上（3.12 推奨） |
| Docker & Docker Compose | Neo4j コンテナ実行用 |
| Azure OpenAI API | GPT-4.1 デプロイメント |
| Web Search API（任意） | Serper / Google Custom Search / Bing のいずれか |

---

## 1. リポジトリのクローン

```bash
git clone <repository-url>
cd AI-one-hour
git checkout plan_masaki
```

---

## 2. Python 仮想環境

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. 環境変数の設定

```bash
cp .env.sample .env
```

`.env` を開いて以下を設定：

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

## 4. Neo4j の起動

```bash
docker compose up -d graph-db
```

起動確認：

```bash
# コンテナ確認
docker ps | grep neo4j-local

# ブラウザでアクセス（認証なし）
# http://localhost:7474
```

> `docker-compose.yml` で `NEO4J_AUTH=none` に設定済みのため、認証不要です。

---

## 5. PKG シードデータの投入

3 ペルソナ（P01, P05, P07）の Personal Knowledge Graph を Neo4j に投入します。

```bash
python -m newresearch.seed_pkg
```

確認：

```bash
python -m newresearch.seed_pkg --check
```

Neo4j Browser (http://localhost:7474) で確認：

```cypher
MATCH (u:ExpUser) RETURN u.persona_id, u.name
```

3 ペルソナが表示されれば成功です。

---

## 6. 実験の実行

### 単一シナリオ実行

```bash
# 条件 A (Full: PKG + RAG + Judge) × S1 × P01
python -m newresearch.run_A --scenario S1 --persona P01

# 条件 B (-PKG)
python -m newresearch.run_B --scenario S1 --persona P01

# 条件 C (-RAG)
python -m newresearch.run_C --scenario S1 --persona P01

# 条件 D (Single Agent)
python -m newresearch.run_D --scenario S1 --persona P01
```

### 全アブレーション実行

```bash
# 4 条件 × 10 シナリオ × 3 ペルソナ = 120 runs
python -m newresearch.runner --all

# 特定ペルソナ・シナリオを指定
python -m newresearch.runner --personas P01 --scenarios S1 S2 S3
```

### メトリクス抽出

```bash
python -m newresearch.metrics
# → newresearch/results/metrics.csv
```

---

## 7. 結果の確認

各実行は `newresearch/results/runs/{A,B,C,D}/{run_id}/` に保存されます：

```
config.json       実行設定
context.json      観察 (O)、仮定 (A)、トリガー
evidence.json     外部エビデンス + 外部観察 (Oext)
hypotheses.json   3–5 仮説
judgements.json    診断結果
decision.json     2 仮説対比選択
final.json        最終応答 + empathy/nudge マーカー
response.txt      プレーンテキスト応答
```

### Neo4j での動的グラフ確認

条件 A/C (`use_pkg=true`) では、パイプライン実行中に推論結果が Neo4j に書き込まれます。

```cypher
-- 全グラフ表示
MATCH (n)-[r]->(m) RETURN n, r, m

-- ペルソナ別
MATCH (u:ExpUser {persona_id: "P01"})-[*1..3]-(connected)
RETURN u, connected

-- ランタイム書き込みのみ
MATCH (n) WHERE n.run_id IS NOT NULL
MATCH (n)-[r]-(m) RETURN n, r, m
```

---

## トラブルシューティング

### Neo4j に接続できない

```bash
docker ps -a | grep neo4j     # コンテナ状態確認
docker compose restart graph-db  # 再起動
```

### Azure OpenAI 401 / 429 エラー

1. `.env` の API キーとエンドポイントを確認
2. デプロイメント名が正しいか確認（デフォルト: `gpt-4.1`）
3. Azure Portal でクォータ制限を確認

### PKG シードエラー

```bash
# 一度クリアして再シード
python -m newresearch.seed_pkg --clear
```

### ポート 7474/7687 が既に使用中

```bash
# 既存の Neo4j コンテナを停止
docker stop $(docker ps -q --filter "publish=7474")
docker compose up -d graph-db
```
