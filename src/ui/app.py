import sys
from pathlib import Path

# Add src to path for imports BEFORE other imports
sys.path.append(str(Path(__file__).parent.parent))

from retrieval.arxiv_searcher import run_arxiv_search, search_arxiv_papers
from retrieval.inmemory import InMemoryIndex
from pipelines.baseline import set_global_index
from pipelines.corrective import answer_with_correction
from ui.send import send_long_message
from data.cache_loader import load_precomputed_cache, cache_exists
from config import use_langgraph
import chainlit as cl

from adapters.mock_agent import run_agent
from ui.components import render_citations, render_cornell, render_quiz

# LangGraph imports (conditional)
try:
    from graphs.message_routing import process_message_with_routing
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph not available, using legacy implementation")

# Global index for RAG
_rag_index = None


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with a greeting message."""
    global _rag_index

    # Initialize RAG index with some sample papers
    await initialize_rag_index()

    await cl.Message(
        content=(
            "## Papers RAG Agent (Baseline + Corrective RAG)\n\n"
            "こんにちは！論文に関する質問をしてください。\n"
            "Baseline RAGまたはHyDEを使った回答を提供します。\n\n"
            "**使い方:**\n"
            "- 通常の質問: RAGによる回答\n"
            "- `arxiv: <query>`: 論文検索\n\n"
            "**テスト用クエリ例:**\n"
            "- 「Transformerに関する論文を探しています」\n"
            "- 「Attention機構について教えてください」\n"
            "- 「BERT と GPT の違いは何ですか？」\n\n"
            "何について知りたいですか？"
        )
    ).send()


async def initialize_rag_index():
    """Initialize RAG index with precomputed cache or fallback to dynamic loading."""
    global _rag_index

    try:
        # Try to load precomputed cache first
        print("🚀 Initializing RAG index...")

        if cache_exists():
            print("📖 Loading precomputed cache...")
            _rag_index = load_precomputed_cache()

            if _rag_index is not None:
                set_global_index(_rag_index)
                print(f"✅ RAG index loaded from cache with {len(_rag_index.papers_with_embeddings)} papers")
                return
            else:
                print("⚠️  Failed to load cache, falling back to dynamic loading...")
        else:
            print("⚠️  Precomputed cache not found, falling back to dynamic loading...")

        # Fallback to dynamic loading (original implementation)
        await _initialize_rag_index_dynamic()

    except Exception as e:
        print(f"❌ Error initializing RAG index: {e}")
        import traceback
        traceback.print_exc()
        _rag_index = None


async def _initialize_rag_index_dynamic():
    """Fallback dynamic initialization (original implementation)."""
    global _rag_index

    try:
        # Search for multiple batches of relevant papers to populate the index
        all_papers = []

        # Search queries targeting different aspects of NLP/Transformer research
        search_queries = [
            'transformer attention mechanism language',
            'BERT GPT language model pre-training',
            'fine-tuning RLHF instruction following',
            'efficient transformer attention flash',
            'language model evaluation benchmark',
            'neural machine translation attention',
            'pre-trained language representation',
            'self-attention multi-head transformer'
        ]

        for i, query in enumerate(search_queries):
            try:
                # Use relevance-based search for better results
                batch_papers = search_arxiv_papers(query, max_results=8)
                all_papers.extend(batch_papers)
                print(f"  Query {i+1}/{len(search_queries)}: '{query}' -> {len(batch_papers)} papers")
            except Exception as e:
                print(f"  ❌ Query {i+1} failed: {e}")
                continue

        # Remove duplicates based on paper ID
        seen_ids = set()
        papers = []
        for paper in all_papers:
            if paper.id not in seen_ids:
                papers.append(paper)
                seen_ids.add(paper.id)

        # If no papers found, try simple fallback searches
        if not papers:
            print("⚠️  No papers from specialized queries, trying fallback...")
            fallback_queries = ['transformer', 'attention mechanism', 'BERT', 'GPT']
            for query in fallback_queries:
                try:
                    batch_papers = search_arxiv_papers(query, max_results=10)
                    all_papers.extend(batch_papers)
                    print(f"  Fallback '{query}' -> {len(batch_papers)} papers")
                    if len(batch_papers) > 0:
                        break
                except Exception as e:
                    print(f"  Fallback '{query}' failed: {e}")
                    continue

            # Remove duplicates again
            seen_ids = set()
            papers = []
            for paper in all_papers:
                if paper.id not in seen_ids:
                    papers.append(paper)
                    seen_ids.add(paper.id)

        if papers:
            _rag_index = InMemoryIndex()
            _rag_index.build(papers)
            set_global_index(_rag_index)
            print(f"✅ RAG index initialized with {len(papers)} papers")
            print(f"✅ Index contains {len(_rag_index.papers_with_embeddings)} embedded papers")
        else:
            print("❌ Warning: No papers found even with fallback searches")
            _rag_index = None

    except Exception as e:
        print(f"❌ Error in dynamic initialization: {e}")
        import traceback
        traceback.print_exc()
        _rag_index = None


@cl.on_message
async def on_message(message: cl.Message):
    """
    Handle incoming messages from users.

    Args:
        message: Chainlit message object containing user input
    """
    global _rag_index

    # Check if we should use LangGraph workflows
    if use_langgraph() and LANGGRAPH_AVAILABLE:
        await handle_message_with_langgraph(message)
    else:
        await handle_message_legacy(message)


async def handle_message_with_langgraph(message: cl.Message):
    """Handle messages using LangGraph workflows."""
    global _rag_index

    # Ensure RAG index is initialized for RAG questions
    if not message.content.lower().startswith("arxiv:") and _rag_index is None:
        print("⚠️ RAG index is None, initializing...")
        await cl.Message(content="RAG索引が初期化されています。しばらくお待ちください。").send()
        await initialize_rag_index()
        if _rag_index is None:
            print("❌ RAG index initialization failed")
            await cl.Message(content="RAG索引の初期化に失敗しました。").send()
            return

    async with cl.Step(name="LangGraph Processing", type="run") as step:
        step.output = "LangGraphワークフローで処理しています..."

        try:
            print(f"🚀 Using LangGraph workflow for: {message.content[:50]}...")

            # Process message with LangGraph routing workflow
            response_content = process_message_with_routing(
                message_content=message.content,
                rag_index=_rag_index
            )

            step.output = "LangGraphワークフロー完了"

        except Exception as e:
            response_content = f"LangGraphワークフローでエラーが発生しました: {str(e)}"
            step.output = f"エラー: {str(e)}"
            print(f"❌ LangGraph workflow failed: {e}")

    # Send response using chunked sending
    await send_long_message(response_content)


async def handle_message_legacy(message: cl.Message):
    """Handle messages using legacy implementation."""
    global _rag_index

    # Handle arXiv search command
    if message.content.lower().startswith("arxiv:"):
        await handle_arxiv_command(message)
        return

    # Handle RAG questions
    if _rag_index is None:
        print("⚠️ RAG index is None, initializing...")
        await cl.Message(content="RAG索引が初期化されていません。しばらくお待ちください。").send()
        await initialize_rag_index()
        if _rag_index is None:
            print("❌ RAG index initialization failed")
            await cl.Message(content="RAG索引の初期化に失敗しました。").send()
            return
        else:
            print(f"✅ RAG index initialized with {len(_rag_index.papers_with_embeddings)} papers")

    async with cl.Step(name="Legacy Processing", type="run") as step:
        step.output = "RAGパイプラインで回答を生成しています..."

        try:
            # Debug info
            print(f"🔍 Processing query: {message.content}")
            print(f"🔍 Using index with {len(_rag_index.papers_with_embeddings)} papers")

            # Use corrective RAG pipeline
            result = answer_with_correction(message.content, index=_rag_index)

            # Debug result
            print(f"🔍 Result support: {result.support:.3f}")
            print(f"🔍 Result citations: {len(result.citations)}")

            # Format support level
            support_level = format_support_level(result.support)

            # Create response content
            response_content = f"## 回答\n\n{result.text}\n\n"

            # Add citations if available
            if result.citations:
                response_content += "## Citations:\n\n"
                for i, citation in enumerate(result.citations, 1):
                    response_content += f"{i}. [{citation['title']}]({citation['link']})\n"
                response_content += "\n"

            # Add support score
            response_content += f"**Support: {support_level} (score={result.support:.2f})**\n"

            # Add debug info about attempts (optional)
            if len(result.attempts) > 1:
                response_content += f"\n*HyDEを使用した補正検索を実行しました*"

            step.output = "回答生成完了"

        except Exception as e:
            response_content = f"エラーが発生しました: {str(e)}"
            step.output = f"エラー: {str(e)}"

    # Send response using chunked sending
    await send_long_message(response_content)


async def handle_arxiv_command(message: cl.Message):
    """Handle arxiv: command for paper search."""
    q = message.content.split(":", 1)[1].strip()
    hits = run_arxiv_search(q, max_results=5)

    if hits:
        lines = [
            f"- [{h['title']}]({h['link']})  •  [PDF]({h['pdf']})"
            if h.get("pdf")
            else f"- [{h['title']}]({h['link']})"
            for h in hits
        ]
        await cl.Message(content="### arXiv検索結果\n" + "\n".join(lines)).send()
    else:
        await cl.Message(content="該当する論文が見つかりませんでした").send()


def format_support_level(support_score: float) -> str:
    """Format support score as High/Med/Low."""
    if support_score >= 0.8:
        return "High"
    elif support_score >= 0.62:
        return "Med"
    else:
        return "Low"


if __name__ == "__main__":
    import os

    # Set environment variable for running the app
    os.environ["CHAINLIT_HOST"] = "localhost"
    os.environ["CHAINLIT_PORT"] = "8000"

    # This is mainly for development/testing
    # In production, use: chainlit run src/ui/app.py
    print("To run the app, use: uv run chainlit run src/ui/app.py -w")
