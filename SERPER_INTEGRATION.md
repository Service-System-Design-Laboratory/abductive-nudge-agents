# Serper API統合ドキュメント

## 📋 概要

Explorer AgentにSerper API（Google検索API）を統合し、リアルタイムの外部情報取得機能を追加しました。

## 🎯 実装内容

### 1. 新規ファイル

#### `src/utils/serper_client.py`
Serper APIとの通信を管理するクライアントクラス

**主要機能:**
- `search()`: 単一クエリでGoogle検索を実行
- `search_multiple_queries()`: 複数クエリを一括検索
- 自動的に日本語（ja）と地域（jp）を設定
- エラーハンドリングとログ出力

**使用例:**
```python
from src.utils.serper_client import serper_client

results = serper_client.search("運動習慣 健康", num_results=5)
for result in results:
    print(f"{result['title']}: {result['snippet']}")
```

### 2. 修正ファイル

#### `src/agents/explorer.py`
- Serper APIクライアントをインポート
- `_search_external_info()` メソッドを追加
  - 議題、サブトピック、キートピックから最大3つの検索クエリを生成
  - 各クエリで3件の結果を取得（合計最大9件）
- `process()` メソッドを更新
  - 検索結果をLLMのコンテキストに含める
  - 検索結果がない場合は一般知識でフォールバック

#### `src/utils/config.py`
- `serper_api_key` フィールドを追加（オプショナル）
- APIキーが設定されていなくてもシステムは動作可能

#### `requirements.txt`
- `requests==2.32.3` を追加

#### `.env`
- `SERPER_API_KEY` 環境変数の設定を追加

#### `README.md`
- Serper API設定手順を追加
- Explorer Agentの説明を更新
- プロジェクト構造にserper_client.pyを追加

### 3. テストファイル

#### `test_serper.py`
Serper API接続をテストするスクリプト

**実行方法:**
```bash
source venv/bin/activate
python test_serper.py
```

## 🔧 セットアップ手順

### 1. Serper APIキーの取得

1. [https://serper.dev/](https://serper.dev/) にアクセス
2. アカウントを作成（無料プランあり）
3. ダッシュボードでAPIキーを取得

### 2. 環境変数の設定

`.env` ファイルに以下を追加:

```env
SERPER_API_KEY=your_serper_api_key_here
```

### 3. ライブラリのインストール

```bash
source venv/bin/activate
pip install requests==2.32.3
```

## 📊 動作フロー

```
1. User Input
   ↓
2. Perception Agent (知識グラフ作成)
   ↓
3. Chair Agent (議題設定)
   ↓
4. Explorer Agent
   ├─→ 検索クエリ生成 (議題、サブトピック、キートピックから)
   ├─→ Serper API呼び出し (各クエリで3件取得)
   ├─→ 検索結果をLLMコンテキストに追加
   └─→ LLMで情報を整理・分析
   ↓
5. Witness Agent (仮説生成)
   ↓
6. ... (以降のエージェント)
```

## 🎨 出力例

### Explorer Agentのログ出力

```
[Explorer Agent] Searching Serper API: Queries: ['ストレス解消の方法について議論する', 'ストレスの原因と種類', '一般的なストレス解消法（運動・趣味・休息など）']

検索結果:
1. 【例文付き】面接の質問「ストレス解消法」の上手な答え方とNG ...
   私のストレス解消法は、好きな音楽を聴きながら、ゆっくりと半身浴をすることです...
   出典: https://kimisuka.com/contents/job-interview/24337

2. ストレス解消法一覧。心身の疲れを癒す方法は？
   ストレス解消法には、運動、趣味、休息、食事など様々な方法があります...
   出典: https://www.example.com/stress-relief
```

## 🔍 API使用制限

### Serper API無料プランの制限
- **1日あたり**: 2,500 検索
- **月あたり**: 5,000 検索

### 本システムでの使用量
- 1回の会話あたり: 最大3クエリ × 3結果 = 9件
- APIキーが設定されていない場合は自動的にフォールバック

## ⚠️ 注意事項

1. **APIキー未設定時の動作**
   - システムは正常に動作します
   - Explorer AgentはLLMの知識のみを使用
   - ログに警告メッセージが表示されます

2. **API制限への対応**
   - 検索クエリ数を最大3つに制限
   - 各クエリの結果を3件に制限
   - 必要に応じて`_search_external_info()`メソッドで調整可能

3. **エラーハンドリング**
   - ネットワークエラー時は空の結果を返す
   - API制限超過時も空の結果を返す
   - LLMはフォールバックして一般知識で回答

## 🧪 テスト方法

### 1. Serper API単体テスト

```bash
python test_serper.py
```

### 2. システム全体テスト

```bash
python cli.py --user test_user --message "ストレス解消の方法を教えてください"
```

### 3. ログ確認

```bash
cat logs/conversation_*.txt | grep "検索結果:"
```

## 📈 今後の拡張案

1. **検索タイプの追加**
   - ニュース検索（`search_type="news"`）
   - 画像検索（`search_type="images"`）

2. **キャッシング機能**
   - 同じクエリの結果をキャッシュして API 使用量を削減

3. **検索結果の精度向上**
   - より詳細な検索クエリの生成
   - 検索結果のランキング・フィルタリング

4. **他の検索APIとの統合**
   - Bing Search API
   - Google Custom Search API
   - DuckDuckGo API

## 📚 参考リンク

- [Serper API Documentation](https://serper.dev/docs)
- [Serper API Playground](https://serper.dev/playground)
- [Pricing](https://serper.dev/pricing)
