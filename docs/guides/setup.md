# Environment Setup Guide

This document describes how to prepare the Papers RAG Agent for local development. A Japanese translation is included in the second half of the file.

## Prerequisites

1. **OpenAI API key** – required for embeddings and text generation.
2. **Python environment** – install dependencies with [uv](https://github.com/astral-sh/uv) (recommended) or `pip`.

### Configure environment variables

```bash
# Temporary for the current shell session
export OPENAI_API_KEY="your_api_key_here"

# Persistent (add to ~/.zshrc or ~/.bashrc)
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

Alternatively, create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai

# Optional LangSmith configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=papers-rag-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Legacy LangSmith variables
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=papers-rag-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# LangGraph configuration
USE_LANGGRAPH=true
GRAPH_RECURSION_LIMIT=10

# RAG configuration
TOP_K=5
SUPPORT_THRESHOLD=0.35
MAX_OUTPUT_CHARS=1400
```

### Install dependencies

```bash
# Recommended
uv sync

# Alternative
pip install -r requirements.txt
```

### Sanity check

Verify the setup with the debug helper:

```bash
uv run python debug_rag.py
```

You should see index loading and retrieval logs when the configuration is correct.

### Run the app locally

```bash
uv run chainlit run src/ui/app.py -w
```

For LangGraph-specific instructions, see [`langgraph.md`](langgraph.md). Deployment details live in [`deployment.md`](deployment.md).

---

## セットアップガイド（日本語）

Papers RAG Agent をローカルで開発・実行するための設定手順です。

### 必須要件

1. **OpenAI API Key** – 埋め込みとテキスト生成に必須です。
2. **Python 実行環境** – [uv](https://github.com/astral-sh/uv)（推奨）または `pip` で依存関係をインストールします。

### 環境変数の設定

```bash
# 一時的な設定（現在のシェルのみ）
export OPENAI_API_KEY="your_api_key_here"

# 永続的な設定（~/.zshrc or ~/.bashrc に追記）
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

プロジェクトルートに `.env` ファイルを作成する場合：

```bash
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai

# LangSmith 設定（任意）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=papers-rag-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# 互換性維持のための旧LangSmith変数
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=papers-rag-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# LangGraph 設定
USE_LANGGRAPH=true
GRAPH_RECURSION_LIMIT=10

# RAG 設定
TOP_K=5
SUPPORT_THRESHOLD=0.35
MAX_OUTPUT_CHARS=1400
```

### 依存関係のインストール

```bash
# 推奨
uv sync

# 代替手段
pip install -r requirements.txt
```

### 動作確認

デバッグスクリプトで初期設定を確認します。

```bash
uv run python debug_rag.py
```

設定が正しければ、インデックスの読み込みや検索結果が表示されます。

### アプリケーションの起動

```bash
uv run chainlit run src/ui/app.py -w
```

LangGraphの詳細は [`langgraph.md`](langgraph.md) を、Cloud Run へのデプロイ手順は [`deployment.md`](deployment.md) を参照してください。
