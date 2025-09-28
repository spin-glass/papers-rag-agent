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
from config import use_langgraph, enable_langsmith_tracing, get_langsmith_api_key, get_langsmith_project, get_langsmith_endpoint
import chainlit as cl


# TODO: Remove this import - it's unused here. Actual import happens at line 340 where it's needed.
# LangGraph availability check
try:
    from graphs.message_routing import process_message_with_routing  # noqa: F401
    LANGGRAPH_AVAILABLE = True
    HAS_MESSAGE_ROUTING = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    HAS_MESSAGE_ROUTING = False
    print("⚠️ LangGraph not available, using legacy implementation")

# Global index for RAG
_rag_index = None

# Add startup logging for Cloud Run debugging
print("🚀 Papers RAG Agent starting up...")
print(f"📍 LangGraph available: {LANGGRAPH_AVAILABLE}")
print("✅ Application module loaded successfully")


def initialize_langsmith_tracing():
    """Initialize LangSmith tracing if enabled."""
    # Simplified: Only log status, don't modify environment variables at runtime
    if enable_langsmith_tracing():
        api_key = get_langsmith_api_key()
        if api_key:
            print(f"✅ LangSmith tracing enabled for project: {get_langsmith_project()}")
        else:
            print("⚠️ LangSmith tracing is enabled but API key not found")
    else:
        print("ℹ️ LangSmith tracing is disabled")


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with a greeting message."""
    global _rag_index

    try:
        # Initialize LangSmith tracing if enabled
        initialize_langsmith_tracing()

        # Check OpenAI API Key before initialization
        from config import get_openai_api_key_safe
        api_key = get_openai_api_key_safe()

        if not api_key:
            await cl.Message(
                content=(
                    "## ⚠️ 設定が必要です\n\n"
                    "Papers RAG Agentを使用するには、OpenAI API Keyの設定が必要です。\n\n"
                    "**設定方法:**\n"
                    "1. [OpenAI Platform](https://platform.openai.com/api-keys) でAPI Keyを取得\n"
                    "2. 環境変数を設定: `export OPENAI_API_KEY=\"your_key_here\"`\n"
                    "3. アプリケーションを再起動\n\n"
                    "詳細は `SETUP.md` をご確認ください。\n\n"
                    "**現在利用可能な機能:**\n"
                    "- `arxiv: <query>`: 論文検索（API Key不要）\n\n"
                    "API Key設定後に全機能をお使いいただけます。"
                )
            ).send()
            return

        # Initialize RAG index with some sample papers
        await initialize_rag_index()

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Critical error during chat initialization: {error_msg}")
        import traceback
        traceback.print_exc()

        await cl.Message(
            content=(
                "## ❌ アプリケーション初期化エラー\n\n"
                f"アプリケーションの初期化中にエラーが発生しました。\n\n"
                f"**エラー詳細:** {error_msg}\n\n"
                "**利用可能な機能:**\n"
                "- `arxiv: <query>`: 論文検索\n\n"
                "管理者にお問い合わせください。"
            )
        ).send()
        return

    await cl.Message(
        content=(
            "## Papers RAG Agent (Baseline + Corrective RAG)\n\n"
            "こんにちは！論文に関する質問をしてください。\n"
            "Baseline RAGまたはHyDEを使った回答を提供します。\n\n"
            "**使い方:**\n"
            "- 通常の質問: RAGによる回答\n"
            "- `arxiv: <query>`: 論文検索\n\n"
            "**テスト用クエリ例:**\n"
            "- 「最近のTransformerに関する論文を探しています」\n"
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

    # Temporarily use legacy implementation for stability
    # TODO: Re-enable LangGraph after Cloud Run deployment is stable
    # if use_langgraph() and LANGGRAPH_AVAILABLE:
    #     await handle_message_with_langgraph(message)
    # else:
    await handle_message_legacy(message)


async def handle_message_with_langgraph(message: cl.Message):
    """Handle messages using LangGraph workflows with streaming support."""
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

    try:
        print(f"🚀 Using LangGraph workflow with streaming for: {message.content[:50]}...")

        # Process message with streaming LangGraph workflow
        response_content = await process_message_with_routing_streaming(
            message_content=message.content,
            rag_index=_rag_index
        )

        print("✅ LangGraph streaming workflow completed")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ LangGraph workflow failed: {e}")

        # Check for specific API key related errors
        if "OPENAI_API_KEY" in error_msg:
            response_content = (
                "## ⚠️ API Key設定エラー\n\n"
                "OpenAI API Keyが設定されていないため、質問に回答できません。\n\n"
                "**解決方法:**\n"
                "1. 環境変数を設定: `export OPENAI_API_KEY=\"your_key_here\"`\n"
                "2. アプリケーションを再起動\n\n"
                "詳細は `SETUP.md` をご確認ください。\n\n"
                "**利用可能な機能:**\n"
                "- `arxiv: <query>`: 論文検索（API Key不要）"
            )
        else:
            response_content = f"LangGraphワークフローでエラーが発生しました: {error_msg}"

        # Send error response
        await send_long_message(response_content)


async def process_message_with_routing_streaming(message_content: str, rag_index=None) -> str:
    """
    LangGraphワークフローをストリーミングで実行し、途中結果をChainlitステップで表示
    """
    from graphs.message_routing import create_message_routing_graph, MessageState
    from config import get_graph_recursion_limit
    from langchain_core.runnables import RunnableConfig

    try:
        # グラフを作成
        routing_graph = create_message_routing_graph()

        # 初期状態を準備
        initial_state = MessageState(
            message_content=message_content,
            message_type="",
            rag_index=rag_index,
            arxiv_results=None,
            rag_result=None,
            final_response=None,
            error=None
        )

        # 最終回答用の空メッセージを準備
        agent_message = cl.Message(content="")
        await agent_message.send()

        config = RunnableConfig(recursion_limit=get_graph_recursion_limit())
        response_chunks = []

        # ストリーミング実行
        async for output in routing_graph.astream_log(initial_state, config=config, include_types=["llm"]):
            for op in output.ops:
                # ノード実行結果の処理
                if op["path"] == "/streamed_output/-":
                    await handle_node_output(op)

                # 最終回答のストリーミング（LLMからの出力）
                elif (op["path"].startswith("/logs/") and
                      op["path"].endswith("/streamed_output_str/-")):
                    chunk = op["value"]
                    response_chunks.append(chunk)
                    await agent_message.stream_token(chunk)

        # 最終的な回答を結合
        final_response = "".join(response_chunks)

        # 回答が空の場合は、最終状態から取得
        if not final_response.strip():
            print("⚠️ No streaming response received, falling back to invoke...")
            final_state = routing_graph.invoke(initial_state, config=config)
            final_response = final_state.get("final_response", "回答の生成に失敗しました。")
            # 空のメッセージに最終回答を設定
            await agent_message.stream_token(final_response)

        return final_response

    except Exception as e:
        print(f"❌ Streaming workflow failed: {e}")
        # フォールバック：通常の処理
        from graphs.message_routing import process_message_with_routing
        return process_message_with_routing(message_content, rag_index)


async def handle_node_output(op):
    """
    各ノードの実行結果をChainlitステップとして表示
    """
    try:
        # ノード名を取得
        node_name = list(op["value"].keys())[0]
        node_state = op["value"][node_name]

        # ノードに応じてステップを表示
        if node_name == "classify":
            await display_classification_step(node_state)
        elif node_name == "rag_pipeline":
            await display_rag_pipeline_step(node_state)
        elif node_name == "arxiv_search":
            await display_arxiv_search_step(node_state)
        elif node_name == "baseline":
            await display_baseline_step(node_state)
        elif node_name == "hyde_rewrite":
            await display_hyde_step(node_state)
        elif node_name == "enhanced_retrieval":
            await display_enhanced_retrieval_step(node_state)
        elif node_name == "format_rag":
            await display_format_step(node_state)
        elif node_name == "format_arxiv":
            await display_arxiv_format_step(node_state)

    except Exception as e:
        print(f"⚠️ Error displaying node output: {e}")


# 各ノード用のステップ表示関数
async def display_classification_step(state):
    """メッセージ分類結果を表示"""
    message_type = state.get("message_type", "unknown")

    async with cl.Step(name="メッセージ分類", type="tool") as step:
        if message_type == "rag":
            step.output = "📝 RAG質問として分類されました"
        elif message_type == "arxiv":
            step.output = "📚 ArXiv検索として分類されました"
        else:
            step.output = f"❓ 分類結果: {message_type}"


async def display_rag_pipeline_step(state):
    """RAGパイプライン実行結果を表示"""
    rag_result = state.get("rag_result")
    error = state.get("error")

    async with cl.Step(name="RAG処理", type="run") as step:
        if error:
            step.output = f"❌ エラー: {error}"
        elif rag_result:
            support = rag_result.support
            citations_count = len(rag_result.citations)
            step.output = f"✅ RAG処理完了\n- Support値: {support:.3f}\n- 引用文献数: {citations_count}"
        else:
            step.output = "🔄 RAG処理中..."


async def display_arxiv_search_step(state):
    """ArXiv検索結果を表示"""
    results = state.get("arxiv_results", [])
    error = state.get("error")

    async with cl.Step(name="ArXiv検索", type="tool") as step:
        if error:
            step.output = f"❌ 検索エラー: {error}"
        else:
            step.output = f"🔍 ArXiv検索完了: {len(results)}件の論文を発見"


async def display_baseline_step(state):
    """ベースライン検索結果を表示"""
    answer = state.get("answer")

    async with cl.Step(name="ベースライン検索", type="tool") as step:
        if answer:
            support = answer.support
            citations = len(answer.citations)
            step.output = f"🔍 ベースライン検索完了\n- Support値: {support:.3f}\n- 検索された文献: {citations}件"
        else:
            step.output = "🔄 ベースライン検索中..."


async def display_hyde_step(state):
    """HyDE処理結果を表示"""
    hyde_query = state.get("hyde_query")

    async with cl.Step(name="HyDE拡張", type="tool") as step:
        if hyde_query:
            # クエリが長い場合は省略
            display_query = hyde_query[:100] + "..." if len(hyde_query) > 100 else hyde_query
            step.output = f"🔄 HyDE拡張クエリ生成完了\n```\n{display_query}\n```"
        else:
            step.output = "❌ HyDE拡張に失敗"


async def display_enhanced_retrieval_step(state):
    """拡張検索結果を表示"""
    answer = state.get("answer")
    baseline_support = state.get("baseline_support")

    async with cl.Step(name="拡張検索", type="tool") as step:
        if answer and baseline_support is not None:
            improvement = answer.support - baseline_support
            step.output = f"✅ HyDE拡張検索完了\n- 新しいSupport値: {answer.support:.3f}\n- 改善度: {improvement:+.3f}"
        else:
            step.output = "🔄 HyDE拡張検索中..."


async def display_format_step(state):
    """最終フォーマット処理を表示"""
    final_response = state.get("final_response")

    async with cl.Step(name="回答フォーマット", type="tool") as step:
        if final_response:
            response_length = len(final_response)
            step.output = f"📝 回答フォーマット完了 ({response_length}文字)"
        else:
            step.output = "🔄 回答をフォーマット中..."


async def display_arxiv_format_step(state):
    """ArXiv検索結果フォーマット処理を表示"""
    final_response = state.get("final_response")
    results = state.get("arxiv_results", [])

    async with cl.Step(name="検索結果フォーマット", type="tool") as step:
        if final_response:
            step.output = f"📝 ArXiv検索結果フォーマット完了 ({len(results)}件)"
        else:
            step.output = "🔄 検索結果をフォーマット中..."


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
                response_content += "\n*HyDEを使用した補正検索を実行しました*"

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
