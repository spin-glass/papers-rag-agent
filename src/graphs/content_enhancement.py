"""Content enhancement workflow using LangGraph for Cornell Note and Quiz generation."""

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from models import CornellNote, QuizItem, QuizOption, AnswerResult, EnhancedAnswerResult
from llm.generator import generate_answer
from config import get_graph_recursion_limit, get_openai_api_key_safe


class ContentEnhancementState(TypedDict):
    """State for content enhancement workflow."""

    question: str  # Remove Annotated to avoid concurrent updates
    answer_text: str
    citations: List[dict]
    support: float
    attempts: List[dict]
    cornell_note: Optional[CornellNote]
    quiz_items: Optional[List[QuizItem]]
    error: Optional[str]  # Remove Annotated to avoid concurrent updates


def cornell_note_generation_node(
    state: ContentEnhancementState,
) -> ContentEnhancementState:
    """Generate Cornell Note from answer content."""
    try:
        # Check if OpenAI API key is available
        if not get_openai_api_key_safe():
            print("⚠️ Skipping Cornell Note generation - OPENAI_API_KEY not set")
            state["error"] = "Cornell Note generation skipped - API key not available"
            return state
        prompt = f"""Based on the following question and answer, create a Cornell Note format summary.

Question: {state["question"]}

Answer: {state["answer_text"]}

Generate a Cornell Note with:
1. Cue: Key concepts and terms (1-2 short phrases)
2. Notes: Main points in bullet format (3-5 bullets)
3. Summary: Concise summary in 1-2 sentences

Format your response as:
CUE: [your cue here]
NOTES: [your notes here]
SUMMARY: [your summary here]
"""

        response = generate_answer(prompt, question=state["question"])

        # Parse the response
        lines = response.strip().split("\n")
        cue = ""
        notes = ""
        summary = ""

        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("CUE:"):
                current_section = "cue"
                cue = line[4:].strip()
            elif line.startswith("NOTES:"):
                current_section = "notes"
                notes = line[6:].strip()
            elif line.startswith("SUMMARY:"):
                current_section = "summary"
                summary = line[8:].strip()
            elif line and current_section:
                if current_section == "cue":
                    cue += f" {line}"
                elif current_section == "notes":
                    notes += f"\n{line}"
                elif current_section == "summary":
                    summary += f" {line}"

        cornell_note = CornellNote(
            cue=cue.strip(), notes=notes.strip(), summary=summary.strip()
        )

        state["cornell_note"] = cornell_note
        print(f"✅ Cornell Note generated: {cue}")

    except Exception as e:
        print(f"❌ Cornell Note generation failed: {e}")
        state["error"] = f"Cornell Note generation failed: {str(e)}"

    return state


def quiz_generation_node(state: ContentEnhancementState) -> ContentEnhancementState:
    """Generate quiz questions from answer content."""
    try:
        # Check if OpenAI API key is available
        if not get_openai_api_key_safe():
            print("⚠️ Skipping Quiz generation - OPENAI_API_KEY not set")
            state["error"] = "Quiz generation skipped - API key not available"
            return state
        prompt = f"""Based on the following question and answer, create 2 multiple-choice quiz questions to test understanding.

Question: {state["question"]}

Answer: {state["answer_text"]}

Generate 2 quiz questions with 4 options each. Format your response exactly as:

QUESTION 1: [your question here]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
CORRECT: [A/B/C/D]

QUESTION 2: [your question here]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
CORRECT: [A/B/C/D]

Make sure the questions test key concepts from the answer and have clear correct answers.
"""

        response = generate_answer(prompt, question=state["question"])

        # Parse the response
        quiz_items = []
        lines = response.strip().split("\n")

        current_question = None
        current_options = []
        current_correct = None

        for line in lines:
            line = line.strip()
            if line.startswith("QUESTION"):
                # Save previous question if exists
                if current_question and len(current_options) == 4 and current_correct:
                    quiz_items.append(
                        QuizItem(
                            question=current_question,
                            options=current_options,
                            correct_answer=current_correct.lower(),
                        )
                    )

                # Start new question
                current_question = line.split(":", 1)[1].strip()
                current_options = []
                current_correct = None
            elif line.startswith(("A)", "B)", "C)", "D)")):
                option_id = line[0].lower()
                option_text = line[3:].strip()
                current_options.append(QuizOption(id=option_id, text=option_text))
            elif line.startswith("CORRECT:"):
                current_correct = line[8:].strip().lower()

        # Save the last question
        if current_question and len(current_options) == 4 and current_correct:
            quiz_items.append(
                QuizItem(
                    question=current_question,
                    options=current_options,
                    correct_answer=current_correct,
                )
            )

        state["quiz_items"] = quiz_items
        print(f"✅ Quiz generated: {len(quiz_items)} questions")

    except Exception as e:
        print(f"❌ Quiz generation failed: {e}")
        state["error"] = f"Quiz generation failed: {str(e)}"

    return state


