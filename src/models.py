"""Type definitions for the Papers RAG Agent."""

from typing import List, Optional, Any

from pydantic import BaseModel, ConfigDict


class CornellNote(BaseModel):
    """Cornell Note-taking format structure."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cue: str
    notes: str
    summary: str


class Citation(BaseModel):
    """Citation information for a source."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    url: Optional[str] = None
    id: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None


class QuizOption(BaseModel):
    """Single option for a quiz question."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    text: str


class QuizItem(BaseModel):
    """Quiz question with multiple options."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    question: str
    options: List[QuizOption]
    correct_answer: str  # ID of the correct option


class AnswerPayload(BaseModel):
    """Complete response payload from the agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    answer: str
    cornell_note: CornellNote
    quiz_items: List[QuizItem]
    citations: List[Citation]


class Paper(BaseModel):
    """arXiv paper model with RAG-required fields."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    title: str
    link: str
    pdf: Optional[str] = None
    summary: str
    authors: Optional[List[str]] = None
    updated: Optional[str] = None
    categories: Optional[List[str]] = None


class RetrievedContext(BaseModel):
    """Retrieved context for RAG pipeline."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    paper_id: str
    title: str
    link: str
    summary: str
    embedding: Any  # numpy array


class AnswerResult(BaseModel):
    """Complete answer result from RAG pipeline."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    citations: List[dict]
    support: float
    attempts: List[dict]  # Each attempt (initial/HyDE) summary
    metadata: Optional[dict] = None  # Additional metadata (e.g., support details)


class EnhancedAnswerResult(BaseModel):
    """Enhanced answer result with Cornell Note and Quiz integration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    citations: List[dict]
    support: float
    attempts: List[dict]
    cornell_note: Optional[CornellNote] = None
    quiz_items: Optional[List[QuizItem]] = None
    metadata: Optional[dict] = None  # Additional metadata (e.g., support details)
