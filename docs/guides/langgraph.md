# LangGraph Integration Guide

This guide covers how LangGraph is used inside the Papers RAG Agent and how to
configure it.

## Overview

LangGraph workflows power three major features:

1. **Content Enhancement** – adds Cornell Notes and quizzes in parallel to
   each answer.
1. **Corrective RAG (CRAG)** – retries low-support answers using
   HyDE-based query rewriting.
1. **Message Routing** – classifies user intent and dispatches to the
   appropriate pipeline.

## Setup

### Dependencies

Install the project requirements (LangGraph, LangChain Core, and LangChain
OpenAI are included in `pyproject.toml`).

```bash
uv sync
```

### Environment variables

Enable or disable LangGraph through the `USE_LANGGRAPH` flag in your `.env`
file:

```bash
USE_LANGGRAPH=true  # use LangGraph workflows
```

An OpenAI API key must also be present:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Workflows

### Content Enhancement (`src/graphs/content_enhancement.py`)

- Generates Cornell Notes and quiz questions in parallel.
- Combines the results with the base RAG answer before returning to the UI.

### Corrective RAG (`src/graphs/corrective_rag.py`)

- Converts the corrective retry logic into an explicit graph.
- Evaluates the baseline answer; if support is low it invokes HyDE rewriting
  and enhanced retrieval.
- Falls back to a "no answer" node when retries fail.

### Message Routing (`src/graphs/message_routing.py`)

- Classifies each message as an ArXiv search or a RAG question.
- Formats the final response depending on the path taken.

## Usage

### Toggle LangGraph

```bash
# Enable LangGraph (default)
USE_LANGGRAPH=true

# Switch back to the legacy implementation
USE_LANGGRAPH=false
```

### Run the application

```bash
uv run chainlit run src/ui/app.py -w
```

With LangGraph enabled you will see real-time workflow updates such as
"LangGraph Processing" in the Chainlit UI.

## Testing

```bash
# LangGraph workflow tests
uv run pytest tests/test_graphs/ -v

# Full test suite
uv run pytest tests/ -v

# Integration tests (require API key)
uv run pytest tests/test_graphs/ -v -m integration
```

## Troubleshooting

1. **`ImportError: LangGraph not available`** – run `uv sync` to install
   dependencies.
1. **Workflow not triggered** – confirm `USE_LANGGRAPH=true` and restart the
   application.
1. **Rate limit errors** – reduce concurrency or adjust quiz/note generation
   settings in the environment variables.