def format_enhanced_result_node(
    state: ContentEnhancementState,
) -> ContentEnhancementState:
    """Format the final enhanced result."""
    try:
        # Create enhanced result
        enhanced_result = EnhancedAnswerResult(
            text=state["answer_text"],
            citations=state["citations"],
            support=state["support"],
            attempts=state["attempts"],
            cornell_note=state.get("cornell_note"),
            quiz_items=state.get("quiz_items"),
        )

        state["enhanced_result"] = enhanced_result
        print("✅ Enhanced result formatted successfully")

    except Exception as e:
        print(f"❌ Result formatting failed: {e}")
        state["error"] = f"Result formatting failed: {str(e)}"

    return state


def create_content_enhancement_graph() -> StateGraph:
    """Create the content enhancement workflow graph."""

    # Define the graph
    graph = StateGraph(ContentEnhancementState)

    # Add nodes
    graph.add_node("cornell_generation", cornell_note_generation_node)
    graph.add_node("quiz_generation", quiz_generation_node)
    graph.add_node("format_result", format_enhanced_result_node)

    # Define the flow (sequential to avoid concurrent updates)
    graph.add_edge(
        START, "cornell_generation"
    )  # TODO: cornell_generation and quiz_generation should be parallel
    graph.add_edge("cornell_generation", "quiz_generation")
    graph.add_edge("quiz_generation", "format_result")
    graph.add_edge("format_result", END)

    return graph.compile()


def enhance_answer_content(
    answer_result: AnswerResult, question: str
) -> EnhancedAnswerResult:
    """
    Enhance answer content with Cornell Note and Quiz using LangGraph.

    Args:
        answer_result: Basic answer result from RAG pipeline
        question: Original user question

    Returns:
        Enhanced answer result with Cornell Note and Quiz
    """
    try:
        # Create the enhancement graph
        enhancement_graph = create_content_enhancement_graph()

        # Prepare initial state
        initial_state = ContentEnhancementState(
            question=question,
            answer_text=answer_result.text,
            citations=answer_result.citations,
            support=answer_result.support,
            attempts=answer_result.attempts,
            cornell_note=None,
            quiz_items=None,
            error=None,
        )

        # Run the enhancement workflow
        print("🚀 Starting content enhancement workflow...")

        # Create RunnableConfig with recursion limit
        config = RunnableConfig(recursion_limit=get_graph_recursion_limit())

        final_state = enhancement_graph.invoke(initial_state, config=config)

        # Check for errors
        if final_state.get("error"):
            print(f"⚠️ Enhancement completed with errors: {final_state['error']}")

        # Return enhanced result
        return EnhancedAnswerResult(
            text=answer_result.text,
            citations=answer_result.citations,
            support=answer_result.support,
            attempts=answer_result.attempts,
            cornell_note=final_state.get("cornell_note"),
            quiz_items=final_state.get("quiz_items") or [],
            metadata=answer_result.metadata,  # Preserve support details
        )

    except Exception as e:
        print(f"❌ Content enhancement workflow failed: {e}")
        # Return basic result without enhancements
        return EnhancedAnswerResult(
            text=answer_result.text,
            citations=answer_result.citations,
            support=answer_result.support,
            attempts=answer_result.attempts,
            cornell_note=None,
            quiz_items=[],
            metadata=answer_result.metadata,  # Preserve support details
        )
