# Papers RAG Agent

<!-- CLOUDRUN_URL_START -->
🚀 **Live Demo**: [https://papers-rag-agent-74fhp6jaca-an.a.run.app](https://papers-rag-agent-74fhp6jaca-an.a.run.app)
<!-- CLOUDRUN_URL_END -->

このプロジェクトは **論文学習に特化した RAG × エージェント型チャットボット** です。
ユーザーが論文タイトルや質問を入力すると、以下の処理が行われます。

## Query Planner

ユーザー入力を解析し、検索クエリを生成します（例: HyDE／クエリ拡張）。

## Retriever（GraphRAG + ベクトルハイブリッド）

* arXivから論文を取得し、PDFをテキスト化 → IMRaD構造ごとにチャンク化 → ベクトルDB（FAISS）に格納して検索。
* 加えて、知識グラフを利用した **GraphRAG** により、概念間の関係性を探索。
* LangGraph上でクエリ解析に基づき **ベクトル検索とGraph検索を動的に切り替え／統合** します。

## Summarizer

検索結果をもとに **Cornell Note形式（Cue / Notes / Summary）** を生成し、理解を深めるための **3問クイズ** を作成します。

## Judge（Corrective RAG: CRAG）

回答と引用の整合性をチェックし、不足や誤りがあれば再検索・再生成を行います。
LangGraphの制御フローを用い、**自己検証と修正ループ**を実現します。

## 🔄 リアルタイム処理表示

**NEW**: LangGraphワークフローの途中結果をリアルタイムで表示する機能を追加しました：

* **メッセージ分類**: 入力がRAG質問かArXiv検索かを自動判別
* **ベースライン検索**: 初回検索結果とSupport値を表示
* **HyDE拡張**: Support値が低い場合の拡張クエリ生成過程
* **拡張検索**: HyDE後の改善されたSupport値と改善度
* **回答生成**: 最終回答のストリーミング表示

これにより、ユーザーはRAGの処理過程を透明性高く確認できます。

## Multi-Agent Cooperation（Aime / TreeQuest思想）

* 複数の専門エージェント（例: 領域専門／数理的厳密性／引用重視）が候補回答を生成。
* **批判エージェント（Critic）**が各候補を評価し、**統合エージェント（Integrator）**が最終回答を決定します。
* これにより、単一モデルの偏りを抑え、より妥当な答えを導出します。

## 🚀 クイックスタート

### 必須要件

1. **OpenAI API Key の設定**

   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

2. **依存関係のインストール**

   ```bash
   uv sync
   ```

3. **アプリケーションの起動**

   ```bash
   uv run chainlit run src/ui/app.py -w
   ```

詳細なセットアップ手順は [`SETUP.md`](SETUP.md) をご確認ください。

## 🔄 LangGraph ワークフロー図

<!-- TODO: Mermaid図の自動更新機能を実装
     現在は手動でコピーしているが、以下の機能を実装予定：
     1. scripts/update_readme_with_graphs.py - READMEマーカー方式での自動更新
     2. Taskfile統合 - task docs:update コマンドでの更新
     3. GitHub Actions - グラフ変更時の自動PR作成
     関連: scripts/generate_mermaid_graphs.py (既存)
-->

Papers RAG Agentは複数のLangGraphワークフローで構成されています：

### メッセージルーティングワークフロー

ユーザーの入力を解析し、適切な処理パイプライン（ArXiv検索またはRAG処理）にルーティングします。

```mermaid
graph TD;
__start__([<p>__start__</p>]):::first
classify(classify)
arxiv_search(arxiv_search)
rag_pipeline(rag_pipeline)
format_arxiv(format_arxiv)
format_rag(format_rag)
__end__([<p>__end__</p>]):::last
__start__ --> classify;
arxiv_search --> format_arxiv;
classify -. &nbsp;arxiv&nbsp; .-> arxiv_search;
classify -. &nbsp;rag&nbsp; .-> rag_pipeline;
rag_pipeline --> format_rag;
format_arxiv --> __end__;
format_rag --> __end__;
classDef default fill:#f2f0ff,line-height:1.2
classDef first fill-opacity:0
classDef last fill:#bfb6fc
```

### 補正RAGワークフロー

HyDE（Hypothetical Document Embeddings）を使用した自己補正RAGシステムです。

```mermaid
graph TD;
__start__([<p>__start__</p>]):::first
baseline(baseline)
evaluate(evaluate)
hyde_rewrite(hyde_rewrite)
enhanced_retrieval(enhanced_retrieval)
no_answer(no_answer)
finalize(finalize)
__end__([<p>__end__</p>]):::last
__start__ --> baseline;
baseline --> evaluate;
enhanced_retrieval --> evaluate;
evaluate -. &nbsp;sufficient&nbsp; .-> finalize;
evaluate -. &nbsp;try_hyde&nbsp; .-> hyde_rewrite;
evaluate -. &nbsp;give_up&nbsp; .-> no_answer;
hyde_rewrite --> enhanced_retrieval;
no_answer --> finalize;
finalize --> __end__;
classDef default fill:#f2f0ff,line-height:1.2
classDef first fill-opacity:0
classDef last fill:#bfb6fc
```

### コンテンツ強化ワークフロー

RAG回答をCornell Note形式とクイズ問題で強化します。

```mermaid
graph TD;
__start__([<p>__start__</p>]):::first
cornell_generation(cornell_generation)
quiz_generation(quiz_generation)
format_result(format_result)
__end__([<p>__end__</p>]):::last
__start__ --> cornell_generation;
cornell_generation --> quiz_generation;
quiz_generation --> format_result;
format_result --> __end__;
classDef default fill:#f2f0ff,line-height:1.2
classDef first fill-opacity:0
classDef last fill:#bfb6fc
```

> 📊 詳細なワークフロー図は [`docs/graphs/`](docs/graphs/) ディレクトリで確認できます。

---

## 目標

**Chainlit UI** を通じて以下を確認できること:

* 質問に対して引用付きで回答が返る
* Cornell Note形式の出力（Cue / Notes / Summary）
* 自動生成された3問クイズ
* **Judgeによる自己修正ループ（CRAG）**の実行履歴
* 複数エージェントの候補・批評・合議結果
* 検索モード（ベクトル／Graph）切替の可視化

> 評価は後回し（LangSmith EvalsやRAGASは次フェーズで導入予定）

---

## フォルダ構成

```tree
papers-rag-agent/
├── src/
│   ├── graphs/                # LangGraph 定義（CRAGループ, マルチエージェント, ハイブリッド検索）
│   ├── agents/                # Query Planner, Summarizer, Judge, Experts, Critics, Integrator
│   ├── retrieval/             # Vector / Graph Retriever 実装 + arXiv検索
│   │   └── arxiv_searcher.py
│   ├── adapters/              # 既存のmock_agentなどはここへ
│   │   └── mock_agent.py
│   ├── ui/                    # Chainlit アプリ (app, components)
│   │   ├── app.py
│   │   └── components.py
│   ├── utils/                 # 共通処理（PDF→text, chunkerなど）
│   └── models.py              # 共通モデル
├── data/                      # サンプル論文PDF
├── tests/                     # テストコード
├── scripts/                   # 評価・補助スクリプト
├── README.md
├── pyproject.toml
├── chainlit.md
└── uv.lock
```
