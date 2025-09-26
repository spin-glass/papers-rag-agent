"""Type definitions for the Papers RAG Agent."""

from typing import List, Optional

from pydantic import BaseModel


class CornellNote(BaseModel):
    """Cornell Note-taking format structure."""
    
    cue: str
    notes: str
    summary: str


class Citation(BaseModel):
    """Citation information for a source."""
    
    id: str
    title: str
    authors: List[str]
    year: int
    url: Optional[str] = None


class QuizOption(BaseModel):
    """Single option for a quiz question."""
    
    id: str
    text: str


class QuizItem(BaseModel):
    """Quiz question with multiple options."""
    
    question: str
    options: List[QuizOption]
    correct_answer: str  # ID of the correct option


class AnswerPayload(BaseModel):
    """Complete response payload from the agent."""
    
    answer: str
    cornell_note: CornellNote
    quiz_items: List[QuizItem]
    citations: List[Citation]
