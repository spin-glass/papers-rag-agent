"""Mock agent implementation for testing the UI."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models import AnswerPayload, Citation, CornellNote, QuizItem, QuizOption


def run_agent(user_query: str) -> AnswerPayload:
    """
    Mock implementation that returns fixed test data.
    
    Args:
        user_query: User's question (currently ignored in mock)
        
    Returns:
        Fixed AnswerPayload with sample data
    """
    # Mock citations
    citations = [
        Citation(
            id="1",
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer", "Parmar"],
            year=2017,
            url="https://arxiv.org/abs/1706.03762"
        ),
        Citation(
            id="2", 
            title="BERT: Pre-training Deep Bidirectional Transformers",
            authors=["Devlin", "Chang", "Lee", "Toutanova"],
            year=2018,
            url="https://arxiv.org/abs/1810.04805"
        )
    ]
    
    # Mock answer with inline citations
    answer = (
        "Transformers have revolutionized natural language processing. "
        "The attention mechanism [1] allows models to focus on relevant parts "
        "of the input sequence. BERT [2] demonstrated the power of bidirectional "
        "transformers for understanding context in both directions."
    )
    
    # Mock Cornell note
    cornell_note = CornellNote(
        cue="Transformer Architecture",
        notes=(
            "- Self-attention mechanism replaces recurrence\n"
            "- Encoder-decoder structure with multi-head attention\n"
            "- Positional encoding for sequence information\n"
            "- BERT uses only encoder for bidirectional context"
        ),
        summary=(
            "Transformers use attention mechanisms to process sequences in parallel, "
            "enabling better performance and faster training than RNNs. "
            "BERT extends this with bidirectional encoding."
        )
    )
    
    # Mock quiz questions
    quiz_items = [
        QuizItem(
            question="What is the key innovation of the Transformer architecture?",
            options=[
                QuizOption(id="a", text="Recurrent connections"),
                QuizOption(id="b", text="Self-attention mechanism"),
                QuizOption(id="c", text="Convolutional layers"),
                QuizOption(id="d", text="Memory networks")
            ],
            correct_answer="b"
        ),
        QuizItem(
            question="What does BERT stand for?",
            options=[
                QuizOption(id="a", text="Basic Encoder Representation Transformer"),
                QuizOption(id="b", text="Bidirectional Encoder Representations from Transformers"),
                QuizOption(id="c", text="Binary Embedding Recurrent Transformer"),
                QuizOption(id="d", text="Boosted Ensemble Regression Trees")
            ],
            correct_answer="b"
        )
    ]
    
    return AnswerPayload(
        answer=answer,
        cornell_note=cornell_note,
        quiz_items=quiz_items,
        citations=citations
    )
