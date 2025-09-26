"""UI rendering components for Chainlit."""

import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models import Citation, CornellNote, QuizItem


def render_cornell(note: CornellNote) -> str:
    """
    Render Cornell note in markdown format.
    
    Args:
        note: CornellNote object to render
        
    Returns:
        Formatted markdown string
    """
    return f"""## Cornell Note

### Cue
{note.cue}

### Notes
{note.notes}

### Summary
{note.summary}
"""


def render_quiz(items: List[QuizItem]) -> str:
    """
    Render quiz questions in markdown format.
    
    Args:
        items: List of QuizItem objects to render
        
    Returns:
        Formatted markdown string
    """
    if not items:
        return ""
    
    markdown = "## Quiz Questions\n\n"
    
    for i, item in enumerate(items, 1):
        markdown += f"### Question {i}\n{item.question}\n\n"
        
        for option in item.options:
            # Mark correct answer with ✓
            marker = "✓ " if option.id == item.correct_answer else ""
            markdown += f"- {marker}{option.id.upper()}: {option.text}\n"
        
        markdown += "\n"
    
    return markdown


def render_citations(cites: List[Citation]) -> str:
    """
    Render citations in markdown format.
    
    Args:
        cites: List of Citation objects to render
        
    Returns:
        Formatted markdown string
    """
    if not cites:
        return ""
    
    markdown = "## References\n\n"
    
    for cite in cites:
        authors_str = ", ".join(cite.authors)
        citation_text = f"[{cite.id}] {authors_str} ({cite.year}). {cite.title}"
        
        if cite.url:
            citation_text += f" [{cite.url}]({cite.url})"
        
        markdown += f"{citation_text}\n\n"
    
    return markdown
