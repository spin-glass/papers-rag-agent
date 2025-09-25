# Papers RAG Agent (MVP)

このプロジェクトは **論文学習に特化した RAG × Agent チャットボット** の最小実装 (MVP) です。
ユーザが論文タイトルや質問を入力すると、以下の処理が行われます。

1. **Query Planner**
   ユーザの入力を解析し、検索クエリを生成します（例: HyDE/クエリ拡張）。

2. **Retriever**
   arXiv から論文を取得し、PDF をテキスト化 → IMRaD/数式ごとにチャンク化 → ベクトルDB (FAISS) に格納し検索します。

3. **Summarizer**
   検索結果をもとに **Cornell Note形式 (Cue / Notes / Summary)** を生成し、理解を深めるための **3問クイズ** を作成します。

4. **Judge**
   回答と引用を照合し、不足や誤りがあればリトライします。

---

## MVPのゴール

- **Chainlit UI** を通じて以下を確認できること:
  - チャットで質問 → 回答が引用付きで返る
  - Cornell Note 出力（Cue / Notes / Summary）
  - 自動生成された 3 問クイズ

- **評価は後回し**（LangSmith Evals や RAGAS は次フェーズ）

---

## フォルダ構成（予定）

papers-rag-agent/
├── src/
│ ├── agents/ # Query Planner, Retriever, Summarizer, Judge
│ ├── ui/ # Chainlit app
│ └── utils/ # 共通処理 (PDF→text, chunker etc.)
├── data/ # サンプル論文PDF
├── tests/ # テストコード
├── scripts/ # evalなどの補助スクリプト
└── README.md

---

## 今後の拡張

- 評価: LangSmith Evals, RAGAS を導入し Faithfulness / Recall / Relevance を測定
- Guardrails: 出典なし断定やNGワードを抑制
- ベクトルDB: FAISS → Pinecone/Weaviate に置換
- CI/CD: LangSmith 回帰テストを品質ゲート化

---
