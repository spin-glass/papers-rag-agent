"""Message routing workflow using LangGraph."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import TypedDict, Optional, Literal, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from models import EnhancedAnswerResult
from graphs.corrective_rag import answer_with_correction_graph
from graphs.content_enhancement import enhance_answer_content
from retrieval.arxiv_searcher import run_arxiv_search
from config import get_graph_recursion_limit


class MessageState(TypedDict):
    """State for message routing workflow."""
    message_content: str
    message_type: str
    rag_index: Optional[Any]
    arxiv_results: Optional[list]
    rag_result: Optional[EnhancedAnswerResult]
    final_response: Optional[str]
    error: Optional[str]


def classify_message_node(state: MessageState) -> MessageState:
    """Classify the incoming message type."""
    try:
        message = state["message_content"].strip()

        print(f"📝 Classifying message: {message[:50]}...")

        # Check for arxiv search command
        if message.lower().startswith("arxiv:"):
            state["message_type"] = "arxiv"
            print("✅ Classified as: ArXiv search")
        else:
            state["message_type"] = "rag"
            print("✅ Classified as: RAG question")

    except Exception as e:
        print(f"❌ Message classification failed: {e}")
        state["message_type"] = "rag"  # Default to RAG
        state["error"] = f"Classification error: {str(e)}"

    return state


def arxiv_search_node(state: MessageState) -> MessageState:
    """Handle ArXiv search requests."""
    try:
        message = state["message_content"]
        query = message.split(":", 1)[1].strip()

        print(f"🔍 Searching ArXiv for: {query}")

        # Perform ArXiv search
        results = run_arxiv_search(query, max_results=5)
        state["arxiv_results"] = results

        print(f"✅ ArXiv search completed: {len(results)} results")

    except Exception as e:
        print(f"❌ ArXiv search failed: {e}")
        state["arxiv_results"] = []
        state["error"] = f"ArXiv search error: {str(e)}"

    return state


def rag_pipeline_node(state: MessageState) -> MessageState:
    """Handle RAG questions with enhanced content generation."""
    try:
        question = state["message_content"]
        index = state["rag_index"]

        print(f"🤖 Processing RAG question: {question[:50]}...")

        # Check if index is available
        if not index:
            state["error"] = "RAG index not available"
            return state

        # Run corrective RAG workflow
        basic_result = answer_with_correction_graph(question, index=index)

        # Enhance with Cornell Note and Quiz
        enhanced_result = enhance_answer_content(basic_result, question)

        state["rag_result"] = enhanced_result

        print(f"✅ RAG processing completed. Support: {enhanced_result.support:.3f}")

    except Exception as e:
        print(f"❌ RAG pipeline failed: {e}")
        state["error"] = f"RAG pipeline error: {str(e)}"

    return state


def format_arxiv_response_node(state: MessageState) -> MessageState:
    """Format ArXiv search results for display."""
    try:
        results = state.get("arxiv_results", [])

        if not results:
            state["final_response"] = "該当する論文が見つかりませんでした。"
            return state

        # Format results
        lines = []
        for result in results:
            if result.get("pdf"):
                lines.append(f"- [{result['title']}]({result['link']})  •  [PDF]({result['pdf']})")
            else:
                lines.append(f"- [{result['title']}]({result['link']})")

        response = "### ArXiv検索結果\n" + "\n".join(lines)
        state["final_response"] = response

        print(f"✅ ArXiv response formatted: {len(results)} results")

    except Exception as e:
        print(f"❌ ArXiv response formatting failed: {e}")
        state["final_response"] = "検索結果の表示中にエラーが発生しました。"
        state["error"] = f"ArXiv formatting error: {str(e)}"

    return state


def format_rag_response_node(state: MessageState) -> MessageState:
    """Format RAG results for display."""
    try:
        result = state.get("rag_result")

        if not result:
            state["final_response"] = "回答の生成に失敗しました。"
            return state

        # Build response content
        response_parts = []

        # Main answer
        response_parts.append(f"## 回答\n\n{result.text}")

        # Citations
        if result.citations:
            response_parts.append("\n## 引用文献\n")
            for i, citation in enumerate(result.citations, 1):
                response_parts.append(f"{i}. [{citation['title']}]({citation['link']})")

        # Cornell Note
        if result.cornell_note:
            response_parts.append(f"\n## Cornell Note\n\n### Cue\n{result.cornell_note.cue}")
            response_parts.append(f"\n### Notes\n{result.cornell_note.notes}")
            response_parts.append(f"\n### Summary\n{result.cornell_note.summary}")

        # Quiz
        if result.quiz_items:
            response_parts.append("\n## 理解度チェック\n")
            for i, quiz in enumerate(result.quiz_items, 1):
                response_parts.append(f"\n### 問題 {i}\n{quiz.question}\n")
                for option in quiz.options:
                    marker = "✓ " if option.id == quiz.correct_answer else ""
                    response_parts.append(f"- {marker}{option.id.upper()}: {option.text}")

        # Support score
        support_level = _format_support_level(result.support)
        response_parts.append(f"\n**Support: {support_level} (score={result.support:.2f})**")

        # HyDE usage info
        if len(result.attempts) > 1:
            response_parts.append("\n*HyDEを使用した補正検索を実行しました*")

        state["final_response"] = "\n".join(response_parts)

        print(f"✅ RAG response formatted successfully")

    except Exception as e:
        print(f"❌ RAG response formatting failed: {e}")
        state["final_response"] = f"回答の表示中にエラーが発生しました: {str(e)}"
        state["error"] = f"RAG formatting error: {str(e)}"

    return state


def _format_support_level(support_score: float) -> str:
    """Format support score as High/Med/Low."""
    if support_score >= 0.8:
        return "High"
    elif support_score >= 0.62:
        return "Med"
    else:
        return "Low"


def route_message_type(state: MessageState) -> Literal["arxiv", "rag"]:
    """Route message based on classified type."""
    return state["message_type"]


def route_to_formatter(state: MessageState) -> Literal["format_arxiv", "format_rag"]:
    """Route to appropriate formatter based on message type."""
    return "format_arxiv" if state["message_type"] == "arxiv" else "format_rag"


def create_message_routing_graph() -> StateGraph:
    """Create the message routing workflow graph."""

    # Define the graph
    graph = StateGraph(MessageState)

    # Add nodes
    graph.add_node("classify", classify_message_node)
    graph.add_node("arxiv_search", arxiv_search_node)
    graph.add_node("rag_pipeline", rag_pipeline_node)
    graph.add_node("format_arxiv", format_arxiv_response_node)
    graph.add_node("format_rag", format_rag_response_node)

    # Define the flow
    graph.add_edge(START, "classify")

    # Route based on message type
    graph.add_conditional_edges(
        "classify",
        route_message_type,
        {
            "arxiv": "arxiv_search",
            "rag": "rag_pipeline"
        }
    )

    # Route to appropriate formatter
    graph.add_conditional_edges(
        "arxiv_search",
        lambda _: "format_arxiv"
    )

    graph.add_conditional_edges(
        "rag_pipeline",
        lambda _: "format_rag"
    )

    graph.add_edge("format_arxiv", END)
    graph.add_edge("format_rag", END)

    return graph.compile()


def process_message_with_routing(message_content: str, rag_index: Any = None) -> str:
    """
    Process incoming message using LangGraph routing workflow.
    
    Args:
        message_content: User message content
        rag_index: RAG index for retrieval (required for RAG questions)
        
    Returns:
        Formatted response string
    """
    try:
        # Create the message routing graph
        routing_graph = create_message_routing_graph()

        # Prepare initial state
        initial_state = MessageState(
            message_content=message_content,
            message_type="",
            rag_index=rag_index,
            arxiv_results=None,
            rag_result=None,
            final_response=None,
            error=None
        )

        print(f"🚀 Starting message routing workflow...")
        
        # Create RunnableConfig with recursion limit
        config = RunnableConfig(recursion_limit=get_graph_recursion_limit())
        
        # Run the routing workflow
        final_state = routing_graph.invoke(initial_state, config=config)

        # Check for errors
        if final_state.get("error"):
            print(f"⚠️ Workflow completed with errors: {final_state['error']}")

        # Return the final response
        response = final_state.get("final_response")
        if response:
            print(f"✅ Message routing completed successfully")
            return response
        else:
            return "申し訳ございませんが、メッセージの処理中にエラーが発生しました。"

    except Exception as e:
        print(f"❌ Message routing workflow failed: {e}")
        return f"システムエラーが発生しました: {str(e)}"
