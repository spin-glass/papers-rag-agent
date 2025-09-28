# Papers RAG Agent セットアップガイド

このドキュメントでは、Papers RAG Agentの初期設定方法について説明します。

## 必須要件

### 1. OpenAI API Key の設定

Papers RAG AgentはOpenAI APIを使用してテキスト生成と埋め込み処理を行います。

#### API Keyの取得方法

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. アカウントにログインまたは新規作成
3. "Create new secret key" をクリック
4. 生成されたAPI Keyをコピー（再表示されないため注意）

#### API Keyの設定方法

**方法1: 環境変数で設定（推奨）**

```bash
# 一時的な設定（現在のセッションのみ）
export OPENAI_API_KEY="your_api_key_here"

# 永続的な設定（~/.bashrc or ~/.zshrc に追加）
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

**方法2: .envファイルで設定**

プロジェクトルートに `.env` ファイルを作成：

```bash
# .env ファイルの内容
OPENAI_API_KEY=your_api_key_here
LLM_PROVIDER=openai
USE_LANGGRAPH=true
```

### 2. 依存関係のインストール

```bash
# uvを使用してプロジェクト依存関係をインストール
uv sync

# または、pipを使用する場合
pip install -r requirements.txt
```

### 3. 設定の確認

API Keyが正しく設定されているか確認：

```bash
# デバッグスクリプトで確認
uv run python debug_rag.py
```

正常に設定されている場合、以下のような出力が表示されます：

```
✅ Index loaded with 64 papers
🔍 Testing query: 最近のTransformerに関する論文を探しています
📋 Retrieved 5 contexts:
1. A Transformer with Stack Attention...
2. Generalized Probabilistic Attention Mechanism...
```

## トラブルシューティング

### 問題1: "OPENAI_API_KEY not found"

**症状**: アプリ起動時にAPI Keyエラーが表示される

**解決方法**:
1. API Keyが正しく設定されているか確認
2. 環境変数の再読み込み（`source ~/.zshrc`）
3. シェルの再起動

### 問題2: "No contexts retrieved"

**症状**: 質問しても検索結果が0件

**原因**: API Keyが設定されていないため、クエリの埋め込み処理ができない

**解決方法**: OpenAI API Keyの設定を完了

### 問題3: "LangGraph concurrent update error"

**症状**: Content Enhancement時にエラー

**解決方法**: 既に修正済み（`Annotated[str, add]`を使用）

## 動作確認

### 1. 基本的な動作確認

```bash
# アプリケーションの起動
uv run chainlit run src/ui/app.py -w
```

### 2. テスト質問

以下の質問で動作確認：

- 「最近のTransformerに関する論文を探しています」
- 「Attention機構について教えてください」
- 「arxiv: transformer attention mechanism」

### 3. 期待される応答

- ✅ Support Score: 0.4以上
- ✅ Citations: 複数の論文リンク
- ✅ Cornell Note: 自動生成
- ✅ Quiz: 理解度チェック問題

## 高度な設定

### 環境変数一覧

```bash
# 必須
OPENAI_API_KEY=your_api_key_here

# オプション（デフォルト値）
LLM_PROVIDER=openai
TOP_K=5
SUPPORT_THRESHOLD=0.62
MAX_OUTPUT_CHARS=1400
USE_LANGGRAPH=true
GRAPH_RECURSION_LIMIT=10
```

### パフォーマンス調整

- `TOP_K`: 検索結果数（多いほど精度向上、処理時間増加）
- `SUPPORT_THRESHOLD`: サポート閾値（高いほど厳格、回答率低下）
- `GRAPH_RECURSION_LIMIT`: 再帰制限（処理の安全性確保）

## よくある質問

**Q: API Keyの料金は？**
A: OpenAI APIは従量課金制です。Papers RAG Agentは効率的に設計されており、通常の使用では月数ドル程度です。

**Q: オフラインで使用できますか？**
A: 現在はOpenAI APIが必須です。将来的にローカルLLMサポートを検討中です。

**Q: 独自の論文データを追加できますか？**
A: `scripts/build_cache.py`を使用してカスタムデータセットを構築できます。

## セキュリティ保護設定

### Cursorでのシークレット保護

このプロジェクトでは以下の方法でAPI KeyなどのシークレットをCursor AIから保護しています：

1. **`.cursorignore`ファイル**: Cursor AIが`.env`ファイルを読み取らないよう設定
2. **`.gitignore`設定**: Gitリポジトリからの除外
3. **環境変数の使用**: ファイルではなく環境変数での設定を推奨

### 追加の保護手順

```bash
# 1. .env.exampleをコピーして.envを作成
cp .env.example .env

# 2. .envファイルに実際のAPI Keyを設定
# （Cursor AIはこのファイルを読み取りません）

# 3. 環境変数での設定も可能
export OPENAI_API_KEY="your_key_here"
```

## サポート

問題が解決しない場合：

1. [Issues](https://github.com/your-repo/issues) でバグ報告
2. `LANGGRAPH_SETUP.md` でLangGraph関連の詳細確認
3. ログファイルの確認（デバッグ情報を含む）
