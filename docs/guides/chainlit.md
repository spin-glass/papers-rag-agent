# Chainlitガイド

## Papers RAG Agent の使い方

### 主な機能

- **ArXiv論文検索** – メッセージの先頭に `arxiv:` を付けることで関連論文を検索し、アブストラクトとPDFリンクを取得できます。
- **研究解説** – 機械学習・AI分野の質問に対して、Cornell Note形式の要約・理解度チェッククイズ・参考文献を生成します。

### 利用例

#### 論文を探す場合

```text
arxiv:transformer attention
arxiv:graph neural networks
arxiv:computer vision survey
```

#### 技術について質問する場合

```text
Transformerアーキテクチャの仕組みを教えてください
アテンション機構とは何ですか？
転移学習について詳しく教えて
```

#### サンプルプロンプト

| 入力例                           | 説明                                    |
| -------------------------------- | --------------------------------------- |
| `arxiv:BERT transformer`         | BERTとTransformerに関する最新論文を検索 |
| `arxiv:few-shot learning`        | Few-shot学習の研究論文を探索            |
| `アテンション機構について教えて` | Cornell Note形式の解説とクイズを生成    |
| `転移学習について詳しく教えて`   | 転移学習の詳細解説と理解度チェック      |
