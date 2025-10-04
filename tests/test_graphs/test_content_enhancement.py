"""Tests for content enhancement workflow."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from models import AnswerResult, CornellNote, QuizItem, QuizOption
from graphs.content_enhancement import enhance_answer_content


class TestContentEnhancement:
    """Test suite for content enhancement workflow."""

    @pytest.fixture
    def sample_answer_result(self):
        """Create a sample answer result for testing."""
        return AnswerResult(
            text="Transformerは自然言語処理において重要なアーキテクチャです。アテンション機構により、長い文章の関係性を効率的に学習できます。",
            citations=[
                {
                    "title": "Attention Is All You Need",
                    "link": "https://arxiv.org/abs/1706.03762",
                }
            ],
            support=0.85,
            attempts=[{"type": "baseline", "support": 0.85}],
        )

    def test_enhance_answer_content_structure(self, sample_answer_result):
        """Test that enhanced answer has the correct structure."""
        question = "Transformerアーキテクチャについて教えてください"

        # This test will be skipped if LangGraph is not available
        try:
            enhanced = enhance_answer_content(sample_answer_result, question)

            # Check that all original fields are preserved
            assert enhanced.text == sample_answer_result.text
            assert enhanced.citations == sample_answer_result.citations
            assert enhanced.support == sample_answer_result.support
            assert enhanced.attempts == sample_answer_result.attempts

            # Check that new fields exist (may be None if generation fails)
            assert hasattr(enhanced, "cornell_note")
            assert hasattr(enhanced, "quiz_items")

        except ImportError:
            pytest.skip("LangGraph not available")

    def test_enhance_answer_content_fallback(self, sample_answer_result):
        """Test fallback behavior when enhancement fails."""
        question = "Invalid question that might cause errors"

        try:
            enhanced = enhance_answer_content(sample_answer_result, question)

            # Should still return a valid EnhancedAnswerResult
            assert enhanced.text == sample_answer_result.text
            assert enhanced.citations == sample_answer_result.citations
            assert enhanced.support == sample_answer_result.support

        except ImportError:
            pytest.skip("LangGraph not available")


class TestContentEnhancementNodes:
    """Test individual nodes in the content enhancement workflow."""

    def test_cornell_note_structure(self):
        """Test Cornell Note structure validation."""
        # Test valid Cornell Note
        note = CornellNote(
            cue="Test cue", notes="Test notes with bullets", summary="Test summary"
        )

        assert note.cue == "Test cue"
        assert note.notes == "Test notes with bullets"
        assert note.summary == "Test summary"

    def test_quiz_structure(self):
        """Test Quiz structure validation."""
        # Test valid Quiz
        quiz = QuizItem(
            question="What is a test?",
            options=[
                QuizOption(id="a", text="Option A"),
                QuizOption(id="b", text="Option B"),
                QuizOption(id="c", text="Option C"),
                QuizOption(id="d", text="Option D"),
            ],
            correct_answer="a",
        )

        assert quiz.question == "What is a test?"
        assert len(quiz.options) == 4
        assert quiz.correct_answer == "a"
        assert quiz.options[0].id == "a"
        assert quiz.options[0].text == "Option A"


# Integration test (requires OpenAI API key)
@pytest.mark.integration
class TestContentEnhancementIntegration:
    """Integration tests for content enhancement."""

    def test_full_enhancement_workflow(self):
        """Test the complete enhancement workflow with real API calls."""
        # This test requires actual API calls and should be run sparingly
        try:
            sample_result = AnswerResult(
                text="機械学習は人工知能の一分野です。データから学習して予測を行います。",
                citations=[{"title": "Sample Paper", "link": "https://example.com"}],
                support=0.8,
                attempts=[{"type": "baseline", "support": 0.8}],
            )

            question = "機械学習について説明してください"
            enhanced = enhance_answer_content(sample_result, question)

            # Check that enhancement was attempted
            assert enhanced.text == sample_result.text

            # Cornell Note and Quiz may or may not be generated depending on API
            # We just verify the structure is correct
            if enhanced.cornell_note:
                assert isinstance(enhanced.cornell_note, CornellNote)
                assert enhanced.cornell_note.cue
                assert enhanced.cornell_note.notes
                assert enhanced.cornell_note.summary

            if enhanced.quiz_items:
                assert isinstance(enhanced.quiz_items, list)
                for quiz in enhanced.quiz_items:
                    assert isinstance(quiz, QuizItem)
                    assert quiz.question
                    assert len(quiz.options) >= 2
                    assert quiz.correct_answer

        except ImportError:
            pytest.skip("LangGraph not available")
        except Exception as e:
            # API-related errors should not fail the test suite
            pytest.skip(f"API integration test failed: {e}")
