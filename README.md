# Papers RAG Agent

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

## Multi-Agent Cooperation（Aime / TreeQuest思想）

* 複数の専門エージェント（例: 領域専門／数理的厳密性／引用重視）が候補回答を生成。
* **批判エージェント（Critic）**が各候補を評価し、**統合エージェント（Integrator）**が最終回答を決定します。
* これにより、単一モデルの偏りを抑え、より妥当な答えを導出します。

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

## フォルダ構成（予定）

```bash
papers-rag-agent/
├── src/
│   ├── graphs/    # LangGraph定義（CRAGループ、マルチエージェント、ハイブリッド検索）
│   ├── agents/    # Query Planner, Summarizer, Judge, Experts, Critics, Integrator
│   ├── retrieval/ # Vector / Graph Retriever 実装
│   ├── ui/        # Chainlitアプリ
│   └── utils/     # 共通処理（PDF→text, chunkerなど）
├── data/          # サンプル論文PDF
├── tests/         # テストコード
├── scripts/       # 評価・補助スクリプト
└── README.md
```
