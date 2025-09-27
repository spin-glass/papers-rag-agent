# Papers RAG Agent 🔍📚

AIによる論文検索・分析システムです。ArXivの最新論文を検索し、研究内容について詳しく解説します。

## 主な機能

### 📋 ArXiv論文検索
メッセージの先頭に `arxiv:` を付けることで、ArXivから関連論文を検索できます。

**検索例:**
- `arxiv:transformer attention`
- `arxiv:graph neural networks`

検索結果では論文タイトル、アブストラクトページ、PDFへの直接リンクを提供します。

### 🧠 研究解説
機械学習・AI分野の専門的な質問にお答えします。回答は以下の形式で提供されます:

- **Cornell Noteスタイル** での構造化された解説
- **理解度チェック** のためのクイズ問題
- **参考文献** と適切な引用

## 利用方法

### 論文を探す場合
```
arxiv:BERT
arxiv:computer vision survey
arxiv:reinforcement learning
```

### 技術について質問する場合
```
Transformerアーキテクチャの仕組みを教えてください
アテンション機構とは何ですか？
強化学習の基本概念について
```

## 活用例

| 入力例 | 説明 |
|--------|------|
| `arxiv:BERT transformer` | BERTとTransformerに関する最新論文を検索 |
| `arxiv:few-shot learning` | Few-shot学習の研究論文を探索 |
| `転移学習について詳しく教えて` | 転移学習の詳細解説とクイズを生成 |
| `GANの仕組みを説明して` | Generative Adversarial Networksの解説 |

研究活動にお役立てください。
