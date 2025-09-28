"""Corrective RAG workflow using LangGraph."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END

from models import AnswerResult
from pipelines.baseline import baseline_answer
from llm.hyde import hyde_rewrite
from config import get_support_threshold, get_graph_recursion_limit


class CorrectionState(TypedDict):
    """State for corrective RAG workflow."""
    question: str
    index: Optional[object]
    theta: float
    answer: Optional[AnswerResult]
    hyde_query: Optional[str]
    attempts: list
    final_result: Optional[AnswerResult]
    hyde_attempted: bool  # Flag to track if HyDE has been attempted


def baseline_retrieval_node(state: CorrectionState) -> CorrectionState:
    """Perform baseline RAG retrieval and generation."""
    try:
        print(f"🔍 Starting baseline retrieval for: {state['question'][:50]}...")

        # Perform baseline RAG
        answer = baseline_answer(state["question"], state["index"])

        state["answer"] = answer
        state["attempts"] = answer.attempts.copy()

        print(f"✅ Baseline retrieval completed. Support: {answer.support:.3f}")

    except Exception as e:
        print(f"❌ Baseline retrieval failed: {e}")
        # Create empty result for error case
        state["answer"] = AnswerResult(
            text=f"ベースライン検索中にエラーが発生しました: {str(e)}",
            citations=[],
            support=0.0,
            attempts=[{"type": "baseline", "error": str(e), "support": 0.0}]
        )

    return state


def evaluate_support_node(state: CorrectionState) -> CorrectionState:
    """Evaluate if the support score is sufficient."""
    try:
        answer = state["answer"]
        theta = state["theta"]

        print(f"📊 Evaluating support: {answer.support:.3f} vs threshold: {theta:.3f}")

        # The routing decision will be made by should_continue_correction function
        # This node just logs the evaluation
        if answer.support >= theta:
            print(f"✅ Support sufficient ({answer.support:.3f} >= {theta:.3f})")
        else:
            print(f"⚠️ Support insufficient ({answer.support:.3f} < {theta:.3f}), will try HyDE")

    except Exception as e:
        print(f"❌ Support evaluation failed: {e}")

    return state


def hyde_rewrite_node(state: CorrectionState) -> CorrectionState:
    """Rewrite query using HyDE approach."""
    try:
        print(f"🔄 Starting HyDE rewrite for: {state['question'][:50]}...")

        # Generate HyDE query
        hyde_query = hyde_rewrite(state["question"])
        state["hyde_query"] = hyde_query
        state["hyde_attempted"] = True  # Mark HyDE as attempted

        print(f"✅ HyDE rewrite completed: {hyde_query[:100]}...")

    except Exception as e:
        print(f"❌ HyDE rewrite failed: {e}")
        state["hyde_query"] = None
        state["hyde_attempted"] = True  # Mark as attempted even if failed

    return state


def enhanced_retrieval_node(state: CorrectionState) -> CorrectionState:
    """Perform enhanced retrieval using HyDE query."""
    try:
        if not state["hyde_query"]:
            print("⚠️ No HyDE query available, skipping enhanced retrieval")
            return state

        print(f"🔍 Starting enhanced retrieval with HyDE query...")

        # Perform retrieval with HyDE query
        hyde_answer = baseline_answer(state["hyde_query"], state["index"])

        # Add HyDE attempt information
        hyde_attempt = {
            "type": "hyde",
            "query": state["hyde_query"],
            "top_ids": hyde_answer.attempts[0]["top_ids"] if hyde_answer.attempts else [],
            "support": hyde_answer.support
        }

        # Update answer and attempts
        state["answer"] = hyde_answer
        state["attempts"].extend(hyde_answer.attempts)
        state["attempts"].append(hyde_attempt)

        print(f"✅ Enhanced retrieval completed. New support: {hyde_answer.support:.3f}")

    except Exception as e:
        print(f"❌ Enhanced retrieval failed: {e}")
        # Keep the original answer if HyDE fails
        if state["attempts"]:
            state["attempts"].append({
                "type": "hyde",
                "error": str(e),
                "support": 0.0
            })

    return state


def no_answer_node(state: CorrectionState) -> CorrectionState:
    """Generate no-answer response when all attempts fail."""
    try:
        print("🚫 Generating no-answer response...")

        from pipelines.corrective import no_answer

        # Generate no-answer result
        no_answer_result = no_answer(state["question"], state["attempts"])
        state["answer"] = no_answer_result

        print("✅ No-answer response generated")

    except Exception as e:
        print(f"❌ No-answer generation failed: {e}")
        # Fallback to basic no-answer
        state["answer"] = AnswerResult(
            text="申し訳ございませんが、この質問に対する適切な回答を見つけることができませんでした。",
            citations=[],
            support=0.0,
            attempts=state["attempts"]
        )

    return state


def finalize_result_node(state: CorrectionState) -> CorrectionState:
    """Finalize the result with all attempts included."""
    try:
        answer = state["answer"]

        # Ensure all attempts are included
        final_result = AnswerResult(
            text=answer.text,
            citations=answer.citations,
            support=answer.support,
            attempts=state["attempts"]
        )

        state["final_result"] = final_result
        print(f"✅ Result finalized with {len(state['attempts'])} attempts")

    except Exception as e:
        print(f"❌ Result finalization failed: {e}")
        state["final_result"] = state["answer"]

    return state


def should_continue_correction(state: CorrectionState) -> Literal["sufficient", "try_hyde", "give_up"]:
    """Determine the next step based on current state."""
    answer = state["answer"]
    theta = state["theta"]

    # If no answer exists, give up
    if not answer:
        return "give_up"

    # If support is sufficient, we're done
    if answer.support >= theta:
        return "sufficient"

    # If we haven't tried HyDE yet, try it
    if not state.get("hyde_attempted", False):
        return "try_hyde"

    # If we've tried HyDE and still insufficient, give up
    return "give_up"


def create_corrective_rag_graph() -> StateGraph:
    """Create the corrective RAG workflow graph."""

    # Define the graph
    graph = StateGraph(CorrectionState)

    # Add nodes
    graph.add_node("baseline", baseline_retrieval_node)
    graph.add_node("evaluate", evaluate_support_node)
    graph.add_node("hyde_rewrite", hyde_rewrite_node)
    graph.add_node("enhanced_retrieval", enhanced_retrieval_node)
    graph.add_node("no_answer", no_answer_node)
    graph.add_node("finalize", finalize_result_node)

    # Define the flow
    graph.add_edge(START, "baseline")
    graph.add_edge("baseline", "evaluate")

    # Conditional routing based on support evaluation
    graph.add_conditional_edges(
        "evaluate",
        should_continue_correction,
        {
            "sufficient": "finalize",
            "try_hyde": "hyde_rewrite",
            "give_up": "no_answer"
        }
    )

    graph.add_edge("hyde_rewrite", "enhanced_retrieval")
    graph.add_edge("enhanced_retrieval", "evaluate")
    graph.add_edge("no_answer", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(
        # Set recursion limit to prevent infinite loops
        {"recursion_limit": get_graph_recursion_limit()}
    )


def answer_with_correction_graph(question: str, theta: float = None, index=None) -> AnswerResult:
    """
    Generate answer using corrective RAG with LangGraph workflow.
    
    Args:
        question: User question
        theta: Support threshold (uses environment default if None)
        index: Index to use for retrieval
        
    Returns:
        AnswerResult with answer or no-answer response
    """
    try:
        if theta is None:
            theta = get_support_threshold()

        # Create the corrective RAG graph
        corrective_graph = create_corrective_rag_graph()

        # Prepare initial state
        initial_state = CorrectionState(
            question=question,
            index=index,
            theta=theta,
            answer=None,
            hyde_query=None,
            attempts=[],
            final_result=None,
            hyde_attempted=False
        )

        print(f"🚀 Starting corrective RAG workflow for: {question[:50]}...")
        print(f"⚙️ Recursion limit set to: {get_graph_recursion_limit()}")

        # Run the corrective RAG workflow
        final_state = corrective_graph.invoke(initial_state)

        # Return the final result
        result = final_state.get("final_result") or final_state.get("answer")

        if result:
            print(f"✅ Corrective RAG completed. Final support: {result.support:.3f}")
            return result
        else:
            # Fallback error result
            return AnswerResult(
                text="申し訳ございませんが、システムエラーが発生しました。",
                citations=[],
                support=0.0,
                attempts=final_state.get("attempts", [])
            )

    except Exception as e:
        error_message = str(e)
        print(f"❌ Corrective RAG workflow failed: {error_message}")

        # Check if it's a recursion limit error
        if "recursion_limit" in error_message.lower() or "GRAPH_RECURSION_LIMIT" in error_message:
            error_text = f"RAGワークフローの再帰制限({get_graph_recursion_limit()})に達しました。質問を簡潔にするか、GRAPH_RECURSION_LIMIT環境変数を調整してください。"
            print(f"🔄 Recursion limit reached. Current limit: {get_graph_recursion_limit()}")
        else:
            error_text = f"RAGワークフローでエラーが発生しました: {error_message}"

        # Return error result
        return AnswerResult(
            text=error_text,
            citations=[],
            support=0.0,
            attempts=[{"type": "workflow_error", "error": error_message, "support": 0.0}]
        )
