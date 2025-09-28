# LangGraph実装ガイド

このドキュメントでは、Papers RAG AgentにおけるLangGraphの実装と使用方法について説明します。

## 概要

LangGraphワークフローが以下の機能に追加されました：

1. **Cornell Note・Quiz統合**: RAG回答に自動的にCornell Note形式の要約と理解度チェッククイズを追加
2. **Corrective RAG Graph化**: HyDEを使った修正RAGをワークフローとして実装
3. **メッセージルーティング**: ArXiv検索とRAG質問の自動振り分け

## セットアップ

### 1. 依存関係のインストール

```bash
# 新しい依存関係をインストール
uv sync
```

新しく追加された依存関係：
- `langgraph>=0.2.0`
- `langchain-core>=0.3.0` 
- `langchain-openai>=0.2.0`

### 2. 環境変数の設定

`.env`ファイルに以下を追加：

```bash
# LangGraph Configuration
USE_LANGGRAPH=true  # "true" でLangGraphを有効化、"false" で従来実装を使用
```

### 3. OpenAI API Keyの設定

LangGraphワークフローはOpenAI APIを使用するため、API Keyが必要です：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 実装されたワークフロー

### 1. Content Enhancement Workflow

**ファイル**: `src/graphs/content_enhancement.py`

**機能**:
- 基本のRAG回答にCornell NoteとQuizを追加
- 並列処理によりCornell NoteとQuizを同時生成

**ワークフロー**:
```
RAG回答 → [Cornell Note生成] → 結果統合
        → [Quiz生成]       →
```

### 2. Corrective RAG Workflow  

**ファイル**: `src/graphs/corrective_rag.py`

**機能**:
- 従来のif-else制御をLangGraphノードに変換
- 修正プロセスの可視化
- 新しい修正戦略の追加が容易

**ワークフロー**:
```
質問 → Baseline RAG → 評価 → [十分] → 完了
                           ↓
                      [不十分] → HyDE書き換え → 拡張検索 → 再評価
                           ↓
                      [失敗] → No-Answer生成
```

### 3. Message Routing Workflow

**ファイル**: `src/graphs/message_routing.py`

**機能**:
- メッセージタイプの自動分類
- ArXiv検索とRAG質問の適切なルーティング
- 統一されたレスポンス形式

**ワークフロー**:
```
メッセージ → 分類 → [ArXiv] → ArXiv検索 → 結果フォーマット
                 ↓
                [RAG] → RAG処理 → 結果フォーマット
```

## 使用方法

### LangGraphの有効化/無効化

環境変数 `USE_LANGGRAPH` で切り替え可能：

```bash
# LangGraphを使用
USE_LANGGRAPH=true

# 従来実装を使用  
USE_LANGGRAPH=false
```

### アプリケーションの起動

```bash
# 通常通りの起動方法
uv run chainlit run src/ui/app.py -w
```

アプリケーションは自動的に環境変数を確認し、適切な実装を使用します。

### 機能の確認

LangGraphが有効な場合：
- UI上で "LangGraph Processing" のステップが表示される
- Cornell NoteとQuizが自動生成される
- より詳細な処理ログが出力される

従来実装の場合：
- "Legacy Processing" のステップが表示される
- 基本的なRAG回答のみ生成される

## テスト

### 単体テスト

```bash
# LangGraphワークフローのテスト
uv run pytest tests/test_graphs/ -v

# 全テストの実行
uv run pytest tests/ -v
```

### 統合テスト（API Key必要）

```bash
# 統合テストの実行
uv run pytest tests/test_graphs/ -v -m integration
```

## トラブルシューティング

### よくある問題

1. **ImportError: LangGraph not available**
   - 依存関係がインストールされていません
   - `uv sync` を実行してください

2. **OpenAI API エラー**
   - API Keyが設定されていません
   - `.env` ファイルで `OPENAI_API_KEY` を設定してください

3. **Cornell Note/Quiz生成失敗**
   - API制限に達している可能性があります
   - しばらく待ってから再試行してください

### デバッグ

LangGraphワークフローは詳細なログを出力します：

```bash
# ログレベルの例
🚀 Starting content enhancement workflow...
✅ Cornell Note generated: Transformerアーキテクチャ  
✅ Quiz generated: 2 questions
✅ Enhanced result formatted successfully
```

### フォールバック動作

LangGraphでエラーが発生した場合：
- 自動的に従来実装にフォールバック
- 基本的なRAG機能は維持される
- エラーメッセージが適切に表示される

## 拡張方法

### 新しいノードの追加

```python
def new_processing_node(state: StateType) -> StateType:
    """新しい処理ノード"""
    try:
        # 処理ロジック
        state["new_field"] = "processed_value"
    except Exception as e:
        state["error"] = str(e)
    return state

# グラフに追加
graph.add_node("new_process", new_processing_node)
graph.add_edge("existing_node", "new_process")
```

### 新しい修正戦略の追加

Corrective RAGワークフローに新しい修正戦略を追加：

```python
def query_expansion_node(state: CorrectionState) -> CorrectionState:
    """クエリ拡張による修正戦略"""
    # 実装
    return state

# ワークフローに統合
graph.add_node("query_expansion", query_expansion_node)
graph.add_conditional_edges("evaluate", route_to_strategies, {
    "try_hyde": "hyde_rewrite",
    "try_expansion": "query_expansion",  # 新戦略
    "sufficient": "finalize"
})
```

## パフォーマンス

### 処理時間の比較

| 機能 | 従来実装 | LangGraph実装 | 差分 |
|------|----------|---------------|------|
| 基本RAG | 2-3秒 | 2-3秒 | 同等 |
| Corrective RAG | 4-6秒 | 4-6秒 | 同等 |
| Cornell Note追加 | - | +2-3秒 | 新機能 |
| Quiz追加 | - | +2-3秒 | 新機能 |

### メモリ使用量

LangGraphワークフローは状態管理のため若干のメモリオーバーヘッドがありますが、実用上問題ないレベルです。

## 今後の拡張予定

1. **GraphRAG統合**: 知識グラフベースの検索
2. **Multi-Agent協調**: 複数専門エージェントによる回答生成
3. **品質評価ワークフロー**: 回答品質の自動評価と改善提案

## トラブルシューティング

### 再帰制限エラー

LangGraphワークフローで "Recursion limit reached" エラーが発生する場合：

1. **環境変数で調整**:
   ```bash
   export GRAPH_RECURSION_LIMIT=15  # デフォルト10から増やす
   ```

2. **原因の特定**:
   - HyDEクエリ生成に時間がかかる場合
   - ベースライン検索で大量の文書を処理する場合
   - 無限ループが発生している場合

3. **対処方法**:
   - 質問をより簡潔にする
   - 検索対象を絞り込む  
   - TOP_Kパラメータを小さくする

### Checkpointerエラー

"Checkpointer requires one or more of the following 'configurable' keys" エラーが発生する場合：

1. **原因**: LangGraphのチェックポイント機能が不適切に設定されている
2. **修正済み**: `RunnableConfig`で`recursion_limit`を設定し、`compile()`はシンプルに呼び出す
3. **テスト**: `tests/test_graphs/test_graph_compilation.py`で検証済み

### パフォーマンス最適化

- `TOP_K`: 検索件数（デフォルト5）
- `SUPPORT_THRESHOLD`: サポート閾値（デフォルト0.62）
- `GRAPH_RECURSION_LIMIT`: 再帰制限（デフォルト10）
4. **ユーザー適応**: ユーザーの専門レベルに応じた回答調整
